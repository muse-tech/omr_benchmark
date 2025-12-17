from typing import Dict
from metrics.chord_metrics import print_chord_metrics
from metrics.element_metrics import print_element_metrics

def _has_element_errors(metrics: Dict, element_type: str) -> bool:
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
        return False

    if element_type == "Text" and 'combined_text' in metrics:
        combined = metrics['combined_text']
        accuracy = combined.get('accuracy', 1.0)
        return accuracy < 1.0
    if element_type == "Lyrics" and 'combined_lyrics' in metrics:
        combined = metrics['combined_lyrics']
        accuracy = combined.get('accuracy', 1.0)
        return accuracy < 1.0
    if attr_name not in metrics:
        return False
    attr_metrics = metrics[attr_name]
    accuracy = attr_metrics.get('accuracy', 1.0)
    errors = attr_metrics.get('errors', [])
    return accuracy < 1.0 or len(errors) > 0

def _has_chord_errors(metrics: Dict) -> bool:
    attributes = ['pitch', 'duration', 'spanner', 'dot', 'articulation', 'arpeggio', 'accidental']
    for attr in attributes:
        if attr in metrics and isinstance(metrics[attr], dict):
            accuracy = metrics[attr].get('accuracy', 1.0)
            errors = metrics[attr].get('errors', [])
            if accuracy < 1.0 or len(errors) > 0:
                return True
    return False

def _print_tree_metrics(results: Dict) -> None:
    if 'tree_edit_distance' not in results:
        print("  (not computed)")
        return
    ted = results['tree_edit_distance']
    print(f"  TED: {ted['distance']} | Normalized Error: {ted['normalized_error']:.4f} | Accuracy: {ted['accuracy']:.4f}")

def _print_sequence_metrics(results: Dict) -> None:
    if 'cer' not in results or 'ser' not in results:
        print("  (not computed)")
        return
    cer = results['cer']
    ser = results['ser']
    print(f"  CER: {cer['cer']:.4f} (Accuracy: {cer['accuracy']:.4f}, Errors: {cer['errors']}/{cer['total_characters']})")
    print(f"  SER: {ser['ser']:.4f} (Accuracy: {ser['accuracy']:.4f}, Errors: {ser['errors']}/{ser['total_symbols']})")

def _print_chord_metrics_summary(metrics: Dict) -> None:
    summary = metrics['summary']
    if summary['gt_chords_count'] == 0 and summary['pred_chords_count'] == 0:
        return
    print(f"  Chords: GT={summary['gt_chords_count']}, Pred={summary['pred_chords_count']}, "
          f"Matched={summary['matched_chords_count']}, Missing={summary['missing_chords_count']}, "
          f"Extra={summary['extra_chords_count']}")
    attributes = ['pitch', 'duration', 'spanner', 'dot', 'articulation', 'arpeggio', 'accidental']
    accuracies = []
    for attr in attributes:
        if attr in metrics:
            acc = metrics[attr]['accuracy']
            accuracies.append(f"{attr}={acc:.3f}")
    if accuracies:
        print(f"Chord attributes accuracies: {' | '.join(accuracies)}")

def _print_element_metrics_summary(metrics: Dict, element_type: str) -> None:
    summary = metrics['summary']
    if summary['gt_elements_count'] == 0 and summary['pred_elements_count'] == 0:
        return
    if element_type == "Rest":
        attr_name = 'duration'
    elif element_type == "Spanner":
        attr_name = 'type'
    elif element_type == "Fermata":
        attr_name = 'subtype'
    elif element_type in ["Tuplet", "Clef", "KeySig", "TimeSig", "Tempo", "Dynamic", "Instrument"]:
        attr_name = 'value'
    elif element_type == "Staff":
        attr_name = 'presence'
    else:
        attr_name = 'value'

    if attr_name in metrics:
        attr_metrics = metrics[attr_name]
        accuracy = attr_metrics['accuracy']
        correct = attr_metrics['correct']
        total = attr_metrics['total']
        print(f"  {element_type}: Accuracy={accuracy:.3f} ({correct}/{total}) | "
              f"GT={summary['gt_elements_count']}, Pred={summary['pred_elements_count']}, "
              f"Missing={summary['missing_elements_count']}, Extra={summary['extra_elements_count']}")
    else:
        print(f"  {element_type}: GT={summary['gt_elements_count']}, Pred={summary['pred_elements_count']}")

def _print_text_metrics_summary(metrics: Dict, element_type: str) -> None:
    summary = metrics['summary']
    if summary['gt_elements_count'] == 0 and summary['pred_elements_count'] == 0:
        return
    if element_type == "Text" and 'combined_text' in metrics:
        combined = metrics['combined_text']
        print(f"  {element_type}: Accuracy={combined['accuracy']:.3f} | "
              f"Edit Distance={combined['edit_distance']} | "
              f"GT={summary['gt_elements_count']}, Pred={summary['pred_elements_count']}")
    elif element_type == "Lyrics" and 'combined_lyrics' in metrics:
        combined = metrics['combined_lyrics']
        print(f"  {element_type}: Accuracy={combined['accuracy']:.3f} | "
              f"Edit Distance={combined['edit_distance']} | "
              f"GT={summary['gt_elements_count']}, Pred={summary['pred_elements_count']}")
    elif element_type == "Tempo" and 'combined_tempos' in metrics:
        combined = metrics['combined_tempos']
        print(f"  {element_type}: Accuracy={combined['accuracy']:.3f} | "
              f"Edit Distance={combined['edit_distance']} | "
              f"GT={summary['gt_elements_count']}, Pred={summary['pred_elements_count']}")
    else:
        _print_element_metrics_summary(metrics, element_type)

def print_metrics(results: Dict, show_detailed_errors: bool = False) -> None:
    print("\n" + "="*80)
    print("OMR QUALITY ASSESSMENT RESULTS")
    print("="*80)

    if 'tree_edit_distance' in results:
        print("\n1. TREE-LEVEL METRICS")
        print("="*80)
        _print_tree_metrics(results)

    if 'cer' in results or 'ser' in results:
        print("\n2. SEQUENCE METRICS")
        print("="*80)
        _print_sequence_metrics(results)
    has_musical_structure = 'chord_metrics' in results or (
        'element_metrics' in results and
        any(key in results['element_metrics'] for key in ['rest', 'tuplet'])
    )

    if has_musical_structure:
        print("\n3. MUSICAL STRUCTURE METRICS")
        print("="*80)
        if 'chord_metrics' in results:
            _print_chord_metrics_summary(results['chord_metrics'])
        if 'element_metrics' in results:
            for element_type in ['Rest', 'Tuplet']:
                element_key = element_type.lower()
                if element_key in results['element_metrics']:
                    _print_element_metrics_summary(results['element_metrics'][element_key], element_type)
    has_score_structure = 'element_metrics' in results and any(
        key in results['element_metrics']
        for key in ['clef', 'keysig', 'timesig', 'tempo', 'instrument', 'staff']
    )

    if has_score_structure:
        print("\n4. SCORE STRUCTURE METRICS")
        print("="*80)
        for element_type in ['Clef', 'KeySig', 'TimeSig', 'Tempo', 'Instrument', 'Staff']:
            element_key = element_type.lower()
            if element_key in results['element_metrics']:
                if element_type == "Tempo":
                    _print_text_metrics_summary(results['element_metrics'][element_key], element_type)
                else:
                    _print_element_metrics_summary(results['element_metrics'][element_key], element_type)
    has_performance_instructions = 'element_metrics' in results and any(
        key in results['element_metrics']
        for key in ['dynamic', 'spanner', 'fermata']
    )

    if has_performance_instructions:
        print("\n5. PERFORMANCE INSTRUCTIONS METRICS")
        print("="*80)
        for element_type in ['Dynamic', 'Spanner', 'Fermata']:
            element_key = element_type.lower()
            if element_key in results['element_metrics']:
                _print_element_metrics_summary(results['element_metrics'][element_key], element_type)
    has_texts = 'element_metrics' in results and any(
        key in results['element_metrics']
        for key in ['text', 'lyrics']
    )

    if has_texts:
        print("\n6. TEXTS METRICS")
        print("="*80)
        for element_type in ['Text', 'Lyrics']:
            element_key = element_type.lower()
            if element_key in results['element_metrics']:
                _print_text_metrics_summary(results['element_metrics'][element_key], element_type)

    if show_detailed_errors:
        print("\n" + "="*80)
        print("DETAILED ERRORS")
        print("="*80)
        if 'chord_metrics' in results:
            if _has_chord_errors(results['chord_metrics']):
                print_chord_metrics(results['chord_metrics'], show_errors=True, error_limit=None)
        if 'element_metrics' in results:
            for element_type in ['Rest', 'Tuplet']:
                element_key = element_type.lower()
                if element_key in results['element_metrics']:
                    if _has_element_errors(results['element_metrics'][element_key], element_type):
                        print_element_metrics(
                            results['element_metrics'][element_key],
                            element_type,
                            show_errors=True,
                            error_limit=None
                        )
            for element_type in ['Clef', 'KeySig', 'TimeSig', 'Tempo', 'Instrument', 'Staff']:
                element_key = element_type.lower()
                if element_key in results['element_metrics']:
                    if _has_element_errors(results['element_metrics'][element_key], element_type):
                        print_element_metrics(
                            results['element_metrics'][element_key],
                            element_type,
                            show_errors=True,
                            error_limit=None
                        )
            for element_type in ['Dynamic', 'Spanner', 'Fermata']:
                element_key = element_type.lower()
                if element_key in results['element_metrics']:
                    if _has_element_errors(results['element_metrics'][element_key], element_type):
                        print_element_metrics(
                            results['element_metrics'][element_key],
                            element_type,
                            show_errors=True,
                            error_limit=None
                        )
            for element_type in ['Text', 'Lyrics']:
                element_key = element_type.lower()
                if element_key in results['element_metrics']:
                    if _has_element_errors(results['element_metrics'][element_key], element_type):
                        print_element_metrics(
                            results['element_metrics'][element_key],
                            element_type,
                            show_errors=True,
                            error_limit=None
                        )
    print("\n" + "="*80 + "\n")
