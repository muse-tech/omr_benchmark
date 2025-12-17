from typing import List, Dict, Tuple
from core.score_tree import Node
from Levenshtein import distance as levenshtein_distance

LABEL_SHORT_MAP = {
    'Instrument': 'inst',
    'Clef': 'cl',
    'KeySig': 'ks',
    'TimeSig': 'ts',
    'Dynamic': 'dyn',
    'Chord': 'ch',
    'Rest': 'r',
    'Note': 'n',
    'Tuplet': 'tup',
    'Fermata': 'ferm',
    'Spanner': 'sp',
    'Accidental': 'acc',
    'Duration': 'dur',
    'Articulation': 'art',
    'Dot': 'dot',
    'Arpeggio': 'arp'
}

DURATION_MAP = {'0':'0', '1024th':'1_1024', '512th':'1_512', '256th':'1_256', '128th':'1_128', '64th':'1_64', '32nd': '1_32',
             '16th':'1_16', 'eighth':'1_8', 'half':'1_2', 'quarter':'1_4', 'whole':'1', 'breve':'2',
             'long':'4', 'massima':'8', 'measure': '1', 'OtherDuration': 'other'}

PITCH_MAP = {"12":"C0", "13":"Cd0", "14":"D0", "15":"Dd0", "16":"E0", "17":"F0", "18":"Fd0", "19":"G0", "20":"Gd0", "21":"A0", "22":"Ad0", "23":"B0",
                      "24":"C1", "25":"Cd1", "26":"D1", "27":"Dd1", "28":"E1", "29":"F1", "30":"Fd1", "31":"G1", "32":"Gd1", "33":"A1", "34":"Ad1", "35":"B1",
                      "36":"C2", "37":"Cd2", "38":"D2", "39":"Dd2", "40":"E2", "41":"F2", "42":"Fd2", "43":"G2", "44":"Gd2", "45":"A2", "46":"Ad2", "47":"B2",
                      "48":"C3", "49":"Cd3", "50":"D3", "51":"Dd3", "52":"E3", "53":"F3", "54":"Fd3", "55":"G3", "56":"Gd3", "57":"A3", "58":"Ad3", "59":"B3",
                      "60":"C4", "61":"Cd4", "62":"D4", "63":"Dd4", "64":"E4", "65":"F4", "66":"Fd4", "67":"G4", "68":"Gd4", "69":"A4", "70":"Ad4", "71":"B4",
                      "72":"C5", "73":"Cd5", "74":"D5", "75":"Dd5", "76":"E5", "77":"F5", "78":"Fd5", "79":"G5", "80":"Gd5", "81":"A5", "82":"Ad5", "83":"B5",
                      "84":"C6", "85":"Cd6", "86":"D6", "87":"Dd6", "88":"E6", "89":"F6", "90":"Fd6", "91":"G6", "92":"Gd6", "93":"A6", "94":"Ad6", "95":"B6",
                      "96":"C7", "97":"Cd7", "98":"D7", "99":"Dd7", "100":"E7", "101":"F7", "102":"Fd7", "103":"G7", "104":"Gd7", "105":"A7", "106":"Ad7", "107":"B7",
                      "108":"C8", "109":"Cd8", "110":"D8", "111":"Dd8", "112":"E8", "113":"F8", "114":"Fd8", "115":"G8", "116":"Gd8", "117":"A8", "118":"Ad8", "119":"B8",
                      'OtherPitch': 'other'}

ACCIDENTAL_MAP = {'accidentalNatural': 'natural', 'accidentalFlat': 'flat', 'accidentalSharp': 'sharp',
 'accidentalDoubleFlat': 'doubleFlat', 'accidentalDoubleSharp': 'doubleSharp', 'OtherAccidental': 'other'}

ARTICULATION_MAP = {'articStaccatoAbove': 'staccato', 'articStaccatoBelow': 'staccato', 'articAccentAbove': 'accent', 'articAccentBelow': 'accent',
'articMarcatoAbove': 'marcato', 'articMarcatoBelow': 'marcato', 'articTenutoAbove': 'tenuto', 'articTenutoBelow': 'tenuto',
'stringsUpBow': 'upbow', 'stringsDownBow': 'downbow', 'otherArticulations': 'other'}

def serialize_score_to_tokens(node: Node) -> List[str]:
    tokens = []
    
    def traverse(n: Node, depth=0):
        if n.label in LABEL_SHORT_MAP:
            short_label = LABEL_SHORT_MAP[n.label]
            token = short_label
            if n.value:
                if n.label == 'Duration':
                    token += f"_{DURATION_MAP[str(n.value) if str(n.value) in DURATION_MAP else 'OtherDuration']}"
                elif n.label == 'Note':
                    token += f"_{PITCH_MAP[str(n.value) if str(n.value) in PITCH_MAP else 'OtherPitch']}"
                elif n.label == 'Accidental':
                    token += f"_{ACCIDENTAL_MAP[str(n.value) if str(n.value) in ACCIDENTAL_MAP else 'OtherAccidental']}"
                elif n.label == 'Articulation':
                    token += f"_{ARTICULATION_MAP[str(n.value) if str(n.value) in ARTICULATION_MAP else 'otherArticulations']}"
                else:
                    token += f"_{str(n.value)}"
            tokens.append(token)
        for child in n.children:
            traverse(child, depth + 1)

    traverse(node)
    return tokens

def list_edit_distance(seq1, seq2):
    n, m = len(seq1), len(seq2)
    if n > m:
        seq1, seq2 = seq2, seq1
        n, m = m, n
    previous_row = list(range(n + 1))
    for i in range(1, m + 1):
        current_row = [i] + [0]*n
        for j in range(1, n + 1):
            insertions = previous_row[j] + 1
            deletions = current_row[j - 1] + 1
            substitutions = previous_row[j - 1] + (seq1[j - 1] != seq2[i - 1])
            current_row[j] = min(insertions, deletions, substitutions)
        previous_row = current_row
    return previous_row[n]

def _calculate_sequence_metrics(gt_tree: Node, pred_tree: Node) -> Tuple[Dict, Dict]:
    gt_symbols = serialize_score_to_tokens(gt_tree)
    pred_symbols = serialize_score_to_tokens(pred_tree)
    
    gt_string = " ".join(gt_symbols)
    pred_string = " ".join(pred_symbols)
    total_chars = max(len(gt_string), len(pred_string), 1)
    char_errors = levenshtein_distance(gt_string, pred_string)
    cer = char_errors / total_chars

    cer_result = {
        'cer': cer,
        'errors': char_errors,
        'total_characters': total_chars,
        'accuracy': 1 - cer
    }

    total_symbols = max(len(gt_symbols), len(pred_symbols), 1)
    symbol_errors = list_edit_distance(gt_symbols, pred_symbols)
    ser = symbol_errors / len(gt_symbols) if len(gt_symbols) > 0 else 0.0
    matches = len(gt_symbols) - symbol_errors

    ser_result = {
        'ser': ser,
        'errors': symbol_errors,
        'total_symbols': total_symbols,
        'matches': matches,
        'accuracy': 1 - ser
    }
    
    return cer_result, ser_result

def character_error_rate(gt_tree: Node, pred_tree: Node) -> Dict:
    cer_result, _ = _calculate_sequence_metrics(gt_tree, pred_tree)
    return cer_result

def symbol_error_rate(gt_tree: Node, pred_tree: Node) -> Dict:
    _, ser_result = _calculate_sequence_metrics(gt_tree, pred_tree)
    return ser_result
