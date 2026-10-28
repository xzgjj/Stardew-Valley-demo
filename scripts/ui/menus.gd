extends RefCounted
## 商店 / 日结算 / 暂停 / 帮助面板：从 HUD 拆出的二级菜单，控制单文件规模。

const UiKit = preload("res://scripts/ui/ui_kit.gd")
const Parity = preload("res://scripts/data/parity.gd")

var hud
var shop_panel: Panel
var shop_info: Label
var summary_panel: Panel
var summary_text: Label
var pause_panel: Panel
var help_panel: Panel


func _init(owner_hud) -> void:
	hud = owner_hud


func build(root: Control) -> void:
	_build_shop(root)
	_build_summary(root)
	_build_pause(root)
	_build_help(root)


func hide_all() -> void:
	shop_panel.visible = false
	summary_panel.visible = false
	pause_panel.visible = false
	help_panel.visible = false


func _build_shop(root: Control) -> void:
	shop_panel = UiKit.panel(root, Vector2(184, 110), Vector2(272, 128))
	UiKit.label(shop_panel, Vector2(10, 6), Vector2(240, 18), "林婶的种子篮", 13)
	shop_info = UiKit.label(shop_panel, Vector2(10, 34), Vector2(250, 18), "", 11)
	var buy := Button.new()
	buy.text = "买 1 粒（20g）"
	buy.position = Vector2(10, 64)
	buy.size = Vector2(120, 26)
	buy.pressed.connect(_on_buy_seed)
	shop_panel.add_child(buy)
	var close := Button.new()
	close.text = "关闭"
	close.position = Vector2(140, 64)
	close.size = Vector2(120, 26)
	close.pressed.connect(hud.close_modal)
	shop_panel.add_child(close)
	shop_panel.visible = false


func _on_buy_seed() -> void:
	GameState.buy("parsnip_seed", Parity.PARSNIP_SEED_PRICE)
	shop_info.text = "防风草种子    20g    金币：%d" % GameState.gold


func _build_summary(root: Control) -> void:
	summary_panel = UiKit.panel(root, Vector2(180, 120), Vector2(280, 120))
	summary_text = UiKit.label(summary_panel, Vector2(14, 16), Vector2(252, 88), "", 12)
	summary_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	summary_panel.visible = false


func _build_pause(root: Control) -> void:
	pause_panel = UiKit.panel(root, Vector2(220, 96), Vector2(200, 170))
	UiKit.label(pause_panel, Vector2(10, 8), Vector2(180, 18), "暂停", 14)
	var resume := Button.new()
	resume.text = "继续游戏"
	resume.position = Vector2(10, 36)
	resume.size = Vector2(180, 28)
	resume.pressed.connect(hud.close_modal)
	pause_panel.add_child(resume)
	var save := Button.new()
	save.text = "保存进度"
	save.position = Vector2(10, 70)
	save.size = Vector2(180, 28)
	save.pressed.connect(_on_save)
	pause_panel.add_child(save)
	var quit := Button.new()
	quit.text = "退出游戏"
	quit.position = Vector2(10, 104)
	quit.size = Vector2(180, 28)
	quit.pressed.connect(_on_quit)
	pause_panel.add_child(quit)
	pause_panel.visible = false


func _on_save() -> void:
	GameState.save_game()
	hud.show_message("已保存。")


func _on_quit() -> void:
	hud.get_tree().quit()


func _build_help(root: Control) -> void:
	help_panel = UiKit.panel(root, Vector2(120, 36), Vector2(400, 288))
	var text := "操作说明\n\nWASD / 方向键  移动\n"
	text += "空格  使用当前栏位（锄地 / 浇水 / 砍树 / 敲石头 / 收割 / 播种）\n"
	text += "E  互动（对话 / 出货箱 / 门 / 床）\n1-9 0 - =  选择工具栏\n"
	text += "Tab  本帮助\nEsc  暂停 / 关闭面板\n\n"
	text += "目标：种下防风草，浇水 4 天，收获后放进出货箱，隔夜结算。"
	var label := UiKit.label(help_panel, Vector2(14, 12), Vector2(372, 264), text, 11)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	help_panel.visible = false
