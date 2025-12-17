import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import csv
from calculate_metrics import calculate_all_metrics
from metrics.output import print_metrics
import io
from contextlib import redirect_stdout
import traceback

def find_matching_files(true_dir: str, predicted_dir: str) -> List[tuple]:
    true_path = Path(true_dir)
    pred_path = Path(predicted_dir)

    if not true_path.exists():
        raise FileNotFoundError(f"Folder {true_dir} not found")
    if not pred_path.exists():
        raise FileNotFoundError(f"Folder {predicted_dir} not found")
    true_files = {f.name: f for f in true_path.iterdir() if f.is_file() and f.suffix.lower() == '.mscz'}
    pred_files = {f.name: f for f in pred_path.iterdir() if f.is_file() and f.suffix.lower() == '.mscz'}
    matching_names = set(true_files.keys()) & set(pred_files.keys())

    if not matching_names:
        print(f"Warning: no .mscz files with matching names found")
        print(f"   Files in {true_dir}: {list(true_files.keys())[:5]}...")
        print(f"   Files in {predicted_dir}: {list(pred_files.keys())[:5]}...")
        return []

    pairs = [(true_files[name], pred_files[name], name) for name in matching_names]
    return sorted(pairs, key=lambda x: x[2])

def format_metric_name(key: str) -> str:
    display_key = key.replace('element_metrics.', '').replace('chord_metrics.', '')
    if display_key.endswith('.accuracy'):
        display_key = display_key[:-9] + ' accuracy'
    elif display_key.endswith('_accuracy'):
        display_key = display_key[:-9] + ' accuracy'
    display_key = display_key.replace('.', ' ').replace('_', ' ')
    words = display_key.split()
    formatted_words = []
    skip_words = {'value', 'subtype', 'type', 'presence', 'combined'}
    for word in words:
        if word.lower() in skip_words:
            continue
        if word.upper() in ['CER', 'SER', 'TED']:
            formatted_words.append(word.upper())
        else:
            formatted_words.append(word.capitalize())
    return ' '.join(formatted_words)

def flatten_metrics(results: Dict, prefix: str = "") -> Dict[str, float]:
    flattened = {}

    if 'tree_edit_distance' in results:
        ted = results['tree_edit_distance']
        flattened['tree_edit_distance.accuracy'] = ted.get('accuracy', 0)

    if 'cer' in results:
        cer = results['cer']
        flattened['cer.accuracy'] = cer.get('accuracy', 0)

    if 'ser' in results:
        ser = results['ser']
        flattened['ser.accuracy'] = ser.get('accuracy', 0)

    if 'chord_metrics' in results:
        chord_metrics = results['chord_metrics']
        attributes = ['pitch', 'duration', 'spanner', 'dot', 'articulation', 'arpeggio', 'accidental']
        for attr in attributes:
            if attr in chord_metrics and isinstance(chord_metrics[attr], dict):
                attr_acc = chord_metrics[attr].get('accuracy')
                if attr_acc is not None:
                    flattened[f'chord_metrics.{attr}.accuracy'] = attr_acc

    if 'element_metrics' in results:
        elem_metrics = results['element_metrics']
        for elem_type in ['rest', 'tuplet']:
            if elem_type in elem_metrics:
                metrics = elem_metrics[elem_type]
                summary = metrics.get('summary', {})
                if summary.get('gt_elements_count', 0) == 0 and summary.get('pred_elements_count', 0) == 0:
                    if elem_type == 'rest' and 'duration' in metrics:
                        flattened[f'element_metrics.{elem_type}.duration.accuracy'] = 1.0
                    elif elem_type == 'tuplet' and 'value' in metrics:
                        flattened[f'element_metrics.{elem_type}.value.accuracy'] = 1.0
                else:
                    if elem_type == 'rest' and 'duration' in metrics:
                        flattened[f'element_metrics.{elem_type}.duration.accuracy'] = metrics['duration'].get('accuracy', 0)
                    elif elem_type == 'tuplet' and 'value' in metrics:
                        flattened[f'element_metrics.{elem_type}.value.accuracy'] = metrics['value'].get('accuracy', 0)

        for elem_type in ['clef', 'keysig', 'timesig', 'tempo', 'instrument', 'staff']:
            if elem_type in elem_metrics:
                metrics = elem_metrics[elem_type]
                summary = metrics.get('summary', {})
                if summary.get('gt_elements_count', 0) == 0 and summary.get('pred_elements_count', 0) == 0:
                    if elem_type == 'staff' and 'presence' in metrics:
                        flattened[f'element_metrics.{elem_type}.presence.accuracy'] = 1.0
                    elif 'value' in metrics:
                        flattened[f'element_metrics.{elem_type}.value.accuracy'] = 1.0
                else:
                    if elem_type == 'staff' and 'presence' in metrics:
                        flattened[f'element_metrics.{elem_type}.presence.accuracy'] = metrics['presence'].get('accuracy', 0)
                    elif 'value' in metrics:
                        flattened[f'element_metrics.{elem_type}.value.accuracy'] = metrics['value'].get('accuracy', 0)

        if 'dynamic' in elem_metrics:
            metrics = elem_metrics['dynamic']
            summary = metrics.get('summary', {})
            if summary.get('gt_elements_count', 0) == 0 and summary.get('pred_elements_count', 0) == 0:
                flattened['element_metrics.dynamic.value.accuracy'] = 1.0
            elif 'value' in metrics:
                flattened['element_metrics.dynamic.value.accuracy'] = metrics['value'].get('accuracy', 0)

        if 'spanner' in elem_metrics:
            metrics = elem_metrics['spanner']
            summary = metrics.get('summary', {})
            if summary.get('gt_elements_count', 0) == 0 and summary.get('pred_elements_count', 0) == 0:
                flattened['element_metrics.spanner.type.accuracy'] = 1.0
            elif 'type' in metrics:
                flattened['element_metrics.spanner.type.accuracy'] = metrics['type'].get('accuracy', 0)

        if 'fermata' in elem_metrics:
            metrics = elem_metrics['fermata']
            summary = metrics.get('summary', {})
            if summary.get('gt_elements_count', 0) == 0 and summary.get('pred_elements_count', 0) == 0:
                flattened['element_metrics.fermata.subtype.accuracy'] = 1.0
            elif 'subtype' in metrics:
                flattened['element_metrics.fermata.subtype.accuracy'] = metrics['subtype'].get('accuracy', 0)

        if 'text' in elem_metrics:
            text_metrics = elem_metrics['text']
            summary = text_metrics.get('summary', {})
            if summary.get('gt_elements_count', 0) == 0 and summary.get('pred_elements_count', 0) == 0:
                flattened['element_metrics.text.combined_accuracy'] = 1.0
            elif 'combined_text' in text_metrics:
                flattened['element_metrics.text.combined_accuracy'] = text_metrics['combined_text'].get('accuracy', 0)

        if 'lyrics' in elem_metrics:
            lyrics_metrics = elem_metrics['lyrics']
            summary = lyrics_metrics.get('summary', {})
            if summary.get('gt_elements_count', 0) == 0 and summary.get('pred_elements_count', 0) == 0:
                flattened['element_metrics.lyrics.combined_accuracy'] = 1.0
            elif 'combined_lyrics' in lyrics_metrics:
                flattened['element_metrics.lyrics.combined_accuracy'] = lyrics_metrics['combined_lyrics'].get('accuracy', 0)
    return flattened

def save_metrics_to_csv(average_metrics: Dict[str, float], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_categories = {
        'tree_level_metrics.csv': ['tree_edit_distance.accuracy'],
        'sequence_metrics.csv': ['cer.accuracy', 'ser.accuracy'],
        'musical_structure_metrics.csv': ['chord_metrics.', 'element_metrics.rest.', 'element_metrics.tuplet.'],
        'score_structure_metrics.csv': ['element_metrics.clef.', 'element_metrics.keysig.',
                                         'element_metrics.timesig.', 'element_metrics.tempo.',
                                         'element_metrics.instrument.', 'element_metrics.staff.'],
        'performance_instructions_metrics.csv': ['element_metrics.dynamic.', 'element_metrics.spanner.',
                                                 'element_metrics.fermata.'],
        'texts_metrics.csv': ['element_metrics.text.', 'element_metrics.lyrics.']
    }
    for csv_filename, prefixes in csv_categories.items():
        csv_path = output_dir / csv_filename
        rows = []
        for key, value in sorted(average_metrics.items()):
            for prefix in prefixes:
                if key.startswith(prefix):
                    metric_name = format_metric_name(key)
                    rows.append({
                        'Metric': metric_name,
                        'Value': f'{value:.6f}'
                    })
                    break
        if rows:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Metric', 'Value'])
                writer.writeheader()
                writer.writerows(rows)
            print(f"Saved {csv_filename} ({len(rows)} metrics)")

def save_detailed_reports(all_metrics: List[Dict], file_pairs: List[tuple], output_dir: Path) -> None:
    reports_dir = output_dir / 'detailed_reports'
    reports_dir.mkdir(parents=True, exist_ok=True)

    for metrics, (true_path, pred_path, filename) in zip(all_metrics, file_pairs):
        report_path = reports_dir / f"{Path(filename).stem}.txt"
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            print(f"File: {filename}")
            print(f"Ground truth: {true_path}")
            print(f"Predicted: {pred_path}")
            print("\n" + "="*80 + "\n")
            print_metrics(metrics, show_detailed_errors=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(output_buffer.getvalue())
        print(f"Saved detailed report: {report_path.name}")

def calculate_average_metrics(true_dir: str, predicted_dir: str,
                             ted_approximate: bool = False,
                             chord_use_alignment: bool = True,
                             output_file: str = None,
                             detailed_errors: bool = False,
                             metric_groups: List[str] = None) -> Dict:
    print("="*80)
    print("COMPUTING AVERAGE METRICS ACROSS FILES")
    print("="*80)
    print(f"Ground truth folder: {true_dir}")
    print(f"Predicted folder: {predicted_dir}")
    print()
    
    file_pairs = find_matching_files(true_dir, predicted_dir)
    
    if not file_pairs:
        print("No files found for processing")
        return {}
    
    print(f"Found {len(file_pairs)} file pairs for processing")
    print()
    
    all_metrics = []
    failed_files = []
    
    for i, (true_path, pred_path, filename) in enumerate(file_pairs, 1):
        print(f"[{i}/{len(file_pairs)}] Processing {filename}...")
        try:
            results = calculate_all_metrics(
                str(true_path),
                str(pred_path),
                ted_approximate=ted_approximate,
                chord_use_alignment=chord_use_alignment,
                metric_groups=metric_groups
            )
            all_metrics.append(results)
            print(f"Successfully processed")
        except Exception as e:
            print(f"Error processing: {e}")
            failed_files.append((filename, str(e)))
            continue

    if not all_metrics:
        print("Failed to process any files")
        return {}

    print()
    print("="*80)
    print("COMPUTING AVERAGE VALUES")
    print("="*80)

    flattened_metrics_list = [flatten_metrics(m) for m in all_metrics]

    metric_sums = defaultdict(float)
    metric_counts = defaultdict(int)

    for flat_metrics in flattened_metrics_list:
        for key, value in flat_metrics.items():
            if isinstance(value, (int, float)) and not (isinstance(value, float) and (value != value)):
                metric_sums[key] += value
                metric_counts[key] += 1

    average_metrics = {}
    for key in metric_sums:
        if metric_counts[key] > 0:
            average_metrics[key] = metric_sums[key] / metric_counts[key]

    result = {
        'summary': {
            'total_files': len(file_pairs),
            'processed_files': len(all_metrics),
            'failed_files': len(failed_files),
            'true_dir': true_dir,
            'predicted_dir': predicted_dir
        },
        'average_metrics': average_metrics,
        'failed_files': failed_files
    }

    print(f"\nProcessed files: {len(all_metrics)}/{len(file_pairs)}")
    if failed_files:
        print(f"\nFiles with errors ({len(failed_files)}):")
        for filename, error in failed_files:
            print(f"  - {filename}: {error}")

    print("\n" + "="*80)
    print("AVERAGE ACCURACY METRICS")
    print("="*80)

    categories = {
        '1. TREE-LEVEL METRICS': ['tree_edit_distance.accuracy'],
        '2. SEQUENCE METRICS': ['cer.accuracy', 'ser.accuracy'],
        '3. MUSICAL STRUCTURE METRICS': ['chord_metrics.', 'element_metrics.rest.', 'element_metrics.tuplet.'],
        '4. SCORE STRUCTURE METRICS': ['element_metrics.clef.', 'element_metrics.keysig.', 'element_metrics.timesig.',
                                        'element_metrics.tempo.', 'element_metrics.instrument.', 'element_metrics.staff.'],
        '5. PERFORMANCE INSTRUCTIONS METRICS': ['element_metrics.dynamic.', 'element_metrics.spanner.', 'element_metrics.fermata.'],
        '6. TEXTS METRICS': ['element_metrics.text.', 'element_metrics.lyrics.']
    }

    for category_name, prefixes in categories.items():
        print(f"\n{category_name}:")
        found_any = False
        for key, value in sorted(average_metrics.items()):
            for prefix in prefixes:
                if key.startswith(prefix):
                    display_key = format_metric_name(key)
                    print(f"  {display_key}: {value:.4f}")
                    found_any = True
                    break
        if not found_any:
            print("  (no data)")

    if output_file:
        output_path = Path(output_file)
        output_path.mkdir(parents=True, exist_ok=True)
        print("\n" + "="*80)
        print("SAVING CSV REPORTS")
        print("="*80)
        save_metrics_to_csv(average_metrics, output_path)
        if detailed_errors:
            print("\n" + "="*80)
            print("SAVING DETAILED REPORTS")
            print("="*80)
            save_detailed_reports(all_metrics, file_pairs, output_path)
    print("\n" + "="*80 + "\n")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compute average metrics across all files from two folders',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('true_dir', help='Path to folder with ground truth files')
    parser.add_argument('predicted_dir', help='Path to folder with predicted files')
    
    parser.add_argument('--ted-approximate', action='store_true',
                       help='Use approximate algorithm for large trees')
    parser.add_argument('--no-chord-alignment', action='store_true',
                       help='Disable chord sequence alignment (use strict position matching)')
    parser.add_argument('-o', '--output', dest='output_file',
                       help='Path to directory for CSV reports or file for JSON results')
    parser.add_argument('--detailed-errors', action='store_true',
                       help='Save detailed text reports for each score file (only with -o directory)')
    parser.add_argument('-metric', '--metric', dest='metric',
                       choices=['all', 'tree', 'sequence', 'chord', 'musical_structure',
                               'score_structure', 'performance_instructions', 'texts', 'other_elements'],
                       default='all',
                       help='Metric group to calculate: all (default), tree, sequence, chord, '
                            'musical_structure, score_structure, performance_instructions, texts, other_elements')
    args = parser.parse_args()
    metric_groups = [args.metric] if args.metric != 'all' else ['all']
    try:
        result = calculate_average_metrics(
            args.true_dir,
            args.predicted_dir,
            ted_approximate=args.ted_approximate,
            chord_use_alignment=not args.no_chord_alignment,
            output_file=args.output_file,
            detailed_errors=args.detailed_errors,
            metric_groups=metric_groups
        )

        if not result:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
        sys.exit(1)
