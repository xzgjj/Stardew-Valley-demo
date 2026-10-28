# 项目协作约定

- 项目是 Godot `4.7.2.stable.official.ed1daf0bf` / GDScript 2D 农场生活 MVP；版本锁死，不升级不降级。
- 分层：`scenes/`（场景）、`scripts/`（autoload / data / systems / world / ui）、`assets/`（素材）、`tests/`、`tools/ci/`、`docs/`。主场景 `scenes/main.tscn`。
- 代码阈值：单 `.gd` ≤300 行；单函数圈复杂度 ≤10；重复代码块 ≥8 行需复用；命名与设计由人评审。
- 文档预算：`CLAUDE.md`、`SPEC.md`、`implementation_plan.md`、`AGENT_EXECUTION_PROTOCOL.md`、`CLI.md`、`CI.md` 各 ≤3000 字符；`docs/` 研究/设计文档免字数上限但 >20KB 告警，均检查重复段落。
- 文档更新机制：核心文档按章节原地更新；`implementation_plan.md` **只追加不删改**（新阶段写 `## 追加 YYYY-MM-DD vX`；推翻旧决策时保留原方案并写明原因）；`docs/decisions.md` 记录决策与理由。
- 实现阶段：每步先写/补对应测试用例 → 最小测试跑通 → 代码评审 3 轮 → 更新文档 → 用户 review → 提交。每个 commit 500–800 行、逻辑完整可运行；未获用户同意不推送。
- 分支与审计：`main` 为首版基线（tag `v0.1-baseline`）；阶段分支 `v1`、`v2`…；commit 标题 `<分支>_[audit_NN]<EnglishName>`，例如 `v1_[audit_03]FarmScene`；不生成 commit 文档，不添加共同作者。
- 测试保护：`tests/protected_test_cases.json` 的用例 id 不得删除或弱化；测试删除告警。
- 范围：每任务先给允许路径 + 预估文件数/行数；默认 ≤50 文件、≤2400 行/次，超出须人批准。首次建库视为基线。
- 素材：只用原创或许可明确的外部素材（优先 CC0/OFL），逐项登记作者、来源、许可与改动；禁止原作美术/音频/文本。
- CI 政策文件（`.github/`、`ci/`、`tools/ci/`、`CI.md`、`GODOT_VERSION.txt`、`project.godot`、测试保护清单）变更须由 `@xzgjj` 在最新 head 批准，且批准人不得是作者。
