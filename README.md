# 📦 Multi-Language Builder

A graphical packaging tool built with Python + tkinter. One-click build executables from source code across **7 programming languages** — no need to memorise complex CLI commands.

![Version](https://img.shields.io/badge/version-0.1.4-blue)
![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

---

## ✨ Features

- 🖥️ **GUI Interface** — No command-line wizardry required
- 🌐 **Bilingual UI** — Switch between English / 中文 on the fly
- 🔧 **7 Languages Supported** — Python, Node.js, Java, C, C++, C#, Go, Rust
- 👁️ **Command Preview** — See the exact commands before execution
- ✅ **Environment Check** — One-click scan to verify installed toolchains
- 📋 **Real-time Output Log** — Watch build progress step by step, with exit codes
- 📦 **Self-Packaging** — Package the tool itself into a standalone exe (since v0.1.3, hardened in v0.1.4)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** (tested on 3.13)
- **pip**
- A desktop session (tkinter is part of the standard library)

### Installation

```bash
git clone https://github.com/h9837732/Personal_Tools.git
cd Personal_Tools
python Builder_v0.1.4.py
```

PyInstaller is installed automatically the first time the tool runs from source. To install it yourself:

```bash
pip install pyinstaller
```

### Prebuilt binary

`Builder_v0.1.4.exe` is a standalone Windows build — double-click to run, no Python required on the machine.

---

## 🧭 Usage

1. **Source file** — pick the entry file (`.py`, `.js`, `.java`, `.c`, `.cs`, `.go`, `.rs`).
2. **Target language** — choose the matching toolchain; the tool fills in the right command.
3. **Output name / directory** — where the product goes (default `./dist`).
4. **Options** — `One File` and `No Console` for Python, plus an icon file.
5. **Check Env** to confirm toolchains, then **Build**.

The **Output** tab streams stdout/stderr, marks failures with `[i/n] step N failed (exit code X)` and tells you which installer to grab when a tool is missing.

---

## 🌍 Supported Languages

| Language | Tool used | Requirement |
|---|---|---|
| Python | PyInstaller | `pip install pyinstaller` |
| Node.js | `npx pkg` | `npm install -g pkg` |
| Java | `javac` + `jar` | JDK ([Adoptium](https://adoptium.net)) |
| C / C++ | `gcc` / `g++` | MinGW-w64 or MSVC |
| C# | `dotnet publish` | .NET SDK |
| Go | `go build` | [Go](https://go.dev) |
| Rust | `cargo build --release` | [rustup](https://rustup.rs) |

Python builds always pass `--noconfirm --clean`, use a temporary workpath/specpath, and keep `--distpath` at your chosen output folder.

---

## 📦 Packaging the Builder Itself

Self-build works — a packaged `Builder.exe` can compile its own source again. Two rules keep it stable:

1. **Never output into the folder where the running exe lives.** PyInstaller wipes `--distpath` before building, so it would delete the app itself. The tool detects this and redirects to `dist_selfbuild/`.
2. **Never overwrite the running exe by name.** Windows keeps a lock on it, so an identical output name is renamed to `<name>_new` automatically.

```bash
# from source
python Builder_v0.1.4.py

# or rebuild the release binary headlessly
python -m PyInstaller --noconfirm --onefile --windowed \
  --name Builder_v0.1.4 Builder_v0.1.4.py
```

> Frozen builds resolve a real Python interpreter from `PATH` before calling PyInstaller. Inside a frozen app `sys.executable` is the app itself, so never call `sys.executable -m pip` there — doing so relaunches the tool recursively.

---

## 🗂️ Repository Layout

| File | Description |
|---|---|
| `Builder_v0.1.4.py` | Current source (version constant, self-build hardening) |
| `Builder_v0.1.3.py` | Archived source of the first self-packing release |
| `Builder_v0.1.4.exe` | Prebuilt Windows standalone binary |
| `CHANGELOG.md` | Version history and verification record |
| `README.md` | This document |

---

## 🐞 Troubleshooting

| Symptom | Cause & fix |
|---|---|
| Clicking **Build** spawns more windows of the tool | An old build is using `sys.executable` as the interpreter output — upgrade to v0.1.3+ |
| Build hangs with no log output | Missing `--noconfirm`: PyInstaller is waiting for interactive confirmation. Fixed in v0.1.3+ |
| `Access is denied` on the output exe | The product is still running, or it is the tool's own exe — close it, or use another name/directory |
| Build fails on a path with spaces or Chinese characters | Commands are executed without `shell=True` since v0.1.3; upgrade |
| `PyInstaller is not installed` inside the exe | Install Python 3 + PyInstaller on the machine, or run the tool from source |

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md). Highlights:

- **v0.1.4** — working dir / naming protection when building itself, real-interpreter resolution, no-hang builds, shell-free execution, decoded logs
- **v0.1.3** — first release able to package itself
- **v0.1.0 – v0.1.2** — multi-language build skeleton, bilingual UI, command preview, environment check

---

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

[h9837732](https://github.com/h9837732)
