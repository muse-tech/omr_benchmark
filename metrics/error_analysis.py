from collections import defaultdict
from typing import List, Dict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.score_tree import Node


def detailed_pitch_error_analysis(ground_truth_tree, predicted_tree):
    from calculate_metrics import extract_notes
    
    gt_notes = extract_notes(ground_truth_tree)
    pred_notes = extract_notes(predicted_tree)
    
    gt_by_measure_staff = defaultdict(list)
    pred_by_measure_staff = defaultdict(list)
    
    for note in gt_notes:
        key = (note.get('part_id'), note.get('staff_id'), note.get('measure_id'))
        gt_by_measure_staff[key].append(note)
    
    for note in pred_notes:
        key = (note.get('part_id'), note.get('staff_id'), note.get('measure_id'))
        pred_by_measure_staff[key].append(note)
    
    errors = []
    all_keys = set(gt_by_measure_staff.keys()) | set(pred_by_measure_staff.keys())
    
    for key in sorted(all_keys):
        part_id, staff_id, measure_id = key
        gt_measure_notes = gt_by_measure_staff[key]
        pred_measure_notes = pred_by_measure_staff[key]
        gt_note_keys = {}
        for i, note in enumerate(gt_measure_notes):
            note_key = (note.get('pitch'), note.get('chord_id'))
            if note_key not in gt_note_keys:
                gt_note_keys[note_key] = []
            gt_note_keys[note_key].append((i, note))
        
        pred_note_keys = {}
        for i, note in enumerate(pred_measure_notes):
            note_key = (note.get('pitch'), note.get('chord_id'))
            if note_key not in pred_note_keys:
                pred_note_keys[note_key] = []
            pred_note_keys[note_key].append((i, note))
        
        matched_gt_indices = set()
        matched_pred_indices = set()
        pitch_mismatches = {} 
        
        min_len = min(len(gt_measure_notes), len(pred_measure_notes))
        
        for i in range(min_len):
            gt_note = gt_measure_notes[i]
            pred_note = pred_measure_notes[i]
            gt_pitch = gt_note.get('pitch')
            pred_pitch = pred_note.get('pitch')
            
            if gt_pitch == pred_pitch:
                matched_gt_indices.add(i)
                matched_pred_indices.add(i)
            else:
                pitch_mismatches[i] = i

        for note_key in set(gt_note_keys.keys()) & set(pred_note_keys.keys()):
            gt_list = gt_note_keys[note_key]
            pred_list = pred_note_keys[note_key]
            
            unmatched_gt = [(idx, note) for idx, note in gt_list if idx not in matched_gt_indices]
            unmatched_pred = [(idx, note) for idx, note in pred_list if idx not in matched_pred_indices]
            
            min_count = min(len(unmatched_gt), len(unmatched_pred))
            
            for j in range(min_count):
                matched_gt_indices.add(unmatched_gt[j][0])
                matched_pred_indices.add(unmatched_pred[j][0])
        
        if len(gt_measure_notes) != len(pred_measure_notes):
            errors.append({
                'type': 'count_mismatch',
                'part_id': part_id,
                'staff_id': staff_id,
                'measure_id': measure_id,
                'gt_count': len(gt_measure_notes),
                'pred_count': len(pred_measure_notes),
                'details': None
            })
        
        for gt_idx, pred_idx in pitch_mismatches.items():
            if gt_idx not in matched_gt_indices and pred_idx not in matched_pred_indices:
                errors.append({
                    'type': 'pitch_mismatch',
                    'part_id': part_id,
                    'staff_id': staff_id,
                    'measure_id': measure_id,
                    'note_index': gt_idx,
                    'gt_pitch': gt_measure_notes[gt_idx].get('pitch'),
                    'pred_pitch': pred_measure_notes[pred_idx].get('pitch'),
                    'gt_duration': gt_measure_notes[gt_idx].get('duration'),
                    'pred_duration': pred_measure_notes[pred_idx].get('duration')
                })
                matched_gt_indices.add(gt_idx)
                matched_pred_indices.add(pred_idx)
        
        for i, note in enumerate(gt_measure_notes):
            if i not in matched_gt_indices:
                errors.append({
                    'type': 'missing_note',
                    'part_id': part_id,
                    'staff_id': staff_id,
                    'measure_id': measure_id,
                    'note_index': i,
                    'gt_pitch': note.get('pitch')
                })
        
        for i, note in enumerate(pred_measure_notes):
            if i not in matched_pred_indices:
                errors.append({
                    'type': 'extra_note',
                    'part_id': part_id,
                    'staff_id': staff_id,
                    'measure_id': measure_id,
                    'note_index': i,
                    'pred_pitch': note.get('pitch')
                })
    
    return errors


def detailed_duration_error_analysis(ground_truth_tree, predicted_tree):
    from calculate_metrics import extract_notes
    
    gt_notes = extract_notes(ground_truth_tree)
    pred_notes = extract_notes(predicted_tree)
    
    errors = []
    gt_by_path = defaultdict(list)
    pred_by_path = defaultdict(list)
    
    for note in gt_notes:
        if note.get('duration'):
            gt_by_path[note['path']].append({
                'duration': note['duration'],
                'pitch': note.get('pitch'),
                'part_id': note.get('part_id'),
                'staff_id': note.get('staff_id'),
                'measure_id': note.get('measure_id')
            })
    
    for note in pred_notes:
        if note.get('duration'):
            pred_by_path[note['path']].append({
                'duration': note['duration'],
                'pitch': note.get('pitch'),
                'part_id': note.get('part_id'),
                'staff_id': note.get('staff_id'),
                'measure_id': note.get('measure_id')
            })
    
    all_paths = set(gt_by_path.keys()) | set(pred_by_path.keys())
    for path in all_paths:
        gt_durs = gt_by_path[path]
        pred_durs = pred_by_path[path]
        min_len = min(len(gt_durs), len(pred_durs))
        
        for i in range(min_len):
            if gt_durs[i]['duration'] != pred_durs[i]['duration']:
                errors.append({
                    'type': 'duration_mismatch',
                    'part_id': gt_durs[i].get('part_id'),
                    'staff_id': gt_durs[i].get('staff_id'),
                    'measure_id': gt_durs[i].get('measure_id'),
                    'index': i,
                    'gt_duration': gt_durs[i]['duration'],
                    'pred_duration': pred_durs[i]['duration'],
                    'pitch': gt_durs[i].get('pitch')
                })
        
        if len(pred_durs) > len(gt_durs):
            for i in range(len(gt_durs), len(pred_durs)):
                errors.append({
                    'type': 'extra_duration',
                    'part_id': pred_durs[i].get('part_id'),
                    'staff_id': pred_durs[i].get('staff_id'),
                    'measure_id': pred_durs[i].get('measure_id'),
                    'pred_duration': pred_durs[i]['duration'],
                    'pitch': pred_durs[i].get('pitch')
                })
        
        if len(gt_durs) > len(pred_durs):
            for i in range(len(pred_durs), len(gt_durs)):
                errors.append({
                    'type': 'missing_duration',
                    'part_id': gt_durs[i].get('part_id'),
                    'staff_id': gt_durs[i].get('staff_id'),
                    'measure_id': gt_durs[i].get('measure_id'),
                    'gt_duration': gt_durs[i]['duration'],
                    'pitch': gt_durs[i].get('pitch')
                })
    
    return errors


def detailed_rest_error_analysis(ground_truth_tree, predicted_tree):
    from calculate_metrics import extract_rests
    
    gt_rests = extract_rests(ground_truth_tree)
    pred_rests = extract_rests(predicted_tree)
    
    errors = []
    gt_by_path = defaultdict(list)
    pred_by_path = defaultdict(list)
    
    for rest in gt_rests:
        gt_by_path[rest['path']].append({
            'duration': rest.get('duration'),
            'part_id': rest.get('part_id'),
            'staff_id': rest.get('staff_id'),
            'measure_id': rest.get('measure_id')
        })
    
    for rest in pred_rests:
        pred_by_path[rest['path']].append({
            'duration': rest.get('duration'),
            'part_id': rest.get('part_id'),
            'staff_id': rest.get('staff_id'),
            'measure_id': rest.get('measure_id')
        })
    
    all_paths = set(gt_by_path.keys()) | set(pred_by_path.keys())
    
    for path in all_paths:
        gt_rest_durs = gt_by_path[path]
        pred_rest_durs = pred_by_path[path]
        min_len = min(len(gt_rest_durs), len(pred_rest_durs))
        
        for i in range(min_len):
            if gt_rest_durs[i]['duration'] != pred_rest_durs[i]['duration']:
                errors.append({
                    'type': 'rest_duration_mismatch',
                    'index': i,
                    'gt_duration': gt_rest_durs[i]['duration'],
                    'pred_duration': pred_rest_durs[i]['duration'],
                    'part_id': gt_rest_durs[i].get('part_id'),
                    'staff_id': gt_rest_durs[i].get('staff_id'),
                    'measure_id': gt_rest_durs[i].get('measure_id')
                })
        
        if len(pred_rest_durs) > len(gt_rest_durs):
            rest_info = pred_rest_durs[len(gt_rest_durs)]
            errors.append({
                'type': 'extra_rest',
                'pred_duration': rest_info['duration'],
                'part_id': rest_info.get('part_id'),
                'staff_id': rest_info.get('staff_id'),
                'measure_id': rest_info.get('measure_id')
            })
        
        if len(gt_rest_durs) > len(pred_rest_durs):
            rest_info = gt_rest_durs[len(pred_rest_durs)]
            errors.append({
                'type': 'missing_rest',
                'gt_duration': rest_info['duration'],
                'part_id': rest_info.get('part_id'),
                'staff_id': rest_info.get('staff_id'),
                'measure_id': rest_info.get('measure_id')
            })
    
    return errors


def detailed_spanner_error_analysis(ground_truth_tree, predicted_tree):
    from calculate_metrics import extract_spanners
    
    gt_spanners = extract_spanners(ground_truth_tree)
    pred_spanners = extract_spanners(predicted_tree)
    
    errors = []
    gt_set = set(gt_spanners)
    pred_set = set(pred_spanners)
    
    for spanner in gt_set - pred_set:
        errors.append({
            'type': 'missing_spanner',
            'spanner': spanner
        })
    
    for spanner in pred_set - gt_set:
        errors.append({
            'type': 'extra_spanner',
            'spanner': spanner
        })
    
    return errors


def detailed_articulation_error_analysis(ground_truth_tree, predicted_tree):
    from calculate_metrics import extract_articulations_with_position
    
    gt_articulations = extract_articulations_with_position(ground_truth_tree)
    pred_articulations = extract_articulations_with_position(predicted_tree)
    
    errors = []
    
    gt_by_position = defaultdict(list)
    pred_by_position = defaultdict(list)
    
    for art in gt_articulations:
        key = (art.get('staff_id'), art.get('measure_id'), art.get('chord_id'))
        gt_by_position[key].append(art['articulation'])
    
    for art in pred_articulations:
        key = (art.get('staff_id'), art.get('measure_id'), art.get('chord_id'))
        pred_by_position[key].append(art['articulation'])
    
    all_positions = set(gt_by_position.keys()) | set(pred_by_position.keys())
    
    for position in all_positions:
        staff_id, measure_id, chord_id = position
        part_id = None
        gt_arts = set(gt_by_position[position])
        pred_arts = set(pred_by_position[position])
        
        for articulation in gt_arts - pred_arts:
            errors.append({
                'type': 'missing_articulation',
                'articulation': articulation,
                'part_id': part_id,
                'staff_id': staff_id,
                'measure_id': measure_id,
                'chord_id': chord_id,
                'gt_articulations': sorted(gt_arts),
                'pred_articulations': sorted(pred_arts)
            })
        
        for articulation in pred_arts - gt_arts:
            errors.append({
                'type': 'extra_articulation',
                'articulation': articulation,
                'part_id': part_id,
                'staff_id': staff_id,
                'measure_id': measure_id,
                'chord_id': chord_id,
                'gt_articulations': sorted(gt_arts),
                'pred_articulations': sorted(pred_arts)
            })
    
    return errors


def detailed_text_error_analysis(ground_truth_tree, predicted_tree):
    from calculate_metrics import extract_text_from_tree
    
    gt_texts = extract_text_from_tree(ground_truth_tree)
    pred_texts = extract_text_from_tree(predicted_tree)
    
    errors = []
    gt_set = set(gt_texts)
    pred_set = set(pred_texts)
    
    for text in gt_set - pred_set:
        errors.append({
            'type': 'missing_text',
            'text': text
        })
    
    for text in pred_set - gt_set:
        errors.append({
            'type': 'extra_text',
            'text': text
        })
    
    return errors


def detailed_lyrics_error_analysis(ground_truth_tree, predicted_tree):
    from calculate_metrics import extract_lyrics
    
    gt_lyrics = extract_lyrics(ground_truth_tree)
    pred_lyrics = extract_lyrics(predicted_tree)
    
    errors = []
    gt_set = set(gt_lyrics)
    pred_set = set(pred_lyrics)
    
    for lyric in gt_set - pred_set:
        errors.append({
            'type': 'missing_lyric',
            'lyric': lyric
        })
    
    for lyric in pred_set - gt_set:
        errors.append({
            'type': 'extra_lyric',
            'lyric': lyric
        })
    
    return errors


def print_detailed_pitch_errors(errors, limit=50):
    if not errors:
        return
    
    print(f"\n  PITCH ERRORS:")
    print(f"  Total errors: {len(errors)}")
    
    by_type = defaultdict(list)
    for error in errors:
        by_type[error['type']].append(error)
    
    print(f"  Error types:")
    for error_type, error_list in by_type.items():
        print(f"    {error_type}: {len(error_list)}")
    
    print(f"  Errors by measures (showing up to {limit} errors):")
    
    shown_count = 0
    current_measure = None
    
    for error in errors[:limit]:
        staff_id = error.get('staff_id', '?')
        measure_id = error.get('measure_id', '?')
        
        measure_key = f"Staff {staff_id}, Measure {measure_id}"
        
        if measure_key != current_measure:
            if current_measure is not None:
                print()
            print(f"    {measure_key}:")
            current_measure = measure_key
        
        if error['type'] == 'pitch_mismatch':
            print(f"      Note #{error['note_index']}: GT={error['gt_pitch']} → Pred={error['pred_pitch']} "
                  f"(Duration: GT={error['gt_duration']}, Pred={error['pred_duration']})")
        elif error['type'] == 'count_mismatch':
            print(f"      Note count mismatch: GT={error['gt_count']}, Pred={error['pred_count']}")
        elif error['type'] == 'extra_note':
            print(f"      Extra note #{error['note_index']}: {error['pred_pitch']}")
        elif error['type'] == 'missing_note':
            print(f"      Missing note #{error['note_index']}: {error['gt_pitch']}")
        
        shown_count += 1
    
    if len(errors) > limit:
        print(f"    ... and {len(errors) - limit} more errors")


def print_detailed_errors(all_errors, limit=50):        
    has_errors = any(errors for errors in all_errors.values() if errors)
    
    if not has_errors:
        print("\nNo errors detected!")
        return
    
    print(f"\nDETAILED ERROR ANALYSIS")
    print("="*100)
    
    if 'pitch_errors' in all_errors and all_errors['pitch_errors']:
        print_detailed_pitch_errors(all_errors['pitch_errors'], limit)
    
    if 'duration_errors' in all_errors and all_errors['duration_errors']:
        errors = all_errors['duration_errors']
        print(f"\n  NOTE DURATION ERRORS:")
        print(f"  Total errors: {len(errors)}")
        
        by_type = defaultdict(list)
        for error in errors:
            by_type[error['type']].append(error)
        
        print(f"  Error types:")
        for error_type, error_list in by_type.items():
            print(f"    {error_type}: {len(error_list)}")
        
        print(f"  Errors (showing up to {limit}):")
        for error in errors[:limit]:
            staff_id = error.get('staff_id', '?')
            measure_id = error.get('measure_id', '?')
            if error['type'] == 'duration_mismatch':
                print(f"    Staff {staff_id}, Measure {measure_id}: "
                      f"GT={error['gt_duration']} → Pred={error['pred_duration']} "
                      f"(Pitch: {error.get('pitch', '?')})")
            elif error['type'] == 'extra_duration':
                print(f"    Extra duration: Pred={error['pred_duration']} (Pitch: {error.get('pitch', '?')})")
            elif error['type'] == 'missing_duration':
                print(f"    Missing duration: GT={error['gt_duration']} (Pitch: {error.get('pitch', '?')})")
        
        if len(errors) > limit:
            print(f"    ... and {len(errors) - limit} more errors")
    
    if 'rest_errors' in all_errors and all_errors['rest_errors']:
        errors = all_errors['rest_errors']
        print(f"\n  REST ERRORS:")
        print(f"  Total errors: {len(errors)}")
        
        by_type = defaultdict(list)
        for error in errors:
            by_type[error['type']].append(error)
        
        print(f"  Error types:")
        for error_type, error_list in by_type.items():
            print(f"    {error_type}: {len(error_list)}")
        
        print(f"  Errors (showing up to {limit}):")
        for error in errors[:limit]:
            staff_id = error.get('staff_id', '?')
            measure_id = error.get('measure_id', '?')
            location = f"Staff {staff_id}, Measure {measure_id}"
            
            if error['type'] == 'rest_duration_mismatch':
                print(f"    {location}: GT={error['gt_duration']} → Pred={error['pred_duration']}")
            elif error['type'] == 'extra_rest':
                print(f"    Extra rest: {location}, Pred={error['pred_duration']}")
            elif error['type'] == 'missing_rest':
                print(f"    Missing rest: {location}, GT={error['gt_duration']}")
        
        if len(errors) > limit:
            print(f"    ... and {len(errors) - limit} more errors")
    
    if 'spanner_errors' in all_errors and all_errors['spanner_errors']:
        errors = all_errors['spanner_errors']
        print(f"\n  SPANNER ERRORS:")
        print(f"  Total errors: {len(errors)}")
        
        by_type = defaultdict(list)
        for error in errors:
            by_type[error['type']].append(error)
        
        print(f"  Error types:")
        for error_type, error_list in by_type.items():
            print(f"    {error_type}: {len(error_list)}")
        
        print(f"  Errors (showing up to {limit}):")
        for error in errors[:limit]:
            if error['type'] == 'missing_spanner':
                print(f"    Missing spanner: {error['spanner']}")
            elif error['type'] == 'extra_spanner':
                print(f"    Extra spanner: {error['spanner']}")
        
        if len(errors) > limit:
            print(f"    ... and {len(errors) - limit} more errors")
    
    if 'articulation_errors' in all_errors and all_errors['articulation_errors']:
        errors = all_errors['articulation_errors']
        print(f"\n  ARTICULATION ERRORS:")
        print(f"  Total errors: {len(errors)}")
        
        by_type = defaultdict(list)
        for error in errors:
            by_type[error['type']].append(error)
        
        print(f"  Error types:")
        for error_type, error_list in by_type.items():
            print(f"    {error_type}: {len(error_list)}")
        
        print(f"  Errors (showing up to {limit}):")
        for error in errors[:limit]:
            staff_id = error.get('staff_id', '?')
            measure_id = error.get('measure_id', '?')
            chord_id = error.get('chord_id', '?')
            location = f"Staff {staff_id}, Measure {measure_id}"
            if chord_id != '?':
                location += f", Chord {chord_id}"
            
            gt_arts = error.get('gt_articulations', [])
            pred_arts = error.get('pred_articulations', [])
            
            if error['type'] == 'missing_articulation':
                gt_str = ', '.join(gt_arts) if gt_arts else '(no articulations)'
                pred_str = ', '.join(pred_arts) if pred_arts else '(no articulations)'
                print(f"    Missing articulation: {error['articulation']} ({location})")
                print(f"       GT: [{gt_str}], Pred: [{pred_str}]")
            elif error['type'] == 'extra_articulation':
                gt_str = ', '.join(gt_arts) if gt_arts else '(no articulations)'
                pred_str = ', '.join(pred_arts) if pred_arts else '(no articulations)'
                print(f"    Extra articulation: {error['articulation']} ({location})")
                print(f"       GT: [{gt_str}], Pred: [{pred_str}]")
        
        if len(errors) > limit:
            print(f"    ... and {len(errors) - limit} more errors")
    
    if 'text_errors' in all_errors and all_errors['text_errors']:
        errors = all_errors['text_errors']
        print(f"\n  TEXT ELEMENT ERRORS:")
        print(f"  Total errors: {len(errors)}")
        
        by_type = defaultdict(list)
        for error in errors:
            by_type[error['type']].append(error)
        
        print(f"  Error types:")
        for error_type, error_list in by_type.items():
            print(f"    {error_type}: {len(error_list)}")
        
        print(f"  Errors (showing up to {limit}):")
        for error in errors[:limit]:
            if error['type'] == 'missing_text':
                print(f"    Missing text: {error['text'][:50]}..." if len(error['text']) > 50 else f"    Missing text: {error['text']}")
            elif error['type'] == 'extra_text':
                print(f"    Extra text: {error['text'][:50]}..." if len(error['text']) > 50 else f"    Extra text: {error['text']}")
        
        if len(errors) > limit:
            print(f"    ... and {len(errors) - limit} more errors")
    
    if 'lyrics_errors' in all_errors and all_errors['lyrics_errors']:
        errors = all_errors['lyrics_errors']
        print(f"\n  LYRICS ERRORS:")
        print(f"  Total errors: {len(errors)}")
        
        by_type = defaultdict(list)
        for error in errors:
            by_type[error['type']].append(error)
        
        print(f"  Error types:")
        for error_type, error_list in by_type.items():
            print(f"    {error_type}: {len(error_list)}")
        
        print(f"  Errors (showing up to {limit}):")
        for error in errors[:limit]:
            if error['type'] == 'missing_lyric':
                print(f"    Missing text: {error['lyric'][:50]}..." if len(error['lyric']) > 50 else f"    Missing text: {error['lyric']}")
            elif error['type'] == 'extra_lyric':
                print(f"    Extra text: {error['lyric'][:50]}..." if len(error['lyric']) > 50 else f"    Extra text: {error['lyric']}")
        
        if len(errors) > limit:
            print(f"    ... and {len(errors) - limit} more errors")
    
    print("\n" + "="*100)


__all__ = [
    'detailed_pitch_error_analysis',
    'detailed_duration_error_analysis',
    'detailed_rest_error_analysis',
    'detailed_spanner_error_analysis',
    'detailed_articulation_error_analysis',
    'detailed_text_error_analysis',
    'detailed_lyrics_error_analysis',
    'print_detailed_pitch_errors',
    'print_detailed_errors'
]
