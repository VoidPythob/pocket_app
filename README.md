# pocket_app

`pocket_app` 是一个使用 PyQt6 构建的桌面端宝可梦数据展示前端项目。当前仓库已经完成基础包结构、应用入口和主窗口骨架，后续可以在此基础上继续补充页面、接口请求与样式系统。

## 当前状态

- 已完成 `src` 布局与可安装 Python 包结构。
- 已提供 PyQt6 应用入口 `pocket_app.main`。
- 已建立 `views`、`components`、`styles`、`api`、`utils` 的职责分层。
- 当前主窗口 `MainWindow` 还是最小骨架实现。
- `api.py`、`utils.py`、`components/`、`styles/` 目前仍是预留位置，等待后续功能落地。

如果你现在打开这个项目，可以把它理解为“宝可梦桌面前端的初始化脚手架”，而不是一个已经完成功能的成品应用。

## 技术栈

- Python 3.13
- PyQt6
- aiohttp
- setuptools `src` 布局

## 快速开始

建议从一个新的虚拟环境开始，不依赖已有本地环境。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m pocket_app.main
```

如果你的终端里没有可用的 `python` 命令，先安装 Python 3.13，并确保解释器已经加入系统环境变量。

## 项目结构

```text
pocket_app/
|- pyproject.toml
|- README.md
|- skills/
|  |- python风格规范/
|  |  `- skill.md
|  `- 项目文件规范/
|     `- skill.md
`- src/
   `- pocket_app/
      |- __init__.py
      |- main.py
      |- api.py
      |- utils.py
      |- components/
      |  `- __init__.py
      |- styles/
      |  `- __init__.py
      `- views/
         |- __init__.py
         `- main_window.py
```

## 目录说明

- `src/pocket_app/main.py`：应用启动入口，负责创建 `QApplication` 并拉起主窗口。
- `src/pocket_app/views/`：页面和窗口层，当前包含 `MainWindow`。
- `src/pocket_app/components/`：可复用 UI 组件目录，适合放卡片、面板、列表项等界面片段。
- `src/pocket_app/styles/`：样式组织目录，适合放 QSS、主题和样式加载逻辑。
- `src/pocket_app/api.py`：远程接口访问入口，适合放宝可梦数据请求逻辑。
- `src/pocket_app/utils.py`：通用工具函数入口，适合放与 UI 无关的辅助逻辑。
- `skills/`：仓库内的开发规范文档，用于约束文件组织和 Python 代码风格。

## 开发约定

仓库内已经提供两份本地 skill 文档，适合作为开发规范：

- `skills/项目文件规范/skill.md`：定义代码应该放在哪个目录、什么时候拆模块。
- `skills/python风格规范/skill.md`：定义 Python 代码的命名、类型标注、函数职责和控制流风格。

如果后续继续扩展页面、接口和组件，建议优先遵守这两份规范，这样结构会更稳定。

## 下一步建议

- 为 `MainWindow` 增加基础布局和首屏展示。
- 在 `api.py` 中接入宝可梦数据来源。
- 在 `components/` 中抽取可复用的数据展示组件。
- 在 `styles/` 中建立统一的 QSS 样式入口。
- 补充基础测试或最小运行检查脚本。

## 许可证

本项目使用 MIT License，详见 [LICENSE](./LICENSE)。
