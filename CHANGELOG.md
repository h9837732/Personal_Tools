# 变更日志 / Changelog

**项目**：多语言程序打包工具（Multi-Language Builder）
**当前版本**：`v0.1.4`
**版本方案**：语义化版本 `MAJOR.MINOR.PATCH` —— 主版本改动架构或界面范式，次版本新增能力，修订版本只修问题。
**版本号位置**：`Builder.py` 顶部的 `VERSION` 常量（窗口标题、启动日志都读它，只改这一处即可）。

---

## 版本总览

| 版本 | 状态 | 关键变化 |
|---|---|---|
| **v0.1.4** | 当前版本 | 修复“打包自己”时的递归启动、输出目录被清空、构建挂起等问题；引入自身保护与真实解释器探测 |
| **v0.1.3** | 里程碑 | **首个成功打包自身的版本**：用本程序产出的 exe 再打包本程序源码，产物可正常启动 |
| v0.1.0 – v0.1.2 | 已归档 | 多语言打包骨架、双语界面、命令预览、环境检查 |

---

## v0.1.4 — 自身打包修复版

> 这一版不新增打包能力，只把“打包自己”这条链路彻底打通，并顺手修掉了几个会导致构建静默失败的老问题。

### 修复

**1. 打包态把自身当解释器，导致无限开窗**

程序被 PyInstaller 冻结后，`sys.executable` 指向的就是程序本体。原实现用 `[sys.executable, "-m", "PyInstaller"]` 和 `sys.executable -m pip install` 调工具，结果每点一次“开始打包”就多弹一个自己的窗口，PyInstaller 从未被真正调用。

- `ensure_pyinstaller_dev()`：检测到 `sys.frozen` 后直接跳过 pip 安装。
- `find_python()` / `_python_candidates()`：冻结态下扫描 `python`、`python3`、`py` 启动器，以及 `%LOCALAPPDATA%\Programs\Python\Python3*`、`%PROGRAMFILES%\Python3*` 等常见安装位置，优先挑选已装 PyInstaller 的解释器，并缓存探测结果。
- `_ensure_pyinstaller()`：缺包时用探测到的**真实解释器**安装，失败时把可复制的命令写进日志和弹窗。

**2. `--distpath` 指向程序所在目录时，PyInstaller 会把正在运行的自己删掉**

PyInstaller 构建前会 `shutil.rmtree(--distpath)`。若把输出目录选成程序所在文件夹（默认值又是 `cwd/dist`），同目录的文件会被清空，构建随之失败。

- 新增 `_guard_self_target()`：distpath 是自身所在目录或其上级时，自动改到 `<程序目录>/dist_selfbuild` 并写日志说明。
- 产物与运行中的 exe 同名时（Windows 会锁定该文件），自动改名为 `<name>_new`。

**3. 缺少 `--noconfirm` 且子进程继承 stdin，第二次打包必定“卡死”**

产物已存在时 PyInstaller 会交互式询问是否删除旧产物；GUI 里没有控制台输入，`subprocess.run` 就一直等待，表现为无响应、无日志。

- Python 分支补上 `--noconfirm`、`--clean`，并把 `--workpath` / `--specpath` 指向系统临时目录。

**4. `shell=True` 拼接命令，路径含空格即失败**

中文用户名路径必然带空格（如 `C:\Users\苗新田\...`），Java 的 `&&`、Go 的 `set GOOS=windows&&` 在 shell 下引号错位。

- 新增 `run_capture()`：统一 `stdin=DEVNULL`、`stdout/stderr=PIPE`、Windows 下 `CREATE_NO_WINDOW`，不再使用 `shell=True`。
- Java 拆成 `javac` → `jar` 两步；Go 的编译环境改用 `env` 字典传递；Rust 用 `cwd` 指定工程目录。
- `_decode()`：输出按 `utf-8` → `gbk` → `mbcs` 回退解码，中文 Windows 不再乱码或抛 `UnicodeDecodeError`。

### 优化

| 项目 | 说明 |
|---|---|
| 语言切换 | 补全控件引用，切到中文后复选框、图标按钮、清空按钮的文字也会同步 |
| 命令预览 | 多步骤命令逐行展示（Java 显示为两条命令），冻结态下如实显示实际使用的解释器 |
| 构建流程 | 逐步骤打印 `[i/n]`、退出码与失败步骤序号；构建期间禁用“开始打包”按钮，避免重复点击 |
| 产物收集 | `_collect()` 支持 `--onedir`（返回目录）；`--onefile` / Java / Go / Rust 返回具体文件路径 |
| 环境检查 | 额外输出运行态（frozen / source）、程序路径、解释器路径与版本、PyInstaller 是否可用，缺工具时附安装提示 |
| 启动日志 | 显示版本号、运行态、exe 路径；冻结态下提醒自打包注意事项 |
| 多进程 | 入口加入 `multiprocessing.freeze_support()`，冻结后更稳定 |

### 已知限制

- 自行打包仍需要系统里存在 **Python 3 + PyInstaller**：产物不内置解释器，只负责调用。
- 无法覆盖正在运行的自身 exe（Windows 文件锁决定的），只能输出到其它名称或目录，手动替换。
- 单文件产物首次启动会解压到临时目录，体积与启动时间会高于 `--onedir`。

---

## v0.1.3 — 首个可自打包版本（里程碑）

首次跑通“用本程序产出的 exe 再打包本程序源码”的闭环，验证了自举（bootstrap）路径可行：

- 冻结态识别（`getattr(sys, "frozen", False)`）与 `APP_EXE` / `APP_DIR` 常量引入，后续所有自身保护都基于它。
- 自打包产物启动正常，界面、语言切换、命令预览功能与源码运行一致。
- 遗留问题：解释器仍取自 `sys.executable`，同目录输出会误删文件，二次构建会等待交互式确认 —— 全部在 v0.1.4 修完。

---

## v0.1.0 – v0.1.2 — 早期版本

框架成型阶段，功能点为多语言打包支持与基础交互，细节记录待补全：

- 支持 Python / Node.js / Java / C / C++ / C# / Go / Rust 八类源码入口。
- 中英双语界面、打包 / 配置 / 输出三个选项卡。
- 源文件、输出名称、输出目录、图标选择与 `--onefile` / `--windowed` 选项。
- 命令预览、环境检查、构建日志（深色滚动文本框）。

---

## 自打包验证记录（v0.1.4）

用 PyInstaller 打包本程序，再让该 exe 打包本程序源码 `Builder.py`：

```
frozen       : True
sys.executable: ...\dist\Builder.exe          ← 冻结态下它就是自己
find_python  : ('C:\Windows\py.EXE', '3.13')  ← 正确解析到真实解释器
PyInstaller  : 6.22.3
RUN: py.EXE -m PyInstaller --noconfirm --clean --workpath <temp> --specpath <temp>
              --distpath ...\dist2 --onefile --name Builder Builder.py
rc: 0   →  dist2\Builder.exe（约 14.4 MB）生成成功，GUI 启动正常
```

对照组（旧实现）：命令行会变成 `Builder.exe -m PyInstaller ...`，即不断启动自身。

---

## 运行环境

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 10 / 11（代码对 Linux / macOS 有分支，未实测） |
| 源码运行 | Python 3.9+（实测 3.13） |
| 打包 Python 项目 | PyInstaller 6.x（实测 6.22.3），缺失时自动 `pip install` |
| 其它语言 | Node.js `npx pkg`、JDK `javac/jar`、MinGW/MSVC、.NET SDK、Go、Rust 工具链按需安装 |

---

## 升级与使用注意

1. **自打包请换输出目录**：不要输出到程序自身所在文件夹，程序会自动退到 `dist_selfbuild`。
2. **产物同名会自动加 `_new`**：确认新 exe 可用后再手动替换旧文件。
3. **版本号只改一处**：`Builder.py` 的 `VERSION`，窗口标题与启动日志自动同步。
4. **冻结态下不要写 `sys.executable -m pip`**：任何后续改动都要走 `find_python()`，否则会重新引入无限开窗。

---

## 待办（v0.1.5 候选）

- [ ] 版本历史补上发布日期，早期版本（0.1.0–0.1.2）细节回填
- [ ] 打包过程放到后台线程，避免构建期间界面无响应
- [ ] Java 支持 `package` 声明，自动推断主类，替换当前按文件名取类名的做法
- [ ] Rust / C# 产物名称支持 `--name` 语义（当前沿用源码名或 `Cargo.toml` 配置）
- [ ] 记住上次的源文件、输出目录与选项（写入本地配置文件）
