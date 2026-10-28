extends RefCounted
## 存档序列化（纯函数，state 为 GameState 实例）。
## 只接受同版本、结构完整的存档；坏档返回 false，由调用方回退新档。

const Parity = preload("res://scripts/data/parity.gd")
const Inventory = preload("res://scripts/systems/inventory.gd")


static func to_data(state) -> Dictionary:
	return {
		"version": Parity.SAVE_VERSION,
		"day": state.day,
		"season": state.season,
		"year": state.year,
		"minutes": state.minutes,
		"gold": state.gold,
		"energy": state.energy,
		"water": state.water,
		"inventory": state.inventory.to_array(),
		"plots": state.plots.duplicate(true),
		"shipping": state.shipping.duplicate(true),
		"friendship": state.friendship,
		"talked_today": state.talked_today,
		"selected_slot": state.selected_slot,
		"scene": state.current_scene,
		"spawn": [state.spawn_cell.x, state.spawn_cell.y],
	}


static func from_data(state, data: Dictionary) -> bool:
	if int(data.get("version", -1)) != Parity.SAVE_VERSION:
		return false
	if not data.has("day") or not data.has("gold") or not data.has("inventory"):
		return false
	if not data["inventory"] is Array:
		return false
	var restored = Inventory.new(Parity.INVENTORY_SLOTS)
	if not restored.from_array(data["inventory"]):
		return false
	state.inventory = restored
	state.day = maxi(1, int(data["day"]))
	state.season = clampi(int(data.get("season", 0)), 0, 3)
	state.year = maxi(1, int(data.get("year", 1)))
	state.minutes = clampi(int(data.get("minutes", Parity.START_MINUTES)), 0, 1439)
	state.gold = maxi(0, int(data["gold"]))
	state.energy = clampf(float(data.get("energy", Parity.MAX_ENERGY)), 0.0, Parity.MAX_ENERGY)
	state.water = clampi(
		int(data.get("water", Parity.WATER_CAN_CAPACITY)), 0, Parity.WATER_CAN_CAPACITY
	)
	state.plots = data.get("plots", {}).duplicate(true)
	state.shipping = data.get("shipping", {}).duplicate(true)
	state.friendship = maxi(0, int(data.get("friendship", 0)))
	state.talked_today = bool(data.get("talked_today", false))
	state.selected_slot = clampi(int(data.get("selected_slot", 0)), 0, Parity.INVENTORY_SLOTS - 1)
	state.current_scene = String(data.get("scene", "farm"))
	var spawn: Array = data.get("spawn", [15, 12])
	state.spawn_cell = Vector2i(int(spawn[0]), int(spawn[1]))
	return true
