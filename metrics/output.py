from typing import Dict


def _print_tree_metrics(results: Dict) -> None:
    print("\nTREE-LEVEL METRICS:")
    print(f"  Tree Edit Distance (TED): {results['tree_edit_distance']['distance']}")
    print(f"  Normalized Error: {results['tree_edit_distance']['normalized_error']:.4f}")
    print(f"  Tree Accuracy: {results['tree_edit_distance']['accuracy']:.4f}")


def _print_sequence_metrics(results: Dict) -> None:
    print("\nSEQUENCE METRICS:")
    print(f"  CER (Character Error Rate): {results['cer']['cer']:.4f}")
    print(f"  CER Accuracy: {results['cer']['accuracy']:.4f}")
    print(f"  CER Errors: {results['cer']['errors']}/{results['cer']['total_characters']}")
    
    print(f"\n  SER (Symbol Error Rate): {results['ser']['ser']:.4f}")
    print(f"  SER Accuracy: {results['ser']['accuracy']:.4f}")
    print(f"  SER Errors: {results['ser']['errors']}/{results['ser']['total_symbols']}")
    print(f"  SER Matches: {results['ser']['matches']}")


def _print_note_level_metrics(results: Dict) -> None:
    print("\nNOTE-LEVEL METRICS:")
    note_level = results['note_level']
    print(f"  Precision: {note_level['precision']:.4f}")
    print(f"  Recall: {note_level['recall']:.4f}")
    print(f"  F1-Score: {note_level['f1']:.4f}")
    print(f"  True Positives: {note_level['true_positives']}")
    print(f"  False Positives: {note_level['false_positives']}")
    print(f"  False Negatives: {note_level['false_negatives']}")
    print(f"  Total Notes in GT: {note_level['total_gt_notes']}")
    print(f"  Total Notes in Prediction: {note_level['total_pred_notes']}")


def _print_pitch_and_duration_metrics(results: Dict) -> None:
    print("\nPITCH ACCURACY:")
    pitch_acc = results['pitch_accuracy']
    print(f"  Pitch Accuracy: {pitch_acc['accuracy']:.4f}")
    print(f"  Correct Pitches: {pitch_acc['correct_pitches']}/{pitch_acc['total_pitches']}")
    
    print("\nDURATION ACCURACY:")
    duration_acc = results['duration_accuracy']
    print(f"  Duration Accuracy: {duration_acc['accuracy']:.4f}")
    print(f"  Correct Durations: {duration_acc['correct_durations']}/{duration_acc['total_durations']}")


def _print_measure_and_staff_metrics(results: Dict) -> None:
    print("\nMEASURE-LEVEL METRICS:")
    measure_level = results['measure_level']
    print(f"  Measure Count Accuracy: {measure_level['measure_count_accuracy']:.4f}")
    print(f"  Measure Content Accuracy: {measure_level['measure_content_accuracy']:.4f}")
    print(f"  Measures in GT: {measure_level['gt_measure_count']}")
    print(f"  Measures in Prediction: {measure_level['pred_measure_count']}")
    
    print("\nSTAFF-LEVEL METRICS:")
    staff_level = results['staff_level']
    print(f"  Staff Count Accuracy: {staff_level['staff_count_accuracy']:.4f}")
    print(f"  Clef Accuracy: {staff_level['clef_accuracy']:.4f}")
    print(f"  Staffs in GT: {staff_level['gt_staff_count']}")
    print(f"  Staffs in Prediction: {staff_level['pred_staff_count']}")


def _print_prf1_metrics(category: str, metrics: Dict, category_name: str = None) -> None:
    if category_name:
        print(f"    {category_name}:")
    else:
        print(f"    {category.upper()}:")
    print(f"      Precision: {metrics['precision']:.4f}")
    print(f"      Recall: {metrics['recall']:.4f}")
    print(f"      F1: {metrics['f1']:.4f}")
    if 'true_positives' in metrics:
        print(f"      TP: {metrics['true_positives']}, "
              f"FP: {metrics['false_positives']}, "
              f"FN: {metrics['false_negatives']}")


def _print_element_categories(results: Dict) -> None:
    print("\nELEMENT CATEGORY METRICS:")
    elem_cats = results['element_categories']
    
    print("\n  1.1. Instruments and System Parameters:")
    category_names = {
        'instruments': 'INSTRUMENTS',
        'staffs': 'STAFFS',
        'clefs': 'CLEFS',
        'time_signatures': 'TIME SIGNATURES'
    }
    for category in ['instruments', 'staffs', 'clefs', 'time_signatures']:
        if category in elem_cats:
            _print_prf1_metrics(category, elem_cats[category], 
                              category_names.get(category, category.upper()))
    
    print("\n  1.2. Spanners:")
    if 'spanners' in elem_cats:
        _print_prf1_metrics('spanners', elem_cats['spanners'])
    
    print("\n  1.3. Articulations:")
    if 'articulations' in elem_cats:
        _print_prf1_metrics('articulations', elem_cats['articulations'])
    
    print("\n  1.4. Text Elements:")
    if 'text_elements_tree' in elem_cats:
        text_tree = elem_cats['text_elements_tree']
        if isinstance(text_tree, dict) and 'overall_accuracy' in text_tree:
            print(f"    TEXT ELEMENTS TREE (Levenshtein):")
            print(f"      Overall Levenshtein Distance: {text_tree['overall_levenshtein_distance']}")
            print(f"      Overall Normalized Distance: {text_tree['overall_normalized_distance']:.4f}")
            print(f"      Overall Accuracy: {text_tree['overall_accuracy']:.4f}")
            print(f"      Total Texts: {text_tree['total_texts']}")
            if 'texts' in text_tree:
                for key, metrics in text_tree['texts'].items():
                    print(f"      {key}: Distance={metrics['levenshtein_distance']}, "
                          f"Accuracy={metrics['accuracy']:.4f}")
                    print(f"        GT: {metrics['gt_text'][:50]}..." if len(metrics['gt_text']) > 50 else f"        GT: {metrics['gt_text']}")
                    print(f"        Pred: {metrics['pred_text'][:50]}..." if len(metrics['pred_text']) > 50 else f"        Pred: {metrics['pred_text']}")
        else:
            _print_prf1_metrics('text_elements_tree', text_tree)
    
    print("\n  1.5. Lyrics:")
    if 'lyrics' in elem_cats:
        _print_prf1_metrics('lyrics', elem_cats['lyrics'])
    
    print("\n  1.6. Tempo and Dynamics:")
    if 'dynamics' in elem_cats:
        print(f"    DYNAMICS:")
        print(f"      Precision: {elem_cats['dynamics']['precision']:.4f}")
        print(f"      Recall: {elem_cats['dynamics']['recall']:.4f}")
        print(f"      F1: {elem_cats['dynamics']['f1']:.4f}")
    
    if 'tempos' in elem_cats:
        print(f"    TEMPOS:")
        print(f"      Precision: {elem_cats['tempos']['precision']:.4f}")
        print(f"      Recall: {elem_cats['tempos']['recall']:.4f}")
        print(f"      F1: {elem_cats['tempos']['f1']:.4f}")
    
    if 'tempo_text' in elem_cats and elem_cats['tempo_text']:
        print(f"    TEMPO TEXT (Levenshtein):")
        for key, metrics in elem_cats['tempo_text'].items():
            print(f"      {key}: Distance={metrics['levenshtein_distance']}, "
                  f"Accuracy={metrics['accuracy']:.4f}")


def print_metrics(results: Dict, show_detailed_errors: bool = False) -> None:       
    from metrics.error_analysis import print_detailed_errors
    
    print("\n" + "="*80)
    print("OMR QUALITY ASSESSMENT RESULTS")
    print("="*80)
    
    _print_tree_metrics(results)
    _print_sequence_metrics(results)
    _print_note_level_metrics(results)
    _print_pitch_and_duration_metrics(results)
    _print_measure_and_staff_metrics(results)

    if show_detailed_errors:
        all_errors = {
            'pitch_errors': results.get('pitch_errors', []),
            'duration_errors': results.get('duration_errors', []),
            'rest_errors': results.get('rest_errors', []),
            'spanner_errors': results.get('spanner_errors', []),
            'articulation_errors': results.get('articulation_errors', []),
            'text_errors': results.get('text_errors', []),
            'lyrics_errors': results.get('lyrics_errors', [])
        }
        print_detailed_errors(all_errors, limit=100)

    _print_element_categories(results)
    
    print("\n" + "="*80 + "\n")
