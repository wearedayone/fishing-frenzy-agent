"""On-chain Ronin blockchain interactions for Fishing Frenzy Agent."""

import time
import urllib.request
import json as _json

from web3 import Web3
from eth_account import Account
from . import state
from . import api_client as api

RONIN_RPC = "https://api.roninchain.com/rpc"
CHAIN_ID = 2020

CONTRACTS = {
    "daily_checkin": "0xaE059c34ce34641Eb19Adf78D721CA81ecADBdBe",
    "fish_token":    "0x5F3262edE02ca4A31BdA6683124539c87CC73138",
    "xfish_token":   "0x533701B17963AAf318E11ab274Ca8e2Ec813aA64",
    "stake":         "0xB9f0D9997f0b92040e73a08Ed470d16FdDa80AB8",
    "chest_nft":     "0x9c76fc5Bd894E7F51c422F072675c876d5998A9e",
    "chest_factory": "0x2A0b24C499bacca01f7D7af8d7e6fB6741ADE321",
    "aquarium":      "0xa005baeb3debfc311b0ea1161828969f24a8e18b",
    "fish_nft":      "0x4079da822E8972982b8569e38cdF719A21069934",
    "rod_nft":       "0x77CE5148b7ad284e431175Ad7258B54A64816da6",
    "usdc":          "0x0b7007c13325c48911f73a2dad5fa5dcbf808adc",
    "spin_wheel":    "0x02F3b724408EE1ba36A279526c213846b7339501",
    "vrf_coordinator": "0x16a62a921e7fec5bf867ff5c805b662db757b778",
}

# Minimal ABIs — only the functions we call

CHECKIN_ABI = [
    {
        "inputs": [],
        "name": "checkIn",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "checkInPrice",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

STAKE_ABI = [
    {
        "inputs": [
            {"name": "tokenAddress", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "duration", "type": "uint256"},
        ],
        "name": "stakeERC20",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "tokenAddress", "type": "address"},
            {"name": "stakeIndex", "type": "uint256"},
        ],
        "name": "unstakeERC20",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "user", "type": "address"},
            {"name": "tokenAddress", "type": "address"},
        ],
        "name": "stakedERC20Lists",
        "outputs": [
            {
                "components": [
                    {"name": "amount", "type": "uint256"},
                    {"name": "startTime", "type": "uint256"},
                    {"name": "duration", "type": "uint256"},
                ],
                "name": "",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

KATANA_V2_ROUTER = "0x7d0556d55ca1a92708681e2e231733ebd922597d"
WRON = "0xe514d9deb7966c8be0ca922de8a064264ea6bcd4"

KATANA_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"},
        ],
        "name": "getAmountsOut",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"},
        ],
        "name": "swapExactRONForTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "payable",
        "type": "function",
    },
]

CHEST_FACTORY_ABI = [
    {
        "inputs": [
            {"name": "chestTokenIds", "type": "bytes32[]"},
            {"name": "tierIds", "type": "uint16[]"},
            {"name": "quantities", "type": "uint256[]"},
            {"name": "nonce", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
            {"name": "signature", "type": "bytes"},
        ],
        "name": "mintBatchChestWithSignature",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "tokenIds", "type": "uint256[]"},
        ],
        "name": "openBatchChest",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


def _get_w3() -> Web3:
    """Get a Web3 instance connected to Ronin RPC with PoA middleware."""
    w3 = Web3(Web3.HTTPProvider(RONIN_RPC))
    # Ronin is a PoA chain — extraData > 32 bytes without this middleware
    try:
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except ImportError:
        # Older web3.py versions
        from web3.middleware import geth_poa_middleware
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to Ronin RPC")
    return w3


def _get_wallet_and_account():
    """Get wallet info and eth_account Account object."""
    wallet = state.get_wallet()
    if not wallet:
        raise RuntimeError("No wallet found. Call setup_account() first.")
    account = Account.from_key(wallet["private_key"])
    return wallet, account


def _send_tx(w3: Web3, tx: dict) -> str:
    """Sign and send a transaction, wait for receipt, return tx hash.

    Args:
        w3: Web3 instance.
        tx: Transaction dict (to, data, value, etc.). Will auto-fill
            chainId, from, nonce, gasPrice, and gas if not provided.

    Returns:
        Transaction hash hex string.
    """
    wallet, account = _get_wallet_and_account()

    tx["chainId"] = CHAIN_ID
    tx["from"] = account.address
    tx["nonce"] = w3.eth.get_transaction_count(account.address)

    if "gasPrice" not in tx:
        tx["gasPrice"] = w3.eth.gas_price

    if "gas" not in tx:
        tx["gas"] = w3.eth.estimate_gas(tx)

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

    if receipt["status"] != 1:
        raise RuntimeError(f"Transaction reverted: {tx_hash.hex()}")

    return tx_hash.hex()


# ============================================================
# Balance Reads
# ============================================================

def get_ron_balance() -> float:
    """Get native RON balance in human-readable units."""
    w3 = _get_w3()
    wallet, _ = _get_wallet_and_account()
    balance_wei = w3.eth.get_balance(wallet["address"])
    return float(w3.from_wei(balance_wei, "ether"))


def get_fish_balance() -> float:
    """Get FISH token balance."""
    w3 = _get_w3()
    wallet, _ = _get_wallet_and_account()
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS["fish_token"]),
        abi=ERC20_ABI,
    )
    decimals = contract.functions.decimals().call()
    balance = contract.functions.balanceOf(wallet["address"]).call()
    return balance / (10 ** decimals)


def get_xfish_balance() -> float:
    """Get xFISH token balance."""
    w3 = _get_w3()
    wallet, _ = _get_wallet_and_account()
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS["xfish_token"]),
        abi=ERC20_ABI,
    )
    decimals = contract.functions.decimals().call()
    balance = contract.functions.balanceOf(wallet["address"]).call()
    return balance / (10 ** decimals)


# ============================================================
# Daily Check-In
# ============================================================

def daily_checkin() -> dict:
    """Perform the daily on-chain check-in. Costs a small RON fee."""
    w3 = _get_w3()
    wallet, _ = _get_wallet_and_account()
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS["daily_checkin"]),
        abi=CHECKIN_ABI,
    )

    # Get the check-in price
    price = contract.functions.checkInPrice().call()

    # Build and send the transaction
    tx = contract.functions.checkIn().build_transaction({
        "value": price,
        "from": wallet["address"],
        "chainId": CHAIN_ID,
        "nonce": w3.eth.get_transaction_count(wallet["address"]),
        "gasPrice": w3.eth.gas_price,
    })
    tx_hash = _send_tx(w3, tx)

    return {
        "success": True,
        "tx_hash": tx_hash,
        "cost_ron": float(w3.from_wei(price, "ether")),
    }


# ============================================================
# Token Wheel Spin (Karma Wheel)
# ============================================================

SPIN_WHEEL_ABI = [
    {"inputs": [{"name": "callbackGasLimit", "type": "uint256"},
                {"name": "gasPriceToFulfill", "type": "uint256"}],
     "name": "spin", "outputs": [], "stateMutability": "payable", "type": "function"},
]

VRF_COORDINATOR_ABI = [
    {"inputs": [{"name": "callbackGasLimit", "type": "uint256"},
                {"name": "gasPrice", "type": "uint256"}],
     "name": "estimateRequestRandomFee",
     "outputs": [{"type": "uint256"}],
     "stateMutability": "view", "type": "function"},
]


def spin_token_wheel() -> dict:
    """Spin the karma/token wheel on-chain, then validate with the API.

    Requires karma >= 120,000 and 2,000+ daily quest points.
    Costs a small RON fee for VRF randomness.

    Returns:
        {"success": True, "tx_hash": "0x...", "cost_ron": 0.12,
         "api_result": {...}}
    """
    w3 = _get_w3()
    wallet, _ = _get_wallet_and_account()

    # Step 1: Calculate VRF fee
    block = w3.eth.get_block("latest")
    base_fee = block.get("baseFeePerGas", w3.eth.gas_price)
    gas_price_to_fulfill = base_fee * 2 + w3.to_wei(20, "gwei")
    callback_gas_limit = 300000

    vrf = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS["vrf_coordinator"]),
        abi=VRF_COORDINATOR_ABI,
    )
    msg_value = vrf.functions.estimateRequestRandomFee(
        callback_gas_limit, gas_price_to_fulfill
    ).call()

    # Step 2: Call spin() on the wheel contract
    spin_contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS["spin_wheel"]),
        abi=SPIN_WHEEL_ABI,
    )
    tx = spin_contract.functions.spin(
        callback_gas_limit, gas_price_to_fulfill
    ).build_transaction({
        "value": msg_value,
        "from": wallet["address"],
        "chainId": CHAIN_ID,
        "nonce": w3.eth.get_transaction_count(wallet["address"]),
        "gasPrice": w3.eth.gas_price,
    })
    tx_hash = _send_tx(w3, tx)
    tx_hash_hex = f"0x{tx_hash}"

    # Step 3: Submit to API for validation + reward
    import httpx
    from . import auth
    headers = {
        "Authorization": f"Bearer {auth.get_token()}",
        "Content-Type": "application/json",
        "Origin": "https://fishingfrenzy.co",
        "Referer": "https://fishingfrenzy.co/",
    }
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{api.BASE_URL}/user-quests/daily-quest/wheel/spin",
            headers=headers,
            json={"wheelType": "Token", "transactionHash": tx_hash_hex},
        )
        api_result = resp.json()

    return {
        "success": resp.status_code == 200,
        "tx_hash": tx_hash_hex,
        "cost_ron": float(w3.from_wei(msg_value, "ether")),
        "api_result": api_result,
    }


# ============================================================
# Chest Minting
# ============================================================

def mint_chests(user_chest_token_ids: list[str]) -> dict:
    """Mint in-game chests as NFTs on-chain (withdraw to wallet).

    1. Request mint signatures from the game server
    2. Call mintBatchChestWithSignature on the chest factory contract

    Args:
        user_chest_token_ids: List of userItemIds from the inventory.

    Returns:
        Dict with tx_hash, minted chest count, and the on-chain chestTokenIds.
    """
    # Step 1: Get server signature for minting
    sig_response = api._request(
        "POST", "/trading/chest-mint-signatures",
        json={"userChestTokenIds": user_chest_token_ids},
    )

    if isinstance(sig_response, dict) and sig_response.get("code") in (400, 404):
        raise RuntimeError(sig_response.get("message", "Failed to get mint signatures"))

    # Extract signature data from response
    data = sig_response.get("data", sig_response)
    chest_token_ids = data.get("chestTokenIds", [])
    tier_ids = data.get("tierIds", [])
    quantities = data.get("quantities", [1] * len(user_chest_token_ids))
    nonce = data.get("nonce")
    deadline = data.get("deadline")
    signature = data.get("signature")

    if not signature or deadline is None or nonce is None:
        raise RuntimeError(f"Invalid mint signature response: {sig_response}")

    # Step 2: Call the on-chain mint function
    w3 = _get_w3()
    wallet, _ = _get_wallet_and_account()
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS["chest_factory"]),
        abi=CHEST_FACTORY_ABI,
    )

    tx = contract.functions.mintBatchChestWithSignature(
        chest_token_ids,
        tier_ids,
        quantities,
        nonce,
        deadline,
        bytes.fromhex(signature.replace("0x", "")),
    ).build_transaction({})

    tx_hash = _send_tx(w3, tx)

    return {
        "success": True,
        "tx_hash": tx_hash,
        "chests_minted": len(user_chest_token_ids),
        "chest_token_ids": chest_token_ids,
    }


def open_chests_onchain(chest_token_ids: list[int]) -> dict:
    """Open chests on-chain via the chest factory contract.

    1. Call openBatchChest(tokenIds) on the chest factory
    2. Notify the game server with the tx hash

    Args:
        chest_token_ids: List of chest NFT token IDs to open.

    Returns:
        Dict with tx_hash and API rewards response.
    """
    w3 = _get_w3()
    wallet, _ = _get_wallet_and_account()
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS["chest_factory"]),
        abi=CHEST_FACTORY_ABI,
    )

    tx = contract.functions.openBatchChest(
        chest_token_ids,
    ).build_transaction({})

    tx_hash = _send_tx(w3, tx)
    tx_hash_hex = f"0x{tx_hash}" if not tx_hash.startswith("0x") else tx_hash

    # Notify game server about the opened chests
    import httpx
    from . import auth
    headers = {
        "Authorization": f"Bearer {auth.get_token()}",
        "Content-Type": "application/json",
        "Origin": "https://fishingfrenzy.co",
        "Referer": "https://fishingfrenzy.co/",
    }
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{api.BASE_URL}/trading/open-nft-chest",
            headers=headers,
            json={"transactionHash": tx_hash_hex},
        )
        api_result = resp.json()

    return {
        "success": resp.status_code == 200,
        "tx_hash": tx_hash_hex,
        "chests_opened": len(chest_token_ids),
        "api_result": api_result,
    }


# ============================================================
# FISH Staking
# ============================================================

def stake_fish(amount: float, duration_months: int) -> dict:
    """Stake FISH tokens for Karma.

    Args:
        amount: Amount of FISH to stake (human-readable, e.g. 100.0).
        duration_months: Staking duration in months (1, 3, 6, or 12).

    Returns:
        Dict with tx_hash and staking details.
    """
    w3 = _get_w3()
    wallet, _ = _get_wallet_and_account()

    fish_address = Web3.to_checksum_address(CONTRACTS["fish_token"])
    stake_address = Web3.to_checksum_address(CONTRACTS["stake"])

    fish_contract = w3.eth.contract(address=fish_address, abi=ERC20_ABI)
    stake_contract = w3.eth.contract(address=stake_address, abi=STAKE_ABI)

    decimals = fish_contract.functions.decimals().call()
    amount_wei = int(amount * (10 ** decimals))
    duration_secs = duration_months * 30 * 24 * 3600

    # Check balance
    balance = fish_contract.functions.balanceOf(wallet["address"]).call()
    if balance < amount_wei:
        raise RuntimeError(
            f"Insufficient FISH balance: have {balance / 10**decimals:.2f}, "
            f"need {amount:.2f}"
        )

    # Step 1: Approve FISH spending if needed
    allowance = fish_contract.functions.allowance(
        wallet["address"], stake_address
    ).call()

    tx_defaults = {
        "from": wallet["address"],
        "chainId": CHAIN_ID,
        "gasPrice": w3.eth.gas_price,
    }

    if allowance < amount_wei:
        approve_tx = fish_contract.functions.approve(
            stake_address, amount_wei
        ).build_transaction({
            **tx_defaults,
            "nonce": w3.eth.get_transaction_count(wallet["address"]),
        })
        _send_tx(w3, approve_tx)

    # Step 2: Stake
    stake_tx = stake_contract.functions.stakeERC20(
        fish_address, amount_wei, duration_secs
    ).build_transaction({
        **tx_defaults,
        "nonce": w3.eth.get_transaction_count(wallet["address"]),
    })
    tx_hash = _send_tx(w3, stake_tx)

    return {
        "success": True,
        "tx_hash": tx_hash,
        "amount": amount,
        "duration_months": duration_months,
        "duration_seconds": duration_secs,
    }


# ============================================================
# Katana DEX — RON → FISH Swap (V3 via AggregateRouter)
# ============================================================

AGGREGATE_ROUTER = "0x5f0acdd3ec767514ff1bf7e79949640bf94576bd"
V3_FACTORY_PROXY = "0x1f0B70d9A137e3cAEF0ceAcD312BC5f81Da0cC0c"
QUOTER_V2 = "0x84Ab2f9Fdc4Bf66312b0819D879437b8749EfDf2"

# V3 multi-hop path: WRON -(fee 100)-> USDC -(fee 3000)-> FISH
# Encodes as: token(20 bytes) + fee(3 bytes) + token(20 bytes) + fee(3 bytes) + token(20 bytes)
_V3_SWAP_PATH = (
    bytes.fromhex(WRON[2:])
    + (100).to_bytes(3, "big")
    + bytes.fromhex(CONTRACTS["usdc"][2:])
    + (3000).to_bytes(3, "big")
    + bytes.fromhex(CONTRACTS["fish_token"][2:])
)

# AggregateRouter command constants
_CMD_WRAP_ETH = 0x0b
_CMD_V3_SWAP_EXACT_IN = 0x00
_CMD_SWEEP = 0x04

# Sentinel addresses used by the AggregateRouter
_ROUTER_AS_RECIPIENT = "0x0000000000000000000000000000000000000002"
_MSG_SENDER = "0x0000000000000000000000000000000000000001"

AGGREGATE_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "commands", "type": "bytes"},
            {"name": "inputs", "type": "bytes[]"},
            {"name": "deadline", "type": "uint256"},
        ],
        "name": "execute",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
]

QUOTER_V2_ABI = [
    {
        "inputs": [
            {"name": "path", "type": "bytes"},
            {"name": "amountIn", "type": "uint256"},
        ],
        "name": "quoteExactInput",
        "outputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "sqrtPriceX96AfterList", "type": "uint160[]"},
            {"name": "initializedTicksCrossedList", "type": "uint32[]"},
            {"name": "gasEstimate", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


def get_fish_quote(ron_amount: float) -> dict:
    """Get an on-chain quote for swapping RON → FISH via Katana V3.

    Uses the multi-hop route: WRON → USDC (fee 100) → FISH (fee 3000)
    via the QuoterV2 contract for accurate pricing.

    Args:
        ron_amount: Amount of RON to swap (human-readable, e.g. 50.0).

    Returns:
        Dict with ron_in, fish_out, and price_per_fish.
    """
    w3 = _get_w3()
    quoter = w3.eth.contract(
        address=Web3.to_checksum_address(QUOTER_V2),
        abi=QUOTER_V2_ABI,
    )
    amount_in_wei = w3.to_wei(ron_amount, "ether")
    result = quoter.functions.quoteExactInput(_V3_SWAP_PATH, amount_in_wei).call()
    fish_out = float(w3.from_wei(result[0], "ether"))
    price_per_fish = ron_amount / fish_out if fish_out > 0 else 0
    return {
        "ron_in": ron_amount,
        "fish_out": round(fish_out, 2),
        "price_per_fish": round(price_per_fish, 6),
    }


def buy_fish_with_ron(ron_amount: float, slippage_pct: float = 1.0) -> dict:
    """Swap RON → FISH via Katana V3 AggregateRouter.

    Uses the multi-hop route: RON → WRON → USDC → FISH
    Executed as three commands via the AggregateRouter:
      1. WRAP_ETH — wrap RON to WRON
      2. V3_SWAP_EXACT_IN — swap WRON��USDC→FISH via V3 pools
      3. SWEEP — send remaining FISH to the caller

    Args:
        ron_amount: Amount of RON to spend.
        slippage_pct: Slippage tolerance in percent (default 1%).

    Returns:
        Dict with success, tx_hash, ron_spent, fish_received.
    """
    w3 = _get_w3()
    wallet, account = _get_wallet_and_account()

    amount_in_wei = w3.to_wei(ron_amount, "ether")

    # Get V3 quote for min output
    quoter = w3.eth.contract(
        address=Web3.to_checksum_address(QUOTER_V2),
        abi=QUOTER_V2_ABI,
    )
    quote_result = quoter.functions.quoteExactInput(_V3_SWAP_PATH, amount_in_wei).call()
    expected_fish_wei = quote_result[0]
    min_fish_wei = int(expected_fish_wei * (100 - slippage_pct) / 100)

    deadline = int(time.time()) + 300  # 5 minutes

    # Build AggregateRouter commands:
    # Cmd 1: WRAP_ETH — wrap RON into WRON inside the router
    #   abi.encode(address recipient, uint256 amountMin)
    wrap_input = w3.codec.encode(
        ["address", "uint256"],
        [Web3.to_checksum_address(_ROUTER_AS_RECIPIENT), amount_in_wei],
    )

    # Cmd 2: V3_SWAP_EXACT_IN — multi-hop swap through V3 pools
    #   abi.encode(address recipient, uint256 amountIn, uint256 amountOutMin, bytes path, bool payerIsUser)
    swap_input = w3.codec.encode(
        ["address", "uint256", "uint256", "bytes", "bool"],
        [
            Web3.to_checksum_address(_ROUTER_AS_RECIPIENT),
            amount_in_wei,
            min_fish_wei,
            _V3_SWAP_PATH,
            False,  # payer is router (has the WRON from wrap)
        ],
    )

    # Cmd 3: SWEEP — send all FISH from router to caller
    #   abi.encode(address token, address recipient, uint256 amountMin)
    sweep_input = w3.codec.encode(
        ["address", "address", "uint256"],
        [
            Web3.to_checksum_address(CONTRACTS["fish_token"]),
            Web3.to_checksum_address(_MSG_SENDER),
            min_fish_wei,
        ],
    )

    commands = bytes([_CMD_WRAP_ETH, _CMD_V3_SWAP_EXACT_IN, _CMD_SWEEP])
    inputs = [wrap_input, swap_input, sweep_input]

    router = w3.eth.contract(
        address=Web3.to_checksum_address(AGGREGATE_ROUTER),
        abi=AGGREGATE_ROUTER_ABI,
    )

    tx = router.functions.execute(commands, inputs, deadline).build_transaction({
        "value": amount_in_wei,
        "from": account.address,
        "chainId": CHAIN_ID,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.eth.gas_price,
    })

    tx_hash = _send_tx(w3, tx)

    fish_received = float(w3.from_wei(expected_fish_wei, "ether"))
    return {
        "success": True,
        "tx_hash": tx_hash,
        "ron_spent": ron_amount,
        "fish_received": round(fish_received, 2),
    }


# ============================================================
# CoinGecko Price Helper
# ============================================================

def get_deposit_recommendation(fish_target: int = 10000, gas_buffer: float = 5.0) -> dict:
    """Calculate how much RON to deposit for buying FISH + gas fees.

    Fetches live RON and FISH prices from CoinGecko, then calculates
    the total RON needed to buy fish_target FISH plus a gas buffer.

    Args:
        fish_target: Number of FISH tokens to buy (default 10,000).
        gas_buffer: Extra RON to reserve for gas fees (default 5.0).

    Returns:
        Dict with recommended_ron, prices, and breakdown.
    """
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ronin,fishing-frenzy&vs_currencies=usd"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = _json.loads(resp.read())

    ron_usd = data.get("ronin", {}).get("usd", 0)
    fish_usd = data.get("fishing-frenzy", {}).get("usd", 0)

    if ron_usd <= 0 or fish_usd <= 0:
        raise RuntimeError(f"Failed to fetch prices: RON=${ron_usd}, FISH=${fish_usd}")

    ron_for_fish = (fish_target * fish_usd) / ron_usd
    import math
    recommended_ron = math.ceil(ron_for_fish + gas_buffer)

    return {
        "recommended_ron": recommended_ron,
        "fish_target": fish_target,
        "fish_price_usd": fish_usd,
        "ron_price_usd": ron_usd,
        "gas_buffer": gas_buffer,
        "ron_for_fish": round(ron_for_fish, 1),
        "breakdown": f"~{round(ron_for_fish)} RON for {fish_target:,} FISH + ~{gas_buffer:.0f} RON for gas",
    }
