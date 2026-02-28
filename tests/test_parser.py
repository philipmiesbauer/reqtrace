import pytest
from reqtrace.models import Requirement, RequirementIndex
from reqtrace.parser import parse_requirements

def test_valid_requirements():
    data = [
        {"id": "SYS-001", "title": "System 1"},
        {"id": "REQ-001", "title": "Req 1", "derived_from": ["SYS-001"]}
    ]
    index = parse_requirements(data)
    
    assert len(index.requirements) == 2
    assert index.get("SYS-001") is not None
    assert index.get("REQ-001").derived_from == ["SYS-001"]

def test_missing_parent_validation():
    data = [
        {"id": "REQ-001", "title": "Req 1", "derived_from": ["SYS-999"]}
    ]
    with pytest.raises(ValueError, match="derives from unknown requirement"):
        parse_requirements(data)

def test_cyclic_dependency_validation():
    data = [
        {"id": "REQ-001", "title": "Req 1", "derived_from": ["REQ-002"]},
        {"id": "REQ-002", "title": "Req 2", "derived_from": ["REQ-001"]}
    ]
    with pytest.raises(ValueError, match="Cyclic dependency detected"):
        parse_requirements(data)

def test_duplicate_id_validation():
    data = [
        {"id": "REQ-001", "title": "First"},
        {"id": "REQ-001", "title": "Duplicate"}
    ]
    with pytest.raises(ValueError, match="already exists"):
        parse_requirements(data)
