class_name WorldScene
extends Node2D
## 场景基类：瓦片地图、玩家、HUD、阻挡格与刷新；输入分发在 actions.gd。
## 子类只负责地图内容（Farm / Farmhouse）与具体互动。

const Art = preload("res://scripts/world/art.gd")
const PlayerScript = preload("res://scripts/world/player.gd")
const HudScript = preload("res://scripts/ui/hud.gd")
const Actions = preload("res://scripts/world/actions.gd")
const Parity = preload("res://scripts/data/parity.gd")

var map_size := Parity.FARM_SIZE
var ground: TileMapLayer
var soil: TileMapLayer
var crops: TileMapLayer
var object_root: Node2D
var player
var hud
var tint: CanvasModulate
var blocked: Dictionary = {}
var objects: Dictionary = {}
var water_cells: Dictionary = {}
var tile_set: TileSet


func _ready() -> void:
	_build_world()
	_build_actors()
	_build_ui()
	GameState.paused = false
	GameState.changed.connect(_on_changed)
	GameState.day_started.connect(_on_day_started)
	_refresh()


func _process(_delta: float) -> void:
	if player != null and hud != null:
		player.can_move = not hud.is_modal()
	if tint != null:
		tint.color = _tint_color(GameState.minutes)


func _unhandled_input(event: InputEvent) -> void:
	Actions.handle_input(self, event)


# ---------------- 地图构建 ----------------


func _prepare_layers() -> void:
	tile_set = Art.build_tile_set()
	ground = _make_layer(-10)
	soil = _make_layer(-9)
	crops = _make_layer(-8)
	object_root = Node2D.new()
	object_root.y_sort_enabled = true
	add_child(object_root)
	tint = CanvasModulate.new()
	add_child(tint)


func _make_layer(z: int) -> TileMapLayer:
	var layer := TileMapLayer.new()
	layer.tile_set = tile_set
	layer.z_index = z
	layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(layer)
	return layer


func _set_ground(cell: Vector2i, index: int) -> void:
	ground.set_cell(cell, 0, Vector2i(index, 0))


func _set_soil(cell: Vector2i, index: int) -> void:
	soil.set_cell(cell, 0, Vector2i(index, 0))


func _set_crop(cell: Vector2i, index: int) -> void:
	crops.set_cell(cell, 1, Vector2i(index, 0))


func _block_cell(cell: Vector2i) -> void:
	blocked[cell_key(cell)] = true


func _block_rect(rect: Rect2i) -> void:
	for x in range(rect.position.x, rect.position.x + rect.size.x):
		for y in range(rect.position.y, rect.position.y + rect.size.y):
			blocked[cell_key(Vector2i(x, y))] = true


func is_walkable(point: Vector2) -> bool:
	var cell := Vector2i(floori(point.x / 16.0), floori(point.y / 16.0))
	if cell.x < 0 or cell.y < 0 or cell.x >= map_size.x or cell.y >= map_size.y:
		return false
	return not blocked.has(cell_key(cell))


func cell_center(cell: Vector2i) -> Vector2:
	return Vector2(cell.x * 16.0 + 8.0, cell.y * 16.0 + 8.0)


func cell_key(cell: Vector2i) -> String:
	return "%d,%d" % [cell.x, cell.y]


func key_cell(key: String) -> Vector2i:
	var parts := key.split(",")
	return Vector2i(int(parts[0]), int(parts[1]))


# ---------------- 角色 / UI ----------------


func _build_actors() -> void:
	player = PlayerScript.new()
	player.position = cell_center(GameState.spawn_cell)
	player.block_check = Callable(self, "is_walkable")
	object_root.add_child(player)
	player.camera.limit_left = 0
	player.camera.limit_top = 0
	player.camera.limit_right = map_size.x * 16
	player.camera.limit_bottom = map_size.y * 16
	player.camera.limit_smoothed = true
	var zoom := _camera_zoom()
	player.camera.zoom = Vector2(zoom, zoom)


func _camera_zoom() -> float:
	return 1.0


func _build_ui() -> void:
	hud = HudScript.new()
	add_child(hud)


func _add_sprite(cell: Vector2i, atlas_index: int) -> Node2D:
	var node := Node2D.new()
	node.position = cell_center(cell)
	var sprite := Sprite2D.new()
	sprite.texture = Art.atlas_cell(Art.objects_texture(), atlas_index)
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	node.add_child(sprite)
	object_root.add_child(node)
	return node


func _register_object(
	cell: Vector2i, kind: String, hp: int, atlas_index: int, drop_id: String, drop_count: int
) -> void:
	_block_cell(cell)
	var node := _add_sprite(cell, atlas_index)
	objects[cell_key(cell)] = {
		"kind": kind,
		"hp": hp,
		"node": node,
		"drop": drop_id,
		"count": drop_count,
	}


# ---------------- 刷新 / 时间色调 ----------------


func _on_changed() -> void:
	_refresh_field()


func _on_day_started(summary: Dictionary) -> void:
	if hud != null:
		hud.show_day_summary(summary)
	_refresh_field()


func _refresh() -> void:
	_refresh_field()
	if hud != null:
		hud.refresh()


func _refresh_field() -> void:
	if soil == null:
		return
	soil.clear()
	crops.clear()
	for key: String in GameState.plots.keys():
		var cell := key_cell(key)
		var plot: Dictionary = GameState.plots[key]
		_set_soil(cell, 4 if bool(plot["watered"]) else 3)
		if String(plot["crop"]) != "":
			_set_crop(cell, clampi(int(plot["growth"]), 0, 4))


func _tint_color(minutes: int) -> Color:
	var hour := minutes / 60.0
	if hour < 5.0:
		return Color(0.38, 0.42, 0.72)
	if hour < 7.0:
		return Color(0.78, 0.78, 0.95)
	if hour < 17.0:
		return Color(1, 1, 1)
	if hour < 20.0:
		return Color(1.0, 0.86, 0.70)
	if hour < 24.0:
		return Color(0.58, 0.60, 0.88)
	return Color(0.40, 0.44, 0.74)


# ---------------- 子类钩子 ----------------


func _build_world() -> void:
	pass


func _allows_farming() -> bool:
	return false


func _interact_world(_cell: Vector2i) -> bool:
	return false
