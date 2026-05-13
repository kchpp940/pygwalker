"""
PyGWalker 统一开发环境管理脚本

提供一套可重复的本地开发脚本，减少手动配置成本：
- 环境初始化
- 前端构建/开发服务器
- Jupyter 和 Web 服务器调试
- 完整的 dry-run 验证模式
"""

import sys
import os
import subprocess
import shutil
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class Color(Enum):
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"


def print_color(text: str, color: Color = Color.RESET):
    """带颜色的打印"""
    print(f"{color.value}{text}{Color.RESET.value}")


def print_header(title: str):
    """打印步骤标题"""
    print()
    print("=" * 70)
    print_color(f"  {title}", Color.BOLD)
    print("=" * 70)
    print()


def print_step(step: str, status: str = "INFO", detail: str = ""):
    """打印步骤信息"""
    icons = {
        "INFO": "ℹ",
        "OK": "✓",
        "FAIL": "✗",
        "WARN": "!",
        "RUN": "»",
        "DRY": "…",
    }
    colors = {
        "INFO": Color.BLUE,
        "OK": Color.GREEN,
        "FAIL": Color.RED,
        "WARN": Color.YELLOW,
        "RUN": Color.CYAN,
        "DRY": Color.YELLOW,
    }
    icon = icons.get(status, "ℹ")
    color = colors.get(status, Color.BLUE)
    if detail:
        print_color(f"  {icon} {step} - {detail}", color)
    else:
        print_color(f"  {icon} {step}", color)


class StageStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    name: str
    status: StageStatus = StageStatus.NOT_STARTED
    duration: float = 0.0
    details: str = ""
    error: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class DevConfig:
    """开发环境配置"""
    project_root: Path
    app_dir: Path
    pygwalker_dir: Path
    templates_dir: Path
    dist_dir: Path
    examples_dir: Path
    venv_dir: Optional[Path] = None

    @classmethod
    def from_project_root(cls, project_root: Path) -> "DevConfig":
        venv_dir = project_root / "venv"
        if not venv_dir.exists():
            conda_env = os.environ.get("CONDA_PREFIX")
            if conda_env:
                venv_dir = Path(conda_env)

        return cls(
            project_root=project_root,
            app_dir=project_root / "app",
            pygwalker_dir=project_root / "pygwalker",
            templates_dir=project_root / "pygwalker" / "templates",
            dist_dir=project_root / "pygwalker" / "templates" / "dist",
            examples_dir=project_root / "examples",
            venv_dir=venv_dir if venv_dir.exists() else None,
        )


@dataclass
class ValidationContext:
    """验证上下文"""
    dry_run: bool = False
    verbose: bool = False
    results: List[StageResult] = field(default_factory=list)
    _start_times: Dict[str, float] = field(default_factory=dict)

    def add_result(self, result: StageResult):
        self.results.append(result)

    def start_timer(self, name: str):
        self._start_times[name] = time.time()

    def stop_timer(self, name: str) -> float:
        if name in self._start_times:
            return time.time() - self._start_times[name]
        return 0.0

    def get_summary(self) -> Tuple[int, int, int]:
        passed = sum(1 for r in self.results if r.status == StageStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == StageStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == StageStatus.SKIPPED)
        return passed, failed, skipped


class CommandRunner:
    """命令执行器"""

    def __init__(self, config: DevConfig, ctx: Optional[ValidationContext] = None):
        self.config = config
        self.ctx = ctx

    def run(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        capture_output: bool = False,
        env: Optional[dict] = None,
        check: bool = True,
    ) -> Tuple[int, List[str], str]:
        """运行命令"""
        cwd_str = str(cwd) if cwd else str(self.config.project_root)
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        print_step(f"执行: {' '.join(cmd)}", "RUN")

        try:
            if capture_output:
                result = subprocess.run(
                    cmd,
                    cwd=cwd_str,
                    capture_output=True,
                    text=True,
                    env=full_env,
                )
                stdout_lines = result.stdout.strip().split("\n") if result.stdout else []
                stderr = result.stderr.strip()
                returncode = result.returncode
            else:
                result = subprocess.run(cmd, cwd=cwd_str, env=full_env)
                returncode = result.returncode
                stdout_lines = []
                stderr = ""

            if check and returncode != 0:
                print_step(f"命令执行失败 (退出码: {returncode})", "FAIL")
                if stderr:
                    print_color(f"    {stderr}", Color.RED)
                sys.exit(returncode)

            return returncode, stdout_lines, stderr
        except FileNotFoundError as e:
            print_step(f"命令未找到: {e}", "FAIL")
            sys.exit(1)

    def run_in_venv(self, cmd: List[str], **kwargs) -> Tuple[int, List[str], str]:
        """在虚拟环境中运行 Python 命令"""
        if self.config.venv_dir:
            if sys.platform == "win32":
                python_exe = self.config.venv_dir / "Scripts" / "python.exe"
            else:
                python_exe = self.config.venv_dir / "bin" / "python"
            return self.run([str(python_exe)] + cmd[1:], **kwargs)
        return self.run(cmd, **kwargs)


class Validator:
    """验证器 - 用于 dry-run 模式"""

    def __init__(self, config: DevConfig, ctx: ValidationContext):
        self.config = config
        self.ctx = ctx
        self.runner = CommandRunner(config, ctx)

    def _check_command_exists(self, cmd: str) -> bool:
        """检查命令是否存在"""
        return shutil.which(cmd) is not None

    def _run_stage(
        self,
        name: str,
        check_func,
        suggestion: str = "",
    ) -> StageResult:
        """运行单个验证阶段"""
        result = StageResult(name=name)
        self.ctx.start_timer(name)

        print_header(f"阶段: {name}")

        try:
            success, details, error = check_func()
            result.duration = self.ctx.stop_timer(name)
            result.details = details
            result.error = error
            result.suggestion = suggestion if not success else None

            if success:
                result.status = StageStatus.PASSED
                print_step(f"{name} ✓", "OK", f"({result.duration:.2f}s)")
            else:
                result.status = StageStatus.FAILED
                print_step(f"{name} ✗", "FAIL", f"({result.duration:.2f}s)")
                if error:
                    print_color(f"    错误: {error}", Color.RED)
                if suggestion:
                    print_color(f"    建议: {suggestion}", Color.YELLOW)
        except Exception as e:
            result.duration = self.ctx.stop_timer(name)
            result.status = StageStatus.FAILED
            result.error = str(e)
            print_step(f"{name} ✗", "FAIL", f"({result.duration:.2f}s)")
            print_color(f"    异常: {e}", Color.RED)

        self.ctx.add_result(result)
        return result

    def check_python(self) -> Tuple[bool, str, Optional[str]]:
        """检查 Python 环境"""
        print_step("检查 Python 版本...", "INFO")

        version = sys.version_info[:2]
        min_version = (3, 7)

        if version >= min_version:
            details = f"Python {version[0]}.{version[1]} (当前解释器: {sys.executable})"
            print_step(details, "OK")
            return True, details, None
        else:
            error = f"Python 版本过低: {version[0]}.{version[1]} (需要 >= {min_version[0]}.{min_version[1]})"
            print_step(error, "FAIL")
            return False, "", error

    def check_node(self) -> Tuple[bool, str, Optional[str]]:
        """检查 Node.js"""
        print_step("检查 Node.js...", "INFO")

        if not self._check_command_exists("node"):
            error = "Node.js 未安装或不在 PATH 中"
            print_step(error, "FAIL")
            return False, "", error

        try:
            _, stdout, _ = self.runner.run(["node", "--version"], capture_output=True)
            version_str = stdout[0].lstrip("v")
            parts = version_str.split(".")
            major = int(parts[0])
            minor = int(parts[1])

            min_version = (16, 0)
            if (major, minor) >= min_version:
                details = f"Node.js {major}.{minor}"
                print_step(details, "OK")
                return True, details, None
            else:
                error = f"Node.js 版本过低: {major}.{minor} (需要 >= {min_version[0]}.{min_version[1]})"
                print_step(error, "FAIL")
                return False, "", error
        except Exception as e:
            return False, "", str(e)

    def check_yarn(self) -> Tuple[bool, str, Optional[str]]:
        """检查 Yarn"""
        print_step("检查 Yarn...", "INFO")

        if not self._check_command_exists("yarn"):
            print_step("Yarn 未找到 (将尝试使用 npm)", "WARN")
            return True, "Yarn 未找到，可使用 npm 替代", None

        try:
            _, stdout, _ = self.runner.run(["yarn", "--version"], capture_output=True)
            details = f"Yarn {stdout[0]}"
            print_step(details, "OK")
            return True, details, None
        except Exception as e:
            return False, "", str(e)

    def check_pip_packages(self) -> Tuple[bool, str, Optional[str]]:
        """检查关键 Python 包"""
        print_step("检查 Python 依赖...", "INFO")

        essential_packages = ["pygwalker", "jupyterlab"]
        missing = []

        for pkg in essential_packages:
            try:
                __import__(pkg if pkg != "jupyterlab" else "jupyter_server")
                print_step(f"  ✓ {pkg} 已安装", "INFO")
            except ImportError:
                missing.append(pkg)
                print_step(f"  ✗ {pkg} 未安装", "FAIL")

        if missing:
            error = f"缺少关键包: {', '.join(missing)}"
            return False, "", error

        return True, f"已安装 {len(essential_packages)} 个关键包", None

    def check_app_directory(self) -> Tuple[bool, str, Optional[str]]:
        """检查前端目录"""
        print_step("检查前端项目结构...", "INFO")

        if not self.config.app_dir.exists():
            error = f"前端目录不存在: {self.config.app_dir}"
            print_step(error, "FAIL")
            return False, "", error

        package_json = self.config.app_dir / "package.json"
        if not package_json.exists():
            error = f"缺少 package.json: {package_json}"
            print_step(error, "FAIL")
            return False, "", error

        print_step(f"  ✓ app/ 目录存在", "INFO")
        print_step(f"  ✓ package.json 存在", "INFO")

        return True, "前端项目结构完整", None

    def check_node_modules(self) -> Tuple[bool, str, Optional[str]]:
        """检查 node_modules"""
        print_step("检查前端依赖安装...", "INFO")

        node_modules = self.config.app_dir / "node_modules"
        if not node_modules.exists():
            print_step("  node_modules 不存在", "WARN")
            return False, "", "node_modules 未安装"

        print_step(f"  ✓ node_modules 存在", "INFO")
        return True, "前端依赖已安装", None

    def check_dist_artifacts(self) -> Tuple[bool, str, Optional[str]]:
        """检查模板产物"""
        print_step("检查构建产物...", "INFO")

        dist_dir = self.config.dist_dir

        if not dist_dir.exists():
            print_step(f"  dist 目录不存在: {dist_dir}", "WARN")
            return False, "", "dist 目录不存在，需要先构建前端"

        expected_files = [
            "pygwalker-app.iife.js",
            "pygwalker-app.es.js",
        ]

        found = []
        missing = []

        for f in expected_files:
            if (dist_dir / f).exists():
                found.append(f)
            else:
                missing.append(f)

        for f in found:
            print_step(f"  ✓ {f}", "INFO")
        for f in missing:
            print_step(f"  ✗ {f}", "FAIL")

        if missing:
            error = f"缺少构建产物: {', '.join(missing)}"
            return False, "", error

        extra_js = list(dist_dir.glob("*.js"))
        return True, f"共 {len(extra_js)} 个 JS 文件", None

    def check_templates(self) -> Tuple[bool, str, Optional[str]]:
        """检查 HTML 模板"""
        print_step("检查 HTML 模板...", "INFO")

        templates_dir = self.config.templates_dir
        expected_templates = [
            "index.html",
            "pygwalker_iframe.html",
            "pygwalker_main_page.html",
        ]

        found = []
        missing = []

        for t in expected_templates:
            if (templates_dir / t).exists():
                found.append(t)
                print_step(f"  ✓ {t}", "INFO")
            else:
                missing.append(t)
                print_step(f"  ✗ {t}", "FAIL")

        if missing:
            error = f"缺少模板: {', '.join(missing)}"
            return False, "", error

        return True, f"{len(found)} 个模板文件完整", None

    def check_examples(self) -> Tuple[bool, str, Optional[str]]:
        """检查示例文件"""
        print_step("检查示例文件...", "INFO")

        examples_dir = self.config.examples_dir
        if not examples_dir.exists():
            error = f"示例目录不存在: {examples_dir}"
            print_step(error, "FAIL")
            return False, "", error

        notebooks = list(examples_dir.glob("*.ipynb"))
        py_files = list(examples_dir.glob("*.py"))

        print_step(f"  ✓ {len(notebooks)} 个 Jupyter notebook", "INFO")
        print_step(f"  ✓ {len(py_files)} 个 Python 示例", "INFO")

        key_examples = [
            ("jupyter_demo.ipynb", "Jupyter 示例"),
            ("web_server_demo.py", "FastAPI Web 示例"),
        ]

        for name, desc in key_examples:
            if (examples_dir / name).exists():
                print_step(f"  ✓ {desc}: {name}", "INFO")
            else:
                print_step(f"  ! {desc}: {name} (缺失)", "WARN")

        return True, f"{len(notebooks)} notebooks, {len(py_files)} Python 脚本", None

    def check_project_structure(self) -> Tuple[bool, str, Optional[str]]:
        """检查完整项目结构"""
        print_step("检查项目结构...", "INFO")

        essential_dirs = [
            ("pygwalker/", "Python 包"),
            ("app/", "前端应用"),
            ("examples/", "示例"),
            ("tests/", "测试"),
        ]

        all_ok = True
        for dir_name, desc in essential_dirs:
            path = self.config.project_root / dir_name
            if path.exists():
                print_step(f"  ✓ {desc}: {dir_name}", "INFO")
            else:
                print_step(f"  ✗ {desc}: {dir_name} (缺失)", "FAIL")
                all_ok = False

        if not all_ok:
            return False, "", "项目结构不完整"

        return True, "项目结构完整", None


class EnvironmentChecker:
    """环境检查器"""

    def __init__(self, runner: CommandRunner):
        self.runner = runner
        self.config = runner.config

    def check_python(self, min_version: Tuple[int, int] = (3, 7)) -> bool:
        """检查 Python 版本"""
        print_step("检查 Python 环境...", "INFO")

        version = sys.version_info[:2]
        if version >= min_version:
            print_step(f"Python {version[0]}.{version[1]} ✓", "OK")
            return True
        else:
            print_step(f"Python 版本过低: {version[0]}.{version[1]} (需要 >= {min_version[0]}.{min_version[1]})", "FAIL")
            return False

    def check_node(self, min_version: Tuple[int, int] = (16, 0)) -> bool:
        """检查 Node.js 版本"""
        print_step("检查 Node.js 环境...", "INFO")

        try:
            _, stdout, _ = self.runner.run(["node", "--version"], capture_output=True)
            version_str = stdout[0].lstrip("v")
            version_parts = version_str.split(".")
            major = int(version_parts[0])
            minor = int(version_parts[1])

            if (major, minor) >= min_version:
                print_step(f"Node.js {major}.{minor} ✓", "OK")
                return True
            else:
                print_step(f"Node.js 版本过低: {major}.{minor} (需要 >= {min_version[0]}.{min_version[1]})", "FAIL")
                return False
        except SystemExit:
            print_step("Node.js 未安装或不在 PATH 中", "FAIL")
            return False

    def check_yarn(self) -> bool:
        """检查 Yarn"""
        print_step("检查 Yarn...", "INFO")

        if shutil.which("yarn"):
            _, stdout, _ = self.runner.run(["yarn", "--version"], capture_output=True)
            print_step(f"Yarn {stdout[0]} ✓", "OK")
            return True
        else:
            print_step("Yarn 未安装", "WARN")
            return False

    def check_all(self) -> bool:
        """运行所有环境检查"""
        print_header("环境检查")

        python_ok = self.check_python()
        node_ok = self.check_node()
        yarn_ok = self.check_yarn()

        all_ok = python_ok and node_ok and yarn_ok

        if all_ok:
            print_step("环境检查通过 ✓", "OK")
        else:
            print_step("环境检查存在问题", "FAIL")

        return all_ok


class EnvironmentSetup:
    """环境设置"""

    def __init__(self, runner: CommandRunner):
        self.runner = runner
        self.config = runner.config

    def create_venv(self):
        """创建虚拟环境"""
        print_header("创建 Python 虚拟环境")

        venv_dir = self.config.project_root / "venv"

        if venv_dir.exists():
            print_step("虚拟环境已存在", "INFO")
            self.config.venv_dir = venv_dir
            return

        print_step("创建虚拟环境...", "RUN")
        self.runner.run([sys.executable, "-m", "venv", str(venv_dir)])
        self.config.venv_dir = venv_dir
        print_step("虚拟环境创建完成 ✓", "OK")

        activate_cmd = "source venv/bin/activate" if sys.platform != "win32" else "venv\\Scripts\\activate"
        print_step(f"激活命令: {activate_cmd}", "INFO")

    def install_python_deps(self, editable: bool = True, extras: List[str] = None):
        """安装 Python 依赖"""
        print_header("安装 Python 依赖")

        extras = extras or ["dev"]
        extras_str = ",".join(extras)

        if editable:
            install_cmd = ["pip", "install", "-e", f".[{extras_str}]"]
        else:
            install_cmd = ["pip", "install", f".[{extras_str}]"]

        print_step("安装 pygwalker 依赖...", "RUN")
        self.runner.run_in_venv(install_cmd)
        print_step("Python 依赖安装完成 ✓", "OK")

    def install_frontend_deps(self):
        """安装前端依赖"""
        print_header("安装前端依赖")

        if not self.config.app_dir.exists():
            print_step(f"前端目录不存在: {self.config.app_dir}", "FAIL")
            return

        print_step("安装前端依赖...", "RUN")
        self.runner.run(["yarn", "install"], cwd=self.config.app_dir)
        print_step("前端依赖安装完成 ✓", "OK")

    def setup_all(self, create_venv: bool = True):
        """完整环境设置"""
        if create_venv:
            self.create_venv()
        self.install_python_deps()
        self.install_frontend_deps()

        print_header("环境设置完成")
        print_step("开发环境已准备就绪！", "OK")
        print()
        print("下一步:")
        print("  1. 激活虚拟环境: source venv/bin/activate")
        print("  2. 构建前端: pygwalker dev build")
        print("  3. 验证开发环境: pygwalker dev all --dry-run")


class FrontendManager:
    """前端管理"""

    def __init__(self, runner: CommandRunner):
        self.runner = runner
        self.config = runner.config

    def build(self, mode: str = "all"):
        """构建前端"""
        print_header(f"构建前端 ({mode})")

        if mode == "app":
            print_step("构建主应用...", "RUN")
            self.runner.run(["yarn", "build:app"], cwd=self.config.app_dir)
        elif mode == "all":
            print_step("完整构建...", "RUN")
            self.runner.run(["yarn", "build"], cwd=self.config.app_dir)
        else:
            print_step(f"未知的构建模式: {mode}", "FAIL")
            return

        if self.config.dist_dir.exists():
            print_step(f"构建产物: {self.config.dist_dir}", "OK")
            js_files = list(self.config.dist_dir.glob("*.js"))
            print_step(f"生成 {len(js_files)} 个 JS 文件", "INFO")
        else:
            print_step("构建完成但未找到 dist 目录", "WARN")

    def start_dev_server(self, host: bool = False, port: Optional[int] = None):
        """启动 Vite 开发服务器"""
        print_header("启动前端开发服务器")

        cmd = ["yarn", "dev:server"] if host else ["yarn", "dev"]

        env = {}
        if port:
            env["PORT"] = str(port)

        print_step("Vite 开发服务器将在 http://localhost:8769/pyg_dev_app/ 运行", "INFO")
        print_step("按 Ctrl+C 停止", "INFO")
        print()

        self.runner.run(cmd, cwd=self.config.app_dir, env=env if env else None)


class DebugServer:
    """调试服务器"""

    def __init__(self, runner: CommandRunner):
        self.runner = runner
        self.config = runner.config

    def start_jupyter_lab(self, port: int = 8888, dev_mode: bool = True):
        """启动 JupyterLab"""
        print_header("启动 JupyterLab")

        env = {}
        cmd = ["jupyter", "lab", f"--port={port}"]

        if dev_mode:
            print_step("配置开发模式 (使用 Vite 热重载)...", "INFO")
            env["PYGWALKER_DEV_MODE"] = "1"
            server_proxy = (
                '--ServerProxy.servers={"pyg_dev_app": {"command": [], '
                '"absolute_url": true, "port": 8769, "timeout": 30}}'
            )
            cmd.append(server_proxy)

        print_step(f"JupyterLab 将在 http://localhost:{port} 运行", "INFO")
        print_step("提示: 在 Notebook 中使用以下代码启用开发模式:", "INFO")
        print()
        print("    from pygwalker.services.global_var import GlobalVarManager")
        print("    GlobalVarManager.set_component_url('/pyg_dev_app/')")
        print("    import pygwalker as pyg")
        print()
        print_step("按 Ctrl+C 停止", "INFO")
        print()

        self.runner.run_in_venv(cmd, env=env)

    def start_web_server(self, port: int = 8000):
        """启动 Web 服务器调试 (FastAPI 示例)"""
        print_header("启动 Web 服务器 (FastAPI 示例)")

        demo_file = self.config.examples_dir / "web_server_demo.py"
        if not demo_file.exists():
            print_step(f"示例文件不存在: {demo_file}", "FAIL")
            return

        print_step(f"Web 服务器将在 http://localhost:{port} 运行", "INFO")
        print_step(f"访问: http://127.0.0.1:{port}/pyg_html/test0", "INFO")
        print_step("按 Ctrl+C 停止", "INFO")
        print()

        os.chdir(self.config.examples_dir)
        self.runner.run_in_venv(
            ["uvicorn", "web_server_demo:app", "--reload", f"--port={port}"],
            cwd=self.config.examples_dir,
        )

    def open_examples(self):
        """打开示例目录"""
        print_header("示例")

        notebooks = list(self.config.examples_dir.glob("*.ipynb"))
        py_examples = list(self.config.examples_dir.glob("*.py"))

        print_step("可用示例:", "INFO")
        print()
        print("Notebooks:")
        for nb in notebooks:
            print(f"  - {nb.name}")

        print()
        print("Python 脚本:")
        for py in py_examples:
            print(f"  - {py.name}")

        print()
        print_step("使用 'pygwalker dev jupyter' 启动 JupyterLab 打开这些示例", "INFO")


class DevValidator:
    """开发环境完整验证器"""

    def __init__(self, config: DevConfig, verbose: bool = False):
        self.config = config
        self.ctx = ValidationContext(verbose=verbose, dry_run=True)
        self.validator = Validator(config, self.ctx)

    def run_all_stages(self) -> bool:
        """运行所有验证阶段"""
        stages = [
            ("Python 环境", self.validator.check_python, "请安装 Python 3.7+"),
            ("Node.js 环境", self.validator.check_node, "请安装 Node.js 16+"),
            ("Yarn", self.validator.check_yarn, "安装: npm install -g yarn"),
            ("项目结构", self.validator.check_project_structure, "检查项目目录是否完整"),
            ("前端项目", self.validator.check_app_directory, "检查 app/ 目录是否存在"),
            ("前端依赖", self.validator.check_node_modules, "运行: pygwalker dev setup 或 cd app && yarn install"),
            ("Python 依赖", self.validator.check_pip_packages, "运行: pip install -e '.[dev]'"),
            ("HTML 模板", self.validator.check_templates, "模板文件应存在于 pygwalker/templates/"),
            ("构建产物", self.validator.check_dist_artifacts, "运行: pygwalker dev build"),
            ("示例文件", self.validator.check_examples, "检查 examples/ 目录"),
        ]

        print_header("PyGWalker 开发环境验证 (Dry-Run)")
        print_step(f"项目根目录: {self.config.project_root}", "INFO")
        if self.config.venv_dir:
            print_step(f"虚拟环境: {self.config.venv_dir}", "INFO")
        else:
            print_step("虚拟环境: 未检测到 (使用系统 Python)", "WARN")
        print()

        for name, check_func, suggestion in stages:
            self.validator._run_stage(name, check_func, suggestion)

        return self.print_summary()

    def print_summary(self) -> bool:
        """打印验证摘要"""
        print_header("验证摘要")

        passed, failed, skipped = self.ctx.get_summary()
        total = len(self.ctx.results)
        total_duration = sum(r.duration for r in self.ctx.results)

        print(f"  总计: {total} 个阶段")
        print_color(f"  ✓ 通过: {passed}", Color.GREEN)
        print_color(f"  ✗ 失败: {failed}", Color.RED)
        if skipped > 0:
            print_color(f"  ○ 跳过: {skipped}", Color.YELLOW)
        print(f"  耗时: {total_duration:.2f}s")
        print()

        if failed > 0:
            print_color("  失败阶段详情:", Color.RED)
            for r in self.ctx.results:
                if r.status == StageStatus.FAILED:
                    print()
                    print_color(f"    ✗ {r.name}", Color.RED)
                    if r.error:
                        print_color(f"      错误: {r.error}", Color.RED)
                    if r.suggestion:
                        print_color(f"      建议: {r.suggestion}", Color.YELLOW)
            print()
            print_color("=" * 70, Color.RED)
            print_color("  验证失败！请修复上述问题后重试。", Color.RED)
            print_color("=" * 70, Color.RED)
            return False
        else:
            print_color("=" * 70, Color.GREEN)
            print_color("  ✓ 所有验证通过！开发环境已就绪。", Color.GREEN)
            print_color("=" * 70, Color.GREEN)
            print()
            print("下一步:")
            print("  1. 启动前端开发服务器: pygwalker dev frontend")
            print("  2. 启动 JupyterLab: pygwalker dev jupyter")
            print("  3. 或运行完整构建: pygwalker dev build")
            return True


class DevCLI:
    """开发 CLI 主入口"""

    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.config = DevConfig.from_project_root(self.project_root)
        self.runner = CommandRunner(self.config)
        self.env_checker = EnvironmentChecker(self.runner)
        self.env_setup = EnvironmentSetup(self.runner)
        self.frontend = FrontendManager(self.runner)
        self.debug = DebugServer(self.runner)

    def cmd_check(self, args):
        """检查开发环境"""
        self.env_checker.check_all()

    def cmd_setup(self, args):
        """完整设置开发环境"""
        create_venv = getattr(args, "no_venv", False) is False
        self.env_setup.setup_all(create_venv=create_venv)

    def cmd_build(self, args):
        """构建前端"""
        mode = getattr(args, "mode", "all")
        self.frontend.build(mode=mode)

    def cmd_frontend(self, args):
        """启动前端开发服务器"""
        host = getattr(args, "host", False)
        port = getattr(args, "port", None)
        self.frontend.start_dev_server(host=host, port=port)

    def cmd_jupyter(self, args):
        """启动 JupyterLab"""
        port = getattr(args, "port", 8888)
        dev_mode = not getattr(args, "no_dev", False)
        self.debug.start_jupyter_lab(port=port, dev_mode=dev_mode)

    def cmd_web(self, args):
        """启动 Web 服务器"""
        port = getattr(args, "port", 8000)
        self.debug.start_web_server(port=port)

    def cmd_examples(self, args):
        """显示可用示例"""
        self.debug.open_examples()

    def cmd_bootstrap(self, args):
        """完整开发流程引导 (按顺序展示 setup -> build -> template -> 示例启动"""
        dry_run = getattr(args, "dry_run", False)
        verbose = getattr(args, "verbose", False)

        if dry_run:
            self._run_bootstrap_dry_run(verbose)
        else:
            self._run_bootstrap_guide()

    def _run_bootstrap_guide(self):
        """运行完整开发流程指南"""
        print_header("PyGWalker 完整开发流程")
        print()
        print("本引导将按顺序展示以下步骤：")
        print()
        print_color("  步骤 1: 环境准备 (Setup)", Color.CYAN)
        print("    pygwalker dev setup")
        print("    或将手动执行:")
        print("      python -m venv venv")
        print("      source venv/bin/activate")
        print("      pip install -e '.[dev]'")
        print("      cd app && yarn install")
        print()
        print_color("  步骤 2: 前端构建 (Frontend Build)", Color.CYAN)
        print("    pygwalker dev build")
        print("    或手动执行:")
        print("      cd app && yarn build")
        print()
        print_color("  步骤 3: 模板产物校验 (Template)", Color.CYAN)
        print("    产物位置: pygwalker/templates/dist/")
        print("    期望产物:")
        print("      - pygwalker-app.iife.js")
        print("      - pygwalker-app.es.js")
        print("      - dsl-to-workflow.umd.js")
        print("      - vega-to-dsl.umd.js")
        print()
        print_color("  步骤 4: 示例调试 (Examples)", Color.CYAN)
        print("    方式 A - Jupyter Notebook:")
        print("      pip install jupyterlab  # 如需要")
        print("      pygwalker dev jupyter")
        print()
        print("    方式 B - FastAPI Web 服务:")
        print("      pip install uvicorn fastapi  # 如需要")
        print("      pygwalker dev web")
        print()
        print("    查看所有示例:")
        print("      pygwalker dev examples")
        print()
        print_step("使用 --dry-run 参数进行预检查:", "INFO")
        print("  pygwalker dev bootstrap --dry-run")
        print()

    def _run_bootstrap_dry_run(self, verbose: bool):
        """运行 bootstrap dry-run 验证 - 展示真实命令执行计划"""
        print_header("PyGWalker 开发流程预检查 (Bootstrap Dry-Run)")
        print_step(f"项目根目录: {self.config.project_root}", "INFO")
        if self.config.venv_dir:
            print_step(f"虚拟环境: {self.config.venv_dir}", "INFO")
        else:
            print_step("虚拟环境: 未检测到 (将使用系统/当前环境)", "WARN")
        print()

        plan = self._generate_execution_plan()
        return self._display_execution_plan(plan)

    def _generate_execution_plan(self) -> List[Dict[str, Any]]:
        """生成完整的执行计划"""
        plan = []

        venv_dir = self.config.project_root / "venv"
        activate_cmd = "source venv/bin/activate" if sys.platform != "win32" else "venv\\Scripts\\activate"

        plan.append({
            "step": 1,
            "name": "环境准备 (Environment Setup)",
            "commands": [
                {
                    "desc": "创建虚拟环境 (如不存在)",
                    "cmd": f"python -m venv {venv_dir}",
                    "condition": not venv_dir.exists(),
                    "check_msg": "虚拟环境已存在" if venv_dir.exists() else "需要创建虚拟环境",
                },
                {
                    "desc": "激活虚拟环境",
                    "cmd": activate_cmd,
                    "condition": True,
                    "check_msg": "手动执行",
                },
                {
                    "desc": "安装 Python 依赖",
                    "cmd": "pip install -e '.[dev]'",
                    "condition": not self._check_pip_package("pygwalker"),
                    "check_msg": "pygwalker 已安装" if self._check_pip_package("pygwalker") else "需要安装",
                },
                {
                    "desc": "安装前端依赖",
                    "cmd": "cd app && yarn install",
                    "condition": not (self.config.app_dir / "node_modules").exists(),
                    "check_msg": "node_modules 已存在" if (self.config.app_dir / "node_modules").exists() else "需要安装",
                },
            ],
        })

        plan.append({
            "step": 2,
            "name": "前端构建 (Frontend Build)",
            "commands": [
                {
                    "desc": "构建所有前端资源",
                    "cmd": "cd app && yarn build",
                    "condition": not self._check_frontend_artifacts(),
                    "check_msg": "构建产物已完整" if self._check_frontend_artifacts() else "需要构建",
                },
                {
                    "desc": "快速构建 (仅主应用)",
                    "cmd": "cd app && yarn build:app",
                    "condition": not self._check_main_app_artifacts(),
                    "check_msg": "主应用已构建" if self._check_main_app_artifacts() else "需要构建",
                },
            ],
        })

        plan.append({
            "step": 3,
            "name": "模板产物校验 (Template/Artifacts Verification)",
            "commands": [
                {
                    "desc": "检查 dist 目录",
                    "cmd": f"ls -la {self.config.dist_dir}",
                    "condition": False,
                    "check_msg": self._check_dist_status(),
                },
                {
                    "desc": "检查 HTML 模板",
                    "cmd": f"ls -la {self.config.templates_dir}/*.html",
                    "condition": False,
                    "check_msg": self._check_templates_status(),
                },
            ],
        })

        plan.append({
            "step": 4,
            "name": "示例调试 (Examples & Debug)",
            "commands": [
                {
                    "desc": "安装 JupyterLab (如缺失)",
                    "cmd": "pip install jupyterlab",
                    "condition": not self._check_jupyterlab_ready(),
                    "check_msg": "JupyterLab 已安装" if self._check_jupyterlab_ready() else "需要安装",
                },
                {
                    "desc": "安装 FastAPI/uvicorn (如缺失)",
                    "cmd": "pip install uvicorn fastapi",
                    "condition": not self._check_fastapi_ready(),
                    "check_msg": "FastAPI 可用" if self._check_fastapi_ready() else "需要安装",
                },
                {
                    "desc": "查看所有示例",
                    "cmd": "pygwalker dev examples",
                    "condition": False,
                    "check_msg": self._check_examples_status(),
                },
            ],
        })

        return plan

    def _display_execution_plan(self, plan: List[Dict[str, Any]]) -> bool:
        """展示执行计划"""
        all_ready = True
        total_commands = 0
        commands_to_run = 0

        for step in plan:
            print_header(f"步骤 {step['step']}: {step['name']}")
            print()

            for cmd_info in step["commands"]:
                total_commands += 1

                status_color = Color.GREEN if not cmd_info["condition"] else Color.YELLOW
                status_icon = "✓" if not cmd_info["condition"] else "›"
                needs_execution = cmd_info["condition"]

                if needs_execution:
                    commands_to_run += 1
                    all_ready = False

                print_color(f"  {status_icon} {cmd_info['desc']}", status_color)
                print_color(f"    命令: {cmd_info['cmd']}", Color.CYAN)

                check_status = cmd_info["check_msg"]
                if needs_execution:
                    print_color(f"    状态: 需要执行 - {check_status}", Color.YELLOW)
                else:
                    print_color(f"    状态: 已就绪 - {check_status}", Color.GREEN)
                print()

        print_header("执行计划摘要")
        print(f"  总计步骤: {len(plan)}")
        print(f"  总计命令: {total_commands}")
        print_color(f"  需要执行: {commands_to_run}", Color.YELLOW if commands_to_run > 0 else Color.GREEN)
        print_color(f"  已就绪: {total_commands - commands_to_run}", Color.GREEN)
        print()

        if all_ready:
            print_color("=" * 70, Color.GREEN)
            print_color("  ✓ 所有步骤已就绪！开发环境完整。", Color.GREEN)
            print_color("=" * 70, Color.GREEN)
            print()
            print("下一步:")
            print("  1. 启动前端开发服务器: pygwalker dev frontend")
            print("  2. 启动 JupyterLab: pygwalker dev jupyter")
            print("  3. 或查看所有可用命令: pygwalker dev --help")
            sys.exit(0)
        else:
            print_color("=" * 70, Color.YELLOW)
            print_color(f"  还有 {commands_to_run} 个命令需要执行。", Color.YELLOW)
            print_color("=" * 70, Color.YELLOW)
            print()
            print("快速执行命令:")
            quick_commands = [
                "pygwalker dev setup          # 完整环境设置",
                "pygwalker dev build          # 前端构建",
                "pygwalker dev all --dry-run  # 详细环境检查",
            ]
            for cmd in quick_commands:
                print_color(f"  {cmd}", Color.CYAN)
            sys.exit(1)

    def _check_pip_package(self, name: str) -> bool:
        """检查 Python 包是否安装"""
        try:
            __import__(name if name != "jupyterlab" else "jupyter_server")
            return True
        except ImportError:
            return False

    def _check_frontend_artifacts(self) -> bool:
        """检查所有前端构建产物"""
        dist_dir = self.config.dist_dir
        required = [
            "pygwalker-app.iife.js",
            "pygwalker-app.es.js",
            "dsl-to-workflow.umd.js",
            "vega-to-dsl.umd.js",
        ]
        return all((dist_dir / f).exists() for f in required)

    def _check_main_app_artifacts(self) -> bool:
        """检查主应用构建产物"""
        dist_dir = self.config.dist_dir
        required = [
            "pygwalker-app.iife.js",
            "pygwalker-app.es.js",
        ]
        return all((dist_dir / f).exists() for f in required)

    def _check_dist_status(self) -> str:
        """检查 dist 目录状态"""
        dist_dir = self.config.dist_dir
        if not dist_dir.exists():
            return "dist 目录不存在"

        js_files = list(dist_dir.glob("*.js"))
        total_size = sum(f.stat().st_size for f in js_files) / 1024 / 1024
        return f"{len(js_files)} 个 JS 文件, 总计 {total_size:.2f} MB"

    def _check_templates_status(self) -> str:
        """检查模板状态"""
        templates_dir = self.config.templates_dir
        required = ["index.html", "pygwalker_iframe.html", "pygwalker_main_page.html"]
        found = sum(1 for f in required if (templates_dir / f).exists())
        return f"{found}/{len(required)} 个必需模板"

    def _check_jupyterlab_ready(self) -> bool:
        """检查 JupyterLab 是否已准备好"""
        return self._check_pip_package("jupyterlab")

    def _check_fastapi_ready(self) -> bool:
        """检查 FastAPI 是否已准备好"""
        try:
            import uvicorn
            import fastapi
            return True
        except ImportError:
            return False

    def _check_examples_status(self) -> str:
        """检查示例状态"""
        examples_dir = self.config.examples_dir
        notebooks = len(list(examples_dir.glob("*.ipynb")))
        py_files = len(list(examples_dir.glob("*.py")))
        return f"{notebooks} notebooks, {py_files} Python 脚本"

    def cmd_all(self, args):
        """启动完整开发环境或执行 dry-run 验证"""
        dry_run = getattr(args, "dry_run", False)
        verbose = getattr(args, "verbose", False)

        if dry_run:
            validator = DevValidator(self.config, verbose=verbose)
            success = validator.run_all_stages()
            sys.exit(0 if success else 1)
        else:
            print_header("启动完整开发环境")
            print_step("提示: 完整开发模式需要两个终端", "WARN")
            print()
            print("终端 1 - 前端开发服务器:")
            print("  pygwalker dev frontend")
            print()
            print("终端 2 - JupyterLab:")
            print("  pygwalker dev jupyter")
            print()
            print_step("或者先运行验证:", "INFO")
            print("  pygwalker dev all --dry-run")
            print()
            print_step("或者使用 --watch 模式进行无热重载开发:", "INFO")
            print("  pygwalker dev build --mode=app")
            print("  pygwalker dev jupyter --no-dev")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="pygwalker dev",
        description="PyGWalker 统一开发环境管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  pygwalker dev check                    # 检查环境
  pygwalker dev setup                    # 完整环境设置
  pygwalker dev build                    # 构建前端
  pygwalker dev frontend                 # 启动 Vite 开发服务器
  pygwalker dev jupyter                  # 启动 JupyterLab (开发模式)
  pygwalker dev web                      # 启动 FastAPI Web 服务器示例
  pygwalker dev examples                 # 列出可用示例
  pygwalker dev all --dry-run            # 完整开发环境验证 (不执行，仅检查)
  pygwalker dev bootstrap --dry-run      # 开发流程预检查 (按步骤：setup->build->template->examples)
        """,
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="可用命令")

    subparsers.add_parser("check", help="检查开发环境")

    setup_parser = subparsers.add_parser("setup", help="完整设置开发环境")
    setup_parser.add_argument(
        "--no-venv",
        action="store_true",
        help="不创建虚拟环境 (使用当前环境)",
    )

    build_parser = subparsers.add_parser("build", help="构建前端")
    build_parser.add_argument(
        "--mode",
        choices=["all", "app"],
        default="all",
        help="构建模式: all (完整) 或 app (仅主应用)",
    )

    frontend_parser = subparsers.add_parser("frontend", help="启动前端开发服务器")
    frontend_parser.add_argument("--host", action="store_true", help="绑定到 0.0.0.0")
    frontend_parser.add_argument("--port", type=int, help="指定端口")

    jupyter_parser = subparsers.add_parser("jupyter", help="启动 JupyterLab")
    jupyter_parser.add_argument("--port", type=int, default=8888, help="端口 (默认: 8888)")
    jupyter_parser.add_argument(
        "--no-dev",
        action="store_true",
        help="禁用开发模式 (使用已构建的 JS)",
    )

    web_parser = subparsers.add_parser("web", help="启动 Web 服务器 (FastAPI 示例)")
    web_parser.add_argument("--port", type=int, default=8000, help="端口 (默认: 8000)")

    subparsers.add_parser("examples", help="列出可用示例")

    all_parser = subparsers.add_parser(
        "all",
        help="完整开发环境验证和启动指南",
    )
    all_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅验证开发环境，不启动任何服务",
    )
    all_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出",
    )

    bootstrap_parser = subparsers.add_parser(
        "bootstrap",
        help="完整开发流程引导 (setup -> build -> template -> examples)",
    )
    bootstrap_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅验证开发流程，不执行实际操作",
    )
    bootstrap_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出",
    )

    args = parser.parse_args()

    cli = DevCLI()

    if args.subcommand is None:
        parser.print_help()
        return

    handlers = {
        "check": cli.cmd_check,
        "setup": cli.cmd_setup,
        "build": cli.cmd_build,
        "frontend": cli.cmd_frontend,
        "jupyter": cli.cmd_jupyter,
        "web": cli.cmd_web,
        "examples": cli.cmd_examples,
        "all": cli.cmd_all,
        "bootstrap": cli.cmd_bootstrap,
    }

    handler = handlers.get(args.subcommand)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
