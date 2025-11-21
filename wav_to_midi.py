import sys
import numpy as np
import librosa
import pretty_midi


def wav_to_midi(
    wav_path: str,
    midi_path: str,
    fmin: str = "C2",
    fmax: str = "C7",
    hop_length: int = 512,
    frame_length: int = 2048,
    min_note_length: float = 0.05,   # seconds
    velocity: int = 90,
):
    # 1. Load audio
    y, sr = librosa.load(wav_path, sr=None, mono=True)

    # 2. Estimate fundamental frequency over time (f0)
    f0 = librosa.yin(
        y,
        fmin=librosa.note_to_hz(fmin),
        fmax=librosa.note_to_hz(fmax),
        sr=sr,
        frame_length=frame_length,
        hop_length=hop_length,
    )

    # Times (in seconds) for each frame
    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

    # 3. Convert f0 (Hz) to MIDI notes, NaN where unvoiced
    midi_f0 = librosa.hz_to_midi(f0)
    # Round to nearest integer MIDI note
    midi_f0_rounded = np.rint(midi_f0)

    # Mark unvoiced frames as NaN explicitly
    midi_f0_rounded[np.isnan(midi_f0)] = np.nan

    # 4. Group consecutive frames with same MIDI note into note events
    notes = []
    current_note = None
    start_time = None

    for t, m in zip(times, midi_f0_rounded):
        if np.isnan(m):  # unvoiced / silence
            if current_note is not None:
                # End current note
                end_time = t
                if end_time - start_time >= min_note_length:
                    notes.append((int(current_note), float(start_time), float(end_time)))
                current_note = None
                start_time = None
            continue

        m = int(m)

        if current_note is None:
            # Start new note
            current_note = m
            start_time = t
        elif m != current_note:
            # Note change: close previous note, start new one
            end_time = t
            if end_time - start_time >= min_note_length:
                notes.append((int(current_note), float(start_time), float(end_time)))
            current_note = m
            start_time = t

    # Close the last open note if any
    if current_note is not None and start_time is not None:
        end_time = times[-1]
        if end_time - start_time >= min_note_length:
            notes.append((int(current_note), float(start_time), float(end_time)))

    # 5. Build MIDI with pretty_midi
    pm = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano

    for pitch, start, end in notes:
        note = pretty_midi.Note(
            velocity=velocity,
            pitch=pitch,
            start=start,
            end=end,
        )
        instrument.notes.append(note)

    pm.instruments.append(instrument)

    # 6. Write MIDI file
    pm.write(midi_path)
    print(f"Saved MIDI to {midi_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python wav_to_midi.py input.wav output.mid")
        sys.exit(1)

    wav_path = sys.argv[1]
    midi_path = sys.argv[2]

    wav_to_midi(wav_path, midi_path)