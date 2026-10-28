extends SceneTree
## 耕作循环：翻地 → 播种 → 浇水 → 过夜成长 → 收获 → 出货。

const Harness = preload("res://tests/harness.gd")
const GameStateScript = preload("res://scripts/autoload/game_state.gd")
const Parity = preload("res://scripts/data/parity.gd")

const CELL := Vector2i(2, 2)


func _init() -> void:
	var h := Harness.new(self)
	var gs = GameStateScript.new()
	gs.save_path = "user://test_farming_save.json"
	gs.new_game()
	h.check(gs.gold == 500, "new game has 500g")
	h.check(gs.inventory.count("parsnip_seed") == 15, "new game has 15 seeds")
	h.check(gs.till(CELL), "till empty ground")
	h.check(is_equal_approx(gs.energy, 268.0), "tilling costs 2 energy")
	h.check(not gs.till(CELL), "cannot till twice")
	h.check(not gs.plant(CELL, "parsnip"), "fails with bad seed id")
	h.check(gs.plant(CELL, "parsnip_seed"), "plant seed on tilled soil")
	h.check(gs.inventory.count("parsnip_seed") == 14, "planting consumes a seed")
	h.check(gs.water_plot(CELL), "water planted crop")
	h.check(is_equal_approx(gs.energy, 266.0), "watering costs 2 energy")
	h.check(gs.water == 39, "watering consumes one water")
	h.check(not gs.water_plot(CELL), "cannot water twice a day")
	gs.advance_day(false)
	h.check(int(gs.plots["2,2"]["growth"]) == 1, "watered crop grows overnight")
	h.check(not bool(gs.plots["2,2"]["watered"]), "watering resets next day")
	h.check(is_equal_approx(gs.energy, 270.0), "sleep restores energy")
	gs.advance_day(false)
	h.check(int(gs.plots["2,2"]["growth"]) == 1, "unwatered crop does not grow")
	for _i in range(3):
		h.check(gs.water_plot(CELL), "water on a growth day")
		gs.advance_day(false)
	h.check(int(gs.plots["2,2"]["growth"]) == 4, "parsnip reaches maturity in 4 watered days")
	h.check(gs.harvest(CELL), "harvest ripe parsnip")
	h.check(gs.inventory.count("parsnip") == 1, "harvested parsnip enters inventory")
	h.check(not gs.harvest(CELL), "cannot harvest an empty plot")
	gs.gold = 0
	h.check(h.first_slot_with(gs, "parsnip") >= 0, "parsnip occupies a slot")
	gs.selected_slot = h.first_slot_with(gs, "parsnip")
	gs.ship_selected()
	h.check(gs.inventory.count("parsnip") == 0, "shipping removes the item")
	gs.advance_day(false)
	h.check(gs.gold == 35, "shipping pays out overnight (35g per parsnip)")
	h.check(gs.water == Parity.WATER_CAN_CAPACITY, "new day refills the watering can")
	h.finish()
