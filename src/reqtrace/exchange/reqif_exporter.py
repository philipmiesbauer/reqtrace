"""
ReqIF Exporter — converts .rqtr YAML requirement files to ReqIF XML.

Produces a ReqIF 1.1 document with:
  - One SpecType (SPEC-OBJECT-TYPE) with Title and Description attribute definitions
  - One SpecObject per requirement
  - SpecRelations for derived_from links
"""
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Union

import yaml

_NS = "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"
_XHTML_NS = "http://www.w3.org/1999/xhtml"
_CREATION_TIME_FMT = "%Y-%m-%dT%H:%M:%S+00:00"


def _now() -> str:
    return datetime.now(tz=timezone.utc).strftime(_CREATION_TIME_FMT)


def _uid() -> str:
    return f"_{uuid.uuid4().hex.upper()}"


def _el(parent: ET.Element, local_tag: str, attribs: Dict[str, str]) -> ET.Element:
    """Create a namespace-qualified sub-element with the given attributes dict."""
    child = ET.SubElement(parent, f"{{{_NS}}}{local_tag}")
    for k, v in attribs.items():
        child.set(k, v)
    return child


# pylint: disable=too-many-locals,too-many-statements
def build_reqif(requirements: List[Dict[str, Any]], tool_id: str = "reqtrace-exchange") -> ET.ElementTree:
    """
    Build a ReqIF XML ElementTree from a list of requirement dicts.

    Args:
        requirements: List of dicts with keys: id, title, description (opt),
                      derived_from (opt).
        tool_id:      Identifier string embedded in the ReqIF header.

    Returns:
        An ElementTree representing the ReqIF document.
    """
    ET.register_namespace("", _NS)
    ET.register_namespace("xhtml", _XHTML_NS)

    root = ET.Element(f"{{{_NS}}}REQ-IF")
    # Note: do NOT call root.set("xmlns", ...) — ElementTree adds the xmlns
    # declaration automatically from register_namespace when serialising.

    # --- THE-HEADER ---
    header_el = _el(root, "THE-HEADER", {})
    _el(
        header_el,
        "REQ-IF-HEADER",
        {
            "IDENTIFIER": _uid(),
            "CREATION-TIME": _now(),
            "REPOSITORY-ID": tool_id,
            "REQ-IF-TOOL-ID": tool_id,
            "REQ-IF-VERSION": "1.1",
            "SOURCE-TOOL-ID": tool_id,
            "TITLE": "reqtrace export",
        },
    )

    # --- CORE-CONTENT ---
    core = _el(root, "CORE-CONTENT", {})
    content = _el(core, "REQ-IF-CONTENT", {})

    # DATATYPES
    datatypes_el = _el(content, "DATATYPES", {})
    dt_string_id = _uid()
    _el(
        datatypes_el,
        "DATATYPE-DEFINITION-STRING",
        {
            "IDENTIFIER": dt_string_id,
            "LAST-CHANGE": _now(),
            "LONG-NAME": "String",
            "MAX-LENGTH": "10000",
        },
    )

    # SPEC-TYPES — one generic object type
    spec_types_el = _el(content, "SPEC-TYPES", {})
    spec_obj_type_id = _uid()
    sot = _el(
        spec_types_el,
        "SPEC-OBJECT-TYPE",
        {
            "IDENTIFIER": spec_obj_type_id,
            "LAST-CHANGE": _now(),
            "LONG-NAME": "Requirement",
        },
    )
    attrs_el = _el(sot, "SPEC-ATTRIBUTES", {})

    # Title and Description attribute definitions
    title_attr_id = _uid()
    desc_attr_id = _uid()
    for attr_id, attr_name in [(title_attr_id, "Title"), (desc_attr_id, "Description")]:
        ad = _el(
            attrs_el,
            "ATTRIBUTE-DEFINITION-STRING",
            {
                "IDENTIFIER": attr_id,
                "LAST-CHANGE": _now(),
                "LONG-NAME": attr_name,
            },
        )
        td = _el(ad, "TYPE", {})
        ref = ET.SubElement(td, f"{{{_NS}}}DATATYPE-DEFINITION-STRING-REF")
        ref.text = dt_string_id

    # SPEC-OBJECTS
    spec_objects_el = _el(content, "SPEC-OBJECTS", {})
    id_to_identifier: Dict[str, str] = {}

    for req in requirements:
        req_id: str = req.get("id", "")
        title: str = req.get("title", "")
        description: str = req.get("description", "")

        obj_identifier = req_id  # use the reqtrace ID directly as the ReqIF IDENTIFIER
        id_to_identifier[req_id] = obj_identifier

        so = _el(
            spec_objects_el,
            "SPEC-OBJECT",
            {
                "IDENTIFIER": obj_identifier,
                "LAST-CHANGE": _now(),
                "LONG-NAME": title,
            },
        )

        # Type reference
        tp = _el(so, "TYPE", {})
        ref = ET.SubElement(tp, f"{{{_NS}}}SPEC-OBJECT-TYPE-REF")
        ref.text = spec_obj_type_id

        # Values
        vals = _el(so, "VALUES", {})

        # Title attribute value
        av_title = _el(vals, "ATTRIBUTE-VALUE-STRING", {"THE-VALUE": title})
        defn_t = _el(av_title, "DEFINITION", {})
        r = ET.SubElement(defn_t, f"{{{_NS}}}ATTRIBUTE-DEFINITION-STRING-REF")
        r.text = title_attr_id

        # Description attribute value (optional)
        if description:
            av_desc = _el(vals, "ATTRIBUTE-VALUE-STRING", {"THE-VALUE": description})
            defn_d = _el(av_desc, "DEFINITION", {})
            rd = ET.SubElement(defn_d, f"{{{_NS}}}ATTRIBUTE-DEFINITION-STRING-REF")
            rd.text = desc_attr_id

    # SPEC-RELATION-GROUPS (empty placeholder)
    _el(content, "SPEC-RELATION-GROUPS", {})

    # SPEC-RELATIONS — derived_from links
    spec_relations_el = _el(content, "SPEC-RELATIONS", {})
    for req in requirements:
        req_id = req.get("id", "")
        for parent_id in req.get("derived_from", []):
            rel = _el(
                spec_relations_el,
                "SPEC-RELATION",
                {
                    "IDENTIFIER": _uid(),
                    "LAST-CHANGE": _now(),
                },
            )
            _el(rel, "TYPE", {})
            src_el = _el(rel, "SOURCE", {})
            src_ref = ET.SubElement(src_el, f"{{{_NS}}}SPEC-OBJECT-REF")
            src_ref.text = id_to_identifier.get(req_id, req_id)
            tgt_el = _el(rel, "TARGET", {})
            tgt_ref = ET.SubElement(tgt_el, f"{{{_NS}}}SPEC-OBJECT-REF")
            tgt_ref.text = id_to_identifier.get(parent_id, parent_id)

    # SPECIFICATIONS (empty)
    _el(content, "SPECIFICATIONS", {})

    ET.indent(root, space="  ")
    return ET.ElementTree(root)


def export_reqif(rqtr_path: Union[str, Path], output_path: Union[str, Path]) -> None:
    """
    Export a .rqtr YAML file to a ReqIF XML file.

    Args:
        rqtr_path:   Path to the source .rqtr file.
        output_path: Path to write the output .reqif file.
    """
    # @trace-start: REQ-EXCHANGE-EXPORT
    rqtr = Path(rqtr_path)
    with open(rqtr, "r", encoding="utf-8") as f:
        requirements: List[Dict[str, Any]] = yaml.safe_load(f)

    if not isinstance(requirements, list):
        raise ValueError(f"Expected a list of requirements in '{rqtr}', got {type(requirements).__name__}")

    tree = build_reqif(requirements)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Write with XML declaration
    tree.write(out, encoding="utf-8", xml_declaration=True)
    # @trace-end: REQ-EXCHANGE-EXPORT
