import zipfile
import os
from lxml import etree
import tempfile
import shutil
from typing import Optional, List

score_element_to_dict = {
    'Score': 0,
    'Part': 1,
    'Staff': 2,
    'Instrument': 3,
    'Clef': 4,
    'KeySig': 5,
    'TimeSig': 6,
    'Dynamic': 7,
    'Tempo': 8,
    'Measure': 9,
    'Chord': 10,
    'Rest': 11,
    'Note': 12,
    'Tuplet': 13,
    'Fermata': 14,
    'Spanner': 15,
    'Accidental': 16,
    'Duration': 17,
    'Articulation': 18,
    'hasDot': 19,
    'Text': 20,
    'Lyrics': 21
}
class Node:
    def __init__(self, label: str, id: Optional[int] = None, children: Optional[List['Node']] = None, value: Optional[str] = None) -> None:
        """
        Initialize a Node in the score tree.
        
        Args:
            label: The label/type of the node (e.g., 'Score', 'Part', 'Staff', etc.)
            id: Optional identifier for the node
            children: Optional list of child nodes
            value: Optional value associated with the node
        
        Returns:
            None
        """
        self.label = label
        self.int_label = score_element_to_dict[label]
        self.id = id
        self.children = children or []
        self.value = value

    def add_child(self, node: 'Node') -> None:
        self.children.append(node)

    def __str__(self) -> str:
        return self._pretty()

    def _pretty(self, prefix: str = "", is_last: bool = True) -> str:
        connector = "└─ " if is_last else "├─ "
        line = prefix + connector + self.label

        if self.id is not None:
            line += f" id={self.id}"
        if self.value:
            line += f" value={self.value}"

        lines = [line]
        prefix_child = prefix + ("   " if is_last else "│  ")
        for i, child in enumerate(self.children):
            last = i == (len(self.children) - 1)
            lines.append(child._pretty(prefix_child, last))
        return "\n".join(lines)


def extract_tree_from_mscz(mscz_path: str) -> etree._Element:
    tmp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(mscz_path, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)
    extracted_files = os.listdir(tmp_dir)
    mscx_file_name = None
    for extracted_file in extracted_files:
        if extracted_file.endswith('.mscx'):
            mscx_file_name = extracted_file
            break
    
    if mscx_file_name is None:
        raise ValueError(f".mscx file not found in archive {mscz_path}")
    
    mscx_file_path = os.path.join(tmp_dir, mscx_file_name)
    tree = etree.parse(mscx_file_path)
    root = tree.getroot()
    shutil.rmtree(tmp_dir)
    return root

def create_simplified_tree(mscz_path: str) -> Node:
    root = extract_tree_from_mscz(mscz_path)
    score_parts = root.findall("./Score/Part") 
    score_staffs = root.findall("./Score/Staff")
    score_node = Node("Score", id=0)
    for text_elem in root.findall(".//Text"):
        if len(text_elem.xpath('visible')) == 0:
            text_type = text_elem.find("style")
            text_type_value = text_type.text if text_type is not None else None
            text_node = text_elem.find("text")
            if text_node is not None:
                text_value = "".join(text_node.itertext()).strip()
                if text_value:
                    score_node.add_child(Node("Text", value=text_value))
    part_id = 0
    staff_id = 0
    instrument_id = 0
    default_clef = 'G'
    for part in score_parts:
        part_node = Node("Part", id=part_id)
        score_node.add_child(part_node)
        part_id += 1
        part_staffs = part.findall("./Staff")
        instrument_name = part.xpath("./trackName")[0].text
        part_node.add_child(Node("Instrument", id=instrument_id, value=instrument_name))
        instrument_id += 1
        for staff in part_staffs:
            staff_node = Node("Staff", id=staff_id)
            part_node.add_child(staff_node)
            staff_measures = score_staffs[staff_id].xpath("Measure")
            staff_id += 1
            measure_id = 0
            chord_id = 0
            rest_id = 0

            clefs = staff.xpath("./defaultClef")
            if len(clefs) > 0:
                staff_clef = clefs[0].text
            else:
                first_measure_clefs = staff_measures[0].xpath("./voice/Clef")
                if len(first_measure_clefs) > 0:
                    staff_clef = first_measure_clefs[0].find('concertClefType').text
                else:
                    staff_clef = default_clef
            staff_node.add_child(Node("Clef", value=staff_clef))

            for measure in staff_measures:
                measure_node = Node("Measure", id=measure_id)
                measure_id += 1
                staff_node.add_child(measure_node)
                keysigs = measure.xpath('voice/KeySig')
                if len(keysigs) > 0:
                    for key_sig in keysigs:
                        if len(key_sig.xpath('visible')) == 0:
                            accidental_elements = key_sig.xpath('accidental')
                            concert_key_elements = key_sig.xpath('concertKey')
                            key_value = None
                            if len(accidental_elements) > 0:
                                key_value = accidental_elements[0].text
                            elif len(concert_key_elements) > 0:
                                key_value = concert_key_elements[0].text
                            if key_value is not None:
                                key_node = Node("KeySig", value=key_value)
                                measure_node.add_child(key_node)
                timesigs = measure.xpath('voice/TimeSig')
                if len(timesigs) > 0:
                    for time_sig in timesigs:
                        if len(time_sig.xpath('visible')) == 0:
                            time_signature_numerator = time_sig.find('sigN').text
                            time_signature_denominator = time_sig.find('sigD').text
                            time_node = Node("TimeSig", value=f"{time_signature_numerator}/{time_signature_denominator}")
                            measure_node.add_child(time_node)
                dynamics = measure.xpath('voice/Dynamic')
                if len(dynamics) > 0:
                    for dynamic in dynamics:
                        if len(dynamic.xpath('visible')) == 0:
                            dynamic_value = dynamic.find('subtype').text
                            dynamic_node = Node("Dynamic", value=dynamic_value)
                            measure_node.add_child(dynamic_node)
                tempo_list = measure.xpath('voice/Tempo')
                if len(tempo_list) > 0:
                    for tempo in tempo_list:
                        if len(tempo.xpath('visible')) == 0:
                            text_elem = tempo.find('text')
                            if text_elem is not None:
                                full_text = "".join(text_elem.itertext()).strip()
                                tempo_node = Node("Tempo", value=full_text)
                                measure_node.add_child(tempo_node)
                                
                measure_clefs = measure.xpath("./voice/Clef")
                if len(measure_clefs) > 0:
                    for measure_clef in measure_clefs:
                        if len(measure_clef.xpath('visible')) == 0:
                            measure_clef_value = measure_clef.find('concertClefType').text
                            if measure_clef_value != staff_clef:
                                measure_clef_node = Node("Clef", value=measure_clef_value)
                                measure_node.add_child(measure_clef_node)
                                staff_clef = measure_clef_value
                voices = measure.findall("./voice")
                for voice in voices:
                    for element in voice:
                        if element.tag == "Chord" and len(element.xpath('visible')) == 0:
                            chord_node = Node("Chord", id=chord_id)
                            measure_node.add_child(chord_node)
                            chord_duration = element.find('durationType').text
                            chord_node.add_child(Node("Duration", value=chord_duration))
                            if len(element.xpath('dots')) > 0:
                                chord_node.add_child(Node("hasDot"))
                            spanners = element.xpath('Spanner')
                            if len(spanners) > 0:
                                for spanner in spanners:
                                    spanner_type = spanner.attrib['type']
                                    spanner_node = Node("Spanner", value=spanner_type)
                                    chord_node.add_child(spanner_node)
                            articulations = element.xpath('Articulation')
                            if len(articulations) > 0:
                                for articulation in articulations:
                                    articulation_type = articulation.find('subtype').text
                                    articulation_node = Node("Articulation", value=articulation_type)
                                    chord_node.add_child(articulation_node)
                            ornaments = element.xpath('Ornament')
                            if len(ornaments) > 0:
                                for ornament in ornaments:
                                    ornament_type = ornament.find('subtype').text
                                    ornament_node = Node("Articulation", value=ornament_type)
                                    chord_node.add_child(ornament_node)
                            lyrics = element.xpath('Lyrics')
                            if len(lyrics) > 0:
                                for lyric in lyrics:
                                    lyric_text = lyric.find('text').text
                                    lyric_node = Node("Lyrics", value=lyric_text)
                                    chord_node.add_child(lyric_node)
                            chord_id += 1
                            notes = element.xpath('Note')
                            for note in notes:
                                note_node = Node("Note", value=note.find('pitch').text)
                                chord_node.add_child(note_node)
                                accidental = note.xpath('Accidental')
                                if len(accidental) > 0:
                                    note_node.add_child(Node("Accidental", value=accidental[0].find('subtype').text))
                                note_spanners = note.xpath('Spanner')
                                if len(note_spanners) > 0:
                                    for note_spanner in note_spanners:
                                        note_spanner_type = note_spanner.attrib['type']
                                        note_spanner_node = Node("Spanner", value=note_spanner_type)
                                        note_node.add_child(note_spanner_node)
                        if element.tag == "Rest" and len(element.xpath('visible')) == 0:
                            rest_node = Node("Rest", id=rest_id)
                            measure_node.add_child(rest_node)
                            rest_duration = element.find('durationType').text
                            rest_node.add_child(Node("Duration", value=rest_duration))
                            rest_id += 1
                        if element.tag == 'Spanner' and len(element.xpath('visible')) == 0:
                            spanner_type = element.attrib['type']
                            spanner_node = Node("Spanner", value=spanner_type)
                            measure_node.add_child(spanner_node)
                        if element.tag == 'Fermata' and len(element.xpath('visible')) == 0:
                            fermata_type = element.find('subtype').text
                            fermata_node = Node("Fermata", value=fermata_type)
                            measure_node.add_child(fermata_node)
                        if element.tag == 'HairPin' and len(element.xpath('visible')) == 0:
                            spanner_node = Node("Spanner", value='HairPin')
                            measure_node.add_child(spanner_node)
                        if element.tag == 'Tuplet' and len(element.xpath('visible')) == 0:
                            normal_notes = element.find('normalNotes').text
                            actual_notes = element.find('actualNotes').text
                            base_notes = element.find('baseNote').text
                            tuplet_node = Node("Tuplet", value=f"{normal_notes}/{actual_notes}/{base_notes}")
                            measure_node.add_child(tuplet_node)
    
    return score_node
