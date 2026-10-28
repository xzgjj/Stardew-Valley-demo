# CLI 与本地命令

Godot 锁定 `4.7.2.stable.official.ed1daf0bf`（见 `GODOT_VERSION.txt`）。Windows 默认 Godot 路径：
`D:\app_finish\Godot\Godot_v4.7.2-stable_win64_console.exe`（可用环境变量 `GODOT` 覆盖）。

## 运行游戏 / 编辑器
```powershell
godot --path .                 # 运行主场景
godot --editor --path .        # 打开编辑器
```

## 无头验证
```powershell
godot --headless --editor --path . --quit          # 导入资源
godot --headless --path . --script res://tests/test_parity.gd
godot --headless --path . res://tests/scene_smoke.tscn
godot --headless --path . --quit-after 120          # 主场景冒烟
```
测试套件：`tests/test_*.gd`；共享断言在 `tests/harness.gd`（不要命名为 `test_*.gd`，否则会被当作套件执行）。

## 本地全流程 CI
```powershell
python tools/ci/run_local.py                 # 全流程，默认最多 3 轮
python tools/ci/run_local.py --rounds 1      # 只跑 1 轮（CI 云端使用）
python tools/ci/run_local.py --only docs,assets
python tools/ci/run_local.py --skip scope,policy_tightening
python tools/ci/run_local.py --list          # 列出全部检查名
python tools/ci/run_local.py --bootstrap     # 先安装 .ci-venv 工具链
```
逐项输出 PASS/FAIL 与耗时，末尾 SUMMARY 与退出码（0 通过 / 1 失败 / 2 用法错误）；失败项完整日志写入 `%TEMP%\stardew-ci-*` 并在末尾打印路径。`--rounds` 超过 `ci/policy.json` 的 `max_rounds`（3）会被拒绝。

## 单个门脚本
```powershell
python tools/ci/check_docs.py            # 文档预算/重复段落/版本一致
python tools/ci/check_protected_tests.py # 受保护用例
python tools/ci/check_assets.py          # 素材登记与许可
python tools/ci/check_gdscript_size.py   # 单文件 ≤300 行
python tools/ci/check_complexity.py      # 单函数圈复杂度 ≤10
python tools/ci/check_duplicate_blocks.py# ≥8 行重复代码块
python tools/ci/check_unused_scripts.py  # res:// 未引用脚本
python tools/ci/check_lint.py            # gdlint + gdformat --check
python tools/ci/check_godot.py           # 导入 + tests/test_*.gd + smoke
```
git 模式（GitHub Actions 使用）：`check_scope.py --base <sha> --head <sha>`、`check_policy_tightening.py --base <sha>`、`check_protected_tests.py --base <sha> --head <sha>`。

## 工具链安装（gdtoolkit 固定 4.5.0）
```powershell
python -m venv .ci-venv
.ci-venv\Scripts\python.exe -m pip install gdtoolkit==4.5.0
python tools/ci/bootstrap_toolchain.py   # 幂等重装（版本来自 ci/policy.json）
```

## 代码风格
```powershell
.ci-venv\Scripts\gdlint.exe scripts tests
.ci-venv\Scripts\gdformat.exe --check scripts tests
.ci-venv\Scripts\gdformat.exe scripts tests   # 自动格式化
```
GDScript 源文件必须是 UTF-8（无 BOM）：gdtoolkit 遇到 BOM 会直接解析失败（Godot 本身容忍 BOM）。

## 基线快照
```powershell
python tools/ci/baseline.py --trusted --force   # 仅建库/里程碑，需人工批准
```
刷新后重跑 `run_local.py` 确认 0 差异。首轮建库视为基线，不按 50 文件/2400 行阻断；后续 diff 再按预算与“只紧不宽”比较。

## 常用 Godot 参数
- `--headless`：无窗口；`--path <dir>`：工程目录。
- `--script <res://...>`：以该脚本作为主循环/入口（需 `extends SceneTree`）。
- `--quit-after N`：N 帧后退出；`--editor --quit`：仅导入后退出。
- 运行指定场景：`godot --headless --path . res://tests/scene_smoke.tscn`。
- 环境变量：`GODOT` 优先于固定路径；`GODOT_BIN` 为旧脚本兼容兜底。

## MCP（Godot）
本机装有 `@coding-solo/godot-mcp`（`D:\app_finish\Godot\.mcp-server`），设置 `GODOT_PATH` 后可调用
`run_project` / `get_debug_output` / `launch_editor`；无 MCP 会话时以本页 CLI 为准。
