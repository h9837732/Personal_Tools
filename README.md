# 📦 Multi-Language Builder · 多语言程序打包工具

**[English](#-english) · [简体中文](#-简体中文)**

![Version](https://img.shields.io/badge/version-0.1.4-blue)
![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

---

# 🇬🇧 English

A graphical packaging tool built with Python + tkinter. One-click build executables from source code across **7 programming languages** — no need to memorise complex CLI commands.

## ✨ Features

- 🖥️ **GUI Interface** — No command-line wizardry required
- 🌐 **Bilingual UI** — Switch between English / 中文 on the fly
- 🔧 **7 Languages Supported** — Python, Node.js, Java, C, C++, C#, Go, Rust
- 👁️ **Command Preview** — See the exact commands before execution
- ✅ **Environment Check** — One-click scan to verify installed toolchains
- 📋 **Real-time Output Log** — Watch build progress step by step, with exit codes
- 📦 **Self-Packaging** — Package the tool itself into a standalone exe (since v0.1.3, hardened in v0.1.4)

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

## 🧭 Usage

1. **Source file** — pick the entry file (`.py`, `.js`, `.java`, `.c`, `.cs`, `.go`, `.rs`).
2. **Target language** — choose the matching toolchain; the tool fills in the right command.
3. **Output name / directory** — where the product goes (default `./dist`).
4. **Options** — `One File` and `No Console` for Python, plus an icon file.
5. **Check Env** to confirm toolchains, then **Build**.

The **Output** tab streams stdout/stderr, marks failures with `[i/n] step N failed (exit code X)` and tells you which installer to grab when a tool is missing.

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

## 🗂️ Repository Layout

| File | Description |
|---|---|
| `Builder_v0.1.4.py` | Current source (version constant, self-build hardening) |
| `Builder_v0.1.3.py` | Archived source of the first self-packing release |
| `Builder_v0.1.4.exe` | Prebuilt Windows standalone binary |
| `CHANGELOG.md` | Version history and verification record |
| `README.md` | This document |
| `LICENSE` | MIT |

## 🐞 Troubleshooting

| Symptom | Cause & fix |
|---|---|
| Clicking **Build** spawns more windows of the tool | An old build is using `sys.executable` as the interpreter — upgrade to v0.1.3+ |
| Build hangs with no log output | Missing `--noconfirm`: PyInstaller is waiting for interactive confirmation. Fixed in v0.1.3+ |
| `Access is denied` on the output exe | The product is still running, or it is the tool's own exe — close it, or use another name/directory |
| Build fails on a path with spaces or Chinese characters | Commands are executed without `shell=True` since v0.1.3; upgrade |
| `PyInstaller is not installed` inside the exe | Install Python 3 + PyInstaller on the machine, or run the tool from source |

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md). Highlights:

- **v0.1.4** — working dir / naming protection when building itself, real-interpreter resolution, no-hang builds, shell-free execution, decoded logs
- **v0.1.3** — first release able to package itself
- **v0.1.0 – v0.1.2** — multi-language build skeleton, bilingual UI, command preview, environment check

## 📄 License

MIT — see [LICENSE](LICENSE).

---

# 🇨🇳 简体中文

基于 Python + tkinter 的图形化打包工具。支持 **7 种编程语言** 的源码一键打包成可执行文件，不必记那些复杂的命令行参数。

## ✨ 功能特性

- 🖥️ **图形界面** — 点按钮就行，不用敲命令行
- 🌐 **中英双语界面** — 运行中随时切换 English / 中文
- 🔧 **支持 7 种语言** — Python、Node.js、Java、C、C++、C#、Go、Rust
- 👁️ **命令预览** — 执行前先看清到底会跑哪条命令
- ✅ **环境检查** — 一键扫描本机工具链是否齐全
- 📋 **实时输出日志** — 逐步显示构建过程与退出码
- 📦 **能打包自己** — 把本工具自身打包成独立 exe（v0.1.3 起支持，v0.1.4 加固）

## 🚀 快速开始

### 环境要求

- **Python 3.9+**（实测 3.13）
- **pip**
- 有桌面环境（tkinter 为标准库自带）

### 安装运行

```bash
git clone https://github.com/h9837732/Personal_Tools.git
cd Personal_Tools
python Builder_v0.1.4.py
```

首次以源码方式运行时会自动安装 PyInstaller；也可以手动装：

```bash
pip install pyinstaller
```

### 免安装版本

`Builder_v0.1.4.exe` 是 Windows 单文件版本，双击即用，目标机器无需安装 Python。

## 🧭 使用步骤

1. **源文件** — 选择入口文件（`.py`、`.js`、`.java`、`.c`、`.cs`、`.go`、`.rs`）。
2. **目标语言** — 选中对应工具链，程序自动生成正确命令。
3. **输出名称 / 输出目录** — 产物放在哪里（默认 `./dist`）。
4. **选项** — Python 专属的「单文件」「无控制台窗口」，以及图标文件。
5. 先点 **检查环境** 确认工具链，再点 **开始打包**。

**输出** 选项卡实时显示 stdout/stderr；失败时标出 `[i/n] 第 N 步执行失败（退出码 X）`，并提示该去装什么工具。

## 🌍 支持的语言与工具链

| 语言 | 使用的工具 | 依赖 |
|---|---|---|
| Python | PyInstaller | `pip install pyinstaller` |
| Node.js | `npx pkg` | `npm install -g pkg` |
| Java | `javac` + `jar` | JDK（[Adoptium](https://adoptium.net)） |
| C / C++ | `gcc` / `g++` | MinGW-w64 或 MSVC |
| C# | `dotnet publish` | .NET SDK |
| Go | `go build` | [Go](https://go.dev) |
| Rust | `cargo build --release` | [rustup](https://rustup.rs) |

Python 分支固定带 `--noconfirm --clean`，`workpath/specpath` 走系统临时目录，`--distpath` 保持为你指定的输出目录。

## 📦 打包自己（自举）

实测可用：打包后的 `Builder.exe` 可以再次编译它自己的源码。两条规则保证稳定：

1. **不要把输出目录设成正在运行的程序所在文件夹。** PyInstaller 构建前会清空 `--distpath`，那样会把程序本身删掉。程序会自动改到 `dist_selfbuild/`。
2. **不要用同名覆盖正在运行的 exe。** Windows 会锁住该文件，遇到同名产物时自动改名为 `<name>_new`。

```bash
# 以源码方式运行
python Builder_v0.1.4.py

# 或者无界面重建发布版二进制
python -m PyInstaller --noconfirm --onefile --windowed \
  --name Builder_v0.1.4 Builder_v0.1.4.py
```

> 打包态（frozen）会先从 `PATH` 里找一个真实可用的 Python 解释器再调用 PyInstaller。frozen 下 `sys.executable` 就是程序自己，所以那里绝不能执行 `sys.executable -m pip`，否则会不断重新启动自己。

## 🗂️ 仓库文件说明

| 文件 | 说明 |
|---|---|
| `Builder_v0.1.4.py` | 当前源码（版本号常量 + 自打包加固） |
| `Builder_v0.1.3.py` | 归档：首个能打包自身的版本源码 |
| `Builder_v0.1.4.exe` | 预编译 Windows 独立程序 |
| `CHANGELOG.md` | 版本历史与自打包验证记录 |
| `README.md` | 本文档 |
| `LICENSE` | MIT 许可证 |

## 🐞 常见问题

| 现象 | 原因与处理 |
|---|---|
| 点「开始打包」反而弹出更多本程序窗口 | 旧版用 `sys.executable` 当解释器，升级到 v0.1.3+ |
| 点了打包没有任何日志、像卡死 | 缺 `--noconfirm`，PyInstaller 在等交互式确认；v0.1.3+ 已修 |
| 输出 exe 报 `Access is denied` | 产物还在运行，或与正在运行的本程序同名；关闭后换文件名/目录 |
| 路径含空格或中文时构建失败 | v0.1.3 起不再用 `shell=True`，升级即可 |
| exe 里提示未安装 PyInstaller | 本机需装 Python 3 + PyInstaller，或改用源码运行 |

## 📝 更新日志

见 [CHANGELOG.md](CHANGELOG.md)，要点：

- **v0.1.4** — 自打包时的工作目录/命名保护、真实解释器探测、构建不再挂起、去掉 shell 拼接、日志解码
- **v0.1.3** — 首个能打包自己的版本
- **v0.1.0 – v0.1.2** — 多语言打包骨架、双语界面、命令预览、环境检查

## 📄 许可证

MIT，见 [LICENSE](LICENSE)。

## 👤 作者

[h9837732](https://github.com/h9837732)
