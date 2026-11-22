"""OptiChain - Streamlit frontend connected to the OptionPricingModel smart contract.

Pricing comes from backend.py. Every record, decision, fingerprint and purchase
is written to and read back from Ganache through web3.py.
users.json only links a username + hashed password to a Ganache wallet.
"""
import base64
import hashlib
import json
import math
import os
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backend import calculate_american_option, compare_with_market

st.set_page_config(page_title="OptiChain", page_icon="⛓️", layout="wide")

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# ---- palette (from the design) ----
PURPLE = "#4A0B5E"       # buttons, active menu
PANEL = "#56478A"        # login panel, accents
STEEL = "#3F6A9E"        # sidebar tint, secondary lines
CHIP = "#C6DAF8"         # chips, lower tree nodes
LINK = "#7DB6F2"
INK = "#1F1A2E"          # main text
MUTED = "#6B6880"
BORDER = "#D6D3DE"
FONT = "Jost"

DECISION_STYLE = {
    "OVER-VALUED": {"color": "#B42318", "title": "Over-valued",
                    "text": "Market price is above fair value. Expensive to buy; consider selling if held."},
    "UNDER-VALUED": {"color": "#1E8A3C", "title": "Under-valued",
                     "text": "Market price is below fair value. Potential buying opportunity."},
    "FAIRLY VALUED": {"color": "#B45309", "title": "Fairly valued",
                      "text": "Market price is within 1% of fair value. No clear edge."},
}
DEFAULT_INPUTS = {"option_type": "call", "stock_price": 100.0, "strike_price": 105.0,
                  "time_to_expiry": 1.0, "intervals": 3, "volatility": 0.20,
                  "risk_free_rate": 0.05, "market_premium": 8.00}


@st.cache_data
def asset_b64(name):
    path = os.path.join(ASSETS, name)
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def inject_css():
    jost, jersey, bg = asset_b64("Jost.ttf"), asset_b64("Jersey25.ttf"), asset_b64("background.jpg")
    photo = f"url(data:image/jpeg;base64,{bg}) center / cover" if bg else "#2E4F7E"
    photo_side = f"url(data:image/jpeg;base64,{bg}) left center / cover" if bg else "#2E4F7E"
    st.markdown(
        f"""
        <style>
        @font-face {{ font-family: 'Jost'; src: url(data:font/ttf;base64,{jost}) format('truetype'); font-weight: 100 900; }}
        @font-face {{ font-family: 'Jersey 25'; src: url(data:font/ttf;base64,{jersey}) format('truetype'); }}

        html, body, .stApp, .stMarkdown, button, input, label, textarea, p, [data-testid="stMetricValue"] {{
            font-family: '{FONT}', system-ui, sans-serif; }}
        .stApp {{ background: #FFFFFF; color: {INK}; }}
        [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] * {{ font-family: '{FONT}', system-ui, sans-serif; }}
        [data-testid="stHeader"] {{ display: none; }}
        .block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1120px; }}

        /* ---------- shared ---------- */
        .page-title {{ font-size: 2.1rem; font-weight: 400; color: {INK}; line-height: 1.1; }}
        .page-sub {{ font-size: 0.95rem; color: {MUTED}; margin: 0.2rem 0 1.6rem; }}
        .sec {{ font-size: 1.12rem; font-weight: 500; color: {INK}; margin: 0.4rem 0 0.1rem; }}
        .box {{ border: 1px solid {BORDER}; border-radius: 6px; padding: 0.75rem 1rem; background: #FFFFFF; }}
        .stat {{ font-size: 1.7rem; font-weight: 500; color: {INK}; }}
        .stat-label {{ font-size: 1rem; color: {INK}; margin-bottom: 0.35rem; }}
        .chips {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.6rem; margin: 0.3rem 0 0.9rem; }}
        .chip {{ background: {CHIP}; border-radius: 5px; padding: 0.4rem 0.6rem; text-align: center; color: {INK}; font-size: 0.95rem; }}
        .chip b {{ font-weight: 500; margin-left: 0.6rem; }}
        .mono, [data-testid="stMarkdownContainer"] .mono {{ font-family: ui-monospace, 'Cascadia Mono', Consolas, monospace; font-size: 0.85rem; word-break: break-all; }}
        .muted {{ color: {MUTED}; }}
        [data-testid="stTooltipIcon"] svg {{ stroke: {PANEL}; }}

        /* bordered containers (chart frames, forms) */
        [data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {{ border-color: {BORDER}; }}
        [data-testid="stForm"] {{ border: 1px solid {BORDER}; border-radius: 6px; padding: 1.3rem 1.4rem; }}

        /* inputs */
        [data-baseweb="input"], [data-baseweb="base-input"] {{ border-radius: 6px; }}
        .stNumberInput input, .stTextInput input, .stDateInput input {{ font-family: '{FONT}'; }}

        /* buttons (main area) */
        .stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] {{
            background: {PURPLE}; border: 1px solid {PURPLE}; color: #FFFFFF; border-radius: 4px;
            font-size: 1rem; padding: 0.45rem 1.6rem; }}
        .stButton button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:hover {{
            background: #36074A; border-color: #36074A; }}
        .stButton button[kind="primary"]:focus-visible {{ outline: 2px solid {LINK}; outline-offset: 2px; }}

        /* slider + radio accents */
        [data-baseweb="slider"] [role="slider"] {{ background: {PURPLE}; }}

        /* ---------- login ---------- */
        .stApp:has(.login-page) {{ background: {photo}; }}
        .stApp:has(.login-page) .block-container {{ max-width: 1180px; padding-top: 4.5rem; }}
        [data-testid="stMarkdownContainer"] .logo, .logo {{ font-family: 'Jersey 25', monospace; color: #FFFFFF; letter-spacing: -0.01em; line-height: 1;
                 -webkit-text-stroke: 1px {PANEL}; text-shadow: 2px 2px 0 {PANEL}; display: flex; align-items: center; gap: 0.6rem; }}
        .logo .mark {{ position: relative; width: 0.55em; height: 0.55em; flex: none; }}
        .logo .mark::before, .logo .mark::after {{ content: ""; position: absolute; width: 0.36em; height: 0.36em;
                 border: 0.07em solid #FFFFFF; border-radius: 0.08em; box-shadow: 1px 1px 0 {PANEL}; }}
        .logo .mark::before {{ left: 0; top: 0; }}
        .logo .mark::after {{ right: 0; bottom: 0; background: #B9A6E8; }}
        .login-logo {{ font-size: 4.6rem; margin: 1.6rem 0 3rem; }}
        .login-copy {{ color: #FFFFFF; font-size: 1.55rem; font-weight: 400; line-height: 1.45; max-width: 27ch;
                       text-shadow: 0 1px 8px rgba(20,35,70,0.55); }}
        .st-key-auth_panel {{ background: rgba(86,71,138,0.86); backdrop-filter: blur(4px); border-radius: 2px;
                              padding: 2.6rem 3.4rem 2.2rem; }}
        .auth-title {{ color: #FFFFFF; text-align: center; font-size: 1.45rem; letter-spacing: 0.03em; margin-bottom: 1.2rem; }}
        .st-key-auth_panel label p {{ color: #FFFFFF; font-size: 0.92rem; }}
        .st-key-auth_panel [data-baseweb="input"] {{ background: #FFFFFF; border: none; }}
        .st-key-auth_panel input {{ background: #FFFFFF; color: {INK}; }}
        .st-key-auth_panel [data-testid="stForm"] {{ border: none; padding: 0; }}
        .st-key-auth_panel [data-testid="stFormSubmitButton"] {{ padding: 0 24%; margin-top: 1.2rem; }}
        .st-key-auth_panel [data-testid="stFormSubmitButton"] button {{ font-size: 1.15rem; padding: 0.5rem 0; }}
        .st-key-auth_panel [data-testid="stFormSubmitButton"] button p {{ font-size: 1.15rem; }}
        .st-key-auth_switch {{ justify-content: center; align-items: baseline; gap: 0.35rem; margin-top: 1.4rem; }}
        .st-key-auth_switch p {{ color: #FFFFFF; font-size: 0.92rem; margin: 0; }}
        .st-key-auth_switch button {{ color: {LINK}; font-weight: 600; padding: 0; min-height: 0; line-height: 1.6; }}
        .st-key-auth_switch [data-testid="stMarkdownContainer"] p, .st-key-auth_switch button p {{ line-height: 1.6; }}
        .st-key-auth_switch button:hover p {{ color: #FFFFFF; text-decoration: underline; }}
        .st-key-auth_switch button p {{ color: {LINK}; font-weight: 600; }}
        .st-key-auth_panel [data-testid="stAlert"] p {{ color: {INK}; }}

        /* ---------- sidebar ---------- */
        [data-testid="stSidebar"] {{ background: {photo_side};
                                    min-width: 290px; max-width: 290px; }}
        [data-testid="stSidebarHeader"] {{ display: none; }}
        [data-testid="stSidebarUserContent"] {{ padding: 2rem 1.2rem 1.5rem; }}
        .side-logo {{ font-size: 2.35rem; justify-content: center; margin-bottom: 1.6rem; }}
        .user {{ display: flex; align-items: center; gap: 0.7rem; color: #FFFFFF; font-size: 1.05rem; }}
        .user svg {{ width: 26px; height: 26px; flex: none; }}
        .wallet {{ display: inline-block; margin: 0.6rem 0 1.6rem; background: rgba(20,30,60,0.35); color: #E6EEFB;
                   border-radius: 4px; padding: 3px 9px; cursor: help; }}
        [data-testid="stSidebar"] .stButton button {{ width: 100%; justify-content: flex-start; height: 2.9rem; border-radius: 4px;
                   border: none; color: #FFFFFF; font-size: 1.08rem; margin-bottom: 0.55rem; padding-left: 0.9rem; }}
        [data-testid="stSidebar"] .stButton button > div {{ justify-content: flex-start; width: 100%; }}
        .st-key-logout .stButton button > div {{ justify-content: center !important; }}
        [data-testid="stSidebar"] .stButton button p {{ font-size: 1.08rem; color: #FFFFFF; }}
        [data-testid="stSidebar"] .stButton button[kind="secondary"] {{ background: rgba(120,100,165,0.38); box-shadow: 4px 4px 0 {PANEL}; }}
        [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {{ background: rgba(120,100,165,0.6); }}
        [data-testid="stSidebar"] .stButton button[kind="primary"] {{ background: {PURPLE}; box-shadow: 4px 4px 0 rgba(30,10,45,0.35); }}
        .st-key-logout {{ margin-top: 30vh; }}
        .st-key-logout .stButton button {{ justify-content: center !important; background: rgba(255,255,255,0.12) !important;
                   box-shadow: none !important; }}
        .st-key-logout .stButton button:hover {{ background: rgba(255,255,255,0.22) !important; }}

        /* ---------- price page ---------- */
        .verdict {{ border: 1px solid {BORDER}; border-top: 6px solid var(--c); border-radius: 6px; padding: 1.3rem 1.6rem; margin: 1.2rem 0 1.4rem; }}
        .verdict .head {{ display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; align-items: flex-start; }}
        .verdict .big {{ color: var(--c); font-size: 2.4rem; font-weight: 600; line-height: 1.05; }}
        .verdict .why {{ color: {INK}; margin-top: 0.4rem; }}
        .verdict .amt {{ color: var(--c); font-size: 1.6rem; font-weight: 500; text-align: right; }}
        .verdict .lbl {{ color: {MUTED}; font-size: 0.85rem; text-align: right; }}
        .scale {{ position: relative; height: 70px; margin: 1.4rem 0.6rem 0; }}
        .scale .axis {{ position: absolute; left: 0; right: 0; top: 32px; height: 4px; background: #ECEAF2; border-radius: 2px; }}
        .scale .gap {{ position: absolute; top: 31px; height: 6px; background: var(--c); opacity: 0.35; border-radius: 3px; }}
        .scale .pin {{ position: absolute; top: 0; transform: translateX(-50%); text-align: center; white-space: nowrap; }}
        .scale .t {{ font-size: 0.8rem; color: {MUTED}; }}
        .scale .dot {{ width: 14px; height: 14px; border-radius: 50%; margin: 6px auto 0; border: 3px solid #FFFFFF; }}
        .scale .v {{ font-size: 0.95rem; font-weight: 500; color: {INK}; margin-top: 3px; }}
        .legend {{ display: flex; gap: 1.2rem; color: {MUTED}; font-size: 0.85rem; }}
        .legend i {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 0.35rem; vertical-align: -1px; }}
        .block {{ border: 1px solid {BORDER}; border-left: 6px solid {PURPLE}; border-radius: 6px; padding: 1rem 1.3rem; }}
        .block .top {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem; }}
        .block .num {{ font-size: 1.2rem; font-weight: 500; }}
        .block .ok {{ color: #1E8A3C; font-weight: 500; font-size: 0.92rem; }}
        .block .row {{ display: grid; grid-template-columns: 7.5rem 1fr; gap: 0.6rem; padding: 0.35rem 0; border-top: 1px solid #F0EEF4; }}
        .block .k {{ color: {MUTED}; font-size: 0.9rem; }}
        .fail {{ border: 1px solid #F5C2BD; background: #FDECEA; color: #B42318; border-radius: 6px; padding: 0.8rem 1rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()

USER_ICON = ("<svg viewBox='0 0 24 24' fill='none' stroke='#FFFFFF' stroke-width='2'>"
             "<circle cx='12' cy='12' r='10'/><circle cx='12' cy='10' r='3.2'/>"
             "<path d='M6.2 18.4c1.4-2 3.4-3 5.8-3s4.4 1 5.8 3'/></svg>")


# =====================================================================
# BLOCKCHAIN CONNECTION  (Ganache + OptionPricingModel.sol via web3.py)
# =====================================================================
RPC_URL = "http://127.0.0.1:7545"
CONTRACT_ADDRESS = "0xc37BB0e902951f997BeB6e998225F2Fe6CB4206f"   # Remix > Deployed Contracts > copy icon

SCALE = 10 ** 6                    # must match SCALE in the contract
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
CHAIN_DECISION = {0: "UNDER-VALUED", 1: "FAIRLY VALUED", 2: "OVER-VALUED"}

_CHAIN = {}


def chain():
    """Returns (w3, contract, error_message). Only successful connections are cached."""
    if "ok" in _CHAIN:
        return _CHAIN["ok"]
    try:
        from web3 import Web3
    except ImportError:
        return None, None, "web3 is not installed. In the terminal run: py -m pip install web3"
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 15}))
    try:
        connected = w3.is_connected()
    except Exception:
        connected = False
    if not connected:
        return None, None, f"Can't reach Ganache at {RPC_URL}. Open Ganache, then refresh this page."
    try:
        address = Web3.to_checksum_address(CONTRACT_ADDRESS)
    except Exception:
        return None, None, "Contract address missing. Paste it into CONTRACT_ADDRESS at the top of app.py."
    if len(w3.eth.get_code(address)) == 0:
        return None, None, ("No contract at this address. Use the address from Remix > Deployed Contracts "
                            "(not the account address), deployed on Ganache.")
    with open(os.path.join(ASSETS, "abi.json")) as f:
        contract = w3.eth.contract(address=address, abi=json.load(f))
    _CHAIN["ok"] = (w3, contract, None)
    return _CHAIN["ok"]


def _send(fn, wallet):
    """Sends a contract transaction from a Ganache wallet and returns the receipt."""
    w3, _, _ = chain()
    tx = fn.transact({"from": wallet})
    return w3.eth.wait_for_transaction_receipt(tx)


def _hex(b):
    h = b.hex() if hasattr(b, "hex") else str(b)
    return h if h.startswith("0x") else "0x" + h


def _revert_reason(err):
    text = str(err)
    return text.split("revert")[-1].strip(" :'\")") if "revert" in text else text[:160]


# ---------- accounts (username -> wallet, kept in users.json) ----------

def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE) as f:
        return json.load(f)


def _save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=1)


def _pw(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000).hex()


def register_investor(username, password):
    """Assigns a free Ganache wallet, calls registerBuyer().
    Returns (receipt_dict, wallet) or raises ValueError."""
    w3, contract, err = chain()
    if err:
        raise ValueError(err)
    users = _load_users()
    if username in users:
        raise ValueError("That username is taken.")
    used = {u["wallet"] for u in users.values()}
    free = [a for a in w3.eth.accounts if a not in used]
    if not free:
        raise ValueError("All Ganache accounts are in use.")
    wallet = free[0]
    if contract.functions.buyers(wallet).call():
        receipt = {"tx_hash": "", "block": w3.eth.block_number}
    else:
        r = _send(contract.functions.registerBuyer(), wallet)
        receipt = {"tx_hash": _hex(r.transactionHash), "block": r.blockNumber}

    salt = os.urandom(16).hex()
    users[username] = {"salt": salt, "password": _pw(password, salt), "wallet": wallet}
    _save_users(users)
    return receipt, wallet


def login_investor(username, password):
    """Returns (wallet, None) or (None, error message)."""
    user = _load_users().get(username)
    if not user or _pw(password, user["salt"]) != user["password"]:
        return None, "Incorrect username or password."
    w3, _, err = chain()
    if err:
        return None, err
    if user["wallet"] not in w3.eth.accounts:
        return None, "This account's wallet isn't on the current Ganache network. Create a new account."
    return user["wallet"], None


# ---------- valuations ----------

def _scaled(inputs, value):
    return [int(round(inputs["stock_price"] * SCALE)), int(round(inputs["strike_price"] * SCALE)),
            int(round(inputs["time_to_expiry"] * SCALE)), int(round(inputs["volatility"] * SCALE)),
            int(round(inputs["risk_free_rate"] * SCALE)), int(inputs["intervals"]),
            int(round(inputs["market_premium"] * SCALE)), int(round(value * SCALE)),
            0 if inputs["option_type"] == "call" else 1]


def record_valuation(wallet, inputs, value):
    """recordCalculation(). The contract decides the valuation and builds the fingerprint."""
    _, contract, err = chain()
    if err:
        raise ValueError(err)
    try:
        r = _send(contract.functions.recordCalculation(*_scaled(inputs, value)), wallet)
    except Exception as e:
        raise ValueError(_revert_reason(e))
    ev = contract.events.CalculationRecorded().process_receipt(r)[0]["args"]
    return {"id": ev["calculationId"], "decision": CHAIN_DECISION[ev["decision"]],
            "record_hash": "0x" + bytes(ev["fingerprint"]).hex(), "tx_hash": _hex(r.transactionHash),
            "block": r.blockNumber, "gas_used": r.gasUsed}


def _calc_dict(cid, c):
    return {"id": cid, "investor": c[0], "stock_price": c[1] / SCALE, "strike_price": c[2] / SCALE,
            "time_to_expiry": c[3] / SCALE, "volatility": c[4] / SCALE, "risk_free_rate": c[5] / SCALE,
            "intervals": c[6], "market_premium": c[7] / SCALE, "theoretical_value": c[8] / SCALE,
            "difference": c[9] / SCALE, "option_type": "call" if c[10] == 0 else "put",
            "decision": CHAIN_DECISION[c[11]], "timestamp": c[12], "block": c[13],
            "record_hash": "0x" + bytes(c[14]).hex(), "raw": c,
            "saved_at": datetime.fromtimestamp(c[12]).strftime("%d %b %Y %H:%M")}


def get_valuations(wallet):
    """getMyCalculations() + getCalculation(id), newest first."""
    _, contract, err = chain()
    if err:
        return []
    try:
        ids = contract.functions.getMyCalculations().call({"from": wallet})
    except Exception:
        return []
    return [_calc_dict(i, contract.functions.getCalculation(i).call()) for i in reversed(ids)]


def rebuild_fingerprint(record, edits=None):
    """Recomputes keccak256(abi.encode(...)) exactly as the contract does.
    'edits' lets the user change values to simulate tampering."""
    from eth_abi import encode
    from web3 import Web3
    c = list(record["raw"])
    for field, idx in (("stock_price", 1), ("strike_price", 2), ("market_premium", 7), ("theoretical_value", 8)):
        if edits and field in edits:
            c[idx] = int(round(edits[field] * SCALE))
    values = [c[0], c[1], c[2], c[7], c[4], c[5], c[3], c[6], c[10], c[8], c[11]]
    types = ["address"] + ["uint256"] * 7 + ["uint8", "uint256", "uint8"]
    return "0x" + Web3.keccak(encode(types, values)).hex().removeprefix("0x")


# =====================================================================
# Display helpers (frontend only - pricing comes from backend.py)
# =====================================================================

def stock_tree(inputs):
    """Stock prices at each node for the chart - same up/down formula as backend.py."""
    n = inputs["intervals"]
    dt = inputs["time_to_expiry"] / n
    u = math.exp(inputs["volatility"] * math.sqrt(dt))
    d = 1 / u
    return [[inputs["stock_price"] * u ** k * d ** (step - k) for k in range(step + 1)] for step in range(n + 1)], dt


def step_dates(start, dt, n):
    return [start + timedelta(days=round(step * dt * 365.25)) for step in range(n + 1)]


def short(addr, n=10):
    return f"{addr[:n + 2]}…{addr[-4:]}"


def price(inputs, volatility=None):
    return calculate_american_option(
        strike_price=inputs["strike_price"], stock_price=inputs["stock_price"],
        intervals=inputs["intervals"], time_to_expiry=inputs["time_to_expiry"],
        volatility=volatility if volatility is not None else inputs["volatility"],
        risk_free_rate=inputs["risk_free_rate"], option_type=inputs["option_type"],
    )

def chart_layout(fig, height, **kw):
    fig.update_layout(height=height, margin=dict(l=10, r=20, t=20, b=10), showlegend=False,
                      plot_bgcolor="#FFFFFF", paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=FONT, color=INK, size=13),
                      hoverlabel=dict(font_family=FONT), **kw)
    return fig


def show_chart(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def tree_figure(tree, dates, strike):
    n = len(tree) - 1
    fig = go.Figure()
    for step in range(n):
        for k in range(step + 1):
            y = 2 * k - step
            for y_next in (y - 1, y + 1):
                fig.add_trace(go.Scatter(x=[step, step + 1], y=[y, y_next], mode="lines",
                                         line=dict(color="#CFC8DE", width=2), hoverinfo="skip"))
    for step, prices in enumerate(tree):
        for k, p in enumerate(prices):
            above = p >= strike
            fig.add_annotation(x=step, y=2 * k - step, showarrow=False, text=f"<b>${p:,.2f}</b>",
                               font=dict(color="#FFFFFF" if above else INK, size=14, family=FONT),
                               bgcolor=PURPLE if above else CHIP, borderpad=9)
    chart_layout(fig, 150 + 110 * n,
                 xaxis=dict(tickmode="array", tickvals=list(range(n + 1)), ticktext=[d.strftime("%b %Y") for d in dates],
                            range=[-0.5, n + 0.5], showgrid=False, zeroline=False, tickfont=dict(color=MUTED)),
                 yaxis=dict(visible=False, range=[-n - 1, n + 1]))
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    return fig


def volatility_figure(inputs):
    vols, values = [], []
    for v in range(5, 101):
        try:
            values.append(price(inputs, v / 100))
            vols.append(v)
        except ValueError:
            continue
    fig = go.Figure(go.Scatter(x=vols, y=values, mode="lines", line=dict(color=PURPLE, width=3),
                               fill="tozeroy", fillcolor="rgba(86,71,138,0.10)",
                               hovertemplate="Volatility %{x}%<br>Fair value $%{y:.2f}<extra></extra>"))
    fig.add_hline(y=inputs["market_premium"], line=dict(color=STEEL, dash="dash", width=2),
                  annotation_text=f"Market premium ${inputs['market_premium']:,.2f}",
                  annotation_position="top left", annotation_font_color=STEEL)
    fig.add_vline(x=inputs["volatility"] * 100, line=dict(color=MUTED, dash="dot"),
                  annotation_text=f"{inputs['volatility'] * 100:.0f}%", annotation_position="top right",
                  annotation_font_color=MUTED)
    chart_layout(fig, 330, xaxis=dict(title="Volatility", gridcolor="#F0EEF4", ticksuffix="%"),
                 yaxis=dict(title="Fair value", gridcolor="#F0EEF4", tickprefix="$"))
    implied = next((v for v, val in zip(vols, values) if val >= inputs["market_premium"]), None)
    return fig, implied


def page_header(title, subtitle):
    st.markdown(f"<div class='page-title'>{title}</div><div class='page-sub'>{subtitle}</div>",
                unsafe_allow_html=True)


def section(title, help=None):
    st.markdown(f"<div class='sec'>{title}</div>", unsafe_allow_html=True, help=help)


def stat_box(label, value, help=None):
    st.markdown(f"<div class='stat-label'>{label}</div>", unsafe_allow_html=True, help=help)
    st.markdown(f"<div class='box stat'>{value}</div>", unsafe_allow_html=True)


def chips_html(inputs):
    if inputs is None:
        items = [("Option", "—"), ("Stock", "—"), ("Strike", "—"), ("Time", "—")]
    else:
        items = [(inputs["option_type"].title() + " Option", ""), ("Stock", f"${inputs['stock_price']:,.0f}"),
                 ("Strike", f"${inputs['strike_price']:,.0f}"), ("Time", f"{inputs['time_to_expiry']:g}yr")]
    return "<div class='chips'>" + "".join(f"<div class='chip'>{a}<b>{b}</b></div>" for a, b in items) + "</div>"


def verdict_html(value, premium, decision):
    s = DECISION_STYLE[decision]
    lo, hi = min(value, premium), max(value, premium)
    pad = max((hi - lo) * 0.6, hi * 0.15)
    a, b = lo - pad, hi + pad
    pos = lambda x: (x - a) / (b - a) * 100
    return f"""
    <div class="verdict" style="--c:{s['color']}">
      <div class="head">
        <div><div class="muted">Decision</div><div class="big">{s['title']}</div><div class="why">{s['text']}</div></div>
        <div><div class="amt">{premium - value:+,.2f}</div><div class="lbl">Market minus fair value</div></div>
      </div>
      <div class="scale">
        <div class="axis"></div>
        <div class="gap" style="left:{pos(lo):.1f}%; width:{pos(hi) - pos(lo):.1f}%"></div>
        <div class="pin" style="left:{pos(value):.1f}%"><div class="t">Fair value</div>
             <div class="dot" style="background:{PURPLE}"></div><div class="v">${value:,.4f}</div></div>
        <div class="pin" style="left:{pos(premium):.1f}%"><div class="t">Market premium</div>
             <div class="dot" style="background:{s['color']}"></div><div class="v">${premium:,.4f}</div></div>
      </div>
    </div>"""


def block_html(title, rows, status="Recorded on-chain", ok=True):
    body = "".join(f"<div class='row'><span class='k'>{k}</span><span class='{'mono' if m else ''}'>{v}</span></div>"
                   for k, v, m in rows)
    colour = "#1E8A3C" if ok else "#B42318"
    mark = "✓" if ok else "✕"
    border = PURPLE if ok else "#B42318"
    return (f"<div class='block' style='border-left-color:{border}'><div class='top'><span class='num'>{title}</span>"
            f"<span class='ok' style='color:{colour}'>{mark} {status}</span></div>{body}</div>")


def chain_error_box(msg):
    st.markdown(f"<div class='fail'><b>Blockchain not connected.</b> {msg}</div>", unsafe_allow_html=True)


# =====================================================================
# Screens
# =====================================================================

def login_screen():
    st.markdown("<div class='login-page'></div>", unsafe_allow_html=True)
    mode = st.session_state.setdefault("auth_mode", "login")
    left, gap, right = st.columns([1.05, 0.15, 1])
    with left:
        st.markdown(
            "<div class='logo login-logo'><span class='mark'></span>OPTICHAIN</div>"
            "<div class='login-copy'>Price American options with a binomial model, see whether the market "
            "premium is fair, and keep a tamper-proof record of every result on the blockchain.</div>",
            unsafe_allow_html=True)
    with right, st.container(key="auth_panel"):
        _, _, err = chain()
        if mode == "login":
            st.markdown("<div class='auth-title'>WELCOME BACK!</div>", unsafe_allow_html=True)
            with st.form("login", border=False):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login", type="primary", width="stretch"):
                    wallet, msg = login_investor(username.strip(), password)
                    if wallet:
                        st.session_state.user = {"username": username.strip(), "wallet": wallet}
                        st.rerun()
                    st.error(msg)
            with st.container(key="auth_switch", horizontal=True):
                st.markdown("Don't have an account?")
                if st.button("Sign up", type="tertiary", key="to_signup"):
                    st.session_state.auth_mode = "signup"
                    st.rerun()
        else:
            st.markdown("<div class='auth-title'>CREATE ACCOUNT</div>", unsafe_allow_html=True)
            with st.form("signup", border=False):
                username = st.text_input("Username", help="At least 3 characters")
                password = st.text_input("Password", type="password", help="At least 6 characters")
                confirm = st.text_input("Confirm password", type="password")
                if st.form_submit_button("Sign up", type="primary", width="stretch"):
                    username = username.strip()
                    if len(username) < 3 or len(password) < 6:
                        st.error("Username needs 3+ characters, password 6+.")
                    elif password != confirm:
                        st.error("Passwords don't match.")
                    else:
                        try:
                            with st.spinner("Registering wallet on-chain…"):
                                receipt, wallet = register_investor(username, password)
                        except ValueError as e:
                            st.error(str(e))
                        else:
                            st.session_state.user = {"username": username, "wallet": wallet}
                            st.session_state.welcome = receipt
                            st.rerun()
            with st.container(key="auth_switch", horizontal=True):
                st.markdown("Already have an account?")
                if st.button("Log in", type="tertiary", key="to_login"):
                    st.session_state.auth_mode = "login"
                    st.rerun()
        if err:
            st.markdown(f"<div style='color:#FFE1DE;font-size:0.85rem;text-align:center;margin-top:1rem'>{err}</div>",
                        unsafe_allow_html=True)


PAGES = ["Dashboard", "Price Option", "History"]


def sidebar():
    user = st.session_state.user
    w3, _, err = chain()
    status = (f"<span style='color:#9BE8B0'>●</span> Ganache · block {w3.eth.block_number}" if not err
              else "<span style='color:#FFB4AB'>●</span> Not connected")
    with st.sidebar:
        st.markdown(
            f"<div class='logo side-logo'><span class='mark'></span>OPTICHAIN</div>"
            f"<div class='user'>{USER_ICON}<span>{user['username']}</span></div>"
            f"<div class='wallet mono' title='Wallet address: {user['wallet']}'>{short(user['wallet'], 6)}</div>"
            f"<div style='color:#E6EEFB;font-size:0.82rem;margin:-1.1rem 0 1.4rem'>{status}</div>",
            unsafe_allow_html=True)
        current = st.session_state.setdefault("page", "Dashboard")
        for name in PAGES:
            if st.button(name, key=f"nav_{name}", type="primary" if name == current else "secondary", width="stretch"):
                st.session_state.page = name
                st.rerun()
        with st.container(key="logout"):
            if st.button("Log Out", key="logout_btn", width="stretch"):
                for key in ("user", "page", "inputs", "result", "auth_mode"):
                    st.session_state.pop(key, None)
                st.rerun()

def dashboard_screen():
    user = st.session_state.user
    page_header("Overview", "Portfolio and Pricing at a Glance")
    if "welcome" in st.session_state:
        r = st.session_state.pop("welcome")
        st.toast(f"Wallet registered on-chain · block {r['block']}", icon="✅")
    _, _, err = chain()
    if err:
        chain_error_box(err)

    valuations, trades = get_valuations(user["wallet"])
    c1, c2 = st.columns(2, gap="large")
    with c1:
        stat_box("On-chain Records", len(valuations), help="Valuations stored in the smart contract for your wallet.")
    with c2:
        stat_box("Portfolio Value", f"${sum(t['quantity'] * t['price'] for t in trades):,.2f}",
                 help="Total cost of your stock purchases recorded on-chain.")

    # inputs: this session's latest pricing, else the latest on-chain record, else empty (new user)
    inputs = st.session_state.get("inputs")
    if inputs is None and valuations:
        last = valuations[0]
        inputs = {k: last[k] for k in ("option_type", "stock_price", "strike_price", "time_to_expiry",
                                       "intervals", "volatility", "risk_free_rate", "market_premium")}

    st.write("")
    section("Volatility Sensitivity",
            help="Fair option value at volatility from 5% to 100%. Dashed line: market premium. "
                 "Dotted line: your volatility input.")
    st.markdown(chips_html(inputs), unsafe_allow_html=True)
    if inputs is None:
        fig = chart_layout(go.Figure(), 330,
                           xaxis=dict(title="Volatility", range=[5, 100], ticksuffix="%", gridcolor="#F0EEF4"),
                           yaxis=dict(title="Fair value", range=[0, 10], tickprefix="$", gridcolor="#F0EEF4"))
        implied = None
    else:
        fig, implied = volatility_figure(inputs)
    with st.container(border=True):
        show_chart(fig)

    section("Insights", help="Implied volatility: the volatility at which the model's fair value equals the market premium.")
    if inputs is None:
        st.markdown("<div class='box muted'>—</div>", unsafe_allow_html=True)
    elif implied:
        st.markdown(f"<div class='box'>The market premium matches the model at roughly <b>{implied}% volatility</b>. "
                    f"Expect less movement than that and the option is priced high.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='box muted'>Market premium is outside the model's range.</div>", unsafe_allow_html=True)

    section("Latest Valuation", help="Most recent record read back from the smart contract.")
    if valuations:
        last = valuations[0]
        s = DECISION_STYLE[last["decision"]]
        st.markdown(f"<div class='box'>{last['option_type'].title()} at strike ${last['strike_price']:,.2f}: "
                    f"<b style='color:{s['color']}'>{s['title']}</b> (fair ${last['theoretical_value']:,.2f} vs market "
                    f"${last['market_premium']:,.2f}) · Block {last['block']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='box muted'>—</div>", unsafe_allow_html=True)


def price_screen():
    user = st.session_state.user
    page_header("Price Option", "Fair Value and Market Check")
    saved = st.session_state.get("inputs", DEFAULT_INPUTS)

    with st.form("pricing"):
        a, b, c = st.columns(3, gap="medium")
        with a:
            option_type = st.radio("Option type", ["call", "put"], horizontal=True,
                                   index=0 if saved["option_type"] == "call" else 1,
                                   format_func=lambda x: x.title(),
                                   help="Call: right to buy. Put: right to sell.")
            stock_price = st.number_input("Stock price ($)", min_value=0.01, value=saved["stock_price"], step=1.0)
            strike_price = st.number_input("Strike price ($)", min_value=0.01, value=saved["strike_price"], step=1.0)
        with b:
            market_premium = st.number_input("Market premium ($)", min_value=0.01, value=saved["market_premium"],
                                             step=0.5, help="Current market price of the option contract.")
            volatility = st.number_input("Volatility (%)", min_value=0.1, max_value=100.0,
                                         value=saved["volatility"] * 100, step=1.0,
                                         help="Expected yearly price movement of the stock.")
            risk_free_rate = st.number_input("Risk-free rate (%)", min_value=0.0, max_value=100.0,
                                             value=saved["risk_free_rate"] * 100, step=0.25)
        with c:
            start = st.date_input("Valuation date", value=date.today())
            time_to_expiry = st.number_input("Time to expiry (years)", min_value=0.01,
                                             value=saved["time_to_expiry"], step=0.25, help="0.5 = six months")
            intervals = st.select_slider("Intervals", options=[1, 2, 3], value=saved["intervals"],
                                         help="Number of steps the time to expiry is split into.")
            preview = step_dates(start, time_to_expiry / intervals, intervals)[1:]
            st.caption("Checkpoints: " + ", ".join(d.strftime("%b %Y") for d in preview))
        submitted = st.form_submit_button("Calculate", type="primary")

    if submitted:
        inputs = {"option_type": option_type, "stock_price": stock_price, "strike_price": strike_price,
                  "time_to_expiry": time_to_expiry, "intervals": intervals, "volatility": volatility / 100,
                  "risk_free_rate": risk_free_rate / 100, "market_premium": market_premium}
        try:
            value = price(inputs)
        except ValueError as e:
            st.error(f"Inputs not supported by the model: {e} Try higher volatility or a lower rate.")
            return
        st.session_state.inputs = inputs
        st.session_state.result = {"value": value, "decision": compare_with_market(value, market_premium),
                                   "start": start, "saved": None}

    result = st.session_state.get("result")
    if not result:
        return

    inputs, value, decision = st.session_state.inputs, result["value"], result["decision"]
    st.markdown(verdict_html(value, inputs["market_premium"], decision), unsafe_allow_html=True)

    section("Price Tree", help="Possible stock prices at each checkpoint, from the binomial model.")
    st.markdown(f"<div class='legend'><span><i style='background:{PURPLE}'></i>At or above strike</span>"
                f"<span><i style='background:{CHIP}'></i>Below strike</span></div>", unsafe_allow_html=True)
    tree, dt = stock_tree(inputs)
    show_chart(tree_figure(tree, step_dates(result["start"], dt, inputs["intervals"]), inputs["strike_price"]))

    section("Blockchain Record", help="Sends the inputs and fair value to the smart contract. The contract decides "
                                      "the valuation itself and stores a fingerprint. Records can't be edited.")
    _, _, err = chain()
    if err:
        chain_error_box(err)
    elif result["saved"]:
        r = result["saved"]
        s = DECISION_STYLE[r["decision"]]
        match = "matches the app" if r["decision"] == decision else "differs from the app"
        st.markdown(block_html(f"Calculation #{r['id']}", [
            ("On-chain decision", f"<b style='color:{s['color']}'>{s['title']}</b> ({match})", False),
            ("Block", r["block"], False), ("Transaction", r["tx_hash"], True), ("Gas used", f"{r['gas_used']:,}", False),
        ]), unsafe_allow_html=True)
        st.markdown("<div class='sec' style='font-size:0.95rem;margin-top:0.8rem'>Fingerprint</div>",
                    unsafe_allow_html=True, help="keccak256 hash stored by the contract for this record.")
        st.code(r["record_hash"], language=None)
    elif st.button("Record on Blockchain", type="primary"):
        try:
            with st.spinner("Waiting for the transaction to be mined…"):
                result["saved"] = record_valuation(user["wallet"], inputs, value)
            st.rerun()
        except ValueError as e:
            st.markdown(f"<div class='fail'>Transaction rejected by the contract: {e}</div>", unsafe_allow_html=True)
    st.caption("Estimates only. Not investment advice.")

def history_screen():
    page_header("History", "Recorded Valuations")
    _, _, err = chain()
    if err:
        chain_error_box(err)
        return
    records = get_valuations(st.session_state.user["wallet"])
    if not records:
        st.markdown("<div class='box muted'>No valuations recorded yet.</div>", unsafe_allow_html=True)
        return
    df = pd.DataFrame(records)
    df["Decision"] = df["decision"].map(lambda x: DECISION_STYLE[x]["title"])
    view = df.rename(columns={"id": "ID", "saved_at": "Saved", "option_type": "Type", "stock_price": "Stock ($)",
                              "strike_price": "Strike ($)", "market_premium": "Market ($)",
                              "theoretical_value": "Fair value ($)", "block": "Block"})
    view["Type"] = view["Type"].str.title()
    colours = {s["title"]: s["color"] for s in DECISION_STYLE.values()}
    styled = view[["ID", "Saved", "Type", "Stock ($)", "Strike ($)", "Market ($)", "Fair value ($)", "Decision", "Block"]] \
        .style.map(lambda v: f"color:{colours.get(v, INK)}; font-weight:600", subset=["Decision"]) \
        .format({"Stock ($)": "${:,.2f}", "Strike ($)": "${:,.2f}", "Market ($)": "${:,.2f}", "Fair value ($)": "${:,.4f}"})
    st.dataframe(styled, hide_index=True, width="stretch")

    st.write("")
    section("Verify Record", help="Rebuilds the fingerprint from the record's details and compares it with the one "
                                  "stored in the contract. Change any value to see tampering detected.")
    by_id = {r["id"]: r for r in records}
    pick = st.selectbox("Record", list(by_id), label_visibility="collapsed",
                        format_func=lambda i: f"#{i} · {by_id[i]['option_type'].title()} · strike "
                                              f"${by_id[i]['strike_price']:,.2f} · {by_id[i]['saved_at']}")
    rec = by_id[pick]
    cols = st.columns(4)
    edits = {}
    for col, (field, label) in zip(cols, [("stock_price", "Stock ($)"), ("strike_price", "Strike ($)"),
                                          ("market_premium", "Market premium ($)"),
                                          ("theoretical_value", "Fair value ($)")]):
        with col:
            edits[field] = st.number_input(label, value=float(rec[field]), format="%.4f", key=f"v_{pick}_{field}")
    if st.button("Verify", type="primary"):
        rebuilt = rebuild_fingerprint(rec, edits)
        ok = rebuilt.lower() == rec["record_hash"].lower()
        st.markdown(block_html(f"Calculation #{rec['id']} · Block {rec['block']}", [
            ("Stored on-chain", rec["record_hash"], True), ("Rebuilt from details", rebuilt, True),
        ], status="Verified, unchanged" if ok else "Mismatch: details were changed", ok=ok), unsafe_allow_html=True)


# =====================================================================
# Router
# =====================================================================
if "user" not in st.session_state:
    login_screen()
else:
    sidebar()
    {"Dashboard": dashboard_screen, "Price Option": price_screen, "History": history_screen}[st.session_state.page]()
