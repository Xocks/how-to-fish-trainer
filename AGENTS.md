# Agent Instructions & Workspace Guidelines

## Package Management & Tool Execution: UV MANDATE

**CRITICAL RULE**: ALWAYS use `uv` for all Python package management, environment synchronization, testing, and script execution in this repository.

### 1. Execution Rules
- **NEVER** run `pip`, global `python`, or global `pytest` directly.
- **NEVER** install dependencies globally or into system/user site-packages.
- **ALWAYS** prefix all commands with `uv run`.

### 2. Common Command Reference

| Task | Allowed Command | Prohibited Command |
| :--- | :--- | :--- |
| **Run Unit Tests** | `uv run pytest` or `uv run pytest -v` | `pytest`, `python -m unittest` |
| **Launch Trainer** | `uv run python run_trainer.py` | `python run_trainer.py` |
| **Run Module** | `uv run python -m howtofish_cheat` | `python -m howtofish_cheat` |
| **Sync Environment** | `uv sync --extra dev` | `pip install -r requirements.txt` |
| **Add Dependency** | `uv add <package>` | `pip install <package>` |
| **Add Dev Dependency** | `uv add --dev <package>` | `pip install <package>` |

### 3. Virtual Environment Isolation
- All dependencies must reside within the local `.venv` managed strictly by `uv`.
- If dependencies or virtual environments change, run `uv sync --extra dev`.
