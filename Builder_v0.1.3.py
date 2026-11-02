# -*- coding: utf-8 -*-
"""
多语言程序打包工具 / Multi-Language Builder

本版本修复了“打包器无法打包自己”的问题，关键改动：
1. 打包态（frozen）不自称解释器：原来用 sys.executable 去跑
   `-m PyInstaller` / `-m pip install`，而 frozen 下 sys.executable 就是
   程序自身，于是会不断启动自己的新窗口（无限递归）。
   现在改为自动寻找系统里真实存在的 python.exe。
2. 不再让 PyInstaller 删掉正在运行的程序目录：PyInstaller 会
   `rmtree(--distpath)`，若把输出目录选成自身所在目录，就会把正在运行的
   exe 及同目录文件一起清掉（表现为“打包自己必失败”）。
   现在会自动改用安全的输出目录 / 改名。
3. 加入 `--noconfirm`、`stdin=DEVNULL` 与临时 workpath/specpath：
   否则产物已存在时 PyInstaller 会等待交互式确认，GUI 里就是“卡死无输出”。
4. Java/Go 等命令不再用 `shell=True` 拼接（路径含空格时必然失败），
   改为分步执行 + env 传参。
5. 输出解码做 utf-8 / gbk 回退，中文 Windows 不再乱码或抛 UnicodeDecodeError。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import glob
import shutil
import tempfile
import subprocess

# ============ 运行态 / 平台常量 ============
IS_WIN = os.name == "nt"
# PyInstaller 打包后运行时 sys.frozen 为 True，此时 sys.executable 是 exe 本体
FROZEN = bool(getattr(sys, "frozen", False))
APP_EXE = os.path.abspath(sys.executable)
APP_DIR = os.path.dirname(APP_EXE)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if IS_WIN else 0


def _decode(data):
    """把子进程输出解码成字符串（utf-8 优先，中文 Windows 回退 gbk）。"""
    if not data:
        return ""
    if isinstance(data, str):
        return data
    for enc in ("utf-8", "gbk", "mbcs", "latin-1"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", "replace")


def run_capture(cmd, cwd=None, env=None):
    """统一的子进程调用：不继承 stdin（否则交互式提问会永久挂起）、不弹黑框。"""
    kwargs = dict(stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE, cwd=cwd, env=env)
    if IS_WIN:
        kwargs["creationflags"] = NO_WINDOW
    return subprocess.run(cmd, **kwargs)


def tool_path(name):
    """解析可执行文件，Windows 下兼容 npm 全局装的 npx.cmd 等。"""
    return shutil.which(name) or name


def tool_exists(name):
    return shutil.which(name) is not None


def ensure_pyinstaller_dev():
    """仅开发态（源码运行）自动安装 PyInstaller。

    打包态绝对不能执行 `sys.executable -m pip ...`：frozen 下 sys.executable
    就是本程序，等于再启动一个自己，形成无限开窗。
    """
    if FROZEN:
        return
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Installing pyinstaller ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


# ============ Python 解释器探测 ============
_PY_CACHE = {"done": False, "result": None}


def _probe_python(exe):
    """返回可用版本号字符串，不可用返回 None。"""
    try:
        r = run_capture([exe, "-c",
                         "import sys;print('%d.%d' % sys.version_info[:2])"])
        if r.returncode == 0:
            ver = _decode(r.stdout).strip()
            if ver.startswith("3."):
                return ver
    except Exception:
        pass
    return None


def _has_module(exe, module):
    try:
        r = run_capture([exe, "-c", "import %s" % module])
        return r.returncode == 0
    except Exception:
        return False


def _python_candidates():
    cands = []
    if not FROZEN:
        cands.append(sys.executable)
        return cands
    # 打包态：绝不能用 sys.executable（那是自己）
    for name in ("python", "python3", "py"):
        p = shutil.which(name)
        if p:
            cands.append(p)
    if IS_WIN:
        for pat in (os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python3*\python.exe"),
                    os.path.expandvars(r"%PROGRAMFILES%\Python3*\python.exe"),
                    os.path.expandvars(r"%PROGRAMFILES(X86)%\Python3*\python.exe"),
                    r"C:\Python3*\python.exe"):
            cands.extend(sorted(glob.glob(pat), reverse=True))
    else:
        cands.extend(["/usr/bin/python3", "/usr/local/bin/python3"])
    # 去重
    out, seen = [], set()
    for p in cands:
        if not p or not os.path.exists(p):
            continue
        key = os.path.normcase(os.path.realpath(p))
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def find_python(refresh=False):
    """返回 (解释器路径, 版本)。优先选已装 PyInstaller 的那个。"""
    if _PY_CACHE["done"] and not refresh:
        return _PY_CACHE["result"]
    best = None
    result = None
    for exe in _python_candidates():
        ver = _probe_python(exe)
        if not ver:
            continue
        if _has_module(exe, "PyInstaller"):
            result = (exe, ver)
            break
        if best is None:
            best = (exe, ver)
    if result is None:
        result = best
    _PY_CACHE["done"] = True
    _PY_CACHE["result"] = result
    return result


# ============ 双语字典 ============
LANG = {
    "zh": {
        "title": "多语言程序打包工具",
        "lang_label": "界面语言:",
        "tab_build": "打包",
        "tab_config": "配置",
        "tab_output": "输出",
        "source_file": "源文件 / 项目目录:",
        "browse": "浏览...",
        "language": "目标语言:",
        "output_name": "输出名称:",
        "output_dir": "输出目录:",
        "options": "选项:",
        "opt_onefile": "单文件",
        "opt_windowed": "无控制台窗口",
        "opt_icon": "图标文件:",
        "select_icon": "选择图标",
        "build": "开始打包",
        "clear": "清空输出",
        "check_env": "检查环境",
        "lang_cfg": "语言配置:",
        "packager": "打包器:",
        "cmd_preview": "命令预览:",
        "output_log": "输出日志:",
        "copied": "已复制",
        "select_source_first": "请先选择源文件",
        "build_success": "打包完成!\n产物已保存到:\n",
        "build_failed": "打包失败，请查看输出日志",
        "env_check": "=== 环境检查结果 ===\n",
        "env_ok": "可用",
        "env_missing": "未安装",
        "select_output_dir": "选择输出目录",
        "all_files": "所有文件",
        "no_python": ("没有找到可用的 Python 解释器。\n"
                      "程序已被打包（frozen），不能再用自身充当 Python，"
                      "请先安装 Python 3 并加入 PATH。"),
        "py_missing_pkg": "当前 Python 缺少 PyInstaller，正在安装……",
        "py_install_fail": "PyInstaller 安装失败，请手动执行:\n{cmd}",
        "self_dist": ("输出目录不能是正在运行的程序所在目录"
                      "（PyInstaller 会清空 distpath，把本程序一起删掉）。\n"
                      "已自动改为: {new}"),
        "self_name": ("输出名称与正在运行的程序同名，Windows 会锁定该 exe。\n"
                      "已自动改为: {new}"),
        "step_failed": "第 {n} 步执行失败（退出码 {code}）",
        "hint_install": "安装提示: ",
        "self_build_note": ("提示：本程序自身的源码若包含 ensure_package 之类的 "
                            "sys.executable -m pip 调用，请确保它在 frozen 下被跳过。"),
    },
    "en": {
        "title": "Multi-Language Builder",
        "lang_label": "UI Language:",
        "tab_build": "Build",
        "tab_config": "Config",
        "tab_output": "Output",
        "source_file": "Source File / Project Dir:",
        "browse": "Browse...",
        "language": "Target Language:",
        "output_name": "Output Name:",
        "output_dir": "Output Dir:",
        "options": "Options:",
        "opt_onefile": "One File",
        "opt_windowed": "No Console",
        "opt_icon": "Icon File:",
        "select_icon": "Select Icon",
        "build": "Build",
        "clear": "Clear",
        "check_env": "Check Env",
        "lang_cfg": "Language Config:",
        "packager": "Packager:",
        "cmd_preview": "Command Preview:",
        "output_log": "Output Log:",
        "copied": "copied",
        "select_source_first": "Please select a source file first",
        "build_success": "Build successful!\nOutput saved to:\n",
        "build_failed": "Build failed. See output log.",
        "env_check": "=== Environment Check ===\n",
        "env_ok": "OK",
        "env_missing": "NOT INSTALLED",
        "select_output_dir": "Select Output Directory",
        "all_files": "All Files",
        "no_python": ("No usable Python interpreter found.\n"
                      "This program is frozen, so it cannot act as Python itself. "
                      "Please install Python 3 and make sure it is on PATH."),
        "py_missing_pkg": "PyInstaller missing in that Python, installing...",
        "py_install_fail": "Failed to install PyInstaller. Run manually:\n{cmd}",
        "self_dist": ("The output directory cannot be the folder of the running "
                      "program (PyInstaller wipes --distpath and would delete "
                      "this app). Switched to: {new}"),
        "self_name": ("Output name equals the running executable, which Windows "
                      "keeps locked. Renamed to: {new}"),
        "step_failed": "Step {n} failed (exit code {code})",
        "hint_install": "Install hint: ",
        "self_build_note": ("Note: if this program's own source calls "
                            "sys.executable -m pip, make sure it is skipped when frozen."),
    }
}
CURRENT_LANG = "en"


def T(key):
    return LANG[CURRENT_LANG][key]


# ============ 各语言打包器配置 ============
# ext: 源码扩展名; packager: 用哪个工具; tool: 需要的命令; install: 安装提示
BUILDERS = {
    "Python":  {"ext": ".py",   "packager": "PyInstaller",   "tool": None,
                "install": "pip install pyinstaller"},
    "Node.js": {"ext": ".js",   "packager": "pkg",           "tool": "npx",
                "install": "npm install -g pkg"},
    "Java":    {"ext": ".java", "packager": "jdk (jar)",     "tool": "javac",
                "install": "Install JDK from https://adoptium.net"},
    "C / C++": {"ext": ".c",    "packager": "gcc / g++",     "tool": "gcc",
                "install": "Install MinGW-w64 or MSVC"},
    "C#":      {"ext": ".cs",   "packager": "dotnet publish", "tool": "dotnet",
                "install": "Install .NET SDK"},
    "Go":      {"ext": ".go",   "packager": "go build",      "tool": "go",
                "install": "Install Go from https://go.dev"},
    "Rust":    {"ext": ".rs",   "packager": "cargo build",   "tool": "cargo",
                "install": "Install Rust from https://rustup.rs"},
}

EXE_EXT = ".exe" if IS_WIN else ""


class BuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title(T("title"))
        self.root.geometry("780x700")

        self.source_var = tk.StringVar()
        self.output_name_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "dist"))
        self.icon_var = tk.StringVar()
        self.lang_var = tk.StringVar(value="Python")
        self.onefile_var = tk.BooleanVar(value=True)
        self.windowed_var = tk.BooleanVar(value=False)

        # Python 标签页实际使用的解释器（do_build 时确定）
        self.python_exe = None
        self._busy = False

        self._build_ui()
        self._refresh_texts()
        self._log_startup()

    # -------- UI --------
    def _build_ui(self):
        # 顶部：语言切换
        top = tk.Frame(self.root, padx=10, pady=5)
        top.pack(fill="x")
        self.lbl_lang = tk.Label(top, text=T("lang_label"))
        self.lbl_lang.pack(side="left")
        self.lang_combo = ttk.Combobox(top, values=["English", "中文"],
                                       state="readonly", width=10)
        self.lang_combo.set("English")
        self.lang_combo.pack(side="left", padx=5)
        self.lang_combo.bind("<<ComboboxSelected>>", self._switch_lang)

        self.env_btn = tk.Button(top, text=T("check_env"), command=self.check_env)
        self.env_btn.pack(side="right")

        # 选项卡
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_build = tk.Frame(self.notebook)
        self.tab_config = tk.Frame(self.notebook)
        self.tab_output = tk.Frame(self.notebook)
        self.notebook.add(self.tab_build, text=T("tab_build"))
        self.notebook.add(self.tab_config, text=T("tab_config"))
        self.notebook.add(self.tab_output, text=T("tab_output"))

        self._build_build_tab()
        self._build_config_tab()
        self._build_output_tab()

    def _build_build_tab(self):
        # 源文件
        f1 = tk.LabelFrame(self.tab_build, padx=10, pady=8)
        f1.pack(fill="x", padx=8, pady=5)
        self.lbl_source = tk.Label(f1, text=T("source_file"))
        self.lbl_source.grid(row=0, column=0, sticky="w")
        tk.Entry(f1, textvariable=self.source_var, width=55).grid(row=0, column=1, padx=5)
        self.btn_browse = tk.Button(f1, text=T("browse"), command=self.browse_source)
        self.btn_browse.grid(row=0, column=2, padx=5)

        # 语言
        self.lbl_lang2 = tk.Label(f1, text=T("language"))
        self.lbl_lang2.grid(row=1, column=0, sticky="w", pady=6)
        self.lang_select = ttk.Combobox(f1, textvariable=self.lang_var,
                                        values=list(BUILDERS.keys()), state="readonly", width=20)
        self.lang_select.grid(row=1, column=1, sticky="w", padx=5)
        self.lang_select.bind("<<ComboboxSelected>>", lambda e: self._update_cmd())

        # 输出名称
        self.lbl_outname = tk.Label(f1, text=T("output_name"))
        self.lbl_outname.grid(row=2, column=0, sticky="w")
        tk.Entry(f1, textvariable=self.output_name_var, width=25).grid(
            row=2, column=1, sticky="w", padx=5)

        # 输出目录
        self.lbl_outdir = tk.Label(f1, text=T("output_dir"))
        self.lbl_outdir.grid(row=3, column=0, sticky="w", pady=6)
        tk.Entry(f1, textvariable=self.output_dir_var, width=55).grid(row=3, column=1, padx=5)
        self.btn_outdir = tk.Button(f1, text=T("browse"), command=self.browse_outdir)
        self.btn_outdir.grid(row=3, column=2, padx=5)

        # 选项
        f2 = tk.LabelFrame(self.tab_build, padx=10, pady=8)
        f2.pack(fill="x", padx=8, pady=5)
        self.lbl_opt = tk.Label(f2, text=T("options"))
        self.lbl_opt.pack(side="left")
        self.chk_onefile = tk.Checkbutton(f2, text=T("opt_onefile"),
                                          variable=self.onefile_var, command=self._update_cmd)
        self.chk_onefile.pack(side="left", padx=8)
        self.chk_windowed = tk.Checkbutton(f2, text=T("opt_windowed"),
                                           variable=self.windowed_var, command=self._update_cmd)
        self.chk_windowed.pack(side="left", padx=8)
        self.lbl_icon = tk.Label(f2, text=T("opt_icon"))
        self.lbl_icon.pack(side="left", padx=(15, 2))
        tk.Entry(f2, textvariable=self.icon_var, width=18).pack(side="left", padx=2)
        self.btn_icon = tk.Button(f2, text=T("select_icon"), command=self.browse_icon)
        self.btn_icon.pack(side="left", padx=5)

        # 命令预览
        f3 = tk.LabelFrame(self.tab_build, padx=10, pady=8)
        f3.pack(fill="both", expand=True, padx=8, pady=5)
        self.lbl_cmd = tk.Label(f3, text=T("cmd_preview"))
        self.lbl_cmd.pack(anchor="w")
        self.cmd_text = tk.Text(f3, height=7, bg="#f4f4f4")
        self.cmd_text.pack(fill="both", expand=True)

        # 打包按钮
        self.build_btn = tk.Button(self.tab_build, text=T("build"),
                                   command=self.do_build, bg="#4CAF50", fg="white",
                                   font=("", 11, "bold"), height=2)
        self.build_btn.pack(fill="x", padx=8, pady=8)

        self._update_cmd()

    def _build_config_tab(self):
        f = tk.Frame(self.tab_config, padx=15, pady=15)
        f.pack(fill="both", expand=True)
        self.lbl_cfg = tk.Label(f, text=T("lang_cfg"), font=("", 11, "bold"))
        self.lbl_cfg.pack(anchor="w")
        cols = ("lang", "packager", "install")
        self.cfg_tree = ttk.Treeview(f, columns=cols, show="headings", height=10)
        for c, w in zip(cols, (120, 160, 400)):
            self.cfg_tree.heading(c, text=c)
            self.cfg_tree.column(c, width=w)
        for name, cfg in BUILDERS.items():
            self.cfg_tree.insert("", "end", values=(name, cfg["packager"], cfg["install"]))
        self.cfg_tree.pack(fill="both", expand=True, pady=8)

    def _build_output_tab(self):
        f = tk.Frame(self.tab_output, padx=10, pady=8)
        f.pack(fill="both", expand=True)
        self.lbl_log = tk.Label(f, text=T("output_log"))
        self.lbl_log.pack(anchor="w")
        self.log = scrolledtext.ScrolledText(f, height=25, bg="#1e1e1e", fg="#dcdcdc",
                                             insertbackground="white")
        self.log.pack(fill="both", expand=True, pady=5)
        self.btn_clear = tk.Button(f, text=T("clear"),
                                   command=lambda: self.log.delete(1.0, "end"))
        self.btn_clear.pack(anchor="e")

    # -------- 逻辑 --------
    def _log(self, msg):
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.root.update_idletasks()

    def _log_startup(self):
        mode = "frozen (exe)" if FROZEN else "source (python)"
        self._log(f"# runner : {mode}")
        self._log(f"# exe    : {APP_EXE}")
        if FROZEN:
            self._log("# " + T("self_build_note"))
        self._log("")

    def _switch_lang(self, e=None):
        global CURRENT_LANG
        CURRENT_LANG = "zh" if self.lang_combo.get() == "中文" else "en"
        self._refresh_texts()

    def _refresh_texts(self):
        self.root.title(T("title"))
        self.notebook.tab(0, text=T("tab_build"))
        self.notebook.tab(1, text=T("tab_config"))
        self.notebook.tab(2, text=T("tab_output"))
        for w, key in [
            (self.lbl_lang, "lang_label"), (self.lbl_source, "source_file"),
            (self.btn_browse, "browse"), (self.lbl_lang2, "language"),
            (self.lbl_outname, "output_name"), (self.lbl_outdir, "output_dir"),
            (self.btn_outdir, "browse"), (self.lbl_opt, "options"),
            (self.chk_onefile, "opt_onefile"), (self.chk_windowed, "opt_windowed"),
            (self.lbl_icon, "opt_icon"), (self.btn_icon, "select_icon"),
            (self.lbl_cmd, "cmd_preview"), (self.build_btn, "build"),
            (self.env_btn, "check_env"), (self.lbl_cfg, "lang_cfg"),
            (self.lbl_log, "output_log"), (self.btn_clear, "clear"),
        ]:
            w.config(text=T(key))
        self._update_cmd()

    def _current(self):
        return BUILDERS[self.lang_var.get()]

    # -------- 命令构造 --------
    def _build_steps(self, lang, src, out, odir, icon=None):
        """返回步骤列表：[{'cmd': [...], 'cwd': ..., 'env': ...}, ...]"""
        ext = EXE_EXT
        if lang == "Python":
            py = self.python_exe or (sys.executable if not FROZEN else "python")
            work = os.path.join(tempfile.gettempdir(), "mlbuilder", "work_" + out)
            cmd = [py, "-m", "PyInstaller", "--noconfirm", "--clean",
                   "--workpath", work, "--specpath", work, "--distpath", odir]
            cmd.append("--onefile" if self.onefile_var.get() else "--onedir")
            if self.windowed_var.get():
                cmd.append("--windowed")
            if icon and os.path.exists(icon):
                cmd += ["--icon", icon]
            cmd += ["--name", out, src]
            return [{"cmd": cmd}]

        if lang == "Node.js":
            return [{"cmd": [tool_path("npx"), "pkg", src,
                             "--output", os.path.join(odir, out)]}]

        if lang == "Java":
            cls = os.path.splitext(os.path.basename(src))[0]
            jar = os.path.join(odir, out + ".jar")
            # 拆成两步，避免 shell 拼接 "&&" 在含空格路径下失败
            return [{"cmd": [tool_path("javac"), "-encoding", "UTF-8", "-d", odir, src]},
                    {"cmd": [tool_path("jar"), "cfe", jar, cls, "-C", odir, "."]}]

        if lang == "C / C++":
            lower = src.lower()
            compiler = "g++" if lower.endswith((".cpp", ".cc", ".cxx", ".hpp", ".h")) else "gcc"
            return [{"cmd": [tool_path(compiler), src,
                             "-o", os.path.join(odir, out + ext)]}]

        if lang == "C#":
            rid = "win-x64" if IS_WIN else "linux-x64"
            return [{"cmd": [tool_path("dotnet"), "publish", src, "-c", "Release",
                             "-r", rid, "--self-contained", "true", "-o", odir]}]

        if lang == "Go":
            env = dict(os.environ)
            env.setdefault("CGO_ENABLED", "0")
            return [{"cmd": [tool_path("go"), "build", "-o",
                             os.path.join(odir, out + ext), src], "env": env}]

        if lang == "Rust":
            return [{"cmd": [tool_path("cargo"), "build", "--release"],
                     "cwd": os.path.dirname(os.path.abspath(src))}]

        return []

    def _update_cmd(self, e=None):
        lang = self.lang_var.get()
        src = self.source_var.get() or "<source%s>" % BUILDERS[lang]["ext"]
        out = self.output_name_var.get() or "output"
        odir = self.output_dir_var.get() or "dist"
        steps = self._build_steps(lang, src, out, odir, self.icon_var.get())
        text = "\n".join(" && ".join(s["cmd"]) for s in steps) if steps else "(no source)"
        self.cmd_text.delete("1.0", "end")
        self.cmd_text.insert("end", text)

    # -------- 自身保护 --------
    def _guard_self_target(self, odir, out):
        """避免打包产物覆盖/删除正在运行的自身（Windows 文件锁 + PyInstaller 清空 distpath）。"""
        odir_abs = os.path.abspath(odir)
        if FROZEN:
            cur = os.path.normcase(APP_EXE)
            base = os.path.normcase(odir_abs)
            # distpath 是自身所在目录（或其上级）时，PyInstaller 会 rmtree 掉本程序
            if cur == base or cur.startswith(base + os.sep):
                new_dir = os.path.join(APP_DIR, "dist_selfbuild")
                os.makedirs(new_dir, exist_ok=True)
                self._log("[!] " + T("self_dist").format(new=new_dir))
                odir_abs = new_dir
            target = os.path.normcase(os.path.join(odir_abs, out + EXE_EXT))
            if target == cur:
                new_out = out + "_new"
                self._log("[!] " + T("self_name").format(new=new_out))
                out = new_out
        return odir_abs, out

    # -------- 环境检查 --------
    def _ensure_pyinstaller(self, exe, ver):
        self._log("# python : %s (%s)" % (exe, ver))
        if not _has_module(exe, "PyInstaller"):
            self._log(T("py_missing_pkg"))
            self.root.update()
            proc = run_capture([exe, "-m", "pip", "install", "pyinstaller"])
            if proc.returncode != 0:
                self._log(_decode(proc.stdout).strip())
                self._log(_decode(proc.stderr).strip())
                self._log(T("py_install_fail").format(
                    cmd="%s -m pip install pyinstaller" % exe))
                messagebox.showerror(T("title"),
                                     T("py_install_fail").format(
                                         cmd="%s -m pip install pyinstaller" % exe))
                return False
            _PY_CACHE["done"] = False
        return True

    def check_env(self):
        self._log(T("env_check"))
        mode = "frozen (exe)" if FROZEN else "source (python)"
        self._log("%-18s %s" % ("runner", mode))
        py = find_python(refresh=True)
        if py:
            has = _has_module(py[0], "PyInstaller")
            self._log("%-18s %s (%s)" % ("python", py[0], py[1]))
            self._log("%-18s %s" % ("PyInstaller", T("env_ok") if has else T("env_missing")))
        else:
            self._log("%-18s %s" % ("python", T("env_missing")))
        self._log("-" * 46)
        for name, cfg in BUILDERS.items():
            tool = cfg["tool"]
            ok = bool(py) if tool is None else tool_exists(tool)
            miss = "" if ok else "   -> " + cfg["install"]
            self._log("%-10s %-15s %s%s" % (name, cfg["packager"],
                                            T("env_ok") if ok else T("env_missing"), miss))
        self._log("")

    # -------- 浏览 --------
    def browse_source(self):
        lang = self.lang_var.get()
        ext = BUILDERS[lang]["ext"]
        path = filedialog.askopenfilename(
            filetypes=[(lang, "*%s" % ext), (T("all_files"), "*.*")])
        if path:
            self.source_var.set(path)
            if not self.output_name_var.get():
                self.output_name_var.set(os.path.splitext(os.path.basename(path))[0])
            self._update_cmd()

    def browse_outdir(self):
        d = filedialog.askdirectory(title=T("select_output_dir"))
        if d:
            self.output_dir_var.set(d)
            self._update_cmd()

    def browse_icon(self):
        path = filedialog.askopenfilename(filetypes=[("Icon", "*.ico *.icns *.png")])
        if path:
            self.icon_var.set(path)
            self._update_cmd()

    # -------- 打包 --------
    def do_build(self):
        if self._busy:
            return
        src = self.source_var.get().strip().strip('"')
        if not src or not os.path.exists(src):
            messagebox.showwarning(T("title"), T("select_source_first"))
            return

        lang = self.lang_var.get()
        out = (self.output_name_var.get() or
               os.path.splitext(os.path.basename(src))[0]).strip()
        odir = self.output_dir_var.get().strip() or "dist"
        icon = self.icon_var.get().strip().strip('"')

        self._busy = True
        self.build_btn.config(state="disabled")
        try:
            if lang == "Python":
                py = find_python(refresh=True)
                if not py:
                    self._log(T("no_python"))
                    messagebox.showerror(T("title"), T("no_python"))
                    return
                self.python_exe = py[0]
                if not self._ensure_pyinstaller(py[0], py[1]):
                    return

            odir, out = self._guard_self_target(odir, out)
            os.makedirs(odir, exist_ok=True)

            steps = self._build_steps(lang, src, out, odir, icon)
            self._log("=" * 56)
            for i, step in enumerate(steps, 1):
                cmd = step["cmd"]
                self._log("[%d/%d] $ %s" % (i, len(steps), " ".join(cmd)))
                try:
                    proc = run_capture(cmd, cwd=step.get("cwd"), env=step.get("env"))
                except FileNotFoundError as e:
                    self._log("ERR: tool not found: %s" % e)
                    self._log(T("hint_install") + BUILDERS[lang]["install"])
                    messagebox.showerror(T("title"), "tool not found: %s\n%s%s" % (
                        cmd[0], T("hint_install"), BUILDERS[lang]["install"]))
                    return
                o, err = _decode(proc.stdout), _decode(proc.stderr)
                if o.strip():
                    self._log(o.rstrip())
                if err.strip():
                    self._log(("ERR: " if proc.returncode else "") + err.rstrip())
                if proc.returncode != 0:
                    self._log("[!] " + T("step_failed").format(n=i, code=proc.returncode))
                    self._log(T("build_failed"))
                    messagebox.showerror(T("title"), T("build_failed"))
                    return

            final = self._collect(lang, src, out, odir)
            self._log("")
            self._log(T("build_success") + final)
            messagebox.showinfo(T("title"), T("build_success") + final)
        finally:
            self._busy = False
            self.build_btn.config(state="normal")

    def _collect(self, lang, src, out, odir):
        """定位最终产物，必要时复制到输出目录根下。"""
        ext = EXE_EXT
        if lang == "Python" and not self.onefile_var.get():
            d = os.path.join(odir, out)
            return d if os.path.isdir(d) else odir

        mapping = {
            "Python": os.path.join(odir, out + ext),
            "Node.js": os.path.join(odir, out),
            "Java": os.path.join(odir, out + ".jar"),
            "C / C++": os.path.join(odir, out + ext),
            "C#": os.path.join(odir, os.path.splitext(os.path.basename(src))[0] + ".dll"),
            "Go": os.path.join(odir, out + ext),
            "Rust": os.path.join(os.path.dirname(os.path.abspath(src)), "target", "release",
                                 os.path.splitext(os.path.basename(src))[0] + ext),
        }
        src_file = mapping.get(lang)
        if src_file and os.path.exists(src_file):
            dst = os.path.join(odir, os.path.basename(src_file))
            if os.path.normcase(os.path.abspath(src_file)) != os.path.normcase(os.path.abspath(dst)):
                shutil.copy2(src_file, dst)
            return dst
        return odir


if __name__ == "__main__":
    try:
        import multiprocessing
        multiprocessing.freeze_support()   # PyInstaller 冻结后多进程更稳
    except Exception:
        pass
    ensure_pyinstaller_dev()
    root = tk.Tk()
    app = BuilderApp(root)
    root.mainloop()
