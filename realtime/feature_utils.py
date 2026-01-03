import numpy as np
import pandas as pd
from scipy.fft import rfft, rfftfreq


def _fft_features(signal: np.ndarray, fs: float = 20.0):
    """
    Izračun FFT značilnic za signal.
    Predpostavka: sampling rate ~20 Hz (WISDM / iOS)
    """
    signal = signal.astype(float)

    # odstrani DC komponento
    signal = signal - signal.mean()

    fft_vals = np.abs(rfft(signal))
    freqs = rfftfreq(len(signal), d=1.0 / fs)

    # energija v pasu 0.5–4 Hz (hoja / tek)
    band = (freqs >= 0.5) & (freqs <= 4.0)
    energy = float(np.sum(fft_vals[band] ** 2))

    # dominantna frekvenca
    peak_freq = float(freqs[np.argmax(fft_vals)])

    return energy, peak_freq


def extract_features_from_window(df: pd.DataFrame) -> dict:
    """
    df mora imeti stolpce: x, y, z
    vrne dict z imenovanimi featureji (kompatibilno s treningom)
    """

    required = {"x", "y", "z"}
    if not required.issubset(df.columns):
        raise ValueError("DataFrame must contain columns: x, y, z")

    x = df["x"].to_numpy(dtype=float)
    y = df["y"].to_numpy(dtype=float)
    z = df["z"].to_numpy(dtype=float)

    mag = np.sqrt(x*x + y*y + z*z)

    # osnovne statistike
    feats = {
        # x
        "x_mean": float(x.mean()),
        "x_std": float(x.std()),
        "x_min": float(x.min()),
        "x_max": float(x.max()),

        # y
        "y_mean": float(y.mean()),
        "y_std": float(y.std()),
        "y_min": float(y.min()),
        "y_max": float(y.max()),

        # z
        "z_mean": float(z.mean()),
        "z_std": float(z.std()),
        "z_min": float(z.min()),
        "z_max": float(z.max()),

        # magnitude
        "mag_mean": float(mag.mean()),
        "mag_std": float(mag.std()),
        "mag_min": float(mag.min()),
        "mag_max": float(mag.max()),
    }

    # FFT značilnice (ZELO POMEMBNO)
    energy, peak_freq = _fft_features(mag)
    feats["fft_energy_0p5_4Hz"] = energy
    feats["fft_peak_freq"] = peak_freq

    return feats
