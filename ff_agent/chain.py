"""On-chain Ronin blockchain interactions for Fishing Frenzy Agent."""

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

CHEST_FACTORY_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "tokenIds", "type": "uint256[]"},
            {"name": "amounts", "type": "uint256[]"},
            {"name": "deadline", "type": "uint256"},
            {"name": "signature", "type": "bytes"},
        ],
        "name": "mintBatchChestWithSignature",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


def _get_w3() -> Web3:
    """Get a Web3 instance connected to Ronin RPC."""
    w3 = Web3(Web3.HTTPProvider(RONIN_RPC))
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
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS["daily_checkin"]),
        abi=CHECKIN_ABI,
    )

    # Get the check-in price
    price = contract.functions.checkInPrice().call()

    # Build and send the transaction
    tx = contract.functions.checkIn().build_transaction({
        "value": price,
    })
    tx_hash = _send_tx(w3, tx)

    return {
        "success": True,
        "tx_hash": tx_hash,
        "cost_ron": float(w3.from_wei(price, "ether")),
    }


# ============================================================
# Chest Minting
# ============================================================

def mint_chests(chest_token_ids: list[int]) -> dict:
    """Mint leaderboard chests on-chain.

    1. Request mint signatures from the game server
    2. Call mintBatchChestWithSignature on the chest factory contract

    Args:
        chest_token_ids: List of chest token IDs to mint.

    Returns:
        Dict with tx_hash and minted chest count.
    """
    # Step 1: Get server signature for minting
    sig_response = api._request(
        "POST", "/trading/chest-mint-signatures",
        json={"chestTokenIds": chest_token_ids},
    )

    if isinstance(sig_response, dict) and sig_response.get("code") in (400, 404):
        raise RuntimeError(sig_response.get("message", "Failed to get mint signatures"))

    # Extract signature data from response
    data = sig_response.get("data", sig_response)
    signature = data.get("signature")
    deadline = data.get("deadline")
    amounts = data.get("amounts", [1] * len(chest_token_ids))

    if not signature or not deadline:
        raise RuntimeError(f"Invalid mint signature response: {sig_response}")

    # Step 2: Call the on-chain mint function
    w3 = _get_w3()
    wallet, _ = _get_wallet_and_account()
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS["chest_factory"]),
        abi=CHEST_FACTORY_ABI,
    )

    tx = contract.functions.mintBatchChestWithSignature(
        wallet["address"],
        chest_token_ids,
        amounts,
        deadline,
        bytes.fromhex(signature.replace("0x", "")),
    ).build_transaction({})

    tx_hash = _send_tx(w3, tx)

    return {
        "success": True,
        "tx_hash": tx_hash,
        "chests_minted": len(chest_token_ids),
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

    if allowance < amount_wei:
        approve_tx = fish_contract.functions.approve(
            stake_address, amount_wei
        ).build_transaction({})
        _send_tx(w3, approve_tx)

    # Step 2: Stake
    stake_tx = stake_contract.functions.stakeERC20(
        fish_address, amount_wei, duration_secs
    ).build_transaction({})
    tx_hash = _send_tx(w3, stake_tx)

    return {
        "success": True,
        "tx_hash": tx_hash,
        "amount": amount,
        "duration_months": duration_months,
        "duration_seconds": duration_secs,
    }
