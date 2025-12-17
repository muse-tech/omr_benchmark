from collections import defaultdict
from typing import List, Dict, Tuple, Set, Optional
from core.score_tree import Node
import re

def normalize_articulation(articulation: str) -> str:
    if not articulation:
        return articulation
    normalized = re.sub(r'\s*(Below|Above)\s*$', '', articulation, flags=re.IGNORECASE)
    return normalized.strip()

def extract_chords_with_attributes(node: Node,
                                   part_id: Optional[int] = None,
                                   staff_id: Optional[int] = None,
                                   measure_id: Optional[int] = None) -> List[Dict]:
    chords = []
    current_part_id = part_id
    current_staff_id = staff_id
    current_measure_id = measure_id

    if node.label == "Part":
        current_part_id = node.id
    elif node.label == "Staff":
        current_staff_id = node.id
    elif node.label == "Measure":
        current_measure_id = node.id

    if node.label == "Chord":
        chord_info = {
            'part_id': current_part_id,
            'staff_id': current_staff_id,
            'measure_id': current_measure_id,
            'chord_id': node.id,
            'pitches': [],
            'duration': None,
            'has_dot': False,
            'spanners': [],
            'articulations': [],
            'arpeggios': [],
            'accidentals': []
        }

        for child in node.children:
            if child.label == "Duration":
                chord_info['duration'] = child.value
            elif child.label == "Dot":
                chord_info['has_dot'] = True
            elif child.label == "Spanner":
                if child.value:
                    chord_info['spanners'].append(child.value)
            elif child.label == "Articulation":
                if child.value:
                    normalized_articulation = normalize_articulation(child.value)
                    if normalized_articulation:
                        chord_info['articulations'].append(normalized_articulation)
            elif child.label == "Arpeggio":
                if child.value:
                    chord_info['arpeggios'].append(child.value)
            elif child.label == "Note":
                if child.value:
                    chord_info['pitches'].append(child.value)
                for note_child in child.children:
                    if note_child.label == "Spanner" and note_child.value:
                        chord_info['spanners'].append(note_child.value)
                    elif note_child.label == "Accidental" and note_child.value:
                        chord_info['accidentals'].append(note_child.value)
        chord_info['pitches'] = sorted(chord_info['pitches'])
        chord_info['spanners'] = sorted(chord_info['spanners'])
        chord_info['articulations'] = sorted(chord_info['articulations'])
        chord_info['arpeggios'] = sorted(chord_info['arpeggios'])
        chord_info['accidentals'] = sorted(chord_info['accidentals'])
        chords.append(chord_info)

    for child in node.children:
        chords.extend(extract_chords_with_attributes(
            child, current_part_id, current_staff_id, current_measure_id
        ))
    return chords

def assign_chord_positions_in_measures(chords: List[Dict]) -> None:
    chords_by_measure = defaultdict(list)
    for chord in chords:
        key = (chord['part_id'], chord['staff_id'], chord['measure_id'])
        chords_by_measure[key].append(chord)
    for key, measure_chords in chords_by_measure.items():
        measure_chords.sort(key=lambda x: x['chord_id'])
        for i, chord in enumerate(measure_chords, start=1):
            chord['chord_position_in_measure'] = i

def chord_similarity(chord1: Dict, chord2: Dict) -> float:
    if chord1 is None or chord2 is None:
        return 0.0
    score = 0.0
    total_weight = 0.0
    gt_pitches = set(chord1.get('pitches', []))
    pred_pitches = set(chord2.get('pitches', []))
    if gt_pitches or pred_pitches:
        pitch_match = len(gt_pitches & pred_pitches) / max(len(gt_pitches | pred_pitches), 1)
        score += pitch_match * 0.4
        total_weight += 0.4

    gt_duration = chord1.get('duration')
    pred_duration = chord2.get('duration')
    if gt_duration is not None or pred_duration is not None:
        duration_match = 1.0 if gt_duration == pred_duration else 0.0
        score += duration_match * 0.3
        total_weight += 0.3

    gt_has_dot = chord1.get('has_dot', False)
    pred_has_dot = chord2.get('has_dot', False)
    dot_match = 1.0 if gt_has_dot == pred_has_dot else 0.0
    score += dot_match * 0.1
    total_weight += 0.1

    gt_spanners = set(chord1.get('spanners', []))
    pred_spanners = set(chord2.get('spanners', []))
    if gt_spanners or pred_spanners:
        spanner_match = len(gt_spanners & pred_spanners) / max(len(gt_spanners | pred_spanners), 1)
        score += spanner_match * 0.1
        total_weight += 0.1

    gt_articulations = set(chord1.get('articulations', []))
    pred_articulations = set(chord2.get('articulations', []))
    if gt_articulations or pred_articulations:
        articulation_match = len(gt_articulations & pred_articulations) / max(len(gt_articulations | pred_articulations), 1)
        score += articulation_match * 0.1
        total_weight += 0.1
    return score / total_weight if total_weight > 0 else 0.0

def measure_similarity(gt_measure_id: int, pred_measure_id: int,
                       staff_id: int,
                       gt_by_measure: Dict, pred_by_measure: Dict) -> float:
    gt_key = (staff_id, gt_measure_id)
    pred_key = (staff_id, pred_measure_id)
    gt_chords = gt_by_measure.get(gt_key, [])
    pred_chords = pred_by_measure.get(pred_key, [])
    if not gt_chords and not pred_chords:
        return 1.0
    if not gt_chords or not pred_chords:
        return 0.0

    gt_chords_sorted = sorted(gt_chords, key=lambda x: x['chord_id'])
    pred_chords_sorted = sorted(pred_chords, key=lambda x: x['chord_id'])
    count_ratio = min(len(gt_chords_sorted), len(pred_chords_sorted)) / max(len(gt_chords_sorted), len(pred_chords_sorted), 1)
    count_score = count_ratio * 0.3

    min_chords = min(len(gt_chords_sorted), len(pred_chords_sorted))
    if min_chords == 0:
        chord_score = 0.0
    else:
        alignment = align_chords_in_measure(gt_chords_sorted, pred_chords_sorted)
        total_similarity = 0.0
        matched_pairs = 0
        for gt_chord, pred_chord in alignment:
            if gt_chord is not None and pred_chord is not None:
                similarity = chord_similarity(gt_chord, pred_chord)
                total_similarity += similarity
                matched_pairs += 1
        if matched_pairs > 0:
            chord_score = (total_similarity / matched_pairs) * 0.7
        else:
            chord_score = 0.0
    return count_score + chord_score

def align_measures_in_staff(staff_id: int,
                            gt_measure_ids: List[int],
                            pred_measure_ids: List[int],
                            gt_by_measure: Dict,
                            pred_by_measure: Dict) -> List[Tuple[Optional[int], Optional[int]]]:
    n = len(gt_measure_ids)
    m = len(pred_measure_ids)
    if n == 0:
        return [(None, pred_measure_id) for pred_measure_id in pred_measure_ids]
    if m == 0:
        return [(gt_measure_id, None) for gt_measure_id in gt_measure_ids]
    match_score = 1.0
    mismatch_penalty = -0.3
    gap_penalty = -0.2
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i-1][0] + gap_penalty
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j-1] + gap_penalty
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            gt_measure_id = gt_measure_ids[i-1]
            pred_measure_id = pred_measure_ids[j-1]
            similarity = measure_similarity(
                gt_measure_id, pred_measure_id, staff_id,
                gt_by_measure, pred_by_measure
            )
            match_value = similarity * match_score + (1 - similarity) * mismatch_penalty
            option_match = dp[i-1][j-1] + match_value
            option_gap_pred = dp[i-1][j] + gap_penalty
            option_gap_gt = dp[i][j-1] + gap_penalty
            dp[i][j] = max(option_match, option_gap_pred, option_gap_gt)
    alignment = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            gt_measure_id = gt_measure_ids[i-1]
            pred_measure_id = pred_measure_ids[j-1]
            similarity = measure_similarity(
                gt_measure_id, pred_measure_id, staff_id,
                gt_by_measure, pred_by_measure
            )
            match_value = similarity * match_score + (1 - similarity) * mismatch_penalty
            if dp[i][j] == dp[i-1][j-1] + match_value:
                alignment.append((gt_measure_id, pred_measure_id))
                i -= 1
                j -= 1
            elif dp[i][j] == dp[i-1][j] + gap_penalty:
                alignment.append((gt_measure_id, None))
                i -= 1
            else:
                alignment.append((None, pred_measure_id))
                j -= 1
        elif i > 0:
            alignment.append((gt_measure_ids[i-1], None))
            i -= 1
        else:
            alignment.append((None, pred_measure_ids[j-1]))
            j -= 1
    alignment.reverse()
    return alignment

def align_chords_in_measure(gt_chords: List[Dict], pred_chords: List[Dict]) -> List[Tuple[Optional[Dict], Optional[Dict]]]:
    n = len(gt_chords)
    m = len(pred_chords)
    if n == 0:
        return [(None, pred_chord) for pred_chord in pred_chords]
    if m == 0:
        return [(gt_chord, None) for gt_chord in gt_chords]

    match_score = 1.0
    mismatch_penalty = -0.5
    gap_penalty = -0.3
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        dp[i][0] = dp[i-1][0] + gap_penalty

    for j in range(1, m + 1):
        dp[0][j] = dp[0][j-1] + gap_penalty

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            gt_chord = gt_chords[i-1]
            pred_chord = pred_chords[j-1]
            similarity = chord_similarity(gt_chord, pred_chord)
            match_value = similarity * match_score + (1 - similarity) * mismatch_penalty
            option_match = dp[i-1][j-1] + match_value
            option_gap_pred = dp[i-1][j] + gap_penalty
            option_gap_gt = dp[i][j-1] + gap_penalty
            dp[i][j] = max(option_match, option_gap_pred, option_gap_gt)

    alignment = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            gt_chord = gt_chords[i-1]
            pred_chord = pred_chords[j-1]
            similarity = chord_similarity(gt_chord, pred_chord)
            match_value = similarity * match_score + (1 - similarity) * mismatch_penalty

            if dp[i][j] == dp[i-1][j-1] + match_value:
                alignment.append((gt_chord, pred_chord))
                i -= 1
                j -= 1
            elif dp[i][j] == dp[i-1][j] + gap_penalty:
                alignment.append((gt_chord, None))
                i -= 1
            else:
                alignment.append((None, pred_chord))
                j -= 1
        elif i > 0:
            alignment.append((gt_chords[i-1], None))
            i -= 1
        else:
            alignment.append((None, pred_chords[j-1]))
            j -= 1
    alignment.reverse()
    return alignment

def match_chords_by_position(gt_chords: List[Dict], pred_chords: List[Dict], use_alignment: bool = True) -> Tuple[List[Tuple[Optional[Dict], Optional[Dict]]], Dict]:
    if not use_alignment:
        gt_by_position = {}
        pred_by_position = {}
        for chord in gt_chords:
            key = (chord['staff_id'], chord['measure_id'], chord['chord_position_in_measure'])
            if key not in gt_by_position:
                gt_by_position[key] = []
            gt_by_position[key].append(chord)
        for chord in pred_chords:
            key = (chord['staff_id'], chord['measure_id'], chord['chord_position_in_measure'])
            if key not in pred_by_position:
                pred_by_position[key] = []
            pred_by_position[key].append(chord)
        all_positions = set(gt_by_position.keys()) | set(pred_by_position.keys())
        matches = []
        for position in sorted(all_positions):
            gt_chords_at_pos = gt_by_position.get(position, [])
            pred_chords_at_pos = pred_by_position.get(position, [])
            gt_chord = gt_chords_at_pos[0] if gt_chords_at_pos else None
            pred_chord = pred_chords_at_pos[0] if pred_chords_at_pos else None
            matches.append((gt_chord, pred_chord))
        return matches, {
            'gt_measures_count': 0,
            'pred_measures_count': 0,
            'matched_measures_count': 0,
            'missing_measures_count': 0,
            'extra_measures_count': 0,
            'missing_measure_details': [],
            'extra_measure_details': []
        }

    gt_by_measure = defaultdict(list)
    pred_by_measure = defaultdict(list)
    for chord in gt_chords:
        key = (chord['staff_id'], chord['measure_id'])
        gt_by_measure[key].append(chord)
    for chord in pred_chords:
        key = (chord['staff_id'], chord['measure_id'])
        pred_by_measure[key].append(chord)

    gt_by_staff = defaultdict(list)
    pred_by_staff = defaultdict(list)
    for measure_key in gt_by_measure.keys():
        staff_id, measure_id = measure_key
        gt_by_staff[staff_id].append(measure_id)
    for measure_key in pred_by_measure.keys():
        staff_id, measure_id = measure_key
        pred_by_staff[staff_id].append(measure_id)
    for staff_id in gt_by_staff:
        gt_by_staff[staff_id] = sorted(set(gt_by_staff[staff_id]))
    for staff_id in pred_by_staff:
        pred_by_staff[staff_id] = sorted(set(pred_by_staff[staff_id]))
    all_matches = []
    all_staffs = set(gt_by_staff.keys()) | set(pred_by_staff.keys())
    measure_stats = {
        'gt_measures_count': 0,
        'pred_measures_count': 0,
        'matched_measures_count': 0,
        'missing_measures_count': 0,
        'extra_measures_count': 0,
        'missing_measure_details': [],
        'extra_measure_details': []
    }

    for staff_id in sorted(all_staffs):
        gt_measure_ids = gt_by_staff.get(staff_id, [])
        pred_measure_ids = pred_by_staff.get(staff_id, [])
        measure_stats['gt_measures_count'] += len(gt_measure_ids)
        measure_stats['pred_measures_count'] += len(pred_measure_ids)
        measure_alignment = align_measures_in_staff(
            staff_id,
            gt_measure_ids,
            pred_measure_ids,
            gt_by_measure,
            pred_by_measure
        )
        for gt_measure_id, pred_measure_id in measure_alignment:
            if gt_measure_id is not None and pred_measure_id is not None:
                measure_stats['matched_measures_count'] += 1
            elif gt_measure_id is not None and pred_measure_id is None:
                measure_stats['missing_measures_count'] += 1
                gt_measure_key = (staff_id, gt_measure_id)
                gt_measure_chords = gt_by_measure.get(gt_measure_key, [])
                measure_stats['missing_measure_details'].append({
                    'staff_id': staff_id,
                    'measure_id': gt_measure_id,
                    'chords_count': len(gt_measure_chords)
                })
            elif gt_measure_id is None and pred_measure_id is not None:
                measure_stats['extra_measures_count'] += 1
                pred_measure_key = (staff_id, pred_measure_id)
                pred_measure_chords = pred_by_measure.get(pred_measure_key, [])
                measure_stats['extra_measure_details'].append({
                    'staff_id': staff_id,
                    'measure_id': pred_measure_id,
                    'chords_count': len(pred_measure_chords)
                })

            if gt_measure_id is not None:
                gt_measure_key = (staff_id, gt_measure_id)
                gt_measure_chords = gt_by_measure.get(gt_measure_key, [])
            else:
                gt_measure_chords = []

            if pred_measure_id is not None:
                pred_measure_key = (staff_id, pred_measure_id)
                pred_measure_chords = pred_by_measure.get(pred_measure_key, [])
            else:
                pred_measure_chords = []
            gt_measure_chords.sort(key=lambda x: x['chord_id'])
            pred_measure_chords.sort(key=lambda x: x['chord_id'])
            chord_alignment = align_chords_in_measure(gt_measure_chords, pred_measure_chords)
            all_matches.extend(chord_alignment)
    return all_matches, measure_stats

def compare_pitch(gt_chord: Dict, pred_chord: Dict) -> Tuple[bool, Dict]:
    gt_pitches = set(gt_chord.get('pitches', []))
    pred_pitches = set(pred_chord.get('pitches', []))
    match = gt_pitches == pred_pitches
    error_details = {
        'match': match,
        'gt_pitches': sorted(gt_pitches),
        'pred_pitches': sorted(pred_pitches),
        'missing_pitches': sorted(gt_pitches - pred_pitches),
        'extra_pitches': sorted(pred_pitches - gt_pitches)
    }
    return match, error_details

def compare_duration(gt_chord: Dict, pred_chord: Dict) -> Tuple[bool, Dict]:
    gt_duration = gt_chord.get('duration')
    pred_duration = pred_chord.get('duration')
    match = gt_duration == pred_duration
    error_details = {
        'match': match,
        'gt_duration': gt_duration,
        'pred_duration': pred_duration
    }
    return match, error_details

def compare_spanner(gt_chord: Dict, pred_chord: Dict) -> Tuple[bool, Dict]:
    gt_spanners = set(gt_chord.get('spanners', []))
    pred_spanners = set(pred_chord.get('spanners', []))
    match = gt_spanners == pred_spanners
    error_details = {
        'match': match,
        'gt_spanners': sorted(gt_spanners),
        'pred_spanners': sorted(pred_spanners),
        'missing_spanners': sorted(gt_spanners - pred_spanners),
        'extra_spanners': sorted(pred_spanners - gt_spanners)
    }
    return match, error_details

def compare_dot(gt_chord: Dict, pred_chord: Dict) -> Tuple[bool, Dict]:
    gt_has_dot = gt_chord.get('has_dot', False)
    pred_has_dot = pred_chord.get('has_dot', False)
    match = gt_has_dot == pred_has_dot
    error_details = {
        'match': match,
        'gt_has_dot': gt_has_dot,
        'pred_has_dot': pred_has_dot
    }
    return match, error_details

def compare_articulation(gt_chord: Dict, pred_chord: Dict) -> Tuple[bool, Dict]:
    gt_articulations = set(gt_chord.get('articulations', []))
    pred_articulations = set(pred_chord.get('articulations', []))
    match = gt_articulations == pred_articulations
    error_details = {
        'match': match,
        'gt_articulations': sorted(gt_articulations),
        'pred_articulations': sorted(pred_articulations),
        'missing_articulations': sorted(gt_articulations - pred_articulations),
        'extra_articulations': sorted(pred_articulations - gt_articulations)
    }
    return match, error_details

def compare_arpeggio(gt_chord: Dict, pred_chord: Dict) -> Tuple[bool, Dict]:
    gt_arpeggios = set(gt_chord.get('arpeggios', []))
    pred_arpeggios = set(pred_chord.get('arpeggios', []))
    match = gt_arpeggios == pred_arpeggios
    error_details = {
        'match': match,
        'gt_arpeggios': sorted(gt_arpeggios),
        'pred_arpeggios': sorted(pred_arpeggios),
        'missing_arpeggios': sorted(gt_arpeggios - pred_arpeggios),
        'extra_arpeggios': sorted(pred_arpeggios - gt_arpeggios)
    }
    return match, error_details

def compare_accidental(gt_chord: Dict, pred_chord: Dict) -> Tuple[bool, Dict]:
    gt_accidentals = set(gt_chord.get('accidentals', []))
    pred_accidentals = set(pred_chord.get('accidentals', []))
    match = gt_accidentals == pred_accidentals
    error_details = {
        'match': match,
        'gt_accidentals': sorted(gt_accidentals),
        'pred_accidentals': sorted(pred_accidentals),
        'missing_accidentals': sorted(gt_accidentals - pred_accidentals),
        'extra_accidentals': sorted(pred_accidentals - gt_accidentals)
    }
    return match, error_details

def extract_all_measures_from_tree(node: Node, staff_id: Optional[int] = None, part_id: Optional[int] = None) -> List[Tuple[int, int]]:
    measures = []
    current_staff_id = staff_id
    current_part_id = part_id

    if node.label == "Part":
        current_part_id = node.id
    elif node.label == "Staff":
        current_staff_id = node.id
    elif node.label == "Measure" and current_staff_id is not None:
        measures.append((current_staff_id, node.id))

    for child in node.children:
        measures.extend(extract_all_measures_from_tree(child, current_staff_id, current_part_id))
    return measures

def get_measure_alignment_from_chords(gt_tree: Node, pred_tree: Node) -> Dict[Tuple[int, int], Optional[int]]:
    gt_chords = extract_chords_with_attributes(gt_tree)
    pred_chords = extract_chords_with_attributes(pred_tree)
    gt_all_measures = extract_all_measures_from_tree(gt_tree)
    pred_all_measures = extract_all_measures_from_tree(pred_tree)

    gt_by_measure = defaultdict(list)
    pred_by_measure = defaultdict(list)
    for chord in gt_chords:
        key = (chord['staff_id'], chord['measure_id'])
        gt_by_measure[key].append(chord)
    for chord in pred_chords:
        key = (chord['staff_id'], chord['measure_id'])
        pred_by_measure[key].append(chord)

    gt_by_staff = defaultdict(list)
    pred_by_staff = defaultdict(list)
    for staff_id, measure_id in gt_all_measures:
        gt_by_staff[staff_id].append(measure_id)
    for staff_id, measure_id in pred_all_measures:
        pred_by_staff[staff_id].append(measure_id)
    for staff_id in gt_by_staff:
        gt_by_staff[staff_id] = sorted(set(gt_by_staff[staff_id]))
    for staff_id in pred_by_staff:
        pred_by_staff[staff_id] = sorted(set(pred_by_staff[staff_id]))

    measure_mapping = {}
    all_staffs = set(gt_by_staff.keys()) | set(pred_by_staff.keys())
    for staff_id in sorted(all_staffs):
        gt_measure_ids = gt_by_staff.get(staff_id, [])
        pred_measure_ids = pred_by_staff.get(staff_id, [])
        measure_alignment = align_measures_in_staff(
            staff_id,
            gt_measure_ids,
            pred_measure_ids,
            gt_by_measure,
            pred_by_measure
        )
        for gt_measure_id, pred_measure_id in measure_alignment:
            if gt_measure_id is not None:
                measure_mapping[(staff_id, gt_measure_id)] = pred_measure_id
    return measure_mapping

def calculate_chord_metrics(gt_tree: Node, pred_tree: Node, use_alignment: bool = True) -> Dict:
    gt_chords = extract_chords_with_attributes(gt_tree)
    pred_chords = extract_chords_with_attributes(pred_tree)
    assign_chord_positions_in_measures(gt_chords)
    assign_chord_positions_in_measures(pred_chords)
    chord_matches, measure_stats = match_chords_by_position(gt_chords, pred_chords, use_alignment=use_alignment)
    metrics = {
        'pitch': {'correct': 0, 'total': 0, 'errors': []},
        'duration': {'correct': 0, 'total': 0, 'errors': []},
        'spanner': {'correct': 0, 'total': 0, 'errors': []},
        'dot': {'correct': 0, 'total': 0, 'errors': []},
        'articulation': {'correct': 0, 'total': 0, 'errors': []},
        'arpeggio': {'correct': 0, 'total': 0, 'errors': []},
        'accidental': {'correct': 0, 'total': 0, 'errors': []}
    }
    for gt_chord, pred_chord in chord_matches:
        if gt_chord is not None:
            position = {
                'part_id': gt_chord['part_id'],
                'staff_id': gt_chord['staff_id'],
                'measure_id': gt_chord['measure_id'],
                'chord_position_in_measure': gt_chord['chord_position_in_measure']
            }
        elif pred_chord is not None:
            position = {
                'part_id': pred_chord['part_id'],
                'staff_id': pred_chord['staff_id'],
                'measure_id': pred_chord['measure_id'],
                'chord_position_in_measure': pred_chord['chord_position_in_measure']
            }
        else:
            continue
        if gt_chord is None:
            empty_gt_chord = {
                'pitches': [],
                'duration': None,
                'has_dot': False,
                'spanners': [],
                'articulations': [],
                'arpeggios': [],
                'accidentals': []
            }
            gt_chord = empty_gt_chord
        elif pred_chord is None:
            empty_pred_chord = {
                'pitches': [],
                'duration': None,
                'has_dot': False,
                'spanners': [],
                'articulations': [],
                'arpeggios': [],
                'accidentals': []
            }
            pred_chord = empty_pred_chord

        pitch_match, pitch_details = compare_pitch(gt_chord, pred_chord)
        metrics['pitch']['total'] += 1
        if pitch_match:
            metrics['pitch']['correct'] += 1
        else:
            metrics['pitch']['errors'].append({
                'position': position,
                'details': pitch_details
            })

        duration_match, duration_details = compare_duration(gt_chord, pred_chord)
        metrics['duration']['total'] += 1
        if duration_match:
            metrics['duration']['correct'] += 1
        else:
            metrics['duration']['errors'].append({
                'position': position,
                'details': duration_details
            })

        spanner_match, spanner_details = compare_spanner(gt_chord, pred_chord)
        metrics['spanner']['total'] += 1
        if spanner_match:
            metrics['spanner']['correct'] += 1
        else:
            metrics['spanner']['errors'].append({
                'position': position,
                'details': spanner_details
            })

        dot_match, dot_details = compare_dot(gt_chord, pred_chord)
        metrics['dot']['total'] += 1
        if dot_match:
            metrics['dot']['correct'] += 1
        else:
            metrics['dot']['errors'].append({
                'position': position,
                'details': dot_details
            })

        articulation_match, articulation_details = compare_articulation(gt_chord, pred_chord)
        metrics['articulation']['total'] += 1
        if articulation_match:
            metrics['articulation']['correct'] += 1
        else:
            metrics['articulation']['errors'].append({
                'position': position,
                'details': articulation_details
            })

        arpeggio_match, arpeggio_details = compare_arpeggio(gt_chord, pred_chord)
        metrics['arpeggio']['total'] += 1
        if arpeggio_match:
            metrics['arpeggio']['correct'] += 1
        else:
            metrics['arpeggio']['errors'].append({
                'position': position,
                'details': arpeggio_details
            })

        accidental_match, accidental_details = compare_accidental(gt_chord, pred_chord)
        metrics['accidental']['total'] += 1
        if accidental_match:
            metrics['accidental']['correct'] += 1
        else:
            metrics['accidental']['errors'].append({
                'position': position,
                'details': accidental_details
            })
    for attr in metrics:
        total = metrics[attr]['total']
        correct = metrics[attr]['correct']
        metrics[attr]['accuracy'] = correct / total if total > 0 else 0.0
    metrics['summary'] = {
        'gt_chords_count': len(gt_chords),
        'pred_chords_count': len(pred_chords),
        'matched_chords_count': len([m for m in chord_matches if m[0] is not None and m[1] is not None]),
        'missing_chords_count': len([m for m in chord_matches if m[0] is not None and m[1] is None]),
        'extra_chords_count': len([m for m in chord_matches if m[0] is None and m[1] is not None]),
        'gt_measures_count': measure_stats['gt_measures_count'],
        'pred_measures_count': measure_stats['pred_measures_count'],
        'matched_measures_count': measure_stats['matched_measures_count'],
        'missing_measures_count': measure_stats['missing_measures_count'],
        'extra_measures_count': measure_stats['extra_measures_count'],
        'missing_measure_details': measure_stats['missing_measure_details'],
        'extra_measure_details': measure_stats['extra_measure_details']
    }
    return metrics

def format_position(position: Dict) -> str:
    staff_id = position.get('staff_id', None)
    measure_id = position.get('measure_id', None)
    staff_str = staff_id + 1 if staff_id is not None else '?'
    measure_str = measure_id + 1 if measure_id is not None else '?'
    return f"Staff {staff_str}, Measure {measure_str}"

def print_chord_metrics(metrics: Dict, show_errors: bool = True, error_limit: Optional[int] = 50) -> None:
    print("\n" + "="*80)
    print("CHORD-LEVEL METRICS")
    print("="*80)

    summary = metrics['summary']
    print(f"\nSUMMARY:")
    print(f"  GT Chords: {summary['gt_chords_count']}")
    print(f"  Pred Chords: {summary['pred_chords_count']}")
    print(f"  Matched Chords: {summary['matched_chords_count']}")
    print(f"  Missing Chords: {summary['missing_chords_count']}")
    print(f"  Extra Chords: {summary['extra_chords_count']}")
    if 'gt_measures_count' in summary:
        print(f"\nMEASURE STATISTICS:")
        print(f"  GT Measures: {summary['gt_measures_count']}")
        print(f"  Pred Measures: {summary['pred_measures_count']}")
        print(f"  Matched Measures: {summary['matched_measures_count']}")
        print(f"  Missing Measures: {summary['missing_measures_count']}")
        print(f"  Extra Measures: {summary['extra_measures_count']}")
        if summary.get('missing_measures_count', 0) > 0 and summary.get('missing_measure_details'):
            print(f"\n  Missing Measure Details ({len(summary['missing_measure_details'])}):")
            for detail in summary['missing_measure_details'][:10]:
                print(f"    Staff {detail['staff_id'] + 1}, Measure {detail['measure_id'] + 1}: {detail['chords_count']} chords")
            if len(summary['missing_measure_details']) > 10:
                print(f"    ... and {len(summary['missing_measure_details']) - 10} more")
        if summary.get('extra_measures_count', 0) > 0 and summary.get('extra_measure_details'):
            print(f"\n  Extra Measure Details ({len(summary['extra_measure_details'])}):")
            for detail in summary['extra_measure_details'][:10]:
                print(f"    Staff {detail['staff_id'] + 1}, Measure {detail['measure_id'] + 1}: {detail['chords_count']} chords")
            if len(summary['extra_measure_details']) > 10:
                print(f"    ... and {len(summary['extra_measure_details']) - 10} more")

    print(f"\nATTRIBUTE ACCURACY:")
    attributes = ['pitch', 'duration', 'spanner', 'dot', 'articulation', 'arpeggio', 'accidental']
    for attr in attributes:
        attr_metrics = metrics[attr]
        accuracy = attr_metrics['accuracy']
        correct = attr_metrics['correct']
        total = attr_metrics['total']
        errors_count = len(attr_metrics['errors'])
        print(f"  {attr.upper()}:")
        print(f"    Accuracy: {accuracy:.4f} ({correct}/{total})")
        print(f"    Errors: {errors_count}")

    if show_errors:
        print(f"\nDETAILED ERRORS:")
        for attr in attributes:
            errors = metrics[attr]['errors']
            if not errors:
                continue
            print(f"\n  {attr.upper()} ERRORS ({len(errors)} total):")
            errors_to_show = errors if error_limit is None else errors[:error_limit]
            for i, error in enumerate(errors_to_show):
                position = error['position']
                details = error['details']
                pos_str = format_position(position)
                if attr == 'pitch':
                    gt_val = details['gt_pitches'] if details['gt_pitches'] else '[]'
                    pred_val = details['pred_pitches'] if details['pred_pitches'] else '[]'
                    print(f"    [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
                elif attr == 'duration':
                    gt_val = details['gt_duration'] if details['gt_duration'] else 'None'
                    pred_val = details['pred_duration'] if details['pred_duration'] else 'None'
                    print(f"    [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
                elif attr == 'spanner':
                    gt_val = details['gt_spanners'] if details['gt_spanners'] else '[]'
                    pred_val = details['pred_spanners'] if details['pred_spanners'] else '[]'
                    print(f"    [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
                elif attr == 'dot':
                    gt_val = details['gt_has_dot']
                    pred_val = details['pred_has_dot']
                    print(f"    [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
                elif attr == 'articulation':
                    gt_val = details['gt_articulations'] if details['gt_articulations'] else '[]'
                    pred_val = details['pred_articulations'] if details['pred_articulations'] else '[]'
                    print(f"    [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
                elif attr == 'accidental':
                    gt_val = details['gt_accidentals'] if details['gt_accidentals'] else '[]'
                    pred_val = details['pred_accidentals'] if details['pred_accidentals'] else '[]'
                    print(f"    [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
                elif attr == 'arpeggio':
                    gt_val = details['gt_arpeggios'] if details['gt_arpeggios'] else '[]'
                    pred_val = details['pred_arpeggios'] if details['pred_arpeggios'] else '[]'
                    print(f"    [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
            if error_limit is not None and len(errors) > error_limit:
                print(f"    ... and {len(errors) - error_limit} more errors")
