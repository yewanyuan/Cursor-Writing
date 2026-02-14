# Cursor-Writing: Phantom Pen - Narrative Hub

A multi-agent collaborative novel writing assistant that simulates a real editorial workflow to solve the "forgetting" and "losing control" problems in long-form fiction writing.

**[中文文档](README_CN.md)** | English

**Key Features**

> 💡 Tip: Click on feature titles below to expand detailed descriptions

<details>
<summary><b>1. Multi-Agent Collaboration System</b></summary>

Four specialized Agents work together, simulating a real editorial workflow.

**Agent Roles:**
- **Archivist**: Generates scene briefs, extracts facts, creates chapter summaries
- **Writer**: Writes drafts based on briefs, supports continuation and insertion
- **Reviewer**: Reviews quality, detects conflicts with established facts
- **Editor**: Revises drafts based on review feedback and user input

</details>

<details>
<summary><b>2. Canon System (Fact Table)</b></summary>

Automatically extracts and maintains facts from the novel to ensure consistency.

**Core Capabilities:**
- Auto-extract facts, timeline events, and character states from chapters
- Sort by chapter order with smart filtering
- Auto-inject relevant facts during writing to avoid contradictions
- Detect conflicts with known facts during review

**Filtering Strategies:**
- Importance levels: critical / normal / minor
- Character relevance priority
- High confidence priority

</details>

<details>
<summary><b>3. Context Ontology System</b></summary>

Structured storage of core story world information for efficient context management.

**Core Components:**
- **CharacterGraph**: Character relationship graph
  - Character nodes (status, location, goals, aliases, organizations)
  - Relationship edges (17 types: kinship, social, emotional, etc.)
  - Path finding, organization filtering
- **WorldOntology**: World-building ontology
  - World rules (can be marked as unbreakable)
  - Locations (hierarchical support)
  - Factions/Organizations
- **Timeline**: Structured timeline
  - Events (time, participants, location, importance, consequences)

**Advantages:**
- Token efficiency: Structured data saves ~90% tokens compared to plain text
- Consistency checking: Can detect conflicts with known rules/facts
- Precise scene context: Only extract relevant character relationships and events
- Auto-extraction: Automatically update ontology after chapter finalization

</details>

<details>
<summary><b>4. Setting Cards System</b></summary>

Structured management of various novel settings.

**Card Types:**
- **Character Card**: Identity, personality, speech style, boundaries, relationships
- **World Card**: Geography, history, systems, organizations, etc.
- **Style Card**: Narrative distance, pacing, example passages, recommended/forbidden words
- **Rules Card**: Must-do's, don'ts, quality standards

</details>

<details>
<summary><b>5. Writing Workflow</b></summary>

Complete chapter creation process support.

**Workflow:**
1. Create chapter, set goals and appearing characters
2. Archivist generates scene brief
3. Writer generates first draft
4. Reviewer reviews, detects conflicts
5. Editor revises, user confirms
6. Auto-extract facts after finalization

**Features:**
- Support for continuation and mid-text insertion
- Multi-version draft management
- Pending confirmation markers `[TO_CONFIRM: ...]`

</details>

<details>
<summary><b>6. Novel Import</b></summary>

Support importing from existing novel files to continue writing.

**Supported Formats:**
- TXT plain text (auto-detect encoding: UTF-8/GBK/GB2312/GB18030/BIG5)
- Markdown (supports YAML Front Matter)
- EPUB e-books (auto-parse metadata and chapter structure)
- PDF documents

**Smart Parsing:**
- Auto chapter splitting: Supports "Chapter X", "第X章", "Prologue/Epilogue", etc.
- Auto-extract title and author information
- Preview chapter breakdown before import

**AI Analysis (Optional):**
- Auto-analyze world-building settings
- Auto-identify main characters and their traits
- Auto-extract writing style characteristics

</details>

<details>
<summary><b>7. Multi-LLM Provider Support</b></summary>

Flexible LLM configuration with multiple provider support.

**Supported Providers:**
- OpenAI (GPT-4o, GPT-5 series, o1/o3 series)
- Anthropic (Claude 4.5, Claude 4.1 series)
- DeepSeek (deepseek-chat, deepseek-reasoner)
- Custom OpenAI-compatible API

**Configuration Methods:**
- Configure online via settings page
- Configure via `.env` file
- Support assigning different models to different Agents

</details>

<details>
<summary><b>8. Data Storage</b></summary>

Git-friendly file storage structure.

**Storage Formats:**
- Project config: YAML
- Draft content: Markdown
- Fact table: JSONL
- Setting cards: YAML

**Directory Structure:**
```
data/projects/{project_id}/
├── project.yaml          # Project info
├── cards/                # Setting cards
│   ├── characters/       # Character cards
│   ├── world/            # World cards
│   ├── style.yaml        # Style card
│   └── rules.yaml        # Rules card
├── drafts/               # Chapter drafts
│   └── {chapter}/
│       ├── brief.yaml    # Scene brief
│       ├── v1.md         # Draft version
│       ├── review.yaml   # Review feedback
│       └── final.md      # Final version
├── canon/                # Fact table
│   ├── facts.jsonl       # Facts
│   ├── timeline.jsonl    # Timeline
│   └── states.jsonl      # Character states
└── ontology/             # Ontology data
    └── story_ontology.yaml  # Structured ontology
```

</details>

## Screenshots

(Screenshots to be added)

## 1. Quick Start

### 1.1. Requirements

- Python 3.10+
- Node.js 18+
- Modern browser
- Network access (for LLM API)

### 1.2. Backend Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1.3. Frontend Installation

```bash
cd frontend
npm install
```

### 1.4. Configuration

**Method 1: Configure via Settings Page (Recommended)**

After starting the app, fill in your API Key in the settings page and save.

**Method 2: Configure via .env File**

```bash
cd backend
cp .env.example .env
# Edit .env, fill in API Key
# Example: DEEPSEEK_API_KEY=sk-your-key
```

### 1.5. Starting the Application

**Method 1: One-Click Start (Recommended)**

```bash
# Linux / macOS
./start.sh

# Windows
start.bat
```

First run will auto-install dependencies. Use `./stop.sh` or `stop.bat` to stop services.

**Method 2: Manual Start**

```bash
# Start backend (Terminal 1)
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m app.main
# Backend runs at http://localhost:8000

# Start frontend (Terminal 2)
cd frontend
npm run dev
# Frontend runs at http://localhost:5173
```

## 2. Architecture

Frontend-backend separation architecture with FastAPI backend and React + TypeScript frontend.

### 2.1. Core Modules

<details>
<summary><b>agents/ - Agent System</b></summary>

**Files:**
- `base.py` - Base class providing LLM calls, XML parsing, etc.
- `archivist.py` - Archivist: scene briefs, fact extraction, summary generation
- `writer.py` - Writer: draft generation, continuation, insertion
- `reviewer.py` - Reviewer: quality review, conflict detection
- `editor.py` - Editor: revise drafts based on feedback

</details>

<details>
<summary><b>storage/ - Storage Layer</b></summary>

**Files:**
- `base.py` - Base class for YAML/JSONL/Markdown read/write
- `project.py` - Project storage
- `card.py` - Setting cards storage
- `draft.py` - Draft storage
- `canon.py` - Fact table storage (with smart filtering)
- `ontology.py` - Ontology storage (character graph, world-building, timeline)

</details>

<details>
<summary><b>llm/ - LLM Gateway</b></summary>

**Files:**
- `providers.py` - Provider adapters (OpenAI/Anthropic/DeepSeek/Custom)
- `client.py` - Unified client with retry and provider switching

</details>

<details>
<summary><b>core/ - Core Business Logic</b></summary>

**Files:**
- `orchestrator.py` - Workflow orchestrator
- `context.py` - Context management
- `budgeter.py` - Token budget management
- `cache.py` - Cache management

</details>

<details>
<summary><b>api/ - API Routes</b></summary>

**Routes:**
- `/api/projects` - Project management
- `/api/projects/{id}/cards` - Setting cards
- `/api/projects/{id}/drafts` - Draft management
- `/api/projects/{id}/canon` - Fact table
- `/api/ontology/{id}` - Ontology data (characters, relationships, timeline, rules)
- `/api/settings` - Global settings
- `/api/statistics` - Writing statistics

</details>

### 2.2. Project Structure

```
Cursor-Writing/
├── start.sh              # One-click start (Linux/macOS)
├── start.bat             # One-click start (Windows)
├── stop.sh               # Stop services (Linux/macOS)
├── stop.bat              # Stop services (Windows)
├── backend/
│   ├── app/
│   │   ├── agents/       # Agent system
│   │   ├── api/          # API routes
│   │   ├── core/         # Core business logic
│   │   ├── llm/          # LLM gateway
│   │   ├── models/       # Pydantic data models
│   │   ├── services/     # Services (export, statistics)
│   │   ├── storage/      # Storage layer
│   │   ├── utils/        # Utility functions
│   │   ├── config.py     # Configuration
│   │   └── main.py       # Entry point
│   ├── config.yaml       # Config file
│   ├── .env              # Environment variables (not committed)
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/          # API calls
│   │   ├── components/   # UI components
│   │   ├── pages/        # Pages
│   │   └── types/        # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── data/                 # Data directory
└── .gitignore
```

## 3. API Documentation

After starting backend, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Core Endpoints:**

```
# Project Management
GET    /api/projects                    # List projects
POST   /api/projects                    # Create project
GET    /api/projects/{id}               # Project details

# Setting Cards
GET    /api/projects/{id}/cards/characters      # List characters
POST   /api/projects/{id}/cards/characters      # Create character
GET    /api/projects/{id}/cards/style           # Style card
PUT    /api/projects/{id}/cards/style           # Update style

# Draft Management
GET    /api/projects/{id}/drafts/chapters       # List chapters
POST   /api/projects/{id}/drafts/chapters       # Create chapter
POST   /api/projects/{id}/drafts/{ch}/generate  # Generate draft
POST   /api/projects/{id}/drafts/{ch}/continue  # Continue writing

# Fact Table
GET    /api/projects/{id}/canon/facts           # List facts
GET    /api/projects/{id}/canon/timeline        # Timeline
GET    /api/projects/{id}/canon/states          # Character states

# Ontology Data
GET    /api/ontology/{id}/overview              # Ontology overview
GET    /api/ontology/{id}/characters            # Character nodes
GET    /api/ontology/{id}/relationships         # Character relationships
GET    /api/ontology/{id}/timeline              # Structured timeline
GET    /api/ontology/{id}/rules                 # World rules
GET    /api/ontology/{id}/context/writing       # Writing context
GET    /api/ontology/{id}/context/review        # Review context

# Settings
GET    /api/settings                    # Get settings
PUT    /api/settings                    # Update settings
POST   /api/settings/test-connection    # Test connection
```

## 4. Development & Contributing

### 4.1. Development Environment

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run dev
```

### 4.2. Contributing Guide

Welcome to contribute via Issues and Pull Requests:
- Feature improvements and performance optimization
- Bug fixes and documentation improvements
- New LLM provider adapters

## 5. Changelog

### 2026-02-13

**Canon Deduplication Optimization**
- Character States: Only one state record per character per chapter
  - Modified `update_character_state()` to update instead of append for same (character, chapter)
- Facts/Timeline: Exact match deduplication for manual additions
  - Facts: Match by `statement` (case-insensitive, trimmed)
  - Timeline: Match by `(time, event)`
- AI Auto-extraction: Delete old chapter data before adding new extractions
  - Solves duplicate issues caused by AI using different wording for same events

**Input Component Optimization**
- New `TagInput` component: For vocabulary-type inputs (preferred words, taboo words)
  - Enter to add, click to delete, backspace to delete last
- New `ListInput` component: For rule-type inputs (do's, don'ts, quality standards)
  - Enter or button to add, inline editing, delete button
- Replaced original Textarea inputs for better interaction experience

---

### 2026-02-12

**Reviewer Scoring System Optimization**
- Fixed issue where review scores were always 0.50-0.60, causing infinite rewrites
  - Cause: Conflict detection set a hard cap on scores (0.6), below quality threshold (0.7)
  - Fix: Changed to penalty-based scoring (0.05 per conflict, max 0.2 deduction)
- Enhanced conflict validation to filter empty and placeholder conflicts from LLM
- Writer now receives and uses review feedback during rewrites
  - Added `review_feedback` and `review_issues` parameter passing
  - Rewrite prompt includes specific issues from previous review

**Continuation/Insertion Feature Fixes**
- Fixed issue where "Revise" button didn't update content
  - Cause: `skipNextDraftLoad` flag not properly reset after continuation
- Fixed insertion generating duplicate content with following paragraphs
  - Optimized insertion prompt to explicitly avoid repeating subsequent content
- Fixed entire chapter being incorrectly highlighted after revision
  - Added `isRevisionMode` flag to maintain current highlight range in revision mode

**UI Optimization**
- Complete redesign of Style settings panel
  - Card-based layout with gradient title bars
  - Custom radio button design (narrative distance, pacing)
  - Color-coded sections for different settings
  - Count badges for vocabulary/passages
- Complete redesign of Rules settings panel
  - Three-column layout (Do's/Don'ts/Standards)
  - Color-coded cards (green/red/amber)
  - Custom icons with bilingual labels
  - Help tips card at bottom

---

### 2026-02-10

**Project Info Editing**
- Added project info editing functionality
  - Support modifying title, author, genre, description
  - Added `ProjectUpdate` model (supports partial updates)
  - Added `PUT /api/projects/{id}` endpoint
  - Added edit button next to workspace page title

**Bug Fixes**
- Fixed `ReviewerAgent.__init__()` parameter error causing AI writing features (new chapter, continue, insert) to fail
  - Cause: `ReviewerAgent` overrode `__init__` without accepting storage parameters
  - Fix: Properly pass `card_storage`, `canon_storage`, `draft_storage` to parent class

**Novel Import Feature**
- Added novel import service `services/importer.py`
  - Supports TXT, Markdown, EPUB, PDF formats
  - Auto chapter splitting: Multiple chapter title formats
  - Multi-encoding support: UTF-8/GBK/GB2312/GB18030/BIG5
  - EPUB: Parse OPF metadata and reading order
  - PDF: Extract text using pypdf
- Added import API `/api/import`
  - `POST /import/preview` - Preview parsing result
  - `POST /import/import` - Import novel and create project
  - `GET /import/formats` - Get supported formats
- AI analysis (optional)
  - Auto-analyze world-building
  - Auto-identify main characters
  - Auto-extract style characteristics
- Frontend import interface
  - Added "Import Novel" button on home page
  - File upload and parsing preview
  - Chapter list confirmation
  - Import options (project name, genre, AI analysis)
- New dependencies: beautifulsoup4, lxml, pypdf

---

### 2026-02-09

**Fact Table Batch Delete**
- Added batch delete API endpoints
  - `POST /projects/{id}/canon/facts/batch-delete`
  - `POST /projects/{id}/canon/timeline/batch-delete`
  - `POST /projects/{id}/canon/states/batch-delete`
- Frontend fact table panels now have checkboxes and batch delete buttons
  - Select all/deselect all
  - Show selected count
  - Batch delete confirmation

**Auto-Extraction Deduplication**
- Check existing data before extraction, auto-skip duplicates
  - Facts: Dedupe by description text (case-insensitive)
  - Timeline: Dedupe by (time, event description) combination
  - Character states: Dedupe by (character name, chapter) combination
- Extraction results show skipped duplicate count

**Bug Fixes**
- Fixed auto-extraction `get_final()` return type error
- Fixed storage class default initialization missing parameters

---

### 2026-02-06

**Context Ontology Modeling System**
- Added structured ontology models `models/ontology.py`
  - **CharacterGraph**: Character relationship graph (node states, 17 relationship types, path finding)
  - **WorldOntology**: World-building ontology (rules, locations, factions)
  - **Timeline**: Timeline (events, participants, importance levels)
  - **StoryOntology**: Aggregate ontology with context generation methods
- Added ontology storage layer `storage/ontology.py`
  - CRUD for characters/relationships/events/rules/locations/factions
  - `get_writing_context()` and `get_review_context()` output compact context within token budget
  - Support rebuilding ontology from specific chapter
- Added ontology extraction service `services/ontology_extractor.py`
  - Auto-extract structured ontology from chapter content
  - Use LLM for JSON-formatted extraction
  - Support long text segmented processing
- Added ontology API `/api/ontology`
  - Overview, characters, relationships, timeline, rules queries
  - Writing/review context retrieval
  - Ontology rebuild and clear

**Agent Ontology Integration**
- Archivist: Use ontology context when generating scene briefs; auto-update ontology after fact extraction
- Reviewer: Use ontology context for consistency checking during review

**LLM Configuration Optimization**
- All LLM providers (OpenAI/Anthropic/DeepSeek) support custom Base URL
- Settings page added Base URL input for proxy/relay services

---

### 2026-02-03

**UI Theme Optimization**
- Applied Cupcake theme (fresh and cute style)
- Added dark mode toggle with light/dark/system modes
- Added theme toggle button to all pages

**Fact Table System Optimization**
- Canon display area now adaptive height, auto-adjusts with window size
- CharacterState added `inventory` and `relationships` fields
- Character state edit dialog supports items and relationships input
- Writer/Reviewer context injection includes items and relationships

**Fact Extraction Standards Optimization**
- Rewrote Archivist fact extraction prompt with clear standards
- Filter trivial facts: No longer extract temporary actions like "walking", "clenching fist", etc.
- Fact merging: Related info merged into one entry
- Quantity control: 5-15 facts per chapter, quality over quantity
- Importance levels: critical (core settings) > normal (general facts) > minor (details)
- Character states only record persistent state snapshots at chapter end

---

### 2026-02-02

**Fact Table System Optimization**
- Added `characters` and `importance` fields for smart filtering
- Implemented chapter order sorting (supports "Chapter 1", "第一章", "ch1", etc.)
- Implemented smart filtering strategies (by importance, character relevance, confidence)
- Writer filtering: 20 facts + 10 timeline events + appearing character states
- Reviewer filtering: 50 facts + 30 timeline events + appearing character states
- Added chapter canon rebuild function `rebuild_chapter_canon()`

**Settings Page Optimization**
- Fixed dropdown menu transparent background issue
- Model selection changed to Select + custom input mode
- Updated preset model list (GPT-5.x, Claude 4.x, o3, etc.)
- Fixed empty API Key causing 401 error during connection test
- Fixed LLM client not rebuilding after settings save (added `reset_client()`)
- Filter unresolved `${VAR}` environment variable placeholders

**Four Setting Panels Enhancement**
- Character Card: Fully injected to all Agents (identity, personality, speech_pattern, boundaries)
- World Card: Extended to Writer/Reviewer/Editor (previously only Archivist)
- Style Card: vocabulary and taboo_words fully injected
- Rules Card: dos/donts/quality_standards fully utilized

**Other Fixes**
- Statistics page `created_at` now uses file mtime
- Canon system `extract_facts()` parsing fix
- Orchestrator `_finalize()` auto-saves extracted facts to storage

---

### 2026-01-30

**Export & Statistics Features**
- Added export service `exporter.py`, supports TXT/Markdown/EPUB formats
- Added statistics service `statistics.py` for writing data statistics
- Added statistics page `StatsPage.tsx` showing creation days, word count, chapters, etc.
- Added export API `/api/projects/{id}/export`

**Agent System Enhancement**
- Archivist: Enhanced fact extraction, supports FACT/EVENT/STATE format parsing
- Reviewer: Enhanced conflict detection, supports `<conflicts>` tag parsing
- Writer: Optimized context injection

**Workspace Optimization**
- Major ProjectWorkspace page optimization
- WritingPage supports more interactive features

---

### 2026-01-23

**Continuation & Insertion Features**
- Writer Agent added `continue_writing()` method
- Supports end continuation and mid-text insertion modes
- Auto-merge content and save new version

**Core System Improvements**
- Added Token budget manager `budgeter.py`
- Added cache manager `cache.py`
- Major context manager `context.py` enhancement
- Orchestrator workflow optimization

**Draft Storage Enhancement**
- Multi-version draft management support
- Added chapter sorting (Chinese/Arabic numbers, special chapters)

**Frontend Optimization**
- Major WritingPage refactor with continuation/insertion interaction
- Added session management API

---

### 2026-01-14 ~ 2026-01-15

**Project Initialization**
- Frontend/backend architecture setup
- React + TypeScript + Vite frontend
- FastAPI + Pydantic backend

**Agent System**
- Implemented four core Agents: Archivist, Writer, Reviewer, Editor
- Base class `BaseAgent` providing LLM calls, XML parsing, etc.

**Storage System**
- Implemented YAML/JSONL/Markdown file storage
- Project, cards, drafts, fact table storage modules

**API Routes**
- Complete API for projects, setting cards, drafts, fact table, settings

**LLM Gateway**
- Multi-provider support (OpenAI/Anthropic/DeepSeek/Custom)
- Unified client with retry and provider switching

**UI Component Library**
- Radix UI-based components (Button, Card, Dialog, Select, etc.)
- Tailwind CSS styling system

---

### 2026-01-08

**Project Restart**
- Replaced old codebase with new architecture
- Finalized multi-agent collaboration + fact table system design

---

## Acknowledgments

- Thanks to FastAPI, React, Tailwind CSS and other open-source projects
- Thanks to OpenAI, Anthropic, DeepSeek for LLM API services

---

Version: v2.4
Last Updated: 2026-02-12
License: MIT
