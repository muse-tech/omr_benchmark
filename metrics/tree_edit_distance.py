from apted import APTED, Config
from collections import defaultdict
from typing import Tuple, List
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

def approximate_ted_by_levels(tree1: AptNode, tree2: AptNode) -> int:
    def get_nodes_by_level(node: AptNode, level=0, levels_dict=None):
        if levels_dict is None:
            levels_dict = defaultdict(list)
        levels_dict[level].append(node)
        for child in node.children:
            get_nodes_by_level(child, level + 1, levels_dict)
        return levels_dict
    
    def sequence_edit_distance_with_operations(seq1: List, seq2: List):
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],
                        dp[i][j-1],
                        dp[i-1][j-1]
                    )
        operations = []
        i, j = m, n
        while i > 0 or j > 0:
            if i > 0 and j > 0 and seq1[i-1] == seq2[j-1]:
                operations.append(('match', i-1, j-1, seq1[i-1]))
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
                operations.append(('substitute', i-1, j-1, seq1[i-1], seq2[j-1]))
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                operations.append(('delete', i-1, seq1[i-1]))
                i -= 1
            else:
                operations.append(('insert', j-1, seq2[j-1]))
                j -= 1
        operations.reverse()
        return dp[m][n], operations
    
    levels1 = get_nodes_by_level(tree1)
    levels2 = get_nodes_by_level(tree2)
    all_levels = set(levels1.keys()) | set(levels2.keys())
    total_dist = 0
    for level in sorted(all_levels):
        seq1 = [node.name for node in levels1.get(level, [])]
        seq2 = [node.name for node in levels2.get(level, [])]
        level_dist, operations = sequence_edit_distance_with_operations(seq1, seq2)
        total_dist += level_dist
    return total_dist

def tree_edit_distance(ground_truth_tree: Node, predicted_tree: Node,
                      approximate=False) -> Tuple[int, float, float]:
    t1 = convert_to_apted_node(ground_truth_tree)
    t2 = convert_to_apted_node(predicted_tree)

    lenA = count_nodes(t1)
    lenB = count_nodes(t2)
    if approximate:
        print(f"    Using approximate algorithm (sizes: {lenA}, {lenB})")
        dist = approximate_ted_by_levels(t1, t2)
    else:
        apted = APTED(t1, t2, AptNodeConfig())
        dist = apted.compute_edit_distance()
    max_len = max(lenA, lenB)
    error = dist / max_len if max_len > 0 else 0
    accuracy = 1 - error
    return dist, error, accuracy

def flatten_notes_in_tree(node: Node) -> Node:
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
                elif child.label != "Duration":
                    new_node.add_child(create_flattened(child))
        else:
            for child in n.children:
                new_node.add_child(create_flattened(child))
        return new_node
    return create_flattened(node)

def tree_edit_distance_normalized(ground_truth_tree: Node, predicted_tree: Node,
                                  approximate=False) -> dict:
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
