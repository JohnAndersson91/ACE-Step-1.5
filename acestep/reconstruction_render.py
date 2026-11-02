"""Render estimated MIDI notes as new instrument samples, without original audio."""
import numpy as np
import tinysoundfont


def render_notes(midi, soundfont: str, duration: float, preset: int,
                 bank: int = 0, is_drums: bool = False) -> np.ndarray:
    """Render a MIDI note estimate with one chosen SoundFont preset."""
    rate = 44100
    synth = tinysoundfont.Synth(samplerate=rate)
    sfid = synth.sfload(soundfont)
    synth.program_select(0, sfid, bank, preset, is_drums=is_drums)
    events = []
    for instrument in midi.instruments:
        for note in instrument.notes:
            events.extend([(int(note.start*rate), 3, note.pitch, note.velocity),
                           (int(note.end*rate), 0, note.pitch, 0)])
        for bend in instrument.pitch_bends:
            events.append((int(bend.time*rate),2,bend.pitch+8192,0))
        for control in instrument.control_changes:
            events.append((int(control.time*rate),1,control.number,control.value))
    events.sort()
    output = np.zeros((int(duration*rate), 2), np.float32)
    cursor = 0
    for frame, kind, pitch, velocity in events:
        frame = min(len(output), max(cursor, frame))
        if frame > cursor:
            output[cursor:frame] = np.frombuffer(synth.generate(frame-cursor), np.float32).reshape(-1,2)
        if kind == 3:
            synth.noteon(0, pitch, velocity)
        elif kind == 0:
            synth.noteoff(0, pitch)
        elif kind == 2:
            synth.pitchbend(0,min(16383,max(0,pitch)))
        elif kind == 1:
            synth.control_change(0,pitch,velocity)
        cursor = frame
    if cursor < len(output):
        output[cursor:] = np.frombuffer(synth.generate(len(output)-cursor), np.float32).reshape(-1,2)
    return output


def render_drum_sketch(path: str, duration: float):
    """Estimate drum onsets and render synthetic hits, returning audio and editable MIDI."""
    import librosa
    import pretty_midi

    rate = 44100
    mono, _ = librosa.load(path, sr=rate)
    stft = abs(librosa.stft(mono))
    frequencies = librosa.fft_frequencies(sr=rate)
    result = np.zeros(int(duration*rate), np.float32)
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0, is_drum=True)
    rng = np.random.default_rng(101)
    for low, high, pitch in [(30,180,36),(180,2500,38),(5000,18000,42)]:
        envelope = np.mean(stft[(frequencies>=low)&(frequencies<high)], axis=0)
        onsets = librosa.onset.onset_detect(onset_envelope=envelope, sr=rate, hop_length=512)
        for frame in onsets:
            start = int(frame*512)
            count = min(int(rate*0.18), len(result)-start)
            if count <= 0:
                continue
            t = np.arange(count)/rate
            if pitch == 36:
                hit = np.sin(2*np.pi*(50*t+7*(1-np.exp(-t*30))))*np.exp(-t*22)
            else:
                hit = rng.normal(size=count)*np.exp(-t*(40 if pitch==42 else 22))
            result[start:start+count] += hit*0.12
            instrument.notes.append(pretty_midi.Note(75,pitch,start/rate,start/rate+0.1))
    midi.instruments.append(instrument)
    return np.column_stack([result,result]), midi
