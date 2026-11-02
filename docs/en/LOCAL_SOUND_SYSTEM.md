# Local sound controls and generation consistency

This update changes the program, rather than rewriting an individual song request.

## Available now

- **Instruments & vocal sound**: 28 instrument descriptions, separate intro/main roles,
  singer lineup, eight delivery choices and four recording styles plus neutral defaults.
- Explicit application previews the actual caption. Instrument choices do not silently
  select a singer or overwrite the story. Lyrics words remain unchanged.
- Continuous solo clean-to-rasp-to-scream delivery requests the same voice and same word.
  Separate Scream/Growl headings are removed only when applying that selected solo mode.
- Contradictory explicit male/female requests are flagged before applying the palette.
- Artist guitar references now describe guitar technique without selecting a harsh vocal genre.
- Omitted sampling shift resolves to 3.0 on Turbo in scripted/API and direct-handler calls,
  matching the normal UI. Explicit choices remain unchanged; non-Turbo omission remains 1.0.

These are conditioning instructions and a sampling-default fix. The installed generator
was not retrained. This is not a sample library, singer-identity model, universal song lookup,
automatic realism detector, autotune remover, or a guarantee against synthetic timbres.
The unchanged-request engine comparison is saved locally under outputs/Generation engine comparison.
Its level checks cannot establish musical quality or singer identity.

## Sources and ideas reviewed

- [ACE-Step inference guide](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INFERENCE.md):
  Turbo sampling recommendations, model-specific controls and reference conditioning.
- [Google AudioSet ontology](https://research.google.com/audioset/ontology/index.html):
  organize sounds by source, musical role and sound concept. Palette descriptions are original.
- [Suno Voices](https://help.suno.com/en/articles/11362369): distinguish singer identity
  from style. Its proprietary voice system has not been implemented here.
- [Udio Sessions](https://help.udio.com/en/articles/11649525-sessions-udio-s-timeline-editing-view):
  compare versions and retain good sections. Our existing comparison/splice tools serve that workflow.
- [Meta AudioCraft](https://github.com/facebookresearch/audiocraft): separate sound generation
  from musical conditioning; JASCO supports chord/melody/drum conditioning. Its code is MIT,
  weights CC-BY-NC 4.0. Nothing was installed or integrated from it in this update.

Copying an interface or enlarging this vocabulary cannot reproduce another service's model.
Stronger identity and timbre control may require different weights, training, or real recorded stems.
