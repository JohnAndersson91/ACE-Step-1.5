"""Fit explicit instrument registers without altering pitch classes or input scores."""
import copy


def fit_register(midi, minimum: int, maximum: int):
    """Octave-shift out-of-range notes in a copy and report every moved note."""
    result = copy.deepcopy(midi)
    shifted = 0
    for instrument in result.instruments:
        for note in instrument.notes:
            original = note.pitch
            while note.pitch < minimum:
                note.pitch += 12
            while note.pitch > maximum:
                note.pitch -= 12
            if not minimum <= note.pitch <= maximum:
                raise ValueError("The chosen register cannot contain this pitch class")
            shifted += int(original != note.pitch)
    return result, shifted
