# reqtrace

🚀 **A GitOps-friendly requirements tracing tool designed for modern CI/CD pipelines.**

`reqtrace` allows developers to define system and business requirements in simple YAML files (using the `.rqtr` extension), map those requirements to their source code via block-style comment tags, and automatically verify that they are strictly implemented and tested.

Unlike legacy tracing tools (like DOORS or heavy Jira setups), `reqtrace` is language-agnostic, developer-friendly, and treats requirements strictly as code.

## 🌟 Key Features

* **GitOps & Docs-as-Code**: Define your requirements in version-controlled `.rqtr` (YAML) files.
* **Graph Architecture (DAG)**: Map requirements strictly to their parents (using `derived_from`), ensuring complete traceability.
* **Language-Agnostic Tagging**: Uses block-style markers (`@trace-start` / `@trace-end`) to wrap implementation logic in any text-based file.
* **Partial Implementations**: Split coverage across multiple files or modules using percentage definitions (e.g., `(50%)`).
* **ReqIF Interoperability**: Import and export requirements from/to industry-standard ReqIF format.
* **Schema Validation**: Ensure your requirement files follow a strict, predefined schema.
* **Interactive HTML Reports**: Generate multi-page dashboards with requirement timelines and detailed coverage stats.

## 📚 Documentation
Read the full documentation on [GitHub Pages](https://philipmiesbauer.github.io/reqtrace/).

## 🚀 Quickstart

1. Clone the repository and install it:
```bash
git clone https://github.com/philipmiesbauer/reqtrace.git
cd reqtrace
pip install -e .
```

2. Run the traceability matrix:
```bash
reqtrace --reqs reqs/ --src src/ --html report/
```

## 🛠️ CLI Tools

`reqtrace` comes with a suite of tools:

- **`reqtrace`**: The main scanner and reporting engine.
- **`reqtrace-validate`**: Validate `.rqtr` files against the requirement schema.
- **`reqtrace-exchange`**: Convert between `.rqtr` and ReqIF formats.

## 🏷️ Traceability Tags

Wrap your implementation with start and end tags:

```python
# @trace-start: REQ-001
def login_user():
    pass
# @trace-end: REQ-001
```

For partial implementations:
```python
# @trace-start: REQ-001 (50%)
def auth_common():
    pass
# @trace-end: REQ-001
```

## 🏗️ Development Status

* [x] **Core Parsing Engine**: Parse `.rqtr` files and validate the dependency graph (DAG).
* [x] **Code Implementation Scanner**: Scan source code for `@trace-start` markers.
* [x] **HTML Reporting**: Generate interactive multi-page dashboards.
* [x] **ReqIF Export/Import**: Full interoperability with exchange formats.
* [x] **Validation Tooling**: CLI for schema verification.
* [ ] **Test Verification Scanner** *(Next)*: Analyze test results to verify requirement testing.
