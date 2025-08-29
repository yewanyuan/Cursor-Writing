# Cursor Writing 简介

Cursor Writing是本人尝试制作的一个小想法，旨在练习并熟悉如何做出AI类工具的流程，整个项目是在AI辅助下搭建并完成的。Cursor Writing是一个功能相对完整的现代文本编辑器，支持AI辅助撰写、语法高亮等功能。

## ✨ 功能介绍

### 🎨 界面设计
- **三栏布局**: 左侧文件树(20%) + 中间编辑区(70%) + 右侧AI面板(10%，可隐藏)
- **现代配色**: 主背景#66CCFF，侧边栏和编辑区白色背景，深灰色文字
- **专业字体**: 编辑区使用Fira Code等宽字体，界面使用Segoe UI系统字体

### 📁 文件管理
- **文件操作**: 新建、打开、保存、另存为、关闭文件
- **文件夹操作**: 打开文件夹，递归加载目录结构
- **文件树**: 支持展开/折叠，右键菜单操作
- **多标签**: 支持多文件同时编辑，显示修改状态

### ✏️ 编辑功能
- **代码编辑器**: 基于CodeMirror，支持语法高亮
- **语言支持**: JavaScript、HTML、CSS、JSON、Markdown、Python等
- **编辑操作**: 撤销/重做、剪切/复制/粘贴、格式化
- **智能缩进**: 自动缩进和代码折叠

### 🤖 AI功能
- **文本补全**: 基于上下文的智能文本内容补全
- **文本扩写**: 对选中文本进行扩展和改进
- **右键集成**: 编辑器右键菜单直接调用AI功能
- **侧边面板**: 专门的AI辅助面板，实时显示生成结果

### ⌨️ 交互体验
- **快捷键**: 完整的键盘快捷键支持
- **自动保存**: 可配置的自动保存功能
- **拖放支持**: 支持拖拽文件到编辑器打开
- **状态栏**: 显示文件类型、光标位置、保存状态等信息
- **通知系统**: 消息提示系统

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- 具体详见 `backend/requirements.txt`
- 一个 OpenAI API Key（任何一个大模型的Key）

### 2. 安装运行

**2.1 下载项目**
   ```
   # 解压到本地
   # cd 到项目目录
   ```

**2.2 配置环境变量**
   ```bash
   cp backend/.env
   # 编辑 .env 文件，添加 OpenAI API Key
   ```

**2.3 启动服务**
   ```bash
   chmod +x start.sh
   ./start.sh
   # 这个是一键启动脚本，如果有现成的虚拟环境，可以手动启动
   ```
  
**2.4 访问应用**
   - 编辑器界面: http://[localhost:8000/static](http://localhost:8000/static/index.html)
   - API文档: http://localhost:8000/docs

### 3. 手动启动

如果自动脚本无法使用，可以手动启动：

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
conda create -n cursor_writing python=3.8
# 比较习惯conda

# 安装依赖
pip install -r requirements.txt

# 启动服务
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📖 使用说明

### 1. 基本操作

**1.1 新建文件**: Ctrl+N 或 菜单 → 文件 → 新建文件
**1.2 打开文件**: Ctrl+O 或 拖拽文件到编辑器
**1.3 打开文件夹**: Ctrl+Shift+O，支持整个项目的文件树浏览
**1.4 保存文件**: Ctrl+S
**1.5 切换文件**: 点击顶部标签页

### 2. AI功能使用

**2.1 文本补全**:
   - 在编辑器中定位光标到需要补全的位置
   - 右键选择"AI补全"或选择文本后使用AI面板
   - AI会根据上下文生成补全建议

**2.2 文本扩写**:
   - 选中需要扩写的文本
   - 右键选择"AI扩写"
   - AI会对选中内容进行扩展和改进

### 3. 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+N | 新建文件 |
| Ctrl+O | 打开文件 |
| Ctrl+Shift+O | 打开文件夹 |
| Ctrl+S | 保存文件 |
| Ctrl+Z | 撤销 |
| Ctrl+Y | 重做 |
| Ctrl+X | 剪切 |
| Ctrl+C | 复制 |
| Ctrl+V | 粘贴 |
| Ctrl+/ | 切换注释 |

## 🏗️ 项目结构

```
project/
├── frontend/                 # 前端文件
│   ├── index.html           # 主页面
│   ├── styles.css           # 样式文件
│   └── js/
│       └── app.js           # 主要JavaScript逻辑
├── backend/                 # 后端文件
│   ├── app/
│   │   └── main.py          # FastAPI主程序
│   ├── requirements.txt     # Python依赖
│   └── .env.example        # 环境变量模板
└── start.sh                # 启动脚本
```

## 🛠️ 技术栈

### 前端
- **HTML5/CSS3**: 响应式布局和现代UI设计
- **JavaScript (ES6+)**: 原生JavaScript，无框架依赖
- **CodeMirror 5.x**: 专业代码编辑器组件
- **Font Awesome**: 图标库

### 后端
- **FastAPI**: 现代Python Web框架
- **OpenAI API**: GPT模型用于AI功能
- **Uvicorn**: ASGI服务器
- **Pydantic**: 数据验证

## 🔧 配置选项

### 环境变量

在 `backend/.env` 文件中配置：

```env
# OpenAI API配置
OPENAI_API_KEY=your_api_key_here

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS配置
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

### 自动保存配置

可以在前端代码中调整自动保存间隔（默认30秒）：

```javascript
// 在 app.js 中修改
this.autoSaveDelay = 30000; // 30秒，单位毫秒
```

## 🚨 注意事项

1. **API Key 安全**: 请妥善保管自己的OpenAI API Key，不要提交到版本控制系统
2. **浏览器兼容性**: 建议使用现代浏览器（Chrome 88+, Firefox 78+, Safari 14+）
3. **文件系统限制**: 由于浏览器安全限制，某些文件操作可能需要用户确认
4. **CORS 配置**: 如果需要从其他域名访问，请相应调整CORS设置

## 📝 开发说明

### 添加新的语言支持

1. 在HTML中引入对应的CodeMirror语言模式
2. 在`getEditorMode()`方法中添加文件类型映射（app.js）
3. 在`getFileIcon()`方法中添加图标映射（app.js）

### 扩展AI功能

可以通过修改后端API来支持更多AI功能：

```python
@app.post("/api/ai/custom")
async def custom_ai_function(request: AIRequest):
    # 实现自定义AI功能
    pass
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

