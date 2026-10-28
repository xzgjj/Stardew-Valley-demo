# 决策记录（append-only）

| 日期 | 决策 | 理由 | 备注 |
|---|---|---|---|
| 2026-10-28 | 引擎锁 Godot 4.7.2，GDScript | 本机与 CI 均已实测 | `GODOT_VERSION.txt` |
| 2026-10-28 | 机制 1:1 贴原作，素材原创/CC0 | 版权安全 + 对齐目标 | 原作素材禁止入库 |
| 2026-10-28 | 主场景用完整标准农场 80×65 | 用户决策 | 不缩图 |
| 2026-10-28 | 像素作者工具用免费 LibreSprite（Aseprite 兼容） | Aseprite 付费未装 | PNG + `.aseprite` 兼容管线 |
| 2026-10-28 | `main` 推 v0.1 基线，阶段分支 v1/v2… | 锁定单版本、增量开发 | commit 标题 `<分支>_[audit_NN]<Name>` |
| 2026-10-28 | 每功能先测试后提交；commit 500–800 行；未批准不推送 | 质量门与人工 review | 见 `AGENT_EXECUTION_PROTOCOL.md` |
| 2026-10-28 | 文档原地更新，`implementation_plan.md` 只追加 | 保留原方案记录 | 推翻决策需写明原因 |
| 2026-10-28 | 版本对齐以 1.6 机制为主、1.7 只做观察 | 1.7 仅 3 项官方确认 | `docs/research_stardew_versions.md` |
