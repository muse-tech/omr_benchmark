import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any
import json

from calculate_metrics import calculate_all_metrics


def find_matching_files(true_dir: str, predicted_dir: str) -> List[tuple]:
    true_path = Path(true_dir)
    pred_path = Path(predicted_dir)
    
    if not true_path.exists():
        raise FileNotFoundError(f"Folder {true_dir} not found")
    if not pred_path.exists():
        raise FileNotFoundError(f"Folder {predicted_dir} not found")
    
    true_files = {f.name: f for f in true_path.iterdir() if f.is_file()}
    pred_files = {f.name: f for f in pred_path.iterdir() if f.is_file()}
    
    matching_names = set(true_files.keys()) & set(pred_files.keys())
    
    if not matching_names:
        print(f"Warning: no files with matching names found")
        print(f"   Files in {true_dir}: {list(true_files.keys())[:5]}...")
        print(f"   Files in {predicted_dir}: {list(pred_files.keys())[:5]}...")
        return []
    
    pairs = [(true_files[name], pred_files[name], name) for name in matching_names]
    return sorted(pairs, key=lambda x: x[2])  # Sort by filename


def extract_numeric_value(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, dict):
        for key in ['accuracy', 'precision', 'recall', 'f1', 'distance', 'error', 
                   'normalized_error', 'cer', 'ser']:
            if key in value and isinstance(value[key], (int, float)):
                return float(value[key])
        for v in value.values():
            if isinstance(v, (int, float)):
                return float(v)
    elif isinstance(value, list):
        if len(value) > 0 and all(isinstance(x, (int, float)) for x in value):
            return sum(value) / len(value)
    return None


def flatten_metrics(results: Dict, prefix: str = "") -> Dict[str, float]:
    flattened = {}
    
    for key, value in results.items():
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            if key == 'tree_edit_distance':
                flattened[f"{full_key}.distance"] = value.get('distance', 0)
                flattened[f"{full_key}.normalized_error"] = value.get('normalized_error', 0)
                flattened[f"{full_key}.accuracy"] = value.get('accuracy', 0)
            elif key == 'cer':
                flattened[f"{full_key}.cer"] = value.get('cer', 0)
                flattened[f"{full_key}.accuracy"] = value.get('accuracy', 0)
            elif key == 'ser':
                flattened[f"{full_key}.ser"] = value.get('ser', 0)
                flattened[f"{full_key}.accuracy"] = value.get('accuracy', 0)
            elif key == 'note_level':
                flattened[f"{full_key}.precision"] = value.get('precision', 0)
                flattened[f"{full_key}.recall"] = value.get('recall', 0)
                flattened[f"{full_key}.f1"] = value.get('f1', 0)
            elif key == 'pitch_accuracy':
                flattened[f"{full_key}.accuracy"] = value.get('accuracy', 0)
            elif key == 'duration_accuracy':
                flattened[f"{full_key}.accuracy"] = value.get('accuracy', 0)
            elif key == 'measure_level':
                flattened[f"{full_key}.measure_count_accuracy"] = value.get('measure_count_accuracy', 0)
                flattened[f"{full_key}.measure_content_accuracy"] = value.get('measure_content_accuracy', 0)
            elif key == 'staff_level':
                flattened[f"{full_key}.staff_count_accuracy"] = value.get('staff_count_accuracy', 0)
                flattened[f"{full_key}.clef_accuracy"] = value.get('clef_accuracy', 0)
            elif key == 'element_categories':
                for cat_key, cat_value in value.items():
                    if isinstance(cat_value, dict):
                        if 'precision' in cat_value:
                            flattened[f"{full_key}.{cat_key}.precision"] = cat_value.get('precision', 0)
                            flattened[f"{full_key}.{cat_key}.recall"] = cat_value.get('recall', 0)
                            flattened[f"{full_key}.{cat_key}.f1"] = cat_value.get('f1', 0)
                        elif 'overall_accuracy' in cat_value:
                            flattened[f"{full_key}.{cat_key}.overall_accuracy"] = cat_value.get('overall_accuracy', 0)
                            flattened[f"{full_key}.{cat_key}.overall_normalized_distance"] = cat_value.get('overall_normalized_distance', 0)
            else:
                flattened.update(flatten_metrics(value, full_key))
        elif isinstance(value, (int, float)):
            flattened[full_key] = float(value)
    
    return flattened


def calculate_average_metrics(true_dir: str, predicted_dir: str, 
                             ted_approximate: bool = False,
                             output_file: str = None) -> Dict:
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
                ted_approximate=ted_approximate
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
            if isinstance(value, (int, float)) and not (isinstance(value, float) and (value != value)):  # Check for NaN
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
    print("AVERAGE METRICS")
    print("="*80)
    
    categories = {
        'Tree Edit Distance': ['tree_edit_distance'],
        'Sequence Metrics': ['cer', 'ser'],
        'Note Level': ['note_level'],
        'Pitch & Duration': ['pitch_accuracy', 'duration_accuracy'],
        'Measure & Staff': ['measure_level', 'staff_level'],
        'Element Categories': ['element_categories']
    }
    
    for category_name, prefixes in categories.items():
        print(f"\n{category_name}:")
        found_any = False
        for key, value in sorted(average_metrics.items()):
            for prefix in prefixes:
                if key.startswith(prefix):
                    print(f"  {key}: {value:.4f}")
                    found_any = True
                    break
        if not found_any:
            print("  (no data)")
    
    printed_keys = set()
    for category_prefixes in categories.values():
        for prefix in category_prefixes:
            for key in average_metrics:
                if key.startswith(prefix):
                    printed_keys.add(key)
    
    remaining = {k: v for k, v in average_metrics.items() if k not in printed_keys}
    if remaining:
        print("\nOther metrics:")
        for key, value in sorted(remaining.items()):
            print(f"  {key}: {value:.4f}")
    
    if output_file:
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results saved to {output_file}")
    
    print("\n" + "="*80 + "\n")
    
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compute average metrics across all files from two folders',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python calculate_average_metrics.py data/true data/predicted
  
  python calculate_average_metrics.py data/true data/predicted --ted-approximate
  
  python calculate_average_metrics.py data/true data/predicted -o results.json
        """
    )
    
    parser.add_argument('true_dir', help='Path to folder with ground truth files')
    parser.add_argument('predicted_dir', help='Path to folder with predicted files')
    
    parser.add_argument('--ted-approximate', action='store_true',
                       help='Use approximate algorithm for large trees')
    
    parser.add_argument('-o', '--output', dest='output_file',
                       help='Path to file for saving results (JSON)')
    
    args = parser.parse_args()
    
    try:
        result = calculate_average_metrics(
            args.true_dir,
            args.predicted_dir,
            ted_approximate=args.ted_approximate,
            output_file=args.output_file
        )
        
        if not result:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
