from typing import Dict, Optional

def format_position(position: Dict, element_type: str = None) -> str:
    staff_id = position.get('staff_id', None)
    measure_id = position.get('measure_id', None)
    staff_str = staff_id + 1 if staff_id is not None else '?'
    measure_str = measure_id + 1 if measure_id is not None else '?'
    if element_type in ["Clef", "KeySig", "TimeSig", "Tempo"]:
        return f"Staff {staff_str}"
    if element_type == "Lyrics" and 'chord_id' in position:
        chord_id = position.get('chord_id')
        return f"Staff {staff_str}, Measure {measure_str}, Chord {chord_id}"
    return f"Staff {staff_str}, Measure {measure_str}"

def print_element_metrics(metrics: Dict, element_type: str, show_errors: bool = True, error_limit: Optional[int] = 50) -> None:
    print("\n" + "="*80)
    print(f"{element_type.upper()}-LEVEL METRICS")
    print("="*80)
    if element_type == "Text" and 'combined_text' in metrics:
        print_text_metrics_combined(metrics, show_errors, error_limit)
        return
    elif element_type == "Lyrics" and 'combined_lyrics' in metrics:
        print_lyrics_metrics_combined(metrics, show_errors, error_limit)
        return
    elif element_type == "Tempo" and 'combined_tempos' in metrics:
        print_tempo_metrics_combined(metrics, show_errors, error_limit)
        return
    if element_type == "Rest":
        attr_name = 'duration'
    elif element_type == "Spanner":
        attr_name = 'type'
    elif element_type == "Fermata":
        attr_name = 'subtype'
    elif element_type in ["Tuplet", "Clef", "KeySig", "TimeSig", "Tempo", "Dynamic", "Text", "Lyrics", "Instrument"]:
        attr_name = 'value'
    elif element_type == "Staff":
        attr_name = 'presence'
    else:
        raise ValueError(f"Unsupported element type: {element_type}")

    summary = metrics['summary']
    print(f"\nSUMMARY:")
    print(f"  GT {element_type}s: {summary['gt_elements_count']}")
    print(f"  Pred {element_type}s: {summary['pred_elements_count']}")
    print(f"  Matched {element_type}s: {summary['matched_elements_count']}")
    print(f"  Missing {element_type}s: {summary['missing_elements_count']}")
    print(f"  Extra {element_type}s: {summary['extra_elements_count']}")
    if element_type not in ["Clef", "KeySig", "TimeSig", "Tempo"] and 'gt_measures_count' in summary:
        print(f"\nMEASURE STATISTICS:")
        print(f"  GT Measures: {summary['gt_measures_count']}")
        print(f"  Pred Measures: {summary['pred_measures_count']}")
        print(f"  Matched Measures: {summary['matched_measures_count']}")
        print(f"  Missing Measures: {summary['missing_measures_count']}")
        print(f"  Extra Measures: {summary['extra_measures_count']}")
        if summary.get('missing_measures_count', 0) > 0 and summary.get('missing_measure_details'):
            print(f"\n  Missing Measure Details ({len(summary['missing_measure_details'])}):")
            for detail in summary['missing_measure_details'][:10]:
                print(f"    Staff {detail['staff_id'] + 1}, Measure {detail['measure_id'] + 1}: {detail['elements_count']} elements")
            if len(summary['missing_measure_details']) > 10:
                print(f"    ... and {len(summary['missing_measure_details']) - 10} more")
        if summary.get('extra_measures_count', 0) > 0 and summary.get('extra_measure_details'):
            print(f"\n  Extra Measure Details ({len(summary['extra_measure_details'])}):")
            for detail in summary['extra_measure_details'][:10]:
                print(f"    Staff {detail['staff_id'] + 1}, Measure {detail['measure_id'] + 1}: {detail['elements_count']} elements")
            if len(summary['extra_measure_details']) > 10:
                print(f"    ... and {len(summary['extra_measure_details']) - 10} more")
    attr_metrics = metrics[attr_name]
    accuracy = attr_metrics['accuracy']
    correct = attr_metrics['correct']
    total = attr_metrics['total']
    errors_count = len(attr_metrics['errors'])
    print(f"\n{attr_name.upper()} ACCURACY:")
    print(f"  Accuracy: {accuracy:.4f} ({correct}/{total})")
    print(f"  Errors: {errors_count}")
    if element_type == "Text" and 'edit_distance' in metrics:
        edit_metrics = metrics['edit_distance']
        if edit_metrics.get('total_matches', 0) > 0:
            print(f"\nEDIT DISTANCE METRICS:")
            print(f"  Average Edit Distance: {edit_metrics.get('average_edit_distance', 0):.2f}")
            print(f"  Average Normalized Distance: {edit_metrics.get('average_normalized_distance', 0):.4f}")
            print(f"  Text Accuracy (1 - normalized distance): {edit_metrics.get('text_accuracy', 0):.4f}")
            print(f"  Exact Match Rate: {edit_metrics.get('exact_match_rate', 0):.4f} ({edit_metrics.get('exact_matches', 0)}/{edit_metrics.get('total_matches', 0)})")
            print(f"  Total Edit Distance: {edit_metrics.get('total_edit_distance', 0)}")
            print(f"  Total Max Length: {edit_metrics.get('total_max_length', 0)}")

    if show_errors:
        errors = attr_metrics['errors']
        if errors:
            print(f"\nDETAILED ERRORS:")
            errors_to_show = errors if error_limit is None else errors[:error_limit]
            for i, error in enumerate(errors_to_show):
                position = error['position']
                details = error['details']
                pos_str = format_position(position, element_type)
                if element_type == "Rest":
                    gt_val = details['gt_duration'] if details['gt_duration'] else 'None'
                    pred_val = details['pred_duration'] if details['pred_duration'] else 'None'
                    print(f"  [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
                elif element_type == "Spanner":
                    gt_val = details['gt_type'] if details['gt_type'] else 'None'
                    pred_val = details['pred_type'] if details['pred_type'] else 'None'
                    print(f"  [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
                elif element_type == "Fermata":
                    gt_val = details['gt_subtype'] if details['gt_subtype'] else 'None'
                    pred_val = details['pred_subtype'] if details['pred_subtype'] else 'None'
                    print(f"  [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
                elif element_type == "Text":
                    gt_val = details.get('gt_value', 'None') if details.get('gt_value') else 'None'
                    pred_val = details.get('pred_value', 'None') if details.get('pred_value') else 'None'
                    edit_dist = details.get('edit_distance', 0)
                    norm_dist = details.get('normalized_distance', 0)
                    exact_match = details.get('exact_match', False)
                    match_str = "✓" if exact_match else f"ED={edit_dist}, ND={norm_dist:.4f}"
                    print(f"  [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val} [{match_str}]")
                elif element_type in ["Tuplet", "Clef", "KeySig", "TimeSig", "Tempo", "Dynamic", "Lyrics", "Instrument"]:
                    gt_val = details.get('gt_value', 'None') if details.get('gt_value') else 'None'
                    pred_val = details.get('pred_value', 'None') if details.get('pred_value') else 'None'
                    print(f"  [{i+1}] {pos_str}: True={gt_val} → Pred={pred_val}")
                elif element_type == "Staff":
                    gt_val = details.get('gt_staff_id', 'None')
                    pred_val = details.get('pred_staff_id', 'None')
                    print(f"  [{i+1}] {pos_str}: True=Staff {gt_val} → Pred=Staff {pred_val}")
            if error_limit is not None and len(errors) > error_limit:
                print(f"  ... and {len(errors) - error_limit} more errors")

def print_text_metrics_combined(metrics: Dict, show_errors: bool = True, error_limit: Optional[int] = 50) -> None:
    summary = metrics['summary']
    combined_text = metrics['combined_text']
    edit_distance_metrics = metrics['edit_distance']
    individual_texts = metrics['individual_texts']
    print(f"\nSUMMARY:")
    print(f"  GT Texts: {summary['gt_elements_count']}")
    print(f"  Pred Texts: {summary['pred_elements_count']}")
    print(f"  Missing Texts: {summary['missing_elements_count']}")
    print(f"  Extra Texts: {summary['extra_elements_count']}")
    print(f"\nCOMBINED TEXT METRICS:")
    print(f"  Text Accuracy: {combined_text['accuracy']:.4f}")
    print(f"  Edit Distance: {combined_text['edit_distance']}")
    print(f"  Normalized Distance: {combined_text['normalized_distance']:.4f}")
    print(f"  Exact Match: {'Yes' if combined_text['exact_match'] else 'No'}")
    gt_combined = combined_text['gt_combined']
    pred_combined = combined_text['pred_combined']
    max_display_len = 200
    print(f"\nCOMBINED TEXT:")
    if len(gt_combined) > max_display_len:
        print(f"  GT (first {max_display_len} chars): {gt_combined[:max_display_len]}...")
        print(f"  GT (full length): {len(gt_combined)} characters")
    else:
        print(f"  GT: {gt_combined}")

    if len(pred_combined) > max_display_len:
        print(f"  Pred (first {max_display_len} chars): {pred_combined[:max_display_len]}...")
        print(f"  Pred (full length): {len(pred_combined)} characters")
    else:
        print(f"  Pred: {pred_combined}")

    if individual_texts['total_texts'] > 0:
        print(f"\nINDIVIDUAL TEXTS METRICS:")
        print(f"  Total Individual Texts: {individual_texts['total_texts']}")
        print(f"  Average Edit Distance: {individual_texts['average_edit_distance']:.2f}")
        print(f"  Average Normalized Distance: {individual_texts['average_normalized_distance']:.4f}")
        print(f"  Average Accuracy: {individual_texts['average_accuracy']:.4f}")
        print(f"  Exact Match Rate: {individual_texts['exact_match_rate']:.4f}")
        if show_errors and individual_texts['metrics']:
            texts_with_errors = [tm for tm in individual_texts['metrics'] if not tm['exact_match']]
            if texts_with_errors:
                print(f"\nINDIVIDUAL TEXTS:")
                texts_to_show = texts_with_errors if error_limit is None else texts_with_errors[:error_limit]
                for i, text_metric in enumerate(texts_to_show):
                    gt_text = text_metric['gt_text']
                    pred_text = text_metric['pred_text']
                    edit_dist = text_metric['levenshtein_distance']
                    norm_dist = text_metric['normalized_distance']
                    max_text_display = 50
                    gt_display = gt_text[:max_text_display] + "..." if len(gt_text) > max_text_display else gt_text
                    pred_display = pred_text[:max_text_display] + "..." if len(pred_text) > max_text_display else pred_text
                    print(f"  [{i+1}] GT: {gt_display} → Pred: {pred_display} [ED={edit_dist}, ND={norm_dist:.4f}]")
                if error_limit is not None and len(texts_with_errors) > error_limit:
                    print(f"  ... and {len(texts_with_errors) - error_limit} more errors")

def print_lyrics_metrics_combined(metrics: Dict, show_errors: bool = True, error_limit: Optional[int] = 50) -> None:
    summary = metrics['summary']
    combined_lyrics = metrics['combined_lyrics']
    edit_distance_metrics = metrics['edit_distance']
    individual_lyrics = metrics['individual_lyrics']
    print(f"\nSUMMARY:")
    print(f"  GT Lyrics: {summary['gt_elements_count']}")
    print(f"  Pred Lyrics: {summary['pred_elements_count']}")
    print(f"  Missing Lyrics: {summary['missing_elements_count']}")
    print(f"  Extra Lyrics: {summary['extra_elements_count']}")
    print(f"\nCOMBINED LYRICS METRICS:")
    print(f"  Lyrics Accuracy: {combined_lyrics['accuracy']:.4f}")
    print(f"  Edit Distance: {combined_lyrics['edit_distance']}")
    print(f"  Normalized Distance: {combined_lyrics['normalized_distance']:.4f}")
    print(f"  Exact Match: {'Yes' if combined_lyrics['exact_match'] else 'No'}")
    gt_combined = combined_lyrics['gt_combined']
    pred_combined = combined_lyrics['pred_combined']
    max_display_len = 200

    print(f"\nCOMBINED LYRICS:")
    if len(gt_combined) > max_display_len:
        print(f"  GT (first {max_display_len} chars): {gt_combined[:max_display_len]}...")
        print(f"  GT (full length): {len(gt_combined)} characters")
    else:
        print(f"  GT: {gt_combined}")

    if len(pred_combined) > max_display_len:
        print(f"  Pred (first {max_display_len} chars): {pred_combined[:max_display_len]}...")
        print(f"  Pred (full length): {len(pred_combined)} characters")
    else:
        print(f"  Pred: {pred_combined}")

    if individual_lyrics['total_lyrics'] > 0:
        print(f"\nINDIVIDUAL LYRICS METRICS:")
        print(f"  Total Individual Lyrics: {individual_lyrics['total_lyrics']}")
        print(f"  Average Edit Distance: {individual_lyrics['average_edit_distance']:.2f}")
        print(f"  Average Normalized Distance: {individual_lyrics['average_normalized_distance']:.4f}")
        print(f"  Average Accuracy: {individual_lyrics['average_accuracy']:.4f}")
        print(f"  Exact Match Rate: {individual_lyrics['exact_match_rate']:.4f}")
        if show_errors and individual_lyrics['metrics']:
            lyrics_with_errors = [lm for lm in individual_lyrics['metrics'] if not lm['exact_match']]
            if lyrics_with_errors:
                print(f"\nINDIVIDUAL LYRICS:")
                lyrics_to_show = lyrics_with_errors if error_limit is None else lyrics_with_errors[:error_limit]
                max_lyric_display = 50
                max_gt_len = 0
                max_pred_len = 0
                max_pos_len = 0
                processed_lyrics = []
                for lyric_metric in lyrics_to_show:
                    gt_lyric = lyric_metric['gt_lyric']
                    pred_lyric = lyric_metric['pred_lyric']
                    chord_id = lyric_metric.get('chord_id')
                    staff_id = lyric_metric.get('staff_id')
                    measure_id = lyric_metric.get('measure_id')
                    gt_display = gt_lyric[:max_lyric_display] + "..." if len(gt_lyric) > max_lyric_display else gt_lyric
                    pred_display = pred_lyric[:max_lyric_display] + "..." if len(pred_lyric) > max_lyric_display else pred_lyric
                    pos_info = ""
                    if staff_id is not None and measure_id is not None:
                        pos_info = f" (Staff {staff_id}, Measure {measure_id}"
                        if chord_id is not None:
                            pos_info += f", Chord {chord_id}"
                        pos_info += ")"
                    max_gt_len = max(max_gt_len, len(gt_display))
                    max_pred_len = max(max_pred_len, len(pred_display))
                    max_pos_len = max(max_pos_len, len(pos_info))
                    processed_lyrics.append({
                        'gt_display': gt_display,
                        'pred_display': pred_display,
                        'pos_info': pos_info,
                        'edit_dist': lyric_metric['levenshtein_distance'],
                        'norm_dist': lyric_metric['normalized_distance']
                    })
                for i, lyric_data in enumerate(processed_lyrics):
                    gt_display = lyric_data['gt_display']
                    pred_display = lyric_data['pred_display']
                    pos_info = lyric_data['pos_info']
                    edit_dist = lyric_data['edit_dist']
                    norm_dist = lyric_data['norm_dist']
                    gt_padded = gt_display.ljust(max_gt_len)
                    pred_padded = pred_display.ljust(max_pred_len)
                    pos_padded = pos_info.ljust(max_pos_len)
                    print(f"  [{i+1}] GT: {gt_padded} → Pred: {pred_padded} [ED={edit_dist}, ND={norm_dist:.4f}]{pos_padded}")
                if error_limit is not None and len(lyrics_with_errors) > error_limit:
                    print(f"  ... and {len(lyrics_with_errors) - error_limit} more errors")

def print_tempo_metrics_combined(metrics: Dict, show_errors: bool = True, error_limit: Optional[int] = 50) -> None:
    summary = metrics['summary']
    combined_tempos = metrics['combined_tempos']
    edit_distance_metrics = metrics['edit_distance']
    print(f"\nSUMMARY:")
    print(f"  GT Tempos: {summary['gt_elements_count']}")
    print(f"  Pred Tempos: {summary['pred_elements_count']}")
    print(f"  Missing Tempos: {summary['missing_elements_count']}")
    print(f"  Extra Tempos: {summary['extra_elements_count']}")
    print(f"\nCOMBINED TEMPO METRICS:")
    print(f"  Tempo Accuracy: {combined_tempos['accuracy']:.4f}")
    print(f"  Edit Distance: {combined_tempos['edit_distance']}")
    print(f"  Normalized Distance: {combined_tempos['normalized_distance']:.4f}")
    print(f"  Exact Match: {'Yes' if combined_tempos['exact_match'] else 'No'}")
    gt_combined = combined_tempos['gt_combined']
    pred_combined = combined_tempos['pred_combined']

    print(f"\nCOMBINED TEMPO VALUES:")
    if len(gt_combined) > 0:
        print(f"  GT: {gt_combined}")
    else:
        print(f"  GT: (empty)")

    if len(pred_combined) > 0:
        print(f"  Pred: {pred_combined}")
    else:
        print(f"  Pred: (empty)")

    print(f"\nEDIT DISTANCE METRICS:")
    print(f"  Total Edit Distance: {edit_distance_metrics.get('total_edit_distance', 0)}")
    print(f"  Total Max Length: {edit_distance_metrics.get('total_max_length', 0)}")
    print(f"  Average Edit Distance: {edit_distance_metrics.get('average_edit_distance', 0):.2f}")
    print(f"  Average Normalized Distance: {edit_distance_metrics.get('average_normalized_distance', 0):.4f}")
    print(f"  Tempo Accuracy (1 - normalized distance): {edit_distance_metrics.get('tempo_accuracy', 0):.4f}")
    print(f"  Exact Match Rate: {edit_distance_metrics.get('exact_match_rate', 0):.4f} ({edit_distance_metrics.get('exact_matches', 0)}/{edit_distance_metrics.get('total_matches', 0)})")

    if show_errors and not combined_tempos['exact_match']:
        print(f"\nDETAILED ERROR:")
        error_details = metrics['value']['errors'][0]['details'] if metrics['value']['errors'] else {}
        edit_dist = error_details.get('edit_distance', 0)
        norm_dist = error_details.get('normalized_distance', 0)
        max_len = error_details.get('max_length', 0)
        print(f"  GT: {gt_combined}")
        print(f"  Pred: {pred_combined}")
        print(f"  Edit Distance: {edit_dist}")
        print(f"  Normalized Distance: {norm_dist:.4f}")
        print(f"  Max Length: {max_len}")
