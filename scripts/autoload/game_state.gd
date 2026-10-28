extends Node
## 全局游戏状态（autoload GameState）。
## 纯逻辑：不依赖场景，测试里可直接 GameStateScript.new() 后调用 new_game()。
## 时间、耕作、背包、出货、社交、存档都从这里走；HUD 直接读字段。

signal changed
signal message(text: String)
signal day_started(summary: Dictionary)

const Inventory = preload("res://scripts/systems/inventory.gd")
const Farming = preload("res://scripts/systems/farming.gd")
const SaveSystem = preload("res://scripts/systems/save_system.gd")
const Items = preload("res://scripts/data/items.gd")
const Crops = preload("res://scripts/data/crops.gd")
const Parity = preload("res://scripts/data/parity.gd")

const SAVE_PATH := "user://savegame.json"
const FARM_SCENE := "res://scenes/main.tscn"
const HOUSE_SCENE := "res://scenes/farmhouse.tscn"

var save_path: String = SAVE_PATH
var day: int = 1
var season: int = 0
var year: int = 1
var minutes: int = Parity.START_MINUTES
var gold: int = Parity.START_GOLD
var energy: float = Parity.MAX_ENERGY
var water: int = Parity.WATER_CAN_CAPACITY
var inventory
var plots: Dictionary = {}
var shipping: Dictionary = {}
var friendship: int = 0
var talked_today: bool = false
var selected_slot: int = 0
var paused: bool = false
var play_seconds: float = 0.0
var current_scene: String = "farm"
var spawn_cell: Vector2i = Vector2i(15, 12)
var last_summary: Dictionary = {}
var initialized: bool = false


func _ready() -> void:
	inventory = Inventory.new(Parity.INVENTORY_SLOTS)
	if not load_game():
		new_game()
	initialized = true


func _process(delta: float) -> void:
	if not initialized or paused:
		return
	play_seconds += delta
	while play_seconds >= Parity.TICK_SECONDS:
		play_seconds -= Parity.TICK_SECONDS
		minutes += Parity.TICK_MINUTES
		changed.emit()
		if minutes >= Parity.DAY_END_MINUTES:
			pass_out()
			break


func new_game() -> void:
	day = 1
	season = 0
	year = 1
	minutes = Parity.START_MINUTES
	gold = Parity.START_GOLD
	energy = Parity.MAX_ENERGY
	water = Parity.WATER_CAN_CAPACITY
	inventory = Inventory.new(Parity.INVENTORY_SLOTS)
	inventory.setup_starting()
	plots = {}
	shipping = {}
	friendship = 0
	talked_today = false
	selected_slot = 0
	play_seconds = 0.0
	current_scene = "farm"
	spawn_cell = Vector2i(15, 12)
	changed.emit()


func spend_energy(cost: float) -> bool:
	if cost <= 0.0:
		return true
	if energy < cost:
		message.emit("太累了，回农舍睡一觉吧。")
		return false
	energy -= cost
	changed.emit()
	return true


# ---------------- 耕地 / 作物 ----------------


func till(cell: Vector2i) -> bool:
	if not spend_energy(float(Parity.TOOL_ENERGY["hoe"])):
		return false
	if not Farming.till(plots, cell):
		energy += float(Parity.TOOL_ENERGY["hoe"])
		return false
	changed.emit()
	return true


func water_plot(cell: Vector2i) -> bool:
	if water <= 0:
		message.emit("浇水壶里没水了，去池塘边补满。")
		return false
	if not spend_energy(float(Parity.TOOL_ENERGY["watering_can"])):
		return false
	if not Farming.water(plots, cell):
		energy += float(Parity.TOOL_ENERGY["watering_can"])
		return false
	water -= 1
	changed.emit()
	return true


func refill_can() -> bool:
	if water >= Parity.WATER_CAN_CAPACITY:
		return false
	water = Parity.WATER_CAN_CAPACITY
	changed.emit()
	return true


func plant(cell: Vector2i, seed_id: String) -> bool:
	var item: Dictionary = Items.get_item(seed_id)
	var crop_id := String(item.get("crop", ""))
	if crop_id == "" or not Crops.can_plant_in(crop_id, season):
		return false
	if inventory.count(seed_id) <= 0:
		message.emit("没有可播种的种子。")
		return false
	if not Farming.plant(plots, cell, crop_id):
		return false
	inventory.remove(seed_id, 1)
	changed.emit()
	return true


func harvest(cell: Vector2i) -> bool:
	var plot: Dictionary = Farming.plot(plots, cell)
	var crop_id := String(plot.get("crop", ""))
	if crop_id == "" or int(plot.get("growth", 0)) < Crops.days_to_grow(crop_id):
		return false
	var harvest_id := Crops.harvest_id(crop_id)
	if not inventory.can_add(harvest_id, 1):
		message.emit("背包满了，无法收获。")
		return false
	if Farming.harvest(plots, cell) == "":
		return false
	inventory.add(harvest_id, 1)
	changed.emit()
	return true


# ---------------- 背包 / 经济 / 社交 ----------------


func add_item(id: String, count: int) -> bool:
	if inventory.add(id, count) != 0:
		message.emit("背包满了。")
		return false
	changed.emit()
	return true


func ship_selected() -> bool:
	var slot: Dictionary = inventory.selected(selected_slot)
	if slot.is_empty() or Items.is_tool_item(String(slot["id"])):
		message.emit("只能把作物或材料放进出货箱。")
		return false
	var id := String(slot["id"])
	var amount := int(slot["count"])
	shipping[id] = int(shipping.get(id, 0)) + amount
	inventory.remove(id, amount)
	changed.emit()
	message.emit("%s x%d 已放进出货箱，明早结算。" % [Items.display_name(id), amount])
	return true


func buy(id: String, price: int) -> bool:
	if gold < price:
		message.emit("金币不够。")
		return false
	if not Items.exists(id):
		return false
	if inventory.add(id, 1) != 0:
		message.emit("背包满了。")
		return false
	gold -= price
	changed.emit()
	return true


func talk() -> bool:
	if talked_today:
		return false
	talked_today = true
	friendship = mini(Parity.FRIENDSHIP_MAX, friendship + Parity.FRIENDSHIP_TALK)
	changed.emit()
	return true


# ---------------- 日推进 / 睡觉 / 昏倒 ----------------


func advance_day(slept: bool, energy_after: float = -1.0) -> void:
	var income: int = 0
	for id: String in shipping.keys():
		income += Items.sell_price(id) * int(shipping[id])
	gold += income
	shipping = {}
	Farming.grow_overnight(plots)
	var season_changed := false
	day += 1
	if day > Parity.SEASON_DAYS:
		day = 1
		season += 1
		season_changed = true
		if season >= 4:
			season = 0
			year += 1
		plots = {}
	minutes = Parity.START_MINUTES
	water = Parity.WATER_CAN_CAPACITY
	play_seconds = 0.0
	talked_today = false
	energy = Parity.MAX_ENERGY if energy_after < 0.0 else energy_after
	last_summary = {
		"day": day,
		"season": season,
		"year": year,
		"income": income,
		"season_changed": season_changed,
	}
	if slept:
		save_game()
	day_started.emit(last_summary)
	changed.emit()


func sleep() -> void:
	advance_day(true)


func pass_out() -> void:
	var penalty: int = mini(int(gold * Parity.PASSOUT_GOLD_RATE), Parity.PASSOUT_GOLD_MAX)
	gold = maxi(0, gold - penalty)
	message.emit("你在凌晨两点昏倒了……医药费 %d 金币。" % penalty)
	advance_day(true, Parity.PASSOUT_ENERGY)


func change_scene(target: String) -> void:
	if target == "house":
		current_scene = "house"
		spawn_cell = Vector2i(5, 5)
		get_tree().change_scene_to_file(HOUSE_SCENE)
	else:
		current_scene = "farm"
		spawn_cell = Vector2i(15, 11)
		get_tree().change_scene_to_file(FARM_SCENE)


# ---------------- 存档 ----------------


func to_data() -> Dictionary:
	return SaveSystem.to_data(self)


func from_data(data: Dictionary) -> bool:
	if not SaveSystem.from_data(self, data):
		return false
	changed.emit()
	return true


func save_game() -> bool:
	var file := FileAccess.open(save_path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(to_data(), "\t"))
	return true


func load_game() -> bool:
	if not FileAccess.file_exists(save_path):
		return false
	var file := FileAccess.open(save_path, FileAccess.READ)
	if file == null:
		return false
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return false
	return from_data(parsed)
