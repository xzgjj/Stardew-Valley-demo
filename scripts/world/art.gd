extends RefCounted
## 美术资源加载与程序化兜底（placeholders）。
## 资源存在且尺寸符合契约时直接用；否则生成同规格贴图，保证无素材也能跑通。

const TILE := 16
const TERRAIN_COLUMNS := 8
const CROP_COLUMNS := 5
const OBJECT_COLUMNS := 8
const ICON_COLUMNS := 10

const TERRAIN_PATH := "res://assets/tilesets/terrain.png"
const CROPS_PATH := "res://assets/tilesets/crops.png"
const OBJECTS_PATH := "res://assets/tilesets/objects.png"
const PLAYER_PATH := "res://assets/characters/player.png"
const VILLAGER_PATH := "res://assets/characters/villager.png"
const HOUSE_PATH := "res://assets/props/farmhouse.png"
const PANEL_PATH := "res://assets/ui/panel.png"
const ICONS_PATH := "res://assets/ui/icons.png"
const FONT_PATH := "res://assets/fonts/pixel.ttf"

const TERRAIN_COLORS := [
	Color("5a9e4b"),
	Color("4f8f45"),
	Color("b08a5a"),
	Color("8b5a2b"),
	Color("5a3a1f"),
	Color("3a6ea5"),
	Color("8a8a8a"),
	Color("a8794a"),
]


static func load_texture(path: String) -> Texture2D:
	if not ResourceLoader.exists(path):
		return null
	var res: Variant = load(path)
	return res if res is Texture2D else null


static func terrain_texture() -> Texture2D:
	var tex := load_texture(TERRAIN_PATH)
	if tex != null and tex.get_width() >= TERRAIN_COLUMNS * TILE and tex.get_height() >= TILE:
		return tex
	return ImageTexture.create_from_image(_strip_image(TERRAIN_COLORS, 1))


static func crops_texture() -> Texture2D:
	var tex := load_texture(CROPS_PATH)
	if tex != null and tex.get_width() >= CROP_COLUMNS * TILE and tex.get_height() >= TILE:
		return tex
	return ImageTexture.create_from_image(_crops_image())


static func objects_texture() -> Texture2D:
	var tex := load_texture(OBJECTS_PATH)
	if tex != null and tex.get_width() >= OBJECT_COLUMNS * TILE and tex.get_height() >= TILE:
		return tex
	return ImageTexture.create_from_image(_objects_image())


static func character_texture(is_villager: bool = false) -> Texture2D:
	var path := VILLAGER_PATH if is_villager else PLAYER_PATH
	var tex := load_texture(path)
	if tex != null and tex.get_width() == 64 and tex.get_height() == 64:
		return tex
	var body := Color("d9a066") if not is_villager else Color("b06a4a")
	var hair := Color("5a3a1f") if not is_villager else Color("8a8a8a")
	return ImageTexture.create_from_image(_character_image(body, hair))


static func house_texture() -> Texture2D:
	var tex := load_texture(HOUSE_PATH)
	if tex != null and tex.get_width() == 112 and tex.get_height() == 64:
		return tex
	return ImageTexture.create_from_image(_house_image())


static func panel_texture() -> Texture2D:
	return load_texture(PANEL_PATH)


static func font() -> Font:
	for path: String in ["res://assets/fonts/pixel.ttf", "res://assets/fonts/pixel.woff2"]:
		if ResourceLoader.exists(path):
			var res: Variant = load(path)
			if res is Font:
				return res
	var system := SystemFont.new()
	system.font_names = PackedStringArray(
		["Microsoft YaHei", "Noto Sans CJK SC", "SimHei", "PingFang SC", "Arial"]
	)
	return system


## 图集裁剪出单个 16x16 贴图（objects / icons）。
static func atlas_cell(texture: Texture2D, index: int) -> Texture2D:
	var region := Rect2(index * TILE, 0, TILE, TILE)
	return AtlasTexture.new() if texture == null else _make_atlas(texture, region)


static func _make_atlas(texture: Texture2D, region: Rect2) -> AtlasTexture:
	var atlas := AtlasTexture.new()
	atlas.atlas = texture
	atlas.region = region
	return atlas


static func icon_texture(index: int) -> Texture2D:
	var tex := load_texture(ICONS_PATH)
	if tex != null and tex.get_width() >= ICON_COLUMNS * TILE and tex.get_height() >= TILE:
		return _make_atlas(tex, Rect2(index * TILE, 0, TILE, TILE))
	return ImageTexture.create_from_image(_icon_image(index))


static func build_tile_set() -> TileSet:
	var terrain := terrain_texture()
	var crops := crops_texture()
	var tile_set := TileSet.new()
	tile_set.tile_size = Vector2i(TILE, TILE)
	_add_atlas(tile_set, terrain, TERRAIN_COLUMNS, 0)
	_add_atlas(tile_set, crops, CROP_COLUMNS, 1)
	return tile_set


static func _add_atlas(tile_set: TileSet, texture: Texture2D, columns: int, source_id: int) -> void:
	var source := TileSetAtlasSource.new()
	source.texture = texture
	source.texture_region_size = Vector2i(TILE, TILE)
	for i in range(columns):
		source.create_tile(Vector2i(i, 0))
	tile_set.add_source(source, source_id)


# ---------------- 程序化兜底贴图 ----------------


static func _strip_image(colors: Array, rows: int = 1) -> Image:
	var image := Image.create(colors.size() * TILE, rows * TILE, false, Image.FORMAT_RGBA8)
	for i in range(colors.size()):
		_fill_tile(image, Vector2i(i, 0), colors[i])
	return image


static func _fill_tile(image: Image, cell: Vector2i, color: Color, noise: bool = true) -> void:
	var origin := cell * TILE
	image.fill_rect(Rect2i(origin.x, origin.y, TILE, TILE), color)
	if not noise:
		return
	for y in range(TILE):
		for x in range(TILE):
			if (x * 31 + y * 17 + cell.x * 13) % 23 == 0:
				image.set_pixel(origin.x + x, origin.y + y, color.darkened(0.08))


static func _crops_image() -> Image:
	var image := Image.create(CROP_COLUMNS * TILE, TILE, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	for stage in range(CROP_COLUMNS):
		var ox := stage * TILE
		var height := 4 + stage * 2
		for y in range(height):
			var py := TILE - 2 - y
			image.set_pixel(ox + 8, py, Color("4f8f45"))
			if stage >= 2:
				image.set_pixel(ox + 6, py, Color("6ab04c"))
				image.set_pixel(ox + 10, py, Color("6ab04c"))
		if stage >= 3:
			image.fill_rect(Rect2i(ox + 5, TILE - 6, 7, 3), Color("d9f0c0"))
		if stage == 4:
			image.fill_rect(Rect2i(ox + 4, TILE - 5, 9, 4), Color("f0e6c8"))
	return image


static func _objects_image() -> Image:
	var image := Image.create(OBJECT_COLUMNS * TILE, TILE, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	# 0 树
	image.fill_rect(Rect2i(6, 12, 4, 4), Color("6b4a2a"))
	image.fill_rect(Rect2i(3, 2, 10, 10), Color("2f6b32"))
	image.fill_rect(Rect2i(5, 4, 6, 6), Color("3f8f3f"))
	# 1 石头
	image.fill_rect(Rect2i(3, 8, 10, 8), Color("8a8a8a"))
	image.fill_rect(Rect2i(5, 6, 6, 4), Color("9a9a9a"))
	# 2 杂草
	for i in range(4):
		image.fill_rect(Rect2i(3 + i * 3, 10 - i, 1, 6), Color("4f8f45"))
	# 3 出货箱
	image.fill_rect(Rect2i(2, 4, 12, 10), Color("8a5a2a"))
	image.fill_rect(Rect2i(2, 4, 12, 3), Color("b07a3a"))
	# 4 邮箱
	image.fill_rect(Rect2i(6, 8, 3, 8), Color("6b4a2a"))
	image.fill_rect(Rect2i(4, 3, 8, 5), Color("c0392b"))
	# 5 温室残骸
	image.fill_rect(Rect2i(2, 2, 12, 12), Color(0.55, 0.75, 0.85, 0.55))
	image.fill_rect(Rect2i(2, 2, 12, 1), Color("9aa7ad"))
	image.fill_rect(Rect2i(2, 13, 12, 1), Color("9aa7ad"))
	# 6 木箱
	image.fill_rect(Rect2i(3, 5, 10, 10), Color("7a5230"))
	image.fill_rect(Rect2i(3, 5, 10, 2), Color("9a6a3a"))
	# 7 备用（路牌）
	image.fill_rect(Rect2i(7, 6, 2, 9), Color("6b4a2a"))
	image.fill_rect(Rect2i(3, 3, 10, 4), Color("d9b06a"))
	return image


static func _character_image(body: Color, hair: Color) -> Image:
	var image := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	for row in range(4):
		for col in range(4):
			var ox := col * TILE
			var oy := row * TILE
			var bob := 1 if col == 1 or col == 3 else 0
			# 腿
			image.fill_rect(Rect2i(ox + 5, oy + 12 + bob, 2, 3), Color("3a3a5a"))
			image.fill_rect(Rect2i(ox + 9, oy + 12 - bob, 2, 3), Color("3a3a5a"))
			# 身体
			image.fill_rect(Rect2i(ox + 4, oy + 8, 8, 5), body)
			# 头
			image.fill_rect(Rect2i(ox + 4, oy + 2, 8, 7), Color("f0c8a0"))
			# 头发
			image.fill_rect(Rect2i(ox + 4, oy + 1, 8, 2), hair)
			if row != 3:
				image.fill_rect(Rect2i(ox + 4, oy + 2, 1, 4), hair)
				image.fill_rect(Rect2i(ox + 11, oy + 2, 1, 4), hair)
			# 眼睛（背面朝上时不画）
			if row == 0:
				image.set_pixel(ox + 6, oy + 5, Color("2a2a3a"))
				image.set_pixel(ox + 9, oy + 5, Color("2a2a3a"))
			elif row == 1:
				image.set_pixel(ox + 5, oy + 5, Color("2a2a3a"))
			elif row == 2:
				image.set_pixel(ox + 10, oy + 5, Color("2a2a3a"))
	return image


static func _house_image() -> Image:
	var image := Image.create(112, 64, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	# 墙体
	image.fill_rect(Rect2i(8, 28, 96, 32), Color("c8a06a"))
	image.fill_rect(Rect2i(8, 28, 96, 4), Color("8a6a4a"))
	# 屋顶
	for i in range(20):
		var width := 112 - i * 4
		image.fill_rect(Rect2i(i * 2, 28 - i, width, 3), Color("8b3a2b"))
	# 门
	image.fill_rect(Rect2i(48, 40, 16, 20), Color("6b4a2a"))
	image.fill_rect(Rect2i(50, 42, 12, 16), Color("4a3020"))
	# 窗
	image.fill_rect(Rect2i(20, 34, 14, 12), Color("a8d8e8"))
	image.fill_rect(Rect2i(78, 34, 14, 12), Color("a8d8e8"))
	image.fill_rect(Rect2i(26, 34, 1, 12), Color("5a6a7a"))
	image.fill_rect(Rect2i(20, 39, 14, 1), Color("5a6a7a"))
	return image


static func _icon_image(index: int) -> Image:
	var image := Image.create(TILE, TILE, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	var colors := [
		Color("8a6a4a"),
		Color("4a90c8"),
		Color("9a9a9a"),
		Color("7a7a7a"),
		Color("b0b0b0"),
		Color("6ab04c"),
		Color("f0e6c8"),
		Color("a8794a"),
		Color("8a8a8a"),
		Color("d9c27a"),
	]
	image.fill_rect(Rect2i(3, 3, 10, 10), colors[posmod(index, colors.size())])
	image.fill_rect(Rect2i(4, 4, 8, 2), Color(1, 1, 1, 0.25))
	return image
