import numpy as np
import pandas as pd
import librosa
import pretty_midi
import networkx as nx
import matplotlib.pyplot as plt

# Audio config 
SR = 44100
FRAME_LENGTH = 1024
HOP_LENGTH = 512
EPS = 1e-10

# MIDI → full-pitch chord sequence (paper method)

def midi_chord_sequence_fullpitch(midi_path):
    """
    From MIDI -> sequence of chords in *full MIDI pitch* space (0..127).
    - Each chord = all pitches starting at the same time (exact start times).
    - Chords are ordered by time.
    - Consecutive duplicate chords are merged.
    This matches the construction in Di Marco et al.
    """
    pm = pretty_midi.PrettyMIDI(midi_path)

    # Map start_time -> list of pitches across all non-drum instruments
    time_to_pitches = {}

    for inst in pm.instruments:
        if inst.is_drum:
            continue
        for note in inst.notes:
            t = note.start
            if t not in time_to_pitches:
                time_to_pitches[t] = []
            time_to_pitches[t].append(note.pitch)

    if not time_to_pitches:
        return []

    # Build ordered chord list
    chords = []
    for t in sorted(time_to_pitches.keys()):
        chord = tuple(sorted(set(time_to_pitches[t])))
        if len(chord) > 0:
            chords.append(chord)

    # Compress consecutive duplicates
    final = []
    prev = None
    for c in chords:
        if c != prev:
            final.append(c)
            prev = c

    return final

# MIDI → pitch-class chord sequence

def midi_chord_sequence_fullpitch(midi_path, time_tol=1e-3):
    """
    From MIDI -> sequence of chords in *full MIDI pitch* space (0..127).
    Each chord is a tuple of pitches; consecutive duplicates merged.
    Follows the construction in Di Marco et al. (per instrument/channel).
    """
    pm = pretty_midi.PrettyMIDI(midi_path)

    chords_all = []

    for inst in pm.instruments:
        if inst.is_drum:
            continue

        # Collect notes for this instrument and sort by onset
        notes = sorted(inst.notes, key=lambda n: n.start)
        if not notes:
            continue

        time_slices = []
        current_time = None
        current_chord = []

        for n in notes:
            t = n.start
            p = n.pitch
            if current_time is None:
                current_time = t
                current_chord = [p]
            elif abs(t - current_time) <= time_tol:
                current_chord.append(p)
            else:
                # close previous slice (full pitches, no mod 12)
                chord = tuple(sorted(set(current_chord)))
                if len(chord) > 0:
                    time_slices.append(chord)
                current_time = t
                current_chord = [p]

        if current_chord:
            chord = tuple(sorted(set(current_chord)))
            if len(chord) > 0:
                time_slices.append(chord)

        # compress consecutive duplicates in this instrument
        prev = None
        for c in time_slices:
            if c != prev:
                chords_all.append(c)
                prev = c

    return chords_all

# Audio → chroma chord sequence

def chroma_chord_sequence(y, sr=SR, hop_length=HOP_LENGTH, thresh=CHROMA_THRESH):
    """
    From audio -> chroma -> sequence of chords in pitch-class space (0..11).
    Each chord is a tuple of pitch classes; consecutive duplicates merged.
    """
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    T = chroma.shape[1]

    chords = []
    prev_chord = None

    for t in range(T):
        frame = chroma[:, t]
        if frame.max() < 1e-6:
            active = ()
        else:
            act = np.where(frame >= thresh * frame.max())[0]
            active = tuple(sorted(set(act.tolist())))

        if active != prev_chord and len(active) > 0:
            chords.append(active)
            prev_chord = active

    return chords

# Build graph from chord sequence (shared for MIDI & audio)

def build_chord_transition_graph(chords):
    """
    chords: list of tuples of integer pitches (e.g., MIDI notes or pitch classes)
    Returns DiGraph with edges weighted by transition counts.
    No self-loops.
    """
    G = nx.DiGraph()
    for chord_a, chord_b in zip(chords[:-1], chords[1:]):
        for i in chord_a:
            for j in chord_b:
                if i == j:
                    continue  # no self-loops
                if G.has_edge(i, j):
                    G[i][j]["weight"] += 1
                else:
                    G.add_edge(i, j, weight=1)
    return G



def weighted_reciprocity(G):
    W = 0.0
    W_bidir = 0.0
    for u, v, data in G.edges(data=True):
        w_uv = data["weight"]
        W += w_uv
        if G.has_edge(v, u):
            w_vu = G[v][u]["weight"]
            W_bidir += min(w_uv, w_vu)
    if W == 0:
        return 0.0
    return W_bidir / W


def shuffle_outgoing_weights_preserve_strength(G, rng=None):
    if rng is None:
        rng = np.random.default_rng()
    H = G.copy()
    for u in H.nodes():
        out_edges = list(H.out_edges(u, data=True))
        if len(out_edges) <= 1:
            continue
        weights = [d["weight"] for _, _, d in out_edges]
        rng.shuffle(weights)
        for (idx, (src, dst, data)) in enumerate(out_edges):
            data["weight"] = float(weights[idx])
    return H


def normalized_weighted_reciprocity(G, n_null=20):
    r_real = weighted_reciprocity(G)
    if G.number_of_edges() == 0:
        return r_real, 0.0, 0.0

    r_null_vals = []
    for _ in range(n_null):
        H = shuffle_outgoing_weights_preserve_strength(G)
        r_null_vals.append(weighted_reciprocity(H))

    r_null = float(np.mean(r_null_vals))
    if r_null >= 1.0:
        rho = 0.0
    else:
        rho = (r_real - r_null) / (1 - r_null)
    return r_real, r_null, rho


def node_entropy(G, u):
    out_edges = list(G.out_edges(u, data=True))
    k = len(out_edges)
    if k <= 1:
        return 0.0
    weights = np.array([d["weight"] for _, _, d in out_edges], dtype=float)
    p = weights / (weights.sum() + EPS)
    H = -np.sum(p * np.log(p + EPS))
    H_max = np.log(k + EPS)
    return H / (H_max + EPS)


def mean_node_entropy(G):
    if G.number_of_nodes() == 0:
        return 0.0
    entropies = [node_entropy(G, u) for u in G.nodes()]
    return float(np.mean(entropies))


def global_efficiency_unweighted(G):
    if G.number_of_nodes() <= 1:
        return 0.0
    sp = dict(nx.all_pairs_shortest_path_length(G))
    nodes = list(G.nodes())
    s = 0.0
    count = 0
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            d = sp.get(i, {}).get(j, np.inf)
            if np.isfinite(d) and d > 0:
                s += 1.0 / d
                count += 1
    return float(s / count) if count > 0 else 0.0


def global_efficiency_weighted(G):
    if G.number_of_nodes() <= 1:
        return 0.0
    H = G.copy()
    for u, v, data in H.edges(data=True):
        data["cost"] = 1.0 / float(data["weight"])

    sp = dict(nx.all_pairs_dijkstra_path_length(H, weight="cost"))
    nodes = list(H.nodes())
    s = 0.0
    count = 0
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            d = sp.get(i, {}).get(j, np.inf)
            if np.isfinite(d) and d > 0:
                s += 1.0 / d
                count += 1
    return float(s / count) if count > 0 else 0.0


def interval_embedding_12d(G):
    """
    12D interval profile over pitch classes; L2-normalized.
    """
    counts = np.zeros(12, dtype=float)
    for u, v, data in G.edges(data=True):
        w = float(data["weight"])
        interval = (v - u) % 12
        counts[interval] += w
    norm = np.linalg.norm(counts)
    if norm > 0:
        return counts / norm
    return counts

# Convenience wrappers for “MIDI network” and “audio network”

def compute_midi_network_metrics(midi_path):
    # Use full MIDI pitches for the graph, as in the paper
    chords = midi_chord_sequence_fullpitch(midi_path)
    G = build_chord_transition_graph(chords)

    metrics = {}
    metrics["n_nodes"] = G.number_of_nodes()
    metrics["n_edges"] = G.number_of_edges()
    metrics["density"] = nx.density(G)

    r_real, r_null, rho = normalized_weighted_reciprocity(G)
    metrics["r_real"] = r_real
    metrics["r_null"] = r_null
    metrics["rho_norm"] = rho

    metrics["mean_entropy"] = mean_node_entropy(G)
    metrics["eff_unweighted"] = global_efficiency_unweighted(G)
    metrics["eff_weighted"] = global_efficiency_weighted(G)

    # Intervals now come from full pitches, then mod 12
    metrics["interval_vec"] = interval_embedding_12d(G)

    metrics["graph"] = G
    return metrics

# Visualize interval profiles (MIDI vs Audio)

def plot_interval_profiles(iv_midi, iv_audio, title="Interval profile"):
    interval_names = [
        "0 (unison)",
        "1 (m2)",
        "2 (M2)",
        "3 (m3)",
        "4 (M3)",
        "5 (P4)",
        "6 (TT)",
        "7 (P5)",
        "8 (m6)",
        "9 (M6)",
        "10 (m7)",
        "11 (M7)",
    ]

    x = np.arange(12)
    width = 0.35

    plt.figure(figsize=(10, 4))
    plt.bar(x - width/2, iv_midi,  width, label="MIDI")
    plt.bar(x + width/2, iv_audio, width, label="Audio (chroma)")

    plt.xticks(x, interval_names, rotation=45, ha="right")
    plt.ylabel("L2-normalized weight")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.show()

# visualize the graphs

def plot_midi_graph(G, title=""):
    if G.number_of_nodes() == 0:
        print("Empty graph")
        return

    pos = nx.spring_layout(G, seed=0)
    weights = np.array([d["weight"] for _, _, d in G.edges(data=True)], dtype=float)
    if len(weights) > 0:
        w_norm = 1 + 4 * (weights - weights.min()) / (weights.max() - weights.min() + EPS)
    else:
        w_norm = 1.0

    # MIDI note -> note name (e.g., 60 -> C4)
    labels = {n: pretty_midi.note_number_to_name(n) for n in G.nodes()}

    plt.figure(figsize=(6, 6))
    nx.draw_networkx_nodes(G, pos, node_size=400)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8)
    nx.draw_networkx_edges(G, pos, width=w_norm, arrows=True, arrowstyle="->")
    plt.title(title)
    plt.axis("off")
    plt.show()

def plot_pitchclass_graph(G, title=""):
    if G.number_of_nodes() == 0:
        print("Empty graph")
        return

    pos = nx.spring_layout(G, seed=0)
    weights = np.array([d["weight"] for _, _, d in G.edges(data=True)], dtype=float)
    if len(weights) > 0:
        # normalize edge widths for visibility
        w_norm = 1 + 4 * (weights - weights.min()) / (weights.max() - weights.min() + EPS)
    else:
        w_norm = 1.0

    plt.figure(figsize=(5, 5))
    nx.draw_networkx_nodes(G, pos, node_size=500)
    nx.draw_networkx_labels(G, pos, labels={n: str(n) for n in G.nodes()})
    nx.draw_networkx_edges(G, pos, width=w_norm, arrows=True, arrowstyle="->")
    plt.title(title)
    plt.axis("off")
    plt.show()

# General helper to compare one pair

def compare_midi_audio_pair(midi_path, audio_path, label="piece"):
    print(f"=== {label} ===")
    midi_metrics = compute_midi_network_metrics(midi_path)
    audio_metrics = compute_audio_network_metrics(audio_path)

    compare_keys = [
        "n_nodes",
        "n_edges",
        "density",
        "r_real",
        "r_null",
        "rho_norm",
        "mean_entropy",
        "eff_unweighted",
        "eff_weighted",
    ]

    rows = []
    for domain, metrics in [("MIDI", midi_metrics), ("Audio", audio_metrics)]:
        row = {"piece": label, "domain": domain}
        for k in compare_keys:
            row[k] = metrics[k]
        rows.append(row)

    df = pd.DataFrame(rows).set_index(["piece", "domain"])

    # cosine similarity of interval vectors
    iv_midi  = midi_metrics["interval_vec"]
    iv_audio = audio_metrics["interval_vec"]
    cosine_sim = float(
        np.dot(iv_midi, iv_audio) /
        (np.linalg.norm(iv_midi) * np.linalg.norm(iv_audio) + EPS)
    )

    print("Cosine similarity of interval profiles:", cosine_sim)
    display(df)

    # plots
    plot_interval_profiles(iv_midi, iv_audio, title=f"Interval profile – {label}")
    plot_midi_graph(midi_metrics["graph"],  title=f"MIDI note network – {label}")
    plot_pitchclass_graph(audio_metrics["graph"], title=f"Audio chroma network – {label}")

    return {
        "midi": midi_metrics,
        "audio": audio_metrics,
        "df": df,
        "cosine": cosine_sim,
    }

