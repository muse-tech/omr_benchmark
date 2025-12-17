from core.score_tree import create_simplified_tree, Node
from typing import List, Dict, Tuple
import argparse
import time
from metrics.tree_edit_distance import (
    tree_edit_distance,
    convert_to_apted_node,
    count_nodes,
)
from metrics.sequence_metrics import (
    character_error_rate,
    symbol_error_rate,
    _calculate_sequence_metrics
)
from metrics.output import print_metrics
from metrics.chord_metrics import (
    calculate_chord_metrics,
    print_chord_metrics,
    get_measure_alignment_from_chords
)
from metrics.element_metrics import (
    calculate_element_metrics,
    print_element_metrics
)

def calculate_all_metrics(ground_truth_path, predicted_path,
                          ted_approximate=False, chord_use_alignment=True,
                          metric_groups=None):
    if metric_groups is None:
        metric_groups = ['all']
    if 'all' in metric_groups:
        metric_groups = ['tree', 'sequence', 'chord', 'musical_structure',
                        'score_structure', 'performance_instructions', 'texts', 'other_elements']
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
    measure_mapping = None
    if 'tree' in metric_groups:
        print("1. Tree Edit Distance...")
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

    if 'sequence' in metric_groups:
        print("2. Sequence metrics (CER, SER)...")
        cer_result, ser_result = _calculate_sequence_metrics(gt_tree, pred_tree)
        results['cer'] = cer_result
        results['ser'] = ser_result

    if 'chord' in metric_groups or 'musical_structure' in metric_groups:
        print("3. Chord-level metrics...")
        chord_metrics = calculate_chord_metrics(gt_tree, pred_tree, use_alignment=chord_use_alignment)
        results['chord_metrics'] = chord_metrics
        print("   Computing measure alignment from chords...")
        measure_mapping = get_measure_alignment_from_chords(gt_tree, pred_tree)

    if any(group in metric_groups for group in ['musical_structure', 'score_structure',
                                                 'performance_instructions', 'texts', 'other_elements']):
        print("4. Other element metrics...")
        results['element_metrics'] = {}
        element_groups = {}
        if 'other_elements' in metric_groups or 'musical_structure' in metric_groups:
            element_groups['Other Elements'] = ['Rest', 'Tuplet']
        if 'score_structure' in metric_groups:
            element_groups['Score Structure'] = ['Clef', 'KeySig', 'TimeSig', 'Tempo', 'Instrument', 'Staff']
        if 'performance_instructions' in metric_groups:
            element_groups['Performance Instructions'] = ['Dynamic', 'Spanner', 'Fermata']
        if 'texts' in metric_groups:
            element_groups['Texts'] = ['Text', 'Lyrics']
        if measure_mapping is None:
            print("   Computing measure alignment from chords...")
            measure_mapping = get_measure_alignment_from_chords(gt_tree, pred_tree)
        for group_name, element_types in element_groups.items():
            for element_type in element_types:
                element_metrics = calculate_element_metrics(gt_tree, pred_tree, element_type, measure_mapping=measure_mapping)
                results['element_metrics'][element_type.lower()] = element_metrics

    return results



if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Compute quality metrics for OMR results',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('ground_truth', help='Path to ground truth .mscz file')
    parser.add_argument('predicted', help='Path to predicted .mscz file')
    parser.add_argument('--ted-approximate', action='store_true',
                       help='Use approximate algorithm for large trees (much faster)')
    parser.add_argument('--detailed-errors', action='store_true',
                       help='Show detailed error analysis for note pitches')
    parser.add_argument('--no-chord-alignment', action='store_true',
                       help='Disable chord sequence alignment (use strict position matching)')
    parser.add_argument('-metric', '--metric', dest='metric',
                       choices=['all', 'tree', 'sequence', 'chord', 'musical_structure',
                               'score_structure', 'performance_instructions', 'texts', 'other_elements'],
                       default='all',
                       help='Metric group to calculate: all (default), tree, sequence, chord, '
                            'musical_structure, score_structure, performance_instructions, texts, other_elements')
    args = parser.parse_args()
    metric_groups = [args.metric] if args.metric != 'all' else ['all']
    results = calculate_all_metrics(
        args.ground_truth,
        args.predicted,
        ted_approximate=args.ted_approximate,
        chord_use_alignment=not args.no_chord_alignment,
        metric_groups=metric_groups
    )
    print_metrics(results, show_detailed_errors=args.detailed_errors)
