from typing import Dict, Tuple, Optional
from core.score_tree import Node
from metrics.element_common import calculate_element_metrics_generic

def calculate_rest_metrics(gt_tree: Node, pred_tree: Node, measure_mapping: Dict[Tuple[int, int], Optional[int]] = None) -> Dict:
    return calculate_element_metrics_generic(gt_tree, pred_tree, "Rest", measure_mapping)

def calculate_tuplet_metrics(gt_tree: Node, pred_tree: Node, measure_mapping: Dict[Tuple[int, int], Optional[int]] = None) -> Dict:
    return calculate_element_metrics_generic(gt_tree, pred_tree, "Tuplet", measure_mapping)
