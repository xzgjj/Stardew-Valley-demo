# CI 规则说明

本文是 `CI.md` 的详细展开：逐条规则 ↔ 用户要求的对应表、阈值、审批边界、重试策略、豁免与已知限制。规则实现全部位于 `tools/ci/`，唯一配置来源是 `ci/policy.json`。

## 1. 规则 ↔ 要求对应表

| 用户要求 | 实现位置 | 检查名 | 判定 |
| --- | --- | --- | --- |
| 核心文档 ≤3000 字符 | `tools/ci/check_docs.py` | `docs` | 超限即失败；缺失核心文档失败 |
| 重复段落（归一化后完全一致） | `check_docs.py` | `docs` | 核心文档与研究文档内重复段落失败 |
| 研究类文档免字数上限、>20KB 告警、查重复段落 | `check_docs.py` | `docs` | 体积超 `research_doc_warn_bytes` 仅 WARN；重复段落失败 |
| GODOT_VERSION.txt ↔ project.godot ↔ CI.md 版本一致 | `check_docs.py` | `docs` | 任一不一致失败；CI.md 还需记录 gdtoolkit 固定版本 |
| 单 `.gd` ≤300 行 | `check_gdscript_size.py` | `gdscript_size` | 超限失败（扫描 `gdscript_roots`） |
| 单函数圈复杂度 ≤10 | `check_complexity.py` | `complexity` | 缩进解析函数体，超限失败 |
| ≥8 行重复代码块 | `check_duplicate_blocks.py` | `duplicate_blocks` | 跨文件或同文件重复出现即失败 |
| 未引用脚本（`res://` 扫描） | `check_unused_scripts.py` | `unused_scripts` | 无引用且无被使用的 `class_name` 即失败 |
| gdlint + gdformat --check | `check_lint.py` | `gdlint`、`gdformat` | 工具缺失/版本不符/检查失败均失败 |
| gdtoolkit 固定版本装 `.ci-venv` | `ci/policy.json`、`bootstrap_toolchain.py`、`check_lint.py` | `gdlint`、`gdformat` | 固定 `4.5.0`，版本不符失败 |
| 白名单 + ≤50 文件 / ≤2400 行增删 | `check_scope.py` | `scope` | 越界或超预算失败 |
| 阈值只紧不松（对比基线快照） | `check_policy_tightening.py` | `policy_tightening` | 放宽阈值/白名单/豁免/固定项失败 |
| policy/CI/测试保护文件改动需审批人 | `.github/workflows/ci.yml` 的 `policy-approval` job | CI job | PR 作者≠`policy_approver` 且当前 head 有其 APPROVED review |
| 受保护用例 id 不得删除 | `check_protected_tests.py` | `protected_tests` | 清单删除用例、测试文件丢失断言均失败 |
| 删除 `.gd` 测试文件告警/失败 | `check_protected_tests.py` | `protected_tests` | 基线中的测试文件消失失败；新增未登记仅 WARN |
| 素材清单覆盖 + 许可非空 | `check_assets.py` | `assets` | 未登记或许可列为空失败 |
| Godot 导入/回归/主场景 smoke | `check_godot.py` | `godot_import`、`godot_tests`、`godot_smoke` | 退出码非 0 或输出出现致命错误模式失败 |
| Godot 路径探测顺序 | `check_godot.py`、`ci/policy.json` | `godot_detect` | `$env:GODOT` → 固定 console 路径 → PATH；版本须等于锁定构建 |
| 本地 runner 最多 3 轮 | `run_local.py` | 全部 | `--rounds` 超过 `max_rounds`(3) 直接拒绝；用尽后打印证据并停止 |
| 一条命令跑完 + PASS/FAIL/耗时 + 总摘要 + 退出码 | `run_local.py` | 全部 | 逐项 PASS/FAIL/耗时，末尾 SUMMARY，0/1 退出码 |

## 2. 阈值（`ci/policy.json`）

| 键 | 值 | 含义 |
| --- | --- | --- |
| `max_core_doc_chars` | 3000 | 核心文档字符上限（Unicode 字符数） |
| `duplicate_paragraph_min_chars` | 20 | 参与重复段落判定的最小归一化长度（低于此长度不报告，避免空行/短标题噪声） |
| `research_doc_warn_bytes` | 20480 | 研究文档体积告警阈值（20KB，仅 WARN） |
| `max_changed_files` | 50 | 单次改动文件数预算 |
| `max_diff_lines` | 2400 | 单次增删行数预算 |
| `max_gdscript_lines` | 300 | 单文件行数上限 |
| `max_cyclomatic_complexity` | 10 | 单函数复杂度上限 |
| `duplicate_block_lines` | 8 | 重复代码块最小行数 |
| `max_rounds` | 3 | 本地 runner 重试轮数上限（硬上限） |
| `godot_timeouts` | import 300s / test 120s / smoke 120s | Godot 子进程超时 |
| `gdtoolkit_version` | 4.5.0 | gdtoolkit 固定版本 |

## 3. 圈复杂度与重复块口径

- 复杂度按函数体缩进解析，基准 1；`if`/`elif`/`for`/`while`/`match` 各 +1，`match` 分支 +1，布尔 `and`/`or` 各 +1（短路路径）。字符串与注释先剥离，避免误计。
- 重复块先归一化（去空白、去空行与整行注释、case 保留），再以 8 行为窗口滑窗；跨文件或同文件多处出现即报告。测试公共脚手架（`_check` + `quit(...)`）也会被判定，正确做法是抽取共享测试辅助脚本。
- GDScript 源文件必须为 UTF-8 **无 BOM**：gdtoolkit 4.5.0 的解析器遇到 BOM 会直接报错，`gdlint`/`gdformat` 门会明确指出带 BOM 的文件，必须重存（Godot 本身容忍 BOM，不代表 CI 可通过）。

## 4. 基线快照与“只紧不松”

- `ci/baseline_snapshot.json` 冻结三部分：`policy`（阈值/白名单/审批人/固定版本）、`protected_cases` + `test_files`（测试保护基线）、`files`（文件内容快照，用于无 git 仓库时的本地范围检查）。
- `policy_tightening` 只允许：上界阈值持平或降低、白名单前缀持平或更窄、豁免项减少、政策路径/核心文档/版本文档增加、审批人与 gdtoolkit 版本不变。
- `scope` 在本地对比快照；`--base SHA --head SHA` 时改用 git 三方 diff（GitHub Actions scope job 使用该模式，为权威口径）。
- 首次引入（快照不存在）按“基线引入，不阻断”处理。
- 刷新快照必须人工批准：`python tools/ci/baseline.py --trusted --force`。GitHub 环境中以 git 历史为准，不允许用刷新快照绕过预算。

## 5. 测试保护

- 清单 `tests/protected_test_cases.json` 的每个用例 id 必须仍出现在对应测试文件里；清单本身删除用例、基线快照中的用例或测试文件消失均失败。
- 新增测试文件未登记只产生 WARN，提示补登用例 id，不阻断并行开发。
- 修复行为回归只能改实现或补测试，不能删/改受保护断言。

## 6. 审批边界

- CI 自动判定：字数、重复、版本、行数、复杂度、重复块、未引用脚本、lint/format、范围预算、阈值收紧、测试保护、素材登记、Godot 导入/回归/smoke。
- 人判定：原创性与许可合法性、玩法价值、抽象/拆分是否合理、超预算是否可接受、受保护用例的语义迁移是否等价。
- 政策 PR 范围（`policy_paths`）：`.github/`、`ci/`、`tools/ci/`、`CI.md`、`GODOT_VERSION.txt`、`project.godot`、`tests/protected_test_cases.json`、`tests/test_*`。GitHub `policy-approval` job 要求 PR 作者 ≠ `policy_approver`，且当前 head 已有 `policy_approver` 的 APPROVED review（取该用户最新 review 状态，`commit_id` 必须等于 head sha）。
- 本地 runner 只能对政策文件改动给出 WARN，无法验证 GitHub 审批状态；最终以 CI job 为准。

## 7. 重试策略

- 本地 runner 默认最多 3 轮；每轮只重跑上一轮失败的检查，避免重复消耗静态检查与 Godot 启动时间。
- `--rounds N`：N 必须为 1..3；超出直接拒绝执行（防止用无限重跑掩盖不稳定失败）。
- 3 轮后仍失败：停止重试，输出每项错误摘要，并把失败项完整输出写入临时证据目录（终端打印路径）。
- CI workflow 使用 `--rounds 1`，失败后通过重新触发 workflow 复现；不自动重跑。

## 8. 豁免与理由

- `.import`、`.uid`：Godot 自动生成的导入/资源 ID 元数据，不是手工素材；由 Godot 维护，无法逐项登记作者/许可。
- `assets/README.md`：目录约定说明文档，不是素材；其内容纳入文档检查体系。
- `assets/licenses/`：许可文本证据本身，通过对应素材行的“许可/凭据位置”字段登记，无需再逐份登记。
- 第三方插件目录（如 `addons/`）不纳入 `gdscript_roots`：非本项目原创代码，不受本项目行数/复杂度/格式约束；但被场景引用时仍参与未引用脚本扫描的引用判定。

## 9. 工具链安装与 gdlint 配置

```powershell
python -m venv .ci-venv
.ci-venv\Scripts\python.exe -m pip install gdtoolkit==4.5.0
python tools/ci/bootstrap_toolchain.py   # 等价的一键安装
```

- 工具解析顺序：`.ci-venv/Scripts/gdlint.exe`（开发者本机）→ `PATH` 中的 `gdlint`（GitHub 运行器）；版本必须等于 `gdtoolkit_version`，否则失败。
- 默认使用 gdtoolkit 严格配置，不削弱任何规则。若遇到 Godot 4.7 新语法导致的**误报**，可在 `ci/gdlintrc` / `ci/.gdlintrc` 中做最小化配置；配置放在 `ci/` 下，刷新由审批人复核，且不得关闭 `max-file-lines`、`max-line-length`、命名/未使用参数等实质规则。
- `gdformat` 默认配置（tab 缩进、行宽 100）通过 `gdformat --check` 强制，不做项目级豁免。

## 10. Godot 门细节

- 探测顺序固定：`$env:GODOT` → `D:\app_finish\Godot\Godot_v4.7.2-stable_win64_console.exe` → `D:\app_finish\Godot\Godot_v4.7.2-stable_win64.exe` → `PATH`（`godot`/`godot4`）→ `$env:GODOT_BIN`（兼容旧脚本）。版本必须等于 `GODOT_VERSION.txt`。
- 导入：`godot --headless --editor --path . --quit`。
- 回归：枚举 `tests/test_*.gd`，要求 `extends SceneTree`，逐个 `--script res://tests/<name>.gd`；退出码非 0、出现 `FAIL:` 或致命输出即失败。
- smoke：`godot --headless --path . --quit-after 120`；另外按 `godot_smoke_scenes` 运行可选场景冒烟（如 `res://tests/scene_smoke.tscn`，文件存在才运行，失败即失败）。
- Godot 在脚本解析错误时仍返回 0，因此扫描 `SCRIPT ERROR`、`Parse Error`、`Failed to load script`、`Cannot open file` 等模式；`ERROR:` 中与退出资源泄漏相关的非致命行只记 WARN。

## 11. 已知限制

- 远端仓库/分支保护未连接，`policy-approval` 与 scope git 模式只能在 GitHub 上生效，本机无法端到端验证。
- 本机项目目录当前不是 git 仓库，本地范围检查使用快照模式（删除/修改按内容哈希与 difflib 行差分计算）；行数预算为精确值，前提是快照保存了文本内容（二进制文件只统计文件数）。
- gdtoolkit 解析器与 Godot 4.7 语法存在滞后风险；出现误报时按第 9 节处理，不以跳过检查的方式绕过。
- 研究文档重复段落检查按文档内判定；跨文档相同段落不属于本门范围。
