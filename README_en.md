# Cursor Writing Introduction

Cursor Writing is a small project I attempted to create, aimed at practicing and familiarizing myself with the process of developing AI-powered tools. Cursor Writing is a relatively complete modern text editor that supports AI-assisted writing, syntax highlighting, and other features.

## ✨ Feature Introduction

### 🎨 Interface Design
- **Three-column layout**: Left file tree (20%) + Middle editing area (70%) + Right AI panel (10%, collapsible)
- **Modern color scheme**: Main background #66CCFF, white background for sidebars and editing area, dark gray text
- **Professional fonts**: Fira Code monospace font for editing area, Segoe UI system font for interface

### 📁 File Management
- **File operations**: New, Open, Save, Save As, Close file
- **Folder operations**: Open folder, recursively load directory structure
- **File tree**: Supports expand/collapse, right-click context menu operations
- **Multi-tab**: Supports editing multiple files simultaneously, displays modification status

### ✏️ Editing Features
- **Code editor**: Based on CodeMirror, supports syntax highlighting
- **Language support**: JavaScript, HTML, CSS, JSON, Markdown, Python, etc.
- **Editing operations**: Undo/Redo, Cut/Copy/Paste, Format
- **Smart indentation**: Auto-indentation and code folding

### 🤖 AI Features
- **Text completion**: Context-aware intelligent text content completion
- **Text expansion**: Expand and improve selected text
- **Right-click integration**: Directly access AI features via editor context menu
- **Side panel**: Dedicated AI assistance panel showing real-time generation results

### ⌨️ Interaction Experience
- **Keyboard shortcuts**: Full keyboard shortcut support
- **Auto-save**: Configurable auto-save functionality
- **Drag-and-drop support**: Supports dragging files into the editor to open
- **Status bar**: Displays file type, cursor position, save status, etc.
- **Notification system**: Message notification system

## 🚀 Quick Start

### 1. Environment Requirements
- Python 3.8+
- See `backend/requirements.txt` for details
- An OpenAI API Key (any major model's key)

### 2. Installation and Running

**2.1 Download Project**
Extract to local
cd to project directory

**2.2 Configure Environment Variables**
```bash
cp backend/.env
# Edit .env file, add OpenAI API Key
```

**2.3 Start Service**
```
chmod +x start.sh
./start.sh
# This is a one-click startup script. If you have an existing virtual environment, you can start manually
```

2.4 Access Application
Editor interface: http://localhost:8000/static/index.html
API documentation: http://localhost:8000/docs

### 3. Manual Startup
If the automatic script doesn't work, you can start manually:

# Enter backend directory
cd backend
# Create virtual environment
conda create -n cursor_writing python=3.8
# Prefer conda

# Install dependencies
pip install -r requirements.txt

# Start service
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

## 📖 Usage Instructions
### 1. Basic Operations
1.1 New File: Ctrl+N or Menu → File → New File
1.2 Open File: Ctrl+O or drag file into editor
1.3 Open Folder: Ctrl+Shift+O, supports browsing entire project file tree
1.4 Save File: Ctrl+S
1.5 Switch Files: Click top tab
### 2. AI Feature Usage
2.1 Text Completion:
Position cursor in editor where completion is needed
Right-click select "AI Complete" or select text and use AI panel
AI will generate completion suggestions based on context
2.2 Text Expansion:
Select text to expand
Right-click select "AI Expand"
AI will expand and improve the selected content
### 3. Keyboard Shortcuts
Shortcut	Function	
Ctrl+N	New File	
Ctrl+O	Open File	
Ctrl+Shift+O	Open Folder	
Ctrl+S	Save File	
Ctrl+Z	Undo	
Ctrl+Y	Redo	
Ctrl+X	Cut	
Ctrl+C	Copy	
Ctrl+V	Paste	
Ctrl+/	Toggle Comment	

## 🏗️ Project Structure
project/
├── frontend/                 # Frontend files
│   ├── index.html           # Main page
│   ├── styles.css           # Stylesheet
│   └── js/
│       └── app.js           # Main JavaScript logic
├── backend/                 # Backend files
│   ├── app/
│   │   └── main.py          # FastAPI main program
│   ├── requirements.txt     # Python dependencies
│   └── .env.example        # Environment variable template
└── start.sh                # Startup script

## 🛠️ Tech Stack
### Frontend
HTML5/CSS3: Responsive layout and modern UI design
JavaScript (ES6+): Native JavaScript, no framework dependencies
CodeMirror 5.x: Professional code editor component
Font Awesome: Icon library

### Backend
FastAPI: Modern Python web framework
OpenAI API: GPT models for AI features
Uvicorn: ASGI server
Pydantic: Data validation

## 🔧 Configuration Options

### Environment Variables

Configure in backend/.env file:
# OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

### Auto-save Configuration
Adjust auto-save interval in frontend code (default 30 seconds):
// Modify in app.js
this.autoSaveDelay = 30000; // 30 seconds, in milliseconds

## 🚨 Important Notes
API Key Security: Please securely store your OpenAI API Key and do not commit it to version control
Browser Compatibility: Modern browsers recommended (Chrome 88+, Firefox 78+, Safari 14+)
File System Limitations: Due to browser security restrictions, some file operations may require user confirmation
CORS Configuration: If accessing from other domains, adjust CORS settings accordingly

## 📝 Development Notes
### Adding New Language Support
Include the corresponding CodeMirror language mode in HTML
Add file type mapping in getEditorMode() method (app.js)
Add icon mapping in getFileIcon() method (app.js)

### Extending AI Features
You can modify the backend API to support more AI features:
@app.post("/api/ai/custom")
async def custom_ai_function(request: AIRequest):
    # Implement custom AI functionality
    pass
    
## 🤝 Contribution Guidelines
Issues and Pull Requests are welcome!
## 📄 License
MIT License
