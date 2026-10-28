extends WorldScene
## 农舍内部：木地板房间、床（睡觉推进到第二天）、出口门回农场。

const ROOM_SIZE := Vector2i(10, 7)
const DOOR_CELL := Vector2i(5, 6)
const BED_CELLS := [Vector2i(2, 2), Vector2i(3, 2), Vector2i(2, 3), Vector2i(3, 3)]
const SPAWN_CELL := Vector2i(5, 5)


func _build_world() -> void:
	map_size = ROOM_SIZE
	_prepare_layers()
	var background := ColorRect.new()
	background.color = Color("1a120c")
	background.position = Vector2(-80, -80)
	background.size = Vector2(map_size.x * 16.0 + 160.0, map_size.y * 16.0 + 160.0)
	background.z_index = -20
	add_child(background)
	for x in range(map_size.x):
		for y in range(map_size.y):
			_set_ground(Vector2i(x, y), 7)
	_build_walls()
	_build_bed()
	_build_door()


func _build_walls() -> void:
	for x in range(map_size.x):
		for y in range(map_size.y):
			if x == 0 or y == 0 or x == map_size.x - 1 or y == map_size.y - 1:
				_block_cell(Vector2i(x, y))
				_set_ground(Vector2i(x, y), 6)


func _camera_zoom() -> float:
	return 2.0


func _build_bed() -> void:
	for cell in BED_CELLS:
		_block_cell(cell)
	var node := Node2D.new()
	node.position = Vector2(2 * 16.0, 2 * 16.0)
	var frame := ColorRect.new()
	frame.color = Color("6b4a2a")
	frame.size = Vector2(32, 32)
	node.add_child(frame)
	var sheet := ColorRect.new()
	sheet.color = Color("d94a4a")
	sheet.position = Vector2(2, 2)
	sheet.size = Vector2(28, 20)
	node.add_child(sheet)
	var pillow := ColorRect.new()
	pillow.color = Color("f4f4f4")
	pillow.position = Vector2(4, 3)
	pillow.size = Vector2(24, 6)
	node.add_child(pillow)
	object_root.add_child(node)


func _build_door() -> void:
	_block_cell(DOOR_CELL)
	var node := Node2D.new()
	node.position = Vector2(DOOR_CELL.x * 16.0, DOOR_CELL.y * 16.0)
	var door := ColorRect.new()
	door.color = Color("8b5a2b")
	door.size = Vector2(16, 16)
	node.add_child(door)
	object_root.add_child(node)


func _interact_world(cell: Vector2i) -> bool:
	if cell == DOOR_CELL:
		GameState.change_scene("farm")
		return true
	for bed_cell in BED_CELLS:
		if cell == bed_cell:
			GameState.sleep()
			return true
	return false
