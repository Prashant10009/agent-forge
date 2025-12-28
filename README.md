# Agent Forge

Agent Forge is a **config-driven multi-agent coding system** for generating, editing, and running Python projects from a single prompt. It ships with a CLI, a FastAPI service, and a Streamlit GUI for document extraction.

## What’s in this repo

- **Core orchestration**: `src/core/` (orchestrator, agents, model client, memory)
- **Tooling**: `src/tools/` (filesystem, code runner, test runner)
- **Apps**:
  - **CLI**: `src/apps/cli.py`
  - **API**: `src/apps/api.py`
  - **Static UI**: `src/apps/static/index.html`
- **Projects**:
  - `src/projects/doc_extractor/` (document extraction service)
  - `src/projects/doc_extractor_gui/` (Streamlit GUI)
  - `src/projects/todo_app_v2/` (example app)
  - `src/projects/factory_test_app/` (example app)
- **Demo scripts**: `src/demo/`
- **Agent configuration**: `config/agents.yaml`
- **Runtime data**: `data/` (SQLite memory DB, brain JSON)
- **Generated artifacts**: `generated/`
- **Instruction manual**: `Instruction manual V1, 11122025.docx`

## Key features

- **Multi-agent workflows** for generating files, editing files, running code, and tests.
- **Triad mode** (`--triad`): three persona drafts + a chief merge to produce final output.
- **Meta-project mode**: bootstrap new projects by generating agents, dependencies, and files.
- **Web + GUI**: FastAPI endpoints and a Streamlit GUI for document extraction.

## Getting started

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> Note: `requirements.txt` appears to be saved with UTF-16 encoding. If `pip` reports encoding issues, convert it to UTF-8 first or re-save the file in UTF-8.

### 2) Run the CLI

```bash
python -m src.apps.cli --help
```

### 3) Run the API

```bash
uvicorn src.apps.api:app --reload
```

### 4) Run the Streamlit GUI

```bash
streamlit run src/projects/doc_extractor_gui/app.py
```

## How it works (high level)

```text
User (CLI / API / GUI)
  │
  ▼
Orchestrator (src/core/orchestrator.py)
  ├─ ModelClient (openrouter | ollama | ollama_cloud | mock)
  ├─ ToolRegistry
  │    ├─ filesystem
  │    ├─ code_runner
  │    └─ test_runner
  ├─ AgentFactory (config/agents.yaml)
  ├─ TaskLog (SQLite: data/memory.db)
  └─ OrchestratorBrain (JSON memory: data/brain_memory.json)
```

## Common paths

- **Agent configuration**: `config/agents.yaml`
- **Memory database**: `data/memory.db`
- **Orchestrator brain**: `data/brain_memory.json`
- **Generated code**: `generated/`

## License

No license file is currently included. If you intend to distribute or reuse this project, add a license that matches your needs.
