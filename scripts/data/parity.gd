extends RefCounted
## Stardew Valley 1:1 对齐常量（parity baseline）。
## 每条参考值在 docs/research_stardew_parity.md 有来源；tests/test_parity.gd 会锁定这些值，
## 防止实现漂移。修改任何常量都必须同步 REFERENCE、研究文档与 SPEC。

const TILE_SIZE := 16
const VIEWPORT_SIZE := Vector2i(640, 360)
const FARM_SIZE := Vector2i(80, 65)

# 时间：6:00 起床；每 10 游戏分钟约 7 现实秒；2:00 昏倒。
const START_MINUTES := 360
const TICK_MINUTES := 10
const TICK_SECONDS := 7.0
const DAY_END_MINUTES := 1560

# 季节与起始资源。
const SEASON_DAYS := 28
const START_GOLD := 500
const START_SEEDS := 15

# 能量与昏倒惩罚。
const MAX_ENERGY := 270.0
const PASSOUT_ENERGY := 135.0
const PASSOUT_GOLD_RATE := 0.1
const PASSOUT_GOLD_MAX := 1000

# 背包 / 浇水壶。
const INVENTORY_SLOTS := 12
const STACK_MAX := 999
const WATER_CAN_CAPACITY := 40

# 工具能量消耗。
const TOOL_ENERGY := {
	"hoe": 2.0,
	"watering_can": 2.0,
	"axe": 2.0,
	"pickaxe": 2.0,
	"scythe": 0.0,
}

# 防风草（Parsnip）：4 天成熟，种子 20g，售价 35g。
const PARSNIP_GROW_DAYS := 4
const PARSNIP_STAGES := 4
const PARSNIP_SEED_PRICE := 20
const PARSNIP_SELL_PRICE := 35

# 社交。
const FRIENDSHIP_TALK := 20
const FRIENDSHIP_MAX := 2500
const FRIENDSHIP_PER_HEART := 250

# 存档。
const SAVE_VERSION := 1

## 参考表：字段 -> [值, 来源说明]。parity 测试逐项比对。
const REFERENCE := {
	"start_minutes": [360, "Stardew Wiki: Day starts 6:00 am"],
	"tick_minutes": [10, "Stardew Wiki: 10 in-game minutes per clock tick"],
	"tick_seconds": [7.0, "Stardew Wiki: 1 in-game hour = 42 real seconds (10 min = 7 s)"],
	"day_end_minutes": [1560, "Stardew Wiki: player passes out at 2:00 am"],
	"season_days": [28, "Stardew Wiki: each season is 28 days"],
	"start_gold": [500, "Stardew Wiki: new save starts with 500g"],
	"start_seeds": [15, "Stardew Wiki: new save starts with 15 parsnip seeds"],
	"max_energy": [270.0, "Stardew Wiki: starting max energy is 270"],
	"inventory_slots": [12, "Stardew Wiki: starting inventory has 12 slots"],
	"parsnip_grow_days": [4, "Stardew Wiki: Parsnip matures in 4 days"],
	"parsnip_seed_price": [20, "Stardew Wiki: Parsnip Seeds cost 20g"],
	"parsnip_sell_price": [35, "Stardew Wiki: Parsnip base sell price 35g"],
	"water_can_capacity": [40, "Stardew Wiki: basic watering can holds 40 water"],
	"farm_size_x": [80, "Stardew Wiki: Standard Farm is 80 tiles wide"],
	"farm_size_y": [65, "Stardew Wiki: Standard Farm is 65 tiles tall"],
	"tool_energy_hoe": [2.0, "Stardew Wiki: hoe uses 2 energy"],
	"tool_energy_can": [2.0, "Stardew Wiki: watering can uses 2 energy"],
	"friendship_talk": [20, "Stardew Wiki: daily chat grants 20 friendship points"],
	"friendship_per_heart": [250, "Stardew Wiki: 250 friendship points per heart"],
}


static func value(key: String) -> Variant:
	if not REFERENCE.has(key):
		return null
	return REFERENCE[key][0]


static func label(season: int) -> String:
	const NAMES := ["春", "夏", "秋", "冬"]
	if season < 0 or season >= NAMES.size():
		return NAMES[0]
	return NAMES[season]
