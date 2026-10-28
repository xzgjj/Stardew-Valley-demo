extends RefCounted
## 游戏时钟工具函数。分钟数从 0 起算（0 = 午夜），360 = 6:00，1560 = 次日 2:00。

const Parity = preload("res://scripts/data/parity.gd")
const SEASONS := ["春", "夏", "秋", "冬"]


static func format(minutes: int) -> String:
	var total: int = posmod(minutes, 1440)
	var hour: int = int(total / 60.0)
	var minute: int = total % 60
	var suffix := "am" if hour < 12 else "pm"
	var hour12: int = hour % 12
	if hour12 == 0:
		hour12 = 12
	return "%d:%02d %s" % [hour12, minute, suffix]


static func date_text(season: int, day: int, year: int) -> String:
	return "%s %d日 · 第 %d 年" % [SEASONS[posmod(season, 4)], day, year]


static func is_late(minutes: int) -> bool:
	return minutes >= 1440


static func tick(minutes: int) -> int:
	return minutes + Parity.TICK_MINUTES
