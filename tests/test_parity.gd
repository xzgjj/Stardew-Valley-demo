extends SceneTree
## 对齐基线测试：所有 1:1 参考常量必须与研究文档一致，防止实现漂移。

const Harness = preload("res://tests/harness.gd")
const Parity = preload("res://scripts/data/parity.gd")
const Items = preload("res://scripts/data/items.gd")
const Crops = preload("res://scripts/data/crops.gd")


func _init() -> void:
	var h := Harness.new(self)
	h.check(Parity.START_MINUTES == 360, "day starts at 6:00 (360 minutes)")
	h.check(Parity.TICK_MINUTES == 10, "clock ticks every 10 in-game minutes")
	h.check(Parity.TICK_SECONDS == 7.0, "10 in-game minutes = 7 real seconds")
	h.check(Parity.DAY_END_MINUTES == 1560, "pass out at 2:00 am (1560)")
	h.check(Parity.SEASON_DAYS == 28, "season has 28 days")
	h.check(Parity.START_GOLD == 500, "new save starts with 500g")
	h.check(Parity.START_SEEDS == 15, "new save starts with 15 parsnip seeds")
	h.check(Parity.MAX_ENERGY == 270.0, "starting max energy 270")
	h.check(Parity.INVENTORY_SLOTS == 12, "starting inventory 12 slots")
	h.check(Parity.WATER_CAN_CAPACITY == 40, "basic watering can holds 40")
	h.check(Parity.PARSNIP_GROW_DAYS == 4, "parsnip matures in 4 days")
	h.check(Parity.PARSNIP_SEED_PRICE == 20, "parsnip seed costs 20g")
	h.check(Parity.PARSNIP_SELL_PRICE == 35, "parsnip sells for 35g")
	h.check(Parity.FARM_SIZE == Vector2i(80, 65), "standard farm is 80x65 tiles")
	h.check(Parity.TOOL_ENERGY["hoe"] == 2.0, "hoe costs 2 energy")
	h.check(Parity.TOOL_ENERGY["watering_can"] == 2.0, "watering can costs 2 energy")
	h.check(
		Items.sell_price("parsnip") == Parity.PARSNIP_SELL_PRICE, "item sheet matches sell price"
	)
	h.check(
		Crops.days_to_grow("parsnip") == Parity.PARSNIP_GROW_DAYS, "crop sheet matches grow days"
	)
	h.check(
		int(Crops.get_crop("parsnip").get("seed_price", 0)) == Parity.PARSNIP_SEED_PRICE,
		"crop sheet matches seed price"
	)
	h.check(
		int(Crops.get_crop("parsnip").get("sell", 0)) == Parity.PARSNIP_SELL_PRICE,
		"crop sheet matches sell"
	)
	h.check(Parity.REFERENCE.size() >= 15, "reference table is populated")
	for key: String in Parity.REFERENCE.keys():
		h.check(Parity.value(key) != null, "reference has value for " + key)
	h.finish()
