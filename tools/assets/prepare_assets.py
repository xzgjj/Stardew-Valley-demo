#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""晨溪农场像素素材生成 / 切片 / 校验脚本（Pillow）。

设计原则
--------
* **幂等**：所有像素都由固定算法 + 固定随机种子生成，同一 Pillow 版本重复运行
  得到完全相同的像素，不会因为重复执行而改变仓库内容。
* **可回溯**：Kenney CC0 图集原图存放在 ``assets/source/kenney/``，本脚本按
  固定 tile 索引切片，索引写在 ``KENNEY_SLICES`` 表里，可在 manifest 中复核。
* **可校验**：``--check`` 不写任何文件，只做两件事：
  1. 结构校验（尺寸 / RGBA / 透明背景 / 帧数与帧内容 / 图集格子是否为空）；
  2. 内容校验（用同样的生成函数在内存里重建每个 PNG，与磁盘文件逐像素比对，
     文件被手改过或生成器改过都会报 stale），保证"脚本 → 产物"严格一致。

用法
----
    python -X utf8 tools/assets/prepare_assets.py          # 生成 + 校验
    python -X utf8 tools/assets/prepare_assets.py --check  # 只校验（CI 用）
    python -X utf8 tools/assets/prepare_assets.py --quiet  # 只在失败时输出

素材来源与许可见 ``docs/asset_manifest.md``。
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - 环境缺失时给出可读提示
    sys.exit("缺少 Pillow：请先 pip install pillow")

# --------------------------------------------------------------------------
# 路径
# --------------------------------------------------------------------------
SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]            # <repo>/tools/assets/prepare_assets.py
ASSETS = ROOT / "assets"
SRC_KENNEY = ASSETS / "source" / "kenney"
TILESETS = ASSETS / "tilesets"
CHARACTERS = ASSETS / "characters"
UI = ASSETS / "ui"
PROPS = ASSETS / "props"
FONTS = ASSETS / "fonts"
FONT_FILE = FONTS / "pixel.ttf"

TILE = 16

# --------------------------------------------------------------------------
# 调色板（取自 Kenney "Tiny" 系列图集的原始像素，保证自制件与 CC0 素材同色系）
# --------------------------------------------------------------------------
OUTLINE = (63, 38, 49, 255)

GRASS = (132, 198, 105, 255)
GRASS_LIGHT = (139, 216, 125, 255)
GRASS_DARK = (101, 165, 86, 255)
SAND = (234, 165, 108, 255)
SAND_LIGHT = (254, 201, 156, 255)
SAND_DARK = (207, 130, 84, 255)
SOIL_DARK = (184, 101, 66, 255)
WOOD = (189, 108, 74, 255)
WOOD_LIGHT = (234, 165, 108, 255)
WOOD_DARK = (118, 59, 54, 255)
STONE = (139, 155, 180, 255)
STONE_LIGHT = (192, 203, 220, 255)
STONE_DARK = (90, 105, 136, 255)

WATER_DEEP = (56, 98, 140, 255)
WATER_MID = (78, 134, 182, 255)
WATER_LIGHT = (120, 178, 214, 255)
WATER_FOAM = (176, 214, 238, 255)

WET_BASE = (146, 94, 60, 255)
WET_DARK = (112, 68, 45, 255)
WET_LIGHT = (172, 114, 76, 255)

CREAM = (243, 233, 205, 255)
CREAM_SHADE = (214, 190, 160, 255)
BRICK = (184, 101, 66, 255)
GLASS = (143, 198, 224, 255)
GLASS_LIGHT = (220, 240, 250, 255)
RED_ACCENT = (196, 74, 66, 255)

SKIN = (242, 199, 155, 255)
SKIN_SHADE = (214, 166, 120, 255)
HAIR_BROWN = (139, 90, 60, 255)
HAIR_BROWN_LIGHT = (176, 120, 80, 255)
HAIR_DARK = (90, 58, 40, 255)
HAIR_DARK_LIGHT = (120, 80, 56, 255)
SHIRT_BLUE = (79, 127, 181, 255)
SHIRT_BLUE_DARK = (56, 96, 140, 255)
PANTS_BLUE = (60, 74, 102, 255)
PANTS_BLUE_LIGHT = (78, 95, 128, 255)
BOOT = (118, 59, 54, 255)
APRON = (127, 176, 90, 255)
APRON_DARK = (94, 138, 66, 255)

# --------------------------------------------------------------------------
# Kenney CC0 素材切片表：assets/source/kenney/*.png 中的 tile 索引（12 列网格）
# --------------------------------------------------------------------------
KENNEY_SLICES = {
    # terrain.png
    "terrain_grass": ("tiny-town", 0),          # 纯草地（整格草绿）
    "terrain_grass_tuft": ("tiny-town", 1),     # 草地（深色草丛纹理）
    "terrain_stone": ("tiny-dungeon", 37),      # 石地 / 石板地
    # objects.png
    "tree": ("tiny-town", 17),                  # 16x16 圆冠小树（带树干）
    "rock": ("tiny-farm", 89),                  # 石堆
    "weeds": ("tiny-farm", 80),                 # 杂草
    "crate": ("tiny-farm", 92),                 # 交叉木条木箱
    # ui/icons.png
    "icon_hoe": ("tiny-town", 115),             # 锄头
    "icon_can": ("tiny-farm", 84),              # 浇水壶
    "icon_axe": ("tiny-town", 127),             # 斧头
    "icon_pickaxe": ("tiny-town", 129),         # 镐
    "icon_sickle": ("tiny-farm", 88),           # 镰刀
    "icon_seed": ("tiny-farm", 9),              # 种子袋
    "icon_parsnip": ("tiny-farm", 31),          # 防风草（块根作物）
    "icon_stone": ("tiny-farm", 89),            # 石头
    "icon_fiber": ("tiny-farm", 65),            # 纤维（草束）
}

_ATLAS_CACHE: dict[str, Image.Image] = {}


# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------
def kenney_tile(name: str) -> Image.Image:
    """按切片表取出一个 16x16 的 Kenney 原始 tile（RGBA）。"""
    atlas_name, index = KENNEY_SLICES[name]
    if atlas_name not in _ATLAS_CACHE:
        path = SRC_KENNEY / f"{atlas_name}-tilemap.png"
        if not path.exists():
            raise SystemExit(f"缺少 Kenney 源图集：{path}")
        _ATLAS_CACHE[atlas_name] = Image.open(path).convert("RGBA")
    atlas = _ATLAS_CACHE[atlas_name]
    cols = atlas.width // TILE
    row, col = divmod(index, cols)
    return atlas.crop((col * TILE, row * TILE, col * TILE + TILE, row * TILE + TILE))


def new_tile(color=(0, 0, 0, 0)) -> Image.Image:
    return Image.new("RGBA", (TILE, TILE), color)


def put(im: Image.Image, x: int, y: int, color) -> None:
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), color)


def rect(im: Image.Image, x0: int, y0: int, x1: int, y1: int, color) -> None:
    """闭区间矩形填充。"""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(im, x, y, color)


def outline(im: Image.Image, color=OUTLINE) -> Image.Image:
    """给当前不透明像素做 1px 外描边（只描剪影外侧，不会画进内部）。

    这是让自制像素件与 Kenney 素材（都有深色描边）风格一致的关键步骤。
    """
    src = im.load()
    w, h = im.size
    mask = [[src[x, y][3] > 0 for y in range(h)] for x in range(w)]
    out = im.copy()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if mask[x][y]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and mask[nx][ny]:
                    dst[x, y] = color
                    break
    return out


def speckle(im: Image.Image, rng: random.Random, count: int, colors) -> None:
    """在已有像素上撒固定数量的确定色点（用于土壤 / 水面的颗粒感）。"""
    opaque = [
        (x, y)
        for y in range(im.height)
        for x in range(im.width)
        if im.getpixel((x, y))[3] > 0
    ]
    if not opaque:
        return
    for _ in range(count):
        x, y = opaque[rng.randrange(len(opaque))]
        im.putpixel((x, y), colors[rng.randrange(len(colors))])


def mirror(im: Image.Image) -> Image.Image:
    return im.transpose(Image.FLIP_LEFT_RIGHT)


def ok(im: Image.Image) -> Image.Image:
    return im.convert("RGBA")


# --------------------------------------------------------------------------
# terrain.png —— 8 格：草 / 草(深) / 泥土路 / 干耕地 / 湿耕地 / 水面 / 石地 / 木地板
# --------------------------------------------------------------------------
def _dirt_path() -> Image.Image:
    """泥土路：Kenney 沙土底色 + 疏落的土粒 / 小石子，做成可平铺的土路面。"""
    tile = new_tile(SAND)
    rng = random.Random(20260101)
    speckle(tile, rng, 12, (SAND_DARK,))
    speckle(tile, rng, 5, (SAND_LIGHT,))
    for x, y in ((3, 5), (10, 2), (13, 9), (6, 13)):
        put(tile, x, y, STONE_LIGHT)
    return tile


def _tilled_soil(wet: bool) -> Image.Image:
    """耕地：断续犁沟 + 土块颗粒。干 / 湿只差色调与水光。"""
    base = WET_BASE if wet else SAND_DARK
    groove = WET_DARK if wet else SOIL_DARK
    ridge = WET_LIGHT if wet else SAND
    tile = new_tile(base)
    for y in range(TILE):
        if y % 4 == 1:                       # 犁沟（断续，避免像木板）
            for x in range(TILE):
                if (x // 3 + y // 4) % 4 != 0:
                    put(tile, x, y, groove)
        elif y % 4 == 3:                     # 犁沟旁的土垄高光
            for x in range(TILE):
                if (x // 2 + y) % 3 == 0:
                    put(tile, x, y, ridge)
    rng = random.Random(777 if wet else 778)
    speckle(tile, rng, 18, (groove, base))
    speckle(tile, rng, 6, (ridge,))
    if wet:
        for x, y in ((3, 6), (12, 7), (7, 12), (14, 13), (5, 3)):
            put(tile, x, y, (150, 186, 206, 255))   # 水膜冷色高光
    return tile


def _water() -> Image.Image:
    """水面：正弦波纹（周期 = 图块宽度，保证平铺无缝）+ 泡沫点。"""
    tile = new_tile(WATER_MID)
    for base_y, amp, thick in ((3, 1.1, 2), (10, 0.9, 1)):
        for x in range(TILE):
            wy = int(round(base_y + amp * math.sin(x * 2 * math.pi / TILE)))
            for k in range(thick):
                put(tile, x, wy + k, WATER_LIGHT)
    for x, y in ((5, 3), (12, 4), (8, 10), (2, 11)):
        put(tile, x, y, WATER_FOAM)
    rng = random.Random(4242)
    speckle(tile, rng, 10, (WATER_DEEP,))
    for x, y in ((0, 6), (7, 6), (15, 6), (3, 13), (11, 14)):
        put(tile, x, y, WATER_DEEP)
    return tile


def _wood_floor() -> Image.Image:
    """木地板：横向木板的板缝 + 高光 + 错缝，可四向平铺。"""
    tile = new_tile(WOOD)
    for y in range(TILE):
        phase = y % 4
        for x in range(TILE):
            if phase == 3:
                put(tile, x, y, WOOD_DARK)
            elif phase == 0:
                put(tile, x, y, WOOD_LIGHT)
    for y0, sx in ((0, 8), (4, 4), (8, 8), (12, 4)):     # 错开的板端缝
        for y in range(y0, min(y0 + 3, TILE)):
            put(tile, sx, y, WOOD_DARK)
    for x, y in ((2, 1), (9, 5), (5, 9), (12, 13), (14, 1)):
        put(tile, x, y, WOOD_DARK)                       # 木纹
    return tile


def build_terrain() -> Image.Image:
    sheet = Image.new("RGBA", (8 * TILE, TILE), (0, 0, 0, 0))
    sheet.alpha_composite(kenney_tile("terrain_grass"), (0, 0))
    sheet.alpha_composite(kenney_tile("terrain_grass_tuft"), (TILE, 0))
    sheet.alpha_composite(_dirt_path(), (2 * TILE, 0))
    sheet.alpha_composite(_tilled_soil(wet=False), (3 * TILE, 0))
    sheet.alpha_composite(_tilled_soil(wet=True), (4 * TILE, 0))
    sheet.alpha_composite(_water(), (5 * TILE, 0))
    sheet.alpha_composite(kenney_tile("terrain_stone"), (6 * TILE, 0))
    sheet.alpha_composite(_wood_floor(), (7 * TILE, 0))
    return sheet


# --------------------------------------------------------------------------
# crops.png —— 防风草 5 阶段（0 幼苗 → 4 成熟可收获），自制像素
# --------------------------------------------------------------------------

# 16x16 像素掩码：'.' 透明 / 'g' 叶 / 'G' 亮叶 / 'd' 暗叶 / 'r' 块根亮面 /
# 's' 块根暗面。逐阶段手工排布，保证"越来越茂盛、最后露出可收获的块根"。
_CROP_MASKS = (
    # 0 幼苗：两片小叶 + 短茎
    (
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        ".......G........",
        "......GgG.......",
        ".......g........",
        ".......g........",
        "................",
        "................",
        "................",
    ),
    # 1 生长：叶丛分叉
    (
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        ".......G........",
        "......GGg.......",
        ".....Ggggg......",
        "......gGg.......",
        ".......g........",
        ".......g........",
        "................",
        "................",
    ),
    # 2 长大：叶丛铺开
    (
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        ".......G........",
        "......GGg.......",
        ".....GggggG.....",
        "....Gggggggg....",
        ".....dggggd.....",
        "......gGg.......",
        ".......g........",
        ".......g........",
        "................",
        "................",
    ),
    # 3 即将成熟：植株变高，块根顶出地面
    (
        "................",
        "................",
        "................",
        ".......G........",
        "......GGg.......",
        ".....GggggG.....",
        "....Gggggggg....",
        "...Gggggggggg...",
        "....dggggggd....",
        ".....dggggd.....",
        "......rrr.......",
        "......rrs.......",
        ".......s........",
        "................",
        "................",
        "................",
    ),
    # 4 可收获成熟：大叶丛 + 露出的块根
    (
        "................",
        ".......G........",
        "......GGg.......",
        ".....GggggG.....",
        "....Gggggggg....",
        "...Gggggggggg...",
        "..Gggggggggggg..",
        "...dggggggggd...",
        "....dggggggd....",
        ".....dggggd.....",
        ".....rrrrrr.....",
        ".....rrrrrs.....",
        "......ssss......",
        "................",
        "................",
        "................",
    ),
)

_CROP_PIXELS = {
    "g": GRASS,
    "G": GRASS_LIGHT,
    "d": GRASS_DARK,
    "r": SAND_LIGHT,
    "s": SAND,
}


def _from_mask(mask) -> Image.Image:
    """把 16x16 字符掩码转成像素图（不描边）。"""
    tile = new_tile()
    for y, line in enumerate(mask):
        for x, ch in enumerate(line):
            if ch in _CROP_PIXELS:
                put(tile, x, y, _CROP_PIXELS[ch])
    return tile


_GREEN_SET = {GRASS, GRASS_LIGHT, GRASS_DARK}


def _shade_blob(tile: Image.Image) -> Image.Image:
    """给自制叶片加"自动边缘光"：上缘提亮、下缘压暗，让纯色块有体积感。

    只重染绿色像素，块根（米色）与描边不受影响。
    """
    src = tile.load()
    w, h = tile.size
    out = tile.copy()
    dst = out.load()
    solid = lambda x, y: 0 <= x < w and 0 <= y < h and src[x, y][3] > 0
    for y in range(h):
        for x in range(w):
            cur = src[x, y]
            if cur[3] == 0 or cur not in _GREEN_SET:
                continue
            if not solid(x, y - 1) or not solid(x - 1, y):
                dst[x, y] = GRASS_LIGHT          # 左上受光
            elif not solid(x, y + 1) or not solid(x + 1, y):
                dst[x, y] = GRASS_DARK           # 右下入影
    return out


def build_crops() -> Image.Image:
    sheet = Image.new("RGBA", (5 * TILE, TILE), (0, 0, 0, 0))
    for stage, mask in enumerate(_CROP_MASKS):
        sheet.alpha_composite(outline(_shade_blob(_from_mask(mask))), (stage * TILE, 0))
    return sheet


# --------------------------------------------------------------------------
# objects.png —— 8 格：树 / 石 / 杂草 / 出货箱 / 邮箱 / 温室残骸 / 木箱 / 备用
# --------------------------------------------------------------------------
def _mailbox() -> Image.Image:
    tile = new_tile()
    rect(tile, 7, 8, 8, 15, WOOD_DARK)          # 木桩
    put(tile, 7, 15, OUTLINE)
    put(tile, 8, 15, OUTLINE)
    rect(tile, 4, 3, 11, 8, WOOD)               # 箱体
    rect(tile, 5, 2, 10, 2, WOOD_LIGHT)         # 箱顶高光
    rect(tile, 4, 7, 11, 8, WOOD_DARK)          # 箱体下部阴影
    rect(tile, 5, 5, 10, 5, OUTLINE)            # 投信口
    rect(tile, 11, 3, 12, 6, RED_ACCENT)        # 红色旗标
    put(tile, 12, 6, RED_ACCENT)
    return outline(tile)


def _greenhouse_ruin() -> Image.Image:
    """温室残骸：歪斜的木框 + 残缺的玻璃 + 地上的碎玻璃。"""
    tile = new_tile()
    glass = (176, 214, 190, 255)
    glass_dark = (128, 172, 148, 255)
    # 底座木台
    rect(tile, 2, 13, 13, 14, WOOD_DARK)
    rect(tile, 2, 13, 13, 13, WOOD)
    # 左立柱（完整）
    rect(tile, 2, 5, 3, 12, WOOD)
    rect(tile, 2, 5, 2, 12, WOOD_DARK)
    # 右立柱（断掉，比左边矮）
    rect(tile, 12, 8, 13, 12, WOOD_DARK)
    # 玻璃墙：左段完整，右段缺失
    rect(tile, 4, 8, 8, 12, glass)
    rect(tile, 4, 8, 8, 8, glass_dark)
    rect(tile, 6, 8, 6, 12, WOOD)          # 窗棂
    rect(tile, 4, 10, 8, 10, WOOD_DARK)
    # 裂痕
    put(tile, 5, 9, glass_dark)
    put(tile, 5, 11, glass_dark)
    put(tile, 7, 12, glass_dark)
    # 歪斜的屋顶横梁（右端断裂）
    rect(tile, 2, 4, 6, 4, WOOD_LIGHT)
    rect(tile, 3, 3, 5, 3, WOOD_LIGHT)
    put(tile, 7, 3, WOOD_LIGHT)
    put(tile, 8, 2, WOOD_LIGHT)
    # 地上碎玻璃
    put(tile, 10, 12, glass_dark)
    put(tile, 11, 12, glass)
    put(tile, 14, 13, glass_dark)
    put(tile, 1, 12, glass_dark)
    put(tile, 9, 13, glass)
    return outline(tile)


def _shipping_bin() -> Image.Image:
    """出货箱：掀开的箱盖 + 深色箱口 + 板条箱身（自制，替代 Kenney 的柜子图）。"""
    tile = new_tile()
    rect(tile, 2, 2, 13, 4, WOOD)               # 掀起的箱盖
    rect(tile, 3, 2, 12, 2, WOOD_LIGHT)
    rect(tile, 2, 4, 13, 4, WOOD_DARK)
    rect(tile, 2, 6, 13, 8, (46, 32, 34, 255))  # 箱口内部阴影
    rect(tile, 3, 6, 12, 6, OUTLINE)
    rect(tile, 2, 9, 13, 14, WOOD)              # 箱身
    rect(tile, 3, 9, 12, 9, WOOD_LIGHT)         # 沿口高光
    rect(tile, 2, 14, 13, 14, WOOD_DARK)
    for x in (5, 8, 11):                        # 板条缝
        rect(tile, x, 10, x, 13, WOOD_DARK)
    rect(tile, 2, 11, 2, 11, WOOD_DARK)
    return outline(tile)


def _wood_log() -> Image.Image:
    """木材图标：两根圆木（端面年轮 + 树皮）。"""
    tile = new_tile()
    # 下面第一根
    rect(tile, 1, 9, 14, 13, WOOD)
    rect(tile, 1, 9, 14, 9, WOOD_LIGHT)
    rect(tile, 1, 13, 14, 13, WOOD_DARK)
    rect(tile, 2, 10, 3, 12, SAND_LIGHT)        # 端面
    put(tile, 3, 11, SAND)
    # 上面第二根
    rect(tile, 3, 3, 14, 7, WOOD)
    rect(tile, 3, 3, 14, 3, WOOD_LIGHT)
    rect(tile, 3, 7, 14, 7, WOOD_DARK)
    rect(tile, 4, 4, 5, 6, SAND_LIGHT)
    put(tile, 5, 5, SAND)
    return outline(tile)


def build_objects() -> Image.Image:
    sheet = Image.new("RGBA", (8 * TILE, TILE), (0, 0, 0, 0))
    sheet.alpha_composite(kenney_tile("tree"), (0, 0))
    sheet.alpha_composite(kenney_tile("rock"), (TILE, 0))
    sheet.alpha_composite(kenney_tile("weeds"), (2 * TILE, 0))
    sheet.alpha_composite(_shipping_bin(), (3 * TILE, 0))
    sheet.alpha_composite(_mailbox(), (4 * TILE, 0))
    sheet.alpha_composite(_greenhouse_ruin(), (5 * TILE, 0))
    sheet.alpha_composite(kenney_tile("crate"), (6 * TILE, 0))
    # 第 7 格「备用」：留空（全透明），占位给后续对象，不引入额外美术
    return sheet


# --------------------------------------------------------------------------
# ui/icons.png —— 10 个 16x16 图标：锄头/水壶/斧/镐/镰/种子/防风草/木材/石/纤维
# --------------------------------------------------------------------------
ICON_ORDER = (
    "icon_hoe",
    "icon_can",
    "icon_axe",
    "icon_pickaxe",
    "icon_sickle",
    "icon_seed",
    "icon_parsnip",
    "_wood_log",        # 自制（Kenney 图集里没有合适的圆木图标）
    "icon_stone",
    "icon_fiber",
)


def build_icons() -> Image.Image:
    sheet = Image.new("RGBA", (len(ICON_ORDER) * TILE, TILE), (0, 0, 0, 0))
    for i, key in enumerate(ICON_ORDER):
        tile = _wood_log() if key == "_wood_log" else kenney_tile(key)
        sheet.alpha_composite(tile, (i * TILE, 0))
    return sheet


# --------------------------------------------------------------------------
# ui/panel.png —— 48x48 九宫格面板（边框 8px，四角圆角）
# --------------------------------------------------------------------------
def build_panel() -> Image.Image:
    size = 48
    border = 8
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, size - 1, size - 1], fill=(CREAM[0], CREAM[1], CREAM[2], 235))
    # 外描边
    d.rectangle([0, 0, size - 1, size - 1], outline=OUTLINE)
    # 木色边框 1..6
    d.rectangle([1, 1, size - 2, size - 2], outline=WOOD)
    d.rectangle([2, 2, size - 3, size - 3], outline=WOOD)
    d.rectangle([3, 3, size - 4, size - 4], outline=WOOD)
    d.rectangle([4, 4, size - 5, size - 5], outline=WOOD)
    d.rectangle([5, 5, size - 6, size - 6], outline=WOOD)
    d.rectangle([6, 6, size - 7, size - 7], outline=WOOD)
    # 高光（左/上）与阴影（右/下）
    d.line([1, 1, size - 2, 1], fill=WOOD_LIGHT)
    d.line([1, 1, 1, size - 2], fill=WOOD_LIGHT)
    d.line([1, size - 2, size - 2, size - 2], fill=WOOD_DARK)
    d.line([size - 2, 1, size - 2, size - 2], fill=WOOD_DARK)
    # 内框线 + 面板内部
    d.rectangle([border - 1, border - 1, size - border, size - border], outline=OUTLINE)
    d.rectangle([border, border, size - border - 1, size - border - 1],
                fill=(CREAM[0], CREAM[1], CREAM[2], 235))
    # 内部左上角一点暖色内阴影
    d.line([border, border, size - border - 1, border], fill=CREAM_SHADE)
    d.line([border, border, border, size - border - 1], fill=CREAM_SHADE)
    # 圆角：清掉四角半径 3 的像素
    px = im.load()
    radius = 3
    for y in range(radius):
        for x in range(radius):
            if (x - (radius - 0.5)) ** 2 + (y - (radius - 0.5)) ** 2 > (radius - 0.3) ** 2:
                px[x, y] = (0, 0, 0, 0)
                px[size - 1 - x, y] = (0, 0, 0, 0)
                px[x, size - 1 - y] = (0, 0, 0, 0)
                px[size - 1 - x, size - 1 - y] = (0, 0, 0, 0)
    return im


# --------------------------------------------------------------------------
# props/farmhouse.png —— 112x64（7x4 格）农舍外观，自制像素
# --------------------------------------------------------------------------
def build_farmhouse() -> Image.Image:
    w, h = 112, 64
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()

    def fill(x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(h, y1 + 1)):
            for x in range(max(0, x0), min(w, x1 + 1)):
                px[x, y] = c

    ROOF = (184, 84, 72, 255)
    ROOF_DARK = (146, 62, 56, 255)
    ROOF_LIGHT = (214, 118, 96, 255)

    # 烟囱
    fill(84, 2, 95, 18, BRICK)
    fill(84, 2, 95, 3, OUTLINE)
    fill(82, 2, 97, 2, OUTLINE)
    for y in (7, 12):
        fill(84, y, 95, y, SOIL_DARK)

    # 屋顶：梯形 (y=6..28)
    apex_y, eave_y = 6, 28
    for y in range(apex_y, eave_y + 1):
        t = (y - apex_y) / (eave_y - apex_y)
        half = int(round(10 + t * 46))
        fill(56 - half, y, 56 + half, y, ROOF)
        if (y - apex_y) % 5 == 4:
            fill(56 - half, y, 56 + half, y, ROOF_DARK)
    # 屋顶边缘 / 檐口
    fill(4, eave_y, 107, eave_y + 2, ROOF_DARK)
    fill(4, eave_y + 3, 107, eave_y + 3, OUTLINE)
    # 屋脊高光
    fill(54, apex_y, 58, apex_y, ROOF_LIGHT)
    fill(53, apex_y + 1, 59, apex_y + 1, ROOF_LIGHT)

    # 墙体
    fill(7, 32, 104, 58, CREAM)
    fill(7, 32, 104, 33, CREAM_SHADE)          # 墙顶阴影
    # 竖向木板纹理
    for x in range(12, 104, 9):
        fill(x, 34, x, 58, CREAM_SHADE)
    # 角柱
    fill(7, 32, 10, 58, WOOD)
    fill(101, 32, 104, 58, WOOD)
    fill(7, 32, 7, 58, WOOD_DARK)
    fill(104, 32, 104, 58, WOOD_DARK)

    # 地基（石）
    fill(4, 59, 107, 63, STONE)
    fill(4, 59, 107, 59, STONE_LIGHT)
    for x in range(6, 107, 12):
        fill(x, 61, x + 3, 61, STONE_DARK)
    fill(4, 63, 107, 63, OUTLINE)

    # 门（居中）
    fill(46, 36, 66, 60, WOOD_DARK)
    fill(47, 37, 65, 60, WOOD)
    fill(49, 38, 63, 58, (166, 96, 64, 255))
    fill(49, 38, 63, 38, WOOD_DARK)
    for y in range(41, 58, 5):
        fill(49, y, 63, y, WOOD_DARK)
    fill(60, 47, 61, 49, WOOD_LIGHT)          # 门把手
    fill(46, 60, 66, 60, STONE_DARK)          # 门槛

    # 窗（左右各一扇）
    for wx in (18, 78):
        fill(wx - 2, 38, wx + 18, 52, WOOD_DARK)
        fill(wx, 40, wx + 16, 50, GLASS)
        fill(wx, 40, wx + 16, 41, GLASS_LIGHT)
        fill(wx + 8, 40, wx + 8, 50, WOOD_DARK)   # 竖中梃
        fill(wx, 45, wx + 16, 45, WOOD_DARK)      # 横中梃
        fill(wx + 2, 42, wx + 4, 43, GLASS_LIGHT) # 玻璃反光
        fill(wx - 2, 53, wx + 18, 55, WOOD)       # 窗台花箱
        fill(wx, 53, wx + 16, 53, WOOD_LIGHT)
        for fx in range(wx + 1, wx + 16, 4):
            put(im, fx, 52, GRASS_DARK)
            put(im, fx + 1, 51, RED_ACCENT if (fx // 4) % 2 else GRASS)

    # 门牌
    fill(52, 30, 60, 34, WOOD_LIGHT)
    fill(53, 31, 59, 33, CREAM)

    return outline(im)


# --------------------------------------------------------------------------
# characters —— 16x16 四方向 x 4 帧行走图集（4 列 x 4 行）
#   行 0 = down，行 1 = left，行 2 = right，行 3 = up；列 = 行走帧
# --------------------------------------------------------------------------
CHAR_DIRS = ("down", "left", "right", "up")


def _char_palette(kind: str) -> dict:
    if kind == "player":
        return {
            "hair": HAIR_BROWN,
            "hair_lt": HAIR_BROWN_LIGHT,
            "skin": SKIN,
            "skin_sh": SKIN_SHADE,
            "eye": OUTLINE,
            "shirt": SHIRT_BLUE,
            "shirt_sh": SHIRT_BLUE_DARK,
            "pants": PANTS_BLUE,
            "pants_lt": PANTS_BLUE_LIGHT,
            "boot": BOOT,
            "accent": APRON,            # 背带裤围裙
            "long_hair": False,
            "skirt": False,
        }
    return {
        "hair": HAIR_DARK,
        "hair_lt": HAIR_DARK_LIGHT,
        "skin": (240, 205, 170, 255),
        "skin_sh": (212, 172, 136, 255),
        "eye": OUTLINE,
        "shirt": CREAM,                 # 米色上衣
        "shirt_sh": CREAM_SHADE,
        "pants": APRON,                 # 绿色长裙
        "pants_lt": APRON_DARK,
        "boot": WOOD_DARK,
        "accent": RED_ACCENT,           # 发带 / 领巾
        "long_hair": True,
        "skirt": True,
    }


def _leg_phase(frame: int) -> int:
    """0 = 并腿；1 / -1 = 前后脚（帧 1 与帧 3 相反）。"""
    return (0, 1, 0, -1)[frame % 4]


def _shift_up(im: Image.Image) -> Image.Image:
    """整体上移 1px：行走"起伏"帧，让 4 帧循环看起来在迈步而不是滑行。"""
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im.crop((0, 0, im.width, im.height - 1)), (0, 0))
    return out


def _draw_legs(t: Image.Image, p: dict, ph: int) -> None:
    """下身：短裤 / 长裙 + 靴子。ph>0 左脚前，ph<0 右脚前。"""
    if p["skirt"]:
        rect(t, 5, 12, 10, 13, p["pants"])
        rect(t, 5, 13, 10, 13, p["pants_lt"])
        lx = 5 - (1 if ph > 0 else 0)
        rx = 9 + (1 if ph < 0 else 0)
        rect(t, lx, 14, lx + 1, 14, p["boot"])
        rect(t, rx, 14, rx + 1, 14, p["boot"])
        return
    lx = 5 - (1 if ph > 0 else 0)
    rx = 9 + (1 if ph < 0 else 0)
    rect(t, lx, 12, lx + 1, 13, p["pants"])
    rect(t, rx, 12, rx + 1, 13, p["pants_lt"])
    rect(t, lx, 14, lx + 1, 14, p["boot"])
    rect(t, rx, 14, rx + 1, 14, p["boot"])


def _draw_torso(t: Image.Image, p: dict, ph: int, facing_back: bool) -> None:
    rect(t, 4, 8, 11, 11, p["shirt"])
    rect(t, 4, 11, 11, 11, p["shirt_sh"])
    if facing_back:
        rect(t, 7, 8, 8, 10, p["shirt_sh"])
    else:
        # 围裙 / 背带
        put(t, 6, 8, p["accent"])
        put(t, 9, 8, p["accent"])
        rect(t, 6, 9, 9, 10, p["accent"])
        rect(t, 7, 9, 8, 10, p["shirt"])
    # 手臂（前后摆）
    rect(t, 3, 8 + (1 if ph > 0 else 0), 3, 10, p["shirt_sh"])
    rect(t, 12, 8 + (1 if ph < 0 else 0), 12, 10, p["shirt_sh"])
    put(t, 3, 11, p["skin"])
    put(t, 12, 11, p["skin"])


def _draw_down(p: dict, frame: int) -> Image.Image:
    t = new_tile()
    ph = _leg_phase(frame)
    # 头发（圆顶 + 鬓角）
    rect(t, 5, 2, 10, 2, p["hair"])
    rect(t, 4, 3, 11, 3, p["hair"])
    rect(t, 4, 4, 4, 6, p["hair"])
    rect(t, 11, 4, 11, 6, p["hair"])
    put(t, 5, 2, p["hair_lt"])
    put(t, 6, 2, p["hair_lt"])
    put(t, 5, 3, p["hair_lt"])
    # 脸
    rect(t, 5, 4, 10, 6, p["skin"])
    rect(t, 5, 6, 10, 6, p["skin_sh"])
    put(t, 6, 5, p["eye"])
    put(t, 9, 5, p["eye"])
    # 颈部
    rect(t, 7, 7, 8, 7, p["skin_sh"])
    _draw_torso(t, p, ph, facing_back=False)
    _draw_legs(t, p, ph)
    return t


def _draw_up(p: dict, frame: int) -> Image.Image:
    t = new_tile()
    ph = _leg_phase(frame)
    # 后脑（整片头发，无五官）
    rect(t, 5, 2, 10, 2, p["hair"])
    rect(t, 4, 3, 11, 3, p["hair"])
    rect(t, 4, 4, 11, 6, p["hair"])
    rect(t, 5, 7, 10, 7, p["hair"])          # 后颈发尾
    put(t, 5, 2, p["hair_lt"])
    put(t, 6, 2, p["hair_lt"])
    put(t, 7, 4, p["hair_lt"])               # 发丝高光
    put(t, 8, 5, p["hair_lt"])
    if p["long_hair"]:
        rect(t, 4, 7, 4, 9, p["hair"])
        rect(t, 11, 7, 11, 9, p["hair"])
    rect(t, 7, 8, 8, 8, p["skin_sh"])        # 脖颈
    _draw_torso(t, p, ph, facing_back=True)
    _draw_legs(t, p, ph)
    return t


def _draw_side(p: dict, frame: int) -> Image.Image:
    """统一画"朝右"的侧面，left 由 _char_frame 镜像得到。"""
    t = new_tile()
    ph = _leg_phase(frame)
    # 头：后脑在左，脸朝右
    rect(t, 5, 2, 10, 2, p["hair"])
    rect(t, 4, 3, 10, 3, p["hair"])
    rect(t, 4, 4, 5, 6, p["hair"])            # 后脑头发
    rect(t, 6, 4, 10, 6, p["skin"])           # 脸
    rect(t, 6, 6, 10, 6, p["skin_sh"])
    put(t, 9, 5, p["eye"])
    put(t, 10, 5, p["skin"])                  # 鼻尖
    put(t, 5, 2, p["hair_lt"])
    put(t, 6, 2, p["hair_lt"])
    if p["long_hair"]:
        rect(t, 4, 7, 5, 9, p["hair"])
    # 脖子
    rect(t, 7, 7, 8, 7, p["skin_sh"])
    # 躯干（侧面窄一点）
    rect(t, 5, 8, 10, 11, p["shirt"])
    rect(t, 5, 11, 10, 11, p["shirt_sh"])
    put(t, 9, 8, p["accent"])
    put(t, 9, 9, p["accent"])
    # 前臂
    ax = 10 + (1 if ph > 0 else 0)
    rect(t, ax, 8, ax, 10, p["shirt_sh"])
    put(t, ax, 11, p["skin"])
    # 腿：前后错开
    fx = 7 + (1 if ph > 0 else 0)
    bx = 7 - (1 if ph < 0 else 0)
    if p["skirt"]:
        rect(t, 5, 12, 9, 13, p["pants"])
        rect(t, 5, 13, 9, 13, p["pants_lt"])
        rect(t, bx + 1, 14, bx + 2, 14, p["boot"])
        rect(t, fx + 2, 14, fx + 3, 14, p["boot"])
        return t
    rect(t, bx + 1, 12, bx + 2, 13, p["pants"])
    rect(t, fx + 2, 12, fx + 3, 13, p["pants_lt"])
    rect(t, bx + 1, 14, bx + 2, 14, p["boot"])
    rect(t, fx + 2, 14, fx + 3, 14, p["boot"])
    return t


def _char_frame(p: dict, direction: str, frame: int) -> Image.Image:
    if direction == "down":
        t = _draw_down(p, frame)
    elif direction == "up":
        t = _draw_up(p, frame)
    else:
        t = _draw_side(p, frame)
    if _leg_phase(frame) != 0:
        t = _shift_up(t)
    if direction == "left":
        t = mirror(t)
    return outline(t)


def build_character(kind: str) -> Image.Image:
    palette = _char_palette(kind)
    sheet = Image.new("RGBA", (4 * TILE, 4 * TILE), (0, 0, 0, 0))
    for row, direction in enumerate(CHAR_DIRS):
        for frame in range(4):
            sheet.alpha_composite(
                _char_frame(palette, direction, frame), (frame * TILE, row * TILE)
            )
    return sheet


# --------------------------------------------------------------------------
# 产物表 + 校验
# --------------------------------------------------------------------------
BUILDERS = {
    TILESETS / "terrain.png": (build_terrain, (128, 16)),
    TILESETS / "crops.png": (build_crops, (80, 16)),
    TILESETS / "objects.png": (build_objects, (128, 16)),
    CHARACTERS / "player.png": (lambda: build_character("player"), (64, 64)),
    CHARACTERS / "villager.png": (lambda: build_character("villager"), (64, 64)),
    UI / "panel.png": (build_panel, (48, 48)),
    UI / "icons.png": (build_icons, (160, 16)),
    PROPS / "farmhouse.png": (build_farmhouse, (112, 64)),
}


def _tiles(im: Image.Image) -> list[Image.Image]:
    return [
        im.crop((c * TILE, 0, c * TILE + TILE, TILE))
        for c in range(im.width // TILE)
    ]


def _alpha_bytes(im: Image.Image) -> bytes:
    return im.getchannel("A").tobytes()


def _opaque_count(im: Image.Image) -> int:
    return sum(1 for a in _alpha_bytes(im) if a > 0)


def _check_structure(errors: list[str]) -> None:
    terrain = Image.open(TILESETS / "terrain.png")
    for i, t in enumerate(_tiles(terrain)):
        if _opaque_count(t) != TILE * TILE:
            errors.append(f"terrain.png 第 {i} 格必须完全不透明（地面不能漏底）")

    objects = Image.open(TILESETS / "objects.png")
    for i, t in enumerate(_tiles(objects)):
        n = _opaque_count(t)
        if i < 7 and n == 0:
            errors.append(f"objects.png 第 {i} 格为空")
        if i == 7 and n != 0:
            errors.append("objects.png 第 7 格（备用）约定为空白")

    for name in ("crops.png", "icons.png"):
        im = Image.open(TILESETS / name if name == "crops.png" else UI / name)
        tiles = _tiles(im)
        tags = "生长阶段" if name == "crops.png" else "图标"
        for i, t in enumerate(tiles):
            if _opaque_count(t) == 0:
                errors.append(f"{name} 第 {i} 个{tags}为空")
        if name == "icons.png":
            seen = {}
            for i, t in enumerate(tiles):
                key = t.tobytes()
                if key in seen:
                    errors.append(f"icons.png 图标 {i} 与图标 {seen[key]} 重复")
                seen[key] = i

    for name in ("player.png", "villager.png"):
        im = Image.open(CHARACTERS / name)
        frames = []
        for row in range(4):
            for col in range(4):
                frames.append(im.crop((col * TILE, row * TILE, col * TILE + TILE, row * TILE + TILE)))
        for i, f in enumerate(frames):
            if _opaque_count(f) == 0:
                errors.append(f"{name} 第 {i} 帧（行 {i // 4} 列 {i % 4}）为空")
            if 0 not in _alpha_bytes(f):
                errors.append(f"{name} 第 {i} 帧没有透明像素（应保留透明背景）")
        # 行走帧之间必须有差异，否则是静态图
        for row in range(4):
            variants = {frames[row * 4 + c].tobytes() for c in range(4)}
            if len(variants) < 3:
                errors.append(f"{name} 第 {row} 行行走帧差异不足（{len(variants)} 种）")

    panel = Image.open(UI / "panel.png")
    if panel.getpixel((0, 0))[3] != 0 or panel.getpixel((47, 47))[3] != 0:
        errors.append("panel.png 四角应透明（九宫格圆角）")
    if panel.getpixel((24, 24))[3] == 0:
        errors.append("panel.png 中心应为不透明面板底色")

    house = Image.open(PROPS / "farmhouse.png")
    if 0 not in _alpha_bytes(house):
        errors.append("farmhouse.png 应保留透明背景")
    if _opaque_count(house) < house.width * house.height * 0.5:
        errors.append("farmhouse.png 可用像素过少，疑似绘制失败")


def _check_font(errors: list[str]) -> None:
    if not FONT_FILE.exists():
        errors.append(f"缺少字体文件 {FONT_FILE}")
        return
    data = FONT_FILE.read_bytes()
    if len(data) < 100_000:
        errors.append("pixel.ttf 体积异常（可能不是完整中文字体）")
    if data[:4] not in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
        errors.append("pixel.ttf 不是合法 TTF/OTF（sfnt 头不符）")
    try:
        from fontTools.ttLib import TTFont  # 可选依赖，缺失则退化为渲染校验
    except ImportError:
        from PIL import ImageFont
        try:
            font = ImageFont.truetype(str(FONT_FILE), 12)
        except OSError:
            errors.append("pixel.ttf 无法被 PIL 加载")
            return
        for ch in "晨溪农场":
            if font.getbbox(ch)[2] - font.getbbox(ch)[0] <= 0:
                errors.append(f"pixel.ttf 缺少汉字「{ch}」的可见字形")
        return
    try:
        cmap = TTFont(str(FONT_FILE)).getBestCmap()
    except Exception as exc:  # noqa: BLE001 - 任何解析失败都要报可读信息
        errors.append(f"pixel.ttf 解析失败：{exc}")
        return
    missing = [ch for ch in "晨溪农场金币种子收获" if ord(ch) not in cmap]
    if missing:
        errors.append(f"pixel.ttf 缺少简体中文字形：{''.join(missing)}")


def _check_files(errors: list[str]) -> None:
    for path, (builder, size) in BUILDERS.items():
        if not path.exists():
            errors.append(f"缺少文件 {path.relative_to(ROOT)}")
            continue
        with Image.open(path) as im:
            if im.mode != "RGBA":
                errors.append(f"{path.relative_to(ROOT)} 必须是 RGBA（含 alpha 通道）")
            if im.size != size:
                errors.append(
                    f"{path.relative_to(ROOT)} 尺寸 {im.size} 与契约 {size} 不符"
                )
                continue
            expected = builder().convert("RGBA")
            if im.convert("RGBA").tobytes() != expected.tobytes():
                errors.append(
                    f"{path.relative_to(ROOT)} 与生成脚本产物不一致（stale：手改过或生成器已变）"
                )


def _check_sources(errors: list[str]) -> None:
    for name in ("tiny-farm", "tiny-town", "tiny-dungeon"):
        path = SRC_KENNEY / f"{name}-tilemap.png"
        if not path.exists():
            errors.append(f"缺少 Kenney 源图集 {path.relative_to(ROOT)}")
    for name in ("tiny-farm", "tiny-town", "tiny-dungeon"):
        lic = ASSETS / "licenses" / f"kenney-{name}-License.txt"
        if not lic.exists():
            errors.append(f"缺少许可文本 {lic.relative_to(ROOT)}")
    ofl = ASSETS / "licenses" / "ark-pixel-font-OFL.txt"
    if not ofl.exists():
        errors.append(f"缺少字体许可文本 {ofl.relative_to(ROOT)}")


CHECKS = (
    ("产物尺寸 / 帧布局", _check_structure),
    ("生成一致性", _check_files),
    ("字体", _check_font),
    ("素材来源与许可", _check_sources),
)


def run_check(quiet: bool = False) -> int:
    errors: list[str] = []
    for title, fn in CHECKS:
        before = len(errors)
        try:
            fn(errors)
        except Exception as exc:  # noqa: BLE001 - 校验器自身异常也要报告而不是崩栈
            errors.append(f"{title} 校验抛错：{exc}")
        if not quiet:
            state = "OK" if len(errors) == before else "FAIL"
            print(f"  [{state}] {title}")
    if errors:
        print("素材校验失败：", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if not quiet:
        print(f"素材校验通过：{len(BUILDERS)} 个 PNG + pixel.ttf + 源图集 + 许可文本")
    return 0


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------
def build_all(quiet: bool = False) -> None:
    for d in (TILESETS, CHARACTERS, UI, PROPS, FONTS):
        d.mkdir(parents=True, exist_ok=True)
    for path, (builder, size) in BUILDERS.items():
        im = builder().convert("RGBA")
        if im.size != size:
            raise SystemExit(f"{path.name} 生成尺寸 {im.size} 与契约 {size} 不一致")
        im.save(path, format="PNG", optimize=False)
        if not quiet:
            print(f"  wrote {path.relative_to(ROOT)} {im.size[0]}x{im.size[1]}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="晨溪农场像素素材生成 / 校验")
    parser.add_argument("--check", action="store_true", help="只校验，不写文件")
    parser.add_argument("--quiet", action="store_true", help="只在失败时输出")
    args = parser.parse_args(argv)
    if args.check:
        return run_check(quiet=args.quiet)
    if not args.quiet:
        print("生成像素素材：")
    build_all(quiet=args.quiet)
    if not args.quiet:
        print("校验：")
    return run_check(quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
