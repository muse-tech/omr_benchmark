from collections import defaultdict
from typing import Dict, Tuple, Optional, List, Callable
from core.score_tree import Node
from Levenshtein import distance as levenshtein_distance
from metrics.element_common import extract_elements_with_attributes, match_elements_by_staff
from metrics.chord_metrics import align_chords_in_measure, extract_chords_with_attributes

def calculate_combined_metrics(
    gt_tree: Node,
    pred_tree: Node,
    element_type: str,
    align_func: Optional[Callable] = None,
    measure_mapping: Optional[Dict[Tuple[int, int], Optional[int]]] = None,
    include_individual: bool = True,
    include_measure_stats: bool = False
) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, element_type)
    pred_elements = extract_elements_with_attributes(pred_tree, element_type)
    
    if align_func:
        aligned_pairs = align_func(gt_elements, pred_elements, measure_mapping, gt_tree, pred_tree)
    else:
        def get_sort_key(elem):
            return (
                elem.get('part_id', -1),
                elem.get('staff_id', -1),
                elem.get('measure_id', -1),
                elem.get('chord_id', -1) if element_type == "Lyrics" else -1,
                elem.get('element_id', -1)
            )
        gt_sorted = sorted(gt_elements, key=get_sort_key)
        pred_sorted = sorted(pred_elements, key=get_sort_key)
        max_len = max(len(gt_elements), len(pred_elements))
        aligned_pairs = [
            (gt_sorted[i] if i < len(gt_sorted) else None, pred_sorted[i] if i < len(pred_sorted) else None)
            for i in range(max_len)
        ]
    
    separator = " "
    gt_values = []
    pred_values = []
    for gt_elem, pred_elem in aligned_pairs:
        if gt_elem:
            gt_values.append(gt_elem.get('value', '') or '')
        if pred_elem:
            pred_values.append(pred_elem.get('value', '') or '')
    
    gt_combined = separator.join(gt_values)
    pred_combined = separator.join(pred_values)
    edit_distance = levenshtein_distance(gt_combined, pred_combined)
    max_len = max(len(gt_combined), len(pred_combined), 1)
    normalized_distance = edit_distance / max_len
    accuracy = 1 - normalized_distance
    exact_match = gt_combined == pred_combined
    
    individual_metrics = []
    if include_individual:
        for gt_elem, pred_elem in aligned_pairs:
            gt_value = gt_elem.get('value', '') if gt_elem else ''
            pred_value = pred_elem.get('value', '') if pred_elem else ''
            if gt_value or pred_value:
                max_val_len = max(len(gt_value), len(pred_value), 1)
                lev_dist = levenshtein_distance(gt_value, pred_value)
                norm_dist = lev_dist / max_val_len
                metric_item = {
                    f'gt_{element_type.lower()}': gt_value,
                    f'pred_{element_type.lower()}': pred_value,
                    'levenshtein_distance': lev_dist,
                    'normalized_distance': norm_dist,
                    'accuracy': 1 - norm_dist,
                    'exact_match': gt_value == pred_value
                }
                if element_type == "Lyrics":
                    metric_item['chord_id'] = gt_elem.get('chord_id') if gt_elem else (pred_elem.get('chord_id') if pred_elem else None)
                    metric_item['staff_id'] = gt_elem.get('staff_id') if gt_elem else (pred_elem.get('staff_id') if pred_elem else None)
                    metric_item['measure_id'] = gt_elem.get('measure_id') if gt_elem else (pred_elem.get('measure_id') if pred_elem else None)
                elif element_type == "Text":
                    metric_item['index'] = len(individual_metrics)
                individual_metrics.append(metric_item)
    
    if individual_metrics:
        avg_edit_distance = sum(m['levenshtein_distance'] for m in individual_metrics) / len(individual_metrics)
        avg_normalized_distance = sum(m['normalized_distance'] for m in individual_metrics) / len(individual_metrics)
        avg_accuracy = sum(m['accuracy'] for m in individual_metrics) / len(individual_metrics)
        exact_match_count = sum(1 for m in individual_metrics if m['exact_match'])
        exact_match_rate = exact_match_count / len(individual_metrics)
    else:
        avg_edit_distance = 0
        avg_normalized_distance = 0
        avg_accuracy = 0
        exact_match_rate = 0
    
    combined_key_map = {
        "Text": 'combined_text',
        "Lyrics": 'combined_lyrics',
        "Tempo": 'combined_tempos'
    }
    combined_key = combined_key_map.get(element_type, f'combined_{element_type.lower()}s')
    individual_key = f'individual_{element_type.lower()}s' if element_type != "Lyrics" else 'individual_lyrics'
    accuracy_key = f'{element_type.lower()}_accuracy' if element_type != "Text" else 'text_accuracy'
    
    metrics = {
        'value': {
            'correct': 1 if exact_match else 0,
            'total': 1,
            'accuracy': accuracy,
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
            accuracy_key: accuracy,
            'exact_match_rate': 1.0 if exact_match else 0.0
        },
        combined_key: {
            'gt_combined': gt_combined,
            'pred_combined': pred_combined,
            'edit_distance': edit_distance,
            'normalized_distance': normalized_distance,
            'accuracy': accuracy,
            'exact_match': exact_match
        },
        'summary': {
            'gt_elements_count': len(gt_elements),
            'pred_elements_count': len(pred_elements),
            'matched_elements_count': min(len(gt_elements), len(pred_elements)),
            'missing_elements_count': max(0, len(gt_elements) - len(pred_elements)),
            'extra_elements_count': max(0, len(pred_elements) - len(gt_elements))
        }
    }
    
    if include_individual and individual_metrics:
        total_key_map = {
            "Text": 'total_texts',
            "Lyrics": 'total_lyrics',
            "Tempo": 'total_tempos'
        }
        total_key = total_key_map.get(element_type, f'total_{element_type.lower()}s')
        metrics[individual_key] = {
            'metrics': individual_metrics,
            'average_edit_distance': avg_edit_distance,
            'average_normalized_distance': avg_normalized_distance,
            'average_accuracy': avg_accuracy,
            'exact_match_rate': exact_match_rate,
            total_key: len(individual_metrics)
        }
    
    if include_measure_stats:
        element_matches, measure_stats = match_elements_by_staff(gt_elements, pred_elements, element_type)
        metrics['summary'].update({
            'gt_measures_count': measure_stats['gt_measures_count'],
            'pred_measures_count': measure_stats['pred_measures_count'],
            'matched_measures_count': measure_stats['matched_measures_count'],
            'missing_measures_count': measure_stats['missing_measures_count'],
            'extra_measures_count': measure_stats['extra_measures_count'],
            'missing_measure_details': measure_stats['missing_measure_details'],
            'extra_measure_details': measure_stats['extra_measure_details']
        })
    
    return metrics

def _align_lyrics_by_chords(gt_elements: List[Dict], pred_elements: List[Dict], 
                            measure_mapping: Optional[Dict[Tuple[int, int], Optional[int]]] = None,
                            gt_tree: Optional[Node] = None,
                            pred_tree: Optional[Node] = None) -> List[Tuple[Optional[Dict], Optional[Dict]]]:
    gt_chords = extract_chords_with_attributes(gt_tree) if gt_tree else []
    pred_chords = extract_chords_with_attributes(pred_tree) if pred_tree else []
    gt_lyrics_by_measure = defaultdict(list)
    pred_lyrics_by_measure = defaultdict(list)
    gt_chords_by_measure = defaultdict(list)
    pred_chords_by_measure = defaultdict(list)

    for lyric in gt_elements:
        staff_id = lyric.get('staff_id')
        measure_id = lyric.get('measure_id')
        if staff_id is not None and measure_id is not None:
            gt_lyrics_by_measure[(staff_id, measure_id)].append(lyric)
    for lyric in pred_elements:
        staff_id = lyric.get('staff_id')
        measure_id = lyric.get('measure_id')
        if staff_id is not None and measure_id is not None:
            pred_lyrics_by_measure[(staff_id, measure_id)].append(lyric)
    for chord in gt_chords:
        staff_id = chord.get('staff_id')
        measure_id = chord.get('measure_id')
        if staff_id is not None and measure_id is not None:
            gt_chords_by_measure[(staff_id, measure_id)].append(chord)
    for chord in pred_chords:
        staff_id = chord.get('staff_id')
        measure_id = chord.get('measure_id')
        if staff_id is not None and measure_id is not None:
            pred_chords_by_measure[(staff_id, measure_id)].append(chord)
    for key in gt_chords_by_measure:
        gt_chords_by_measure[key].sort(key=lambda c: c.get('chord_id', -1))
    for key in pred_chords_by_measure:
        pred_chords_by_measure[key].sort(key=lambda c: c.get('chord_id', -1))
    for key in gt_lyrics_by_measure:
        gt_lyrics_by_measure[key].sort(key=lambda l: (l.get('chord_id', -1), l.get('element_id', -1)))
    for key in pred_lyrics_by_measure:
        pred_lyrics_by_measure[key].sort(key=lambda l: (l.get('chord_id', -1), l.get('element_id', -1)))

    aligned_lyrics = []
    if measure_mapping is not None:
        gt_measures_by_staff = defaultdict(list)
        pred_measures_by_staff = defaultdict(set)
        for (staff_id, gt_measure_id), pred_measure_id in measure_mapping.items():
            gt_measures_by_staff[staff_id].append(gt_measure_id)
            if pred_measure_id is not None:
                pred_measures_by_staff[staff_id].add(pred_measure_id)
        for staff_id in gt_measures_by_staff:
            gt_measures_by_staff[staff_id] = sorted(set(gt_measures_by_staff[staff_id]))
        for staff_id in sorted(set(gt_measures_by_staff.keys()) | set(pred_measures_by_staff.keys())):
            gt_measure_ids = gt_measures_by_staff.get(staff_id, [])
            for gt_measure_id in gt_measure_ids:
                pred_measure_id = measure_mapping.get((staff_id, gt_measure_id))
                if pred_measure_id is not None:
                    gt_measure_chords = gt_chords_by_measure.get((staff_id, gt_measure_id), [])
                    pred_measure_chords = pred_chords_by_measure.get((staff_id, pred_measure_id), [])
                    chord_alignment = align_chords_in_measure(gt_measure_chords, pred_measure_chords)
                    for gt_chord, pred_chord in chord_alignment:
                        gt_chord_id = gt_chord.get('chord_id') if gt_chord else None
                        pred_chord_id = pred_chord.get('chord_id') if pred_chord else None
                        gt_measure_lyrics = gt_lyrics_by_measure.get((staff_id, gt_measure_id), [])
                        pred_measure_lyrics = pred_lyrics_by_measure.get((staff_id, pred_measure_id), [])
                        gt_lyrics_for_chord = [l for l in gt_measure_lyrics if l.get('chord_id') == gt_chord_id]
                        pred_lyrics_for_chord = [l for l in pred_measure_lyrics if l.get('chord_id') == pred_chord_id]
                        gt_lyric = gt_lyrics_for_chord[0] if gt_lyrics_for_chord else None
                        pred_lyric = pred_lyrics_for_chord[0] if pred_lyrics_for_chord else None
                        aligned_lyrics.append((gt_lyric, pred_lyric))
                else:
                    gt_measure_lyrics = gt_lyrics_by_measure.get((staff_id, gt_measure_id), [])
                    for gt_lyric in gt_measure_lyrics:
                        aligned_lyrics.append((gt_lyric, None))
            for pred_measure_id in sorted(pred_measures_by_staff.get(staff_id, set())):
                found_in_mapping = False
                for (s_id, gt_m_id), pred_m_id in measure_mapping.items():
                    if s_id == staff_id and pred_m_id == pred_measure_id:
                        found_in_mapping = True
                        break
                if not found_in_mapping:
                    pred_measure_lyrics = pred_lyrics_by_measure.get((staff_id, pred_measure_id), [])
                    for pred_lyric in pred_measure_lyrics:
                        aligned_lyrics.append((None, pred_lyric))
    else:
        def get_sort_key(elem):
            return (
                elem.get('part_id', -1),
                elem.get('staff_id', -1),
                elem.get('measure_id', -1),
                elem.get('chord_id', -1),
                elem.get('element_id', -1)
            )
        gt_lyrics_sorted = sorted(gt_elements, key=get_sort_key)
        pred_lyrics_sorted = sorted(pred_elements, key=get_sort_key)
        max_individual = max(len(gt_elements), len(pred_elements))
        for i in range(max_individual):
            gt_lyric = gt_lyrics_sorted[i] if i < len(gt_lyrics_sorted) else None
            pred_lyric = pred_lyrics_sorted[i] if i < len(pred_lyrics_sorted) else None
            aligned_lyrics.append((gt_lyric, pred_lyric))
    return aligned_lyrics

def calculate_text_metrics_combined(gt_tree: Node, pred_tree: Node) -> Dict:
    return calculate_combined_metrics(gt_tree, pred_tree, "Text", include_individual=True, include_measure_stats=False)

def calculate_lyrics_metrics_combined(gt_tree: Node, pred_tree: Node, measure_mapping: Optional[Dict[Tuple[int, int], Optional[int]]] = None) -> Dict:
    return calculate_combined_metrics(
        gt_tree, pred_tree, "Lyrics",
        align_func=_align_lyrics_by_chords,
        measure_mapping=measure_mapping,
        include_individual=True,
        include_measure_stats=False
    )
