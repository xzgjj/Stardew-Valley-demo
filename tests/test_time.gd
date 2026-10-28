extends SceneTree
## 时间系统：时钟格式、10 分钟刻、睡觉推进、季节轮换、2:00 昏倒惩罚。

const Harness = preload("res://tests/harness.gd")
const GameStateScript = preload("res://scripts/autoload/game_state.gd")
const Clock = preload("res://scripts/systems/clock.gd")
const Parity = preload("res://scripts/data/parity.gd")


func _init() -> void:
	var h := Harness.new(self)
	h.check(Clock.format(360) == "6:00 am", "clock formats 6:00 am")
	h.check(Clock.format(720) == "12:00 pm", "clock formats noon")
	h.check(Clock.format(780) == "1:00 pm", "clock formats 1:00 pm")
	h.check(Clock.format(1440) == "12:00 am", "clock formats midnight")
	var gs = GameStateScript.new()
	gs.save_path = "user://test_time_save.json"
	gs.new_game()
	gs.initialized = true
	gs._process(6.9)
	h.check(gs.minutes == 360, "no tick before 7 seconds")
	gs._process(0.2)
	h.check(gs.minutes == 370, "one tick advances 10 in-game minutes")
	h.check(Clock.format(gs.minutes) == "6:10 am", "clock text tracks minutes")
	gs.advance_day(false)
	h.check(gs.minutes == 360, "new day resets clock to 6:00")
	h.check(gs.day == 2, "sleep advances the day")
	gs.day = 28
	gs.season = 0
	gs.plots = {"1,1": {"crop": "parsnip", "growth": 2, "watered": true}}
	gs.advance_day(false)
	h.check(gs.day == 1, "season rolls over after day 28")
	h.check(gs.season == 1, "next season is summer")
	h.check(gs.plots.is_empty(), "crops wither at season change")
	gs.gold = 500
	gs.energy = 10.0
	gs.day = 1
	gs.pass_out()
	h.check(gs.gold == 450, "passing out costs 10% of gold")
	h.check(is_equal_approx(gs.energy, Parity.PASSOUT_ENERGY), "passing out restores half energy")
	h.check(gs.day == 2, "passing out advances the day")
	h.finish()
