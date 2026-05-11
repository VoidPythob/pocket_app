# pocket_app

`pocket_app` 是一个使用 PyQt6 构建的桌面端宝可梦数据展示前端项目。

## 技术栈

- Python 3.13
- PyQt6
- aiohttp

## 快速开始

建议从一个新的虚拟环境开始，不依赖已有本地环境。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m pocket_app.main
```

如果你的终端里没有可用的 `python` 命令，先安装 Python 3.13，并确保解释器已经加入系统环境变量。

## 开发约定

仓库内已经提供两份本地 skill 文档，适合作为开发规范：

- `skills/项目文件规范/skill.md`：定义代码应该放在哪个目录、什么时候拆模块。
- `skills/python风格规范/skill.md`：定义 Python 代码的命名、类型标注、函数职责和控制流风格。

如果后续继续扩展页面、接口和组件，建议优先遵守这两份规范，这样结构会更稳定。

## 许可证

本项目使用 MIT License，详见 [LICENSE](./LICENSE)。
