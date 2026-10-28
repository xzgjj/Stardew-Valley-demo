# 素材目录与来源约定

## 目录

| 路径 | 内容 |
| --- | --- |
| `tilesets/` | 地形 / 作物 / 对象图集，全部 16x16 网格：`terrain.png`(128x16, 8 格)、`crops.png`(80x16, 5 阶段)、`objects.png`(128x16, 8 格) |
| `characters/` | 四方向行走图集（64x64 = 4 列 x 4 行，16x16/帧；行序 down/left/right/up） |
| `ui/` | `panel.png`(48x48 九宫格，边框 8px)、`icons.png`(160x16, 10 个图标) |
| `props/` | 场景摆件：`farmhouse.png`(112x64 = 7x4 格农舍外观) |
| `fonts/` | v1 计划放入 Ark Pixel 12px（OFL-1.1）；当前用系统字体兜底 |
| `source/kenney/` | Kenney CC0 原始图集（切片原料，勿手改） |
| `licenses/` | 许可原文：Kenney 三包 License.txt、CC0 法律文本、Ark Pixel OFL 文本 |

## 生成与校验（不要手改 PNG）

全部 PNG 由脚本幂等生成，手改会被 `--check` 判为 stale：

```bash
python -X utf8 tools/assets/prepare_assets.py          # 重新生成全部 PNG
python -X utf8 tools/assets/prepare_assets.py --check  # 校验尺寸 / 帧布局 / 透明度 / 生成一致性 / 字体 / 许可文本
```

- 生成规则、Kenney 切片索引（`KENNEY_SLICES`）与调色板都在 `tools/assets/prepare_assets.py`；
  换美术时改脚本或直接覆盖 PNG，然后同步 `docs/asset_manifest.md` 对应行。
- 逐项登记（作者 / 来源 URL / 许可 / 是否可商用 / 改动）见 `docs/asset_manifest.md`。

## Godot 导入设置（像素美术必须）

本项目 `project.godot` 已全局设置：

```ini
[rendering]
textures/canvas_textures/default_texture_filter=0   ; 0 = Nearest
textures/default_filters/use_nearest_mipmap_filter=false
```

新增/替换贴图后，确认每个 PNG 的导入面板：

- **Filter**：`Nearest`（关掉 Linear / Mipmaps，否则 16x16 像素会糊）
- **Mipmaps**：`Off`
- **Compress → Mode**：`Lossless`（像素图不要 VRAM 压缩，避免色带）
- **Process → Fix Alpha Border**：可开（避免描边处出现暗边）
- 图集类资源（terrain/crops/objects/icons）由代码按 16px 网格裁 `AtlasTexture`，**不要**在导入时裁剪留白。

## 路径契约

代码按固定路径加载（`scripts/world/art.gd`），改名/移动会退回程序化兜底贴图：
`res://assets/tilesets/terrain.png`、`crops.png`、`objects.png`，
`res://assets/characters/player.png`、`villager.png`，
`res://assets/ui/panel.png`、`icons.png`，`res://assets/props/farmhouse.png`，
`res://assets/fonts/pixel.ttf`。

## 来源与原创纪律

- 只用**原创**或**许可明确**（CC0 / OFL / 已购买授权）的外部素材，逐项登记；不依据"免费可下载"推定可商用。
- 不从《星露谷物语》安装文件、Wiki 截图、拆包文件或粉丝素材包提取美术、音频、字体、地图、UI、对白、角色形象。
- 不把 itch.io 等平台上"禁止再分发"许可的素材包提交进本仓库。
