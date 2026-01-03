from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import pandas as pd
import io
import joblib
from pathlib import Path
import numpy as np

from feature_utils import extract_features_from_window

app = FastAPI()

# ------------------------------------------------------------
# Paths / config
# ------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent
TAG = "5s_50pct_purity80"

FEATURES_PATH = DATA_DIR / "prepared" / f"features_{TAG}.parquet"

# Priporočeno: shranjen pipeline (StandardScaler + LogisticRegression)
PIPE_PATH = DATA_DIR / "models" / f"logreg_pipe_{TAG}.joblib"

# Fallback: goli model (ni priporočeno)
MODEL_FALLBACK_PATH = DATA_DIR / "models" / f"logisticregression_{TAG}.joblib"


# ------------------------------------------------------------
# Training feature columns (load once)
# ------------------------------------------------------------
_train_df_cols = pd.read_parquet(FEATURES_PATH, engine="pyarrow").columns
TRAIN_FEATURE_COLS = [
    c for c in _train_df_cols
    if c not in ["label", "subject_id", "start_ts", "end_ts"]
]


# ------------------------------------------------------------
# Load model/pipeline once
# ------------------------------------------------------------
def _load_predictor():
    if PIPE_PATH.exists():
        print(f"[server] Loading PIPELINE: {PIPE_PATH}")
        return joblib.load(PIPE_PATH), True

    print(f"[server][WARN] Pipeline not found: {PIPE_PATH}")
    print(f"[server][WARN] Falling back to raw model (may cause bad probabilities).")
    print(f"[server] Loading MODEL: {MODEL_FALLBACK_PATH}")
    return joblib.load(MODEL_FALLBACK_PATH), False


PREDICTOR, IS_PIPELINE = _load_predictor()
print(f"[server] IS_PIPELINE = {IS_PIPELINE} | predictor type = {type(PREDICTOR)}")


# ------------------------------------------------------------
# Last state (for Streamlit polling)
# ------------------------------------------------------------
LAST_STATE = {
    "p_rush": None,
    "status": None,
    "window_count": 0
}


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _ensure_features_df(X) -> pd.DataFrame:
    """Normalizira output iz feature_utils v DataFrame z imeni stolpcev."""
    if isinstance(X, pd.DataFrame):
        return X.copy()
    if isinstance(X, pd.Series):
        return pd.DataFrame([X.to_dict()])
    if isinstance(X, dict):
        return pd.DataFrame([X])

    arr = np.asarray(X).ravel()
    return pd.DataFrame([arr])


def _align_to_training_cols(X: pd.DataFrame) -> pd.DataFrame:
    """Poravna featureje na trening: doda manjkajoče (0), odstrani odvečne, uskladi vrstni red."""
    for col in TRAIN_FEATURE_COLS:
        if col not in X.columns:
            X[col] = 0.0

    X = X[TRAIN_FEATURE_COLS]
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return X


def _predict_p_rush(X: pd.DataFrame) -> float:
    """Vrne p(rush) = P(class=1)."""
    proba = PREDICTOR.predict_proba(X)
    return float(proba[:, 1][0])


def _prepare_sensor_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    1) zahteva ax, ay, az (iOS CSV)
    2) pretvori v numeric in odstrani NaN
    3) po potrebi pretvori g -> m/s^2 (heuristika)
    4) preimenuje v x,y,z (ker feature_utils + trening featureji so x_*, y_*, z_*)
    """
    required = {"ax", "ay", "az"}
    if not required.issubset(df.columns):
        raise ValueError("CSV must contain columns: ax, ay, az (timestamp_ms optional).")

    # numeric + drop NaN
    for c in ["ax", "ay", "az"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["ax", "ay", "az"]).reset_index(drop=True)

    # Heuristika enot:
    # - če je max abs < 3 -> skoraj sigurno 'g' (CoreMotion), pretvori v m/s^2
    # - če je že ~10-20 -> že m/s^2, ne dotikaj se
    mx = float(np.nanmax(np.abs(df[["ax", "ay", "az"]].values)))
    if mx < 3.0:
        g = 9.80665
        df["ax"] *= g
        df["ay"] *= g
        df["az"] *= g

    # rename v x,y,z za feature extraction
    df = df.rename(columns={"ax": "x", "ay": "y", "az": "z"})
    return df


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.post("/ingest")
async def ingest(request: Request):
    try:
        body = await request.body()
        df_raw = pd.read_csv(io.BytesIO(body))

        # Debug (raw)
        print("[ingest] raw rows:", len(df_raw), "cols:", df_raw.columns.tolist())

        # Prepare + normalize
        df = _prepare_sensor_df(df_raw)

        # Debug (prepared)
        print("[ingest] prepared rows:", len(df))
        print("[ingest] x range:", df["x"].min(), df["x"].max())
        print("[ingest] y range:", df["y"].min(), df["y"].max())
        print("[ingest] z range:", df["z"].min(), df["z"].max())

        # Extract features
        feats = extract_features_from_window(df)

        # To DataFrame + align
        X = _ensure_features_df(feats)
        X = _align_to_training_cols(X)

        # Predict
        p_rush = _predict_p_rush(X)
        status = int(p_rush >= 0.5)

        # update last state
        LAST_STATE["p_rush"] = p_rush
        LAST_STATE["status"] = status
        LAST_STATE["window_count"] += 1

        # Optional: print a couple of key features once in a while
        if LAST_STATE["window_count"] % 10 == 1:
            try:
                row = X.iloc[0]
                print("[debug] x_std:", float(row.get("x_std", np.nan)),
                      "mag_mean:", float(row.get("mag_mean", np.nan)),
                      "fft_energy:", float(row.get("fft_energy_0p5_4Hz", np.nan)))
            except Exception:
                pass

        return JSONResponse({"p_rush": p_rush, "status": status})

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/latest")
def latest():
    """Streamlit bere trenutno stanje."""
    return LAST_STATE
