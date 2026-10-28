extends Node
## 场景冒烟测试（作为主场景运行）：实例化农场与农舍，校验玩家/HUD/地图/阻挡格。
## 运行：godot --headless --path . res://tests/scene_smoke.tscn

var failures := 0


func _ready() -> void:
	var farm = load("res://scenes/main.tscn").instantiate()
	add_child(farm)
	_check(farm.player != null, "farm spawns a player")
	_check(farm.hud != null, "farm spawns the HUD")
	_check(farm.hud.slot_panels.size() == 12, "HUD has 12 hotbar slots")
	_check(farm.ground.get_used_cells().size() > 4000, "farm ground is populated")
	_check(farm.villager != null, "farm has the villager")
	_check(farm.objects.size() > 20, "farm has gatherables")
	_check(farm.blocked.size() > 100, "farm has collision cells")
	_check(farm.is_walkable(Vector2(15 * 16 + 8, 12 * 16 + 8)), "spawn tile is walkable")
	_check(not farm.is_walkable(Vector2(15 * 16 + 8, 9 * 16 + 8)), "farmhouse door tile is blocked")
	farm.queue_free()
	var house = load("res://scenes/farmhouse.tscn").instantiate()
	add_child(house)
	_check(house.player != null, "farmhouse spawns a player")
	_check(house.hud != null, "farmhouse spawns the HUD")
	_check(house.map_size == Vector2i(10, 7), "farmhouse map size is 14x10")
	_check(house.blocked.size() > 30, "farmhouse has walls")
	_check(not house.is_walkable(Vector2(5 * 16 + 8, 6 * 16 + 8)), "farmhouse exit door is blocked")
	get_tree().quit(1 if failures > 0 else 0)


func _check(condition: bool, label: String) -> void:
	if condition:
		print("PASS: ", label)
	else:
		failures += 1
		print("FAIL: ", label)
