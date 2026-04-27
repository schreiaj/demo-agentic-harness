# Demo Coding Agent

This repository showcases a **demo coding agent** setup, leveraging modern Python tooling for development, dependency management, and reproducibility. It's designed to demonstrate an AI-assisted coding workflow with a focus on demystifying the concept of agentic coding harnesses. It's not intended as a production tool or even good code. It's meant to be readable. 

And yes, I used it to help write this readme as a test.

## 🚀 Quick Start

1. **Clone the repo**:
   ```bash
   git clone <repo-url>
   cd demo-coding-agent
   ```

2. **Enter the Nix development shell** (recommended for reproducibility):
   ```bash
   nix develop
   ```
   This sets up a flake-based environment with Python and all dependencies.

3. **Alternative: Use uv for local setup**:
   ```bash
   uv sync  # Installs dependencies from pyproject.toml
   ```

4. **Run the main script**:
   ```bash
   uv run main.py  # Or just `python main.py` in the Nix shell
   ```

## 🛠️ Project Structure

- **`main.py`**: Entry point for the coding agent demo. Demonstrates core functionality (e.g., tool usage, file operations).
- **`pyproject.toml`**: Project metadata and dependencies managed by `uv` or `poetry`.
- **`flake.nix`**: Nix flake for reproducible development environments.
- **`flake.lock` / `uv.lock`**: Lockfiles for deterministic builds.
- **`.env`**: Environment variables (add to `.gitignore` in production).
- **`.venv/`**: Virtual environment (managed by `uv` or Nix).

## 🔧 Tools & Dependencies

| Tool | Purpose | Version/Command |
|------|---------|-----------------|
| **Nix Flakes** | Reproducible envs | `nix develop` |
| **uv** | Fast Python packaging | `uv sync`, `uv run` |
| **Python** | Runtime | 3.12+ (via `.python-version`) |

Key Python dependencies are listed in `pyproject.toml` (e.g., for agent tooling, file I/O).

## 📋 Development Workflow

- **Lint & Format**: Use `ruff` (integrated via Nix/uv).
  ```bash
  uv run ruff check . --fix
  ```
- **Type Check**: `uv run pyright .` or similar.
- **Testing**: Add tests in `tests/` (TBD).
- **Build & Lock**:
  ```bash
  uv lock
  nix flake check
  ```

## 🌐 Environment Notes

- **`.python-version`**: Enforces Python version via `pyenv`.
- **`.gitignore`**: Ignores `.venv`, `.env`, Nix store, etc.
- **Secrets**: Use `.env` for API keys; never commit!

## 🤝 Contributing

1. Fork & PR.
2. Ensure `nix flake check` passes.
3. Update locks: `uv lock && nix flake lock`.
