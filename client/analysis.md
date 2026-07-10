# 工程分析：usb_kvm_client

## 1. 项目定位

该目录是一个基于 **PySide6 (Qt)** 的桌面 GUI 程序，项目名为 `usb_kvm_client`（见 [pyproject.toml](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/pyproject.toml)），功能目标是作为“USB KVM Client”，通过不同的控制器实现（如 CH9329 / kvm-card-mini）向设备发送键盘/鼠标事件，并通过 Qt Multimedia 采集并展示视频输入设备画面。

项目中未引入 OpenCV（代码中未发现 `cv2`），目录名 `opencv` 更像是上层仓库组织方式，与本子工程的核心技术栈并不直接绑定。

## 2. 运行环境与依赖

- Python：`>=3.12, <3.15`（见 [pyproject.toml](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/pyproject.toml#L5)）
- GUI：PySide6（Qt Widgets + Qt Multimedia）
- 配置：PyYAML
- 日志：loguru
- 设备通信：
  - 串口：pyserial
  - HID：hidapi
  - CH9329：pych9329
- Windows 特性：
  - `pywin32`（为 `pythoncom` 提供支持）
  - `pyWinhook/pywinhook`（系统键盘钩子功能；在 Python 3.12 下通常需要本机编译工具链才能安装）

本工程自带了一个“完整 requirements”（见 [data/requirements.bin](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/data/requirements.bin)），其中包含打包与代码格式化/检查依赖（如 black、flake8、nuitka 等）。为便于“只运行 GUI”，我额外提供了一个更精简的运行时依赖列表：[requirements_runtime_windows.bin](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/data/requirements_runtime_windows.bin)。

## 3. 目录结构速览

- 根目录
  - [main.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py)：主 GUI 逻辑与大部分业务实现（窗口、状态、输入处理、视频、定时器/线程等）
  - [usb_kvm_client.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/usb_kvm_client.py)：发布入口/包装入口，捕获异常并落盘 `exception.log`
  - `project_*.py`：项目路径/配置/信息等辅助
  - `*_buffer.py`：键盘、鼠标与状态缓冲
- [controller/](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/controller/)
  - [base.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/controller/base.py)：控制器抽象
  - [general.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/controller/general.py)：按 `controller_type` 分发到具体实现（`ch9329` / `kvm-card-mini`）
  - `serial_device.py` 等：串口发现/连接
- [ui/](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/ui/)
  - `ui_resource/`：Qt Designer `.ui` 与生成的 Python 文件
  - `ui_main.py` 等：对生成 UI 的二次封装
- [data/](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/data/)
  - 默认配置、键盘 HID 映射表、requirements 等
- [translate/](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/translate/)
  - Qt 翻译资源 `.ts/.qm`
- [script/](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/script/)
  - 打包/生成依赖/更新翻译/代码检查脚本

## 4. 启动与主流程

### 4.1 入口选择

- 开发/源码直接运行：可以直接运行 [main.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py#L2519-L2542)
- 更像“发行入口”的方式：运行 [usb_kvm_client.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/usb_kvm_client.py#L12-L26)
  - 该入口会捕获异常并写入 `exception.log`，便于分发后的故障定位

### 4.2 main() 启动做了什么

见 [main()](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py#L2519-L2542)：

1. `os_init()`：Windows 下设置 Qt 字体渲染相关环境变量，并将工作目录切换到二进制目录（`argv[0]` 所在目录）（见 [os_init()](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py#L2501-L2516)）
2. `command_line_parser()`：解析 `--debug` 并初始化 loguru（见 [command_line_parser()](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py#L2485-L2499)）
3. 创建 `QApplication`
4. 加载 `translate/*.qm` 翻译文件
5. 创建并显示 `AppMainWindow()`（见 [AppMainWindow](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py#L488-L636)）

## 5. 配置管理

配置入口在 [MainConfig](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/project_config.py#L37-L71)：

- 默认配置字符串来自 [MAIN_DEFAULT_CONFIG_DATA](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/data/default_config.py)
- 若 `config.yaml` 不存在，会自动生成并写入默认配置（见 [project_config.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/project_config.py#L65-L70)）
- 配置拆分到 `connection/controller/mouse/paste_board/shortcut_keys/ui/video/video_record` 等节点（见 [split_data_node()](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/project_config.py#L53-L64)）

与“资源/运行目录”相关的定位在 [project_path.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/project_path.py)：

- `project_source_directory_path()`：指向源码目录（`__file__` 所在）
- `project_binary_directory_path()`：指向运行目录（`argv[0]` 所在）

这套设计便于同时支持：

- 源码运行（资源文件在源码目录）
- 打包后运行（资源文件随 exe 分发，运行目录即二进制目录）

## 6. 控制器与设备层（输入注入）

控制器统一分发入口：[ControllerGeneralDevice](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/controller/general.py#L9-L60)

- 通过配置字段 `controller_type` 决定具体实现（`ch9329` / `kvm-card-mini`）
- 上层 GUI 通过统一的 `device_event(command, buffer)` 与控制器交互（例如 `keyboard_write`、`mouse_absolute_write` 等命令见 [ControllerEventProxy.command_send](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py#L122-L145) 的 docstring）

输入状态用缓冲类承载：

- 键盘缓冲：[keyboard_buffer.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/keyboard_buffer.py)
- 鼠标缓冲：[mouse_buffer.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/mouse_buffer.py)
- 全局状态缓存：[status_buffer.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/status_buffer.py)

## 7. 视频采集/显示与录制

视频相关逻辑集中在 [VideoSession](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py#L257-L346)：

- 使用 `QMediaDevices.videoInputs()` 枚举视频输入
- 通过 `QCamera / QMediaCaptureSession / QVideoSink` 展示画面
- 支持 `QImageCapture` 截图与 `QMediaRecorder` 录制（MPEG4）

因此，对“视频设备”的依赖来自系统层（采集卡/摄像头驱动），而不是 OpenCV。

## 8. Windows 系统钩子（pyWinhook）

工程在 Windows 下提供“系统键盘钩子”能力（见 [init_system_hook()](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py#L764-L774)、[system_hook_triggered()](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py#L1318-L1344)），用于捕获全局键盘事件。

现实情况是：`pywinhook/pyWinhook` 在 Python 3.12 环境下通常缺少现成 wheel，会走本机编译，依赖 SWIG + MSVC Build Tools。

为了让工程在“没有本机编译工具链”的环境也能运行 GUI，我做了一个兼容性调整：

- Windows 下 `pyWinhook` / `pythoncom` 改为可选导入
- 若缺失则自动禁用“系统钩子”菜单入口，并在用户点击时提示不可用

相关改动位于 [main.py](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/main.py#L99-L105) 与系统钩子函数处。

## 9. 工程脚本（开发/打包）

脚本目录：[script/](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/script/)

- Nuitka 打包： [compiler.ps1](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/script/compiler.ps1)
- 生成 requirements： [create_requirements.ps1](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/script/create_requirements.ps1)
- 更新/编译翻译： [update_translate.ps1](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/script/update_translate.ps1)
- 代码检查： [code_check.ps1](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/script/code_check.ps1)

## 10. 本地创建虚拟环境并运行（Windows）

在项目根目录（本目录）执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install -r .\data\requirements_runtime_windows.bin
.\.venv\Scripts\python .\usb_kvm_client.py
```

如需打开调试日志：

```powershell
.\.venv\Scripts\python .\usb_kvm_client.py --debug
```

首次启动会在工作目录生成 `config.yaml`（若不存在）。

## 11. 常见问题

### 11.1 安装 pywinhook 失败

若你尝试安装 [data/requirements.bin](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/data/requirements.bin) 并遇到 `pywinhook` 构建失败（缺 SWIG / MSVC）：

- 仅运行 GUI：使用 [requirements_runtime_windows.bin](file:///c:/Users/SheiHoGain/Desktop/9329/opencv/client/data/requirements_runtime_windows.bin)
- 需要系统钩子：安装 SWIG + Visual C++ Build Tools 后再安装 `pywinhook`

### 11.2 无法找到视频设备

视频设备枚举来自 `QMediaDevices.videoInputs()`；如果下拉列表为空或找不到目标设备：

- 先确认系统已识别采集卡/摄像头（设备管理器/系统设置）
- 检查配置中的 `video.device` 是否匹配设备 `description()`
