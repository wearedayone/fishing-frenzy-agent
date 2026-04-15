"""WebSocket-based diving client for Fishing Frenzy.

The diving minigame uses a WebSocket connection:
1. Connect to wss://ssc-prd.fishingfrenzy.co?token=<JWT>&gameType=diving
2. Send {"cmd": "new_dive"} to start
3. Receive board via {"type": "init_diving"}
4. Select cells via {"cmd": "select", "col": X, "row": Y}
5. Receive results via {"type": "select_response"}
6. Cash out via {"cmd": "endgame"} or game ends when result is found
"""

import asyncio
import json
import random

import websockets

WS_URL = "wss://ssc-prd.fishingfrenzy.co"
WS_BAD_REQUEST = 400


def dive_session(token: str, max_picks: int = 0) -> dict:
    """Execute one complete diving session via WebSocket.

    This handles ONLY the WebSocket gameplay portion. The caller must
    have already purchased + used a ticket and called start_diving().

    Args:
        token: JWT access token.
        max_picks: Max cells to reveal before cashing out (0 = play until game over).

    Returns:
        Dict with success, rewards collected, cells revealed, board data.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already in async context — create a new thread to avoid nesting
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                asyncio.run, _dive_session_async(token, max_picks)
            ).result()
    else:
        return asyncio.run(_dive_session_async(token, max_picks))


async def _dive_session_async(token: str, max_picks: int = 0) -> dict:
    """Async implementation of a diving session."""
    url = f"{WS_URL}?token={token}&gameType=diving"
    headers = {
        "Origin": "https://fishingfrenzy.co",
        "User-Agent": "Mozilla/5.0 (compatible; FishingFrenzyAgent/1.0)",
    }

    try:
        async with websockets.connect(
            url, additional_headers=headers, close_timeout=5
        ) as ws:
            # Send new_dive to start
            await ws.send(json.dumps({"cmd": "new_dive"}))

            # Wait for init_diving response
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))

            if msg.get("status") == WS_BAD_REQUEST:
                return {"success": False, "error": msg.get("message", "Bad request")}

            if msg.get("type") != "init_diving":
                return {"success": False, "error": f"Unexpected response: {msg.get('type')}"}

            board_data = msg.get("data", {})
            board_size = _get_board_size(board_data)
            cols, rows = board_size

            # Build list of all selectable cells
            all_cells = [(c, r) for c in range(cols) for r in range(rows)]
            random.shuffle(all_cells)

            revealed = []
            rewards = []
            game_over = False
            picks_made = 0

            # Select cells one by one
            for col, row in all_cells:
                if game_over:
                    break
                if max_picks > 0 and picks_made >= max_picks:
                    break

                await asyncio.sleep(random.uniform(0.5, 1.5))
                await ws.send(json.dumps({"cmd": "select", "col": col, "row": row}))

                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))

                if resp.get("status") == WS_BAD_REQUEST:
                    break

                if resp.get("type") == "select_response":
                    cell_data = resp.get("data", {})
                    revealed.append({"col": col, "row": row, "data": cell_data})
                    picks_made += 1

                    # Check if this cell had a reward
                    if cell_data.get("reward"):
                        rewards.append(cell_data["reward"])

                    # data.result truthy = game over (found the main prize or all revealed)
                    if cell_data.get("result"):
                        game_over = True

            # If we stopped early (max_picks reached), cash out
            if not game_over:
                await ws.send(json.dumps({"cmd": "endgame"}))
                end_resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))

                if end_resp.get("type") == "endgame_response":
                    return {
                        "success": True,
                        "cashed_out_early": True,
                        "cells_revealed": picks_made,
                        "board_size": f"{cols}x{rows}",
                        "rewards": rewards,
                        "endgame_rewards": end_resp.get("data"),
                        "full_board": end_resp.get("board"),
                    }

            # Game ended naturally
            return {
                "success": True,
                "cashed_out_early": False,
                "cells_revealed": picks_made,
                "board_size": f"{cols}x{rows}",
                "rewards": rewards,
                "revealed_cells": revealed,
            }

    except websockets.ConnectionClosed as e:
        if e.code == 4000:
            return {"success": False, "error": "Disconnected by server"}
        return {"success": False, "error": f"Connection closed: {e.code} {e.reason}"}
    except asyncio.TimeoutError:
        return {"success": False, "error": "WebSocket timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_board_size(board_data: dict) -> tuple[int, int]:
    """Extract board dimensions from init_diving data.

    Falls back to 5x5 if dimensions can't be determined.
    """
    # Try common field names for board dimensions
    cols = board_data.get("cols") or board_data.get("width") or board_data.get("col")
    rows = board_data.get("rows") or board_data.get("height") or board_data.get("row")

    if cols and rows:
        return (int(cols), int(rows))

    # Try to infer from board/cells array
    cells = board_data.get("board") or board_data.get("cells") or []
    if isinstance(cells, list) and cells:
        if isinstance(cells[0], list):
            return (len(cells), len(cells[0]))
        # Flat array — assume square
        import math
        side = int(math.sqrt(len(cells)))
        if side * side == len(cells):
            return (side, side)

    # Default fallback
    return (5, 5)
