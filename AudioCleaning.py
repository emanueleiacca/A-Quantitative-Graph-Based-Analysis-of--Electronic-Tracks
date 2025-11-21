import librosa
import soundfile as sf
import numpy as np
from scipy.signal import butter, filtfilt
import noisereduce as nr
from pathlib import Path
from tqdm import tqdm

# --------------------
# 1) Band-pass filter
# --------------------
def bandpass_filter(y, sr, lowcut=30.0, highcut=18000.0, order=4):
    """
    Filtro passa-banda 'gentile' per techno:
    - lowcut: tieni un po' di sub (30 Hz)
    - highcut: tieni aria fino a 18 kHz
    Funziona sia mono che stereo.
    """
    nyq = 0.5 * sr
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")

    if y.ndim == 1:
        # mono
        return filtfilt(b, a, y)
    else:
        # stereo: filtra ogni canale separatamente
        y_filt = np.zeros_like(y)
        for ch in range(y.shape[0]):
            y_filt[ch] = filtfilt(b, a, y[ch])
        return y_filt

# --------------------
# 2) Peak normalization
# --------------------
def normalize_peak(y, peak_target=0.99):
    """
    Normalizza il segnale in modo che il valore assoluto massimo
    sia peak_target (tipicamente ~1.0).
    Funziona sia per segnali mono (1D) che stereo (2D).
    """
    peak = np.max(np.abs(y))
    if peak == 0:
        return y
    return y * (peak_target / peak)


# --------------------
# 3) Noise estimation from quiet parts (for full songs)
# --------------------
def estimate_noise_from_quiet_parts(y, sr, frame_duration=0.5, percentile=20):
    """
    Divide il brano in frame, calcola l'RMS di ciascun frame,
    prende il percentile più basso (ad es. 20%) come stima del rumore.
    """
    frame_len = int(frame_duration * sr)
    if frame_len <= 0 or len(y) < frame_len:
        # fallback: primi 0.5 secondi
        return y[: int(0.5 * sr)]

    # tronca per avere un numero intero di frame
    usable_len = len(y) - (len(y) % frame_len)
    frames = y[:usable_len].reshape(-1, frame_len)

    rms = np.sqrt(np.mean(frames**2, axis=1))
    threshold = np.percentile(rms, percentile)
    noise_frames = frames[rms <= threshold]

    if noise_frames.size == 0:
        # se non trova niente di sufficientemente "quiet",
        # prendi comunque i primi 0.5 s
        return y[: int(0.5 * sr)]

    return noise_frames.flatten()


def clean_techno(
    in_path,
    out_path,
    sr=44100,
    use_mono=True,
    apply_bandpass=True,
    lowcut=30.0,
    highcut=18000.0,
    trim_edges=False,
    trim_db=40.0,
):
    """
    Pipeline di pulizia pensata per tracce techno intere.

    - sr:      44100 Hz (più fedele sui transienti rispetto a 22050)
    - use_mono: True = mix in mono (consigliato per l'analisi)
    - band-pass: 30–18000 Hz di default, abbastanza morbido
    - niente denoise: evitiamo ovattamento nei momenti forti
    """

    # 1. Carica audio (mono o stereo)
    y, sr = librosa.load(in_path, sr=sr, mono=use_mono)

    # 2. (Opzionale) trim ai bordi, ma di default lo lascio spento per techno
    if trim_edges:
        if y.ndim == 1:
            y_trimmed, _ = librosa.effects.trim(y, top_db=trim_db)
            if len(y_trimmed) > 0.1 * sr:
                y = y_trimmed
        else:
            # per stereo: trim su una versione mono "di servizio"
            y_mono_for_trim = librosa.to_mono(y)
            y_trimmed, idx = librosa.effects.trim(y_mono_for_trim, top_db=trim_db)
            if len(y_trimmed) > 0.1 * sr:
                start, end = idx
                y = y[:, start:end]

    # 3. Normalizzazione iniziale del livello
    y = normalize_peak(y, peak_target=0.99)

    # 4. Band-pass (facoltativo ma consigliato per coerenza tra brani)
    if apply_bandpass:
        y = bandpass_filter(y, sr, lowcut=lowcut, highcut=highcut)

    # 5. Normalizzazione finale (dopo il filtro i picchi cambiano)
    y = normalize_peak(y, peak_target=0.99)

    # 6. Salvataggio
    # se use_mono=True → y è 1D; se False → 2D (canali, campioni)
    if y.ndim == 1:
        sf.write(out_path, y.astype(np.float32), sr)
    else:
        # soundfile accetta (n_samples, n_channels), quindi trasponiamo
        sf.write(out_path, y.T.astype(np.float32), sr)

    return out_path

def summarize_audio(path, sr=44100):
    y, sr = librosa.load(path, sr=sr, mono=True)

    # livello globale
    rms_global = np.sqrt(np.mean(y**2))

    # STFT per feature spettrali
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512)) ** 2

    centroid = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
    bandwidth = librosa.feature.spectral_bandwidth(S=S, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(S=S, sr=sr, roll_percent=0.85)[0]
    flatness = librosa.feature.spectral_flatness(S=S)[0]

    # MFCC (primi 5 come riassunto timbrico grossolano)
    mfcc = librosa.feature.mfcc(S=librosa.power_to_db(S + 1e-10), sr=sr, n_mfcc=5)

    summary = {
        "rms": rms_global,
        "centroid_mean": np.mean(centroid),
        "centroid_std": np.std(centroid),
        "bandwidth_mean": np.mean(bandwidth),
        "rolloff_mean": np.mean(rolloff),
        "flatness_mean": np.mean(flatness),
    }

    # media dei primi 5 MFCC
    for i in range(mfcc.shape[0]):
        summary[f"mfcc{i+1}_mean"] = np.mean(mfcc[i])

    return summary