"""Regression checks for model-aware sampling without changing explicit schedules."""
import unittest

from acestep.sampling_defaults import resolve_sampling_shift


class SamplingDefaultsTests(unittest.TestCase):
    """Check automatic schedules and the actual handler forwarding path."""

    def test_family_defaults(self):
        self.assertEqual(resolve_sampling_shift(None, True), 3.0)
        self.assertEqual(resolve_sampling_shift(None, False), 1.0)

    def test_explicit_values_preserved(self):
        for value in (1.0, 2.0, 3.0):
            for turbo in (True, False):
                self.assertEqual(resolve_sampling_shift(value, turbo), value)

    def test_handler_forwards_resolved_schedule(self):
        from acestep.core.generation.handler.generate_music_test import _Host
        for turbo, explicit, expected in ((True, None, 3.0), (False, None, 1.0), (True, 1.0, 1.0)):
            host = _Host(is_turbo=turbo)
            host.generate_music(captions="test", shift=explicit)
            args = host.calls["_run_generate_music_service_with_progress"]
            self.assertEqual(args["shift"], expected)

    def test_parameter_omission_is_distinct_from_explicit_one(self):
        from acestep.inference import GenerationParams
        self.assertIsNone(GenerationParams().shift)
        self.assertEqual(GenerationParams(shift=1.0).shift, 1.0)

    def test_api_resolves_before_forwarding_without_mutating_recipe(self):
        from unittest.mock import MagicMock
        from acestep.inference import GenerationConfig, GenerationParams, generate_music
        from acestep.inference_seed_fallback_test import RecordingDitHandler

        class RecordingTurbo(RecordingDitHandler):
            """Capture the API schedule before a real model would run."""
            def is_turbo_model(self):
                """Identify the installed model family."""
                return True

            def generate_music(self, shift=None, **kwargs):
                """Record the schedule and return the existing stub response."""
                self.received_shift = shift
                return super().generate_music(**kwargs)

        params = GenerationParams(task_type="complete", src_audio="source.wav")
        handler = RecordingTurbo()
        generate_music(handler, MagicMock(), params, GenerationConfig())
        self.assertEqual(handler.received_shift, 3.0)
        self.assertIsNone(params.shift)


if __name__ == "__main__":
    unittest.main()
