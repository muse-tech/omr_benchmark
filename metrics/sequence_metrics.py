"""
Module for computing sequence metrics (CER, SER).
"""

from typing import List, Dict
from core.score_tree import Node
from Levenshtein import distance as levenshtein_distance


def serialize_score_to_string(node: Node, include_metadata=True) -> str:
    tokens = []
    
    def traverse(n: Node, depth=0):
        """Tree traversal."""
        if n.label != "Score":
            tokens.append(f"<{n.label}>")
        
        if n.value:
            tokens.append(str(n.value))
        
        if n.id is not None:
            tokens.append(f"#{n.id}")
        
        for child in n.children:
            traverse(child, depth + 1)
        
        if n.label != "Score":
            tokens.append(f"</{n.label}>")
    
    traverse(node)
    return " ".join(tokens)


def serialize_score_to_symbols(node: Node) -> List[str]:
    symbols = []
    
    def traverse(n: Node):
        """Collects musical elements."""
        if n.label in ["Note", "Rest", "Chord", "Clef", "TimeSig", "KeySig", 
                       "Dynamic", "Tempo", "Accidental", "Duration", "Measure"]:
            symbols.append(n.label)
            if n.value:
                symbols.append(n.value)
    
    def traverse_ordered(n: Node):
        """Recursive traversal."""
        traverse(n)
        for child in n.children:
            traverse_ordered(child)
    
    traverse_ordered(node)
    return symbols


def character_error_rate(gt_tree: Node, pred_tree: Node) -> Dict:
    gt_string = serialize_score_to_string(gt_tree)
    pred_string = serialize_score_to_string(pred_tree)
    
    total_chars = max(len(gt_string), len(pred_string), 1)
    errors = levenshtein_distance(gt_string, pred_string)
    cer = errors / total_chars
    
    return {
        'cer': cer,
        'errors': errors,
        'total_characters': total_chars,
        'accuracy': 1 - cer
    }


def symbol_error_rate(gt_tree: Node, pred_tree: Node) -> Dict:
    gt_symbols = serialize_score_to_symbols(gt_tree)
    pred_symbols = serialize_score_to_symbols(pred_tree)

    gt_symbol_str = "|".join(str(s) for s in gt_symbols)
    pred_symbol_str = "|".join(str(s) for s in pred_symbols)
    
    total_symbols = max(len(gt_symbols), len(pred_symbols), 1)
    
    errors = levenshtein_distance(gt_symbol_str, pred_symbol_str)
    
    ser = errors / total_symbols if total_symbols > 0 else 0
    
    matches = sum(1 for i in range(min(len(gt_symbols), len(pred_symbols)))
                  if gt_symbols[i] == pred_symbols[i])
    
    return {
        'ser': ser,
        'errors': errors,
        'total_symbols': total_symbols,
        'matches': matches,
        'accuracy': 1 - ser
    }
