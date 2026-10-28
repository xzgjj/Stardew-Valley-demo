extends RefCounted
## HUD 工厂与样式：面板 / 文本 / 九宫格样式集中在这里，控制单个脚本规模。

const Art = preload("res://scripts/world/art.gd")


static func panel(parent: Node, position: Vector2, size: Vector2) -> Panel:
	var node := Panel.new()
	node.position = position
	node.size = size
	node.add_theme_stylebox_override("panel", panel_style())
	parent.add_child(node)
	return node


static func label(
	parent: Node, position: Vector2, size: Vector2, text: String, font_size: int
) -> Label:
	var node := Label.new()
	node.position = position
	node.size = size
	node.text = text
	node.add_theme_font_size_override("font_size", font_size)
	node.add_theme_color_override("font_color", Color("f2e9d8"))
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(node)
	return node


static func panel_style() -> StyleBox:
	var texture := Art.panel_texture()
	if texture != null:
		var style := StyleBoxTexture.new()
		style.texture = texture
		style.texture_margin_left = 8.0
		style.texture_margin_top = 8.0
		style.texture_margin_right = 8.0
		style.texture_margin_bottom = 8.0
		return style
	var flat := StyleBoxFlat.new()
	flat.bg_color = Color(0.11, 0.09, 0.07, 0.92)
	flat.border_color = Color(0.55, 0.42, 0.26, 1.0)
	flat.set_border_width_all(2)
	return flat


static func slot_style(selected: bool) -> StyleBox:
	var flat := StyleBoxFlat.new()
	flat.bg_color = Color(0.98, 0.82, 0.35, 0.25) if selected else Color(0.1, 0.08, 0.06, 0.75)
	flat.border_color = Color("ffd479") if selected else Color(0.45, 0.38, 0.28, 1.0)
	flat.set_border_width_all(1)
	return flat
