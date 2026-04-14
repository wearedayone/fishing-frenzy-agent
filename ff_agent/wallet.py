"""Ethereum wallet generation and SIWE message signing for Fishing Frenzy Agent."""

from datetime import datetime, timezone
from eth_account import Account
from eth_account.messages import encode_defunct

from . import state


def create_wallet() -> dict:
    """Generate a new Ethereum wallet and persist it."""
    existing = state.get_wallet()
    if existing:
        return {"address": existing["address"], "created": False}

    account = Account.create()
    address = account.address
    private_key = account.key.hex()
    state.save_wallet(address, private_key)
    return {"address": address, "created": True}


def get_wallet() -> dict | None:
    """Retrieve the stored wallet."""
    return state.get_wallet()


def sign_siwe_message(nonce: str, chain_id: int = 2020) -> tuple[str, str]:
    """Construct and sign a SIWE message.

    Args:
        nonce: The nonce from Privy's /siwe/init endpoint.
        chain_id: The chain ID for the SIWE message (2020 for Ronin).

    Returns:
        Tuple of (message, signature) where signature is hex-encoded with 0x prefix.
    """
    wallet = state.get_wallet()
    if not wallet:
        raise RuntimeError("No wallet found. Call create_wallet() first.")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    message = (
        f"fishingfrenzy.co wants you to sign in with your Ethereum account:\n"
        f"{wallet['address']}\n\n"
        f"By signing, you are proving you own this wallet and logging in. "
        f"This does not initiate a transaction or cost any fees.\n\n"
        f"URI: https://fishingfrenzy.co\n"
        f"Version: 1\n"
        f"Chain ID: {chain_id}\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {now}\n"
        f"Resources:\n"
        f"- https://privy.io"
    )

    account = Account.from_key(wallet["private_key"])
    signed = account.sign_message(encode_defunct(text=message))
    signature = "0x" + signed.signature.hex()

    return message, signature


def get_address() -> str | None:
    """Get the wallet address if one exists."""
    wallet = state.get_wallet()
    return wallet["address"] if wallet else None
