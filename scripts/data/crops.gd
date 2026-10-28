extends RefCounted
## 作物定义。days=成熟所需天数；stages=生长阶段数；seasons=可种植季节（0 春）。

const CROPS := {
	"parsnip":
	{
		"name": "防风草",
		"seed": "parsnip_seed",
		"harvest": "parsnip",
		"days": 4,
		"stages": 4,
		"seasons": [0],
		"sell": 35,
		"seed_price": 20,
	},
}


static func get_crop(id: String) -> Dictionary:
	return CROPS.get(id, {})


static func days_to_grow(id: String) -> int:
	return int(get_crop(id).get("days", 0))


static func harvest_id(id: String) -> String:
	return String(get_crop(id).get("harvest", ""))


static func seed_id(id: String) -> String:
	return String(get_crop(id).get("seed", ""))


static func can_plant_in(id: String, season: int) -> bool:
	var seasons: Array = get_crop(id).get("seasons", [])
	return seasons.has(season)


static func harvest_yield(_id: String) -> int:
	return 1
