# 项目协作约定

- **开工前必读**：`AGENT_EXECUTION_PROTOCOL.md` + 本文件；任何修改前先输出中文确认区块
  （GOAL_CONFIRMATION / IMPACT_ANALYSIS / RISK_LEVEL），等待用户批准；低风险获批后可连续执行。
- 引擎锁定 `4.7.2.stable.official.ed1daf0bf`；GDScript；Python ≥3.12；gdtoolkit 4.5.0。不升级、不换栈。
- 分层：`scenes/`、`scripts/{autoload,data,systems,world,ui}`、`assets/`、`tests/`、`tools/ci/`、`docs/`。
  作用域白名单见 `ci/policy.json` 的 `allowed_prefixes` + `allowed_files`；越界需批准。
- 代码阈值：单 `.gd` ≤300 行；圈复杂度 ≤10；重复块 ≥8 行需复用；gdlint/gdformat 0 问题；命名与设计人审。
- 文档预算：`CLAUDE.md`、`SPEC.md`、`CLI.md`、`CI.md` ≤3000 字符；`implementation_plan.md` ≤12000、
  `AGENT_EXECUTION_PROTOCOL.md` ≤8000（用户批准的例外）；研究/设计文档免字数上限但 >20KB 告警、查重复段落。
- 文档维护：`implementation_plan.md` 只追加（`## 追加 YYYY-MM-DD vX`，保留原方案）；`implementation-notes.md`
  持续记录设计决策/偏差/权衡/未决问题；`docs/decisions.md` 记录关键决策。
- 测试位置：目标结构 `tests/unit`（纯逻辑）、`tests/integration`（GameState 流程）、`tests/scene`（场景/截图）、
  `tests/protected_test_cases.json`；当前平铺 `tests/test_*.gd` 先保持，迁移时同步 CI 扫描与保护清单。
- 功能节奏：先写/补测试 → 最小测试跑通 → 全量 `python tools/ci/run_local.py` → 3 轮评审 → 更新文档 → 本地 commit；
  每个 commit 500–800 行、逻辑完整；**未获批准不推送**。
- 分支与命名：`main` = v0.1 基线（tag `v0.1-baseline`）；阶段分支 `v1`、`v2`…；commit 标题
  `<分支>_[audit_NN]<EnglishName>`，如 `v1_[audit_03]InputParity`；不加共同作者、不生成 commit 文档。
- 只保留两个重要版本（v0.1 与 v1）；之后在 v1 连续修改，不再打新版本快照，除非用户要求。
- 范围：默认 ≤50 文件、≤2400 行/次；首次建库即基线；超出须批准。CI 政策/测试保护/引擎版本变更须 `@xzgjj` 批准。
- 测试保护：`tests/protected_test_cases.json` 的用例 id 不得删除或弱化；禁止删测试、放宽阈值、跳过 CI。
- 素材：只用原创或 CC0/OFL 等许可明确素材，逐项登记 `docs/asset_manifest.md`；禁止原作美术/音频/对白/角色名。
- Godot 不随意启动/重启：验证统一走 `run_local.py`；视觉取证使用 `tests/screenshot_capture.tscn`；
  用户要求打开编辑器时保持运行，不主动关闭。
- 完成标准：`run_local.py` 全 PASS、VS Code Problems 面板无报错、文档已更新、用户 review 通过。
