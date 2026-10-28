# 星露谷农场 MVP

Godot 4.7.2 + GDScript 的 2D 农场生活 MVP：标准农场（80×65）主场景 + 农舍内景，玩家与村民，
时间/能量/耕作/采集/背包/出货/商店/存档/HUD。机制按《星露谷物语》1:1 对齐，素材为原创/许可明确的外部资源。

锁定构建：`4.7.2.stable.official.ed1daf0bf`（见 `GODOT_VERSION.txt`）。



## 快速开始

```powershell
godot --path .
```
或运行 `python tools/ci/run_local.py` 跑完整本地检查（Godot 路径见 `CLI.md`）。



## 目录

- `scenes/`：`main.tscn` 农场、`farmhouse.tscn` 农舍
- `scripts/autoload`、`data`、`systems`、`world`、`ui`
- `assets/`：素材（契约见 `docs/design_gameplay.md`，清单见 `docs/asset_manifest.md`）
- `tests/`：回归与场景冒烟；`tools/ci/`：CI 检查
- `docs/`：机制调研、游戏逻辑设计、工具链、CI 规则



## 文档

`SPEC.md`（范围与验收）、`implementation_plan.md`（阶段计划，只追加）、
`AGENT_EXECUTION_PROTOCOL.md`（阶段流程）、`CLI.md`（命令）、`CI.md`（CI 规则）、
`docs/design_gameplay.md`（游戏逻辑设计）、`docs/research_stardew_parity.md`（对齐依据）。



## 状态

v0.1 基线：核心循环可运行，6 个测试套件与场景冒烟通过。后续按阶段分支 v1、v2… 增量开发。
