"""
Module for computing quality metrics for OMR results.
"""

from .tree_edit_distance import (
    tree_edit_distance,
    tree_edit_distance_normalized,
    AptNodeConfig,
    AptNode
)
from .sequence_metrics import (
    character_error_rate,
    symbol_error_rate
)
from .chord_metrics import (
    calculate_chord_metrics,
    get_measure_alignment_from_chords
)
from .element_metrics import (
    calculate_element_metrics
)
from .element_output import (
    print_element_metrics
)
from .output import print_metrics

__all__ = [
    'tree_edit_distance',
    'tree_edit_distance_normalized',
    'AptNodeConfig',
    'AptNode',
    'character_error_rate',
    'symbol_error_rate',
    'calculate_chord_metrics',
    'get_measure_alignment_from_chords',
    'calculate_element_metrics',
    'print_element_metrics',
    'print_metrics',
]
