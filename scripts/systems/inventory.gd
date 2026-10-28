extends RefCounted
## 12 格工具栏背包：工具不可堆叠，物品按 999 堆叠。
## 纯数据对象，不依赖场景树，便于无头测试。

const Items = preload("res://scripts/data/items.gd")

var size: int = 12
var slots: Array = []


func _init(slot_count: int = 12) -> void:
	size = slot_count
	slots.clear()
	for _i in range(size):
		slots.append({})


## 初始装备：5 件工具 + 15 粒防风草种子（与星露谷新档一致）。
func setup_starting() -> void:
	slots.clear()
	for _i in range(size):
		slots.append({})
	var tools := ["hoe", "watering_can", "axe", "pickaxe", "scythe"]
	for i in range(tools.size()):
		slots[i] = {"id": tools[i], "count": 1}
	add("parsnip_seed", 15)


## 返回未能放入的数量（0 表示全部放入）。
func add(id: String, count: int) -> int:
	if not Items.exists(id) or count <= 0:
		return count
	var stack_max := _stack_max(id)
	return _fill_empty(id, _merge_existing(id, count, stack_max), stack_max)


func can_add(id: String, count: int) -> bool:
	if count <= 0:
		return true
	if not Items.exists(id):
		return false
	var stack_max := _stack_max(id)
	var left := count
	for i in range(size):
		var slot: Dictionary = slots[i]
		if slot.get("id", "") == id:
			left -= maxi(0, stack_max - int(slot["count"]))
	for i in range(size):
		if slots[i].is_empty():
			left -= stack_max
	return left <= 0


func remove(id: String, count: int) -> bool:
	if count <= 0 or count(id) < count:
		return false
	var left := count
	for i in range(size):
		if left <= 0:
			break
		var slot: Dictionary = slots[i]
		if slot.get("id", "") != id:
			continue
		var taken: int = mini(int(slot["count"]), left)
		slot["count"] = int(slot["count"]) - taken
		left -= taken
		slots[i] = {} if int(slot["count"]) <= 0 else slot
	return true


func count(id: String) -> int:
	var total := 0
	for i in range(size):
		var slot: Dictionary = slots[i]
		if slot.get("id", "") == id:
			total += int(slot["count"])
	return total


func is_empty() -> bool:
	for i in range(size):
		if not slots[i].is_empty():
			return false
	return true


func has_free_slot() -> bool:
	return first_empty() >= 0


func first_empty() -> int:
	for i in range(size):
		if slots[i].is_empty():
			return i
	return -1


## 选中格：索引始终合法（0..size-1）。
func selected(selected_index: int) -> Dictionary:
	if selected_index < 0 or selected_index >= size:
		return {}
	return slots[selected_index]


func swap(a: int, b: int) -> void:
	if a < 0 or b < 0 or a >= size or b >= size or a == b:
		return
	var tmp: Dictionary = slots[a]
	slots[a] = slots[b]
	slots[b] = tmp


func to_array() -> Array:
	return slots.duplicate(true)


func from_array(data: Array) -> bool:
	if data.size() != size:
		return false
	var restored: Array = []
	for i in range(size):
		var entry: Variant = data[i]
		if entry == null or not entry is Dictionary:
			restored.append({})
			continue
		var id := String(entry.get("id", ""))
		var amount := int(entry.get("count", 0))
		if id == "" or amount <= 0:
			restored.append({})
			continue
		restored.append({"id": id, "count": amount})
	slots = restored
	return true


func _stack_max(id: String) -> int:
	return 1 if Items.is_tool_item(id) else 999


func _merge_existing(id: String, count: int, stack_max: int) -> int:
	var left := count
	for i in range(size):
		if left <= 0:
			break
		var slot: Dictionary = slots[i]
		if slot.get("id", "") != id:
			continue
		var room: int = stack_max - int(slot["count"])
		if room <= 0:
			continue
		var moved: int = mini(room, left)
		slot["count"] = int(slot["count"]) + moved
		slots[i] = slot
		left -= moved
	return left


func _fill_empty(id: String, left: int, stack_max: int) -> int:
	for i in range(size):
		if left <= 0:
			break
		if not slots[i].is_empty():
			continue
		var moved: int = mini(stack_max, left)
		slots[i] = {"id": id, "count": moved}
		left -= moved
	return left
