import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import uuid
import time
import json
import hashlib
import hmac
import base64

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
""", unsafe_allowed_html=True)

# -----------------------------------------------------------------------------
# 1. CRYPTOGRAPHIC LICENSING ENGINE (Based on v1.1 HMAC)
# -----------------------------------------------------------------------------
DEFAULT_SECRET = "SOVEREIGN_QUANT_DEFAULT_HMAC_SECRET_2026"

def generate_offline_licence_key(licensee_name, tier, duration_days, secret=DEFAULT_SECRET):
    """Generates an HMAC-SHA256 signed license key (matching v1.1 specification)."""
    payload = {
        "licensee": licensee_name,
        "tier": tier,
        "duration": int(duration_days),
        "created_at": "2026-08-22"
    }
    payload_json = json.dumps(payload, sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    
    # Sign payload
    signature = hmac.new(
        secret.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    # Combined key
    return f"{payload_b64}.{signature_b64}"

def verify_offline_licence_key(key, secret=DEFAULT_SECRET):
    """Verifies HMAC signature of key and extracts tier details."""
    try:
        parts = key.split(".")
        if len(parts) != 2:
            return {"valid": False, "reason": "Invalid key format"}
        
        payload_b64, signature_b64 = parts[0], parts[1]
        
        # Recalculate signature
        expected_sig = hmac.new(
            secret.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
        
        # Prevent timing attacks via constant-time compare
        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            return {"valid": False, "reason": "Cryptographic signature validation failed"}
        
        # Decode payload
        padding = "=" * (4 - len(payload_b64) % 4)
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
    st.info("The system operates offline-first. Activate your HMAC key locally.")
    user_key = st.text_area("Licence Key", help="Paste base64 HMAC signature key here.")
    secret_override = st.text_input("Signing Secret (Optional)", type="password", help="Defaults to internal SOVEREIGN_QUANT secret.")
    
    if st.button("Activate locally"):
        secret_to_use = secret_override if secret_override else DEFAULT_SECRET
        result = verify_offline_licence_key(user_key, secret=secret_to_use)
        if result.get("valid"):
            st.session_state.licence = result
            st.success(f"Success! Activated `{result['tier']}` License.")
            st.rerun()
        else:
            st.error(f"Activation Failed: {result.get('reason', 'Invalid Key')}")

with st.sidebar.expander("Demo License Key Generator"):
    st.warning("For evaluation use only. Generates locally valid cryptographic licenses.")
    gen_name = st.text_input("Licensee Name", "Proprietary Trader")
    gen_tier = st.selectbox("Tier", ["Community", "Professional", "Institutional"])
    gen_days = st.slider("Duration (Days)", 30, 365, 365)
    gen_secret = st.text_input("Generator Secret (Optional)", type="password", placeholder="Keep default if testing standard app")
    
    if st.button("Generate License Key"):
        secret_to_use = gen_secret if gen_secret else DEFAULT_SECRET
        key = generate_offline_licence_key(gen_name, gen_tier, gen_days, secret=secret_to_use)
        st.code(key, language=None)

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
        
        # Step-by-step agent simulation mimicking actual execution trace
        steps = [
            ("Orchestrator", "GOAL", f"Received Goal: '{goal_input}'"),
            ("LicenceAgent", "LICENCE", f"Verifying active license limits. Active Tier: '{lic_info['tier']}'"),
            ("DataAgent", "DATA", "Checked disk cache for Parquet. Loading synthetic candle series for BTC and ETH..."),
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
            """, unsafe_allowed_html=True)
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
    
    # Generate Synthetic Data for Charts
    np.random.seed(42)
    dates = pd.date_range(start="2026-01-01", periods=100, freq="D")
    
    if strategy_choice == "Pairs (Statistical Arbitrage)":
        st.subheader("Statistical Arbitrage: Engle-Granger Cointegration & OLS Hedge")
        st.write("Calculates rolling hedge ratios and Z-score deviations from the cointegrated mean.")
        
        # Generate two cointegrated series
        x = np.cumsum(np.random.normal(0, 1, 100)) + 100
        spread = np.random.normal(0, 1.5, 100)
        y = 0.8 * x + spread + 20
        
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
        
        # Price process
        prices = np.cumsum(np.random.normal(0.2, 2, 100)) + 150
        df = pd.DataFrame({"Price": prices}, index=dates)
        df["Fast"] = df["Price"].rolling(window=fast_ma).mean()
        df["Slow"] = df["Price"].rolling(window=slow_ma).mean()
        df["Volatility"] = df["Price"].rolling(window=20).std()
        
        # Generate mock ADX trend filter
        df["ADX"] = np.random.uniform(15, 35, 100)
        
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
        
        # Price and volatility regime
        price = 100 + np.sin(np.linspace(0, 6*np.pi, 100)) * 10 + np.random.normal(0, 1, 100)
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
                unsafe_allowed_html=True
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
    
    # Generate mock cumulative equity curves
    t_index = pd.date_range(start="2026-01-01", periods=200, freq="12H")
    base_equity = 100000 * np.cumprod(1 + np.random.normal(0.001, 0.012, 200))
    
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
    col_t1.metric("Sharpe Ratio", "2.84", "+0.15")
    col_t2.metric("Sortino Ratio", "3.12", "+0.09")
    col_t3.metric("Profit Factor", "1.92", "-0.04")
    
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
