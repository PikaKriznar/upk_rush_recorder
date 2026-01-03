
import numpy as np
import pandas as pd
import joblib
import streamlit as st
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(page_title="Rush Index Demo", layout="wide")

# -----------------------
# Nastavitve (spremeni po potrebi)
# -----------------------
DATA_DIR = Path(r"/Users/pikakriznar/Documents/1_letnik_MAG/UPK/Projekti/Razpoznava_hitenja_projekt/data/wisdm+smartphone+and+smartwatch+activity+and+biometrics+dataset/wisdm-dataset")
TAG = "5s_50pct_purity80"
MODEL_PATH = DATA_DIR / "models" / "logisticregression5s_50pct_purity80.joblib"
FEATURES_PATH = DATA_DIR / "prepared" / f"features_{TAG}.parquet"

# -----------------------
# Helperji
# -----------------------
def rush_index(binary_series: pd.Series) -> float:
    return 100.0 * float(binary_series.mean()) if len(binary_series) else 0.0

def personalized_threshold(p_rush_values: pd.Series, method="quantile", q=0.9) -> float:
    vals = p_rush_values.to_numpy()
    if method == "quantile":
        return float(np.quantile(vals, q))
    elif method == "mean_std":
        return float(vals.mean() + 0.5 * vals.std())
    else:
        raise ValueError("Unknown method")

def generate_feedback(ri: float) -> str:
    if ri > 40:
        return "Pogosto hitiš. Morda bi ti koristil kratek odmor ali bolj umirjen tempo."
    elif ri > 20:
        return "Občasno hitiš. Poskusi bolj enakomerno razporediti obveznosti."
    else:
        return "Tvoj tempo je večinoma umirjen. Odlično!"

@st.cache_data
def load_features(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)

@st.cache_resource
def load_model(path: Path):
    return joblib.load(path)

# -----------------------
# UI: Sidebar
# -----------------------
st.sidebar.title("Nastavitve")
mode = st.sidebar.radio("Pogled", ["Minimal", "Analytic"], index=1)

threshold_mode = st.sidebar.selectbox("Personaliziran prag (kalibracija)", ["quantile (q)", "mean+0.5*std"])
q = st.sidebar.slider("q (če quantile)", min_value=0.70, max_value=0.99, value=0.90, step=0.01)

global_thr = st.sidebar.slider("Globalni prag p(rush)", min_value=0.1, max_value=0.9, value=0.5, step=0.05)

# -----------------------
# Load
# -----------------------
df = load_features(FEATURES_PATH)
model = load_model(MODEL_PATH)

feature_cols = [c for c in df.columns if c not in ["label", "subject_id", "start_ts", "end_ts"]]
X = df[feature_cols].to_numpy()
df = df.copy()
df["p_rush"] = model.predict_proba(X)[:, 1]

subjects = sorted(df["subject_id"].unique().tolist())
subject_id = st.sidebar.selectbox("Izberi uporabnika (subject_id)", subjects, index=0)

user_df = df[df["subject_id"] == subject_id].copy()
user_df = user_df.sort_values("start_ts").reset_index(drop=True)

# Status (global)
user_df["rush_global"] = (user_df["p_rush"] >= global_thr).astype(int)
ri_global = rush_index(user_df["rush_global"])

# Status (personal)
if threshold_mode.startswith("quantile"):
    thr_user = personalized_threshold(user_df["p_rush"], method="quantile", q=q)
else:
    thr_user = personalized_threshold(user_df["p_rush"], method="mean_std")

user_df["rush_personal"] = (user_df["p_rush"] >= thr_user).astype(int)
ri_personal = rush_index(user_df["rush_personal"])

# -----------------------
# Header
# -----------------------
st.title("Rush Index — demo (WISDM)")
st.caption("Binarni model: walking(0) vs jogging(1). 'Personal' uporablja prag iz kalibracije uporabnika.")

colA, colB, colC = st.columns(3)
colA.metric("Rush Index (global)", f"{ri_global:.1f}%")
colB.metric("Rush Index (personal)", f"{ri_personal:.1f}%")
colC.metric("Personal threshold", f"{thr_user:.3f}")

st.info(generate_feedback(ri_personal))

# -----------------------
# Vizualizacija
# -----------------------
x = np.arange(len(user_df))

if mode == "Minimal":
    # samo zadnje stanje + barva
    last_status = int(user_df["rush_personal"].iloc[-1]) if len(user_df) else 0
    if last_status == 1:
        st.error("Trenutno stanje: HITI (personal)")
    else:
        st.success("Trenutno stanje: NORMALNO (personal)")

else:
    left, right = st.columns([2,1])

    with left:
        fig = plt.figure()
        plt.plot(x, user_df["p_rush"], label="p(rush)")
        plt.axhline(global_thr, linestyle="--", label=f"global_thr={global_thr:.2f}")
        plt.axhline(thr_user, linestyle="--", label=f"personal_thr={thr_user:.2f}")
        plt.ylim(0, 1)
        plt.xlabel("Okno (časovna os)")
        plt.ylabel("p(rush)")
        plt.title(f"Uporabnik {subject_id}: p(rush) skozi čas")
        plt.legend()
        st.pyplot(fig)

        # segment graf (binary)
        fig2 = plt.figure()
        plt.step(x, user_df["rush_global"], where="post", label="global status")
        plt.step(x, user_df["rush_personal"], where="post", label="personal status")
        plt.yticks([0,1], ["normalno", "hiti"])
        plt.xlabel("Okno (časovna os)")
        plt.title("Binarni status (0/1) skozi čas")
        plt.legend()
        st.pyplot(fig2)

    with right:
        st.subheader("Povzetek")
        st.write(f"Št. oken: **{len(user_df)}**")
        st.write(f"Globalni prag: **{global_thr:.2f}**")
        st.write(f"Personal prag: **{thr_user:.3f}**")

        st.subheader("Primeri priporočil")
        st.write("- Če pogosto hitiš: predlagaj odmor / spremembo rutine.")
        st.write("- Če redko hitiš: motivacijsko sporočilo.")
        st.write("- (Nadgradnja) Upoštevaj čas dneva in epizode hitenja.")

st.divider()
st.subheader("Podatki (preview)")
st.dataframe(user_df[["start_ts","end_ts","label","p_rush","rush_global","rush_personal"]].head(20))
