import sys
import os
import re
from core.score_tree import create_simplified_tree, Node
from collections import defaultdict
from typing import List, Dict, Tuple, Set
from Levenshtein import distance as levenshtein_distance

from metrics.tree_edit_distance import (
    tree_edit_distance,
    convert_to_apted_node,
    count_nodes,
    approximate_ted
)
from metrics.sequence_metrics import (
    character_error_rate,
    symbol_error_rate
)
from metrics.output import print_metrics
from metrics.error_analysis import (
    detailed_pitch_error_analysis,
    detailed_duration_error_analysis,
    detailed_rest_error_analysis,
    detailed_spanner_error_analysis,
    detailed_articulation_error_analysis,
    detailed_text_error_analysis,
    detailed_lyrics_error_analysis,
    print_detailed_errors
)


def extract_notes(node: Node, path: str = "", parent_chord_id=None, parent_duration=None, parent_has_dot=False, 
                  staff_id=None, part_id=None, measure_id=None) -> List[Dict]:
    notes = []
    
    current_staff_id = staff_id
    current_part_id = part_id
    current_measure_id = measure_id
    
    if node.label == "Part":
        current_part_id = node.id
    elif node.label == "Staff":
        current_staff_id = node.id
    elif node.label == "Measure":
        current_measure_id = node.id
    
    if node.label == "Note":
        note_info = {
            'pitch': node.value,
            'path': path,
            'accidental': None,
            'duration': parent_duration,
            'has_dot': parent_has_dot,
            'chord_id': parent_chord_id,
            'staff_id': current_staff_id,
            'part_id': current_part_id,
            'measure_id': current_measure_id
        }
        for child in node.children:
            if child.label == "Accidental":
                note_info['accidental'] = child.value
        notes.append(note_info)
    
    current_duration = parent_duration
    current_has_dot = parent_has_dot
    current_chord_id = parent_chord_id
    
    if node.label == "Chord":
        current_chord_id = node.id
        for child in node.children:
            if child.label == "Duration":
                current_duration = child.value
            elif child.label == "hasDot":
                current_has_dot = True
    
    for child in node.children:
        child_path = f"{path}/{node.label}" if path else node.label
        notes.extend(extract_notes(child, child_path, current_chord_id, current_duration, current_has_dot,
                                 current_staff_id, current_part_id, current_measure_id))
    
    return notes

def extract_rests(node: Node, path: str = "", staff_id=None, part_id=None, measure_id=None) -> List[Dict]:
    rests = []
    
    current_staff_id = staff_id
    current_part_id = part_id
    current_measure_id = measure_id
    
    if node.label == "Part":
        current_part_id = node.id
    elif node.label == "Staff":
        current_staff_id = node.id
    elif node.label == "Measure":
        current_measure_id = node.id
    
    if node.label == "Rest":
        rest_info = {
            'duration': None,
            'path': path,
            'staff_id': current_staff_id,
            'part_id': current_part_id,
            'measure_id': current_measure_id
        }
        for child in node.children:
            if child.label == "Duration":
                rest_info['duration'] = child.value
        rests.append(rest_info)
    
    for child in node.children:
        child_path = f"{path}/{node.label}" if path else node.label
        rests.extend(extract_rests(child, child_path, current_staff_id, current_part_id, current_measure_id))
    
    return rests

def note_level_metrics(ground_truth_tree, predicted_tree):
    gt_notes = extract_notes(ground_truth_tree)
    pred_notes = extract_notes(predicted_tree)
    
    gt_pitches = set(note['pitch'] for note in gt_notes)
    pred_pitches = set(note['pitch'] for note in pred_notes)
    
    true_positives = len(gt_pitches & pred_pitches)
    false_positives = len(pred_pitches - gt_pitches)
    false_negatives = len(gt_pitches - pred_pitches)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'total_gt_notes': len(gt_notes),
        'total_pred_notes': len(pred_notes)
    }

def pitch_accuracy(ground_truth_tree, predicted_tree):
    gt_notes = extract_notes(ground_truth_tree)
    pred_notes = extract_notes(predicted_tree)
    
    gt_by_path = defaultdict(list)
    pred_by_path = defaultdict(list)
    
    for note in gt_notes:
        gt_by_path[note['path']].append(note)
    for note in pred_notes:
        pred_by_path[note['path']].append(note)
    
    correct_pitches = 0
    total_comparisons = 0
    
    all_paths = set(gt_by_path.keys()) | set(pred_by_path.keys())
    
    for path in all_paths:
        gt_path_notes = gt_by_path[path]
        pred_path_notes = pred_by_path[path]
        
        min_len = min(len(gt_path_notes), len(pred_path_notes))
        for i in range(min_len):
            total_comparisons += 1
            if gt_path_notes[i]['pitch'] == pred_path_notes[i]['pitch']:
                correct_pitches += 1
    
    accuracy = correct_pitches / total_comparisons if total_comparisons > 0 else 0
    return accuracy, correct_pitches, total_comparisons

def duration_accuracy(ground_truth_tree, predicted_tree):
    gt_notes = extract_notes(ground_truth_tree)
    pred_notes = extract_notes(predicted_tree)
    gt_rests = extract_rests(ground_truth_tree)
    pred_rests = extract_rests(predicted_tree)
    
    gt_durations = [n['duration'] for n in gt_notes if n['duration'] is not None]
    pred_durations = [n['duration'] for n in pred_notes if n['duration'] is not None]
    
    gt_rest_durations = [r['duration'] for r in gt_rests if r['duration'] is not None]
    pred_rest_durations = [r['duration'] for r in pred_rests if r['duration'] is not None]
    
    gt_by_path = defaultdict(list)
    pred_by_path = defaultdict(list)
    
    for note in gt_notes:
        if note['duration']:
            gt_by_path[note['path']].append(note['duration'])
    for note in pred_notes:
        if note['duration']:
            pred_by_path[note['path']].append(note['duration'])
    
    correct_durations = 0
    total_durations = 0
    
    all_paths = set(gt_by_path.keys()) | set(pred_by_path.keys())
    for path in all_paths:
        gt_durs = gt_by_path[path]
        pred_durs = pred_by_path[path]
        min_len = min(len(gt_durs), len(pred_durs))
        for i in range(min_len):
            total_durations += 1
            if gt_durs[i] == pred_durs[i]:
                correct_durations += 1
    
    accuracy = correct_durations / total_durations if total_durations > 0 else 0
    return accuracy, correct_durations, total_durations


def extract_measures(node: Node) -> List[Dict]:
    measures = []
    
    if node.label == "Measure":
        measure_info = {
            'id': node.id,
            'notes_count': 0,
            'rests_count': 0,
            'chords_count': 0
        }
        for child in node.children:
            if child.label == "Note":
                measure_info['notes_count'] += 1
            elif child.label == "Rest":
                measure_info['rests_count'] += 1
            elif child.label == "Chord":
                measure_info['chords_count'] += 1
        measures.append(measure_info)
    
    for child in node.children:
        measures.extend(extract_measures(child))
    
    return measures

def measure_level_metrics(ground_truth_tree, predicted_tree):
    gt_measures = extract_measures(ground_truth_tree)
    pred_measures = extract_measures(predicted_tree)
    
    gt_measure_count = len(gt_measures)
    pred_measure_count = len(pred_measures)
    measure_count_accuracy = min(gt_measure_count, pred_measure_count) / max(gt_measure_count, pred_measure_count) if max(gt_measure_count, pred_measure_count) > 0 else 0
    
    min_measures = min(gt_measure_count, pred_measure_count)
    correct_measures = 0
    
    for i in range(min_measures):
        gt_m = gt_measures[i]
        pred_m = pred_measures[i]
        if (gt_m['notes_count'] + gt_m['chords_count']) == (pred_m['notes_count'] + pred_m['chords_count']):
            correct_measures += 1
    
    measure_content_accuracy = correct_measures / min_measures if min_measures > 0 else 0
    
    return {
        'measure_count_accuracy': measure_count_accuracy,
        'measure_content_accuracy': measure_content_accuracy,
        'gt_measure_count': gt_measure_count,
        'pred_measure_count': pred_measure_count,
        'correct_measures': correct_measures
    }


def extract_staffs(node: Node) -> List[Dict]:
    staffs = []
    
    if node.label == "Staff":
        staff_info = {
            'id': node.id,
            'clef': None,
            'measures_count': 0
        }
        for child in node.children:
            if child.label == "Clef":
                staff_info['clef'] = child.value
            elif child.label == "Measure":
                staff_info['measures_count'] += 1
        staffs.append(staff_info)
    
    for child in node.children:
        staffs.extend(extract_staffs(child))
    
    return staffs

def staff_level_metrics(ground_truth_tree, predicted_tree):
    gt_staffs = extract_staffs(ground_truth_tree)
    pred_staffs = extract_staffs(predicted_tree)
    
    gt_staff_count = len(gt_staffs)
    pred_staff_count = len(pred_staffs)
    staff_count_accuracy = min(gt_staff_count, pred_staff_count) / max(gt_staff_count, pred_staff_count) if max(gt_staff_count, pred_staff_count) > 0 else 0
    
    min_staffs = min(gt_staff_count, pred_staff_count)
    correct_clefs = 0
    
    for i in range(min_staffs):
        if gt_staffs[i]['clef'] == pred_staffs[i]['clef']:
            correct_clefs += 1
    
    clef_accuracy = correct_clefs / min_staffs if min_staffs > 0 else 0
    
    return {
        'staff_count_accuracy': staff_count_accuracy,
        'clef_accuracy': clef_accuracy,
        'gt_staff_count': gt_staff_count,
        'pred_staff_count': pred_staff_count,
        'correct_clefs': correct_clefs
    }


def calculate_prf1(gt_elements: List, pred_elements: List, key_func=None):
    if key_func is None:
        key_func = lambda x: str(x) if not isinstance(x, dict) else str(x.get('value', x))
    
    gt_set = set(key_func(elem) for elem in gt_elements)
    pred_set = set(key_func(elem) for elem in pred_elements)
    
    true_positives = len(gt_set & pred_set)
    false_positives = len(pred_set - gt_set)
    false_negatives = len(gt_set - pred_set)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives
    }

def extract_elements_by_label(node: Node, label: str) -> List[Dict]:
    elements = []
    
    if node.label == label:
        elem_info = {'value': node.value, 'id': node.id}
        elements.append(elem_info)
    
    for child in node.children:
        elements.extend(extract_elements_by_label(child, label))
    
    return elements

def extract_instruments(node: Node) -> List[str]:
    instruments = []
    
    if node.label == "Instrument":
        if node.value:
            instruments.append(node.value)
    
    for child in node.children:
        instruments.extend(extract_instruments(child))
    
    return instruments

def normalize_instrument_name(name: str) -> str:
    return re.sub(r'\s+\d+$', '', name).strip()

def extract_clefs(node: Node) -> List[str]:
    clefs = []
    
    if node.label == "Clef":
        if node.value:
            clefs.append(node.value)
    
    for child in node.children:
        clefs.extend(extract_clefs(child))
    
    return clefs

def extract_time_signatures(node: Node) -> List[str]:
    time_sigs = []
    
    if node.label == "TimeSig":
        if node.value:
            time_sigs.append(node.value)
    
    for child in node.children:
        time_sigs.extend(extract_time_signatures(child))
    
    return time_sigs

def extract_accidentals(node: Node) -> List[str]:
    accidentals = []
    
    if node.label == "Accidental":
        if node.value:
            accidentals.append(node.value)
    
    for child in node.children:
        accidentals.extend(extract_accidentals(child))
    
    return accidentals

def extract_ties(node: Node) -> List[str]:
    ties = []
    
    if node.label == "Spanner":
        if node.value and ('tie' in node.value.lower() or node.value == 'Tie'):
            ties.append(node.value)
    
    for child in node.children:
        ties.extend(extract_ties(child))
    
    return ties

def extract_dynamics(node: Node) -> List[str]:
    dynamics = []
    
    if node.label == "Dynamic":
        if node.value:
            dynamics.append(node.value)
    
    for child in node.children:
        dynamics.extend(extract_dynamics(child))
    
    return dynamics

def extract_tempos(node: Node) -> List[str]:
    tempos = []
    
    if node.label == "Tempo":
        if node.value:
            tempos.append(node.value)
    
    for child in node.children:
        tempos.extend(extract_tempos(child))
    
    return tempos

def extract_lyrics(node: Node) -> List[str]:
    lyrics = []
    
    if node.label == "Lyrics":
        if node.value:
            lyrics.append(node.value)
    
    for child in node.children:
        lyrics.extend(extract_lyrics(child))
    
    return lyrics

def extract_spanners(node: Node) -> List[str]:
    spanners = []
    
    if node.label == "Spanner":
        if node.value:
            spanners.append(node.value)
    
    for child in node.children:
        spanners.extend(extract_spanners(child))
    
    return spanners

def extract_articulations(node: Node) -> List[str]:
    articulations = []
    
    if node.label == "Articulation":
        if node.value:
            articulations.append(node.value)
    
    for child in node.children:
        articulations.extend(extract_articulations(child))
    
    return articulations

def extract_articulations_with_position(node: Node, staff_id=None, part_id=None, measure_id=None, chord_id=None) -> List[Dict]:
    articulations = []
    
    current_staff_id = staff_id
    current_part_id = part_id
    current_measure_id = measure_id
    current_chord_id = chord_id
    
    if node.label == "Part":
        current_part_id = node.id
    elif node.label == "Staff":
        current_staff_id = node.id
    elif node.label == "Measure":
        current_measure_id = node.id
    elif node.label == "Chord":
        current_chord_id = node.id
    
    if node.label == "Articulation":
        if node.value:
            articulations.append({
                'articulation': node.value,
                'staff_id': current_staff_id,
                'part_id': current_part_id,
                'measure_id': current_measure_id,
                'chord_id': current_chord_id
            })
    
    for child in node.children:
        articulations.extend(extract_articulations_with_position(
            child, current_staff_id, current_part_id, current_measure_id, current_chord_id
        ))
    
    return articulations

def extract_text_from_tree(node: Node) -> List[str]:
    texts = []
    
    if node.label == "Text":
        if node.value:
            texts.append(node.value)
    
    for child in node.children:
        texts.extend(extract_text_from_tree(child))
    
    return texts

def individual_element_category_metrics(ground_truth_tree, predicted_tree, gt_path, pred_path):
    results = {}
    
    gt_instruments = extract_instruments(ground_truth_tree)
    pred_instruments = extract_instruments(predicted_tree)

    results['instruments'] = calculate_prf1(gt_instruments, pred_instruments, key_func=normalize_instrument_name)
    
    gt_staffs = extract_staffs(ground_truth_tree)
    pred_staffs = extract_staffs(predicted_tree)
    results['staffs'] = calculate_prf1(
        [s['id'] for s in gt_staffs],
        [s['id'] for s in pred_staffs]
    )
    
    gt_clefs = extract_clefs(ground_truth_tree)
    pred_clefs = extract_clefs(predicted_tree)
    results['clefs'] = calculate_prf1(gt_clefs, pred_clefs)
    
    gt_time_sigs = extract_time_signatures(ground_truth_tree)
    pred_time_sigs = extract_time_signatures(predicted_tree)
    results['time_signatures'] = calculate_prf1(gt_time_sigs, pred_time_sigs)
    
    gt_accidentals = extract_accidentals(ground_truth_tree)
    pred_accidentals = extract_accidentals(predicted_tree)
    results['accidentals'] = calculate_prf1(gt_accidentals, pred_accidentals)
    
    gt_ties = extract_ties(ground_truth_tree)
    pred_ties = extract_ties(predicted_tree)
    results['ties'] = calculate_prf1(gt_ties, pred_ties)
    
    gt_spanners = extract_spanners(ground_truth_tree)
    pred_spanners = extract_spanners(predicted_tree)
    results['spanners'] = calculate_prf1(gt_spanners, pred_spanners)
    
    gt_articulations = extract_articulations(ground_truth_tree)
    pred_articulations = extract_articulations(predicted_tree)
    results['articulations'] = calculate_prf1(gt_articulations, pred_articulations)
    
    gt_text_tree = extract_text_from_tree(ground_truth_tree)
    pred_text_tree = extract_text_from_tree(predicted_tree)
    
    text_tree_metrics = {}
    total_lev_dist = 0
    total_max_len = 0
    matched_count = 0
    
    max_len = max(len(gt_text_tree), len(pred_text_tree))
    for i in range(max_len):
        gt_t = gt_text_tree[i] if i < len(gt_text_tree) else ""
        pred_t = pred_text_tree[i] if i < len(pred_text_tree) else ""
        
        if gt_t or pred_t:
            max_text_len = max(len(gt_t), len(pred_t), 1)
            lev_dist = levenshtein_distance(gt_t, pred_t)
            total_lev_dist += lev_dist
            total_max_len += max_text_len
            
            text_tree_metrics[f'text_{i}'] = {
                'levenshtein_distance': lev_dist,
                'normalized_distance': lev_dist / max_text_len,
                'accuracy': 1 - (lev_dist / max_text_len) if max_text_len > 0 else 0,
                'gt_text': gt_t,
                'pred_text': pred_t
            }
            matched_count += 1
    
    overall_normalized = total_lev_dist / total_max_len if total_max_len > 0 else 0
    overall_accuracy = 1 - overall_normalized
    
    results['text_elements_tree'] = {
        'texts': text_tree_metrics,
        'overall_levenshtein_distance': total_lev_dist,
        'overall_normalized_distance': overall_normalized,
        'overall_accuracy': overall_accuracy,
        'total_texts': matched_count
    }
    
    gt_lyrics = extract_lyrics(ground_truth_tree)
    pred_lyrics = extract_lyrics(predicted_tree)
    results['lyrics'] = calculate_prf1(gt_lyrics, pred_lyrics)
    
    gt_dynamics = extract_dynamics(ground_truth_tree)
    pred_dynamics = extract_dynamics(predicted_tree)
    results['dynamics'] = calculate_prf1(gt_dynamics, pred_dynamics)
    
    gt_tempos = extract_tempos(ground_truth_tree)
    pred_tempos = extract_tempos(predicted_tree)
    results['tempos'] = calculate_prf1(gt_tempos, pred_tempos)
    
    tempo_text_metrics = {}
    for i, (gt_t, pred_t) in enumerate(zip(gt_tempos, pred_tempos)):
        if gt_t or pred_t:
            max_len = max(len(gt_t), len(pred_t), 1)
            lev_dist = levenshtein_distance(gt_t, pred_t)
            tempo_text_metrics[f'tempo_{i}'] = {
                'levenshtein_distance': lev_dist,
                'normalized_distance': lev_dist / max_len,
                'accuracy': 1 - (lev_dist / max_len)
            }
    results['tempo_text'] = tempo_text_metrics
    
    return results



def calculate_all_metrics(ground_truth_path, predicted_path, 
                          ted_approximate=False):
    print(f"Loading ground truth from {ground_truth_path}...")
    gt_tree = create_simplified_tree(ground_truth_path)
    
    print(f"Loading prediction from {predicted_path}...")
    pred_tree = create_simplified_tree(predicted_path)
    
    gt_size = count_nodes(convert_to_apted_node(gt_tree))
    pred_size = count_nodes(convert_to_apted_node(pred_tree))
    print(f"Tree sizes: GT={gt_size}, Pred={pred_size}")
    
    if gt_size > 500 or pred_size > 500:
        if not ted_approximate:
            print("  Large trees detected. Consider using --ted-approximate")
    
    print("Computing metrics...")
    
    results = {}
    
    print("\n1. Computing Tree Edit Distance...")
    import time
    ted_start = time.time()
    ted, ted_error, ted_accuracy = tree_edit_distance(
        gt_tree, pred_tree,
        approximate=ted_approximate
    )
    ted_elapsed = time.time() - ted_start
    print(f"   TED computed in {ted_elapsed:.2f} seconds")
    results['tree_edit_distance'] = {
        'distance': ted,
        'normalized_error': ted_error,
        'accuracy': ted_accuracy,
        'computation_time': ted_elapsed
    }
    
    print("2. Computing note-level metrics...")
    note_metrics = note_level_metrics(gt_tree, pred_tree)
    results['note_level'] = note_metrics
    
    pitch_acc, correct_pitches, total_pitches = pitch_accuracy(gt_tree, pred_tree)
    results['pitch_accuracy'] = {
        'accuracy': pitch_acc,
        'correct_pitches': correct_pitches,
        'total_pitches': total_pitches
    }
    
    pitch_errors = detailed_pitch_error_analysis(gt_tree, pred_tree)
    results['pitch_errors'] = pitch_errors
    
    duration_errors = detailed_duration_error_analysis(gt_tree, pred_tree)
    results['duration_errors'] = duration_errors
    
    rest_errors = detailed_rest_error_analysis(gt_tree, pred_tree)
    results['rest_errors'] = rest_errors
    
    spanner_errors = detailed_spanner_error_analysis(gt_tree, pred_tree)
    results['spanner_errors'] = spanner_errors
    
    articulation_errors = detailed_articulation_error_analysis(gt_tree, pred_tree)
    results['articulation_errors'] = articulation_errors
    
    text_errors = detailed_text_error_analysis(gt_tree, pred_tree)
    results['text_errors'] = text_errors
    
    lyrics_errors = detailed_lyrics_error_analysis(gt_tree, pred_tree)
    results['lyrics_errors'] = lyrics_errors
    
    dur_acc, correct_durs, total_durs = duration_accuracy(gt_tree, pred_tree)
    results['duration_accuracy'] = {
        'accuracy': dur_acc,
        'correct_durations': correct_durs,
        'total_durations': total_durs
    }
    
    measure_metrics = measure_level_metrics(gt_tree, pred_tree)
    results['measure_level'] = measure_metrics
    
    staff_metrics = staff_level_metrics(gt_tree, pred_tree)
    results['staff_level'] = staff_metrics
    
    print("\n4. Computing element category metrics...")
    results['element_categories'] = individual_element_category_metrics(
        gt_tree, pred_tree, ground_truth_path, predicted_path
    )
    
    print("\n5. Computing sequence metrics (CER, SER)...")
    results['cer'] = character_error_rate(gt_tree, pred_tree)
    results['ser'] = symbol_error_rate(gt_tree, pred_tree)
    
    return results



if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Compute quality metrics for OMR results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python calculate_metrics.py data/mscz/score.mscz data/predicted/score.mscz
  
  python calculate_metrics.py data/mscz/score.mscz data/predicted/score.mscz \\
      --ted-approximate
  
  python calculate_metrics.py data/mscz/score.mscz data/predicted/score.mscz \\
      --detailed-errors
        """
    )
    
    parser.add_argument('ground_truth', help='Path to ground truth .mscz file')
    parser.add_argument('predicted', help='Path to predicted .mscz file')
    
    parser.add_argument('--ted-approximate', action='store_true',
                       help='Use approximate algorithm for large trees (much faster)')
    
    parser.add_argument('--detailed-errors', action='store_true',
                       help='Show detailed error analysis for note pitches')
    
    args = parser.parse_args()
    
    results = calculate_all_metrics(
        args.ground_truth,
        args.predicted,
        ted_approximate=args.ted_approximate
    )
    print_metrics(results, show_detailed_errors=args.detailed_errors)
