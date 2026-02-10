# Cursor-Writing 幻笔·叙事中枢 小说创作助手

基于多智能体协作的辅助小说创作系统，通过模拟真实编辑部工作流程，解决长篇小说创作中的"遗忘"和"失控"问题。

**主要功能**

> 💡 提示：点击下方功能标题可展开查看详细说明

<details>
<summary><b>1. 多智能体协作系统</b></summary>

四个专业 Agent 分工协作，模拟真实编辑部工作流程。

**智能体分工：**
- **资料员 (Archivist)**：生成场景简报、提取事实、生成章节摘要
- **撰稿人 (Writer)**：根据简报撰写草稿，支持续写和插入
- **审稿人 (Reviewer)**：审核质量、检测与已知事实的冲突
- **编辑 (Editor)**：根据审稿意见和用户反馈修订草稿

</details>

<details>
<summary><b>2. 事实表系统 (Canon)</b></summary>

自动提取和维护小说中的事实，确保前后一致性。

**核心能力：**
- 自动从章节提取事实、时间线事件、角色状态
- 按章节顺序排序，支持智能筛选
- 写作时自动注入相关事实，避免矛盾
- 审稿时检测与已知事实的冲突

**筛选策略：**
- 重要性分级：critical / normal / minor
- 角色关联性优先
- 高置信度优先

</details>

<details>
<summary><b>3. 上下文本体系统 (Ontology)</b></summary>

结构化存储故事世界的核心信息，用于高效的上下文管理。

**核心组件：**
- **CharacterGraph**：角色关系图
  - 角色节点（状态、位置、目标、别名、所属组织）
  - 关系边（支持17种类型：亲属、社会、情感等）
  - 路径查找、组织筛选
- **WorldOntology**：世界观本体
  - 世界规则（可标记为不可违反）
  - 地点（支持层级关系）
  - 势力/组织
- **Timeline**：结构化时间线
  - 事件（时间、参与者、地点、重要性、后果）

**优势：**
- Token 效率：结构化数据比纯文本节省约 90% token
- 一致性检查：可检测与已知规则/事实的冲突
- 精确场景上下文：只提取相关角色的关系和事件
- 自动提取：章节定稿后自动更新本体

</details>

<details>
<summary><b>4. 设定卡片系统</b></summary>

结构化管理小说的各类设定信息。

**卡片类型：**
- **角色卡**：身份、性格、说话风格、边界、人物关系
- **世界观卡**：地理、历史、体系、组织等设定
- **文风卡**：叙事距离、节奏、范文、推荐/禁用词汇
- **规则卡**：必须遵守、禁止事项、质量标准

</details>

<details>
<summary><b>5. 写作工作流</b></summary>

完整的章节创作流程支持。

**工作流程：**
1. 创建章节，设置目标和出场角色
2. 资料员生成场景简报
3. 撰稿人生成初稿
4. 审稿人审核，检测冲突
5. 编辑修订，用户确认
6. 定稿后自动提取事实

**特性：**
- 支持续写和中间插入
- 多版本草稿管理
- 待确认项标记 `[TO_CONFIRM: ...]`

</details>

<details>
<summary><b>6. 小说导入功能</b></summary>

支持从已有小说文件导入，继续创作。

**支持格式：**
- TXT 纯文本（自动检测编码：UTF-8/GBK/GB2312/GB18030/BIG5）
- Markdown（支持 YAML Front Matter）
- EPUB 电子书（自动解析元数据和章节结构）
- PDF 文档

**智能解析：**
- 自动分解章节：支持「第X章」「Chapter X」「序章/楔子/尾声」等多种格式
- 自动提取书名、作者信息
- 导入前预览章节分解结果

**AI 分析（可选）：**
- 自动分析世界观设定
- 自动识别主要角色及其特点
- 自动提取文风特征

</details>

<details>
<summary><b>7. 多 LLM 提供商支持</b></summary>

灵活的 LLM 配置，支持多种提供商。

**支持的提供商：**
- OpenAI (GPT-4o, GPT-5 系列, o1/o3 系列)
- Anthropic (Claude 4.5, Claude 4.1 系列)
- DeepSeek (deepseek-chat, deepseek-reasoner)
- 自定义 OpenAI 兼容 API

**配置方式：**
- 通过设置页面在线配置
- 通过 `.env` 文件配置
- 支持为不同 Agent 指定不同模型

</details>

<details>
<summary><b>8. 数据存储</b></summary>

Git 友好的文件存储结构。

**存储格式：**
- 项目配置：YAML
- 草稿内容：Markdown
- 事实表：JSONL
- 设定卡片：YAML

**目录结构：**
```
data/projects/{project_id}/
├── project.yaml          # 项目信息
├── cards/                # 设定卡片
│   ├── characters/       # 角色卡
│   ├── world/            # 世界观卡
│   ├── style.yaml        # 文风卡
│   └── rules.yaml        # 规则卡
├── drafts/               # 章节草稿
│   └── {chapter}/
│       ├── brief.yaml    # 场景简报
│       ├── v1.md         # 草稿版本
│       ├── review.yaml   # 审稿意见
│       └── final.md      # 成稿
├── canon/                # 事实表
│   ├── facts.jsonl       # 事实
│   ├── timeline.jsonl    # 时间线
│   └── states.jsonl      # 角色状态
└── ontology/             # 本体数据
    └── story_ontology.yaml  # 结构化本体
```

</details>

## 效果展示

（待补充截图）

## 1. 快速开始

### 1.1. 环境要求

- Python 3.10+
- Node.js 18+
- 现代浏览器
- 可用网络（需访问 LLM API）

### 1.2. 后端安装

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1.3. 前端安装

```bash
cd frontend
npm install
```

### 1.4. 配置

**方式一：通过设置页面配置（推荐）**

启动应用后，在设置页面直接填写 API Key 并保存。

**方式二：通过 .env 文件配置**

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入 API Key
# 例如：DEEPSEEK_API_KEY=sk-your-key
```

### 1.5. 启动

**方式一：一键启动（推荐）**

```bash
# Linux / macOS
./start.sh

# Windows
start.bat
```

首次运行会自动安装依赖。使用 `./stop.sh` 或 `stop.bat` 停止服务。

**方式二：手动启动**

```bash
# 启动后端（终端 1）
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m app.main
# 后端运行在 http://localhost:8000

# 启动前端（终端 2）
cd frontend
npm run dev
# 前端运行在 http://localhost:5173
```

## 2. 架构

采用前后端分离架构，后端基于 FastAPI，前端基于 React + TypeScript。

### 2.1. 核心模块

<details>
<summary><b>agents/ - 智能体系统</b></summary>

**文件：**
- `base.py` - 基类，提供 LLM 调用、XML 解析等通用能力
- `archivist.py` - 资料员：场景简报、事实提取、摘要生成
- `writer.py` - 撰稿人：草稿生成、续写、插入
- `reviewer.py` - 审稿人：质量审核、冲突检测
- `editor.py` - 编辑：根据反馈修订草稿

</details>

<details>
<summary><b>storage/ - 存储层</b></summary>

**文件：**
- `base.py` - 基类，YAML/JSONL/Markdown 读写
- `project.py` - 项目存储
- `card.py` - 设定卡片存储
- `draft.py` - 草稿存储
- `canon.py` - 事实表存储（含智能筛选）
- `ontology.py` - 本体存储（角色图、世界观、时间线）

</details>

<details>
<summary><b>llm/ - LLM 网关</b></summary>

**文件：**
- `providers.py` - 提供商适配器（OpenAI/Anthropic/DeepSeek/Custom）
- `client.py` - 统一客户端，支持重试和提供商切换

</details>

<details>
<summary><b>core/ - 核心业务</b></summary>

**文件：**
- `orchestrator.py` - 工作流编排器
- `context.py` - 上下文管理
- `budgeter.py` - Token 预算管理
- `cache.py` - 缓存管理

</details>

<details>
<summary><b>api/ - API 路由</b></summary>

**路由：**
- `/api/projects` - 项目管理
- `/api/projects/{id}/cards` - 设定卡片
- `/api/projects/{id}/drafts` - 草稿管理
- `/api/projects/{id}/canon` - 事实表
- `/api/ontology/{id}` - 本体数据（角色、关系、时间线、规则）
- `/api/settings` - 全局设置
- `/api/statistics` - 写作统计

</details>

### 2.2. 项目结构

```
Cursor-Writing/
├── start.sh              # 一键启动 (Linux/macOS)
├── start.bat             # 一键启动 (Windows)
├── stop.sh               # 停止服务 (Linux/macOS)
├── stop.bat              # 停止服务 (Windows)
├── backend/
│   ├── app/
│   │   ├── agents/       # 智能体系统
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心业务逻辑
│   │   ├── llm/          # LLM 网关
│   │   ├── models/       # Pydantic 数据模型
│   │   ├── services/     # 服务（导出、统计）
│   │   ├── storage/      # 存储层
│   │   ├── utils/        # 工具函数
│   │   ├── config.py     # 配置管理
│   │   └── main.py       # 入口
│   ├── config.yaml       # 配置文件
│   ├── .env              # 环境变量（不提交）
│   └── requirements.txt  # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── api/          # API 调用
│   │   ├── components/   # UI 组件
│   │   ├── pages/        # 页面
│   │   └── types/        # TypeScript 类型
│   ├── package.json
│   └── vite.config.ts
├── data/                 # 数据目录
└── .gitignore
```

## 3. API 文档

启动后端后访问：
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

**核心接口：**

```
# 项目管理
GET    /api/projects                    # 项目列表
POST   /api/projects                    # 创建项目
GET    /api/projects/{id}               # 项目详情

# 设定卡片
GET    /api/projects/{id}/cards/characters      # 角色列表
POST   /api/projects/{id}/cards/characters      # 创建角色
GET    /api/projects/{id}/cards/style           # 文风卡
PUT    /api/projects/{id}/cards/style           # 更新文风

# 草稿管理
GET    /api/projects/{id}/drafts/chapters       # 章节列表
POST   /api/projects/{id}/drafts/chapters       # 创建章节
POST   /api/projects/{id}/drafts/{ch}/generate  # 生成草稿
POST   /api/projects/{id}/drafts/{ch}/continue  # 续写

# 事实表
GET    /api/projects/{id}/canon/facts           # 事实列表
GET    /api/projects/{id}/canon/timeline        # 时间线
GET    /api/projects/{id}/canon/states          # 角色状态

# 本体数据
GET    /api/ontology/{id}/overview              # 本体概览
GET    /api/ontology/{id}/characters            # 角色节点列表
GET    /api/ontology/{id}/relationships         # 角色关系
GET    /api/ontology/{id}/timeline              # 结构化时间线
GET    /api/ontology/{id}/rules                 # 世界规则
GET    /api/ontology/{id}/context/writing       # 写作上下文
GET    /api/ontology/{id}/context/review        # 审稿上下文

# 设置
GET    /api/settings                    # 获取设置
PUT    /api/settings                    # 更新设置
POST   /api/settings/test-connection    # 测试连接
```

## 4. 开发与贡献

### 4.1. 开发环境

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端
cd frontend
npm install
npm run dev
```

### 4.2. 贡献指南

欢迎通过 Issue 与 Pull Request 参与贡献：
- 功能改进与性能优化
- Bug 修复与文档完善
- 新 LLM 提供商适配

## 5. 更新日志

### 2026-02-10

**项目信息编辑功能**
- 新增项目信息编辑功能
  - 支持修改作品名称、作者、类型、简介
  - 新增 `ProjectUpdate` 模型（支持部分更新）
  - 新增 `PUT /api/projects/{id}` 端点
  - 工作区页面标题旁新增编辑按钮

**Bug 修复**
- 修复 `ReviewerAgent.__init__()` 参数错误导致 AI 写作三大功能（创作新章节、续写、插入）失效的问题
  - 原因：`ReviewerAgent` 重写了 `__init__` 但未接收 storage 参数
  - 修复：正确传递 `card_storage`、`canon_storage`、`draft_storage` 到父类

**小说导入功能**
- 新增小说导入服务 `services/importer.py`
  - 支持 TXT、Markdown、EPUB、PDF 四种格式
  - 自动章节分解：支持多种章节标题格式（第X章、Chapter X、序章/楔子/尾声等）
  - 多编码支持：自动检测 UTF-8/GBK/GB2312/GB18030/BIG5
  - EPUB：解析 OPF 元数据和阅读顺序
  - PDF：使用 pypdf 提取文本
- 新增导入 API `/api/import`
  - `POST /import/preview` - 预览解析结果（不创建项目）
  - `POST /import/import` - 导入小说并创建项目
  - `GET /import/formats` - 获取支持的格式列表
- AI 分析功能（可选）
  - 自动分析世界观设定
  - 自动识别主要角色及其特点
  - 自动提取文风特征（叙事距离、节奏、句式等）
- 前端导入界面
  - 首页新增「导入小说」按钮
  - 文件上传与解析预览
  - 章节列表确认
  - 导入选项设置（项目名、类型、是否 AI 分析）
- 新增依赖：beautifulsoup4、lxml、pypdf

---

### 2026-02-09

**事实表批量删除功能**
- 新增批量删除 API 端点
  - `POST /projects/{id}/canon/facts/batch-delete` - 批量删除事实
  - `POST /projects/{id}/canon/timeline/batch-delete` - 批量删除时间线
  - `POST /projects/{id}/canon/states/batch-delete` - 批量删除角色状态
- 前端事实表三个板块添加复选框和批量删除按钮
  - 支持全选/取消全选
  - 显示已选数量
  - 批量删除确认提示

**自动提取去重优化**
- 提取前检测已有数据，自动跳过重复条目
  - 事实：基于描述文本去重（忽略大小写）
  - 时间线：基于 (时间, 事件描述) 组合去重
  - 角色状态：基于 (角色名, 章节) 组合去重
- 提取结果显示跳过的重复条目数量

**Bug 修复**
- 修复自动提取功能 `get_final()` 返回值类型错误
- 修复存储类默认初始化缺少参数问题

---

### 2026-02-06

**上下文本体建模系统**
- 新增结构化本体模型 `models/ontology.py`
  - **CharacterGraph**：角色关系图（节点状态、17种关系类型、路径查找）
  - **WorldOntology**：世界观本体（规则、地点、势力）
  - **Timeline**：时间线（事件、参与者、重要性分级）
  - **StoryOntology**：聚合本体，提供上下文生成方法
- 新增本体存储层 `storage/ontology.py`
  - 角色/关系/事件/规则/地点/势力的增删改查
  - `get_writing_context()` 和 `get_review_context()` 按 token 预算输出紧凑上下文
  - 支持从指定章节重建本体
- 新增本体提取服务 `services/ontology_extractor.py`
  - 从章节内容自动提取结构化本体信息
  - 使用 LLM 进行 JSON 格式化提取
  - 支持长文本分段处理
- 新增本体 API `/api/ontology`
  - 概览、角色、关系、时间线、规则查询
  - 写作/审稿上下文获取
  - 本体重建和清空

**Agent 本体集成**
- Archivist：生成场景简报时使用本体上下文；提取事实后自动更新本体
- Reviewer：审稿时使用本体上下文进行一致性检查

**LLM 配置优化**
- 所有 LLM 提供商（OpenAI/Anthropic/DeepSeek）支持自定义 Base URL
- 设置页面新增 Base URL 输入框，支持代理/中转服务

---

### 2026-02-03

**界面主题优化**
- 应用 Cupcake 主题（清新可爱风格）
- 新增深色模式切换功能，支持浅色/深色/跟随系统三种模式
- 所有页面添加主题切换按钮

**事实表系统优化**
- Canon 显示区域改为自适应高度，随窗口大小自动调整
- CharacterState 新增 `inventory`（持有物品）和 `relationships`（人物关系）字段
- 角色状态编辑弹窗支持物品和关系的输入
- Writer/Reviewer 上下文注入包含物品和关系信息

**事实提取标准优化**
- 重写 Archivist 事实提取 prompt，明确提取标准
- 过滤琐碎事实：不再提取"走在路上"、"攥紧拳头"、"眯起眼"等临时动作
- 事实合并：相关信息合并为一条，避免碎片化
- 数量控制：每章事实控制在 5-15 条，宁缺毋滥
- 重要性分级说明：critical（核心设定）> normal（一般事实）> minor（细节补充）
- 角色状态仅记录章节结束时的持续状态快照

---

### 2026-02-02

**事实表系统优化**
- 新增 `characters` 和 `importance` 字段，支持智能筛选
- 实现按章节顺序排序（支持"第一章"、"第1章"、"ch1"等格式）
- 实现智能筛选策略（按重要性、角色关联性、置信度）
- Writer 筛选：20条事实 + 10条时间线 + 出场角色状态
- Reviewer 筛选：50条事实 + 30条时间线 + 出场角色状态
- 新增章节重建功能 `rebuild_chapter_canon()`

**设置页面优化**
- 修复下拉菜单背景透明问题（补充 popover CSS 变量）
- 模型选择改为 Select + 自定义输入模式，支持手动输入新模型
- 更新预设模型列表（GPT-5.x, Claude 4.x, o3 等）
- 修复测试连接时空 API Key 导致 401 错误
- 修复设置保存后 LLM 客户端未重建问题（新增 `reset_client()`）
- 过滤 `${VAR}` 未解析的环境变量占位符

**四大设定面板完善**
- 角色卡：完整注入到所有 Agent（identity, personality, speech_pattern, boundaries）
- 世界观卡：扩展到 Writer/Reviewer/Editor（之前仅 Archivist 使用）
- 文风卡：vocabulary 和 taboo_words 全面注入
- 规则卡：dos/donts/quality_standards 全面使用

**其他修复**
- 统计页面 `created_at` 改用文件 mtime（之前始终为当前时间）
- Canon 系统 `extract_facts()` 解析修复（之前返回原始响应）
- Orchestrator `_finalize()` 自动保存提取的事实到存储

---

### 2026-01-30

**导出与统计功能**
- 新增导出服务 `exporter.py`，支持导出为 TXT/Markdown/EPUB 格式
- 新增统计服务 `statistics.py`，提供写作数据统计
- 新增统计页面 `StatsPage.tsx`，展示创作天数、字数、章节等数据
- 新增导出 API `/api/projects/{id}/export`

**Agent 系统增强**
- Archivist：增强事实提取能力，支持解析 FACT/EVENT/STATE 格式
- Reviewer：增强冲突检测，支持 `<conflicts>` 标签解析
- Writer：优化上下文注入

**工作区优化**
- ProjectWorkspace 页面大幅优化，改善用户体验
- WritingPage 支持更多交互功能

---

### 2026-01-23

**续写与插入功能**
- Writer Agent 新增 `continue_writing()` 方法
- 支持末尾续写和中间插入两种模式
- 自动合并内容并保存新版本

**核心系统完善**
- 新增 Token 预算管理器 `budgeter.py`
- 新增缓存管理器 `cache.py`
- 上下文管理器 `context.py` 大幅增强
- Orchestrator 工作流编排优化

**草稿存储增强**
- 支持多版本草稿管理
- 新增章节排序（支持中文数字、阿拉伯数字、特殊章节）

**前端优化**
- WritingPage 大幅重构，支持续写/插入交互
- 新增会话管理 API

---

### 2026-01-14 ~ 2026-01-15

**项目初始化**
- 前后端基础架构搭建
- React + TypeScript + Vite 前端
- FastAPI + Pydantic 后端

**智能体系统**
- 实现四个核心 Agent：Archivist、Writer、Reviewer、Editor
- 基类 `BaseAgent` 提供 LLM 调用、XML 解析等通用能力

**存储系统**
- 实现 YAML/JSONL/Markdown 文件存储
- 项目、卡片、草稿、事实表存储模块

**API 路由**
- 项目管理、设定卡片、草稿管理、事实表、设置等完整 API

**LLM 网关**
- 多提供商支持（OpenAI/Anthropic/DeepSeek/Custom）
- 统一客户端，支持重试和提供商切换

**UI 组件库**
- 基于 Radix UI 的组件库（Button、Card、Dialog、Select 等）
- Tailwind CSS 样式系统

---

### 2026-01-08

**项目重启**
- 替换旧代码库，采用新架构重新设计
- 确定多智能体协作 + 事实表系统的核心方案

---

## 致谢

- 感谢 FastAPI、React、Tailwind CSS 等开源项目
- 感谢 OpenAI、Anthropic、DeepSeek 提供的 LLM API

---

版本：v2.3
更新时间：2026-02-10
许可证：MIT
