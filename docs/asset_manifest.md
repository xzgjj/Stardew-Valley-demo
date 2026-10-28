# 素材清单（assets/asset_manifest.md）

本清单按 CI 素材门要求登记 `assets/` 下**每一个**非豁免文件（豁免：`*.import`、`*.uid`、
`assets/README.md`、`assets/licenses/**`）。路径均为仓库相对路径。
全部素材均为 CC0 / OFL 或本项目原创，不含《星露谷物语》原作美术、音频、字体。

## 一、登记表

| 文件 | 作者 | 来源 URL | 许可 | 是否可商用 | 改动说明 |
| --- | --- | --- | --- | --- | --- |
| assets/tilesets/terrain.png | Kenney（CC0 部分）+ 本项目 | https://kenney.nl/assets/tiny-town ；https://kenney.nl/assets/tiny-dungeon | CC0-1.0（外部素材）+ 原创（自制格） | 是 | 128x16，8 格 16x16：0 草地、1 草地(草丛)、2 泥土路、3 干耕地、4 湿耕地、5 水面、6 石地、7 木地板；0/1 取自 Tiny Town tile 0/1，6 取自 Tiny Dungeon tile 37，其余由脚本按同一调色板自制（格子顺序为项目契约，非 Kenney 图集原序） |
| assets/tilesets/crops.png | 本项目原创 | 本地生成：tools/assets/prepare_assets.py | 原创（CC0-1.0 精神，可自由替换） | 是 | 80x16，防风草 5 阶段（幼苗/生长/长大/即将成熟/可收获成熟），16x16 字符掩码手绘生成，自制占位可替换 |
| assets/tilesets/objects.png | Kenney（CC0 部分）+ 本项目 | https://kenney.nl/assets/tiny-town ；https://kenney.nl/assets/tiny-farm | CC0-1.0（外部素材）+ 原创（自制格） | 是 | 128x16，8 格：0 树(Tiny Town tile 17)、1 石头(Tiny Farm tile 89)、2 杂草(Tiny Farm tile 80)、3 出货箱(自制)、4 邮箱(自制)、5 温室残骸(自制)、6 木箱(Tiny Farm tile 92)、7 备用(全透明空格) |
| assets/characters/player.png | 本项目原创 | 本地生成：tools/assets/prepare_assets.py | 原创（可自由替换） | 是 | 64x64，4 行 x 4 帧 16x16；行序 down/left/right/up，列=行走帧；透明背景；自制占位可替换 |
| assets/characters/villager.png | 本项目原创 | 本地生成：tools/assets/prepare_assets.py | 原创（可自由替换） | 是 | 64x64，与 player 同规格同行序；村长禾宁配色（深褐长发、米色上衣、绿裙），自制占位可替换 |
| assets/ui/panel.png | 本项目原创 | 本地生成：tools/assets/prepare_assets.py | 原创（可自由替换） | 是 | 48x48 九宫格面板，边框 8px，四角透明圆角，填充米色半透明 |
| assets/ui/icons.png | Kenney（CC0 部分）+ 本项目 | https://kenney.nl/assets/tiny-farm ；https://kenney.nl/assets/tiny-town | CC0-1.0（外部素材）+ 原创（自制格） | 是 | 160x16，10 个 16x16 图标固定顺序：0 锄头(Tiny Town 115)、1 浇水壶(Tiny Farm 84)、2 斧头(Tiny Town 127)、3 镐(Tiny Town 129)、4 镰刀(Tiny Farm 88)、5 种子(Tiny Farm 9)、6 防风草(Tiny Farm 31)、7 木材(自制圆木)、8 石头(Tiny Farm 89)、9 纤维(Tiny Farm 65) |
| assets/props/farmhouse.png | 本项目原创 | 本地生成：tools/assets/prepare_assets.py | 原创（可自由替换） | 是 | 112x64（7x4 格）农舍外观：坡屋顶+烟囱+门窗+石基座，透明背景，自制占位可替换 |
| assets/fonts/pixel.ttf | TakWolf（Fusion Pixel Font） | https://github.com/TakWolf/fusion-pixel-font/releases/tag/2026.10.25 | OFL-1.1 | 是 | Fusion Pixel 12px proportional 简体中文构建（`fusion-pixel-12px-proportional-zh_hans.ttf`，38,130 字形）原样重命名为 `pixel.ttf`，字形未改动；许可原文 assets/licenses/fusion-pixel-font-OFL.txt。注：先试过 Ark Pixel 12px，实测缺「溪/然/窗/药/垦」等字（项目名「晨溪农场」会显示方块），故换覆盖更全的 Fusion Pixel |
| assets/source/kenney/tiny-farm-tilemap.png | Kenney | https://kenney.nl/assets/tiny-farm | CC0-1.0 | 是 | 原始 16x16 图集（12x11，1px 间距已由官方 packed 版去掉），作为切片原料原样保存，未改动像素 |
| assets/source/kenney/tiny-town-tilemap.png | Kenney | https://kenney.nl/assets/tiny-town | CC0-1.0 | 是 | 原始 16x16 图集（12x11 packed），切片原料原样保存 |
| assets/source/kenney/tiny-dungeon-tilemap.png | Kenney | https://kenney.nl/assets/tiny-dungeon | CC0-1.0 | 是 | 原始 16x16 图集（12x11 packed），切片原料原样保存 |

## 二、许可结论

- **Kenney Tiny Farm / Tiny Town / Tiny Dungeon**：三个包均为 **CC0 1.0（公共领域贡献）**，
  作者 Kenney，官网明示 "free to use in personal, educational and commercial projects"，
  署名非强制（本项目仍在清单中署名）。CC0 允许再分发与改造，故原始图集与切片均可进公开仓库。
  许可原文：`assets/licenses/kenney-tiny-farm-License.txt`、`kenney-tiny-town-License.txt`、
  `kenney-tiny-dungeon-License.txt`；法律文本 `assets/licenses/CC0-1.0-legalcode.txt`。
- **Fusion Pixel Font**：**SIL Open Font License 1.1**，允许嵌入、再分发与商业使用，
  要求保留版权与许可声明、不得单独售卖字体、衍生字体不得使用保留字体名。本项目只原样分发，
  许可原文 `assets/licenses/fusion-pixel-font-OFL.txt`。
  选型记录：Ark Pixel 12px（同为 TakWolf/OFL）实测缺「溪/然/窗/药/垦」等常用字，会让中文 UI
  出现方块，故改用同作者覆盖 38,130 字形的 Fusion Pixel 12px；两者都是纯像素字体。
- **本项目自制部分**（terrain 4 个自制格、crops、player、villager、panel、icons 第 7 格、farmhouse、
  objects 3/4/5 格）：原创像素，按"自制占位，可替换"标注；后续如有正式美术，直接覆盖同名 PNG
  并更新本表一行即可（尺寸契约不变）。
- **明确未使用**：星露谷原作或任何同人素材包的美术/音频/字体；itch.io 上"禁止再分发"许可的包
  （本轮一个都没打包进仓库）。

## 三、复现与校验

```bash
python -X utf8 tools/assets/prepare_assets.py          # 重新生成全部 PNG（幂等）
python -X utf8 tools/assets/prepare_assets.py --check  # CI 校验：尺寸/帧布局/透明通道/生成一致性/字体/来源
```

`--check` 的"生成一致性"会用同一套生成函数在内存里重建每个 PNG 并与磁盘逐像素比对：
文件被手改、或生成器改了却没重跑，都会报 stale 并失败。

## 四、契约速查（代码按此加载，勿随意改）

| 文件 | 尺寸 | 版式 |
| --- | --- | --- |
| terrain.png | 128x16 | 8 个 16x16，单行：草地/草地草丛/泥土路/干耕地/湿耕地/水面/石地/木地板 |
| crops.png | 80x16 | 5 个 16x16，单行：幼苗/生长/长大/即将成熟/可收获成熟 |
| objects.png | 128x16 | 8 个 16x16，单行：树/石头/杂草/出货箱/邮箱/温室残骸/木箱/备用(空) |
| player.png、villager.png | 64x64 | 4 列 x 4 行，16x16/帧；行=down/left/right/up，列=4 帧行走循环 |
| panel.png | 48x48 | 九宫格，边框 8px |
| icons.png | 160x16 | 10 个 16x16：锄头/浇水壶/斧/镐/镰/种子/防风草/木材/石头/纤维 |
| farmhouse.png | 112x64 | 7x4 格农舍外观 |