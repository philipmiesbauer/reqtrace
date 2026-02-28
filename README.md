# reqtrace

🚀 **A GitOps-friendly requirements tracing tool designed for modern CI/CD pipelines.**

`reqtrace` allows developers to define system and business requirements in simple YAML files, map those requirements to their source code via comment tags (e.g., `@trace: REQUIRE-001 (50%)`), and automatically verify that they are strictly implemented and tested.

Unlike legacy tracing tools (like DOORS or heavy Jira setups), `reqtrace` is language-agnostic, developer-friendly, and treats requirements strictly as code.

## 🌟 Key Features

* **GitOps & Docs-as-Code**: Define your requirements in simple, version-controlled YAML.
* **Graph Architecture (DAG)**: Map requirements strictly to their parents (using `derived_from`), ensuring complete traceability up to the top-level system requirements.
* **Language-Agnostic Tagging**: Because it operates via smart text-based scanning, you can tag traceability in Python, Go, C++, or any text file just by writing a comment.
* **Partial Implementations**: Split coverage across multiple microservices or modules using percentage definitions in your tags.

## 📚 Documentation
Read the full documentation on [GitHub Pages](https://philipmiesbauer.github.io/reqtrace/).

## 🚀 Quickstart

1. Clone the repository and install it:
```bash
git clone https://github.com/philipmiesbauer/reqtrace.git
cd reqtrace
pip install -e .
```

2. Run the traceability matrix on the project itself!
```bash
reqtrace --reqs reqs/*.yml --src src/
```

## 🏗️ Phase 1 Development

* [x] **Core Parsing Engine**: Parse `requirements.yaml` and validate the dependency graph (DAG), ensuring missing identifiers and cyclic dependencies are strictly caught.
* [ ] **Code Implementation Scanner** *(Up Next)*: Deeply scan source code repositories to dynamically detect `@trace: REQUIRE-001` coverage tokens.
* [ ] **Test Verification Scanner**: Analyze test matrices to verify tracing implementation exists.
