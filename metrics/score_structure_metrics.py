from typing import Dict, Tuple, Optional
from core.score_tree import Node
from Levenshtein import distance as levenshtein_distance
from metrics.element_common import (
    extract_elements_with_attributes,
    extract_all_clefs,
    assign_element_positions_in_measures,
    match_elements_by_position,
    match_elements_by_staff
)
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

def match_clefs_by_staff(gt_clefs: list, pred_clefs: list) -> Tuple[list, Dict]:
    return match_elements_by_staff(gt_clefs, pred_clefs, "Clef")

def calculate_clef_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    gt_elements = extract_all_clefs(gt_tree)
    pred_elements = extract_all_clefs(pred_tree)
    element_matches, measure_stats = match_clefs_by_staff(gt_elements, pred_elements)
    metrics = {
        'value': {'correct': 0, 'total': 0, 'errors': []}
    }
    for gt_element, pred_element in element_matches:
        if gt_element is not None:
            position = {
                'part_id': gt_element['part_id'],
                'staff_id': gt_element['staff_id'],
                'measure_id': None,
                'element_position_in_measure': None
            }
        elif pred_element is not None:
            position = {
                'part_id': pred_element['part_id'],
                'staff_id': pred_element['staff_id'],
                'measure_id': None,
                'element_position_in_measure': None
            }
        else:
            continue
        if gt_element is None:
            gt_element = {'value': None}
        elif pred_element is None:
            pred_element = {'value': None}
        attr_match, attr_details = compare_value_element(gt_element, pred_element, 'value', "Clef")
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

def calculate_keysig_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "KeySig")
    pred_elements = extract_elements_with_attributes(pred_tree, "KeySig")
    element_matches, measure_stats = match_elements_by_staff(gt_elements, pred_elements, "KeySig")
    metrics = {
        'value': {'correct': 0, 'total': 0, 'errors': []}
    }

    for gt_element, pred_element in element_matches:
        if gt_element is not None:
            position = {
                'part_id': gt_element['part_id'],
                'staff_id': gt_element['staff_id'],
                'measure_id': None,
                'element_position_in_measure': None
            }
        elif pred_element is not None:
            position = {
                'part_id': pred_element['part_id'],
                'staff_id': pred_element['staff_id'],
                'measure_id': None,
                'element_position_in_measure': None
            }
        else:
            continue

        if gt_element is None:
            gt_element = {'value': None}
        elif pred_element is None:
            pred_element = {'value': None}
        attr_match, attr_details = compare_value_element(gt_element, pred_element, 'value', "KeySig")
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

def calculate_timesig_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "TimeSig")
    pred_elements = extract_elements_with_attributes(pred_tree, "TimeSig")
    element_matches, measure_stats = match_elements_by_staff(gt_elements, pred_elements, "TimeSig")
    metrics = {
        'value': {'correct': 0, 'total': 0, 'errors': []}
    }
    for gt_element, pred_element in element_matches:
        if gt_element is not None:
            position = {
                'part_id': gt_element['part_id'],
                'staff_id': gt_element['staff_id'],
                'measure_id': None,
                'element_position_in_measure': None
            }
        elif pred_element is not None:
            position = {
                'part_id': pred_element['part_id'],
                'staff_id': pred_element['staff_id'],
                'measure_id': None,
                'element_position_in_measure': None
            }
        else:
            continue

        if gt_element is None:
            gt_element = {'value': None}
        elif pred_element is None:
            pred_element = {'value': None}
        attr_match, attr_details = compare_value_element(gt_element, pred_element, 'value', "TimeSig")
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

def calculate_tempo_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "Tempo")
    pred_elements = extract_elements_with_attributes(pred_tree, "Tempo")

    def get_sort_key(elem):
        return (
            elem.get('part_id', -1),
            elem.get('staff_id', -1),
            elem.get('measure_id', -1),
            elem.get('element_id', -1)
        )
    
    gt_tempos_sorted = sorted(gt_elements, key=get_sort_key)
    pred_tempos_sorted = sorted(pred_elements, key=get_sort_key)

    separator = " "
    gt_tempo_list = [elem.get('value', '') or '' for elem in gt_tempos_sorted]
    pred_tempo_list = [elem.get('value', '') or '' for elem in pred_tempos_sorted]
    
    gt_combined = separator.join(gt_tempo_list)
    pred_combined = separator.join(pred_tempo_list)

    edit_distance = levenshtein_distance(gt_combined, pred_combined)
    max_len = max(len(gt_combined), len(pred_combined), 1)
    normalized_distance = edit_distance / max_len
    tempo_accuracy = 1 - normalized_distance
    exact_match = gt_combined == pred_combined

    element_matches, measure_stats = match_elements_by_staff(gt_elements, pred_elements, "Tempo")
    metrics = {
        'value': {
            'correct': 1 if exact_match else 0,
            'total': 1,
            'accuracy': tempo_accuracy,
            'errors': [] if exact_match else [{
                'position': {'combined': True},
                'details': {
                    'exact_match': exact_match,
                    'gt_value': gt_combined,
                    'pred_value': pred_combined,
                    'edit_distance': edit_distance,
                    'normalized_distance': normalized_distance,
                    'max_length': max_len
                }
            }]
        },
        'edit_distance': {
            'total_edit_distance': edit_distance,
            'total_max_length': max_len,
            'exact_matches': 1 if exact_match else 0,
            'total_matches': 1,
            'average_edit_distance': edit_distance,
            'average_normalized_distance': normalized_distance,
            'tempo_accuracy': tempo_accuracy,
            'exact_match_rate': 1.0 if exact_match else 0.0
        },
        'combined_tempos': {
            'gt_combined': gt_combined,
            'pred_combined': pred_combined,
            'edit_distance': edit_distance,
            'normalized_distance': normalized_distance,
            'accuracy': tempo_accuracy,
            'exact_match': exact_match
        },
        'summary': {
            'gt_elements_count': len(gt_elements),
            'pred_elements_count': len(pred_elements),
            'matched_elements_count': min(len(gt_elements), len(pred_elements)),
            'missing_elements_count': max(0, len(gt_elements) - len(pred_elements)),
            'extra_elements_count': max(0, len(pred_elements) - len(gt_elements)),
            'gt_measures_count': measure_stats['gt_measures_count'],
            'pred_measures_count': measure_stats['pred_measures_count'],
            'matched_measures_count': measure_stats['matched_measures_count'],
            'missing_measures_count': measure_stats['missing_measures_count'],
            'extra_measures_count': measure_stats['extra_measures_count'],
            'missing_measure_details': measure_stats['missing_measure_details'],
            'extra_measure_details': measure_stats['extra_measure_details']
        }
    }
    return metrics

def calculate_instrument_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "Instrument")
    pred_elements = extract_elements_with_attributes(pred_tree, "Instrument")
    assign_element_positions_in_measures(gt_elements, "Instrument")
    assign_element_positions_in_measures(pred_elements, "Instrument")
    element_matches, measure_stats = match_elements_by_position(
        gt_elements, pred_elements, "Instrument", use_alignment=False
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
        attr_match, attr_details = compare_value_element(gt_element, pred_element, 'value', "Instrument")
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

def calculate_staff_metrics(gt_tree: Node, pred_tree: Node) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "Staff")
    pred_elements = extract_elements_with_attributes(pred_tree, "Staff")
    assign_element_positions_in_measures(gt_elements, "Staff")
    assign_element_positions_in_measures(pred_elements, "Staff")
    element_matches, measure_stats = match_elements_by_position(
        gt_elements, pred_elements, "Staff", use_alignment=True
    )
    metrics = {
        'presence': {'correct': 0, 'total': 0, 'errors': []}
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
            gt_element = {'staff_id': None}
        elif pred_element is None:
            pred_element = {'staff_id': None}
        attr_match, attr_details = compare_staff(gt_element, pred_element)
        metrics['presence']['total'] += 1

        if attr_match:
            metrics['presence']['correct'] += 1
        else:
            metrics['presence']['errors'].append({
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
        metrics['presence']['accuracy'] = 1.0
    else:
        total = metrics['presence']['total']
        correct = metrics['presence']['correct']
        metrics['presence']['accuracy'] = correct / total if total > 0 else 0.0
    return metrics
