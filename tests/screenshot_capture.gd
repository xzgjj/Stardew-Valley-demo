extends Node
## 视觉证据工具：实例化主场景，等 1 秒渲染后截图到 user://screenshot.png，然后退出。
## 运行：godot --path . res://tests/screenshot_capture.tscn（非 headless，需要渲染）


func _ready() -> void:
	var farm = load("res://scenes/main.tscn").instantiate()
	add_child(farm)
	await get_tree().create_timer(1.0).timeout
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	var target := ProjectSettings.globalize_path("user://screenshot.png")
	image.save_png(target)
	print("SCREENSHOT: ", target)
	get_tree().quit()
