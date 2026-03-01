"""
Tests for reqtrace-exchange: ReqIF import and export.
"""
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path
import yaml

from reqtrace.exchange.reqif_importer import parse_reqif, import_reqif
from reqtrace.exchange.reqif_exporter import build_reqif, export_reqif


# ---------------------------------------------------------------------------
# Minimal hand-crafted ReqIF XML for testing imports
# ---------------------------------------------------------------------------
_MINIMAL_REQIF = textwrap.dedent(
    """\
    <?xml version="1.0" encoding="UTF-8"?>
    <REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
      <THE-HEADER>
        <REQ-IF-HEADER IDENTIFIER="_HDR001"
                       CREATION-TIME="2026-01-01T00:00:00+00:00"
                       TITLE="Test" REQ-IF-VERSION="1.1"
                       SOURCE-TOOL-ID="test" REQ-IF-TOOL-ID="test"/>
      </THE-HEADER>
      <CORE-CONTENT>
        <REQ-IF-CONTENT>
          <DATATYPES/>
          <SPEC-TYPES/>
          <SPEC-OBJECTS>
            <SPEC-OBJECT IDENTIFIER="SYS-001" LONG-NAME="System Requirement">
              <TYPE/>
              <VALUES/>
            </SPEC-OBJECT>
            <SPEC-OBJECT IDENTIFIER="REQ-001" LONG-NAME="Child Requirement">
              <TYPE/>
              <VALUES/>
            </SPEC-OBJECT>
          </SPEC-OBJECTS>
          <SPEC-RELATIONS>
            <SPEC-RELATION IDENTIFIER="_REL001" LAST-CHANGE="2026-01-01T00:00:00+00:00">
              <TYPE/>
              <SOURCE>
                <SPEC-OBJECT-REF>REQ-001</SPEC-OBJECT-REF>
              </SOURCE>
              <TARGET>
                <SPEC-OBJECT-REF>SYS-001</SPEC-OBJECT-REF>
              </TARGET>
            </SPEC-RELATION>
          </SPEC-RELATIONS>
          <SPEC-RELATION-GROUPS/>
          <SPECIFICATIONS/>
        </REQ-IF-CONTENT>
      </CORE-CONTENT>
    </REQ-IF>
    """
)


def _write_reqif(tmp_path: Path, content: str = _MINIMAL_REQIF) -> Path:
    p = tmp_path / "test.reqif"
    p.write_text(content, encoding="utf-8")
    return p


def _write_rqtr(tmp_path: Path, reqs) -> Path:
    p = tmp_path / "test.rqtr"
    with open(p, "w", encoding="utf-8") as f:
        yaml.dump(reqs, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return p


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------


def test_parse_reqif_basic(tmp_path):
    """parse_reqif returns one dict per SpecObject."""
    reqif_path = _write_reqif(tmp_path)
    reqs = parse_reqif(reqif_path)
    ids = [r["id"] for r in reqs]
    assert "SYS-001" in ids
    assert "REQ-001" in ids


def test_parse_reqif_titles(tmp_path):
    """LONG-NAME is mapped to the title field."""
    reqif_path = _write_reqif(tmp_path)
    reqs = parse_reqif(reqif_path)
    by_id = {r["id"]: r for r in reqs}
    assert by_id["SYS-001"]["title"] == "System Requirement"
    assert by_id["REQ-001"]["title"] == "Child Requirement"


def test_parse_reqif_relations(tmp_path):
    """SpecRelations are converted to derived_from lists."""
    reqif_path = _write_reqif(tmp_path)
    reqs = parse_reqif(reqif_path)
    by_id = {r["id"]: r for r in reqs}
    assert by_id["REQ-001"].get("derived_from") == ["SYS-001"]


def test_import_reqif_writes_rqtr(tmp_path):
    """import_reqif writes a valid YAML file."""
    reqif_path = _write_reqif(tmp_path)
    out_path = tmp_path / "out.rqtr"
    import_reqif(reqif_path, out_path)
    assert out_path.exists()
    with open(out_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, list)
    assert len(data) == 2


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------


def test_build_reqif_contains_identifiers():
    """build_reqif produces XML containing the requirement identifiers."""
    reqs = [
        {"id": "SYS-001", "title": "System Req"},
        {"id": "REQ-001", "title": "Child Req", "derived_from": ["SYS-001"]},
    ]
    tree = build_reqif(reqs)
    root = tree.getroot()
    xml_str = ET.tostring(root, encoding="unicode")

    assert "SYS-001" in xml_str
    assert "REQ-001" in xml_str
    assert "System Req" in xml_str


def test_export_reqif_writes_file(tmp_path):
    """export_reqif writes a .reqif XML file that is parseable."""
    reqs = [{"id": "SYS-001", "title": "System Req", "description": "A system requirement."}]
    rqtr_path = _write_rqtr(tmp_path, reqs)
    out_path = tmp_path / "out.reqif"
    export_reqif(rqtr_path, out_path)
    assert out_path.exists()
    # Parse it back — must be valid XML
    tree = ET.parse(out_path)
    assert tree.getroot() is not None


# ---------------------------------------------------------------------------
# Round-trip test
# ---------------------------------------------------------------------------


def test_roundtrip(tmp_path):
    """Export .rqtr → .reqif, then import back → check IDs are preserved."""
    original_reqs = [
        {"id": "SYS-001", "title": "System Requirement"},
        {"id": "REQ-001", "title": "Child Requirement", "derived_from": ["SYS-001"]},
    ]
    rqtr_path = _write_rqtr(tmp_path, original_reqs)
    reqif_path = tmp_path / "round_trip.reqif"
    rqtr_reimport_path = tmp_path / "reimported.rqtr"

    export_reqif(rqtr_path, reqif_path)
    import_reqif(reqif_path, rqtr_reimport_path)

    with open(rqtr_reimport_path, encoding="utf-8") as f:
        reimported = yaml.safe_load(f)

    reimported_ids = {r["id"] for r in reimported}
    assert "SYS-001" in reimported_ids
    assert "REQ-001" in reimported_ids
