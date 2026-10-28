extends SceneTree
## 存档：版本校验、往返一致、坏档拒绝。

const Harness = preload("res://tests/harness.gd")
const GameStateScript = preload("res://scripts/autoload/game_state.gd")


func _init() -> void:
	var h := Harness.new(self)
	var gs = GameStateScript.new()
	gs.save_path = "user://test_save_roundtrip.json"
	gs.new_game()
	gs.gold = 1234
	gs.day = 7
	gs.season = 2
	gs.energy = 200.0
	gs.plots = {"4,5": {"crop": "parsnip", "growth": 3, "watered": true}}
	gs.shipping = {"parsnip": 2}
	gs.friendship = 250
	gs.talked_today = true
	gs.selected_slot = 3
	gs.spawn_cell = Vector2i(9, 9)
	gs.current_scene = "house"
	var data: Dictionary = gs.to_data()
	h.check(int(data["version"]) == 1, "save data is versioned")
	var restored = GameStateScript.new()
	h.check(restored.from_data(data), "save data restores")
	h.check(restored.gold == 1234, "gold restored")
	h.check(restored.day == 7 and restored.season == 2, "date restored")
	h.check(is_equal_approx(restored.energy, 200.0), "energy restored")
	h.check(restored.inventory.count("parsnip_seed") == 15, "inventory restored")
	h.check(int(restored.plots["4,5"]["growth"]) == 3, "plots restored")
	h.check(int(restored.shipping.get("parsnip", 0)) == 2, "shipping bin restored")
	h.check(restored.friendship == 250, "friendship restored")
	h.check(restored.spawn_cell == Vector2i(9, 9), "spawn cell restored")
	h.check(restored.current_scene == "house", "scene restored")
	var wrong_version: Dictionary = data.duplicate(true)
	wrong_version["version"] = 999
	h.check(not restored.from_data(wrong_version), "rejects unknown save version")
	h.check(not restored.from_data({"version": 1}), "rejects incomplete save")
	var bad_inventory: Dictionary = {"version": 1, "day": 1, "gold": 1, "inventory": "bad"}
	h.check(not restored.from_data(bad_inventory), "rejects bad inventory payload")
	h.check(gs.save_game(), "save game writes a file")
	var loaded = GameStateScript.new()
	loaded.save_path = gs.save_path
	h.check(loaded.load_game(), "load game reads the file")
	h.check(loaded.gold == 1234 and loaded.day == 7, "round-trip preserves progress")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(gs.save_path))
	h.finish()
