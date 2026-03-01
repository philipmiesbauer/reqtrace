"""
JSON Schema definition for .rqtr (reqtrace) requirement files.

A .rqtr file is a YAML file (list at the top level) where each item
is a requirement object.
"""

RQTR_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "reqtrace Requirement File",
    "description": "A list of requirement objects in a .rqtr file.",
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "title"],
        "additionalProperties": True,
        "properties": {
            "id": {
                "type": "string",
                "minLength": 1,
                "description": "Unique requirement identifier (e.g. REQ-001).",
            },
            "title": {
                "type": "string",
                "minLength": 1,
                "description": "Short human-readable title of the requirement.",
            },
            "description": {
                "type": "string",
                "description": "Detailed description of the requirement.",
            },
            "derived_from": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "description": "List of parent requirement IDs this requirement derives from.",
            },
        },
    },
}
