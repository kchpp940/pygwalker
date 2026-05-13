# PyGWalker 测试体系指南

本目录包含 PyGWalker 项目的所有测试相关文件。测试按类型分层管理，以便于维护、运行和定位问题。

## 目录结构

```
tests/
├── unit/              # 单元测试 - 快速、独立、无外部依赖
├── integration/       # 集成测试 - 测试模块间交互
├── verification/      # 临时验证脚本 - 开发过程中的一次性验证
├── static_checks/     # 静态检查脚本 - 代码质量和架构检查
└── notebooks/         # Notebook 测试 - Jupyter notebook 用例
```

## 测试类型详解

### 1. 单元测试 (unit/)

**什么时候跑**：
- 每次代码提交前
- CI 构建的核心测试环节
- 本地开发时的快速反馈

**运行命令**：
```bash
# 使用分组脚本（推荐，排除可选依赖测试）
python scripts/run_pytest_groups.py --group core

# 直接运行所有单元测试（包含需要可选依赖的测试）
pytest tests/unit/ -v --tb=short
```

**依赖**：
- Python 3.7+
- pytest
- pandas, numpy, jinja2, sqlalchemy, duckdb 等核心依赖

**分组说明**：
- **core 组**（推荐）：`python scripts/run_pytest_groups.py --group core`
  - 包含：`test_field_quality.py`, `test_fname_encodings.py`, `test_scatter_plot_sampling.py`
  - **实际测试结果**（验证日期：2026-05-13）：**55 个测试全部通过** ✅
  - 排除：`test_dsl_transform.py`（需要 `mini-racer` 可选依赖）

- **optional-deps 组**（需要可选依赖）：`python scripts/run_pytest_groups.py --group optional-deps`
  - 包含：`test_dsl_transform.py`（需要 `mini-racer`）
  - 安装：`pip install mini-racer` 或 `pip install pygwalker[export]`

**失败时如何定位**：
1. 检查具体失败的测试方法名称
2. 查看 pytest 输出的 traceback
3. 单元测试是独立的，问题通常局限于被测试的方法或类

**常见失败原因及解决**：
- **ImportError: No module named 'py_mini_racer'**
  - 原因：`test_dsl_transform.py` 需要 JavaScript 运行时
  - 解决：使用 `--group core` 跳过，或安装 `pip install mini-racer`
  - 注意：这是可选依赖，不影响核心功能

- **ModuleNotFoundError: No module named 'pygwalker'**
  - 原因：pygwalker 包未安装
  - 解决：`pip install -e .` 或 `pip install -e ".[export]"`

- **AssertionError**
  - 原因：测试断言失败，功能逻辑有问题
  - 定位：根据测试方法名找到对应的源码位置
  - 示例：`test_field_quality.py` 失败 → 检查 `pygwalker/utils/field_quality.py`

**文件列表**：
- `test_dsl_transform.py` - DSL 转换逻辑测试（需要 `mini-racer`，属于 optional-deps 组）
- `test_field_quality.py` - 字段质量分析核心逻辑测试
- `test_fname_encodings.py` - 文件名编码测试
- `test_scatter_plot_sampling.py` - 散点图采样逻辑测试

---

### 2. 集成测试 (integration/)

**什么时候跑**：
- 核心功能修改后
- PR 合并前的完整测试
- CI 的 integration 测试环节（仅 Linux）

**运行命令**：
```bash
# 使用分组脚本（推荐，排除可选依赖测试）
python scripts/run_pytest_groups.py --group integration

# 直接运行所有集成测试（包含需要可选依赖的测试）
pytest tests/integration/ -v --tb=short

# 运行所有测试（单元 + 集成）
python scripts/run_pytest_groups.py --group all
```

**依赖**：
- 所有单元测试依赖
- pandas, polars, duckdb 等数据处理库
- 可能需要网络连接（部分测试）
- 更长的执行时间

**分组说明**：
- **integration 组**（推荐）：`python scripts/run_pytest_groups.py --group integration`
  - 包含：`test_data_pipeline.py`, `test_field_quality_integration.py`, `test_spec_pipeline.py`, `test_spec_persistence.py`, `test_recommendation_explainer.py`, `test_format_invoke_walk_code.py`
  - **实际测试结果**（验证日期：2026-05-13）：**67 个测试全部通过** ✅
  - 排除：`test_data_parsers.py::test_connector`（需要 `duckdb-engine` 可选依赖）

- **optional-deps 组**（需要可选依赖）：`python scripts/run_pytest_groups.py --group optional-deps`
  - 包含：`test_data_parsers.py`（需要 `duckdb-engine`）
  - 安装：`pip install duckdb-engine`

**失败时如何定位**：
1. 识别测试涉及的模块边界
2. 检查模块间的接口和数据传递
3. 使用 `--tb=long` 查看完整调用栈
4. 考虑是否需要单独运行某个测试文件来缩小范围
5. 示例：`test_field_quality_integration.py` 失败 → 检查 DataParser → SQL 查询 → 字段质量的完整数据流

**常见失败原因及解决**：
- **sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:duckdb**
  - 原因：`test_data_parsers.py::test_connector` 需要 duckdb SQLAlchemy 方言
  - 解决：使用 `--group integration` 跳过，或安装 `pip install duckdb-engine`

- **FileNotFoundError 或 ImportError**
  - 原因：测试文件中的相对路径问题或缺少模块
  - 检查：确认测试文件中的 `__file__` 或 `os.path.dirname` 使用正确
  - 注意：测试从 `tests/` 移动到 `tests/integration/` 后，路径深度增加了一层

**文件列表**：
- `test_data_pipeline.py` - 数据管道集成测试
- `test_data_parsers.py` - 数据解析器集成测试（`test_connector` 需要 `duckdb-engine`，属于 optional-deps 组）
- `test_field_quality_integration.py` - 字段质量端到端测试
- `test_spec_pipeline.py` - Spec 管道集成测试
- `test_spec_persistence.py` - Spec 持久化测试
- `test_recommendation_explainer.py` - 推荐解释器测试
- `test_format_invoke_walk_code.py` - 代码格式化测试

---

### 3. 临时验证脚本 (verification/)

**什么时候跑**：
- 开发特定功能时的临时验证
- 重构前后的行为一致性检查
- 非回归验证

**运行命令**：
```bash
# Python 验证脚本
python tests/verification/verify_return_structure.py
python tests/verification/verify_recommendation_explanation.py

# 前端验证脚本（在 app/ 目录下）
cd app && yarn verify:data-pipeline
cd app && yarn verify:export-config
cd app && yarn verify:all
```

**依赖**：
- 根据具体脚本而定
- Python 脚本需要 pygwalker 包
- 前端脚本需要 Node.js 和 yarn

**失败时如何定位**：
1. 验证脚本通常有详细的输出说明
2. 查看脚本中的具体断言位置
3. 验证脚本通常用于检查代码结构或特定模式，而非功能正确性
4. 示例：`verify-data-pipeline-unification.js` 失败 → 检查前后端数据管道 API 的一致性

**文件列表**：
- `verify_filter_consistency.py` - 过滤逻辑一致性验证
- `verify_frontend_field_quality.py` - 前端字段质量验证
- `verify_recommendation_explanation.py` - 推荐解释验证
- `verify_return_structure.py` - 返回结构验证
- `run_full_verification.py` - 完整验证流程
- `run_recommendation_demo.py` - 推荐功能演示

**前端验证脚本（app/tests/verification/）**：
- `verify-data-pipeline-unification.js` - 数据管道统一验证
- `verify-end-to-end.js` - 端到端验证
- `verify-export-config.js` - 导出配置验证
- `verify-export-refactor.js` - 导出重构验证
- `verify-recommendation-explanation.js` - 推荐解释验证

---

### 4. 静态检查 (static_checks/)

**什么时候跑**：
- 代码提交前的质量检查
- CI 的 linting 环节
- 架构合规性检查

**运行命令**：
```bash
# 使用分组脚本运行所有静态检查
python scripts/run_pytest_groups.py --group static-checks

# TypeScript 类型检查（前端）
cd app && yarn typecheck

# Python linting（使用项目配置）
pylint pygwalker/ --rcfile=.pylintrc

# 查看项目的 pylint 配置
cat .pylintrc
```

**依赖**：
- 前端：Node.js, yarn, TypeScript
- Python：pylint（项目已配置 `.pylintrc`）
  - 安装：`pip install pylint`

**实际测试结果**（验证日期：2026-05-13）：
- **TypeScript 类型检查**：✅ 通过
- **Python Lint**：⚠️ pylint 未安装（配置了 `continue_on_error`，不影响整体退出码）

**失败时如何定位**：
1. 查看具体的 lint 错误信息
2. TypeScript 类型错误：检查函数签名、变量类型注解
3. Pylint 错误：根据错误代码（如 C0114, W0612）参考 Python 编码规范
4. CI 中的类型检查失败通常是代码逻辑问题，需要修复

**项目已配置的静态检查**：
- `.pylintrc` - Python 代码风格检查配置
- `app/tsconfig.json` - TypeScript 类型检查配置

---

### 5. Notebook 测试 (notebooks/)

**什么时候跑**：
- API 变更后
- 文档示例验证
- 特定环境下的功能验证

**运行命令**：
```bash
cd tests/notebooks
jupyter nbconvert --execute --to html *.ipynb
```

**依赖**：
- Jupyter, nbconvert
- ipykernel
- 完整的 pygwalker 依赖

**失败时如何定位**：
1. 查看生成的 HTML 文件中的错误
2. 检查 notebook 中失败的 cell
3. 考虑是否是环境问题而非代码问题

**文件列表**：
- `main.ipynb` - 主要功能演示
- `main-modin.ipynb` - Modin DataFrame 测试
- `main-polars.ipynb` - Polars DataFrame 测试
- `field-spec.ipynb` - 字段规格测试
- `test_component_api.ipynb` - 组件 API 测试

## 快速参考

| 测试类型 | 执行频率 | 运行时间 | 失败影响 | 关键命令 |
|---------|---------|---------|---------|---------|
| 单元测试 (core) | 每次提交 | 快速 (< 2分钟) | 高 - 必须修复 | `python scripts/run_pytest_groups.py --group core` |
| 集成测试 (integration) | PR 合并前 | 中等 (< 10分钟) | 高 - 必须修复 | `python scripts/run_pytest_groups.py --group integration` |
| 可选依赖测试 (optional-deps) | 需要时 | 中等 | 中 - 可选 | `python scripts/run_pytest_groups.py --group optional-deps` |
| 静态检查 (static-checks) | 每次提交 | 快 | 中 - 建议修复 | `python scripts/run_pytest_groups.py --group static-checks` |
| 数据管道 (data-pipeline) | 数据管道修改时 | 中等 | 高 | `python scripts/run_pytest_groups.py --group data-pipeline` |
| 字段质量 (field-quality) | 字段质量修改时 | 快 | 中 | `python scripts/run_pytest_groups.py --group field-quality` |
| 工具函数 (utility) | 工具函数修改时 | 快 | 中 | `python scripts/run_pytest_groups.py --group utility` |
| 全部测试 (all) | 版本发布前 | 慢 | 高 | `python scripts/run_pytest_groups.py --group all` |
| 前端验证脚本 | 开发期间 | 快 | 中 - 视情况而定 | `cd app && yarn verify:all` |
| Notebook 测试 | 版本发布前 | 慢 | 低 - 可能不稳定 | `cd tests/notebooks && jupyter nbconvert --execute --to html *.ipynb` |

### 可选依赖说明

| 依赖 | 用途 | 安装命令 |
|-----|------|---------|
| `mini-racer` | `test_dsl_transform.py` 中的 4 个测试 | `pip install mini-racer` 或 `pip install pygwalker[export]` |
| `duckdb-engine` | `test_data_parsers.py::test_connector` | `pip install duckdb-engine` |
| `pylint` | Python 代码风格检查 | `pip install pylint` |

**注意**：
- `--group core` 和 `--group integration` 是默认推荐的稳定分组，不包含可选依赖测试
- `--group optional-deps` 包含所有需要可选依赖的测试
- `--group all` 包含所有测试（包括可选依赖）

## CI/CD 集成

项目的 GitHub Actions 工作流（`.github/workflows/auto-ci.yml`）自动执行：

1. **前端检查**：
   - TypeScript 类型检查
   - 前端构建
   - 验证脚本执行

2. **Python 测试**（跨平台）：
   - Core 测试（单元测试）- 所有平台
   - Integration 测试 - 仅 Linux

3. **Notebook 测试**：
   - 仅 Linux，Core 组

## 本地开发建议

1. **快速反馈循环**：
   ```bash
   # 只运行单元测试
   python scripts/run_pytest_groups.py --group core
   ```

2. **完整验证**：
   ```bash
   # 使用 local-ci.sh 脚本
   bash scripts/local-ci.sh --quick
   ```

3. **特定功能测试**：
   ```bash
   # 运行数据管道相关测试
   python scripts/run_pytest_groups.py --group data-pipeline
   
   # 运行字段质量相关测试
   python scripts/run_pytest_groups.py --group field-quality
   ```

4. **查看所有可用测试组**：
   ```bash
   python scripts/run_pytest_groups.py --list-groups
   ```

## 命名规范

- **测试文件**：`test_<module>_<scenario>.py`
  - 单元测试：`test_<feature>.py`
  - 集成测试：`test_<feature>_integration.py`
  
- **测试类/方法**：
  - 类名：`Test<Feature><Scenario>`
  - 方法名：`test_<action>_<expected_behavior>`

- **验证脚本**：`verify_<purpose>.py` 或 `verify-<purpose>.js`

## 添加新测试

1. **单元测试**：放在 `tests/unit/`，确保独立无外部依赖
2. **集成测试**：放在 `tests/integration/`，测试模块交互
3. **临时验证**：放在 `tests/verification/` 或 `app/tests/verification/`
4. **更新文档**：如果是新的测试类型或重要测试，更新此 README

## 故障排除

### 测试导入失败
- 确保已安装开发依赖：`pip install -e ".[export]"`
- 检查 Python 路径

### 数据相关测试失败
- 确保测试数据已下载：`python scripts/test-init.py`
- 检查 pandas/polars 版本兼容性

### 前端验证失败
- 确保前端已构建：`cd app && yarn build`
- 检查 Node.js 版本（需要 22.x）

### CI 测试通过但本地失败
- 检查 CI 使用的 Python/Node 版本
- 考虑使用虚拟环境重现 CI 环境
