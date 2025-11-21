import librosa
import numpy as np

def _safe_normalize(vec, axis=0, eps=1e-10):
    denom = np.sum(vec, axis=axis, keepdims=True)
    denom = np.maximum(denom, eps)
    return vec / denom


def extract_features(
    wav_path,
    sr=44100,
    hop_seconds=0.25,
    win_seconds=1.0,
    n_mfcc=40,
    n_chroma_micro=24,
):
    """
    Estrae un vettore di stato ricco per ogni frame del brano.

    Output:
      - trajectory: np.ndarray di shape (T, d)
      - feature_names: lista di stringhe, una per ogni colonna di trajectory
    """

    # 1. Caricamento audio (mono, già pulito a monte)
    y, sr = librosa.load(wav_path, sr=sr, mono=True)

    # 2. Parametri STFT
    hop_length = int(hop_seconds * sr)
    win_length = int(win_seconds * sr)
    n_fft = 2 ** int(np.ceil(np.log2(win_length)))  # prossima potenza di 2

    # 3. Spettrogramma di potenza
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length,
                            win_length=win_length)) ** 2
    S_amp = np.sqrt(S)  # ampiezza per funzioni spectral di librosa
    S_db = librosa.power_to_db(S + 1e-10)

    # Frequenze per descrittori custom
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    freqs = freqs[:, np.newaxis]  # shape (F, 1)

    # -----------------------------
    # 4. MFCCs (timbre envelope)
    # -----------------------------
    mfcc = librosa.feature.mfcc(S=S_db, sr=sr, n_mfcc=n_mfcc)  # (n_mfcc, T)

    # ---------------------------------
    # 5. Spettral descriptors (texture)
    # ---------------------------------
    centroid = librosa.feature.spectral_centroid(S=S_amp, sr=sr)         # (1, T)
    bandwidth = librosa.feature.spectral_bandwidth(S=S_amp, sr=sr)       # (1, T)
    rolloff85 = librosa.feature.spectral_rolloff(S=S_amp, sr=sr,
                                                 roll_percent=0.85)      # (1, T)
    rolloff95 = librosa.feature.spectral_rolloff(S=S_amp, sr=sr,
                                                 roll_percent=0.95)      # (1, T)
    flatness = librosa.feature.spectral_flatness(S=S_amp)               # (1, T)

    # Spectral flux (usando onset envelope)
    flux = librosa.onset.onset_strength(S=S_amp, sr=sr)[np.newaxis, :]  # (1, T)

    # Entropy, crest, spread – calcolati dal power spectrum S
    # Normalizziamo lo spettro in probabilità per frame
    P_norm = _safe_normalize(S, axis=0)  # (F, T)

    # Entropia normalizzata (0–1)
    entropy = -np.sum(P_norm * np.log(P_norm + 1e-10), axis=0)
    entropy /= np.log(P_norm.shape[0] + 1e-10)
    entropy = entropy[np.newaxis, :]  # (1, T)

    # Spectral crest: max / mean
    crest = (np.max(S, axis=0) / (np.mean(S, axis=0) + 1e-10))[np.newaxis, :]

    # Spectral spread: varianza attorno al centroid (in Hz)
    # centroid: (1, T), freqs: (F, 1)
    # usiamo P_norm come pesi
    centroid_Hz = centroid  # già in Hz
    spread = np.sqrt(np.sum(P_norm * (freqs - centroid_Hz) ** 2, axis=0))
    spread = spread[np.newaxis, :]  # (1, T)

    # -----------------------------
    # 6. Energy / dynamics
    # -----------------------------
    # RMS su y, allineato alla STFT
    rms = librosa.feature.rms(y=y, frame_length=win_length,
                              hop_length=hop_length)  # (1, T_rms)

    # Onset strength come "transient strength"
    transient_strength = flux.copy()  # già (1, T), coerente con S

    # -----------------------------
    # 7. Pitch / Chroma domain
    # -----------------------------
    # Chroma microtonale (24 bin)
    chroma_micro = librosa.feature.chroma_cqt(
        y=y,
        sr=sr,
        hop_length=hop_length,
        n_chroma=n_chroma_micro,
        bins_per_octave=n_chroma_micro,
    )  # (24, T_chroma)

    # Chroma energy concentration (max / somma)
    chroma_norm = _safe_normalize(chroma_micro, axis=0)
    chroma_concentration = np.max(chroma_norm, axis=0)[np.newaxis, :]  # (1, T)

    # -----------------------------
    # 8. Allineamento temporale
    # -----------------------------
    # Troviamo T comune a tutte le feature
    T_list = [
        mfcc.shape[1],
        centroid.shape[1],
        bandwidth.shape[1],
        rolloff85.shape[1],
        rolloff95.shape[1],
        flatness.shape[1],
        flux.shape[1],
        entropy.shape[1],
        crest.shape[1],
        spread.shape[1],
        rms.shape[1],
        transient_strength.shape[1],
        chroma_micro.shape[1],
        chroma_concentration.shape[1],
    ]
    T = min(T_list)

    def cut(feat):
        return feat[:, :T]

    mfcc = cut(mfcc)
    centroid = cut(centroid)
    bandwidth = cut(bandwidth)
    rolloff85 = cut(rolloff85)
    rolloff95 = cut(rolloff95)
    flatness = cut(flatness)
    flux = cut(flux)
    entropy = cut(entropy)
    crest = cut(crest)
    spread = cut(spread)
    rms = cut(rms)
    transient_strength = cut(transient_strength)
    chroma_micro = cut(chroma_micro)
    chroma_concentration = cut(chroma_concentration)

    # -----------------------------
    # 9. Concatenazione finale
    # -----------------------------
    features = np.vstack([
        mfcc,                 # n_mfcc
        centroid,             # 1
        bandwidth,            # 1
        rolloff85,            # 1
        rolloff95,            # 1
        flux,                 # 1
        entropy,              # 1
        crest,                # 1
        spread,               # 1
        flatness,             # 1
        rms,                  # 1
        transient_strength,   # 1
        chroma_micro,         # n_chroma_micro
        chroma_concentration, # 1
    ])  # shape (d, T)

    trajectory = features.T  # (T, d)

    # -----------------------------
    # 10. Nomi delle feature
    # -----------------------------
    feature_names = []

    # MFCC
    for i in range(n_mfcc):
        feature_names.append(f"mfcc_{i+1}")

    # Spectral descriptors
    feature_names += [
        "spec_centroid",
        "spec_bandwidth",
        "spec_rolloff_85",
        "spec_rolloff_95",
        "spec_flux",
        "spec_entropy",
        "spec_crest",
        "spec_spread",
        "spec_flatness",
        "rms",
        "transient_strength",
    ]

    # Chroma micro
    for i in range(n_chroma_micro):
        feature_names.append(f"chroma24_{i+1}")

    feature_names.append("chroma_concentration")

    assert trajectory.shape[1] == len(feature_names)

    return trajectory, feature_names