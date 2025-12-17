import zipfile
import os
from lxml import etree
import tempfile
import shutil
from typing import Optional, List
from core.tempo_markings import contains_tempo_marking

ELEMENT_TO_INT_MAP = {
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
    'Dot': 19,
    'Text': 20,
    'Lyrics': 21,
    'Arpeggio': 22
}

class Node:
    def __init__(self, label: str, id: Optional[int] = None, children: Optional[List['Node']] = None, value: Optional[str] = None) -> None:
        self.label = label
        if label not in ELEMENT_TO_INT_MAP:
            raise ValueError(f"Unknown label '{label}'. Valid labels are: {list(ELEMENT_TO_INT_MAP.keys())}")
        self.int_label = ELEMENT_TO_INT_MAP[label]
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
        child_prefix = prefix + ("   " if is_last else "│  ")
        for i, child in enumerate(self.children):
            is_last_child = i == (len(self.children) - 1)
            lines.append(child._pretty(child_prefix, is_last_child))
        return "\n".join(lines)


def extract_xml_tree_from_mscz(mscz_path: str) -> etree._Element:
    temp_directory = tempfile.mkdtemp()
    try:
        if not os.path.exists(mscz_path):
            raise FileNotFoundError(f"File not found: {mscz_path}")
        try:
            with zipfile.ZipFile(mscz_path, 'r') as zip_file:
                zip_file.extractall(temp_directory)
        except zipfile.BadZipFile:
            raise ValueError(f"Invalid zip file: {mscz_path}")
        extracted_files = os.listdir(temp_directory)
        mscx_filename = None
        for file in extracted_files:
            if file.endswith('.mscx'):
                mscx_filename = file
                break

        if mscx_filename is None:
            raise ValueError(f".mscx file not found in archive {mscz_path}")

        mscx_file_path = os.path.join(temp_directory, mscx_filename)
        try:
            xml_tree = etree.parse(mscx_file_path)
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XML in file {mscx_file_path}: {e}")
        root = xml_tree.getroot()
        return root
    finally:
        try:
            shutil.rmtree(temp_directory)
        except OSError:
            pass

def create_simplified_tree(mscz_path: str) -> Node:
    xml_root = extract_xml_tree_from_mscz(mscz_path)
    parts = xml_root.findall("./Score/Part")
    staffs = xml_root.findall("./Score/Staff")
    root_node = Node("Score", id=0)

    part_counter = 0
    staff_counter = 0
    instrument_counter = 0
    default_clef_type = 'G'

    for part in parts:
        part_node = Node("Part", id=part_counter)
        root_node.add_child(part_node)
        part_counter += 1
        part_staffs = part.findall("./Staff")

        track_name_elements = part.xpath("./trackName")
        if len(track_name_elements) == 0:
            instrument_name = None
        else:
            instrument_name = track_name_elements[0].text
        part_node.add_child(Node("Instrument", id=instrument_counter, value=instrument_name))
        instrument_counter += 1

        for staff in part_staffs:
            if len(staff.xpath('isStaffVisible')) != 0:
                staff_counter += 1
                continue
            staff_node = Node("Staff", id=staff_counter)
            part_node.add_child(staff_node)
            if staff_counter >= len(staffs):
                staff_counter += 1
                continue

            if staff_counter == 0:
                for text_element in (xml_root.findall(".//Text") + xml_root.findall(".//StaffText") + xml_root.findall(".//SystemText")):
                    if len(text_element.xpath('visible')) == 0:
                        style_element = text_element.find("style")
                        text_node = text_element.find("text")
                        if text_node is not None:
                            text_content = "".join(text_node.itertext()).strip()
                            if text_content:
                                is_tempo, tempo_marking = contains_tempo_marking(text_content)
                                if is_tempo:
                                    staff_node.add_child(Node("Tempo", value=text_content))
                                else:
                                    staff_node.add_child(Node("Text", value=text_content))

            measures = staffs[staff_counter].xpath("Measure")
            staff_counter += 1
            measure_counter = 0
            chord_counter = 0
            rest_counter = 0

            clef_elements = staff.xpath("./defaultClef")
            if len(clef_elements) > 0:
                current_clef = clef_elements[0].text
            else:
                current_clef = default_clef_type

            if len(measures) > 0:
                first_measure_clefs = measures[0].xpath("./voice/Clef")
                if len(first_measure_clefs) > 0:
                    concert_clef_element = first_measure_clefs[0].find('concertClefType')
                    if concert_clef_element is not None and concert_clef_element.text is not None:
                        first_clef = concert_clef_element.text
                        if current_clef != first_clef:
                            current_clef = first_clef
            staff_node.add_child(Node("Clef", value=current_clef))

            for measure in measures:
                measure_node = Node("Measure", id=measure_counter)
                measure_counter += 1
                staff_node.add_child(measure_node)

                key_signatures = measure.xpath('voice/KeySig')
                if len(key_signatures) > 0:
                    for key_sig in key_signatures:
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

                time_signatures = measure.xpath('voice/TimeSig')
                if len(time_signatures) > 0:
                    for time_sig in time_signatures:
                        if len(time_sig.xpath('visible')) == 0:
                            numerator_element = time_sig.find('sigN')
                            denominator_element = time_sig.find('sigD')
                            if numerator_element is not None and denominator_element is not None:
                                numerator = numerator_element.text
                                denominator = denominator_element.text
                                if numerator is not None and denominator is not None:
                                    time_node = Node("TimeSig", value=f"{numerator}/{denominator}")
                                    measure_node.add_child(time_node)

                dynamics = measure.xpath('voice/Dynamic')
                if len(dynamics) > 0:
                    for dynamic in dynamics:
                        if len(dynamic.xpath('visible')) == 0:
                            subtype_element = dynamic.find('subtype')
                            if subtype_element is not None and subtype_element.text is not None:
                                dynamic_value = subtype_element.text
                                dynamic_node = Node("Dynamic", value=dynamic_value)
                                measure_node.add_child(dynamic_node)

                tempo_elements = measure.xpath('voice/Tempo')
                if len(tempo_elements) > 0:
                    for tempo in tempo_elements:
                        if len(tempo.xpath('visible')) == 0:
                            text_element = tempo.find('text')
                            if text_element is not None:
                                tempo_text = "".join(text_element.itertext()).strip()
                                tempo_node = Node("Tempo", value=tempo_text)
                                staff_node.add_child(tempo_node)

                measure_clefs = measure.xpath("./voice/Clef")
                if len(measure_clefs) > 0:
                    for measure_clef in measure_clefs:
                        if len(measure_clef.xpath('visible')) == 0:
                            concert_clef_element = measure_clef.find('concertClefType')
                            if concert_clef_element is not None and concert_clef_element.text is not None:
                                clef_value = concert_clef_element.text
                                if clef_value != current_clef:
                                    clef_node = Node("Clef", value=clef_value)
                                    measure_node.add_child(clef_node)
                                    current_clef = clef_value

                voices = measure.xpath("./voice")
                for voice in voices:
                    for element in voice:
                        if element.tag == "Chord" and len(element.xpath('visible')) == 0:
                            chord_node = Node("Chord", id=chord_counter)
                            measure_node.add_child(chord_node)
                            duration_element = element.find('durationType')
                            if duration_element is not None and duration_element.text is not None:
                                duration_value = duration_element.text
                                chord_node.add_child(Node("Duration", value=duration_value))
                            if len(element.xpath('dots')) > 0:
                                chord_node.add_child(Node("Dot"))
                            spanner_elements = element.xpath('Spanner')
                            if len(spanner_elements) > 0:
                                for spanner in spanner_elements:
                                    if len(spanner.xpath('visible')) == 0:
                                        spanner_type = spanner.attrib.get('type')
                                        if spanner_type is not None:
                                            spanner_node = Node("Spanner", value=spanner_type)
                                            chord_node.add_child(spanner_node)
                            articulation_elements = element.xpath('Articulation')
                            if len(articulation_elements) > 0:
                                for articulation in articulation_elements:
                                    if len(articulation.xpath('visible')) == 0:
                                        subtype_element = articulation.find('subtype')
                                        if subtype_element is not None and subtype_element.text is not None:
                                            articulation_type = subtype_element.text
                                            articulation_node = Node("Articulation", value=articulation_type)
                                            chord_node.add_child(articulation_node)
                            ornament_elements = element.xpath('Ornament')
                            if len(ornament_elements) > 0:
                                for ornament in ornament_elements:
                                    if len(ornament.xpath('visible')) == 0:
                                        subtype_element = ornament.find('subtype')
                                        if subtype_element is not None and subtype_element.text is not None:
                                            ornament_type = subtype_element.text
                                            ornament_node = Node("Articulation", value=ornament_type)
                                            chord_node.add_child(ornament_node)
                            lyric_elements = element.xpath('Lyrics')
                            if len(lyric_elements) > 0:
                                for lyric in lyric_elements:
                                    if len(lyric.xpath('visible')) == 0:
                                        text_element = lyric.find('text')
                                        if text_element is not None and text_element.text is not None:
                                            lyric_text = text_element.text
                                            lyric_node = Node("Lyrics", value=lyric_text)
                                            chord_node.add_child(lyric_node)
                            arpeggio_elements = element.xpath('Arpeggio')
                            if len(arpeggio_elements) > 0:
                                for arpeggio in arpeggio_elements:
                                    if len(arpeggio.xpath('visible')) == 0:
                                        subtype_element = arpeggio.find('subtype')
                                        if subtype_element is not None and subtype_element.text is not None:
                                            arpeggio_type = subtype_element.text
                                            arpeggio_node = Node("Arpeggio", value=arpeggio_type)
                                            chord_node.add_child(arpeggio_node)
                            chord_counter += 1
                            note_elements = element.xpath('Note')
                            for note in note_elements:
                                pitch_element = note.find('pitch')
                                if pitch_element is not None and pitch_element.text is not None:
                                    note_node = Node("Note", value=pitch_element.text)
                                    chord_node.add_child(note_node)
                                    accidental_elements = note.xpath('Accidental')
                                    if len(accidental_elements) > 0:
                                        if len(accidental_elements[0].xpath('visible')) == 0:
                                            subtype_element = accidental_elements[0].find('subtype')
                                            if subtype_element is not None and subtype_element.text is not None:
                                                note_node.add_child(Node("Accidental", value=subtype_element.text))
                                    note_spanner_elements = note.xpath('Spanner')
                                    if len(note_spanner_elements) > 0:
                                        for note_spanner in note_spanner_elements:
                                            if len(note_spanner.xpath('visible')) == 0:
                                                spanner_type = note_spanner.attrib.get('type')
                                                if spanner_type is not None:
                                                    spanner_node = Node("Spanner", value=spanner_type)
                                                    note_node.add_child(spanner_node)
                        if element.tag == "Rest" and len(element.xpath('visible')) == 0:
                            rest_node = Node("Rest", id=rest_counter)
                            measure_node.add_child(rest_node)
                            duration_element = element.find('durationType')
                            if duration_element is not None and duration_element.text is not None:
                                duration_value = duration_element.text
                                rest_node.add_child(Node("Duration", value=duration_value))
                            rest_counter += 1
                        if element.tag == 'Spanner' and len(element.xpath('visible')) == 0:
                            spanner_type = element.attrib.get('type')
                            if spanner_type is not None:
                                spanner_node = Node("Spanner", value=spanner_type)
                                measure_node.add_child(spanner_node)
                        if element.tag == 'Fermata' and len(element.xpath('visible')) == 0:
                            subtype_element = element.find('subtype')
                            if subtype_element is not None and subtype_element.text is not None:
                                fermata_type = subtype_element.text
                                fermata_node = Node("Fermata", value=fermata_type)
                                measure_node.add_child(fermata_node)
                        if element.tag == 'HairPin' and len(element.xpath('visible')) == 0:
                            spanner_node = Node("Spanner", value='HairPin')
                            measure_node.add_child(spanner_node)
                        if element.tag == 'Tuplet' and len(element.xpath('visible')) == 0:
                            normal_notes_element = element.find('normalNotes')
                            actual_notes_element = element.find('actualNotes')
                            base_notes_element = element.find('baseNote')
                            if (normal_notes_element is not None and normal_notes_element.text is not None and
                                actual_notes_element is not None and actual_notes_element.text is not None and
                                base_notes_element is not None and base_notes_element.text is not None):
                                normal_notes = normal_notes_element.text
                                actual_notes = actual_notes_element.text
                                base_notes = base_notes_element.text
                                tuplet_node = Node("Tuplet", value=f"{normal_notes}/{actual_notes}/{base_notes}")
                                measure_node.add_child(tuplet_node)
    return root_node
