# 参考工具链与可复用资产（Godot 4.x 农场 MVP）

日期：2026-10-28。面向 `Stardew-Valley-demo`（Godot 4.7.2 / GDScript）。原则：**能复用引擎能力就不写轮子；能复用的第三方只选许可清楚、可维护的**。所有 URL 在 2026-10-28 实际请求过（HTTP 200），标 **已核实**；仅凭记忆或访问失败的标 **待核实**。

## 0. 结论速览

| 问题 | 结论 |
|---|---|
| 有没有可直接抄的 Godot 星露谷-like 成品？ | 没有成熟项目。GitHub 搜索结果全是 0–2 星的学习仓库或无许可教程配套，**参考价值有限，不要指望整套复用** |
| 最值得复用的第三方是什么？ | **Dialogue Manager（MIT）**、**Aseprite Wizard（MIT）**、**官方 godot-demo-projects（MIT）** |
| 引擎侧要自己搭什么？ | 地块状态机、作物数据 `Resource`、JSON 存档与迁移、时间/能量结算——都在 100–300 行内，无需外部库 |
| 素材怎么解决？ | Kenney **CC0** 包先做占位；OpenGameArt 用 CC0 过滤器；**任何原作素材/反编译代码一律禁止** |

## 1. 开源参考项目（名称 + URL + 许可 + 可借鉴点）

许可与 Star 数由 `gh repo view` 于 2026-10-28 读取，均 **已核实**。

| 项目 | 许可 | Star | 可借鉴 | 风险 |
|---|---|---|---|---|
| [nova-denton-parry/farmsim-godot](https://github.com/nova-denton-parry/farmsim-godot) | GPL-3.0 | 1 | Godot 4 农场系统拆分：作物、采集、JSON 存档、昼夜；WIP 结构可看 | 代码 GPL-3.0 **有传染性**，只能读思路不能拷进闭源工程；素材未入库 |
| [ifeasome/CropTails](https://github.com/ifeasome/CropTails) | 无 LICENSE | 1 | YouTube 教程完整工程：TileMap、工具、箱子、库存的组织方式 | **无许可=默认保留全部权利**，不可复制代码/素材 |
| [rapidvectors/tutorial-components-and-scripts](https://github.com/rapidvectors/tutorial-components-and-scripts) | 无许可 | 213 | 25 集教程配套脚本：玩家工具、昼夜、库存、交互箱、主菜单、音效 | 无许可，仅可阅读；基于 Godot 4.3，API 需按 4.7 校对 |
| [clear-code-projects/PyDew-Valley](https://github.com/clear-code-projects/PyDew-Valley) | 无许可 | 585 | 用 pygame 复刻星露谷式系统的分层（时间、作物、NPC、存档） | 非 Godot；无许可，只当架构读物 |
| [Leoocast/lofi-valley-engine](https://github.com/Leoocast/lofi-valley-engine) | MIT | 22 | 数据驱动作物/工具/经济边界的建模方式（React+TS） | 前端状态管理不能照搬到 Godot 节点树 |
| [hpeinar/stardewplanner](https://github.com/hpeinar/stardewplanner) | Apache-2.0 | 268 | 农场布局规划器：地图格坐标、可放置性判断的参考 | 地图数据源自原作，**只能参考结构，不要复制数据** |
| [godotengine/godot-demo-projects](https://github.com/godotengine/godot-demo-projects) | MIT | 9719 | 官方 2D 示例（移动角色、TileMap、音频、UI），可直接对照写法 | 不含农场玩法，仅作 Godot 惯用法基准 |
| [WeDias/StardewValley](https://github.com/WeDias/StardewValley) | 无许可（反编译） | 357 | ❌ **仅用于理解机制**，不可读入工程、不可移植 | 反编译衍生代码，法律与社区红线 |

> 说明：GitHub `search/repositories` 对 farm/Stardew 类 Godot 项目返回的几乎都是 0–2 星仓库；用 `topic:farming-game`、`stardew valley godot`、`farm sim godot` 多次检索后结论一致。**不要花时间找"现成完整实现"**。

## 2. 可复用 Godot 4.x 能力清单

官方文档 URL 均已核实可访问（`en/stable` 对应 4.x）。

| 需求 | 引擎能力 | 文档 | 落地要点 |
|---|---|---|---|
| 地表/土壤/作物分层 | `TileMapLayer`（4.3+ 取代 TileMap 单节点） | [Using TileMaps](https://docs.godotengine.org/en/stable/tutorials/2d/using_tilemaps.html) · [TileMapLayer 类](https://docs.godotengine.org/en/stable/classes/class_tilemaplayer.html) | 每层一个节点：Ground/Soil/Crops；地块状态不存图块，存逻辑字典 |
| 树/屋檐遮挡人物 | Y-sort（`CanvasItem.y_sort_enabled`） | [CanvasItem](https://docs.godotengine.org/en/stable/classes/class_canvasitem.html) | 按脚底 Y 排序；同层内树、人、屋檐都开 y_sort；不要用固定 z_index 硬排 |
| 玩家移动与碰撞 | `CharacterBody2D` + `move_and_slide()` | [2D movement](https://docs.godotengine.org/en/stable/tutorials/2d/2d_movement.html) · [CharacterBody2D](https://docs.godotengine.org/en/stable/classes/class_characterbody2d.html) | 碰撞体用脚下小矩形（约 10×12 px）而非整贴图；朝向用 `facing` 枚举 |
| 角色/作物帧动画 | `AnimatedSprite2D` + `SpriteFrames` | [2D sprite animation](https://docs.godotengine.org/en/stable/tutorials/2d/2d_sprite_animation.html) | 作物每个生长阶段一帧；动画名用 `stage_0..4`，状态驱动不用计时器 |
| 作物/物品数据 | 自定义 `Resource`（`class_name CropDefinition`） | [Resources](https://docs.godotengine.org/en/stable/tutorials/scripting/resources.html) | 字段：id/名称/成熟天数/阶段数/种子价/售价/季节/可重复收获 |
| 存档/读档 | `FileAccess` + `JSON` / `ConfigFile` | [Saving games](https://docs.godotengine.org/en/stable/tutorials/io/saving_games.html) | `user://` + 版本号 + 原子写（先 `.tmp` 再 rename） |
| 分辨率/像素缩放 | Stretch 模式、整数缩放、像素吸附 | [Multiple resolutions](https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html) | `canvas_items` + `keep` + 整数缩放；视口 640×360 |
| 纹理导入过滤 | 导入选项 Filter/Mipmaps | [Importing images](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_images.html) | 像素图：**Filter 关、Mipmaps 关**；全局默认纹理过滤设 Nearest |
| 对话框 | Dialogue Manager（第三方，MIT） | [nathanhoad/godot_dialogue_manager](https://github.com/nathanhoad/godot_dialogue_manager) | 见 §3 |
| Aseprite 导入 | Aseprite Wizard（第三方，MIT） | [viniciusgerevini/godot-aseprite-wizard](https://github.com/viniciusgerevini/godot-aseprite-wizard) | 见 §4 |
| 找插件 | Godot Asset Library | [asset-library/asset](https://godotengine.org/asset-library/asset) | 装前看许可与最近更新年份 |
| 引擎版本 | Godot 4.7 发布说明 | [releases/4.7](https://godotengine.org/releases/4.7/) | 工程锁 `4.7.2.stable.official.ed1daf0bf`，不跟随 latest |

状态机不需要库：`enum State { IDLE, TILL, WATER, ... }` + `match` 在 `_physics_process` 分流；超过 5 个状态再考虑节点式 FSM（自建 <100 行）。

## 3. Dialogue Manager 落地要点（MIT，已核实）

- 装法：Asset Library 搜 "Dialogue Manager" 或下载 release zip 放 `addons/dialogue_manager/`，启用插件；会注册 `DialogueManager` autoload。
- 写对话：`.dialogue` 文本文件，`~ start` 起标签，`=>` 写选项回复；支持条件/赋值（语法以仓库 README 为准）。
- 跑对话：`DialogueManager.show_example_dialogue_balloon(load("res://dialogue/x.dialogue"), "start")`；结束监听 `dialogue_ended` 信号再恢复玩家输入。
- MVP 用法：原创村民（禾宁）用 1 个 `.dialogue` + 按日期/好感分支；**不要**把对白写进 `.tscn` 或脚本字符串。

## 4. Aseprite 管线（已核实）

- 工具：[Aseprite](https://www.aseprite.org/)（付费，可自编译免费版），源文件 `.aseprite` 入库 `assets/art/`。
- 导入：Aseprite Wizard 支持 `.aseprite/.ase`→`SpriteFrames`/`AnimationPlayer`/`AnimationTree`，按 tag 生成动画；也可导出 PNG 序列 + 手工切帧。
- 规范（16×16 格、视口 640×360、项目冻结 4.7.2）：
  1. 画布尺寸取 16 的整数倍；角色 16×32，作物单阶段 16×16。
  2. 调色板限制 16–32 色，统一光源方向；导出 PNG 不缩放。
  3. sprite sheet 用 tag 命名（`idle/walk/till`），帧标签进 Godot 后保持同名。
  4. 禁止把原作 sprite 描边/改色当原创素材（见 §6）。

## 5. 存档方案对比（Godot 4.x）

| 方式 | 优点 | 缺点 | 适用 |
|---|---|---|---|
| JSON（`JSON.stringify` / `parse_string`） | 人可读、易调试、便于 CI 断言 | 数字只有 float，读回要显式转 int；无类型保障 | **本工程推荐**（含 `version` 字段） |
| ConfigFile | 键值读写省事、支持 section | 结构表达力弱，嵌套字典仍要转换 | 小型设置 |
| 二进制（`var_to_bytes`/`store_var`） | 快、类型保真 | 不可读、难迁移 | 存档量大后再评估 |
| 资源文件（`.tres`/`.res`） | 与自定义 `Resource` 无缝 | 不适合玩家存档（易被误当内容资源） | 静态数据（CropDefinition） |

存档纪律：写入前 `version`；读取失败不覆盖原档；每次新字段同步 `to_data/load_data` + 迁移用例；存档文件与 protected tests 绑定。

## 6. 素材来源与许可（CC0 优先）

| 来源 | 许可 | 状态 | 用途 |
|---|---|---|---|
| [Kenney Assets](https://kenney.nl/assets) | CC0（各包页面另行标注） | 已核实（站点与包页 200） | 首选占位/可发布素材 |
| [Kenney Tiny Dungeon](https://kenney.nl/assets/tiny-dungeon) | CC0 | 已核实（页面 200；许可以包内 License.txt 为准） | 角色/道具/地块占位 |
| [Kenney Roguelike/RPG pack](https://kenney.nl/assets/roguelike-rpg-pack) | CC0 | 已核实（页面 200；许可以包内 License.txt 为准） | 房屋/树木/地块 |
| [Kenney Tiny Town](https://kenney.nl/assets/tiny-town) | CC0 | 已核实（页面 200；许可以包内 License.txt 为准） | 小镇、路径 |
| [OpenGameArt](https://opengameart.org/) | 逐件不同（可选 CC0 过滤） | 已核实站点；CC0 过滤链接 200 | 补充素材，逐件登记 |
| [CC0 1.0 法律文本](https://creativecommons.org/publicdomain/zero/1.0/) | CC0 | 已核实 | 许可依据 |
| itch.io 免费素材 | 逐包不同 | **待核实**（本机访问超时，未核） | 需人工读许可后再用 |
| LPC（Liberated Pixel Cup）角色包 | 常见 CC-BY-SA / GPL 双许可 | **待核实**（未取到单一权威页） | 需署名+同许可，谨慎 |

## 7. 许可雷区（红线）

1. **原作素材**：wiki 文件页明确标 "© ConcernedApe 2016 … freely usable **on this wiki**"（`File:Standard_Farm.png` 页脚，已核实）——贴图、UI、音乐、地图全不能用。
2. **反编译/拆包**：`WeDias/StardewValley` 等反编译仓库、XNB 解包产物，不可读入、不可移植。
3. **wiki 图片**：正文 CC BY-NC-SA 3.0，但图片单独受限；**不要**把 wiki 图当素材库。
4. **无 LICENSE 仓库**（CropTails、rapidvectors 脚本）：默认保留全部权利，只能读不能抄。
5. **GPL 传染**：直接把 GPL-3.0 项目代码搬进工程会迫使整体 GPL，闭源发行前禁止。
6. **"免费"≠可商用**：itch.io/个人博客的免费包常带"禁止再分发/禁商用/需署名"条款，逐包读 License 文件。
7. **AI/第三方生成素材**：同样要登记来源、许可和生成工具，不能默认可用。
8. 每个引入素材在 `assets/README.md` 记：作者、来源 URL、许可、下载日期、改动说明（对应 `CLAUDE.md` 的登记要求）。

## 8. 调研方法与工具

| 工具/方法 | 用法 | 注意 |
|---|---|---|
| 官方 wiki（英文） | 数值/规则首选；`File:` 页读像素尺寸与许可 | 正文 CC BY-NC-SA；只引数值 |
| `gh search repos` / `gh repo view --json licenseInfo,stargazerCount` | 找项目并核许可/活跃度 | 比网页搜索可靠；2026-10-28 实测可用 |
| Godot 官方文档（`en/stable`） | TileMapLayer/CharacterBody2D/存档/分辨率 | 版本以项目锁定 4.7.2 为准 |
| DeepWiki | 快速读懂第三方仓库结构：`https://deepwiki.com/<owner>/<repo>` | 直连返回 **429**（已核实），必须走 MCP 端点 `https://mcp.deepwiki.com/mcp`；`ask_wiki_question` 会答错，只作探索，结论回源码核 |
| `web_search` + `web_fetch` | 找二手解释、补中文资料 | 二手信息一律回 wiki/源码复核 |
| Aseprite + Godot 导入 | 像素流水线 | 导出前确认尺寸与调色板 |

## 9. 落地优先级建议

| 顺序 | 动作 | 成本 | 收益 |
|---|---|---|---|
| 1 | 冻结项目设置（640×360、nearest、像素吸附、整数缩放） | 0.5 h | 避免后期返工 |
| 2 | 作物/物品/工具写成 `Resource` 数据文件 | 2 h | 加作物不改代码 |
| 3 | JSON 存档 + `version` + 原子写 + 迁移测试 | 2 h | 行为可回归 |
| 4 | 引入 Dialogue Manager 做 1 个 NPC | 1 h | 后续对话零改代码 |
| 5 | Aseprite Wizard + Kenney CC0 素材替换占位 SVG | 1–2 h | 视觉接近目标 |
| 6 | 找现成 Godot 农场项目复用 | **不建议** | 无成熟项目，收益低于自建 |
