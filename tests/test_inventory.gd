extends SceneTree
## 背包契约：初始装备、堆叠、容量、移除与序列化。

const Harness = preload("res://tests/harness.gd")
const Inventory = preload("res://scripts/systems/inventory.gd")


func _init() -> void:
	var h := Harness.new(self)
	var inv = Inventory.new(12)
	h.check(inv.size == 12, "inventory starts with 12 slots")
	h.check(inv.is_empty(), "new inventory is empty")
	inv.setup_starting()
	h.check(inv.count("hoe") == 1, "starting inventory has hoe")
	h.check(inv.count("watering_can") == 1, "starting inventory has watering can")
	h.check(inv.count("parsnip_seed") == 15, "starting inventory has 15 seeds")
	h.check(inv.count("parsnip") == 0, "no parsnip at start")
	h.check(inv.add("parsnip", 3) == 0, "can add parsnip")
	h.check(inv.count("parsnip") == 3, "parsnip stack counts")
	h.check(inv.add("parsnip", 900) == 0, "stack merges into existing slot")
	h.check(inv.count("parsnip") == 903, "stack value after merge")
	h.check(inv.can_add("parsnip", 96), "99 room left in the stack is enough")
	h.check(inv.can_add("hoe", 1), "tool needs a free slot and one exists")
	h.check(inv.remove("parsnip", 900), "can remove a large amount")
	h.check(inv.count("parsnip") == 3, "remove leaves the remainder")
	h.check(not inv.remove("parsnip", 99), "cannot remove more than held")
	h.check(inv.selected(0)["id"] == "hoe", "slot 0 is the hoe")
	var restored = Inventory.new(12)
	h.check(restored.from_array(inv.to_array()), "inventory array restores")
	h.check(restored.count("parsnip") == 3, "restored inventory keeps items")
	h.check(not Inventory.new(13).from_array(inv.to_array()), "rejects mismatched slot count")
	h.finish()
