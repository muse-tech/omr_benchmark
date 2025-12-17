from typing import Dict, List, Callable

from metrics.chord_metrics import print_chord_metrics
from metrics.element_metrics import print_element_metrics

COMBINED_METRICS_MAP = {
    "Text": 'combined_text',
    "Lyrics": 'combined_lyrics',
    "Tempo": 'combined_tempos',
}
CHORD_ATTRIBUTES = ['pitch', 'duration', 'spanner', 'dot', 'articulation', 'arpeggio', 'accidental']

ELEMENT_GROUPS = {
    'musical_structure': ['Rest', 'Tuplet'],
    'score_structure': ['Clef', 'KeySig', 'TimeSig', 'Tempo', 'Instrument', 'Staff'],
    'performance_instructions': ['Dynamic', 'Spanner', 'Fermata'],
    'texts': ['Text', 'Lyrics'],
}

def _has_element_errors(metrics: Dict, element_type: str) -> bool:
    combined_key = COMBINED_METRICS_MAP.get(element_type)
    if combined_key and combined_key in metrics:
        return metrics[combined_key].get('accuracy', 1.0) < 1.0
    
    if 'value' not in metrics:
        return False
    
    attr_metrics = metrics['value']
    return attr_metrics.get('accuracy', 1.0) < 1.0 or len(attr_metrics.get('errors', [])) > 0

def _has_chord_errors(metrics: Dict) -> bool:
    for attr in CHORD_ATTRIBUTES:
        if attr in metrics and isinstance(metrics[attr], dict):
            attr_metrics = metrics[attr]
            if attr_metrics.get('accuracy', 1.0) < 1.0 or len(attr_metrics.get('errors', [])) > 0:
                return True
    return False

def _has_element_group(results: Dict, element_types: List[str]) -> bool:
    if 'element_metrics' not in results:
        return False
    element_keys = [et.lower() for et in element_types]
    return any(key in results['element_metrics'] for key in element_keys)

def _format_metric_section(title: str, content_func: Callable) -> None:
    print(f"\n{title}")
    print("="*80)
    content_func()

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

def _print_chord_summary(metrics: Dict) -> None:
    summary = metrics['summary']
    if summary['gt_chords_count'] == 0 and summary['pred_chords_count'] == 0:
        return
    print(f"  Chords: GT={summary['gt_chords_count']}, Pred={summary['pred_chords_count']}, "
          f"Matched={summary['matched_chords_count']}, Missing={summary['missing_chords_count']}, "
          f"Extra={summary['extra_chords_count']}")
    accuracies = [f"{attr}={metrics[attr]['accuracy']:.3f}" 
                  for attr in CHORD_ATTRIBUTES if attr in metrics]
    if accuracies:
        print(f"Chord attributes accuracies: {' | '.join(accuracies)}")

def _print_element_summary(metrics: Dict, element_type: str) -> None:
    summary = metrics['summary']
    if summary['gt_elements_count'] == 0 and summary['pred_elements_count'] == 0:
        return
    
    combined_key = COMBINED_METRICS_MAP.get(element_type)
    if combined_key and combined_key in metrics:
        combined = metrics[combined_key]
        print(f"  {element_type}: Accuracy={combined['accuracy']:.3f} | "
              f"Edit Distance={combined['edit_distance']} | "
              f"GT={summary['gt_elements_count']}, Pred={summary['pred_elements_count']}")
        return
    
    if 'value' in metrics:
        attr_metrics = metrics['value']
        print(f"  {element_type}: Accuracy={attr_metrics['accuracy']:.3f} ({attr_metrics['correct']}/{attr_metrics['total']}) | "
              f"GT={summary['gt_elements_count']}, Pred={summary['pred_elements_count']}, "
              f"Missing={summary['missing_elements_count']}, Extra={summary['extra_elements_count']}")
    else:
        print(f"  {element_type}: GT={summary['gt_elements_count']}, Pred={summary['pred_elements_count']}")

def _print_element_group_summary(results: Dict, element_types: List[str]) -> None:
    if 'element_metrics' not in results:
        return
    for element_type in element_types:
        element_key = element_type.lower()
        if element_key in results['element_metrics']:
            _print_element_summary(results['element_metrics'][element_key], element_type)

def _print_element_group_errors(results: Dict, element_types: List[str]) -> None:
    if 'element_metrics' not in results:
        return
    for element_type in element_types:
        element_key = element_type.lower()
        if element_key in results['element_metrics']:
            metrics = results['element_metrics'][element_key]
            if _has_element_errors(metrics, element_type):
                print_element_metrics(metrics, element_type, show_errors=True, error_limit=None)

def print_metrics(results: Dict, show_detailed_errors: bool = False) -> None:
    print("\n" + "="*80)
    print("OMR QUALITY ASSESSMENT RESULTS")
    print("="*80)

    if 'tree_edit_distance' in results:
        _format_metric_section("1. TREE-LEVEL METRICS", lambda: _print_tree_metrics(results))

    if 'cer' in results or 'ser' in results:
        _format_metric_section("2. SEQUENCE METRICS", lambda: _print_sequence_metrics(results))
    
    has_musical_structure = ('chord_metrics' in results or 
                             _has_element_group(results, ELEMENT_GROUPS['musical_structure']))
    if has_musical_structure:
        _format_metric_section("3. MUSICAL STRUCTURE METRICS", lambda: (
            _print_chord_summary(results['chord_metrics']) if 'chord_metrics' in results else None,
            _print_element_group_summary(results, ELEMENT_GROUPS['musical_structure'])
        ))

    if _has_element_group(results, ELEMENT_GROUPS['score_structure']):
        _format_metric_section("4. SCORE STRUCTURE METRICS", 
                              lambda: _print_element_group_summary(results, ELEMENT_GROUPS['score_structure']))

    if _has_element_group(results, ELEMENT_GROUPS['performance_instructions']):
        _format_metric_section("5. PERFORMANCE INSTRUCTIONS METRICS",
                              lambda: _print_element_group_summary(results, ELEMENT_GROUPS['performance_instructions']))

    if _has_element_group(results, ELEMENT_GROUPS['texts']):
        _format_metric_section("6. TEXTS METRICS",
                              lambda: _print_element_group_summary(results, ELEMENT_GROUPS['texts']))

    if show_detailed_errors:
        print("\n" + "="*80)
        _format_metric_section("DETAILED ERRORS", lambda: _print_detailed_errors(results))
    
    print("\n" + "="*80 + "\n")

def _print_detailed_errors(results: Dict) -> None:
    if 'chord_metrics' in results and _has_chord_errors(results['chord_metrics']):
        print_chord_metrics(results['chord_metrics'], show_errors=True, error_limit=None)
    
    for element_types in ELEMENT_GROUPS.values():
        _print_element_group_errors(results, element_types)
