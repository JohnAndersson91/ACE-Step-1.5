"""Resolve omitted sampling values consistently across local generation entry points."""


def resolve_sampling_shift(value, is_turbo):
    """Use the documented Turbo schedule while preserving explicit and non-Turbo values."""
    if value is None:
        return 3.0 if is_turbo else 1.0
    return value
