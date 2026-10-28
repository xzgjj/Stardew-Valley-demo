extends RefCounted
## 共享测试断言与退出码，避免各套件重复实现。

var tree: SceneTree
var failures: int = 0


func _init(scene_tree: SceneTree) -> void:
	tree = scene_tree


func check(condition: bool, label: String) -> void:
	if condition:
		print("PASS: ", label)
	else:
		failures += 1
		print("FAIL: ", label)
		push_error("FAIL: " + label)


func first_slot_with(gs, item_id: String) -> int:
	for i in range(gs.inventory.size):
		var slot: Dictionary = gs.inventory.slots[i]
		if String(slot.get("id", "")) == item_id:
			return i
	return -1


func finish() -> void:
	tree.quit(1 if failures > 0 else 0)
