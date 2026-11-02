"""Generation-tab section orchestrator for the Gradio interface."""

from typing import Any

import gradio as gr

from acestep.constants import GENERATION_MODES_BASE, GENERATION_MODES_TURBO
from acestep.practice_audio import build_practice_controls
from acestep.music_workflows import build_workflow_guide
from acestep.reconstruction_ui import build_reconstruction_ui
from acestep.correction_lab import build_correction_lab
from acestep.transcription_options import build_transcription_options
from acestep.song_prompt import build_song_prompt
from acestep.vocal_song_ui import build_vocal_song
from acestep.songwriting import build_songwriting
from acestep.style_request_ui import build_style_direction
from acestep.reference_analysis_ui import build_reference_analysis

from .generation_defaults import compute_init_defaults, resolve_is_pure_base_model
from .generation_tab_primary_controls import (
    build_hidden_generation_state,
    build_mode_selector_controls,
)
from .generation_tab_simple_controls import (
    build_simple_mode_controls,
)
from .generation_tab_source_controls import (
    build_source_track_and_code_controls,
)
from .generation_tab_generate_controls import (
    build_generate_row_controls,
)
from .generation_tab_optional_controls import (
    build_optional_parameter_controls,
)
from .generation_tab_secondary_controls import (
    build_cover_strength_controls,
    build_custom_mode_controls,
    build_repainting_controls,
)
from .generation_tab_variation_morph_controls import build_variation_morph_controls


def create_generation_tab_section(
    dit_handler: Any,
    llm_handler: Any,
    init_params: dict[str, Any] | None = None,
    language: str = "en",
) -> dict[str, Any]:
    """Create generation-tab controls and mode-specific UI sections.

    Args:
        dit_handler: DiT service handler used for model-aware mode defaults.
        llm_handler: LM service handler retained for signature parity with callers.
        init_params: Optional startup state used to prefill runtime defaults.
        language: UI language code used for default computation.

    Returns:
        A merged component map for generation-tab controls and runtime metadata.
    """

    _ = llm_handler  # retained for caller signature parity
    defaults = compute_init_defaults(init_params, language)
    service_pre_initialized = defaults["service_pre_initialized"]
    service_mode = defaults["service_mode"]
    lm_initialized = defaults["lm_initialized"]
    max_duration = defaults["max_duration"]
    max_batch_size = defaults["max_batch_size"]
    default_batch_size = defaults["default_batch_size"]

    is_pure_base_model = resolve_is_pure_base_model(
        dit_handler=dit_handler,
        init_params=init_params,
        service_pre_initialized=service_pre_initialized,
    )
    initial_mode_choices = GENERATION_MODES_BASE if is_pure_base_model else GENERATION_MODES_TURBO

    with gr.Group():
        hidden_state_controls = build_hidden_generation_state()
        with gr.Accordion("📂 Add a song",open=False):
            source_track_code_controls = build_source_track_and_code_controls()
        with gr.Tabs():
            with gr.Tab("🎵 Create a song"):
                with gr.Accordion("Mode: new song, remix or repair",open=False):
                    mode_controls = build_mode_selector_controls(initial_mode_choices)
                    cover_controls = build_cover_strength_controls()
                    repainting_controls = build_repainting_controls()
                simple_mode_controls = build_simple_mode_controls()
                custom_mode_controls = build_custom_mode_controls()
                build_vocal_song(dit_handler,llm_handler)
                build_song_prompt(custom_mode_controls["captions"], custom_mode_controls["instrumental_checkbox"])
                optional_controls = build_optional_parameter_controls(
                    max_duration=max_duration,max_batch_size=max_batch_size,
                    default_batch_size=default_batch_size,service_mode=service_mode)
                build_songwriting(custom_mode_controls["lyrics"],custom_mode_controls["instrumental_checkbox"],
                    custom_mode_controls["captions"],optional_controls["audio_duration"],
                    hidden_state_controls["lyrics_before_instrumental"],dit_handler)
                build_style_direction(custom_mode_controls,optional_controls)
                build_reference_analysis(custom_mode_controls,optional_controls,dit_handler)
                generate_controls = build_generate_row_controls(
                    service_pre_initialized=service_pre_initialized,init_params=init_params,
                    lm_initialized=lm_initialized,service_mode=service_mode)
            with gr.Tab("🎤 Sing & record"):
                build_practice_controls(source_track_code_controls["src_audio"],
                    custom_mode_controls["lyrics"],expanded=True)
            with gr.Tab("🛠 More tools"):
                variation_morph_controls = build_variation_morph_controls()
                build_reconstruction_ui(source_track_code_controls["src_audio"])
                build_correction_lab()
                build_transcription_options()
                build_workflow_guide()

    result: dict[str, Any] = {}
    result.update(mode_controls)
    result.update(hidden_state_controls)
    result.update(simple_mode_controls)
    result.update(source_track_code_controls)
    result.update(variation_morph_controls)
    result.update(cover_controls)
    result.update(custom_mode_controls)
    result.update(repainting_controls)
    result.update(optional_controls)
    result.update(generate_controls)
    result.update(
        {
            "max_duration": max_duration,
            "max_batch_size": max_batch_size,
        }
    )
    return result
