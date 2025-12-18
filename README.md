# OMR Benchmark

Benchmark for evaluating the quality of Optical Music Recognition (OMR) results.

## Benchmark Dataset

The benchmark dataset is available on HuggingFace: [musegroup/omr_benchmark](https://huggingface.co/datasets/musegroup/omr_benchmark)

It contains **1077 pairs** of:
- Symbolic music scores (ground truth in MuseScore format)
- Corresponding PDF renderings with data augmentation (ink blobs, scratches, paper texture, rotation, etc.)

All underlying works are **Public Domain** (CC0-1.0 license).

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Basic usage (computes all metrics)
python calculate_metrics.py <ground_truth.mscz> <predicted.mscz>

# With detailed error analysis
python calculate_metrics.py <ground_truth.mscz> <predicted.mscz> --detailed-errors

# Compute only specific metric groups
python calculate_metrics.py <ground_truth.mscz> <predicted.mscz> --metric tree
python calculate_metrics.py <ground_truth.mscz> <predicted.mscz> --metric musical_structure

# Use approximate algorithm for Tree Edit Distance
python calculate_metrics.py <ground_truth.mscz> <predicted.mscz> --ted-approximate
```



### Computing Average Metrics Across Multiple Files

To evaluate OMR quality on a set of files, you can compute average metrics across all files:

```bash
# Basic usage
python calculate_average_metrics.py data/mscz/ data/predicted/

# With approximate algorithm for large trees
python calculate_average_metrics.py data/mscz/ data/predicted/ --ted-approximate

# Save reports to CSV files in a directory
python calculate_average_metrics.py data/mscz/ data/predicted/ -o report_dir/

# Save CSV reports and detailed text reports for each file
python calculate_average_metrics.py data/mscz/ data/predicted/ -o report_dir/ --detailed-errors

# Compute only specific metric groups
python calculate_average_metrics.py data/mscz/ data/predicted/ --metric score_structure
```

The script will automatically find all pairs of files with matching names in the specified folders, compute metrics for each pair, and output average values across all files.

**Output files (when using `-o` option):**
- `tree_level_metrics.csv` - Tree Edit Distance metrics
- `sequence_metrics.csv` - CER and SER metrics
- `musical_structure_metrics.csv` - Chord attributes, rests, tuplets
- `score_structure_metrics.csv` - Clefs, key signatures, time signatures, tempo, instruments, staffs
- `performance_instructions_metrics.csv` - Dynamics, spanners, fermatas
- `texts_metrics.csv` - Text elements and lyrics
- `detailed_reports/` - Individual detailed reports for each file (with `--detailed-errors`)



### Parameters

**Optimization:**
- `--ted-approximate` - Use approximate algorithm for Tree Edit Distance (much faster for large trees)
  - Recommended for trees > 500 nodes
  - For trees < 500 nodes: use without this flag

**Metric selection:**
- `--metric` - Select which metric groups to compute:
  - `all` (default) - Compute all metrics
  - `tree` - Tree-level metrics (TED)
  - `sequence` - Sequence metrics (CER, SER)
  - `chord` - Chord-level metrics (pitches, durations, articulations, etc.)
  - `musical_structure` - Musical structure (chords, rests, tuplets)
  - `score_structure` - Score structure (clefs, key/time signatures, tempo, instruments, staffs)
  - `performance_instructions` - Performance instructions (dynamics, spanners, fermatas)
  - `texts` - Text elements and lyrics

**Output options:**
- `--detailed-errors` - Show detailed error analysis (for single file) or save detailed reports (for batch processing)
- `-o` / `--output` - Output directory for CSV reports (batch processing only)



** **
<details>
<summary>Example detailed output for a single file</summary>

```
Loading ground truth from data/mscz/score_file_12.mscz...
Loading prediction from data/predicted/score_file_12.mscz...
Tree sizes: GT=2674, Pred=2654
Computing metrics...
1. Tree Edit Distance...
    Using approximate algorithm (sizes: 2674, 2654)
   TED computed in 0.51 seconds
2. Sequence metrics (CER, SER)...
3. Chord-level metrics...
   Computing measure alignment from chords...
4. Other element metrics...

================================================================================
OMR QUALITY ASSESSMENT RESULTS
================================================================================

1. TREE-LEVEL METRICS
================================================================================
  TED: 50 | Normalized Error: 0.0187 | Accuracy: 0.9813

2. SEQUENCE METRICS
================================================================================
  CER: 0.0384 (Accuracy: 0.9616, Errors: 616/16041)
  SER: 0.0525 (Accuracy: 0.9475, Errors: 132/2514)

3. MUSICAL STRUCTURE METRICS
================================================================================
  Chords: GT=573, Pred=573, Matched=573, Missing=0, Extra=0
Chord attributes accuracies: pitch=0.885 | duration=0.997 | spanner=0.970 | dot=0.997 | articulation=0.993 | arpeggio=0.998 | accidental=0.997
  Rest: Accuracy=1.000 (46/46) | GT=46, Pred=46, Missing=0, Extra=0

4. SCORE STRUCTURE METRICS
================================================================================
  Clef: Accuracy=1.000 (4/4) | GT=4, Pred=4, Missing=0, Extra=0
  KeySig: Accuracy=0.250 (2/8) | GT=6, Pred=8, Missing=0, Extra=2
  TimeSig: Accuracy=1.000 (2/2) | GT=2, Pred=2, Missing=0, Extra=0
  Tempo: Accuracy=1.000 | Edit Distance=0 | GT=1, Pred=1
  Instrument: Accuracy=1.000 (1/1) | GT=1, Pred=1, Missing=0, Extra=0
  Staff: Accuracy=1.000 (2/2) | GT=2, Pred=2, Missing=0, Extra=0

5. PERFORMANCE INSTRUCTIONS METRICS
================================================================================
  Dynamic: Accuracy=1.000 (16/16) | GT=16, Pred=16, Missing=0, Extra=0
  Spanner: Accuracy=0.844 (54/64) | GT=62, Pred=56, Missing=8, Extra=2
  Fermata: Accuracy=1.000 (1/1) | GT=1, Pred=1, Missing=0, Extra=0

6. TEXTS METRICS
================================================================================
  Text: Accuracy=1.000 | Edit Distance=0 | GT=1, Pred=1

================================================================================
DETAILED ERRORS
================================================================================

================================================================================
CHORD-LEVEL METRICS
================================================================================

SUMMARY:
  GT Chords: 573
  Pred Chords: 573
  Matched Chords: 573
  Missing Chords: 0
  Extra Chords: 0

MEASURE STATISTICS:
  GT Measures: 152
  Pred Measures: 152
  Matched Measures: 152
  Missing Measures: 0
  Extra Measures: 0

ATTRIBUTE ACCURACY:
  PITCH:
    Accuracy: 0.8848 (507/573)
    Errors: 66
  DURATION:
    Accuracy: 0.9965 (571/573)
    Errors: 2
  SPANNER:
    Accuracy: 0.9703 (556/573)
    Errors: 17
  DOT:
    Accuracy: 0.9965 (571/573)
    Errors: 2
  ARTICULATION:
    Accuracy: 0.9930 (569/573)
    Errors: 4
  ARPEGGIO:
    Accuracy: 0.9983 (572/573)
    Errors: 1
  ACCIDENTAL:
    Accuracy: 0.9965 (571/573)
    Errors: 2

DETAILED ERRORS:

  PITCH ERRORS (66 total):
    [1] Staff 1, Measure 1: True=['75'] → Pred=['72']
    [2] Staff 1, Measure 2: True=['74'] → Pred=['70']
    [3] Staff 1, Measure 2: True=['72'] → Pred=['69']
    [4] Staff 1, Measure 11: True=['69'] → Pred=['72']
    [5] Staff 1, Measure 15: True=['72'] → Pred=['75']
    [6] Staff 1, Measure 15: True=['69'] → Pred=['72']
    [7] Staff 1, Measure 16: True=['67'] → Pred=['70']
    [8] Staff 1, Measure 16: True=['66'] → Pred=['70']
    [9] Staff 1, Measure 20: True=['68'] → Pred=['69']
    [10] Staff 1, Measure 21: True=['68'] → Pred=['69']
    [11] Staff 1, Measure 23: True=['68'] → Pred=['69']
    [12] Staff 1, Measure 24: True=['68'] → Pred=['69']
    [13] Staff 1, Measure 24: True=['68'] → Pred=['69']
    [14] Staff 1, Measure 31: True=['71'] → Pred=['74']
    [15] Staff 1, Measure 60: True=['70'] → Pred=['74']
    [16] Staff 1, Measure 60: True=['79'] → Pred=['82']
    [17] Staff 1, Measure 60: True=['70'] → Pred=['74']
    [18] Staff 1, Measure 60: True=['79'] → Pred=['82']
    [19] Staff 1, Measure 61: True=['79'] → Pred=['75']
    [20] Staff 1, Measure 64: True=['72', '81'] → Pred=['69', '81']
    [21] Staff 1, Measure 77: True=['59', '62', '67'] → Pred=['62', '67', '70']
    [22] Staff 2, Measure 16: True=['48'] → Pred=['51']
    [23] Staff 2, Measure 16: True=['51'] → Pred=['55']
    [24] Staff 2, Measure 20: True=['46', '50', '56'] → Pred=['46', '50', '57']
    [25] Staff 2, Measure 21: True=['56'] → Pred=['53']
    [26] Staff 2, Measure 21: True=['55'] → Pred=['51']
    [27] Staff 2, Measure 22: True=['63'] → Pred=['60']
    [28] Staff 2, Measure 22: True=['61'] → Pred=['58']
    [29] Staff 2, Measure 23: True=['60'] → Pred=['57']
    [30] Staff 2, Measure 23: True=['65'] → Pred=['62']
    [31] Staff 2, Measure 23: True=['56'] → Pred=['53']
    [32] Staff 2, Measure 24: True=['63'] → Pred=['57']
    [33] Staff 2, Measure 24: True=['62'] → Pred=['55']
    [34] Staff 2, Measure 24: True=['58'] → Pred=['55']
    [35] Staff 2, Measure 27: True=['58', '68'] → Pred=['60', '68']
    [36] Staff 2, Measure 27: True=['62'] → Pred=['60']
    [37] Staff 2, Measure 27: True=['63'] → Pred=['65']
    [38] Staff 2, Measure 28: True=['58', '68'] → Pred=['60', '68']
    [39] Staff 2, Measure 28: True=['65'] → Pred=['60']
    [40] Staff 2, Measure 29: True=['58', '68'] → Pred=['56', '68']
    [41] Staff 2, Measure 29: True=['62'] → Pred=['65']
    [42] Staff 2, Measure 29: True=['63'] → Pred=['65']
    [43] Staff 2, Measure 30: True=['58', '68'] → Pred=['48']
    [44] Staff 2, Measure 30: True=['65'] → Pred=['41']
    [45] Staff 2, Measure 31: True=['63', '67'] → Pred=['43', '46']
    [46] Staff 2, Measure 32: True=['56', '63', '65'] → Pred=['36', '43', '44']
    [47] Staff 2, Measure 33: True=['58', '62', '68'] → Pred=['38', '41', '48']
    [48] Staff 2, Measure 34: True=['63', '67'] → Pred=['43', '46']
    [49] Staff 2, Measure 34: True=['70'] → Pred=['50']
    [50] Staff 2, Measure 34: True=['68'] → Pred=['48']
    [51] Staff 2, Measure 34: True=['67'] → Pred=['46']
    [52] Staff 2, Measure 34: True=['65'] → Pred=['44']
    [53] Staff 2, Measure 34: True=['63'] → Pred=['43']
    [54] Staff 2, Measure 35: True=['63', '67'] → Pred=['43', '46']
    [55] Staff 2, Measure 45: True=['42'] → Pred=['46']
    [56] Staff 2, Measure 53: True=['42'] → Pred=['46']
    [57] Staff 2, Measure 53: True=['43'] → Pred=['46']
    [58] Staff 2, Measure 54: True=['36'] → Pred=['39']
    [59] Staff 2, Measure 54: True=['48'] → Pred=['51']
    [60] Staff 2, Measure 54: True=['38'] → Pred=['41']
    [61] Staff 2, Measure 54: True=['50'] → Pred=['53']
    [62] Staff 2, Measure 54: True=['38'] → Pred=['41']
    [63] Staff 2, Measure 54: True=['50'] → Pred=['53']
    [64] Staff 2, Measure 56: True=['51'] → Pred=['55']
    [65] Staff 2, Measure 56: True=['55'] → Pred=['58']
    [66] Staff 2, Measure 66: True=['58'] → Pred=['62']

  DURATION ERRORS (2 total):
    [1] Staff 2, Measure 28: True=quarter → Pred=half
    [2] Staff 2, Measure 30: True=quarter → Pred=half

  SPANNER ERRORS (17 total):
    [1] Staff 1, Measure 19: True=['Tie'] → Pred=['Slur', 'Tie']
    [2] Staff 1, Measure 19: True=['Slur'] → Pred=[]
    [3] Staff 1, Measure 27: True=['Slur'] → Pred=[]
    [4] Staff 1, Measure 27: True=['Slur'] → Pred=[]
    [5] Staff 1, Measure 32: True=['Slur', 'Tie'] → Pred=['Tie']
    [6] Staff 1, Measure 32: True=['Slur'] → Pred=[]
    [7] Staff 1, Measure 41: True=[] → Pred=['Slur']
    [8] Staff 1, Measure 42: True=['Slur'] → Pred=[]
    [9] Staff 2, Measure 20: True=['Tie'] → Pred=[]
    [10] Staff 2, Measure 21: True=['Slur', 'Tie'] → Pred=['Slur']
    [11] Staff 2, Measure 26: True=['Slur'] → Pred=[]
    [12] Staff 2, Measure 26: True=['Slur'] → Pred=[]
    [13] Staff 2, Measure 29: True=['Tie'] → Pred=[]
    [14] Staff 2, Measure 30: True=['Tie'] → Pred=[]
    [15] Staff 2, Measure 35: True=['Slur'] → Pred=[]
    [16] Staff 2, Measure 37: True=['Slur'] → Pred=['Tie']
    [17] Staff 2, Measure 38: True=['Slur'] → Pred=['Tie']

  DOT ERRORS (2 total):
    [1] Staff 2, Measure 28: True=False → Pred=True
    [2] Staff 2, Measure 30: True=False → Pred=True

  ARTICULATION ERRORS (4 total):
    [1] Staff 1, Measure 17: True=[] → Pred=['articStaccato']
    [2] Staff 1, Measure 17: True=['articStaccato'] → Pred=[]
    [3] Staff 1, Measure 61: True=['articAccent'] → Pred=[]
    [4] Staff 1, Measure 68: True=['articStaccato'] → Pred=[]

  ARPEGGIO ERRORS (1 total):
    [1] Staff 1, Measure 76: True=[] → Pred=['0']

  ACCIDENTAL ERRORS (2 total):
    [1] Staff 1, Measure 31: True=['accidentalNatural'] → Pred=[]
    [2] Staff 2, Measure 22: True=['accidentalFlat'] → Pred=[]

================================================================================
KEYSIG-LEVEL METRICS
================================================================================

SUMMARY:
  GT KeySigs: 6
  Pred KeySigs: 8
  Matched KeySigs: 6
  Missing KeySigs: 0
  Extra KeySigs: 2

VALUE ACCURACY:
  Accuracy: 0.2500 (2/8)
  Errors: 6

DETAILED ERRORS:
  [1] Staff 1: True=-3 → Pred=-2
  [2] Staff 1: True=-2 → Pred=-3
  [3] Staff 1: True=None → Pred=-2
  [4] Staff 2: True=-3 → Pred=-2
  [5] Staff 2: True=-2 → Pred=-3
  [6] Staff 2: True=None → Pred=-2

================================================================================
SPANNER-LEVEL METRICS
================================================================================

SUMMARY:
  GT Spanners: 62
  Pred Spanners: 56
  Matched Spanners: 54
  Missing Spanners: 8
  Extra Spanners: 2

VALUE ACCURACY:
  Accuracy: 0.8438 (54/64)
  Errors: 10

DETAILED ERRORS:
  [1] Staff 1, Measure 26: True=HairPin → Pred=None
  [2] Staff 1, Measure 27: True=HairPin → Pred=None
  [3] Staff 1, Measure 32: True=HairPin → Pred=None
  [4] Staff 1, Measure 33: True=HairPin → Pred=None
  [5] Staff 1, Measure 35: True=Volta → Pred=None
  [6] Staff 1, Measure 36: True=Volta → Pred=None
  [7] Staff 1, Measure 50: True=HairPin → Pred=None
  [8] Staff 1, Measure 52: True=HairPin → Pred=None
  [9] Staff 2, Measure 26: True=None → Pred=HairPin
  [10] Staff 2, Measure 27: True=None → Pred=HairPin

================================================================================
```
</details>

** **


## Quality Metrics

The benchmark computes metrics organized into 6 main categories:

### 1. Tree-level Metrics
- **Tree Edit Distance (TED)** - Edit distance between the ground truth and predicted score trees
- **Normalized Error** - TED normalized by the size of the larger tree
- **Tree Accuracy** - 1 - normalized error

### 2. Sequence Metrics
- **CER (Character Error Rate)** - Error rate at character level when serializing the score
- **SER (Symbol Error Rate)** - Error rate at musical symbol level (notes, rests, clefs, etc.)
- Both metrics include accuracy values (1 - error rate)

### 3. Musical Structure Metrics
Metrics for the core musical content:

**Chord-level attributes:**
- **Pitch Accuracy** - Accuracy of note pitches in chords
- **Duration Accuracy** - Accuracy of chord durations
- **Spanner Accuracy** - Accuracy of spanners (ties, slurs, etc.) attached to chords
- **Dot Accuracy** - Accuracy of dotted note recognition
- **Articulation Accuracy** - Accuracy of articulations (staccato, accent, etc.)
- **Arpeggio Accuracy** - Accuracy of arpeggio markings
- **Accidental Accuracy** - Accuracy of accidentals (sharps, flats, naturals)

**Other musical elements:**
- **Rest Duration Accuracy** - Accuracy of rest durations
- **Tuplet Accuracy** - Accuracy of tuplet values

### 4. Score Structure Metrics
Metrics for structural elements of the score:
- **Clef Accuracy** - Accuracy of clef recognition
- **KeySig Accuracy** - Accuracy of key signature recognition
- **TimeSig Accuracy** - Accuracy of time signature recognition
- **Tempo Accuracy** - Accuracy of tempo markings
- **Instrument Accuracy** - Accuracy of instrument recognition
- **Staff Accuracy** - Accuracy of staff presence (count and structure)

### 5. Performance Instructions Metrics
Metrics for performance-related markings:
- **Dynamic Accuracy** - Accuracy of dynamic markings (piano, forte, etc.)
- **Spanner Accuracy** - Accuracy of spanner types (slurs, ties, etc.)
- **Fermata Accuracy** - Accuracy of fermata recognition

### 6. Texts Metrics
Metrics for textual elements:
- **Text Accuracy** - Accuracy of text elements (title, composer, etc.) using Levenshtein distance
- **Lyrics Accuracy** - Accuracy of lyrics using Levenshtein distance

### Understanding Accuracy Metrics

The term "Accuracy" has different meanings depending on the metric type:

**1. Tree-level Accuracy:**
- Formula: `Accuracy = 1 - (TED / max(tree_size_GT, tree_size_Pred))`
- Meaning: Normalized accuracy based on tree edit distance. Represents how structurally similar the trees are, normalized by the size of the larger tree.
- Range: 0.0 to 1.0 (higher is better)

**2. Sequence Metrics Accuracy (CER/SER):**
- Formula: `Accuracy = 1 - Error_Rate`
- Meaning: Proportion of correctly recognized characters/symbols in the serialized score representation.
- Range: 0.0 to 1.0 (higher is better)

**3. Chord and Element Metrics Accuracy:**
- Formula: `Accuracy = correct / total`
- Meaning: Proportion of correctly recognized attributes among all matched chord/element pairs. For each matched pair (GT chord ↔ Predicted chord), individual attributes (pitch, duration, etc.) are compared. Accuracy is the fraction of attributes that match correctly.
- Range: 0.0 to 1.0 (higher is better)
- Note: Only matched pairs are evaluated (missing or extra elements are counted separately in summary statistics)

**4. Text/Lyrics/Tempo Accuracy:**
- Formula: `Accuracy = 1 - (Levenshtein_distance / max(text_length_GT, text_length_Pred))`
- Meaning: Normalized string similarity based on edit distance. Represents how similar the text strings are, accounting for insertions, deletions, and substitutions.
- Range: 0.0 to 1.0 (higher is better)

