"""
Module for computing Tree Edit Distance (TED) between trees.
"""

from apted import APTED, Config
from collections import defaultdict
from typing import Tuple
from core.score_tree import Node


class AptNodeConfig(Config):
    def rename(self, node1, node2):
        return 0 if node1.name == node2.name else 1


class AptNode:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []


def convert_to_apted_node(node: Node) -> AptNode:
    return AptNode(
        name=node.int_label,
        children=[convert_to_apted_node(c) for c in node.children]
    )


def count_nodes(node) -> int:
    return 1 + sum(count_nodes(ch) for ch in node.children)


def approximate_ted(tree1: AptNode, tree2: AptNode) -> int:
    """
    Approximate TED computation for large trees.
    Uses a faster algorithm based on comparing structural characteristics.
    """
    def get_level_histogram(node, level=0, hist=None):
        if hist is None:
            hist = defaultdict(int)
        hist[level] += 1
        for child in node.children:
            get_level_histogram(child, level + 1, hist)
        return hist
    
    hist1 = get_level_histogram(tree1)
    hist2 = get_level_histogram(tree2)
    
    all_levels = set(hist1.keys()) | set(hist2.keys())
    level_diff = sum(abs(hist1.get(level, 0) - hist2.get(level, 0)) for level in all_levels)
    
    def get_label_counts(node, counts=None):
        """Counts nodes by type."""
        if counts is None:
            counts = defaultdict(int)
        counts[node.name] += 1
        for child in node.children:
            get_label_counts(child, counts)
        return counts
    
    counts1 = get_label_counts(tree1)
    counts2 = get_label_counts(tree2)
    
    all_labels = set(counts1.keys()) | set(counts2.keys())
    label_diff = sum(abs(counts1.get(label, 0) - counts2.get(label, 0)) for label in all_labels)
    
    approximate_dist = (level_diff + label_diff) // 2
    
    return approximate_dist


def tree_edit_distance(ground_truth_tree: Node, predicted_tree: Node, 
                      approximate=False) -> Tuple[int, float, float]:
    """
    Computes Tree Edit Distance (TED) between two trees.
    
    Parameters:
    - approximate: use approximate algorithm for large trees
    
    Returns: (distance, normalized_error, accuracy)
    """
    t1 = convert_to_apted_node(ground_truth_tree)
    t2 = convert_to_apted_node(predicted_tree)

    lenA = count_nodes(t1)
    lenB = count_nodes(t2)
    
    if approximate or (lenA > 1000 or lenB > 1000):
        print(f"    Using approximate algorithm (sizes: {lenA}, {lenB})")
        dist = approximate_ted(t1, t2)
    else:
        apted = APTED(t1, t2, AptNodeConfig())
        dist = apted.compute_edit_distance()
    
    max_len = max(lenA, lenB)
    error = dist / max_len if max_len > 0 else 0
    accuracy = 1 - error
    return dist, error, accuracy


def flatten_notes_in_tree(node: Node) -> Node:
    """
    Creates a flattened version of the tree where notes inside chords are unfolded.
    Used for TEDn.
    """
    def create_flattened(n: Node) -> Node:
        new_node = Node(n.label, n.id, [], n.value)
        
        if n.label == "Chord":
            for child in n.children:
                if child.label == "Duration":
                    new_node.add_child(Node("Duration", None, [], child.value))
            
            for child in n.children:
                if child.label == "Note":
                    note_node = Node("Note", None, [], child.value)
                    for note_child in child.children:
                        note_node.add_child(create_flattened(note_child))
                    new_node.add_child(note_node)
                elif child.label != "Duration":  # Duration already added
                    new_node.add_child(create_flattened(child))
        else:
            for child in n.children:
                new_node.add_child(create_flattened(child))
        
        return new_node
    
    return create_flattened(node)


def tree_edit_distance_normalized(ground_truth_tree: Node, predicted_tree: Node, 
                                  approximate=False) -> dict:
    """
    2.3. TEDn - Tree Edit Distance with Note Flattening
    
    Parameters:
    - approximate: use approximate algorithm for large trees
    """
    gt_flat = flatten_notes_in_tree(ground_truth_tree)
    pred_flat = flatten_notes_in_tree(predicted_tree)
    
    ted, ted_error, ted_accuracy = tree_edit_distance(
        gt_flat, pred_flat, 
        approximate=approximate
    )
    
    return {
        'tedn': ted,
        'normalized_error': ted_error,
        'accuracy': ted_accuracy,
        'gt_node_count': count_nodes(convert_to_apted_node(gt_flat)),
        'pred_node_count': count_nodes(convert_to_apted_node(pred_flat))
    }
