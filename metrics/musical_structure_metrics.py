from typing import Dict, Tuple, Optional
from core.score_tree import Node
from metrics.element_common import (
    extract_elements_with_attributes,
    assign_element_positions_in_measures,
    match_elements_by_position
)

def compare_rest(gt_rest: Dict, pred_rest: Dict) -> Tuple[bool, Dict]:
    gt_duration = gt_rest.get('duration')
    pred_duration = pred_rest.get('duration')
    match = gt_duration == pred_duration
    error_details = {
        'match': match,
        'gt_duration': gt_duration,
        'pred_duration': pred_duration
    }
    return match, error_details

def compare_tuplet(gt_tuplet: Dict, pred_tuplet: Dict) -> Tuple[bool, Dict]:
    gt_value = gt_tuplet.get('value')
    pred_value = pred_tuplet.get('value')
    match = gt_value == pred_value
    error_details = {
        'match': match,
        'gt_value': gt_value,
        'pred_value': pred_value
    }
    return match, error_details

def calculate_rest_metrics(gt_tree: Node, pred_tree: Node, measure_mapping: Dict[Tuple[int, int], Optional[int]] = None) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "Rest")
    pred_elements = extract_elements_with_attributes(pred_tree, "Rest")
    assign_element_positions_in_measures(gt_elements, "Rest")
    assign_element_positions_in_measures(pred_elements, "Rest")
    element_matches, measure_stats = match_elements_by_position(
        gt_elements, pred_elements, "Rest", use_alignment=True, measure_mapping=measure_mapping
    )
    metrics = {
        'duration': {'correct': 0, 'total': 0, 'errors': []}
    }
    for gt_element, pred_element in element_matches:
        if gt_element is not None:
            position = {
                'part_id': gt_element['part_id'],
                'staff_id': gt_element['staff_id'],
                'measure_id': gt_element['measure_id'],
                'element_position_in_measure': gt_element.get('element_position_in_measure')
            }
        elif pred_element is not None:
            position = {
                'part_id': pred_element['part_id'],
                'staff_id': pred_element['staff_id'],
                'measure_id': pred_element['measure_id'],
                'element_position_in_measure': pred_element.get('element_position_in_measure')
            }
        else:
            continue
        if gt_element is None:
            gt_element = {'duration': None}
        elif pred_element is None:
            pred_element = {'duration': None}
        attr_match, attr_details = compare_rest(gt_element, pred_element)
        metrics['duration']['total'] += 1
        if attr_match:
            metrics['duration']['correct'] += 1
        else:
            metrics['duration']['errors'].append({
                'position': position,
                'details': attr_details
            })

    metrics['summary'] = {
        'gt_elements_count': len(gt_elements),
        'pred_elements_count': len(pred_elements),
        'matched_elements_count': len([m for m in element_matches if m[0] is not None and m[1] is not None]),
        'missing_elements_count': len([m for m in element_matches if m[0] is not None and m[1] is None]),
        'extra_elements_count': len([m for m in element_matches if m[0] is None and m[1] is not None]),
        'gt_measures_count': measure_stats['gt_measures_count'],
        'pred_measures_count': measure_stats['pred_measures_count'],
        'matched_measures_count': measure_stats['matched_measures_count'],
        'missing_measures_count': measure_stats['missing_measures_count'],
        'extra_measures_count': measure_stats['extra_measures_count'],
        'missing_measure_details': measure_stats['missing_measure_details'],
        'extra_measure_details': measure_stats['extra_measure_details']
    }

    if metrics['summary']['gt_elements_count'] == 0 and metrics['summary']['pred_elements_count'] == 0:
        metrics['duration']['accuracy'] = 1.0
    else:
        total = metrics['duration']['total']
        correct = metrics['duration']['correct']
        metrics['duration']['accuracy'] = correct / total if total > 0 else 0.0
    return metrics

def calculate_tuplet_metrics(gt_tree: Node, pred_tree: Node, measure_mapping: Dict[Tuple[int, int], Optional[int]] = None) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "Tuplet")
    pred_elements = extract_elements_with_attributes(pred_tree, "Tuplet")
    assign_element_positions_in_measures(gt_elements, "Tuplet")
    assign_element_positions_in_measures(pred_elements, "Tuplet")
    element_matches, measure_stats = match_elements_by_position(
        gt_elements, pred_elements, "Tuplet", use_alignment=True, measure_mapping=measure_mapping
    )
    metrics = {
        'value': {'correct': 0, 'total': 0, 'errors': []}
    }

    for gt_element, pred_element in element_matches:
        if gt_element is not None:
            position = {
                'part_id': gt_element['part_id'],
                'staff_id': gt_element['staff_id'],
                'measure_id': gt_element['measure_id'],
                'element_position_in_measure': gt_element.get('element_position_in_measure')
            }
        elif pred_element is not None:
            position = {
                'part_id': pred_element['part_id'],
                'staff_id': pred_element['staff_id'],
                'measure_id': pred_element['measure_id'],
                'element_position_in_measure': pred_element.get('element_position_in_measure')
            }
        else:
            continue

        if gt_element is None:
            gt_element = {'value': None}
        elif pred_element is None:
            pred_element = {'value': None}
        attr_match, attr_details = compare_tuplet(gt_element, pred_element)
        metrics['value']['total'] += 1

        if attr_match:
            metrics['value']['correct'] += 1
        else:
            metrics['value']['errors'].append({
                'position': position,
                'details': attr_details
            })

    metrics['summary'] = {
        'gt_elements_count': len(gt_elements),
        'pred_elements_count': len(pred_elements),
        'matched_elements_count': len([m for m in element_matches if m[0] is not None and m[1] is not None]),
        'missing_elements_count': len([m for m in element_matches if m[0] is not None and m[1] is None]),
        'extra_elements_count': len([m for m in element_matches if m[0] is None and m[1] is not None]),
        'gt_measures_count': measure_stats['gt_measures_count'],
        'pred_measures_count': measure_stats['pred_measures_count'],
        'matched_measures_count': measure_stats['matched_measures_count'],
        'missing_measures_count': measure_stats['missing_measures_count'],
        'extra_measures_count': measure_stats['extra_measures_count'],
        'missing_measure_details': measure_stats['missing_measure_details'],
        'extra_measure_details': measure_stats['extra_measure_details']
    }

    if metrics['summary']['gt_elements_count'] == 0 and metrics['summary']['pred_elements_count'] == 0:
        metrics['value']['accuracy'] = 1.0
    else:
        total = metrics['value']['total']
        correct = metrics['value']['correct']
        metrics['value']['accuracy'] = correct / total if total > 0 else 0.0
    return metrics
