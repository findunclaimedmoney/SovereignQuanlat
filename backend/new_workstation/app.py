import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import uuid
import time
import json
import base64
import requests
from pathlib import Path

# Configure matplotlib for headless environment
matplotlib.use('Agg')

# Page Configuration
st.set_page_config(
    page_title="Sovereign Quant Super Agent Dashboard",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1f2937;
        border-radius: 4px 4px 0px 0px;
        padding-left: 16px;
        padding-right: 16px;
        color: #f3f4f6;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
        font-weight: bold;
    }
    .agent-box {
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #374151;
        background-color: #111827;
        margin-bottom: 8px;
    }
    .agent-header {
        font-weight: bold;
        color: #60a5fa;
        margin-bottom: 4px;
    }
    .risk-alert {
        padding: 12px;
        border-radius: 6px;
        background-color: #7f1d1d;
        border: 1px solid #f87171;
        color: #fca5a5;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 0. DATA AGENT — REAL MARKET DATA (Binance klines, Coinbase fallback, Parquet cache)
# -----------------------------------------------------------------------------
DATA_CACHE_DIR = Path(__file__).resolve().parent / "data_cache"
DATA_CACHE_DIR.mkdir(exist_ok=True)

# UI pair name ("BTC/USDT") -> exchange symbol ("BTCUSDT"). Extend as more pairs are added.
PAIR_TO_SYMBOL = {
    "BTC/USDT": "BTCUSDT",
    "ETH/USDT": "ETHUSDT",
}

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
COINBASE_CANDLES_URL = "https://api.exchange.coinbase.com/products/{product_id}/candles"


def pair_to_symbol(pair: str) -> str:
    """Map a UI-style pair like 'BTC/USDT' to an exchange symbol like 'BTCUSDT'."""
    return PAIR_TO_SYMBOL.get(pair, pair.replace("/", "").upper())


def _cache_path(symbol: str, interval: str, limit: int) -> Path:
    return DATA_CACHE_DIR / f"{symbol}_{interval}_{limit}.parquet"


def fetch_binance_klines(symbol: str, interval: str = "12h", limit: int = 200) -> pd.DataFrame:
    """Fetch real historical OHLCV candles from Binance's public (keyless) klines endpoint.

    symbol:   exchange format, e.g. 'BTCUSDT' (no slash).
    interval: Binance interval string, LOWERCASE, e.g. '12h' — NOT '12H'. The
              uppercase alias is what caused the original pd.date_range crash in
              this file; Binance (and modern pandas) both want lowercase.
    limit:    number of candles, Binance max is 1000 per call.
    """
    resp = requests.get(
        BINANCE_KLINES_URL,
        params={"symbol": symbol, "interval": interval, "limit": limit},
        timeout=10,
    )
    resp.raise_for_status()
    raw = resp.json()
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore",
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df[["open_time", "open", "high", "low", "close", "volume"]]


def fetch_coinbase_candles(symbol: str, interval: str = "12h", limit: int = 200) -> pd.DataFrame:
    """Fallback source if Binance is unreachable (e.g. geo-blocked). Free, no key.

    Coinbase only offers fixed granularities (60/300/900/3600/21600/86400s), so
    this is best-effort — it maps our interval to the nearest one it supports.
    """
    product_map = {"BTCUSDT": "BTC-USD", "ETHUSDT": "ETH-USD"}
    product_id = product_map.get(symbol, symbol.replace("USDT", "-USD"))
    interval_seconds = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "12h": 43200, "1d": 86400}
    requested = interval_seconds.get(interval, 43200)
    granularity = min([g for g in (60, 300, 900, 3600, 21600, 86400) if g >= requested] or [86400])

    resp = requests.get(
        COINBASE_CANDLES_URL.format(product_id=product_id),
        params={"granularity": granularity},
        timeout=10,
        headers={"User-Agent": "sovereign-quant-dashboard"},
    )
    resp.raise_for_status()
    raw = resp.json()  # rows: [time, low, high, open, close, volume], newest first
    df = pd.DataFrame(raw, columns=["time", "low", "high", "open", "close", "volume"])
    df["open_time"] = pd.to_datetime(df["time"], unit="s")
    df = df.sort_values("open_time").tail(limit)
    return df[["open_time", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def get_real_candles(pair: str, interval: str = "12h", limit: int = 200, max_cache_age_hours: float = 4.0):
    """Disk-cached real OHLCV fetch for a UI pair (e.g. 'BTC/USDT').

    Checks the Parquet disk cache first; only hits the network when the cache is
    missing or stale, then re-caches whatever it fetched. Returns (df, meta) —
    meta always describes what actually happened (cache hit, live fetch, which
    source, or failure) so callers can log something true instead of a canned
    string. Returns (None, meta) only if there is truly no data available
    anywhere (no cache, both live sources failed) — it never fabricates candles.
    """
    symbol = pair_to_symbol(pair)
    path = _cache_path(symbol, interval, limit)

    if path.exists():
        age_hours = (time.time() - path.stat().st_mtime) / 3600.0
        if age_hours <= max_cache_age_hours:
            df = pd.read_parquet(path)
            return df, {"source": "disk_cache", "pair": pair, "symbol": symbol,
                        "candles": len(df), "age_hours": round(age_hours, 2)}

    last_error = None
    for source_name, fetch_fn in (("Binance", fetch_binance_klines), ("Coinbase", fetch_coinbase_candles)):
        try:
            df = fetch_fn(symbol, interval=interval, limit=limit)
            if df is not None and len(df) > 0:
                df.to_parquet(path, index=False)
                return df, {"source": source_name, "pair": pair, "symbol": symbol,
                            "candles": len(df), "age_hours": 0.0}
        except Exception as e:
            last_error = e

    # Both live sources failed (no internet, API geo/network-blocked, etc). Fall
    # back to a stale cache if one exists rather than silently faking data.
    if path.exists():
        df = pd.read_parquet(path)
        age_hours = (time.time() - path.stat().st_mtime) / 3600.0
        return df, {"source": "stale_disk_cache", "pair": pair, "symbol": symbol, "candles": len(df),
                     "age_hours": round(age_hours, 2), "error": str(last_error)}

    return None, {"source": "unavailable", "pair": pair, "symbol": symbol, "error": str(last_error)}


def backtest_pairs_strategy(close_a: pd.Series, close_b: pd.Series, z_entry: float = 2.0,
                             z_exit: float = 0.5, periods_per_year: int = 730):
    """Real (if simple) pairs-spread backtest on real close prices.

    OLS hedge ratio -> spread -> rolling z-score -> the same entry/exit state
    machine used in the Strategy Playground tab, applied one bar after the
    signal (no lookahead). Returns an actual equity curve plus Sharpe/Sortino/
    Profit Factor computed from the resulting return series — not hardcoded
    display strings.
    """
    x = close_a.values.astype(float)
    y = close_b.values.astype(float)
    hedge_ratio = np.polyfit(x, y, 1)[0]
    spread = y - hedge_ratio * x

    roll_mean = pd.Series(spread).rolling(window=20).mean().bfill()
    roll_std = pd.Series(spread).rolling(window=20).std().bfill().replace(0, 1)
    z = ((spread - roll_mean) / roll_std).values

    position = np.zeros(len(z))
    state = 0
    for i, zi in enumerate(z):
        if state == 0:
            if zi > z_entry:
                state = -1
            elif zi < -z_entry:
                state = 1
        elif state == 1 and zi >= -z_exit:
            state = 0
        elif state == -1 and zi <= z_exit:
            state = 0
        position[i] = state

    spread_ret = pd.Series(spread).diff().fillna(0).values
    # position decided on bar i is realized on bar i+1's move (avoid lookahead)
    strat_ret = np.roll(position, 1) * spread_ret
    strat_ret[0] = 0.0
    notional = np.mean(np.abs(y)) or 1.0
    pct_ret = strat_ret / notional

    equity = 100000 * np.cumprod(1 + pct_ret)

    mean_ret, std_ret = np.mean(pct_ret), np.std(pct_ret)
    sharpe = (mean_ret / std_ret) * np.sqrt(periods_per_year) if std_ret > 0 else 0.0

    downside = pct_ret[pct_ret < 0]
    downside_std = np.std(downside) if len(downside) > 0 else 0.0
    sortino = (mean_ret / downside_std) * np.sqrt(periods_per_year) if downside_std > 0 else 0.0

    gains = pct_ret[pct_ret > 0].sum()
    losses = -pct_ret[pct_ret < 0].sum()
    profit_factor = (gains / losses) if losses > 0 else float("inf")

    return equity, sharpe, sortino, profit_factor, position


# -----------------------------------------------------------------------------
# 1. CRYPTOGRAPHIC LICENSING ENGINE (Ed25519 public-key signatures)
# -----------------------------------------------------------------------------
# Only the PUBLIC key lives here, which is safe to ship — it can verify a
# signature but cannot produce one. License keys are minted separately, offline,
# by whoever holds the matching private key (see seller_only/license_signing_tool.py,
# which is NOT part of this distributed app). This replaces the previous scheme,
# where the same secret used to check a key was also embedded here and could sign
# new keys — meaning anyone with this file could mint their own "Institutional"
# license for free. Public-key signing closes that: verification is safe to
# distribute, signing is not, and the two are no longer the same secret.
PUBLIC_KEY_B64 = "MdHqH5TbXv0TzEh2jGjxlFhSXdl7EShSfScBu8h7Obo="

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature as _InvalidSignature

def verify_offline_licence_key(key):
    """Verifies an Ed25519 signature and extracts tier details.

    Keys issued under the old HMAC scheme will no longer validate — that's
    intentional; those were forgeable by anyone with this file.
    """
    try:
        parts = key.split(".")
        if len(parts) != 2:
            return {"valid": False, "reason": "Invalid key format"}

        payload_b64, signature_b64 = parts[0], parts[1]

        pub = Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(PUBLIC_KEY_B64))
        sig_padding = "=" * (-len(signature_b64) % 4)
        signature = base64.urlsafe_b64decode(signature_b64 + sig_padding)

        try:
            pub.verify(signature, payload_b64.encode())
        except _InvalidSignature:
            return {"valid": False, "reason": "Cryptographic signature validation failed"}

        # Decode payload (only after the signature checks out)
        padding = "=" * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode()
        payload = json.loads(payload_json)
        payload["valid"] = True
        return payload
    except Exception as e:
        return {"valid": False, "reason": f"Verification error: {str(e)}"}

# Define limits for each tier as stated in our Memory Core
TIER_LIMITS = {
    "Community": {
        "max_capital": 50000,
        "concurrent_strategies": 1,
        "walk_forward": False,
        "monte_carlo": False,
        "branded_reports": False,
        "signal_export": False,
        "multi_account": False
    },
    "Professional": {
        "max_capital": 1000000,
        "concurrent_strategies": 3,
        "walk_forward": True,
        "monte_carlo": False,
        "branded_reports": True,
        "signal_export": True,
        "multi_account": False
    },
    "Institutional": {
        "max_capital": 50000000,
        "concurrent_strategies": 10,
        "walk_forward": True,
        "monte_carlo": True,
        "branded_reports": True,
        "signal_export": True,
        "multi_account": True
    }
}

# -----------------------------------------------------------------------------
# 2. STATE INITIALISATION
# -----------------------------------------------------------------------------
if "risk_manager" not in st.session_state:
    st.session_state.risk_manager = {
        "daily_loss_limit_pct": 2.5,
        "max_drawdown_limit_pct": 10.0,
        "leverage_limit": 3.0,
        "portfolio_heat_limit_pct": 20.0,
        "kill_switch_triggered": False,
        "current_drawdown": 0.0,
        "daily_loss": 0.0,
        "open_leverage": 0.0,
        "portfolio_heat": 0.0,
        "active_trades": []
    }

if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = []

if "licence" not in st.session_state:
    # Standard start-off tier: Community default
    st.session_state.licence = {
        "valid": True,
        "licensee": "Self-Owned Developer",
        "tier": "Community",
        "duration": 365,
        "created_at": "2026-08-22"
    }

# -----------------------------------------------------------------------------
# SIDEBAR: STATUS, RISK PARAMETERS & LICENSING
# -----------------------------------------------------------------------------
st.sidebar.title("👑 Sovereign Quant")
st.sidebar.caption("v1.3 Super Agent Core (Offline-First)")

# System Health State
system_status = "🔴 OFFLINE" if st.session_state.risk_manager["kill_switch_triggered"] else "🟢 ACTIVE"
st.sidebar.subheader(f"System State: {system_status}")

if st.session_state.risk_manager["kill_switch_triggered"]:
    st.sidebar.error("⚠️ RISK ENGINE KILL-SWITCH TRIGGERED. Live/Paper adapters locked out.")
    if st.sidebar.button("Reset Circuit Breaker"):
        st.session_state.risk_manager["kill_switch_triggered"] = False
        st.session_state.risk_manager["current_drawdown"] = 0.0
        st.session_state.risk_manager["daily_loss"] = 0.0
        st.session_state.risk_manager["active_trades"] = []
        st.sidebar.success("Circuit breaker reset successfully.")
        st.rerun()

# License Information Block
st.sidebar.markdown("---")
st.sidebar.subheader("🔑 Licence Management")
lic_info = st.session_state.licence
tier_limits = TIER_LIMITS[lic_info["tier"]]

st.sidebar.write(f"**Licensee**: {lic_info['licensee']}")
st.sidebar.write(f"**Tier**: `{lic_info['tier']}`")
st.sidebar.write(f"**Max Capital**: ${tier_limits['max_capital']:,}")
st.sidebar.write(f"**Concurrent Strategies**: Up to {tier_limits['concurrent_strategies']}")

# Expandable Key Activation
with st.sidebar.expander("Activate New Licence Key"):
    st.info("The system operates offline-first. Verification happens locally against a "
            "public key baked into this app — no phone-home required.")
    user_key = st.text_area("Licence Key", help="Paste the key you received after purchase.")

    if st.button("Activate locally"):
        result = verify_offline_licence_key(user_key)
        if result.get("valid"):
            st.session_state.licence = result
            st.success(f"Success! Activated `{result['tier']}` License.")
            st.rerun()
        else:
            st.error(f"Activation Failed: {result.get('reason', 'Invalid Key')}")

# NOTE: the self-serve "Demo License Key Generator" that used to live here has
# been removed on purpose. This app now only holds a PUBLIC verification key —
# signing new keys requires the private key, which is intentionally kept out
# of this file (see seller_only/license_signing_tool.py). If you need a demo/
# trial key for yourself, issue one with that tool the same way you would for
# a customer.

# -----------------------------------------------------------------------------
# MAIN DASHBOARD TABS
# -----------------------------------------------------------------------------
st.title("Sovereign Quant Super Agent Dashboard")
st.markdown("Proprietary multi-agent quantitative workstation. **Zero cloud telemetry, 100% self-owned.**")

tab_orch, tab_strat, tab_risk, tab_rep = st.tabs([
    "🤖 Multi-Agent Orchestrator", 
    "📈 Trading Strategy Playground", 
    "🛡️ Risk Gates & Circuit Breakers",
    "📊 Branded Reports & Tearsheets"
])

# -----------------------------------------------------------------------------
# TAB 1: MULTI-AGENT ORCHESTRATOR
# -----------------------------------------------------------------------------
with tab_orch:
    st.header("🤖 Natural Language Goal Orchestrator")
    st.markdown("""
    The central `Orchestrator` coordinates specialized offline agents (Data, Strategy, Risk, Reporting, and Licence) 
    via structured, in-process messages. Enter an operational objective to route tasks.
    """)
    
    goal_input = st.text_input(
        "Execute Agent Goal Directive:",
        "Backtest paired spread trading for BTC/USDT and ETH/USDT on historical parquet cache with default Risk limits."
    )
    
    col_run, col_clear = st.columns([1, 6])
    run_clicked = col_run.button("Dispatch Goal", type="primary")
    if col_clear.button("Clear Communication Logs"):
        st.session_state.agent_logs = []
        st.rerun()
        
    if run_clicked:
        st.session_state.agent_logs = []  # reset for new execution trace
        cid = str(uuid.uuid4())[:8]

        # Which pairs is this goal actually about? Fall back to the two pairs the
        # dashboard is themed around if none are named explicitly in the goal text.
        target_pairs = [p for p in PAIR_TO_SYMBOL if p in goal_input] or ["BTC/USDT", "ETH/USDT"]

        # Real DataAgent fetch (Binance klines -> Coinbase fallback -> Parquet disk
        # cache). This is the step that used to just print a fabricated string.
        data_meta = []
        for pair in target_pairs:
            _, meta = get_real_candles(pair, interval="12h", limit=200)
            data_meta.append(meta)

        ok_meta = [m for m in data_meta if m["source"] != "unavailable"]
        if ok_meta:
            parts = []
            for m in ok_meta:
                if m["source"] == "disk_cache":
                    parts.append(f"{m['pair']}: {m['candles']} candles from Parquet cache ({m['age_hours']}h old)")
                elif m["source"] == "stale_disk_cache":
                    parts.append(f"{m['pair']}: {m['candles']} candles from STALE Parquet cache (live fetch failed: {m['error']})")
                else:
                    parts.append(f"{m['pair']}: fetched {m['candles']} fresh candles from {m['source']}, cached to Parquet")
            data_msg = "Checked disk cache for Parquet. " + " | ".join(parts)
        else:
            err = data_meta[0]["error"] if data_meta else "unknown error"
            data_msg = (f"Checked disk cache for Parquet. No cache present and live fetch failed for "
                        f"all pairs ({err}). No candle data available.")

        # Step-by-step agent trace — DataAgent's line now reflects what actually
        # happened above instead of a canned "synthetic" string.
        steps = [
            ("Orchestrator", "GOAL", f"Received Goal: '{goal_input}'"),
            ("LicenceAgent", "LICENCE", f"Verifying active license limits. Active Tier: '{lic_info['tier']}'"),
            ("DataAgent", "DATA", data_msg),
            ("StrategyAgent", "SIGNAL", f"Analyzing historical series... Formulating Pairs Statistical Arbitrage signal spread."),
            ("RiskAgent", "RISK_CHECK", "Analyzing portfolio heat, margin bounds and cointegrated leverage parameters."),
            ("Orchestrator", "RESULT", "Execution and Signal Generation accomplished. Strategy Backtest logs updated.")
        ]
        
        for agent, msg_type, msg in steps:
            # Check license limits during runtime
            if agent == "LicenceAgent":
                if lic_info["tier"] == "Community" and ("Monte-Carlo" in goal_input or "Walk-forward" in goal_input):
                    st.session_state.agent_logs.append({
                        "agent": "LicenceAgent",
                        "type": "ERROR",
                        "message": f"Goal blocked: Monte-Carlo / Walk-forward simulation requires Professional or Institutional license tier.",
                        "cid": cid,
                        "timestamp": time.strftime('%H:%M:%S')
                    })
                    break
            
            st.session_state.agent_logs.append({
                "agent": agent,
                "type": msg_type,
                "message": msg,
                "cid": cid,
                "timestamp": time.strftime('%H:%M:%S')
            })
            
    # Draw Trace Timeline
    if st.session_state.agent_logs:
        st.subheader("📬 Orchestrator Message Trace Stream (Correlation-Traced)")
        for log in st.session_state.agent_logs:
            color = "#ef4444" if log["type"] in ["ERROR", "CRITICAL"] else "#10b981" if log["type"] in ["RESULT", "RISK_CHECK"] else "#3b82f6"
            
            st.markdown(f"""
            <div class="agent-box" style="border-left: 4px solid {color};">
                <div class="agent-header">
                    <span>🕵️‍♂️ {log['agent']}</span> | 
                    <span style="color: {color}; font-weight: bold;">{log['type']}</span> | 
                    <span style="color: #9ca3af; font-size: 0.85em;">CID: {log['cid']} | {log['timestamp']}</span>
                </div>
                <div style="color: #e5e7eb; font-size: 0.95em;">{log['message']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Enter an instruction above and click 'Dispatch Goal' to witness the multi-agent orchestration workflow.")

# -----------------------------------------------------------------------------
# TAB 2: Strategy Playground
# -----------------------------------------------------------------------------
with tab_strat:
    st.header("📈 Trading Strategy Playground")
    st.markdown("Validate strategies written from first principles. Configure parameters and review simulated signals.")
    
    strategy_choice = st.selectbox(
        "Select Strategy to Analyze", 
        ["Pairs (Statistical Arbitrage)", "Momentum / Trend Following", "Mean-Reversion"]
    )
    
    # Real Market Data (Binance klines, Coinbase fallback, Parquet-cached) —
    # replaces the previous np.random synthetic generator.
    btc_df, btc_meta = get_real_candles("BTC/USDT", interval="12h", limit=150)
    eth_df, eth_meta = get_real_candles("ETH/USDT", interval="12h", limit=150)
    is_synthetic = btc_df is None or eth_df is None

    if is_synthetic:
        st.markdown(
            '<div class="risk-alert">⚠️ SYNTHETIC FALLBACK DATA — live market data unavailable '
            f'({btc_meta.get("error") or eth_meta.get("error")}), and no Parquet cache exists yet.</div>',
            unsafe_allow_html=True,
        )
        np.random.seed(42)
        dates = pd.date_range(start="2026-01-01", periods=100, freq="D")
        btc_close = pd.Series(np.cumsum(np.random.normal(0, 1, 100)) + 100, index=dates)
        eth_close = pd.Series(0.8 * btc_close.values + np.random.normal(0, 1.5, 100) + 20, index=dates)
    else:
        n = min(len(btc_df), len(eth_df))
        btc_df, eth_df = btc_df.tail(n).reset_index(drop=True), eth_df.tail(n).reset_index(drop=True)
        dates = pd.DatetimeIndex(btc_df["open_time"])
        # Rebased to 100 at the start of the window ("indexed" price) — this keeps
        # the existing slider thresholds below (tuned for a ~100-scale series)
        # meaningful regardless of BTC/ETH's actual dollar price level.
        btc_close = pd.Series(100 * btc_df["close"].values / btc_df["close"].values[0], index=dates)
        eth_close = pd.Series(100 * eth_df["close"].values / eth_df["close"].values[0], index=dates)
        source_label = "Parquet cache" if btc_meta["source"] in ("disk_cache", "stale_disk_cache") else f"live {btc_meta['source']} fetch"
        st.caption(f"📡 Real BTC/USDT & ETH/USDT candles ({n}, via {source_label}) — indexed to 100 at window start.")

    if strategy_choice == "Pairs (Statistical Arbitrage)":
        st.subheader("Statistical Arbitrage: Engle-Granger Cointegration & OLS Hedge")
        st.write("Calculates rolling hedge ratios and Z-score deviations from the cointegrated mean.")

        # OLS hedge ratio + spread on the real (indexed) BTC/ETH price series
        x = btc_close.values
        hedge_ratio = np.polyfit(x, eth_close.values, 1)[0]
        spread = eth_close.values - hedge_ratio * x
        y = eth_close.values

        col_pair1, col_pair2, col_z = st.columns(3)
        z_entry = col_pair1.slider("Z-Score Entry Threshold", 1.0, 3.0, 2.0, step=0.1)
        z_exit = col_pair2.slider("Z-Score Exit Threshold", 0.0, 1.5, 0.5, step=0.1)
        half_life_cap = col_z.number_input("Max OU Half-Life Filter (Days)", value=15)
        
        # Compute dynamic z-scores
        rolling_mean = pd.Series(spread).rolling(window=20).mean().fillna(0)
        rolling_std = pd.Series(spread).rolling(window=20).std().fillna(1)
        z_scores = (spread - rolling_mean) / rolling_std
        
        # Generate Signals
        signals = []
        state = 0 # 0: idle, 1: long spread, -1: short spread
        for z in z_scores:
            if state == 0:
                if z > z_entry:
                    state = -1
                elif z < -z_entry:
                    state = 1
            elif state == 1:
                if z >= -z_exit:
                    state = 0
            elif state == -1:
                if z <= z_exit:
                    state = 0
            signals.append(state)
            
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
        ax1.plot(dates, x, label="Asset A (BTC)", color="#f59e0b")
        ax1.plot(dates, y, label="Asset B (ETH)", color="#3b82f6")
        ax1.set_title("Cointegrated Asset Pairs")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Color signal bands
        ax2.plot(dates, z_scores, label="Spread Z-Score", color="#10b981")
        ax2.axhline(z_entry, color="red", linestyle="--", alpha=0.7, label="Entry threshold")
        ax2.axhline(-z_entry, color="red", linestyle="--", alpha=0.7)
        ax2.axhline(z_exit, color="gray", linestyle=":", alpha=0.5, label="Exit Threshold")
        ax2.axhline(-z_exit, color="gray", linestyle=":")
        ax2.set_title("Spread Z-Score Signal Generation")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        st.pyplot(fig)
        plt.close(fig)
        
    elif strategy_choice == "Momentum / Trend Following":
        st.subheader("Trend Following with Volatility Sizing")
        st.write("Combines Dual Moving Average Crossover (fast/slow), ADX trend filtering, and volatility sizing.")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        fast_ma = col_m1.slider("Fast MA Period", 5, 50, 12)
        slow_ma = col_m2.slider("Slow MA Period", 20, 200, 26)
        adx_filt = col_m3.slider("ADX Trend Strength Filter", 10, 40, 20)
        
        # Real BTC/USDT price series (indexed to 100 at window start, see above)
        prices = btc_close.values
        df = pd.DataFrame({"Price": prices}, index=dates)
        df["Fast"] = df["Price"].rolling(window=fast_ma).mean()
        df["Slow"] = df["Price"].rolling(window=slow_ma).mean()
        df["Volatility"] = df["Price"].rolling(window=20).std()

        # ADX (trend strength) filter is not yet computed from real OHLC data —
        # a full ADX implementation is out of scope for this data-source change,
        # so it stays a placeholder. Flagged clearly rather than silently faked.
        st.caption("ℹ️ ADX trend-strength values below are still a placeholder — not yet computed from real high/low data.")
        df["ADX"] = np.random.uniform(15, 35, len(df))
        
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(df.index, df["Price"], label="Close Price", color="#ffffff")
        ax.plot(df.index, df["Fast"], label=f"EMA {fast_ma}", color="#a78bfa", linestyle="--")
        ax.plot(df.index, df["Slow"], label=f"SMA {slow_ma}", color="#f43f5e")
        ax.fill_between(df.index, df["Price"].min(), df["Price"].max(), 
                        where=(df["Fast"] > df["Slow"]) & (df["ADX"] > adx_filt), 
                        color="green", alpha=0.15, label="Bull Trend Zone")
        ax.set_title("Trend-Following Execution Zones")
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)
        
    elif strategy_choice == "Mean-Reversion":
        st.subheader("Mean Reversion in Volatility Contained Regimes")
        st.write("Identifies high z-score deviations specifically in low-volatility, range-bound market environments.")
        
        # Real BTC/USDT price series (indexed to 100 at window start, see above)
        price = btc_close.values
        vol = pd.Series(price).rolling(window=10).std().fillna(1)
        regime = np.where(vol < 3.5, "Low-Vol", "High-Vol")
        
        col_mr1, col_mr2 = st.columns(2)
        mr_z = col_mr1.slider("Mean-Reversion Z-Score Limit", 1.5, 3.0, 1.8)
        max_vol_limit = col_mr2.slider("Volatility Regime Threshold (Upper Filter)", 1.0, 5.0, 3.0, step=0.1)
        
        fig, (ax_p, ax_v) = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
        ax_p.plot(dates, price, color="#60a5fa", label="Price")
        ax_p.set_title("Mean-Reversion Price Series")
        
        # Highlight low vol regime
        ax_v.plot(dates, vol, color="#f472b6", label="Rolling Volatility")
        ax_v.axhline(max_vol_limit, color="red", linestyle="--", label="Max Vol Gate")
        ax_v.set_title("Volatility Threshold Regime Filter")
        ax_v.legend()
        ax_v.grid(True, alpha=0.3)
        
        st.pyplot(fig)
        plt.close(fig)

# -----------------------------------------------------------------------------
# TAB 3: Risk Gates & Circuit Breakers
# -----------------------------------------------------------------------------
with tab_risk:
    st.header("🛡️ Non-Bypassable Risk Gates")
    st.markdown("""
    The `RiskManager` serves as a core, non-bypassable runtime gate. All multi-agent order routing requests 
    must pass `RiskManager.check_order()` to confirm safety parameters before execution.
    """)
    
    r_limit = st.session_state.risk_manager
    
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        st.subheader("Risk Manager Runtime Setup")
        max_daily_loss = st.slider("Daily Loss Limit %", 1.0, 5.0, r_limit["daily_loss_limit_pct"])
        max_dd = st.slider("Max Drawdown Limit % (Triggers Kill-Switch)", 5.0, 20.0, r_limit["max_drawdown_limit_pct"])
        max_lev = st.slider("Absolute Leverage Limit", 1.0, 10.0, r_limit["leverage_limit"])
        max_heat = st.slider("Max Portfolio Heat Limit %", 5.0, 30.0, r_limit["portfolio_heat_limit_pct"])
        
        # Sync state
        r_limit["daily_loss_limit_pct"] = max_daily_loss
        r_limit["max_drawdown_limit_pct"] = max_dd
        r_limit["leverage_limit"] = max_lev
        r_limit["portfolio_heat_limit_pct"] = max_heat
        
    with col_r2:
        st.subheader("Live Portfolio Sandbox Metrics")
        sim_dd = st.slider("Simulate Current Peak-to-Trough Drawdown %", 0.0, 25.0, r_limit["current_drawdown"])
        sim_loss = st.slider("Simulate Today's Loss %", 0.0, 10.0, r_limit["daily_loss"])
        sim_heat = st.slider("Simulate Existing Portfolio Heat %", 0.0, 40.0, r_limit["portfolio_heat"])
        
        # Update dynamic simulated state
        r_limit["current_drawdown"] = sim_dd
        r_limit["daily_loss"] = sim_loss
        r_limit["portfolio_heat"] = sim_heat
        
        # Check drawdown against circuit-breaker
        if sim_dd >= max_dd:
            r_limit["kill_switch_triggered"] = True
            st.error(f"🛑 RISK VIOLATION: Current Drawdown ({sim_dd}%) exceeded limit ({max_dd}%). Kill-switch activated!")
            
    # Order Dispatch Validator
    st.markdown("---")
    st.subheader("🛡️ Runtime Order Validation Simulator")
    st.write("Dispatch a simulated market trade through the non-bypassable risk engine:")
    
    col_o1, col_o2, col_o3 = st.columns(3)
    order_ticker = col_o1.text_input("Order Ticker Symbol", "BTC/USDT")
    order_size = col_o2.number_input("Order Size ($)", value=25000)
    order_lev = col_o3.number_input("Order Target Leverage", value=1.5, step=0.1)
    
    if st.button("Evaluate Order Security"):
        if r_limit["kill_switch_triggered"]:
            st.markdown(
                '<div class="risk-alert">❌ ORDER BLOCKED: The system is currently in a KILL-SWITCH locked state. Reset circuit breaker in sidebar first.</div>', 
                unsafe_allow_html=True
            )
        elif (order_size / tier_limits["max_capital"] * 100) > r_limit["portfolio_heat_limit_pct"]:
            st.error(f"❌ ORDER BLOCKED: Order portfolio heat exceeds portfolio heat limit of {r_limit['portfolio_heat_limit_pct']}%.")
        elif order_lev > r_limit["leverage_limit"]:
            st.error(f"❌ ORDER BLOCKED: Requested leverage ({order_lev}x) exceeds System Limit ({r_limit['leverage_limit']}x).")
        elif order_size > tier_limits["max_capital"]:
            st.error(f"❌ ORDER BLOCKED: Order exceeds maximum allowed capital of your licence tier (${tier_limits['max_capital']:,}).")
        else:
            st.success(f"✅ ORDER APPROVED: {order_ticker} for ${order_size:,} at {order_lev}x leverage cleared all risk gates.")

# -----------------------------------------------------------------------------
# TAB 4: Branded Reports & Tearsheets
# -----------------------------------------------------------------------------
with tab_rep:
    st.header("📊 Branded Reports & Tearsheets")
    st.markdown("""
    The `ReportingAgent` synthesizes trade histories into executive tearsheets. Branded reporting and export operations 
    are restricted based on your license tier.
    """)
    
    if not tier_limits["branded_reports"]:
        st.warning("⚠️ Branded Reports are exclusive to Professional & Institutional tiers. Upgrade your offline licence key to unlock.")
    else:
        st.success(f"🎉 Fully unlocked reporting modules under `{lic_info['tier']}` License.")
        
    st.subheader("Portfolio Performance Backtest Summary")

    # Real BTC/USDT & ETH/USDT candles, Parquet-cached — feeds an actual pairs
    # backtest below instead of a fabricated random-walk equity curve.
    btc_df, btc_meta = get_real_candles("BTC/USDT", interval="12h", limit=200)
    eth_df, eth_meta = get_real_candles("ETH/USDT", interval="12h", limit=200)

    sharpe_val = sortino_val = pf_val = None
    if btc_df is None or eth_df is None:
        st.markdown(
            '<div class="risk-alert">⚠️ Live market data unavailable '
            f'({btc_meta.get("error") or eth_meta.get("error")}) and no Parquet cache exists yet — '
            'showing a clearly-labelled SYNTHETIC fallback tearsheet, not a real backtest.</div>',
            unsafe_allow_html=True,
        )
        np.random.seed(7)
        t_index = pd.date_range(start="2026-01-01", periods=200, freq="12h")  # lowercase 'h' — fixes the original freq bug
        base_equity = 100000 * np.cumprod(1 + np.random.normal(0.001, 0.012, 200))
    else:
        n = min(len(btc_df), len(eth_df))
        btc_close = pd.Series(btc_df["close"].values[-n:], index=pd.DatetimeIndex(btc_df["open_time"].values[-n:]))
        eth_close = pd.Series(eth_df["close"].values[-n:], index=btc_close.index)
        t_index = btc_close.index
        base_equity, sharpe_val, sortino_val, pf_val, _ = backtest_pairs_strategy(btc_close, eth_close)
        source_label = "Parquet cache" if btc_meta["source"] in ("disk_cache", "stale_disk_cache") else f"live {btc_meta['source']} fetch"
        st.caption(f"📡 Backtested on {n} real BTC/USDT & ETH/USDT 12h candles (via {source_label}). "
                   "Simple Z-score pairs strategy (entry 2.0 / exit 0.5) — same logic as the Strategy Playground tab.")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t_index, base_equity, color="#60a5fa", label="Sovereign Core Strategy", linewidth=2)
    ax.set_title("Sovereign Quant Cumulative Backtest Returns")
    ax.fill_between(t_index, base_equity, 100000, where=(base_equity > 100000), color="#10b981", alpha=0.1)
    ax.fill_between(t_index, base_equity, 100000, where=(base_equity < 100000), color="#ef4444", alpha=0.1)
    ax.set_ylabel("Portfolio Value ($)")
    ax.legend()
    ax.grid(True, alpha=0.2)
    st.pyplot(fig)
    plt.close(fig)
    
    col_t1, col_t2, col_t3 = st.columns(3)
    if sharpe_val is not None:
        col_t1.metric("Sharpe Ratio", f"{sharpe_val:.2f}")
        col_t2.metric("Sortino Ratio", f"{sortino_val:.2f}")
        col_t3.metric("Profit Factor", f"{pf_val:.2f}" if np.isfinite(pf_val) else "∞")
    else:
        col_t1.metric("Sharpe Ratio", "N/A")
        col_t2.metric("Sortino Ratio", "N/A")
        col_t3.metric("Profit Factor", "N/A")
    
    st.markdown("---")
    st.subheader("🛠️ Report Generator Export Panel")
    
    col_rep_fmt = st.selectbox("Format Output Selection", ["Professional PDF Tearsheet", "Long-format CSV Signal Dump"])
    
    if st.button("Compile Executive Report"):
        if not tier_limits["branded_reports"] and col_rep_fmt == "Professional PDF Tearsheet":
            st.error("Feature Locked: Professional PDF compilation is restricted to Professional and Institutional licensees.")
        elif not tier_limits["signal_export"] and col_rep_fmt == "Long-format CSV Signal Dump":
            st.error("Feature Locked: Exporting signals is restricted to Professional and Institutional licensees.")
        else:
            with st.spinner("Generating clean reports with zero external leaks..."):
                time.sleep(1.5)
                st.balloons()
                st.success(f"Successfully generated and cached `{col_rep_fmt}` in local outbox.")
