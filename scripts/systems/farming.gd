extends RefCounted
## 地块与作物状态机（纯数据，不触碰场景 / 背包 / 能量）。
## plot = {"crop": String, "growth": int, "watered": bool}；plots 的 key 为 "x,y"。

const Crops = preload("res://scripts/data/crops.gd")


static func key(cell: Vector2i) -> String:
	return "%d,%d" % [cell.x, cell.y]


static func plot(plots: Dictionary, cell: Vector2i) -> Dictionary:
	return plots.get(key(cell), {})


static func till(plots: Dictionary, cell: Vector2i) -> bool:
	if plots.has(key(cell)):
		return false
	plots[key(cell)] = {"crop": "", "growth": 0, "watered": false}
	return true


static func water(plots: Dictionary, cell: Vector2i) -> bool:
	var entry: Dictionary = plots.get(key(cell), {})
	if entry.is_empty() or bool(entry["watered"]):
		return false
	entry["watered"] = true
	plots[key(cell)] = entry
	return true


static func plant(plots: Dictionary, cell: Vector2i, crop_id: String) -> bool:
	var entry: Dictionary = plots.get(key(cell), {})
	if entry.is_empty() or String(entry["crop"]) != "":
		return false
	if not Crops.CROPS.has(crop_id):
		return false
	entry["crop"] = crop_id
	entry["growth"] = 0
	plots[key(cell)] = entry
	return true


## 返回收获物品 id；未成熟或空地返回空串。
static func harvest(plots: Dictionary, cell: Vector2i) -> String:
	var entry: Dictionary = plots.get(key(cell), {})
	if entry.is_empty():
		return ""
	var crop_id := String(entry["crop"])
	if crop_id == "" or int(entry["growth"]) < Crops.days_to_grow(crop_id):
		return ""
	entry["crop"] = ""
	entry["growth"] = 0
	entry["watered"] = false
	plots[key(cell)] = entry
	return Crops.harvest_id(crop_id)


## 过夜：只有当天浇过水的作物才成长。浇水状态每天清空。
static func grow_overnight(plots: Dictionary) -> void:
	for entry_key: String in plots.keys():
		var entry: Dictionary = plots[entry_key]
		var crop_id := String(entry["crop"])
		if crop_id != "" and bool(entry["watered"]):
			entry["growth"] = mini(int(entry["growth"]) + 1, Crops.days_to_grow(crop_id))
		entry["watered"] = false
		plots[entry_key] = entry


static func stage(plot_entry: Dictionary) -> int:
	if plot_entry.is_empty():
		return 0
	if String(plot_entry["crop"]) == "":
		return 0
	return clampi(int(plot_entry["growth"]), 0, 4)
