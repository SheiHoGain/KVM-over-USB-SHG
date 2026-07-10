# KVM over USB

这是一个基于 [wevsty/KVM-over-USB](https://github.com/wevsty/KVM-over-USB) 的 fork 版本，当前主要展示我在此基础上的功能改动。

## 修改点

- 添加 RGB24 视频格式支持。
- 添加无显示输入模式，可在无视频显示输入时进行单键鼠控制。

## 编译

推荐使用 Python 3.12-3.14，具体以 `client/pyproject.toml` 中的 `requires-python` 为准。

```powershell
git clone https://github.com/wevsty/KVM-over-USB.git
cd client
uv venv
uv sync
# 执行 compiler.ps1 时请根据实际环境进行修改
./compiler.ps1
```

## 上游项目

本仓库基于 [wevsty/KVM-over-USB](https://github.com/wevsty/KVM-over-USB) fork 修改，并保留上游许可证与版权声明。

## 许可证

本项目源码基于 MIT License 发布，详见 [LICENSE](./LICENSE)。

## 第三方组件声明

第三方说明见 [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md)。
