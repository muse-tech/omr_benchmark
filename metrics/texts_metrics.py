from collections import defaultdict
from typing import Dict, Tuple, Optional
from core.score_tree import Node
from Levenshtein import distance as levenshtein_distance
from metrics.element_common import extract_elements_with_attributes
from metrics.chord_metrics import align_chords_in_measure, extract_chords_with_attributes

def calculate_text_metrics_combined(gt_tree: Node, pred_tree: Node) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "Text")
    pred_elements = extract_elements_with_attributes(pred_tree, "Text")
    
    def get_sort_key(elem):
        return (
            elem.get('part_id', -1),
            elem.get('staff_id', -1),
            elem.get('measure_id', -1),
            elem.get('element_id', -1)
        )

    gt_texts_sorted = sorted(gt_elements, key=get_sort_key)
    pred_texts_sorted = sorted(pred_elements, key=get_sort_key)
    separator = " "
    gt_combined = separator.join([elem.get('value', '') or '' for elem in gt_texts_sorted])
    pred_combined = separator.join([elem.get('value', '') or '' for elem in pred_texts_sorted])
    edit_distance = levenshtein_distance(gt_combined, pred_combined)
    max_len = max(len(gt_combined), len(pred_combined), 1)
    normalized_distance = edit_distance / max_len
    text_accuracy = 1 - normalized_distance
    exact_match = gt_combined == pred_combined
    individual_texts_metrics = []
    max_individual = max(len(gt_elements), len(pred_elements))

    for i in range(max_individual):
        gt_text = gt_texts_sorted[i].get('value', '') if i < len(gt_texts_sorted) else ''
        pred_text = pred_texts_sorted[i].get('value', '') if i < len(pred_texts_sorted) else ''
        if gt_text or pred_text:
            max_text_len = max(len(gt_text), len(pred_text), 1)
            lev_dist = levenshtein_distance(gt_text, pred_text)
            norm_dist = lev_dist / max_text_len
            individual_texts_metrics.append({
                'index': i,
                'gt_text': gt_text,
                'pred_text': pred_text,
                'levenshtein_distance': lev_dist,
                'normalized_distance': norm_dist,
                'accuracy': 1 - norm_dist,
                'exact_match': gt_text == pred_text
            })

    if individual_texts_metrics:
        avg_edit_distance = sum(m['levenshtein_distance'] for m in individual_texts_metrics) / len(individual_texts_metrics)
        avg_normalized_distance = sum(m['normalized_distance'] for m in individual_texts_metrics) / len(individual_texts_metrics)
        avg_accuracy = sum(m['accuracy'] for m in individual_texts_metrics) / len(individual_texts_metrics)
        exact_match_count = sum(1 for m in individual_texts_metrics if m['exact_match'])
        exact_match_rate = exact_match_count / len(individual_texts_metrics)
    else:
        avg_edit_distance = 0
        avg_normalized_distance = 0
        avg_accuracy = 0
        exact_match_rate = 0

    metrics = {
        'value': {
            'correct': 1 if exact_match else 0,
            'total': 1,
            'accuracy': text_accuracy,
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
            'text_accuracy': text_accuracy,
            'exact_match_rate': 1.0 if exact_match else 0.0
        },
        'combined_text': {
            'gt_combined': gt_combined,
            'pred_combined': pred_combined,
            'edit_distance': edit_distance,
            'normalized_distance': normalized_distance,
            'accuracy': text_accuracy,
            'exact_match': exact_match
        },
        'individual_texts': {
            'metrics': individual_texts_metrics,
            'average_edit_distance': avg_edit_distance,
            'average_normalized_distance': avg_normalized_distance,
            'average_accuracy': avg_accuracy,
            'exact_match_rate': exact_match_rate,
            'total_texts': len(individual_texts_metrics)
        },
        'summary': {
            'gt_elements_count': len(gt_elements),
            'pred_elements_count': len(pred_elements),
            'matched_elements_count': min(len(gt_elements), len(pred_elements)),
            'missing_elements_count': max(0, len(gt_elements) - len(pred_elements)),
            'extra_elements_count': max(0, len(pred_elements) - len(gt_elements))
        }
    }

    return metrics

def calculate_lyrics_metrics_combined(gt_tree: Node, pred_tree: Node, measure_mapping: Dict[Tuple[int, int], Optional[int]] = None) -> Dict:
    gt_elements = extract_elements_with_attributes(gt_tree, "Lyrics")
    pred_elements = extract_elements_with_attributes(pred_tree, "Lyrics")
    gt_chords = extract_chords_with_attributes(gt_tree)
    pred_chords = extract_chords_with_attributes(pred_tree)
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
                    gt_chord_id_to_chord = {c.get('chord_id'): c for c in gt_measure_chords}
                    pred_chord_id_to_chord = {c.get('chord_id'): c for c in pred_measure_chords}
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
    gt_lyrics_list = []
    pred_lyrics_list = []
    for gt_lyric, pred_lyric in aligned_lyrics:
        if gt_lyric:
            gt_lyrics_list.append(gt_lyric.get('value', '') or '')
        if pred_lyric:
            pred_lyrics_list.append(pred_lyric.get('value', '') or '')

    separator = " "
    gt_combined = separator.join(gt_lyrics_list)
    pred_combined = separator.join(pred_lyrics_list)
    edit_distance = levenshtein_distance(gt_combined, pred_combined)
    max_len = max(len(gt_combined), len(pred_combined), 1)
    normalized_distance = edit_distance / max_len
    lyrics_accuracy = 1 - normalized_distance
    exact_match = gt_combined == pred_combined
    individual_lyrics_metrics = []
    for gt_lyric, pred_lyric in aligned_lyrics:
        gt_lyric_text = gt_lyric.get('value', '') if gt_lyric else ''
        pred_lyric_text = pred_lyric.get('value', '') if pred_lyric else ''
        if gt_lyric_text or pred_lyric_text:
            max_lyric_len = max(len(gt_lyric_text), len(pred_lyric_text), 1)
            lev_dist = levenshtein_distance(gt_lyric_text, pred_lyric_text)
            norm_dist = lev_dist / max_lyric_len
            individual_lyrics_metrics.append({
                'gt_lyric': gt_lyric_text,
                'pred_lyric': pred_lyric_text,
                'levenshtein_distance': lev_dist,
                'normalized_distance': norm_dist,
                'accuracy': 1 - norm_dist,
                'exact_match': gt_lyric_text == pred_lyric_text,
                'chord_id': gt_lyric.get('chord_id') if gt_lyric else (pred_lyric.get('chord_id') if pred_lyric else None),
                'staff_id': gt_lyric.get('staff_id') if gt_lyric else (pred_lyric.get('staff_id') if pred_lyric else None),
                'measure_id': gt_lyric.get('measure_id') if gt_lyric else (pred_lyric.get('measure_id') if pred_lyric else None)
            })

    if individual_lyrics_metrics:
        avg_edit_distance = sum(m['levenshtein_distance'] for m in individual_lyrics_metrics) / len(individual_lyrics_metrics)
        avg_normalized_distance = sum(m['normalized_distance'] for m in individual_lyrics_metrics) / len(individual_lyrics_metrics)
        avg_accuracy = sum(m['accuracy'] for m in individual_lyrics_metrics) / len(individual_lyrics_metrics)
        exact_match_count = sum(1 for m in individual_lyrics_metrics if m['exact_match'])
        exact_match_rate = exact_match_count / len(individual_lyrics_metrics)
    else:
        avg_edit_distance = 0
        avg_normalized_distance = 0
        avg_accuracy = 0
        exact_match_rate = 0

    metrics = {
        'value': {
            'correct': 1 if exact_match else 0,
            'total': 1,
            'accuracy': lyrics_accuracy,
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
            'lyrics_accuracy': lyrics_accuracy,
            'exact_match_rate': 1.0 if exact_match else 0.0
        },
        'combined_lyrics': {
            'gt_combined': gt_combined,
            'pred_combined': pred_combined,
            'edit_distance': edit_distance,
            'normalized_distance': normalized_distance,
            'accuracy': lyrics_accuracy,
            'exact_match': exact_match
        },
        'individual_lyrics': {
            'metrics': individual_lyrics_metrics,
            'average_edit_distance': avg_edit_distance,
            'average_normalized_distance': avg_normalized_distance,
            'average_accuracy': avg_accuracy,
            'exact_match_rate': exact_match_rate,
            'total_lyrics': len(individual_lyrics_metrics)
        },
        'summary': {
            'gt_elements_count': len(gt_elements),
            'pred_elements_count': len(pred_elements),
            'matched_elements_count': min(len(gt_elements), len(pred_elements)),
            'missing_elements_count': max(0, len(gt_elements) - len(pred_elements)),
            'extra_elements_count': max(0, len(pred_elements) - len(gt_elements))
        }
    }
    return metrics
