# OMR Benchmark

Benchmark for evaluating the quality of Optical Music Recognition (OMR) results.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Basic usage
python calculate_metrics.py <ground_truth.mscz> <predicted.mscz>

# With detailed error analysis
python calculate_metrics.py <ground_truth.mscz> <predicted.mscz> --detailed-errors
```



### Computing Average Metrics Across Multiple Files

To evaluate OMR quality on a set of files, you can compute average metrics across all files:

```bash
# Basic usage
python calculate_average_metrics.py data/mscz/ data/predicted/

# With approximate algorithm for large trees
python calculate_average_metrics.py data/mscz/ data/predicted/ --ted-approximate

# With saving results to JSON file
python calculate_average_metrics.py data/mscz/ data/predicted/ -o results.json
```

The script will automatically find all pairs of files with matching names in the specified folders, compute metrics for each pair, and output average values across all files.



### Optimization for Large Trees

TED can be slow on large scores. The following optimization is available:

```bash
# Use approximate algorithm (much faster)
python calculate_metrics.py data/mscz/score.mscz data/predicted/score.mscz --ted-approximate
```

**Optimization parameters:**
- `--ted-approximate` - uses approximate algorithm for large trees (recommended for trees > 500 nodes)

**Recommendations:**
- For trees < 500 nodes: use without optimizations
- For trees > 500 nodes: use `--ted-approximate`



**Example output for a single file with detailed error analysis:**

```
================================================================================
OMR QUALITY ASSESSMENT RESULTS
================================================================================

TREE-LEVEL METRICS:
  Tree Edit Distance (TED): 21
  Normalized Error: 0.0079
  Tree Accuracy: 0.9921

SEQUENCE METRICS:
  CER (Character Error Rate): 0.0214
  CER Accuracy: 0.9786
  CER Errors: 1457/68154

  SER (Symbol Error Rate): 0.0609
  SER Accuracy: 0.9391
  SER Errors: 215/3533
  SER Matches: 2291

NOTE-LEVEL METRICS:
  Precision: 0.9333
  Recall: 1.0000
  F1-Score: 0.9655
  True Positives: 42
  False Positives: 3
  False Negatives: 0
  Total Notes in GT: 661
  Total Notes in Prediction: 660

PITCH ACCURACY:
  Pitch Accuracy: 0.6303
  Correct Pitches: 416/660

DURATION ACCURACY:
  Duration Accuracy: 0.9818
  Correct Durations: 648/660

MEASURE-LEVEL METRICS:
  Measure Count Accuracy: 1.0000
  Measure Content Accuracy: 1.0000
  Measures in GT: 154
  Measures in Prediction: 154

STAFF-LEVEL METRICS:
  Staff Count Accuracy: 1.0000
  Clef Accuracy: 1.0000
  Staffs in GT: 2
  Staffs in Prediction: 2

DETAILED ERROR ANALYSIS
====================================================================================================

  PITCH ERRORS:
  Total errors: 76
  Error types:
    pitch_mismatch: 72
    missing_note: 2
    extra_note: 1
    count_mismatch: 1
  Errors by measures (showing up to 100 errors):
    Staff 0, Measure 0:
      Note #1: GT=75 → Pred=72 (Duration: GT=16th, Pred=16th)

    Staff 0, Measure 1:
      Note #0: GT=74 → Pred=70 (Duration: GT=quarter, Pred=quarter)
      Note #1: GT=72 → Pred=69 (Duration: GT=quarter, Pred=quarter)

    Staff 0, Measure 10:
      Note #1: GT=69 → Pred=72 (Duration: GT=eighth, Pred=eighth)

    Staff 0, Measure 14:
      Note #2: GT=72 → Pred=75 (Duration: GT=eighth, Pred=eighth)
      Note #3: GT=69 → Pred=72 (Duration: GT=eighth, Pred=eighth)

    Staff 0, Measure 15:
      Note #4: GT=67 → Pred=70 (Duration: GT=eighth, Pred=eighth)
      Note #5: GT=66 → Pred=70 (Duration: GT=eighth, Pred=eighth)

    Staff 0, Measure 19:
      Note #2: GT=68 → Pred=69 (Duration: GT=eighth, Pred=eighth)

    Staff 0, Measure 20:
      Note #0: GT=68 → Pred=69 (Duration: GT=quarter, Pred=quarter)

    Staff 0, Measure 22:
      Note #5: GT=68 → Pred=69 (Duration: GT=eighth, Pred=eighth)

    Staff 0, Measure 23:
      Note #0: GT=68 → Pred=69 (Duration: GT=eighth, Pred=eighth)
      Note #4: GT=68 → Pred=69 (Duration: GT=eighth, Pred=eighth)

    Staff 0, Measure 30:
      Note #3: GT=71 → Pred=74 (Duration: GT=quarter, Pred=quarter)

    Staff 0, Measure 59:
      Note #0: GT=70 → Pred=74 (Duration: GT=eighth, Pred=eighth)
      Note #1: GT=79 → Pred=82 (Duration: GT=eighth, Pred=eighth)
      Note #2: GT=70 → Pred=74 (Duration: GT=eighth, Pred=eighth)
      Note #3: GT=79 → Pred=82 (Duration: GT=eighth, Pred=eighth)

    Staff 0, Measure 60:
      Note #6: GT=79 → Pred=75 (Duration: GT=eighth, Pred=eighth)

    Staff 0, Measure 63:
      Note #3: GT=72 → Pred=69 (Duration: GT=eighth, Pred=eighth)

    Staff 0, Measure 76:
      Missing note #0: 59
      Extra note #2: 70

    Staff 1, Measure 15:
      Note #0: GT=48 → Pred=51 (Duration: GT=eighth, Pred=eighth)
      Note #1: GT=51 → Pred=55 (Duration: GT=eighth, Pred=eighth)

    Staff 1, Measure 19:
      Note #2: GT=56 → Pred=57 (Duration: GT=half, Pred=half)

    Staff 1, Measure 20:
      Note #0: GT=56 → Pred=53 (Duration: GT=quarter, Pred=quarter)
      Note #1: GT=55 → Pred=51 (Duration: GT=quarter, Pred=quarter)

    Staff 1, Measure 21:
      Note #0: GT=63 → Pred=60 (Duration: GT=half, Pred=half)
      Note #1: GT=61 → Pred=58 (Duration: GT=quarter, Pred=quarter)

    Staff 1, Measure 22:
      Note #0: GT=60 → Pred=57 (Duration: GT=half, Pred=half)
      Note #1: GT=65 → Pred=62 (Duration: GT=quarter, Pred=quarter)
      Note #2: GT=56 → Pred=53 (Duration: GT=half, Pred=half)

    Staff 1, Measure 23:
      Note #0: GT=63 → Pred=57 (Duration: GT=half, Pred=half)
      Note #1: GT=62 → Pred=55 (Duration: GT=quarter, Pred=quarter)
      Note #2: GT=58 → Pred=55 (Duration: GT=half, Pred=half)

    Staff 1, Measure 26:
      Note #0: GT=58 → Pred=60 (Duration: GT=half, Pred=half)
      Note #2: GT=62 → Pred=60 (Duration: GT=half, Pred=half)
      Note #3: GT=63 → Pred=65 (Duration: GT=quarter, Pred=quarter)

    Staff 1, Measure 27:
      Note #0: GT=58 → Pred=60 (Duration: GT=quarter, Pred=quarter)
      Note #2: GT=65 → Pred=60 (Duration: GT=quarter, Pred=half)

    Staff 1, Measure 28:
      Note #0: GT=58 → Pred=56 (Duration: GT=half, Pred=half)
      Note #2: GT=62 → Pred=65 (Duration: GT=half, Pred=half)
      Note #3: GT=63 → Pred=65 (Duration: GT=quarter, Pred=quarter)

    Staff 1, Measure 29:
      Note count mismatch: GT=3, Pred=2
      Note #0: GT=58 → Pred=48 (Duration: GT=quarter, Pred=quarter)
      Note #1: GT=68 → Pred=41 (Duration: GT=quarter, Pred=half)
      Missing note #2: 65

    Staff 1, Measure 30:
      Note #0: GT=63 → Pred=43 (Duration: GT=half, Pred=half)
      Note #1: GT=67 → Pred=46 (Duration: GT=half, Pred=half)

    Staff 1, Measure 31:
      Note #0: GT=56 → Pred=36 (Duration: GT=half, Pred=half)
      Note #1: GT=63 → Pred=43 (Duration: GT=half, Pred=half)
      Note #2: GT=65 → Pred=44 (Duration: GT=half, Pred=half)

    Staff 1, Measure 32:
      Note #0: GT=58 → Pred=38 (Duration: GT=half, Pred=half)
      Note #1: GT=62 → Pred=41 (Duration: GT=half, Pred=half)
      Note #2: GT=68 → Pred=48 (Duration: GT=half, Pred=half)

    Staff 1, Measure 33:
      Note #0: GT=63 → Pred=43 (Duration: GT=eighth, Pred=eighth)
      Note #1: GT=67 → Pred=46 (Duration: GT=eighth, Pred=eighth)
      Note #2: GT=70 → Pred=50 (Duration: GT=eighth, Pred=eighth)
      Note #3: GT=68 → Pred=48 (Duration: GT=eighth, Pred=eighth)
      Note #4: GT=67 → Pred=46 (Duration: GT=eighth, Pred=eighth)
      Note #5: GT=65 → Pred=44 (Duration: GT=eighth, Pred=eighth)
      Note #6: GT=63 → Pred=43 (Duration: GT=eighth, Pred=eighth)

    Staff 1, Measure 34:
      Note #0: GT=63 → Pred=43 (Duration: GT=quarter, Pred=quarter)
      Note #1: GT=67 → Pred=46 (Duration: GT=quarter, Pred=quarter)

    Staff 1, Measure 44:
      Note #1: GT=42 → Pred=46 (Duration: GT=quarter, Pred=quarter)

    Staff 1, Measure 52:
      Note #2: GT=42 → Pred=46 (Duration: GT=eighth, Pred=eighth)
      Note #4: GT=43 → Pred=46 (Duration: GT=eighth, Pred=eighth)

    Staff 1, Measure 53:
      Note #0: GT=36 → Pred=39 (Duration: GT=eighth, Pred=eighth)
      Note #1: GT=48 → Pred=51 (Duration: GT=eighth, Pred=eighth)
      Note #2: GT=38 → Pred=41 (Duration: GT=eighth, Pred=eighth)
      Note #3: GT=50 → Pred=53 (Duration: GT=eighth, Pred=eighth)
      Note #4: GT=38 → Pred=41 (Duration: GT=eighth, Pred=eighth)
      Note #5: GT=50 → Pred=53 (Duration: GT=eighth, Pred=eighth)

    Staff 1, Measure 55:
      Note #0: GT=51 → Pred=55 (Duration: GT=eighth, Pred=eighth)
      Note #1: GT=55 → Pred=58 (Duration: GT=eighth, Pred=eighth)

    Staff 1, Measure 65:
      Note #1: GT=58 → Pred=62 (Duration: GT=eighth, Pred=eighth)

  NOTE DURATION ERRORS:
  Total errors: 13
  Error types:
    duration_mismatch: 12
    missing_duration: 1
  Errors (showing up to 100):
    Staff 1, Measure 27: GT=quarter → Pred=half (Pitch: 65)
    Staff 1, Measure 29: GT=quarter → Pred=half (Pitch: 68)
    Staff 1, Measure 29: GT=quarter → Pred=half (Pitch: 65)
    Staff 1, Measure 32: GT=half → Pred=eighth (Pitch: 68)
    Staff 1, Measure 33: GT=eighth → Pred=quarter (Pitch: 63)
    Staff 1, Measure 34: GT=quarter → Pred=half (Pitch: 67)
    Staff 1, Measure 36: GT=half → Pred=quarter (Pitch: 58)
    Staff 1, Measure 46: GT=quarter → Pred=eighth (Pitch: 38)
    Staff 1, Measure 58: GT=eighth → Pred=quarter (Pitch: 48)
    Staff 1, Measure 60: GT=quarter → Pred=eighth (Pitch: 43)
    Staff 1, Measure 66: GT=eighth → Pred=quarter (Pitch: 57)
    Staff 1, Measure 72: GT=quarter → Pred=half (Pitch: 55)
    Missing duration: GT=half (Pitch: 43)

  ARTICULATION ERRORS:
  Total errors: 6
  Error types:
    missing_articulation: 4
    extra_articulation: 2
  Errors (showing up to 100):
    Missing articulation: articAccentAbove (Staff 0, Measure 60, Chord 268)
       GT: [articAccentAbove], Pred: [(no articulations)]
    Missing articulation: articStaccatoAbove (Staff 0, Measure 1, Chord 3)
       GT: [articStaccatoAbove], Pred: [articStaccatoBelow]
    Extra articulation: articStaccatoBelow (Staff 0, Measure 1, Chord 3)
       GT: [articStaccatoAbove], Pred: [articStaccatoBelow]
    Missing articulation: articStaccatoBelow (Staff 0, Measure 16, Chord 66)
       GT: [articStaccatoBelow], Pred: [(no articulations)]
    Missing articulation: articStaccatoAbove (Staff 0, Measure 67, Chord 310)
       GT: [articStaccatoAbove], Pred: [(no articulations)]
    Extra articulation: articStaccatoBelow (Staff 0, Measure 16, Chord 65)
       GT: [(no articulations)], Pred: [articStaccatoBelow]

====================================================================================================

ELEMENT CATEGORY METRICS:

  1.1. Instruments and System Parameters:
    INSTRUMENTS:
      Precision: 1.0000
      Recall: 1.0000
      F1: 1.0000
      TP: 1, FP: 0, FN: 0
    STAFFS:
      Precision: 1.0000
      Recall: 1.0000
      F1: 1.0000
      TP: 2, FP: 0, FN: 0
    CLEFS:
      Precision: 1.0000
      Recall: 1.0000
      F1: 1.0000
      TP: 2, FP: 0, FN: 0
    TIME SIGNATURES:
      Precision: 1.0000
      Recall: 1.0000
      F1: 1.0000
      TP: 1, FP: 0, FN: 0

  1.2. Spanners:
    SPANNERS:
      Precision: 1.0000
      Recall: 1.0000
      F1: 1.0000
      TP: 4, FP: 0, FN: 0

  1.3. Articulations:
    ARTICULATIONS:
      Precision: 1.0000
      Recall: 1.0000
      F1: 1.0000
      TP: 4, FP: 0, FN: 0

  1.4. Text Elements:
    TEXT ELEMENTS TREE (Levenshtein):
      Overall Levenshtein Distance: 0
      Overall Normalized Distance: 0.0000
      Overall Accuracy: 1.0000
      Total Texts: 1
      text_0: Distance=0, Accuracy=1.0000
        GT: Bagatelle
        Pred: Bagatelle

  1.5. Lyrics:
    LYRICS:
      Precision: 0.0000
      Recall: 0.0000
      F1: 0.0000
      TP: 0, FP: 0, FN: 0

  1.6. Tempo and Dynamics:
    DYNAMICS:
      Precision: 1.0000
      Recall: 1.0000
      F1: 1.0000
    TEMPOS:
      Precision: 1.0000
      Recall: 1.0000
      F1: 1.0000
    TEMPO TEXT (Levenshtein):
      tempo_0: Distance=0, Accuracy=1.0000

================================================================================

```


## Quality Metrics

The `calculate_metrics.py` script computes the following metrics:

### 1. Tree-level Metrics
- **Tree Edit Distance (TED)** - edit distance between trees
- **Normalized Error** - TED normalized by the size of the larger tree
- **Tree Accuracy** - 1 - normalized error

### 2. Sequence Metrics (Sequential Representation)
- **CER (Character Error Rate)** - error at character level when serializing the score
- **SER (Symbol Error Rate)** - error at musical symbol level (notes, rests, clefs, etc.)

### 3. Note-level Metrics
- **Precision** - proportion of correctly recognized notes among all predicted notes
- **Recall** - proportion of correctly recognized notes among all notes in ground truth
- **F1-Score** - harmonic mean of precision and recall
- Counts: True Positives, False Positives, False Negatives

### 4. Pitch Accuracy
- Compares the pitch of each note by position in the score
- Shows how accurately note pitches are recognized

### 5. Duration Accuracy
- Compares durations of notes and rests
- Shows how accurately rhythmic values are recognized

### 6. Measure-level Metrics
- **Measure Count Accuracy** - accuracy of measure count
- **Measure Content Accuracy** - accuracy of measure content (number of notes/chords)

### 7. Staff-level Metrics
- **Staff Count Accuracy** - accuracy of staff count
- **Clef Accuracy** - accuracy of clef recognition

### 8. Individual Element Category Metrics

#### 8.1. Instruments and System Parameters
- **Instruments** - Precision/Recall/F1 for instruments
- **Staffs** - Precision/Recall/F1 for staffs
- **Clefs** - Precision/Recall/F1 for clefs
- **Time Signatures** - Precision/Recall/F1 for time signatures

#### 8.2. Notes and Their Attributes
- **Pitches** - Precision/Recall/F1 for note pitches
- **Note Durations** - Precision/Recall/F1 for note durations
- **Accidentals** - Precision/Recall/F1 for accidentals
- **Ties** - Precision/Recall/F1 for ties

#### 8.3. Rests
- **Rests** - Precision/Recall/F1 for rests and their durations

#### 8.4. Text Elements
- **Title, Subtitle, Composer** - Levenshtein distance for text fields

#### 8.5. Tempo and Dynamics
- **Dynamics** - Precision/Recall/F1 for dynamic markings
- **Tempos** - Precision/Recall/F1 for tempo markings
- **Tempo Text** - Levenshtein distance for textual tempo markings
