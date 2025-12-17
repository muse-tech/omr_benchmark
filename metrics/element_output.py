from typing import Dict, Optional

COMBINED_METRICS_MAP = {
    "Text": 'combined_text',
    "Lyrics": 'combined_lyrics',
    "Tempo": 'combined_tempos',
}

INDIVIDUAL_METRICS_MAP = {
    "Text": ('individual_texts', 'total_texts'),
    "Lyrics": ('individual_lyrics', 'total_lyrics'),
    "Tempo": ('individual_tempos', 'total_tempos'),
}

STAFF_ONLY_ELEMENTS = ["Clef", "KeySig", "TimeSig", "Tempo"]

def format_position(position: Dict, element_type: str = None) -> str:
    staff_id = position.get('staff_id', None)
    measure_id = position.get('measure_id', None)
    staff_str = staff_id + 1 if staff_id is not None else '?'
    measure_str = measure_id + 1 if measure_id is not None else '?'
    
    if element_type in STAFF_ONLY_ELEMENTS:
        return f"Staff {staff_str}"
    if element_type == "Lyrics" and 'chord_id' in position:
        chord_id = position.get('chord_id')
        return f"Staff {staff_str}, Measure {measure_str}, Chord {chord_id}"
    return f"Staff {staff_str}, Measure {measure_str}"

def print_element_metrics(metrics: Dict, element_type: str, show_errors: bool = True, error_limit: Optional[int] = 50) -> None:
    print("\n" + "="*80)
    print(f"{element_type.upper()}-LEVEL METRICS")
    print("="*80)
    
    combined_key = COMBINED_METRICS_MAP.get(element_type)
    if combined_key and combined_key in metrics:
        if element_type == "Text":
            print_text_metrics_combined(metrics, show_errors, error_limit)
        elif element_type == "Lyrics":
            print_lyrics_metrics_combined(metrics, show_errors, error_limit)
        elif element_type == "Tempo":
            print_tempo_metrics_combined(metrics, show_errors, error_limit)
        return

    summary = metrics['summary']
    print(f"\nSUMMARY:")
    print(f"  GT {element_type}s: {summary['gt_elements_count']}")
    print(f"  Pred {element_type}s: {summary['pred_elements_count']}")
    print(f"  Matched {element_type}s: {summary['matched_elements_count']}")
    print(f"  Missing {element_type}s: {summary['missing_elements_count']}")
    print(f"  Extra {element_type}s: {summary['extra_elements_count']}")
    attr_metrics = metrics['value']
    accuracy = attr_metrics['accuracy']
    correct = attr_metrics['correct']
    total = attr_metrics['total']
    errors_count = len(attr_metrics['errors'])
    print(f"\nVALUE ACCURACY:")
    print(f"  Accuracy: {accuracy:.4f} ({correct}/{total})")
    print(f"  Errors: {errors_count}")

    if show_errors:
        errors = attr_metrics['errors']
        if errors:
            print(f"\nDETAILED ERRORS:")
            errors_to_show = errors if error_limit is None else errors[:error_limit]
            for i, error in enumerate(errors_to_show):
                position = error['position']
                details = error['details']
                pos_str = format_position(position, element_type)
                
                if element_type == "Staff":
                    gt_val = details.get('gt_staff_id', 'None')
                    pred_val = details.get('pred_staff_id', 'None')
                    print(f"  [{i+1}] {pos_str}: True=Staff {gt_val} → Pred=Staff {pred_val}")
                else:
                    gt_val = details.get('gt_value') or 'None'
                    pred_val = details.get('pred_value') or 'None'
                    print(f"  [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
            if error_limit is not None and len(errors) > error_limit:
                print(f"  ... and {len(errors) - error_limit} more errors")

def _print_combined_summary(summary: Dict, element_name: str) -> None:
    print(f"\nSUMMARY:")
    print(f"  GT {element_name}: {summary['gt_elements_count']}")
    print(f"  Pred {element_name}: {summary['pred_elements_count']}")
    print(f"  Missing {element_name}: {summary['missing_elements_count']}")
    print(f"  Extra {element_name}: {summary['extra_elements_count']}")

def _print_combined_metrics_header(combined: Dict, element_name: str) -> None:
    print(f"\nCOMBINED {element_name.upper()} METRICS:")
    print(f"  {element_name.capitalize()} Accuracy: {combined['accuracy']:.4f}")
    print(f"  Edit Distance: {combined['edit_distance']}")
    print(f"  Normalized Distance: {combined['normalized_distance']:.4f}")
    print(f"  Exact Match: {'Yes' if combined['exact_match'] else 'No'}")

def _print_combined_values(gt_combined: str, pred_combined: str, element_name: str, 
                          max_display_len: int = 200) -> None:
    print(f"\nCOMBINED {element_name.upper()}:")
    for label, value in [("GT", gt_combined), ("Pred", pred_combined)]:
        if len(value) == 0:
            print(f"  {label}: (empty)")
        elif len(value) > max_display_len:
            print(f"  {label} (first {max_display_len} chars): {value[:max_display_len]}...")
            print(f"  {label} (full length): {len(value)} characters")
        else:
            print(f"  {label}: {value}")

def _print_individual_items(items_with_errors: list, item_name: str, error_limit: Optional[int],
                           get_display_func) -> None:
    if not items_with_errors:
        return
    print(f"\nINDIVIDUAL {item_name.upper()}:")
    items_to_show = items_with_errors if error_limit is None else items_with_errors[:error_limit]
    for i, item_metric in enumerate(items_to_show):
        gt_display, pred_display, edit_dist, norm_dist, pos_info = get_display_func(item_metric, i)
        print(f"  [{i+1}] GT: {gt_display} → Pred: {pred_display} [ED={edit_dist}, ND={norm_dist:.4f}]{pos_info}")
    if error_limit is not None and len(items_with_errors) > error_limit:
        print(f"  ... and {len(items_with_errors) - error_limit} more errors")

def print_combined_metrics(metrics: Dict, element_type: str, show_errors: bool = True, error_limit: Optional[int] = 50) -> None:
    combined_key = COMBINED_METRICS_MAP.get(element_type)
    if not combined_key or combined_key not in metrics:
        return
    
    summary = metrics['summary']
    combined = metrics[combined_key]
    
    element_name_plural = element_type + "s" if element_type != "Tempo" else "Tempos"
    element_name_singular = element_type
    
    _print_combined_summary(summary, element_name_plural)
    _print_combined_metrics_header(combined, element_name_singular)
    
    if 'gt_combined' in combined and 'pred_combined' in combined:
        _print_combined_values(combined['gt_combined'], combined['pred_combined'], element_name_singular)
    
    if 'edit_distance' in metrics:
        ed = metrics['edit_distance']
        print(f"\nEDIT DISTANCE METRICS:")
        print(f"  Total Edit Distance: {ed.get('total_edit_distance', 0)}")
        print(f"  Total Max Length: {ed.get('total_max_length', 0)}")
        print(f"  Average Edit Distance: {ed.get('average_edit_distance', 0):.2f}")
        print(f"  Average Normalized Distance: {ed.get('average_normalized_distance', 0):.4f}")
        accuracy = ed.get('tempo_accuracy', ed.get('average_accuracy', 0))
        print(f"  Tempo Accuracy: {accuracy:.4f}")
        print(f"  Exact Match Rate: {ed.get('exact_match_rate', 0):.4f} ({ed.get('exact_matches', 0)}/{ed.get('total_matches', 0)})")
    
    individual_info = INDIVIDUAL_METRICS_MAP.get(element_type)
    if individual_info:
        individual_key, total_key = individual_info
        if individual_key in metrics:
            individual = metrics[individual_key]
        if individual.get(total_key, 0) > 0:
            print(f"\nINDIVIDUAL {element_name_plural.upper()} METRICS:")
            print(f"  Total Individual {element_name_plural}: {individual[total_key]}")
            print(f"  Average Edit Distance: {individual['average_edit_distance']:.2f}")
            print(f"  Average Normalized Distance: {individual['average_normalized_distance']:.4f}")
            print(f"  Average Accuracy: {individual['average_accuracy']:.4f}")
            print(f"  Exact Match Rate: {individual['exact_match_rate']:.4f}")
            
            if show_errors and individual.get('metrics'):
                items_with_errors = [item for item in individual['metrics'] if not item['exact_match']]
                
                def get_display_func(item_metric, _):
                    max_display = 50
                    gt_key = f'gt_{element_type.lower()}'
                    pred_key = f'pred_{element_type.lower()}'
                    gt_value = item_metric[gt_key]
                    pred_value = item_metric[pred_key]
                    gt_display = gt_value[:max_display] + "..." if len(gt_value) > max_display else gt_value
                    pred_display = pred_value[:max_display] + "..." if len(pred_value) > max_display else pred_value
                    
                    pos_info = ""
                    if element_type == "Lyrics":
                        chord_id = item_metric.get('chord_id')
                        staff_id = item_metric.get('staff_id')
                        measure_id = item_metric.get('measure_id')
                        if staff_id is not None and measure_id is not None:
                            pos_info = f" (Staff {staff_id}, Measure {measure_id}"
                            if chord_id is not None:
                                pos_info += f", Chord {chord_id}"
                            pos_info += ")"
                    
                    return gt_display, pred_display, item_metric['levenshtein_distance'], \
                           item_metric['normalized_distance'], pos_info
                
                _print_individual_items(items_with_errors, element_name_plural, error_limit, get_display_func)
    

def print_text_metrics_combined(metrics: Dict, show_errors: bool = True, error_limit: Optional[int] = 50) -> None:
    print_combined_metrics(metrics, "Text", show_errors, error_limit)

def print_lyrics_metrics_combined(metrics: Dict, show_errors: bool = True, error_limit: Optional[int] = 50) -> None:
    print_combined_metrics(metrics, "Lyrics", show_errors, error_limit)

def print_tempo_metrics_combined(metrics: Dict, show_errors: bool = True, error_limit: Optional[int] = 50) -> None:
    print_combined_metrics(metrics, "Tempo", show_errors, error_limit)
