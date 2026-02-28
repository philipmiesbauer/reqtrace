# Welcome to reqtrace Documentation

`reqtrace` is a GitOps-friendly requirements tracing tool designed for modern CI/CD pipelines.

It allows you to map system requirements strictly to source code implementation logic via comment tags (e.g., `@trace: REQ-001 (50%)`) and prove that the requirements are both implemented and tested.

## Core Concepts

### Requirements (The What)
Requirements are written in `yaml` files. E.g.
```yaml
- id: REQ-001
  title: Authentication
  description: The system shall authenticate users.
```

### Traceability Tags (The How)
Inside your source code (Python, Go, TS, etc.), you leave comment tags to tell the scanner what requirement a specific function implements.

```python
def login_user():
    # @trace: REQ-001
    pass
```

## Running a Scan

Run the CLI tool pointing to your requirements definition files and your source code directory:

```bash
reqtrace --reqs reqs/*.yml --src src/
```

The tool will calculate a matrix and fail your CI pipeline if any coverage is missed!
