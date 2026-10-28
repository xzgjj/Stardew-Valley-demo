class_name Hud
extends CanvasLayer
## HUD：时钟 / 日期 / 金币 / 能量条 / 12 格工具栏 / 消息 / 对话框；二级菜单交给 menus.gd。

const Art = preload("res://scripts/world/art.gd")
const UiKit = preload("res://scripts/ui/ui_kit.gd")
const MenusScript = preload("res://scripts/ui/menus.gd")
const Items = preload("res://scripts/data/items.gd")
const Parity = preload("res://scripts/data/parity.gd")
const Clock = preload("res://scripts/systems/clock.gd")

var root: Control
var clock_label: Label
var date_label: Label
var energy_fill: ColorRect
var energy_label: Label
var message_label: Label
var slot_panels: Array = []
var slot_icons: Array = []
var slot_counts: Array = []
var dialogue_panel: Panel
var dialogue_speaker: Label
var dialogue_text: Label
var dialogue_hint: Label
var menus

var _modal := ""
var _message_left := 0.0
var _summary_left := 0.0


func _ready() -> void:
	layer = 10
	var theme := Theme.new()
	theme.default_font = Art.font()
	theme.default_font_size = 12
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = theme
	add_child(root)
	menus = MenusScript.new(self)
	menus.build(root)
	_build_status()
	_build_hotbar()
	_build_message()
	_build_dialogue()
	GameState.changed.connect(refresh)
	GameState.message.connect(show_message)
	refresh()


func _process(delta: float) -> void:
	if clock_label:
		clock_label.text = Clock.format(GameState.minutes)
		energy_fill.size.x = 142.0 * _energy_ratio()
		energy_label.text = "%d / %d" % [int(GameState.energy), int(Parity.MAX_ENERGY)]
	if _message_left > 0.0:
		_message_left -= delta
		if _message_left <= 0.0:
			message_label.visible = false
	if _summary_left > 0.0 and _modal == "summary":
		_summary_left -= delta
		if _summary_left <= 0.0:
			close_modal()


func is_modal() -> bool:
	return _modal != ""


func modal_kind() -> String:
	return _modal


func toggle_pause() -> void:
	if _modal == "pause":
		close_modal()
		return
	if _modal != "":
		return
	menus.pause_panel.visible = true
	_modal = "pause"
	GameState.paused = true


func close_modal() -> void:
	_modal = ""
	dialogue_panel.visible = false
	menus.hide_all()
	GameState.paused = false


func show_message(text: String) -> void:
	message_label.text = text
	message_label.visible = true
	_message_left = 3.2


func show_dialogue(speaker: String, text: String, shopping: bool = false) -> void:
	dialogue_speaker.text = speaker
	dialogue_text.text = text
	dialogue_hint.text = "X 关闭   B 买种子" if shopping else "X 关闭"
	dialogue_panel.visible = true
	menus.shop_panel.visible = false
	_modal = "dialogue"
	GameState.paused = true


func open_shop() -> void:
	if _modal != "dialogue":
		return
	menus.shop_panel.visible = true
	dialogue_panel.visible = false
	menus.shop_info.text = "防风草种子    20g    金币：%d" % GameState.gold
	_modal = "shop"
	GameState.paused = true


func show_day_summary(summary: Dictionary) -> void:
	var title := (
		"第 %d 天 · %s" % [int(summary.get("day", 1)), Parity.label(int(summary.get("season", 0)))]
	)
	var lines := [title]
	if int(summary.get("income", 0)) > 0:
		lines.append("出货箱收入：%d 金币" % int(summary["income"]))
	if bool(summary.get("season_changed", false)):
		lines.append("季节更替，田里的作物枯萎了。")
	menus.summary_text.text = "\n".join(lines)
	menus.summary_panel.visible = true
	_modal = "summary"
	_summary_left = 3.2
	GameState.paused = true


func toggle_help() -> void:
	if _modal == "help":
		close_modal()
		return
	if _modal != "":
		return
	menus.help_panel.visible = true
	_modal = "help"
	GameState.paused = true


func refresh() -> void:
	if not clock_label:
		return
	clock_label.text = Clock.format(GameState.minutes)
	date_label.text = (
		"%s  ·  %d 金币"
		% [Clock.date_text(GameState.season, GameState.day, GameState.year), GameState.gold]
	)
	energy_fill.size.x = 142.0 * _energy_ratio()
	energy_label.text = "%d / %d" % [int(GameState.energy), int(Parity.MAX_ENERGY)]
	for i in range(slot_panels.size()):
		_refresh_slot(i)


func _energy_ratio() -> float:
	return clampf(GameState.energy / Parity.MAX_ENERGY, 0.0, 1.0)


func _refresh_slot(index: int) -> void:
	var slot: Dictionary = GameState.inventory.slots[index]
	var icon: TextureRect = slot_icons[index]
	var count: Label = slot_counts[index]
	if slot.is_empty():
		icon.visible = false
		count.text = ""
	else:
		icon.visible = true
		icon.texture = Art.icon_texture(Items.icon_index(String(slot["id"])))
		var amount := int(slot["count"])
		count.text = str(amount) if amount > 1 else ""
	var panel: Panel = slot_panels[index]
	panel.add_theme_stylebox_override("panel", UiKit.slot_style(index == GameState.selected_slot))


# ---------------- 构建 ----------------


func _build_status() -> void:
	var panel := UiKit.panel(root, Vector2(446, 6), Vector2(188, 50))
	clock_label = UiKit.label(panel, Vector2(8, 3), Vector2(172, 20), "6:00 am", 14)
	date_label = UiKit.label(panel, Vector2(8, 24), Vector2(172, 18), "春 1日 · 第 1 年", 11)
	var energy_back := ColorRect.new()
	energy_back.position = Vector2(474, 318)
	energy_back.size = Vector2(146, 10)
	energy_back.color = Color(0.08, 0.08, 0.1, 0.85)
	root.add_child(energy_back)
	energy_fill = ColorRect.new()
	energy_fill.position = Vector2(476, 320)
	energy_fill.size = Vector2(142, 6)
	energy_fill.color = Color("6ab04c")
	root.add_child(energy_fill)
	energy_label = UiKit.label(root, Vector2(474, 300), Vector2(150, 16), "270 / 270", 10)


func _build_hotbar() -> void:
	var bar := HBoxContainer.new()
	bar.position = Vector2(200, 332)
	bar.add_theme_constant_override("separation", 2)
	root.add_child(bar)
	for _i in range(Parity.INVENTORY_SLOTS):
		var panel := Panel.new()
		panel.custom_minimum_size = Vector2(18, 18)
		panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
		panel.add_theme_stylebox_override("panel", UiKit.slot_style(false))
		bar.add_child(panel)
		var icon := TextureRect.new()
		icon.position = Vector2(1, 1)
		icon.size = Vector2(16, 16)
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		panel.add_child(icon)
		var count := UiKit.label(panel, Vector2(4, 8), Vector2(14, 10), "", 9)
		count.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		slot_panels.append(panel)
		slot_icons.append(icon)
		slot_counts.append(count)


func _build_message() -> void:
	message_label = UiKit.label(root, Vector2(90, 296), Vector2(460, 18), "", 11)
	message_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	message_label.add_theme_color_override("font_color", Color("f2e9d8"))
	message_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	message_label.add_theme_constant_override("outline_size", 3)
	message_label.visible = false


func _build_dialogue() -> void:
	dialogue_panel = UiKit.panel(root, Vector2(48, 216), Vector2(544, 74))
	dialogue_speaker = UiKit.label(dialogue_panel, Vector2(10, 4), Vector2(200, 16), "林婶", 12)
	dialogue_speaker.add_theme_color_override("font_color", Color("ffd479"))
	dialogue_text = UiKit.label(dialogue_panel, Vector2(10, 22), Vector2(524, 34), "", 11)
	dialogue_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	dialogue_hint = UiKit.label(dialogue_panel, Vector2(10, 56), Vector2(300, 14), "E 关闭", 9)
	dialogue_hint.add_theme_color_override("font_color", Color("c8c8c8"))
	dialogue_panel.visible = false
