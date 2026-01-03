import streamlit as st
import requests
import time
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide", page_title="Rush Index — Live Stream")

API = "http://127.0.0.1:8000/latest"
REFRESH_SEC = 1.0

# -------------------------
# State (ostane med reruni)
# -------------------------
if "rows" not in st.session_state:
    st.session_state.rows = []  # list of dicts
if "last_seen_wc" not in st.session_state:
    st.session_state.last_seen_wc = -1

# -------------------------
# Helpers
# -------------------------
def fetch_latest():
    try:
        r = requests.get(API, timeout=1.5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def status_label(s: int) -> str:
    return "RUSH" if int(s) == 1 else "CALM"

def status_emoji(s: int) -> str:
    return "🚨" if int(s) == 1 else "✅"

def status_color(s: int) -> str:
    # used in markdown badge
    return "#FF4B4B" if int(s) == 1 else "#2ECC71"

def p_to_percent(p: float) -> int:
    return int(round(max(0.0, min(1.0, float(p))) * 100))

def style_history_df(df: pd.DataFrame):
    # Barva cele vrstice glede na status
    def row_style(row):
        if row.get("status") == "RUSH":
            return ["background-color: rgba(255, 75, 75, 0.12)"] * len(row)
        else:
            return ["background-color: rgba(46, 204, 113, 0.12)"] * len(row)
    return df.style.apply(row_style, axis=1)

# -------------------------
# Header
# -------------------------
st.title("Rush Index — Live Stream")

with st.expander("ℹ️ Kako brati ta demo?", expanded=True):
    st.markdown(
        """
        **Kaj gledamo?**  
        Aplikacija prikazuje izhod ML modela, ki iz podatkov akcelerometra ocenjuje, ali uporabnik trenutno **hiti (RUSH)** ali se giba **umirjeno (CALM)**.

        - **p(rush)** = verjetnost (0–1), da je okno gibanja “hitenje”.
        - **status** = končna odločitev (CALM/RUSH) na podlagi praga (trenutno 0.5).
        - **window_count** = števec časovnih oken, ki jih je backend že obdelal (da vemo, ali prihajajo novi podatki).

        V spodnjem delu se vodi zgodovina oknov in graf verjetnosti skozi čas.
        """
    )

# -------------------------
# Fetch latest
# -------------------------
data = fetch_latest()

# Layout: left = current card, right = history
left, right = st.columns([1.05, 1.95], gap="large")

# -------------------------
# Current status card (LEFT)
# -------------------------
with left:
    st.subheader("Trenutno stanje")

    if "error" in data:
        st.error(f"API ni dosegljiv: {data['error']}")
        st.info("Preveri, ali uvicorn teče in ali je API pravilen.")
    else:
        wc = int(data.get("window_count", 0))
        p = data.get("p_rush", None)
        s = data.get("status", None)

        # Meta info
        st.caption(f"Backend window_count: **{wc}** | Last seen: **{st.session_state.last_seen_wc}**")

        # Če pride novo okno, ga zapišemo v history
        if wc != st.session_state.last_seen_wc and p is not None and s is not None:
            st.session_state.last_seen_wc = wc

            p = float(p)
            s = int(s)
            stamp = dt.datetime.now().strftime("%H:%M:%S")

            st.session_state.rows.append({
                "window": wc,
                "time": stamp,
                "p_rush": p,
                "status": status_label(s)
            })

        # Card UI
        if p is None or s is None:
            st.info("Čakam na prve podatke… (pošlji /ingest iz telefona)")
        else:
            p = float(p)
            s = int(s)

            # Badge
            badge = f"""
            <div style="
                padding: 14px 16px;
                border-radius: 16px;
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.10);
            ">
                <div style="display:flex; align-items:center; justify-content:space-between;">
                    <div style="font-size: 18px; font-weight: 700;">
                        {status_emoji(s)} {status_label(s)}
                    </div>
                    <div style="
                        font-size: 12px;
                        font-weight: 700;
                        padding: 6px 10px;
                        border-radius: 999px;
                        color: {status_color(s)};
                        background: {status_color(s)}22;
                        border: 1px solid {status_color(s)}55;
                    ">
                        window #{wc}
                    </div>
                </div>
                <div style="margin-top:10px; color: rgba(255,255,255,0.75);">
                    Verjetnost hitenja v zadnjem oknu
                </div>
            </div>
            """
            st.markdown(badge, unsafe_allow_html=True)

            # Metrics
            c1, c2 = st.columns(2)
            with c1:
                st.metric("p(rush)", f"{p:.3f}")
            with c2:
                st.metric("p(rush) %", f"{p_to_percent(p)}%")

            # Progress
            st.progress(p_to_percent(p))

            # Small hint text
            if s == 1:
                st.error("Sistem trenutno zaznava **hitenje** glede na prag (0.5).")
            else:
                st.success("Sistem trenutno zaznava **umirjeno gibanje** glede na prag (0.5).")

            st.caption("Opomba: status je odvisen od praga. Kasneje lahko dodamo personaliziran prag.")

# -------------------------
# History + Chart (RIGHT)
# -------------------------
with right:
    st.subheader("Zgodovina in trend")

    df = pd.DataFrame(st.session_state.rows)

    if len(df) == 0:
        st.info("Ko prispe prvo okno, se bo tukaj pokazala tabela in graf.")
    else:
        # Zadnjih N vrstic
        last_n = 40
        df_show = df.tail(last_n).copy()

        # Lepši prikaz p_rush
        df_show["p_rush"] = df_show["p_rush"].astype(float).round(3)

        # Tabela z barvami po vrstici
        st.dataframe(
            style_history_df(df_show),
            use_container_width=True,
            height=420
        )

        # Graf
        st.markdown("**Trend p(rush) skozi okna**")
        st.line_chart(df.set_index("window")["p_rush"])

# -------------------------
# Refresh
# -------------------------
time.sleep(REFRESH_SEC)
st.rerun()


# import streamlit as st
# import requests
# import time
# import pandas as pd
# import datetime as dt

# st.set_page_config(layout="wide")
# st.title("Rush Index — Live Stream")

# API = "http://127.0.0.1:8000/latest"
# REFRESH_SEC = 1.0

# # -------------------------
# # State (ostane med reruni)
# # -------------------------
# if "rows" not in st.session_state:
#     st.session_state.rows = []  # list of dicts

# # zadnje videni window_count (da ne dupliciramo istih vrednosti)
# if "last_seen_wc" not in st.session_state:
#     st.session_state.last_seen_wc = -1

# status_box = st.empty()
# meta_box = st.empty()
# table_box = st.empty()
# chart_box = st.empty()

# def fetch_latest():
#     try:
#         r = requests.get(API, timeout=1.5)
#         r.raise_for_status()
#         return r.json()
#     except Exception as e:
#         status_box.warning(f"API ni dosegljiv: {e}")
#         return None

# # -------------------------
# # Main loop (rerun-based)
# # -------------------------
# data = fetch_latest()

# if data is not None:
#     wc = int(data.get("window_count", 0))
#     p = data.get("p_rush", None)
#     s = data.get("status", None)

#     # meta info, da vidiš ali dejansko prihajajo nova okna
#     meta_box.caption(f"Backend window_count: {wc} | Last seen: {st.session_state.last_seen_wc}")

#     # dodaj samo, ko pride NOVO okno (wc se spremeni)
#     if wc != st.session_state.last_seen_wc and p is not None and s is not None:
#         st.session_state.last_seen_wc = wc

#         p = float(p)
#         s = int(s)
#         stamp = dt.datetime.now().strftime("%H:%M:%S")

#         st.session_state.rows.append({
#             "window": wc,          # real okno iz backenda
#             "time": stamp,
#             "p_rush": p,
#             "status": "RUSH" if s == 1 else "CALM"
#         })

#         if s == 1:
#             status_box.error(f"🚨 #{wc} — RUSH (p={p:.3f}) @ {stamp}")
#         else:
#             status_box.success(f"✅ #{wc} — CALM (p={p:.3f}) @ {stamp}")
#     else:
#         # Ni novega okna (Streamlit samo poll-a), pokaži zadnje znano stanje
#         if p is None or s is None:
#             status_box.info("Čakam na prve podatke (pošlji /ingest)…")
#         else:
#             p = float(p)
#             s = int(s)
#             if s == 1:
#                 status_box.error(f"🚨 (zadnje) RUSH (p={p:.3f})")
#             else:
#                 status_box.success(f"✅ (zadnje) CALM (p={p:.3f})")

# # -------------------------
# # Display
# # -------------------------
# df = pd.DataFrame(st.session_state.rows)

# if len(df):
#     table_box.dataframe(df, use_container_width=True)
#     chart_box.line_chart(df.set_index("window")["p_rush"])

# # Refresh
# time.sleep(REFRESH_SEC)
# st.rerun()
