class_name Villager
extends Node2D
## 农舍旁的邻居「林婶」：固定站位、按天数/好感轮换问候。

const Art = preload("res://scripts/world/art.gd")

var sprite: Sprite2D


func _ready() -> void:
	sprite = Sprite2D.new()
	sprite.texture = Art.character_texture(true)
	sprite.hframes = 4
	sprite.vframes = 4
	sprite.frame = 1
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(sprite)


func line(friendship: int) -> String:
	var lines := [
		"早上好呀。农场头几天最难，先把防风草种下去吧。",
		"防风草四天就能收，记得每天浇水，不然它不会长大。",
		"浇水壶空了就去池塘边按一下，能补满。",
		"出货箱里的东西过一夜才会结算，别急着等钱。",
		"累了就回屋睡觉，凌晨两点还在外面会昏倒的。",
	]
	if friendship >= 250:
		lines.append("你已经算是村里人了，需要种子随时来找我。")
	var hearts := int(friendship / 250)
	var index: int = (GameState.day + hearts) % lines.size()
	return lines[index]


func talk_line() -> String:
	return line(GameState.friendship)
