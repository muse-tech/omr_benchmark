from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from core.score_tree import Node

def extract_elements_with_attributes(node: Node,
                                    element_type: str,
                                    part_id: Optional[int] = None,
                                    staff_id: Optional[int] = None,
                                    measure_id: Optional[int] = None,
                                    chord_id: Optional[int] = None,
                                    inside_chord: bool = False,
                                    inside_note: bool = False) -> List[Dict]:
    elements = []
    current_part_id = part_id
    current_staff_id = staff_id
    current_measure_id = measure_id
    current_chord_id = chord_id
    current_inside_chord = inside_chord
    current_inside_note = inside_note

    if node.label == "Part":
        current_part_id = node.id
    elif node.label == "Staff":
        current_staff_id = node.id
    elif node.label == "Measure":
        current_measure_id = node.id
        current_inside_chord = False
        current_inside_note = False
    elif node.label == "Chord":
        current_chord_id = node.id
        current_inside_chord = True
        current_inside_note = False
    elif node.label == "Note":
        current_inside_note = True

    if node.label == element_type:
        if element_type in ["Spanner", "Fermata"]:
            if current_inside_chord or current_inside_note:
                pass
            else:
                element_info = {
                    'part_id': current_part_id,
                    'staff_id': current_staff_id,
                    'measure_id': current_measure_id,
                    'element_id': node.id,
                }
                if element_type == "Spanner":
                    element_info['type'] = node.value
                elif element_type == "Fermata":
                    element_info['subtype'] = node.value
                elements.append(element_info)
        else:
            element_info = {
                'part_id': current_part_id,
                'staff_id': current_staff_id,
                'measure_id': current_measure_id,
                'element_id': node.id,
            }
            if element_type == "Rest":
                element_info['duration'] = None
                for child in node.children:
                    if child.label == "Duration":
                        element_info['duration'] = child.value
                        break
            elif element_type == "Tuplet":
                element_info['value'] = node.value
            elif element_type == "Clef":
                element_info['value'] = node.value
            elif element_type == "KeySig":
                element_info['value'] = node.value
            elif element_type == "TimeSig":
                element_info['value'] = node.value
            elif element_type == "Tempo":
                element_info['value'] = node.value
            elif element_type == "Dynamic":
                element_info['value'] = node.value
            elif element_type == "Instrument":
                element_info['value'] = node.value
            elif element_type == "Staff":
                element_info['value'] = None
            elif element_type == "Text":
                element_info['value'] = node.value
            elif element_type == "Lyrics":
                element_info['value'] = node.value
                element_info['chord_id'] = current_chord_id
            elements.append(element_info)
    for child in node.children:
        elements.extend(extract_elements_with_attributes(
            child, element_type, current_part_id, current_staff_id, current_measure_id,
            current_chord_id, current_inside_chord, current_inside_note
        ))
    return elements

def extract_all_clefs(node: Node,
                      part_id: Optional[int] = None,
                      staff_id: Optional[int] = None,
                      measure_id: Optional[int] = None) -> List[Dict]:
    elements = []
    current_part_id = part_id
    current_staff_id = staff_id
    current_measure_id = measure_id
    if node.label == "Part":
        current_part_id = node.id
    elif node.label == "Staff":
        current_staff_id = node.id
    elif node.label == "Measure":
        current_measure_id = node.id
    if node.label == "Clef":
        element_info = {
            'part_id': current_part_id,
            'staff_id': current_staff_id,
            'measure_id': current_measure_id,
            'element_id': node.id,
            'value': node.value
        }
        elements.append(element_info)
    for child in node.children:
        elements.extend(extract_all_clefs(
            child, current_part_id, current_staff_id, current_measure_id
        ))
    return elements

def assign_element_positions_in_measures(elements: List[Dict], element_type: str = None) -> None:
    if element_type == "Lyrics":
        for element in elements:
            if 'chord_id' not in element:
                element['element_position_in_measure'] = None
        return
    if element_type == "Instrument":
        for element in elements:
            element['element_position_in_measure'] = None
        return

    elements_by_measure = defaultdict(list)
    for element in elements:
        key = (element['part_id'], element['staff_id'], element['measure_id'])
        elements_by_measure[key].append(element)
    for key, measure_elements in elements_by_measure.items():
        def sort_key(x):
            element_id = x.get('element_id')
            if element_id is not None:
                return (0, element_id)
            attrs = []
            if 'duration' in x:
                attrs.append(x.get('duration', ''))
            if 'type' in x:
                attrs.append(x.get('type', ''))
            if 'subtype' in x:
                attrs.append(x.get('subtype', ''))
            if 'value' in x:
                attrs.append(x.get('value', ''))
            return (1, tuple(attrs))
        measure_elements.sort(key=sort_key)
        for i, element in enumerate(measure_elements, start=1):
            element['element_position_in_measure'] = i

def measure_similarity_for_elements(gt_measure_id: int, pred_measure_id: int,
                                    staff_id: int,
                                    gt_by_measure: Dict, pred_by_measure: Dict) -> float:
    gt_key = (staff_id, gt_measure_id)
    pred_key = (staff_id, pred_measure_id)
    gt_elements = gt_by_measure.get(gt_key, [])
    pred_elements = pred_by_measure.get(pred_key, [])
    if not gt_elements and not pred_elements:
        return 1.0
    if not gt_elements or not pred_elements:
        return 0.0
    count_ratio = min(len(gt_elements), len(pred_elements)) / max(len(gt_elements), len(pred_elements), 1)
    return count_ratio

def align_measures_in_staff_for_elements(staff_id: int,
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
            similarity = measure_similarity_for_elements(
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
            similarity = measure_similarity_for_elements(
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

def element_similarity(element1: Dict, element2: Dict, element_type: str) -> float:
    if element1 is None or element2 is None:
        return 0.0
    if element_type == "Rest":
        gt_duration = element1.get('duration')
        pred_duration = element2.get('duration')
        return 1.0 if gt_duration == pred_duration else 0.0
    elif element_type == "Tuplet":
        gt_value = element1.get('value')
        pred_value = element2.get('value')
        return 1.0 if gt_value == pred_value else 0.0
    elif element_type == "Spanner":
        gt_type = element1.get('type')
        pred_type = element2.get('type')
        return 1.0 if gt_type == pred_type else 0.0
    elif element_type == "Fermata":
        gt_subtype = element1.get('subtype')
        pred_subtype = element2.get('subtype')
        return 1.0 if gt_subtype == pred_subtype else 0.0
    elif element_type == "Dynamic":
        gt_value = element1.get('value')
        pred_value = element2.get('value')
        return 1.0 if gt_value == pred_value else 0.0
    elif element_type in ["Clef", "KeySig", "TimeSig", "Tempo", "Instrument"]:
        gt_value = element1.get('value')
        pred_value = element2.get('value')
        return 1.0 if gt_value == pred_value else 0.0
    else:
        return 1.0 if element1 == element2 else 0.0

def align_elements_in_measure(gt_elements: List[Dict], pred_elements: List[Dict], element_type: str) -> List[Tuple[Optional[Dict], Optional[Dict]]]:
    n = len(gt_elements)
    m = len(pred_elements)
    if n == 0:
        return [(None, pred_element) for pred_element in pred_elements]
    if m == 0:
        return [(gt_element, None) for gt_element in gt_elements]
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
            gt_element = gt_elements[i-1]
            pred_element = pred_elements[j-1]
            similarity = element_similarity(gt_element, pred_element, element_type)
            match_value = similarity * match_score + (1 - similarity) * mismatch_penalty
            option_match = dp[i-1][j-1] + match_value
            option_gap_pred = dp[i-1][j] + gap_penalty
            option_gap_gt = dp[i][j-1] + gap_penalty
            dp[i][j] = max(option_match, option_gap_pred, option_gap_gt)
    alignment = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            gt_element = gt_elements[i-1]
            pred_element = pred_elements[j-1]
            similarity = element_similarity(gt_element, pred_element, element_type)
            match_value = similarity * match_score + (1 - similarity) * mismatch_penalty
            if dp[i][j] == dp[i-1][j-1] + match_value:
                alignment.append((gt_element, pred_element))
                i -= 1
                j -= 1
            elif dp[i][j] == dp[i-1][j] + gap_penalty:
                alignment.append((gt_element, None))
                i -= 1
            else:
                alignment.append((None, pred_element))
                j -= 1
        elif i > 0:
            alignment.append((gt_elements[i-1], None))
            i -= 1
        else:
            alignment.append((None, pred_elements[j-1]))
            j -= 1
    alignment.reverse()
    return alignment

def match_elements_by_staff(gt_elements: List[Dict], pred_elements: List[Dict], element_type: str) -> Tuple[List[Tuple[Optional[Dict], Optional[Dict]]], Dict]:
    gt_by_staff = defaultdict(list)
    pred_by_staff = defaultdict(list)
    for element in gt_elements:
        staff_id = element.get('staff_id')
        if staff_id is not None:
            gt_by_staff[staff_id].append(element)
    for element in pred_elements:
        staff_id = element.get('staff_id')
        if staff_id is not None:
            pred_by_staff[staff_id].append(element)
    for staff_id in gt_by_staff:
        gt_by_staff[staff_id].sort(key=lambda x: (
            x.get('measure_id') if x.get('measure_id') is not None else -1,
            x.get('element_id') if x.get('element_id') is not None else -1
        ))
    for staff_id in pred_by_staff:
        pred_by_staff[staff_id].sort(key=lambda x: (
            x.get('measure_id') if x.get('measure_id') is not None else -1,
            x.get('element_id') if x.get('element_id') is not None else -1
        ))
    all_staffs = set(gt_by_staff.keys()) | set(pred_by_staff.keys())
    matches = []
    for staff_id in sorted(all_staffs):
        gt_staff_elements = gt_by_staff.get(staff_id, [])
        pred_staff_elements = pred_by_staff.get(staff_id, [])
        max_len = max(len(gt_staff_elements), len(pred_staff_elements))
        for i in range(max_len):
            gt_element = gt_staff_elements[i] if i < len(gt_staff_elements) else None
            pred_element = pred_staff_elements[i] if i < len(pred_staff_elements) else None
            matches.append((gt_element, pred_element))
    return matches, {
        'gt_measures_count': 0,
        'pred_measures_count': 0,
        'matched_measures_count': 0,
        'missing_measures_count': 0,
        'extra_measures_count': 0,
        'missing_measure_details': [],
        'extra_measure_details': []
    }

def match_elements_by_position(gt_elements: List[Dict], pred_elements: List[Dict], element_type: str = None, use_alignment: bool = True, measure_mapping: Dict[Tuple[int, int], Optional[int]] = None) -> Tuple[List[Tuple[Optional[Dict], Optional[Dict]]], Dict]:
    if element_type == "Lyrics" or element_type == "Instrument":
        use_alignment = False
    if not use_alignment:
        gt_by_position = {}
        pred_by_position = {}
        for element in gt_elements:
            if element_type not in ["Instrument", "Staff"]:
                if element.get('staff_id') is None or element.get('measure_id') is None:
                    continue
            if element_type == "Lyrics" and 'chord_id' in element:
                key = (element['staff_id'], element['measure_id'], element.get('chord_id'))
            elif element_type == "Instrument":
                key = (element.get('part_id'),)
            elif element_type == "Staff":
                key = (element.get('staff_id'),)
            else:
                key = (element['staff_id'], element['measure_id'], element.get('element_position_in_measure'))
            if key not in gt_by_position:
                gt_by_position[key] = []
            gt_by_position[key].append(element)
        for element in pred_elements:
            if element_type not in ["Instrument", "Staff"]:
                if element.get('staff_id') is None or element.get('measure_id') is None:
                    continue
            if element_type == "Lyrics" and 'chord_id' in element:
                key = (element['staff_id'], element['measure_id'], element.get('chord_id'))
            elif element_type == "Instrument":
                key = (element.get('part_id'),)
            elif element_type == "Staff":
                key = (element.get('staff_id'),)
            else:
                key = (element['staff_id'], element['measure_id'], element.get('element_position_in_measure'))
            if key not in pred_by_position:
                pred_by_position[key] = []
            pred_by_position[key].append(element)
        all_positions = set(gt_by_position.keys()) | set(pred_by_position.keys())
        matches = []
        
        def sort_key(pos):
            return tuple(-1 if x is None else x for x in pos)
        for position in sorted(all_positions, key=sort_key):
            gt_elements_at_pos = gt_by_position.get(position, [])
            pred_elements_at_pos = pred_by_position.get(position, [])
            gt_element = gt_elements_at_pos[0] if gt_elements_at_pos else None
            pred_element = pred_elements_at_pos[0] if pred_elements_at_pos else None
            matches.append((gt_element, pred_element))
        return matches, {
            'gt_measures_count': 0,
            'pred_measures_count': 0,
            'matched_measures_count': 0,
            'missing_measures_count': 0,
            'extra_measures_count': 0,
            'missing_measure_details': [],
            'extra_measure_details': []
        }

    if element_type == "Staff":
        gt_by_staff = {}
        pred_by_staff = {}
        for element in gt_elements:
            staff_id = element.get('staff_id')
            if staff_id is not None:
                gt_by_staff[staff_id] = element
        for element in pred_elements:
            staff_id = element.get('staff_id')
            if staff_id is not None:
                pred_by_staff[staff_id] = element
        all_staffs = set(gt_by_staff.keys()) | set(pred_by_staff.keys())
        matches = []
        for staff_id in sorted(all_staffs):
            gt_staff = gt_by_staff.get(staff_id)
            pred_staff = pred_by_staff.get(staff_id)
            matches.append((gt_staff, pred_staff))
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
    for element in gt_elements:
        if element.get('staff_id') is None or element.get('measure_id') is None:
            continue
        key = (element['staff_id'], element['measure_id'])
        gt_by_measure[key].append(element)
    for element in pred_elements:
        if element.get('staff_id') is None or element.get('measure_id') is None:
            continue
        key = (element['staff_id'], element['measure_id'])
        pred_by_measure[key].append(element)
    gt_by_staff = defaultdict(list)
    pred_by_staff = defaultdict(list)
    for measure_key in gt_by_measure.keys():
        staff_id, measure_id = measure_key
        if staff_id is not None and measure_id is not None:
            gt_by_staff[staff_id].append(measure_id)
    for measure_key in pred_by_measure.keys():
        staff_id, measure_id = measure_key
        if staff_id is not None and measure_id is not None:
            pred_by_staff[staff_id].append(measure_id)
    
    def sort_measure_ids(measure_ids):
        valid_ids = [m for m in measure_ids if m is not None]
        return sorted(valid_ids)

    for staff_id in gt_by_staff:
        gt_by_staff[staff_id] = sort_measure_ids(set(gt_by_staff[staff_id]))
    for staff_id in pred_by_staff:
        pred_by_staff[staff_id] = sort_measure_ids(set(pred_by_staff[staff_id]))
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

    gt_elements_by_measure = {}
    pred_elements_by_measure = {}
    for key, elements in gt_by_measure.items():
        gt_elements_by_measure[key] = elements
    for key, elements in pred_by_measure.items():
        pred_elements_by_measure[key] = elements
    for staff_id in sorted(all_staffs):
        gt_measure_ids = gt_by_staff.get(staff_id, [])
        pred_measure_ids = pred_by_staff.get(staff_id, [])
        measure_stats['gt_measures_count'] += len(gt_measure_ids)
        measure_stats['pred_measures_count'] += len(pred_measure_ids)
        if measure_mapping is not None:
            measure_alignment = []
            for gt_measure_id in gt_measure_ids:
                mapped_pred_measure_id = measure_mapping.get((staff_id, gt_measure_id))
                measure_alignment.append((gt_measure_id, mapped_pred_measure_id))
            mapped_pred_measure_ids = {mapped for _, mapped in measure_alignment if mapped is not None}
            for pred_measure_id in pred_measure_ids:
                if pred_measure_id not in mapped_pred_measure_ids:
                    found = False
                    for gt_mid, pred_mid in measure_alignment:
                        if pred_mid == pred_measure_id:
                            found = True
                            break
                    if not found:
                        measure_alignment.append((None, pred_measure_id))
        else:
            measure_alignment = align_measures_in_staff_for_elements(
                staff_id,
                gt_measure_ids,
                pred_measure_ids,
                gt_elements_by_measure,
                pred_elements_by_measure
            )
        for gt_measure_id, pred_measure_id in measure_alignment:
            if gt_measure_id is not None and pred_measure_id is not None:
                measure_stats['matched_measures_count'] += 1
            elif gt_measure_id is not None and pred_measure_id is None:
                measure_stats['missing_measures_count'] += 1
                gt_measure_key = (staff_id, gt_measure_id)
                gt_measure_elements = gt_by_measure.get(gt_measure_key, [])
                measure_stats['missing_measure_details'].append({
                    'staff_id': staff_id,
                    'measure_id': gt_measure_id,
                    'elements_count': len(gt_measure_elements)
                })
            elif gt_measure_id is None and pred_measure_id is not None:
                measure_stats['extra_measures_count'] += 1
                pred_measure_key = (staff_id, pred_measure_id)
                pred_measure_elements = pred_by_measure.get(pred_measure_key, [])
                measure_stats['extra_measure_details'].append({
                    'staff_id': staff_id,
                    'measure_id': pred_measure_id,
                    'elements_count': len(pred_measure_elements)
                })

            if gt_measure_id is not None:
                gt_measure_key = (staff_id, gt_measure_id)
                gt_measure_elements = gt_by_measure.get(gt_measure_key, [])
            else:
                gt_measure_elements = []

            if pred_measure_id is not None:
                pred_measure_key = (staff_id, pred_measure_id)
                pred_measure_elements = pred_by_measure.get(pred_measure_key, [])
            else:
                pred_measure_elements = []
            
            def sort_key(x):
                element_id = x.get('element_id')
                if element_id is not None:
                    return element_id
                attrs = []
                if 'duration' in x:
                    attrs.append(x.get('duration', ''))
                if 'type' in x:
                    attrs.append(x.get('type', ''))
                if 'subtype' in x:
                    attrs.append(x.get('subtype', ''))
                if 'value' in x:
                    attrs.append(x.get('value', ''))
                return tuple(attrs)
            gt_measure_elements.sort(key=sort_key)
            pred_measure_elements.sort(key=sort_key)
            element_alignment = align_elements_in_measure(gt_measure_elements, pred_measure_elements, element_type)
            all_matches.extend(element_alignment)
    return all_matches, measure_stats
