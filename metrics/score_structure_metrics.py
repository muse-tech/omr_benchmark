from typing import Dict, Tuple, Optional
from core.score_tree import Node
from metrics.element_common import (
    extract_elements_with_attributes,
    extract_all_clefs,
    assign_element_positions_in_measures,
    match_elements_by_position,
    match_elements_by_staff,
    calculate_element_metrics_generic,
    calculate_element_metrics_by_staff
)
from metrics.texts_metrics import calculate_combined_metrics
import re

def compare_value_element(gt_element: Dict, pred_element: Dict, attr_name: str = 'value', element_type: str = None) -> Tuple[bool, Dict]:
    gt_value = gt_element.get(attr_name)
    pred_value = pred_element.get(attr_name)
    if element_type == "Instrument":
        def normalize_instrument_name(name: str) -> str:
            if name is None:
                return ""
            return re.sub(r'\s+\d+$', '', str(name)).strip()
        gt_normalized = normalize_instrument_name(gt_value)
        pred_normalized = normalize_instrument_name(pred_value)
        match = gt_normalized == pred_normalized
    else:
        match = gt_value == pred_value

    error_details = {
        'match': match,
        f'gt_{attr_name}': gt_value,
        f'pred_{attr_name}': pred_value
    }
    return match, error_details

def compare_staff(gt_staff: Dict, pred_staff: Dict) -> Tuple[bool, Dict]:
    match = True
    error_details = {
        'match': match,
        'gt_staff_id': gt_staff.get('staff_id'),
        'pred_staff_id': pred_staff.get('staff_id')
    }
    return match, error_details

def calculate_clef_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    return calculate_element_metrics_by_staff(
        gt_tree, pred_tree, "Clef",
        extract_func=extract_all_clefs,
        compare_func=compare_value_element
    )

def calculate_keysig_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    return calculate_element_metrics_by_staff(
        gt_tree, pred_tree, "KeySig",
        compare_func=compare_value_element
    )

def calculate_timesig_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    return calculate_element_metrics_by_staff(
        gt_tree, pred_tree, "TimeSig",
        compare_func=compare_value_element
    )

def calculate_tempo_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    return calculate_combined_metrics(
        gt_tree, pred_tree, "Tempo",
        include_individual=True,
        include_measure_stats=True
    )

def calculate_instrument_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    return calculate_element_metrics_generic(
        gt_tree, pred_tree, "Instrument",
        compare_func=lambda gt, pred: compare_value_element(gt, pred, 'value', "Instrument")
    )

def calculate_staff_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    return calculate_element_metrics_generic(
        gt_tree, pred_tree, "Staff",
        compare_func=compare_staff
    )
