"""Privy SIWE authentication and JWT management for Fishing Frenzy Agent."""

import uuid
import httpx

from . import state
from . import wallet

PRIVY_APP_ID = "cm06k1f5p00obmoff19qdgri4"
PRIVY_CA_ID = "c7c9d8b2-eeef-4eef-816b-4733cf63ad0c"
PRIVY_CLIENT = "react-auth:1.88.4"
GAME_API = "https://api.fishingfrenzy.co"

CHAIN_ID = 2020  # Ronin
AGENT_VERSION = "1.0.0"


def _privy_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Origin": "https://fishingfrenzy.co",
        "Referer": "https://fishingfrenzy.co/",
        "privy-app-id": PRIVY_APP_ID,
        "privy-ca-id": PRIVY_CA_ID,
        "privy-client": PRIVY_CLIENT,
    }


def setup_account() -> dict:
    """Create wallet + authenticate + register guest account. Full first-run setup."""
    # Step 1: Create wallet if needed
    wallet_result = wallet.create_wallet()
    address = wallet_result["address"]

    # Step 2: Authenticate via SIWE
    auth_result = authenticate()

    return {
        "wallet_address": address,
        "wallet_created": wallet_result["created"],
        "user_id": auth_result["user_id"],
        "authenticated": True,
    }


def authenticate() -> dict:
    """Full SIWE flow: nonce → sign → Privy auth → game login."""
    address = wallet.get_address()
    if not address:
        raise RuntimeError("No wallet found. Call setup_account() first.")

    return _authenticate_with_chain(address, CHAIN_ID)


def _authenticate_with_chain(address: str, chain_id: int) -> dict:
    """Attempt SIWE auth with a specific chain ID."""
    with httpx.Client(timeout=30) as client:
        # Step 1: Request nonce from Privy
        resp = client.post(
            "https://auth.privy.io/api/v1/siwe/init",
            json={"address": address},
            headers=_privy_headers(),
        )
        if resp.status_code != 200:
            raise AuthError(f"Nonce request failed: {resp.status_code} {resp.text}")
        nonce = resp.json()["nonce"]

        # Step 2: Sign SIWE message
        message, signature = wallet.sign_siwe_message(nonce, chain_id=chain_id)

        # Step 3: Authenticate with Privy
        resp = client.post(
            "https://auth.privy.io/api/v1/siwe/authenticate",
            json={
                "message": message,
                "signature": signature,
                "chainId": f"eip155:{chain_id}",
                "walletClientType": "metamask",
                "connectorType": "injected",
                "mode": "login-or-sign-up",
            },
            headers=_privy_headers(),
        )
        if resp.status_code != 200:
            raise AuthError(
                f"Privy auth failed (chain {chain_id}): {resp.status_code} {resp.text}"
            )

        privy_data = resp.json()
        privy_token = privy_data.get("token")
        if not privy_token:
            raise AuthError(f"No token in Privy response: {privy_data}")

        # Step 4: Exchange Privy token for game JWT
        resp = client.post(
            f"{GAME_API}/v1/auth/login",
            json={
                "deviceId": str(uuid.uuid4()),
                "teleUserId": None,
                "teleName": None,
                "agentMetadata": {
                    "type": "claude-code-skill",
                    "version": AGENT_VERSION,
                    "skill": "fishing-frenzy-agent",
                },
            },
            headers={
                "Content-Type": "application/json",
                "Origin": "https://fishingfrenzy.co",
                "Referer": "https://fishingfrenzy.co/",
                "x-privy-token": privy_token,
            },
        )
        if resp.status_code != 200:
            raise AuthError(f"Game login failed: {resp.status_code} {resp.text}")

        data = resp.json()
        tokens = data.get("tokens", {})
        access_token = tokens.get("access", {}).get("token")
        refresh_token = tokens.get("refresh", {}).get("token")
        user = data.get("user", {})
        user_id = user.get("id")

        if not access_token or not user_id:
            raise AuthError(f"Incomplete login response: {data}")

        # Persist everything
        state.save_auth(access_token, refresh_token, user_id, privy_token)

        return {
            "user_id": user_id,
            "wallet_address": address,
            "chain_id": chain_id,
        }


def login() -> dict:
    """Ensure we have a valid auth token. Refreshes if expired."""
    access = state.get_auth("access_token")
    if access:
        return {
            "authenticated": True,
            "user_id": state.get_auth("user_id"),
            "token_status": "valid",
        }

    # Try refresh first
    refresh = state.get_auth("refresh_token")
    if refresh:
        try:
            return refresh_tokens()
        except AuthError:
            pass

    # Full re-auth needed
    return authenticate()


def refresh_tokens() -> dict:
    """Refresh the game JWT using the refresh token."""
    refresh = state.get_auth("refresh_token")
    if not refresh:
        raise AuthError("No refresh token available")

    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{GAME_API}/v1/auth/refresh-tokens",
            json={"refreshToken": refresh},
            headers={
                "Content-Type": "application/json",
                "Origin": "https://fishingfrenzy.co",
            },
        )

        if resp.status_code != 200:
            raise AuthError(f"Token refresh failed: {resp.status_code}")

        data = resp.json()
        tokens = data.get("tokens", data)
        access_token = tokens.get("access", {}).get("token")
        refresh_token = tokens.get("refresh", {}).get("token")
        user_id = state.get_auth("user_id")

        if access_token:
            state.save_auth(access_token, refresh_token or refresh, user_id)
            return {
                "authenticated": True,
                "user_id": user_id,
                "token_status": "refreshed",
            }

        raise AuthError("No access token in refresh response")


def get_token() -> str:
    """Get a valid access token, refreshing if needed."""
    access = state.get_auth("access_token")
    if access:
        return access
    login()
    access = state.get_auth("access_token")
    if not access:
        raise AuthError("Failed to obtain access token")
    return access


class AuthError(Exception):
    """Authentication-related errors."""
    pass
