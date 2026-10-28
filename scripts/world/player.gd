class_name Player
extends CharacterBody2D
## 玩家：四方向行走 + 逐帧动画。碰撞采用瓦片网格阻挡检查（block_check 回调）。

const Art = preload("res://scripts/world/art.gd")

const SPEED := 84.0
const HALF := Vector2(5, 4)

var facing := Vector2i.DOWN
var block_check: Callable = Callable()
var can_move := true
var sprite: Sprite2D
var camera: Camera2D
var walk_time := 0.0


func _ready() -> void:
	sprite = Sprite2D.new()
	sprite.texture = Art.character_texture(false)
	sprite.hframes = 4
	sprite.vframes = 4
	sprite.frame = 1
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(sprite)
	camera = Camera2D.new()
	camera.position = Vector2.ZERO
	add_child(camera)


func _physics_process(delta: float) -> void:
	if not can_move:
		walk_time = 0.0
		_update_frame()
		return
	var input := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if input.length() < 0.1:
		walk_time = 0.0
		_update_frame()
		return
	_set_facing(input)
	walk_time += delta
	var target := global_position + input.normalized() * SPEED * delta
	_move_toward(target)
	_update_frame()


func facing_cell() -> Vector2i:
	return Vector2i(floori(global_position.x / 16.0), floori(global_position.y / 16.0)) + facing


func _move_toward(target: Vector2) -> void:
	if _can_walk(target):
		global_position = target
		return
	var axis_x := Vector2(target.x, global_position.y)
	if _can_walk(axis_x):
		global_position = axis_x
	var axis_y := Vector2(global_position.x, target.y)
	if _can_walk(axis_y):
		global_position = axis_y


func _can_walk(point: Vector2) -> bool:
	if not block_check.is_valid():
		return true
	return (
		bool(block_check.call(point + Vector2(-HALF.x, -HALF.y)))
		and bool(block_check.call(point + Vector2(HALF.x, -HALF.y)))
		and bool(block_check.call(point + Vector2(-HALF.x, HALF.y)))
		and bool(block_check.call(point + Vector2(HALF.x, HALF.y)))
	)


func _set_facing(input: Vector2) -> void:
	if absf(input.x) > absf(input.y):
		facing = Vector2i.RIGHT if input.x > 0.0 else Vector2i.LEFT
	else:
		facing = Vector2i.DOWN if input.y > 0.0 else Vector2i.UP


func _update_frame() -> void:
	var row := 0
	if facing == Vector2i.LEFT:
		row = 1
	elif facing == Vector2i.RIGHT:
		row = 2
	elif facing == Vector2i.UP:
		row = 3
	var column := 1
	if walk_time > 0.0:
		column = int(walk_time * 8.0) % 4
	sprite.frame = row * 4 + column
