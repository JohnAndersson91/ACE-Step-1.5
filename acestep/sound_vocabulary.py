"""Original sound descriptions for explicit instrument and vocal conditioning.

The category approach is informed by AudioSet's music ontology, not copied audio:
https://research.google.com/audioset/ontology/index.html
These descriptions are instructions, not samples, new model weights, or a timbre guarantee.
"""

INSTRUMENTS = {
    "Clean electric guitar": "picked clean electric guitar, string attack, ringing notes and expressive bends",
    "Heavy rhythm guitar": "overdriven electric rhythm guitar, distinct palm-muted attacks and sustained chords",
    "Melodic lead guitar": "electric lead guitar with articulated picked runs, bends and harmonized melodic lines",
    "Steel-string acoustic": "steel-string acoustic guitar, audible pick or finger attack and wooden body resonance",
    "Nylon-string guitar": "nylon-string classical guitar with warm plucked notes and finger articulation",
    "Electric bass": "electric bass guitar with defined plucked low notes, controlled sustain and clear rhythmic phrasing",
    "Upright bass": "plucked upright bass with woody resonance and fingerboard articulation",
    "Acoustic drum kit": "acoustic drum kit with distinct kick and snare attacks, natural cymbal decay, dynamic fills and room ambience",
    "Brush drums": "acoustic snare brushes, soft kick and lightly played cymbals",
    "Drum machine": "deliberately electronic drum-machine kick, snare and hi-hat patterns",
    "Hand percussion": "hand-played shakers and congas with distinct strokes and changing dynamics",
    "Grand piano": "acoustic grand piano with felt-hammer attacks, natural note decay and pedal resonance",
    "Electric piano": "warm electric piano with bell-like tine attacks and gentle sustained chords",
    "Organ": "sustained tonewheel organ with drawbar harmonics and gentle rotary-speaker movement",
    "Violin": "bowed violin with connected phrasing, expressive vibrato and distinct bow attacks",
    "Cello": "bowed cello with warm low-register resonance and expressive sustained phrases",
    "String ensemble": "orchestral string ensemble with coordinated bow attacks and dynamic swells",
    "Trumpet": "brass trumpet with breath-shaped phrases, articulated attacks and rounded sustained notes",
    "Saxophone": "saxophone with reed texture, breath-shaped articulation and expressive phrasing",
    "Flute": "flute with airy breath attacks and fluid melodic phrasing",
    "Harp": "plucked harp with ringing string decay and flowing arpeggios",
    "Accordion": "accordion with reed tone, sustained chords and expressive bellows phrasing",
    "Banjo": "banjo with bright short plucked attacks and rolling picked patterns",
    "Mandolin": "mandolin with crisp paired-string attacks and picked tremolo",
    "Sitar": "sitar with buzzing plucked strings, bending ornaments and sympathetic resonance",
    "Synth bass": "electronic synthesizer bass with controlled low-frequency weight",
    "Synth lead": "intentionally synthetic lead melody with a consistent electronic timbre",
    "Atmospheric pads": "soft sustained synthesizer pads with slow attacks and evolving texture",
}

DELIVERIES = {
    "Keep my request": "",
    "Clean and intimate": "close expressive melodic singing, restrained vibrato and clear words",
    "Powerful clean belting": "full-bodied chest voice opening into powerful clean melodic belts",
    "Breathy and gentle": "gentle breathy singing with soft phrase beginnings and clear words",
    "Clean → rasp → brief scream": "mostly clear melodic singing; on only two phrase peaks, the same lead singer moves continuously from a clean sustained vowel through increasing rasp into a brief pitched scream on that SAME word, then returns to clean singing; preserve the singer's register and identity across the transition",
    "Raspy throughout": "textured raspy melodic singing with intelligible words and connected phrasing",
    "Rap / spoken rhythm": "rhythmic rap delivery with clearly articulated words",
    "Operatic": "operatic singing with supported sustained notes and expressive vibrato",
}

PRODUCTION = {
    "Keep my request": "",
    "Natural band recording": "distinct band instruments, human playing dynamics, clear drum transients and realistic note decay; lead vocal forward with restrained doubling and preserved natural pitch movement",
    "Intimate acoustic": "close acoustic recording, natural room resonance, gentle dynamics and a clear exposed lead vocal",
    "Polished pop": "polished pop mix with a clear lead vocal, controlled low end and supportive backing layers",
    "Electronic / designed sound": "intentional electronic sound design with clearly separated synth layers and controlled low end",
}

VOICES = {
    "Keep my request": "",
    "One female singer": "one female lead singer throughout every verse, chorus and vocal-intensity change; all clean, raspy and screamed notes belong to this SAME female singer; any backing layers are performed by this same female singer",
    "One male singer": "one male lead singer throughout every verse, chorus and vocal-intensity change; all clean, raspy and screamed notes belong to this SAME male singer; any backing layers are performed by this same male singer",
    "Duet": "two distinct lead singers performing a duet with clearly separated phrases",
    "Choir": "a coordinated vocal choir with distinct harmonies and supported ensemble phrasing",
    "Instrumental": "instrumental music without sung or spoken voices",
}
