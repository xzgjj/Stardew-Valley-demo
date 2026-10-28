# CI 规则与执行

## 固定版本
- Godot `4.7.2.stable.official.ed1daf0bf`：`GODOT_VERSION.txt`、`project.godot` 特性 `4.7` 与本文件三方一致。
- Python ≥ 3.12（本地实测 3.13）。
- gdtoolkit 固定 `4.5.0`，安装在项目 `.ci-venv`；GitHub 运行器安装同一版本并校验。
- 阈值与白名单唯一来源：`ci/policy.json`；详细规则见 `docs/ci_rules.md`。

## 必过门
1. **文档**：CLAUDE.md、SPEC.md、implementation_plan.md、AGENT_EXECUTION_PROTOCOL.md、CLI.md、CI.md 各 ≤3000 字符；归一化后重复段落报错。研究文档（`docs/research_*.md`、`docs/reference_*.md`）不限字数，但 >20KB 告警且查重复段落。
2. **代码**：单 `.gd` ≤300 行；单函数圈复杂度 ≤10；≥8 行重复代码块报错；`res://` 未引用脚本报错；`gdlint` 与 `gdformat --check` 必须通过。
3. **范围**：仅 `ci/policy.json` 白名单路径，单次 ≤50 文件、≤2400 行增删；阈值/白名单/豁免/受保护项只允许收紧（对比 `ci/baseline_snapshot.json` 冻结基线）。
4. **测试保护**：`tests/protected_test_cases.json` 的用例 id 不得删除或从测试文件消失；删除 `tests/*.gd` 测试文件失败。
5. **素材**：`docs/asset_manifest.md` 必须覆盖 `assets/` 下所有素材且许可字段非空（`.import`/`.uid`、`assets/README.md`、`assets/licenses/` 为文档化豁免）。
6. **Godot**：无界面导入、逐个运行 `tests/test_*.gd`（SceneTree 脚本）、主场景 smoke（`--quit-after 120`）。Godot 脚本错误时仍返回 0，因此同时扫描 `SCRIPT ERROR`/`Parse Error` 输出并判失败。

## 本地运行
一条命令：`python tools/ci/run_local.py`
- 每项打印 PASS/FAIL 与耗时，末尾输出总摘要，退出码 0/1。
- 失败检查最多重试 3 轮（`--rounds N`，N≤3），超限停止并打印证据目录，不无限重跑。
- 常用参数：`--only docs,assets`、`--skip scope,policy_tightening`、`--list`、`--bootstrap`（安装 `.ci-venv` 工具链）。
- Godot 探测顺序：`$env:GODOT` → `D:\app_finish\Godot\Godot_v4.7.2-stable_win64_console.exe` → PATH。

## 人工审批边界
CI 只判定可自动判定的事项；原创性、玩法价值、抽象合理性与超预算是否可接受由人判断。`.github/`、`ci/`、`tools/ci/`、`CI.md`、`GODOT_VERSION.txt`、`project.godot`、`tests/protected_test_cases.json`、`tests/test_*` 的改动构成政策 PR：PR 作者不得是 `ci/policy.json` 的 `policy_approver`，且当前 head 必须已有该审批人的 APPROVED review（由 GitHub Actions 的 policy-approval job 强制）。远端仓库尚未连接，分支保护与必需检查无法在本机实测。
