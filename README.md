# Architecture Diagrams Generator (macOS-focused setup)

This repository contains Python scripts that generate Azure architecture diagrams (PNG, DOT, and editable Draw.io) using the `diagrams` library and GraphViz. The instructions below focus on macOS (Intel or Apple Silicon) setup and the troubleshooting steps encountered while implementing and generating diagrams.

## Quick Overview
- Scripts: `Arch_Diagrams/*.py` (generators and examples)
- Outputs: `Arch_Diagrams/diagrams/*.png`, `*.dot`, `*.drawio`

## macOS Setup (step-by-step)

1. Install Xcode Command Line Tools

```bash
sudo xcode-select --install
```

2. Install Homebrew (if not already installed)

See https://brew.sh/ and follow the install command.

3. Install GraphViz and `pkg-config`

```bash
brew install graphviz pkg-config
```

4. Create and activate a Python virtual environment (use project venv)

```bash
cd "Architecture_Diagrams_Python_AI/Arch_Diagrams"
python -m venv .venv
source .venv/bin/activate
```

5. Export Homebrew include/lib and pkg-config paths (Apple Silicon shown)

```bash
export CPPFLAGS="-I/opt/homebrew/include"
export LDFLAGS="-L/opt/homebrew/lib"
export PKG_CONFIG_PATH="/opt/homebrew/opt/graphviz/lib/pkgconfig:/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
# On Intel macs use /usr/local instead of /opt/homebrew
```

6. Install Python dependencies

pygraphviz often requires GraphViz headers at build time. Install packaging tools first and then install `pygraphviz` and other requirements:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install pygraphviz
python -m pip install -r requirements.txt
```

7. Generate the example diagram (instructions script)

```bash
python instructions_architecture.py
# Output: diagrams/instructions_architecture.png and .dot
```

8. Convert DOT to Draw.io (optional)

Install `graphviz2drawio` in the venv:

```bash
python -m pip install graphviz2drawio
graphviz2drawio diagrams/instructions_architecture.dot -o diagrams/instructions_architecture.drawio
```

9. Edit the `.drawio` file in VS Code

Install the Draw.io extension: `hediet.vscode-drawio` and open the file: `Arch_Diagrams/diagrams/instructions_architecture.drawio`.

## Troubleshooting (what I ran into and how to fix it)

- Missing GraphViz headers when building `pygraphviz` (error: `fatal error: 'graphviz/cgraph.h' file not found`)
	- Fix: install GraphViz via Homebrew and point build flags to Homebrew include/lib (see step 5). Verify header exists at `/opt/homebrew/include/graphviz/cgraph.h` or `/usr/local/include/graphviz/cgraph.h`.

- `pkg-config` could not find `graphviz` (message: `Package graphviz was not found in the pkg-config search path`)
	- Fix: locate `graphviz.pc` (Homebrew usually puts it at `/opt/homebrew/Cellar/graphviz/<version>/lib/pkgconfig/graphviz.pc`) and add its directory to `PKG_CONFIG_PATH`.
	- Example: `export PKG_CONFIG_PATH="$(brew --prefix graphviz)/lib/pkgconfig:$PKG_CONFIG_PATH"`

- `pygraphviz` installed into system Python instead of the venv
	- Fix: activate your venv before `pip install pygraphviz` and check `python -c "import pygraphviz; print(pygraphviz.__file__)"` to confirm it points to the venv site-packages.

- Packaging version conflicts after upgrading tooling
	- Example: `checkov` required `packaging<24` while `wheel` required `packaging>=24` after an upgrade. I resolved this by pinning `packaging` to a compatible version (`packaging==23.2`) and downgrading `wheel` to `0.45.1` in the venv. Use `python -m pip show wheel packaging` to verify versions.

- `graphviz2drawio` not installed or not found
	- Fix: `python -m pip install graphviz2drawio` in the active venv and run the conversion command above.

- Draw.io editing in VS Code
	- Use the `hediet.vscode-drawio` extension. If VS Code extensions are unavailable, open the `.drawio` file at https://app.diagrams.net/ by drag-and-drop.

## How I validated everything locally

- Verified `cgraph.h` exists under Homebrew include.
- Exported `PKG_CONFIG_PATH` so `pkg-config --cflags --libs graphviz` returns flags.
- Built and installed `pygraphviz` inside the venv and verified `import pygraphviz` succeeds.
- Generated `diagrams/instructions_architecture.png` and `.dot` using `instructions_architecture.py`.
- Converted `.dot` to `.drawio` using `graphviz2drawio` (installed in the venv).

## Files of interest

- `instructions_architecture.py` — script I added to generate the scenario diagram from `instructions.md`.
- `contoso_architecture.py` — existing example generator.
- `diagrams/` — generated PNG/DOT/DRAWIO outputs.
- `requirements.txt` — includes `graphviz2drawio` and other Python deps.

If you'd like, I can:
- Commit these changes and the generated diagrams to git,
- Further tweak cluster colors, labels, or layout, or
- Produce a small `Makefile` or `scripts/run.sh` to automate the full flow.

---

