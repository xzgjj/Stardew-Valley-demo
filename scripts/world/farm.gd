extends WorldScene
## 第一个主场景：标准农场（80x65）。农舍、出货箱、池塘、温室残骸、森林边界与可采集物。

const VillagerScript = preload("res://scripts/world/villager.gd")

const HOUSE_RECT := Rect2i(12, 6, 7, 4)
const DOOR_CELL := Vector2i(15, 9)
const BIN_CELL := Vector2i(20, 8)
const MAILBOX_CELL := Vector2i(19, 11)
const GREENHOUSE_RECT := Rect2i(54, 5, 12, 10)
const VILLAGER_CELL := Vector2i(22, 12)
const SCATTER_SEED := 20261028

var villager
var path_cells: Dictionary = {}


func _build_world() -> void:
	_prepare_layers()
	_fill_grass()
	_build_paths()
	_build_pond()
	_build_house_exterior()
	_build_greenhouse()
	_build_borders()
	_scatter_objects()
	_build_fixtures()
	_build_villager()


func _allows_farming() -> bool:
	return true


func _fill_grass() -> void:
	for x in range(map_size.x):
		for y in range(map_size.y):
			var index := 0 if (x * 7 + y * 13) % 5 != 0 else 1
			_set_ground(Vector2i(x, y), index)


func _build_paths() -> void:
	for y in range(10, map_size.y):
		_mark_path(Vector2i(15, y))
	for x in range(15, 24):
		_mark_path(Vector2i(x, 12))
	for y in range(6, 13):
		_mark_path(Vector2i(19, y))


func _mark_path(cell: Vector2i) -> void:
	path_cells[cell_key(cell)] = true
	_set_ground(cell, 2)


func _build_pond() -> void:
	for x in range(4, 26):
		for y in range(40, 60):
			var dx := (x - 14) / 10.0
			var dy := (y - 50) / 6.0
			if dx * dx + dy * dy <= 1.0:
				water_cells[cell_key(Vector2i(x, y))] = true
				_block_cell(Vector2i(x, y))
				_set_ground(Vector2i(x, y), 5)


func _build_house_exterior() -> void:
	_block_rect(HOUSE_RECT)
	var base := Vector2(
		HOUSE_RECT.position.x * 16.0, (HOUSE_RECT.position.y + HOUSE_RECT.size.y) * 16.0
	)
	var node := Node2D.new()
	node.position = base
	var sprite := Sprite2D.new()
	sprite.texture = Art.house_texture()
	sprite.centered = false
	sprite.position = Vector2(0, -64)
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	node.add_child(sprite)
	object_root.add_child(node)


func _build_greenhouse() -> void:
	_block_rect(GREENHOUSE_RECT)
	for x in range(GREENHOUSE_RECT.position.x, GREENHOUSE_RECT.position.x + GREENHOUSE_RECT.size.x):
		for y in range(
			GREENHOUSE_RECT.position.y, GREENHOUSE_RECT.position.y + GREENHOUSE_RECT.size.y
		):
			_add_sprite(Vector2i(x, y), 5)


func _build_borders() -> void:
	for x in range(map_size.x):
		for y in range(2):
			_block_cell(Vector2i(x, y))
			_block_cell(Vector2i(x, map_size.y - 1 - y))
	for y in range(map_size.y):
		for x in range(2):
			_block_cell(Vector2i(x, y))
			_block_cell(Vector2i(map_size.x - 1 - x, y))
	for x in range(2, map_size.x - 2, 2):
		_add_sprite(Vector2i(x, 2), 0)
		_add_sprite(Vector2i(x, map_size.y - 3), 0)
	for y in range(2, map_size.y - 2, 2):
		_add_sprite(Vector2i(2, y), 0)
		_add_sprite(Vector2i(map_size.x - 3, y), 0)


func _scatter_objects() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = SCATTER_SEED
	var placed := 0
	var attempts := 0
	while placed < 70 and attempts < 400:
		attempts += 1
		var cell := Vector2i(rng.randi_range(4, map_size.x - 5), rng.randi_range(4, map_size.y - 5))
		var key := cell_key(cell)
		if blocked.has(key) or path_cells.has(key) or water_cells.has(key):
			continue
		if _near_start(cell):
			continue
		var roll := rng.randf()
		if roll < 0.45:
			_register_object(cell, "tree", 3, 0, "wood", 3)
		elif roll < 0.8:
			_register_object(cell, "stone", 3, 1, "stone", 2)
		else:
			_register_object(cell, "weed", 1, 2, "fiber", 1)
		placed += 1


func _near_start(cell: Vector2i) -> bool:
	if absi(cell.x - 15) <= 3 and cell.y >= 6 and cell.y <= 16:
		return true
	return false


func _build_fixtures() -> void:
	_register_object(BIN_CELL, "bin", 1, 3, "wood", 0)
	_block_cell(MAILBOX_CELL)
	_add_sprite(MAILBOX_CELL, 4)


func _build_villager() -> void:
	villager = VillagerScript.new()
	villager.position = cell_center(VILLAGER_CELL)
	_block_cell(VILLAGER_CELL)
	object_root.add_child(villager)


func _interact_world(cell: Vector2i) -> bool:
	if villager != null and player.global_position.distance_to(villager.global_position) <= 32.0:
		hud.show_dialogue("林婶", villager.talk_line(), true)
		GameState.talk()
		return true
	if cell == DOOR_CELL:
		GameState.change_scene("house")
		return true
	if cell == BIN_CELL:
		GameState.ship_selected()
		return true
	if cell == MAILBOX_CELL:
		hud.show_message("邮箱里只有一封镇长的欢迎信：先种下 15 粒防风草种子吧。")
		return true
	return false
