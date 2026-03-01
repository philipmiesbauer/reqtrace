"""
ReqIF Importer — parses a .reqif XML file and produces a .rqtr YAML file.

Supports the core ReqIF 1.0 / 1.1 subset:
  - SpecObjects   → requirements (id, title, description)
  - SpecRelations → derived_from links
"""
from pathlib import Path
from typing import Any, Dict, List, Union
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET  # pylint: disable=import-error
import yaml

# ReqIF XML namespaces (the namespace URI is the same across ReqIF 1.0 & 1.1)
_NS = "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"
_Q = f"{{{_NS}}}"  # shorthand for namespace-qualified tag prefix


def _tag(local: str) -> str:
    return f"{_Q}{local}"


def _find_value(values_el: Element) -> str:
    """Extract the first plain-text value found in a VALUES element."""
    # ReqIF stores values as ATTRIBUTE-VALUE-STRING, ATTRIBUTE-VALUE-XHTML, etc.
    for av in values_el:
        # The DEFINITION child holds a reference whose LONG-NAME matches attr_name
        defn = (
            av.find(f".//{_tag('ATTRIBUTE-DEFINITION-STRING-REF')}")
            or av.find(f".//{_tag('ATTRIBUTE-DEFINITION-XHTML-REF')}")
            or av.find(f".//{_tag('ATTRIBUTE-DEFINITION-ENUMERATION-REF')}")
        )
        if defn is not None:
            # We use the THE-VALUE attribute or inner text
            the_value = av.get("THE-VALUE")
            if the_value:
                return the_value.strip()
            # XHTML values are nested inside THE-VALUE element
            tv_el = av.find(f".//{_tag('THE-VALUE')}")
            if tv_el is not None:
                # Flatten all text content
                return "".join(tv_el.itertext()).strip()
    return ""


def _attr_defs(spec_types_el: Element) -> Dict[str, str]:
    """Build a map of ATTRIBUTE-DEFINITION IDENTIFIER → LONG-NAME."""
    mapping: Dict[str, str] = {}
    for spec_type in spec_types_el:
        for attr_def in spec_type:
            ident = attr_def.get("IDENTIFIER")
            long_name = attr_def.get("LONG-NAME")
            if ident and long_name:
                mapping[ident] = long_name
    return mapping


# pylint: disable=too-many-locals,too-many-branches
def parse_reqif(reqif_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Parse a ReqIF file and return a list of requirement dicts suitable for
    writing as a .rqtr YAML file.

    Returns:
        List of dicts with keys: id, title, description (optional),
        derived_from (optional).
    """
    # @trace-start: REQ-EXCHANGE-IMPORT
    path = Path(reqif_path)
    tree = ET.parse(path)
    root = tree.getroot()

    # Strip namespace from root tag if needed (ElementTree keeps them)
    core_content = root.find(_tag("CORE-CONTENT"))
    if core_content is None:
        # Try without namespace (some tools omit it)
        core_content = root.find("CORE-CONTENT")
    if core_content is None:
        raise ValueError(f"No CORE-CONTENT element found in '{path}'")

    req_if_content = core_content.find(_tag("REQ-IF-CONTENT"))
    if req_if_content is None:
        req_if_content = core_content.find("REQ-IF-CONTENT")
    if req_if_content is None:
        raise ValueError(f"No REQ-IF-CONTENT element found in '{path}'")

    spec_objects_el = req_if_content.find(_tag("SPEC-OBJECTS"))
    spec_relations_el = req_if_content.find(_tag("SPEC-RELATIONS"))

    # Build id → requirement dict
    requirements: Dict[str, Dict[str, Any]] = {}

    if spec_objects_el is not None:
        for spec_obj in spec_objects_el.findall(_tag("SPEC-OBJECT")):
            obj_id = spec_obj.get("IDENTIFIER", "").strip()
            long_name = spec_obj.get("LONG-NAME", "").strip()

            req: Dict[str, Any] = {"id": obj_id, "title": long_name}

            # Try to extract ATTRIBUTE-VALUEs for description
            values_el = spec_obj.find(_tag("VALUES"))
            if values_el is not None:
                desc = _find_value(values_el)
                if desc:
                    req["description"] = desc

            requirements[obj_id] = req

    # Process SpecRelations: SOURCE derives from TARGET
    if spec_relations_el is not None:
        for relation in spec_relations_el.findall(_tag("SPEC-RELATION")):
            source_el = relation.find(f".//{_tag('SOURCE')}/{_tag('SPEC-OBJECT-REF')}")
            target_el = relation.find(f".//{_tag('TARGET')}/{_tag('SPEC-OBJECT-REF')}")
            if source_el is not None and target_el is not None:
                src_id = source_el.text.strip() if source_el.text else ""
                tgt_id = target_el.text.strip() if target_el.text else ""
                if src_id in requirements and tgt_id:
                    derived = requirements[src_id].setdefault("derived_from", [])
                    if tgt_id not in derived:
                        derived.append(tgt_id)

    return list(requirements.values())
    # @trace-end: REQ-EXCHANGE-IMPORT


def import_reqif(reqif_path: Union[str, Path], output_path: Union[str, Path]) -> None:
    """
    Import a ReqIF file and write the resulting requirements as a .rqtr YAML file.

    Args:
        reqif_path:  Path to the source .reqif file.
        output_path: Path to write the output .rqtr file.
    """
    reqs = parse_reqif(reqif_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        yaml.dump(reqs, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
