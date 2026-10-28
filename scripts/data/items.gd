extends RefCounted
## 物品定义。kind: tool（工具，不可堆叠）/ seed（种子）/ crop（作物）/ material（材料）。
## icon 对应 assets/ui/icons.png 的列号；sell 为出货箱售价；tool 为工具标识。

const ITEMS := {
	"hoe": {"name": "锄头", "kind": "tool", "tool": "hoe", "icon": 0, "sell": 0, "energy": 2.0},
	"watering_can":
	{"name": "浇水壶", "kind": "tool", "tool": "watering_can", "icon": 1, "sell": 0, "energy": 2.0},
	"axe": {"name": "斧头", "kind": "tool", "tool": "axe", "icon": 2, "sell": 0, "energy": 2.0},
	"pickaxe":
	{"name": "镐", "kind": "tool", "tool": "pickaxe", "icon": 3, "sell": 0, "energy": 2.0},
	"scythe": {"name": "镰刀", "kind": "tool", "tool": "scythe", "icon": 4, "sell": 0, "energy": 0.0},
	"parsnip_seed":
	{"name": "防风草种子", "kind": "seed", "crop": "parsnip", "icon": 5, "sell": 10, "energy": 0.0},
	"parsnip": {"name": "防风草", "kind": "crop", "icon": 6, "sell": 35, "energy": 0.0},
	"wood": {"name": "木材", "kind": "material", "icon": 7, "sell": 2, "energy": 0.0},
	"stone": {"name": "石头", "kind": "material", "icon": 8, "sell": 2, "energy": 0.0},
	"fiber": {"name": "纤维", "kind": "material", "icon": 9, "sell": 1, "energy": 0.0},
}


static func get_item(id: String) -> Dictionary:
	return ITEMS.get(id, {})


static func exists(id: String) -> bool:
	return ITEMS.has(id)


static func is_tool_item(id: String) -> bool:
	return get_item(id).get("kind", "") == "tool"


static func sell_price(id: String) -> int:
	return int(get_item(id).get("sell", 0))


static func display_name(id: String) -> String:
	return String(get_item(id).get("name", id))


static func icon_index(id: String) -> int:
	return int(get_item(id).get("icon", 0))


static func energy_cost(id: String) -> float:
	return float(get_item(id).get("energy", 0.0))
