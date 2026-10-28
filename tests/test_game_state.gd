extends SceneTree
## 受保护回归套件：沿用 v0.1 基线的 9 个关键用例 id，行为契约不得弱化。

const Harness = preload("res://tests/harness.gd")
const GameStateScript = preload("res://scripts/autoload/game_state.gd")

const CELL := Vector2i(1, 1)


func _init() -> void:
	var h := Harness.new(self)
	var gs = GameStateScript.new()
	gs.save_path = "user://test_game_state_save.json"
	gs.new_game()
	h.check(gs.till(CELL), "till creates a plot")
	h.check(not gs.till(CELL), "cannot till the same plot twice")
	h.check(gs.plant(CELL, "parsnip_seed"), "seed can be planted on tilled soil")
	h.check(gs.inventory.count("parsnip_seed") == 14, "planting consumes one seed")
	h.check(not gs.harvest(CELL), "unripe crop cannot be harvested")
	h.check(gs.water_plot(CELL), "water planted crop")
	gs.advance_day(false)
	h.check(int(gs.plots["1,1"]["growth"]) == 1, "watered crop grows overnight")
	for _i in range(3):
		gs.water_plot(CELL)
		gs.advance_day(false)
	h.check(gs.harvest(CELL), "ripe crop can be harvested")
	gs.selected_slot = h.first_slot_with(gs, "parsnip")
	gs.ship_selected()
	gs.advance_day(false)
	h.check(gs.gold == 535 and gs.inventory.count("parsnip") == 0, "harvest grants money and count")
	var data: Dictionary = gs.to_data()
	var restored = GameStateScript.new()
	h.check(restored.from_data(data), "save data can be restored")
	h.finish()
