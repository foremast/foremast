"""Tests for string formatting functions."""
from foremast.utils.pipelines import normalize_pipeline_name

SAFE_PIPELINE_NAMES = {
    '#pudding/pop': '_pudding_pop',
    'caesar?salad': 'caesar_salad',
    'chutes&ladders.json': 'chutes&ladders.json',
    'conga-line': 'conga-line',
    'DAKOTA\\ACCESS': 'DAKOTA_ACCESS',
    'jelly/baby': 'jelly_baby',
    'pizza%2Fpie': 'pizza_2Fpie',
    'water': 'water',
}


def test_safe_pipeline_names():
    """Check Pipeline name safe formatting."""
    for raw, safe in SAFE_PIPELINE_NAMES.items():
        assert normalize_pipeline_name(name=raw) == safe
