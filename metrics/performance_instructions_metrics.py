from typing import Dict, Tuple, Optional
from core.score_tree import Node
from metrics.element_common import (
    extract_elements_with_attributes,
    assign_element_positions_in_measures,
    match_elements_by_position
)

def compare_dynamic(gt_element: Dict, pred_element: Dict) -> Tuple[bool, Dict]:
    gt_value = gt_element.get('value')
    pred_value = pred_element.get('value')
    match = gt_value == pred_value
    error_details = {
        'match': match,
        'gt_value': gt_value,
        'pred_value': pred_value
    }
    return match, error_details

def compare_spanner(gt_spanner: Dict, pred_spanner: Dict) -> Tuple[bool, Dict]:
    gt_type = gt_spanner.get('type')
    pred_type = pred_spanner.get('type')
    match = gt_type == pred_type
    error_details = {
        'match': match,
        'gt_type': gt_type,
        'pred_type': pred_type
    }
    return match, error_details

def compare_fermata(gt_fermata: Dict, pred_fermata: Dict) -> Tuple[bool, Dict]:
    gt_subtype = gt_fermata.get('subtype')
    pred_subtype = pred_fermata.get('subtype')
    match = gt_subtype == pred_subtype
    error_details = {
        'match': match,
        'gt_subtype': gt_subtype,
        'pred_subtype': pred_subtype
    }
    return match, error_details

def calculate_dynamic_metrics(gt_tree: Node, pred_tree: Node, measure_mapping: Dict[Tuple[int, int], Optional[int]] = None) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "Dynamic")
    pred_elements = extract_elements_with_attributes(pred_tree, "Dynamic")
    assign_element_positions_in_measures(gt_elements, "Dynamic")
    assign_element_positions_in_measures(pred_elements, "Dynamic")
    element_matches, measure_stats = match_elements_by_position(
        gt_elements, pred_elements, "Dynamic", use_alignment=True, measure_mapping=measure_mapping
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

        attr_match, attr_details = compare_dynamic(gt_element, pred_element)
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

def calculate_spanner_metrics(gt_tree: Node, pred_tree: Node, measure_mapping: Dict[Tuple[int, int], Optional[int]] = None) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "Spanner")
    pred_elements = extract_elements_with_attributes(pred_tree, "Spanner")
    assign_element_positions_in_measures(gt_elements, "Spanner")
    assign_element_positions_in_measures(pred_elements, "Spanner")
    element_matches, measure_stats = match_elements_by_position(
        gt_elements, pred_elements, "Spanner", use_alignment=True, measure_mapping=measure_mapping
    )
    metrics = {
        'type': {'correct': 0, 'total': 0, 'errors': []}
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
            gt_element = {'type': None}
        elif pred_element is None:
            pred_element = {'type': None}

        attr_match, attr_details = compare_spanner(gt_element, pred_element)
        metrics['type']['total'] += 1
        if attr_match:
            metrics['type']['correct'] += 1
        else:
            metrics['type']['errors'].append({
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
        metrics['type']['accuracy'] = 1.0
    else:
        total = metrics['type']['total']
        correct = metrics['type']['correct']
        metrics['type']['accuracy'] = correct / total if total > 0 else 0.0
    return metrics

def calculate_fermata_metrics(gt_tree: Node, pred_tree: Node, measure_mapping: Dict[Tuple[int, int], Optional[int]] = None) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "Fermata")
    pred_elements = extract_elements_with_attributes(pred_tree, "Fermata")
    assign_element_positions_in_measures(gt_elements, "Fermata")
    assign_element_positions_in_measures(pred_elements, "Fermata")
    element_matches, measure_stats = match_elements_by_position(
        gt_elements, pred_elements, "Fermata", use_alignment=True, measure_mapping=measure_mapping
    )
    metrics = {
        'subtype': {'correct': 0, 'total': 0, 'errors': []}
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
            gt_element = {'subtype': None}
        elif pred_element is None:
            pred_element = {'subtype': None}

        attr_match, attr_details = compare_fermata(gt_element, pred_element)
        metrics['subtype']['total'] += 1
        if attr_match:
            metrics['subtype']['correct'] += 1
        else:
            metrics['subtype']['errors'].append({
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
        metrics['subtype']['accuracy'] = 1.0
    else:
        total = metrics['subtype']['total']
        correct = metrics['subtype']['correct']
        metrics['subtype']['accuracy'] = correct / total if total > 0 else 0.0
    return metrics
