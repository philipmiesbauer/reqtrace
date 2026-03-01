# Welcome to reqtrace Documentation

`reqtrace` is a GitOps-friendly requirements tracing tool designed for modern CI/CD pipelines.

It allows you to map system requirements strictly to source code implementation logic via block-style comment tags and prove that the requirements are both implemented and tested.

## Core Concepts

### Requirements (The What)
Requirements are defined in `.rqtr` files, which use YAML syntax.

```yaml
- id: REQ-001
  title: Authentication
  description: The system shall authenticate users.
```

### Traceability Tags (The How)
Inside your source code (Python, Go, TS, C++, etc.), you wrap implementation logic with start and end tags.

```python
def login_user():
    # @trace-start: REQ-001
    do_login()
    # @trace-end: REQ-001
    pass
```

### Partial Coverage
If a requirement is implemented across multiple locations, you can specify the percentage of the requirement covered by a specific block:

```python
# @trace-start: REQ-001 (50%)
def auth_helper():
    pass
# @trace-end: REQ-001
```

## Running a Scan

Run the `reqtrace` CLI tool pointing to your requirements directory and your source code directory:

```bash
reqtrace --reqs reqs/ --src src/ --html report/
```

The tool will calculate a coverage matrix, generate an interactive HTML report, and fail your CI pipeline if any coverage thresholds are missed!

## 🛠️ Additional Tools

- **`reqtrace-validate`**: Validate your `.rqtr` files against the requirement schema.
- **`reqtrace-exchange`**: Import from or export to ReqIF format for interoperability with other tools.

## Live Traceability Report
You can explore the traceability data and implementation history for this project!
👉 [**View the Interactive HTML Report**](report/index.html)
