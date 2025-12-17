from typing import Dict, Optional, Tuple
from core.score_tree import Node
from metrics.musical_structure_metrics import (
    calculate_rest_metrics,
    calculate_tuplet_metrics
)
from metrics.score_structure_metrics import (
    calculate_clef_metrics,
    calculate_keysig_metrics,
    calculate_timesig_metrics,
    calculate_tempo_metrics,
    calculate_instrument_metrics,
    calculate_staff_metrics
)
from metrics.performance_instructions_metrics import (
    calculate_dynamic_metrics,
    calculate_spanner_metrics,
    calculate_fermata_metrics
)
from metrics.texts_metrics import (
    calculate_text_metrics_combined,
    calculate_lyrics_metrics_combined
)
from metrics.element_output import print_element_metrics

def calculate_element_metrics(gt_tree: Node, pred_tree: Node, element_type: str, measure_mapping: Dict[Tuple[int, int], Optional[int]] = None) -> Dict:
    if element_type == "Text":
        return calculate_text_metrics_combined(gt_tree, pred_tree)
    elif element_type == "Lyrics":
        return calculate_lyrics_metrics_combined(gt_tree, pred_tree, measure_mapping=measure_mapping)
    elif element_type == "Rest":
        return calculate_rest_metrics(gt_tree, pred_tree, measure_mapping=measure_mapping)
    elif element_type == "Tuplet":
        return calculate_tuplet_metrics(gt_tree, pred_tree, measure_mapping=measure_mapping)
    elif element_type == "Clef":
        return calculate_clef_metrics(gt_tree, pred_tree)
    elif element_type == "KeySig":
        return calculate_keysig_metrics(gt_tree, pred_tree)
    elif element_type == "TimeSig":
        return calculate_timesig_metrics(gt_tree, pred_tree)
    elif element_type == "Tempo":
        return calculate_tempo_metrics(gt_tree, pred_tree)
    elif element_type == "Instrument":
        return calculate_instrument_metrics(gt_tree, pred_tree)
    elif element_type == "Staff":
        return calculate_staff_metrics(gt_tree, pred_tree)
    elif element_type == "Dynamic":
        return calculate_dynamic_metrics(gt_tree, pred_tree, measure_mapping=measure_mapping)
    elif element_type == "Spanner":
        return calculate_spanner_metrics(gt_tree, pred_tree, measure_mapping=measure_mapping)
    elif element_type == "Fermata":
        return calculate_fermata_metrics(gt_tree, pred_tree, measure_mapping=measure_mapping)
    else:
        raise ValueError(f"Unsupported element type: {element_type}")

__all__ = ['calculate_element_metrics', 'print_element_metrics']
