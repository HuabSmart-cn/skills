#!/usr/bin/env python3
"""
evm_client.py — EVM blockchain CLI tool for the Hermes Agent project.
Zero external dependencies. Uses stdlib only: urllib, json, argparse, time, os, sys, typing.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Chain registry
# ---------------------------------------------------------------------------

CHAINS: Dict[str, Dict[str, Any]] = {
    "ethereum": {
        "chain_id": 1,
        "rpc": "https://ethereum-rpc.publicnode.com",
        "native": "ETH",
        "coingecko": "ethereum",
        "explorer": "https://etherscan.io",
        "decimals": 18,
    },
    "bsc": {
        "chain_id": 56,
        "rpc": "https://bsc-dataseed1.binance.org",
        "native": "BNB",
        "coingecko": "binancecoin",
        "explorer": "https://bscscan.com",
        "decimals": 18,
    },
    "base": {
        "chain_id": 8453,
        "rpc": "https://mainnet.base.org",
        "native": "ETH",
        "coingecko": "ethereum",
        "explorer": "https://basescan.org",
        "decimals": 18,
    },
    "arbitrum": {
        "chain_id": 42161,
        "rpc": "https://arb1.arbitrum.io/rpc",
        "native": "ETH",
        "coingecko": "ethereum",
        "explorer": "https://arbiscan.io",
        "decimals": 18,
    },
    "polygon": {
        "chain_id": 137,
        "rpc": "https://polygon-rpc.com",
        "native": "MATIC",
        "coingecko": "matic-network",
        "explorer": "https://polygonscan.com",
        "decimals": 18,
    },
    "optimism": {
        "chain_id": 10,
        "rpc": "https://mainnet.optimism.io",
        "native": "ETH",
        "coingecko": "ethereum",
        "explorer": "https://optimistic.etherscan.io",
        "decimals": 18,
    },
    "avalanche": {
        "chain_id": 43114,
        "rpc": "https://api.avax.network/ext/bc/C/rpc",
        "native": "AVAX",
        "coingecko": "avalanche-2",
        "explorer": "https://snowtrace.io",
        "decimals": 18,
    },
    "zksync": {
        "chain_id": 324,
        "rpc": "https://mainnet.era.zksync.io",
        "native": "ETH",
        "coingecko": "ethereum",
        "explorer": "https://explorer.zksync.io",
        "decimals": 18,
    },
}

DEFAULT_CHAIN = "ethereum"

# ---------------------------------------------------------------------------
# Known ERC-20 token registry  {chain -> {symbol -> address}}
# ---------------------------------------------------------------------------

KNOWN_TOKENS: ***REDACTED***
    "ethereum": {
        "USDT":  "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "USDC":  "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "DAI":   "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "WETH":  "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "WBTC":  "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "LINK":  "0x514910771AF9Ca656af840dff83E8264EcF986CA",
        "UNI":   "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "AAVE":  "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
        "MKR":   "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
        "COMP":  "0xc00e94Cb662C3520282E6f5717214004A7f26888",
        "SNX":   "0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F",
        "CRV":   "0xD533a949740bb3306d119CC777fa900bA034cd52",
        "LDO":   "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32",
        "RPL":   "0xD33526068D116cE69F19A9ee46F0bd304F21A51f",
        "MATIC": "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0",
        "SHIB":  "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",
        "APE":   "0x4d224452801ACEd8B2F0aebE155379bb5D594381",
        "GRT":   "0xc944E90C64B2c07662A292be6244BDf05Cda44a7",
        "FXS":   "0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0",
        "FRAX":  "0x853d955aCEf822Db058eb8505911ED77F175b99e",
        "BAL":   "0xba100000625a3754423978a60c9317c58a424e3D",
        "SUSHI": "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2",
        "YFI":   "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
        "1INCH": "0x111111111117dC0aa78b770fA6A738034120C302",
        "ENS":   "0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72",
        "IMX":   "0xF57e7e7C23978C3cAEC3C3548E3D615c346e79fF",
        "SAND":  "0x3845badAde8e6dFF049820680d1F14bD3903a5d0",
        "MANA":  "0x0F5D2fB29fb7d3CFeE444a200298f468908cC942",
        "AXS":   "0xBB0E17EF65F82Ab018d8EDd776e8DD940327B28b",
        "CHZ":   "0x3506424F91fD33084466F402d5D97f05F8e3b4AF",
        "PEPE":  "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
    },
    "bsc": {
        "USDT":  "0x55d398326f99059fF775485246999027B3197955",
        "USDC":  "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
        "BUSD":  "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
        "WBNB":  "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "CAKE":  "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
        "XVS":   "0xcF6BB5389c92Bdda8a3747Ddb454cB7a64626C63",
        "ALPACA":"0x8F0528cE5eF7B51152A59745bEfDD91D97091d2F",
        "BAKE":  "0xE02dF9e3e622DeBdD69fb838bB799E3F168902c5",
        "BURGER":"0xAe9269f27437f0fcBC232d39Ec814844a51d6b8f",
        "DOGE":  "0xbA2aE424d960c26247Dd6c32edC70B295c744C43",
    },
    "base": {
        # Stables + wrapped
        "USDC":   "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "DAI":    "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        "WETH":   "0x4200000000000000000000000000000000000006",
        # Liquid-staked ETH variants
        "cbETH":  "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cF0DEc22",
        "wstETH": "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452",
        "rETH":   "0xB6fe221Fe9EeF5aBa221c348bA20A1Bf5e73624c",
        "cbBTC":  "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
        # Base-native DeFi + meme tokens (carried over from the standalone base/ skill)
        "AERO":   "0x940181a94A35A4569E4529A3CDfB74e38FD98631",
        "DEGEN":  "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed",
        "TOSHI":  "0xAC1Bd2486aAf3B5C0fc3Fd868558b082a531B2B4",
        "BRETT":  "0x532f27101965dd16442E59d40670FaF5eBB142E4",
        "WELL":   "0xA88594D404727625A9437C3f886C7643872296AE",
    },
    "arbitrum": {
        "USDC":  "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "USDT":  "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "WETH":  "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "ARB":   "0x912CE59144191C1204E64559FE8253a0e49E6548",
    },
    "optimism": {
        "USDC":  "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
        "USDT":  "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
        "WETH":  "0x4200000000000000000000000000000000000006",
        "OP":    "0x4200000000000000000000000000000000000042",
    },
    "polygon": {
        "USDC":  "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "USDT":  "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "WMATIC":"0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "WETH":  "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        "DAI":   "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    },
    "avalanche": {
        "USDC":  "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
        "USDT":  "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",
        "WAVAX": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
    },
}

# Gas estimates (units) for common operations
GAS_ESTIMATES = {
    "transfer":     21_000,
    "erc20":        65_000,
    "approve":      46_000,
    "swap":        180_000,
    "nft_mint":    150_000,
    "nft_transfer": 85_000,
}

# CoinGecko symbol -> id map for common tokens
COINGECKO_IDS: Dict[str, str] = {
    "ETH":   "ethereum",
    "BTC":   "bitcoin",
    "BNB":   "binancecoin",
    "MATIC": "matic-network",
    "AVAX":  "avalanche-2",
    "USDT":  "tether",
    "USDC":  "usd-coin",
    "DAI":   "dai",
    "WBTC":  "wrapped-bitcoin",
    "WETH":  "weth",
    "LINK":  "chainlink",
    "UNI":   "uniswap",
    "AAVE":  "aave",
    "MKR":   "maker",
    "COMP":  "compound-governance-token",
    "SNX":   "havven",
    "CRV":   "curve-dao-token",
    "LDO":   "lido-dao",
    "RPL":   "rocket-pool",
    "SHIB":  "shiba-inu",
    "APE":   "apecoin",
    "GRT":   "the-graph",
    "BAL":   "balancer",
    "SUSHI": "sushi",
    "YFI":   "yearn-finance",
    "1INCH": "1inch",
    "ENS":   "ethereum-name-service",
    "IMX":   "immutable-x",
    "SAND":  "the-sandbox",
    "MANA":  "decentraland",
    "AXS":   "axie-infinity",
    "ARB":   "arbitrum",
    "OP":    "optimism",
    "CAKE":  "pancakeswap-token",
    "PEPE":  "pepe",
    "CHZ":   "chiliz",
}

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def hex_to_int(h: str) -> int:
    if not h or h == "0x":
        return 0
    return int(h, 16)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def is_valid_address(s: str) -> bool:
    """Return True if `s` looks like a 20-byte hex Ethereum address.

    Does NOT validate EIP-55 checksum — RPC endpoints accept any-case hex.
    Just guards against typos / wrong-length input before we burn an RPC call.
    """
    if not isinstance(s, str):
        return False
    if not s.startswith("0x") and not s.startswith("0X"):
        return False
    if len(s) != 42:
        return False
    try:
        int(s, 16)
    except ValueError:
        return False
    return True


def is_valid_txhash(s: str) -> bool:
    """Return True if `s` looks like a 32-byte hex transaction hash."""
    if not isinstance(s, str):
        return False
    if not s.startswith("0x") and not s.startswith("0X"):
        return False
    if len(s) != 66:
        return False
    try:
        int(s, 16)
    except ValueError:
        return False
    return True


def require_address(s: str, *, field: str = "address") -> str:
    """Return `s` lowercased if valid, else exit with an error message.

    Centralizing validation here means every subcommand fails fast on bad input
    instead of bubbling up an opaque RPC error 30 seconds later.
    """
    if not is_valid_address(s):
        sys.stderr.write(
            f"error: invalid {field} {s!r}: expected 0x-prefixed 40-hex-char address\n"
        )
        sys.exit(2)
    return s.lower()


def require_txhash(s: str, *, field: str = "tx hash") -> str:
    """Return `s` lowercased if valid, else exit with an error message."""
    if not is_valid_txhash(s):
        sys.stderr.write(
            f"error: invalid {field} {s!r}: expected 0x-prefixed 64-hex-char tx hash\n"
        )
        sys.exit(2)
    return s.lower()


def wei_to_native(wei: int, decimals: int = 18) -> float:
    return wei / (10 ** decimals)


def gwei_from_wei(wei: int) -> float:
    return wei / 1e9

def _short_addr(addr: str) -> str:
    if addr and len(addr) >= 10:
        return addr[:6] + "..." + addr[-4:]
    return addr or ""

def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))

# ---------------------------------------------------------------------------
# HTTP / JSON-RPC layer
# ---------------------------------------------------------------------------

def _http_post(url: str, payload: Any, retries: int = 5, timeout: int = 20) -> Any:
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Accept":       "application/json",
        "User-Agent":   "Mozilla/5.0 (compatible; evm_client/1.0)",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    delay = 1.0
    last_err: Exception = RuntimeError("No attempts made")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(delay)
                delay = min(delay * 2, 30)
                last_err = e
                continue
            body_text = ""
            try:
                body_text = e.read().decode()
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code}: {body_text}") from e
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(delay)
                delay = min(delay * 2, 30)
    raise RuntimeError(f"Request failed after {retries} retries: {last_err}") from last_err

def _http_get(url: str, retries: int = 5, timeout: int = 20) -> Any:
    headers = {"Accept": "application/json", "User-Agent": "evm_client/1.0"}
    req = urllib.request.Request(url, headers=headers, method="GET")
    delay = 1.0
    last_err: Exception = RuntimeError("No attempts made")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(delay)
                delay = min(delay * 2, 30)
                last_err = e
                continue
            body_text = ""
            try:
                body_text = e.read().decode()
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code}: {body_text}") from e
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(delay)
                delay = min(delay * 2, 30)
    raise RuntimeError(f"Request failed after {retries} retries: {last_err}") from last_err

# ---------------------------------------------------------------------------
# RPC helpers
# ---------------------------------------------------------------------------

def get_rpc_url(chain: str) -> str:
    env = os.environ.get("EVM_RPC_URL", "")
    if env:
        return env
    cfg = CHAINS.get(chain)
    if not cfg:
        raise ValueError(f"Unknown chain '{chain}'. Available: {', '.join(CHAINS)}")
    return cfg["rpc"]

def rpc_call(chain: str, method: str, params: List[Any], req_id: int = 1) -> Any:
    url = get_rpc_url(chain)
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    resp = _http_post(url, payload)
    if "error" in resp:
        raise RuntimeError(f"RPC error: {resp['error']}")
    return resp.get("result")

def rpc_batch(chain: str, calls: List[Tuple[str, List[Any]]], batch_limit: int = 10) -> List[Any]:
    """Send a batch of JSON-RPC calls; returns list of results in same order.

    Auto-chunks at `batch_limit` (default 10) so we stay under per-RPC limits.
    Base's public RPC caps batches at 10 — exceeding that returns a single error
    dict instead of a results list, which would mask all our calls.
    """
    url = get_rpc_url(chain)

    # Build the full payload, preserving order via JSON-RPC `id`
    items = [
        {"jsonrpc": "2.0", "id": i, "method": m, "params": p}
        for i, (m, p) in enumerate(calls)
    ]

    out: List[Any] = [None] * len(items)
    for start in range(0, len(items), batch_limit):
        chunk = items[start:start + batch_limit]
        resp = _http_post(url, chunk)
        if not isinstance(resp, list):
            # Single error response (e.g. batch-too-large) — leave this chunk as None
            continue
        for r in resp:
            rid = r.get("id")
            if isinstance(rid, int) and 0 <= rid < len(out):
                if "error" in r:
                    out[rid] = None
                else:
                    out[rid] = r.get("result")
    return out

# ---------------------------------------------------------------------------
# ABI encoding helpers (minimal, for ERC-20 calls)
# ---------------------------------------------------------------------------

def _encode_address(addr: str) -> str:
    """Pad address to 32 bytes."""
    return addr.lower().replace("0x", "").zfill(64)

def _keccak256(data: bytes) -> bytes:
    """Pure Python Keccak-256 (Ethereum's hash, NOT SHA3-256)."""
    # Keccak-256 round constants
    RC = [
        0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
        0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
        0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
        0x000000008000808B, 0x800000000000008B, 0x8000_0000_0000_8089, 0x8000000000008003,
        0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
        0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
    ]
    ROT = [
        [0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61],
        [28, 55, 25, 21, 56], [27, 20, 39, 8, 14],
    ]
    def rot64(x, n): return ((x << n) | (x >> (64 - n))) & 0xFFFFFFFFFFFFFFFF
    rate = 136  # 1088 bits for keccak-256
    # Padding
    msg = bytearray(data)
    msg.append(0x01)
    while len(msg) % rate != 0:
        msg.append(0x00)
    msg[-1] |= 0x80
    # Absorb
    state = [0] * 25
    for block_start in range(0, len(msg), rate):
        block = msg[block_start:block_start + rate]
        for i in range(rate // 8):
            state[i] ^= int.from_bytes(block[i*8:(i+1)*8], "little")
        # Keccak-f[1600]
        for rnd in range(24):
            # Theta
            C = [state[x] ^ state[x+5] ^ state[x+10] ^ state[x+15] ^ state[x+20] for x in range(5)]
            D = [C[(x-1) % 5] ^ rot64(C[(x+1) % 5], 1) for x in range(5)]
            state = [state[i] ^ D[i % 5] for i in range(25)]
            # Rho + Pi
            B = [0] * 25
            for x in range(5):
                for y in range(5):
                    B[y*5 + ((2*x+3*y) % 5)] = rot64(state[x + 5*y], ROT[x][y])
            # Chi
            state = [B[i] ^ ((~B[(i//5)*5 + (i%5+1)%5]) & B[(i//5)*5 + (i%5+2)%5]) for i in range(25)]
            # Iota
            state[0] ^= RC[rnd]
    # Squeeze
    out = b"".join(state[i].to_bytes(8, "little") for i in range(4))
    return out


def _selector(sig: str) -> str:
    """Compute 4-byte function selector via keccak-256."""
    return "0x" + _keccak256(sig.encode()).hex()[:8]

# Precomputed selectors for ERC-20 functions
ERC20_SELECTORS: Dict[str, str] = {
    "name()":                  "0x06fdde03",
    "symbol()":                "0x95d89b41",
    "decimals()":              "0x313ce567",
    "totalSupply()":           "0x18160ddd",
    "balanceOf(address)":      "0x70a08231",
}

def eth_call_erc20(chain: str, contract: str, fn: str, arg_addr: Optional[str] = None) -> str:
    selector = ERC20_SELECTORS[fn]
    data = selector
    if arg_addr:
        data += _encode_address(arg_addr)
    params = [{"to": contract, "data": data}, "latest"]
    return rpc_call(chain, "eth_call", params) or "0x"

def decode_string(hex_data: str) -> str:
    """Decode ABI-encoded string from eth_call result."""
    try:
        raw = hex_data[2:] if hex_data.startswith("0x") else hex_data
        if len(raw) < 128:
            # Try decoding as raw bytes (some tokens return non-ABI strings)
            b = bytes.fromhex(raw)
            return b.rstrip(b"\x00").decode("utf-8", errors="replace").strip()
        # offset (skip 32 bytes), length, data
        length = int(raw[64:128], 16)
        chars = raw[128:128 + length * 2]
        return bytes.fromhex(chars).decode("utf-8", errors="replace").strip()
    except Exception:
        return ""

def decode_uint256(hex_data: str) -> int:
    try:
        raw = hex_data[2:] if hex_data.startswith("0x") else hex_data
        if not raw:
            return 0
        return int(raw, 16)
    except Exception:
        return 0

def decode_uint8(hex_data: str) -> int:
    return decode_uint256(hex_data)

# ---------------------------------------------------------------------------
# CoinGecko price fetching
# ---------------------------------------------------------------------------

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

def cg_price_by_id(cg_id: str) -> Optional[float]:
    try:
        url = f"{COINGECKO_BASE}/simple/price?ids={cg_id}&vs_currencies=usd"
        data = _http_get(url)
        return data.get(cg_id, {}).get("usd")
    except Exception:
        return None

def cg_price_by_ids(cg_ids: List[str]) -> Dict[str, float]:
    """Fetch multiple prices in one request."""
    if not cg_ids:
        return {}
    try:
        joined = ",".join(cg_ids)
        url = f"{COINGECKO_BASE}/simple/price?ids={joined}&vs_currencies=usd"
        data = _http_get(url)
        return {k: v.get("usd", 0.0) for k, v in data.items() if "usd" in v}
    except Exception:
        return {}

def cg_price_by_contract(chain: str, contract: str) -> Optional[float]:
    cg_platform_map = {
        "ethereum": "ethereum",
        "bsc":      "binance-smart-chain",
        "base":     "base",
        "arbitrum": "arbitrum-one",
        "polygon":  "polygon-pos",
        "optimism": "optimistic-ethereum",
        "avalanche":"avalanche",
        "zksync":   "zksync",
    }
    platform = cg_platform_map.get(chain)
    if not platform:
        return None
    try:
        url = (
            f"{COINGECKO_BASE}/simple/token_price/{platform}"
            f"?contract_addresses={contract}&vs_currencies=usd"
        )
        data = _http_get(url)
        addr_lower = contract.lower()
        for k, v in data.items():
            if k.lower() == addr_lower:
                return v.get("usd")
        return None
    except Exception:
        return None

def get_native_price(chain: str) -> Optional[float]:
    cg_id = CHAINS[chain]["coingecko"]
    return cg_price_by_id(cg_id)

# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def cmd_stats(args: argparse.Namespace) -> None:
    chain = args.chain
    cfg = CHAINS[chain]

    # Batch: blockNumber + gasPrice
    results = rpc_batch(chain, [
        ("eth_blockNumber", []),
        ("eth_gasPrice",    []),
    ])
    block_num = hex_to_int(results[0] or "0x0")
    gas_price_wei = hex_to_int(results[1] or "0x0")

    # TPS estimate: compare latest block timestamp with parent
    tps: Optional[float] = None
    try:
        latest_block = rpc_call(chain, "eth_getBlockByNumber", ["latest", False])
        if latest_block:
            parent_hex = latest_block.get("parentHash")
            parent_block = rpc_call(chain, "eth_getBlockByHash", [parent_hex, False])
            if parent_block:
                t1 = hex_to_int(latest_block.get("timestamp", "0x0"))
                t0 = hex_to_int(parent_block.get("timestamp", "0x0"))
                tx_count = len(latest_block.get("transactions", []))
                if t1 > t0:
                    tps = round(tx_count / (t1 - t0), 2)
    except Exception:
        pass

    native_price = get_native_price(chain)

    print_json({
        "chain":           chain,
        "block_number":    block_num,
        "gas_price_gwei":  round(gwei_from_wei(gas_price_wei), 4),
        "gas_price_wei":   gas_price_wei,
        "native_token":    ***REDACTED***
        "native_price_usd": native_price,
        "tps_estimate":    tps,
        "explorer":        cfg["explorer"],
    })


def cmd_wallet(args: argparse.Namespace) -> None:
    address = require_address(args.address)
    chain   = args.chain
    limit   = args.limit
    no_prices = args.no_prices
    cfg     = CHAINS[chain]

    # Native balance
    balance_hex = rpc_call(chain, "eth_getBalance", [address, "latest"])
    native_wei  = hex_to_int(balance_hex or "0x0")
    native_val  = wei_to_native(native_wei, cfg["decimals"])

    native_usd_price: Optional[float] = None
    native_usd: Optional[float] = None
    if not no_prices:
        native_usd_price = get_native_price(chain)
        if native_usd_price is not None:
            native_usd = round(native_val * native_usd_price, 4)

    # ERC-20 tokens
    token_list = ***REDACTED***
    tokens_out = ***REDACTED***
    portfolio_usd = native_usd or 0.0

    if token_list:
        ***REDACTED***
        balance_calls = [
            ("eth_call", [{"to": addr, "data": ERC20_SELECTORS["balanceOf(address)"] + _encode_address(address)}, "latest"])
            for _, addr in token_list
        ]
        balances = rpc_batch(chain, balance_calls)

        for idx, (symbol, addr) in enumerate(token_list):
            ***REDACTED***
            if raw_bal == 0:
                continue

            # Fetch decimals
            dec_hex = eth_call_erc20(chain, addr, "decimals()")
            decimals = decode_uint8(dec_hex) if dec_hex and dec_hex != "0x" else 18
            bal_human = wei_to_native(raw_bal, decimals)

            token_pr

... [Content truncated, total 55,875 chars] ...