extends RefCounted
## 场景输入与工具/互动动作（从 WorldScene 拆出，控制单文件规模与圈复杂度）。

const Items = preload("res://scripts/data/items.gd")
const Parity = preload("res://scripts/data/parity.gd")


static func handle_input(scene, event: InputEvent) -> void:
	if scene.hud == null:
		return
	if event.is_action_pressed("pause_game"):
		if scene.hud.is_modal() and scene.hud.modal_kind() != "pause":
			scene.hud.close_modal()
		else:
			scene.hud.toggle_pause()
		return
	if scene.hud.is_modal():
		_handle_modal(scene, event)
		return
	if event.is_action_pressed("toggle_help"):
		scene.hud.toggle_help()
	elif event.is_action_pressed("use_tool"):
		use_selected(scene)
	elif event.is_action_pressed("interact"):
		interact(scene)
	else:
		_handle_hotbar(scene, event)


static func _handle_modal(scene, event: InputEvent) -> void:
	if event.is_action_pressed("interact") or event.is_action_pressed("confirm"):
		scene.hud.close_modal()
		return
	var key_event := false
	if event is InputEventKey:
		var key := event as InputEventKey
		key_event = key.pressed and key.physical_keycode == KEY_B
	if key_event and scene.hud.modal_kind() == "dialogue":
		scene.hud.open_shop()


static func _handle_hotbar(scene, event: InputEvent) -> void:
	for i in range(Parity.INVENTORY_SLOTS):
		if event.is_action_pressed("hotbar_%d" % (i + 1)):
			GameState.selected_slot = i
			scene.hud.refresh()
			return


static func use_selected(scene) -> void:
	var slot: Dictionary = GameState.inventory.selected(GameState.selected_slot)
	if slot.is_empty():
		scene.hud.show_message("当前栏位是空的。")
		return
	var id := String(slot["id"])
	var item: Dictionary = Items.get_item(id)
	var cell: Vector2i = scene.player.facing_cell()
	match String(item.get("kind", "")):
		"tool":
			use_tool(scene, String(item.get("tool", "")), cell)
		"seed":
			plant(scene, cell, id)
		_:
			scene.hud.show_message("「%s」不能直接使用。" % Items.display_name(id))
	scene.hud.refresh()


static func use_tool(scene, tool: String, cell: Vector2i) -> void:
	if not scene._allows_farming():
		scene.hud.show_message("屋里不能使用农具。")
		return
	match tool:
		"hoe":
			do_till(scene, cell)
		"watering_can":
			do_water(scene, cell)
		"axe":
			hit_object(scene, cell, "tree", "axe")
		"pickaxe":
			hit_object(scene, cell, "stone", "pickaxe")
		"scythe":
			hit_object(scene, cell, "weed", "scythe")
		_:
			scene.hud.show_message("这个工具暂时用不了。")


static func do_till(scene, cell: Vector2i) -> void:
	if GameState.till(cell):
		scene.hud.show_message("翻好了一块地，可以播种了。")
	else:
		scene.hud.show_message("这里不能开垦。")


static func do_water(scene, cell: Vector2i) -> void:
	if scene.water_cells.has(scene.cell_key(cell)):
		if GameState.refill_can():
			scene.hud.show_message("浇水壶补满了。")
		else:
			scene.hud.show_message("浇水壶已经是满的。")
		return
	if GameState.water_plot(cell):
		scene.hud.show_message("浇水完成。")
	else:
		scene.hud.show_message("这里没有可以浇水的耕地。")


static func plant(scene, cell: Vector2i, seed_id: String) -> void:
	if GameState.plant(cell, seed_id):
		scene.hud.show_message("种下了种子。")
	else:
		scene.hud.show_message("需要一块已开垦的空地，且背包里有种子。")


static func hit_object(scene, cell: Vector2i, kind: String, tool: String) -> void:
	var key: String = scene.cell_key(cell)
	var entry: Dictionary = scene.objects.get(key, {})
	if entry.is_empty() or String(entry["kind"]) != kind:
		scene.hud.show_message("这里没有可以采集的东西。")
		return
	if not GameState.spend_energy(float(Parity.TOOL_ENERGY.get(tool, 2.0))):
		return
	entry["hp"] = int(entry["hp"]) - 1
	if int(entry["hp"]) > 0:
		scene.objects[key] = entry
		scene.hud.show_message("还需要再敲 %d 下。" % int(entry["hp"]))
		return
	_clear_object(scene, key, entry)


static func _clear_object(scene, key: String, entry: Dictionary) -> void:
	var node: Node2D = entry["node"]
	if is_instance_valid(node):
		node.queue_free()
	scene.objects.erase(key)
	scene.blocked.erase(key)
	var drop := String(entry["drop"])
	var count := int(entry["count"])
	GameState.add_item(drop, count)
	scene.hud.show_message("收集到 %s x%d。" % [Items.display_name(drop), count])


static func interact(scene) -> void:
	var cell: Vector2i = scene.player.facing_cell()
	if scene._interact_world(cell):
		return
	scene.hud.show_message("这里没有可以互动的东西。")
