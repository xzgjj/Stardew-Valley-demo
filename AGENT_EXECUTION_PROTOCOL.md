# 代理执行协议

## 每阶段流程
1. **预估**：列出目标、允许路径、预计文件数与行数、测试点、风险；预估提交给用户。
2. **拆任务/commit**：按 500–800 行拆成可独立运行、逻辑完整的提交；每步先写测试用例。
3. **实现**：小步修改；每实现一个功能立即跑最小测试，未通过不进入下一步。
4. **评审**：代码评审 3 轮（自审 diff → 规范/测试 → 需求对齐），评审后修完再跑全量。
5. **文档**：更新 `implementation_plan.md`（追加）与相关文档；核心文档 ≤3000 字符。
6. **提交**：`git commit`（标题 `<分支>_[audit_NN]<EnglishName>`），**不推送**，等用户确认。
7. **推送**：用户明确同意后才 `git push`；最终阶段推送同样须同意。

## 分支与版本
- `main`：v0.1 基线（tag `v0.1-baseline`）。
- 阶段分支：`v1`、`v2`……按整数递增；上一阶段完成并推送后，从 `main` 建下一分支。
- commit 示例：`v1_[audit_03]FarmScene`；审计编号在阶段内递增。

## 质量门
- 提交前本地全流程：`python tools/ci/run_local.py`（Godot 导入 + 全部 `tests/test_*.gd` + `tests/scene_smoke.tscn` + 静态检查）。
- 禁止通过删测试、弱化断言、放宽阈值、跳过 CI 来过门；政策文件变更须用户批准。
- VS Code Problems 面板必须无报错；Godot 输出不得有 SCRIPT ERROR/Parse Error。
- 单文件 ≤300 行、圈复杂度 ≤10、gdlint/gdformat 0 问题；文档预算与重复段落检查通过。

## 对齐与素材
- 机制常量以 `scripts/data/parity.gd` 与 `docs/research_stardew_parity.md` 为唯一来源，改动需同步 parity 测试。
- 只使用 CC0/OFL 或自制素材，登记 `docs/asset_manifest.md`；禁止原作美术、音频、对白、角色名。

## 回滚与验证
- 每个新功能前建 git 基线；失败用 `git revert`/`git reset` 回到最近可运行 commit，禁止不可逆覆盖。
- 无 git 的项目先建库并配置本地检查点，再开始改动。

## 结束条件
- 阶段验收项全部通过 + 用户 review 通过 + 文档已更新；最终阶段需用户同意后才推送。
