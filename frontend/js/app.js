/**
 * Cursor Writing主应用程序
 */

class TextEditor {
    constructor() {
        this.files = new Map(); // 存储打开的文件
        this.currentFile = null; // 当前激活文件
        this.editor = null; // CodeMirror 实例
        this.fileTree = null; // 文件树数据
        this.autoSaveInterval = null; // 自动保存定时器
        this.autoSaveEnabled = false; // 默认关闭自动保存
        this.autoSaveDelay = 30000; // 30秒
        this.nextAutoSave = 0;
        
        this.init();
    }

    init() {
        this.setupEditor();
        this.setupEventListeners();
        this.setupMenus();
        this.setupContextMenus();
        this.setupDragDrop();
        this.startAutoSaveTimer();
        this.updateStatusBar();
    }

    // 初始化CodeMirror编辑器
    setupEditor() {
        const editorContainer = document.createElement('div');
        editorContainer.id = 'codemirror-container';
        document.getElementById('editor-main').appendChild(editorContainer);
        
        this.editor = CodeMirror(editorContainer, {
            value: '',
            mode: 'text/plain',
            theme: 'default',
            lineNumbers: true,
            lineWrapping: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            indentUnit: 4,
            indentWithTabs: false,
            styleActiveLine: true,
            foldGutter: true,
            gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
            extraKeys: {
                "Ctrl-S": () => this.saveFile(),
                "Ctrl-N": () => this.newFile(),
                "Ctrl-O": () => this.openFile(),
                "Ctrl-Shift-O": () => this.openFolder(),
                "Ctrl-Z": () => this.editor.undo(),
                "Ctrl-Y": () => this.editor.redo(),
                "Ctrl-/": () => this.toggleComment(),
                "Tab": (cm) => {
                    if (cm.somethingSelected()) {
                        cm.indentSelection("add");
                    } else {
                        cm.replaceSelection(cm.getOption("indentWithTabs") ? "\t" : Array(cm.getOption("indentUnit") + 1).join(" "));
                    }
                }
            }
        });

        // 编辑器事件监听
        this.editor.on('change', () => {
            if (this.currentFile) {
                this.markFileDirty(this.currentFile);
                this.updateStatusBar();
            }
        });

        this.editor.on('cursorActivity', () => {
            this.updateStatusBar();
        });

        this.hideEditor();
    }

    // 设置事件监听器
    setupEventListeners() {
        // 文件操作按钮
        document.getElementById('file-input').addEventListener('change', (e) => this.handleFileSelect(e));
        document.getElementById('folder-input').addEventListener('change', (e) => this.handleFolderSelect(e));
        
        // 欢迎屏幕按钮
        document.querySelectorAll('.welcome-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleAction(action);
            });
        });

        // AI面板相关
        document.getElementById('close-ai-panel').addEventListener('click', () => {
            this.closeAIPanel();
        });

        document.querySelectorAll('.ai-mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectAIMode(e.target.dataset.mode);
            });
        });

        document.getElementById('generate-ai-content').addEventListener('click', () => {
            this.generateAIContent();
        });

        document.getElementById('apply-ai-result').addEventListener('click', () => {
            this.applyAIResult();
        });

        document.getElementById('copy-ai-result').addEventListener('click', () => {
            this.copyAIResult();
        });

        // 标签页相关
        document.getElementById('close-all-tabs').addEventListener('click', () => {
            this.closeAllTabs();
        });

        // 文件树相关
        document.getElementById('refresh-tree').addEventListener('click', () => {
            this.refreshFileTree();
        });

        document.getElementById('collapse-tree').addEventListener('click', () => {
            this.collapseFileTree();
        });

        // 窗口事件
        window.addEventListener('beforeunload', (e) => {
            const dirtyFiles = Array.from(this.files.values()).filter(f => f.isDirty);
            if (dirtyFiles.length > 0) {
                e.preventDefault();
                return '您有未保存的文件，确定要离开吗？';
            }
        });

        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcut(e);
        });
    }

    // 设置菜单系统
    setupMenus() {
        const menuItems = document.querySelectorAll('.menu-item');
        
        menuItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleDropdown(item);
            });
        });

        // 下拉菜单项点击事件
        document.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = item.dataset.action;
                this.handleAction(action);
                this.hideAllDropdowns();
            });
        });

        // 点击其他地方关闭菜单
        document.addEventListener('click', () => {
            this.hideAllDropdowns();
        });
    }

    // 设置右键菜单
    setupContextMenus() {
        // 编辑器右键菜单
        document.getElementById('editor-main').addEventListener('contextmenu', (e) => {
            e.preventDefault();
            if (this.editor && this.currentFile) {
                this.showContextMenu(e, 'context-menu');
            }
        });

        // 文件树右键菜单
        document.getElementById('file-tree').addEventListener('contextmenu', (e) => {
            e.preventDefault();
            const fileItem = e.target.closest('.file-tree-item');
            if (fileItem) {
                this.showContextMenu(e, 'file-tree-context-menu', fileItem);
            }
        });

        // 右键菜单项点击
        document.querySelectorAll('.context-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const action = item.dataset.action;
                this.handleContextAction(action, e);
                this.hideContextMenu();
            });
        });

        // 点击其他地方关闭右键菜单
        document.addEventListener('click', () => {
            this.hideContextMenu();
        });
    }

    // 设置拖拽功能
    setupDragDrop() {
        const dropZone = document.querySelector('.app-container');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-over');
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const files = Array.from(e.dataTransfer.files);
            files.forEach(file => this.openFileFromDrop(file));
        });
    }

    // 处理动作
    handleAction(action) {
        switch (action) {
            case 'new-file':
                this.newFile();
                break;
            case 'open-file':
                this.openFile();
                break;
            case 'open-folder':
                this.openFolder();
                break;
            case 'save':
                this.saveFile();
                break;
            case 'save-as':
                this.saveAsFile();
                break;
            case 'close':
                this.closeCurrentFile();
                break;
            case 'toggle-autosave':
                this.toggleAutoSave();
                break;
            case 'undo':
                this.editor?.undo();
                break;
            case 'redo':
                this.editor?.redo();
                break;
            case 'cut':
                this.cutText();
                break;
            case 'copy':
                this.copyText();
                break;
            case 'paste':
                this.pasteText();
                break;
            case 'format':
                this.formatCode();
                break;
            case 'shortcuts':
                this.showShortcuts();
                break;
            case 'about':
                this.showAbout();
                break;
        }
    }

    // 处理右键菜单动作
    handleContextAction(action, event) {
        switch (action) {
            case 'ai-complete':
                this.openAIPanel('complete');
                break;
            case 'ai-expand':
                this.openAIPanel('expand');
                break;
            case 'cut':
            case 'copy':
            case 'paste':
                this.handleAction(action);
                break;
            case 'open-file':
                // 文件树右键打开文件
                const fileItem = event.target.closest('.file-tree-item');
                if (fileItem) {
                    this.openFileFromTree(fileItem);
                }
                break;
            case 'rename-file':
                // 实现文件重命名
                const renameItem = event.target.closest('.file-tree-item');
                if (renameItem) {
                    this.renameFileInTree(renameItem);
                }
                break;
            case 'delete-file':
                // 实现文件删除
                const deleteItem = event.target.closest('.file-tree-item');
                if (deleteItem) {
                    this.deleteFileFromTree(deleteItem);
                }
                break;
        }
    }

    // 新建文件
    newFile() {
        const fileName = `新建文件${this.files.size + 1}.txt`;
        const fileId = `new-${Date.now()}`;
        
        const fileInfo = {
            id: fileId,
            name: fileName,
            content: '',
            isDirty: false,
            isNew: true,
            path: null,
            type: 'text/plain'
        };

        this.files.set(fileId, fileInfo);
        this.createTab(fileInfo);
        this.switchToFile(fileId);
        this.showEditor();
        this.showNotification('新建文件成功', 'success');
    }

    // 打开文件
    async openFile() {
        if ('showOpenFilePicker' in window) {
            // 使用File System Access API
            try {
                const [fileHandle] = await window.showOpenFilePicker({
                    multiple: false,
                    types: [
                        {
                            description: '文本文件',
                            accept: {
                                'text/*': ['.txt', '.js', '.html', '.css', '.json', '.md', '.py', '.xml', '.yml', '.yaml']
                            }
                        }
                    ]
                });
                
                const file = await fileHandle.getFile();
                await this.loadFileWithHandle(file, fileHandle);
                
            } catch (error) {
                if (error.name !== 'AbortError') {
                    this.showNotification('打开文件失败', 'error');
                }
            }
        } else {
            // 降级到传统文件输入
            document.getElementById('file-input').click();
        }
    }

    // 使用fileHandle加载文件
    async loadFileWithHandle(file, fileHandle) {
        try {
            // 检查文件是否已经打开
            const existingFile = this.findFileByPath(file.name);
            if (existingFile) {
                this.switchToFile(existingFile.id);
                this.showNotification(`文件 "${file.name}" 已经打开`, 'warning');
                return;
            }

            const fileId = `file-${Date.now()}-${Math.random()}`;
            const content = await file.text();
            const fileInfo = {
                id: fileId,
                name: file.name,
                content: content,
                isDirty: false,
                isNew: false,
                path: file.name,
                type: this.getFileType(file.name),
                file: file,
                fileHandle: fileHandle // 保存fileHandle以便后续保存
            };

            this.files.set(fileId, fileInfo);
            this.createTab(fileInfo);
            this.switchToFile(fileId);
            this.showEditor();
            this.showNotification(`文件 "${file.name}" 加载成功`, 'success');
        } catch (error) {
            this.showNotification(`加载文件失败: ${error.message}`, 'error');
        }
    }

    // 打开文件夹
    openFolder() {
        document.getElementById('folder-input').click();
    }

    // 处理文件选择
    handleFileSelect(event) {
        const files = Array.from(event.target.files);
        files.forEach(file => this.loadFile(file));
        event.target.value = ''; // 清空选择
    }

    // 处理文件夹选择
    handleFolderSelect(event) {
        const files = Array.from(event.target.files);
        this.buildFileTree(files);
        event.target.value = ''; // 清空选择
    }

    // 加载文件
    async loadFile(file) {
        try {
            // 检查文件是否已经打开
            const existingFile = this.findFileByPath(file.webkitRelativePath || file.name);
            if (existingFile) {
                // 文件已经打开，切换到该标签
                this.switchToFile(existingFile.id);
                this.showNotification(`文件 "${file.name}" 已经打开`, 'warning');
                return;
            }

            const fileId = `file-${Date.now()}-${Math.random()}`;
            const content = await this.readFileContent(file);
            const fileInfo = {
                id: fileId,
                name: file.name,
                content: content,
                isDirty: false,
                isNew: false,
                path: file.webkitRelativePath || file.name,
                type: this.getFileType(file.name),
                file: file
            };

            this.files.set(fileId, fileInfo);
            this.createTab(fileInfo);
            this.switchToFile(fileId);
            this.showEditor();
            this.showNotification(`文件 "${file.name}" 加载成功`, 'success');
        } catch (error) {
            this.showNotification(`加载文件失败: ${error.message}`, 'error');
        }
    }

    // 根据路径查找文件
    findFileByPath(path) {
        for (const fileInfo of this.files.values()) {
            if (fileInfo.path === path) {
                return fileInfo;
            }
        }
        return null;
    }

    // 从拖拽打开文件
    async openFileFromDrop(file) {
        if (file.type.startsWith('text/') || this.isTextFile(file.name)) {
            await this.loadFile(file);
        } else {
            this.showNotification(`不支持的文件类型: ${file.name}`, 'warning');
        }
    }

    // 读取文件内容
    readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('文件读取失败'));
            reader.readAsText(file);
        });
    }

    // 保存文件
    async saveFile() {
        if (!this.currentFile) {
            this.showNotification('没有打开的文件', 'warning');
            return;
        }

        const fileInfo = this.files.get(this.currentFile);
        
        if (fileInfo.isNew || !fileInfo.fileHandle) {
            this.saveAsFile();
            return;
        }

        try {
            const content = this.editor.getValue();
            
            // 尝试使用File System Access API保存到原文件
            if (fileInfo.fileHandle && 'createWritable' in fileInfo.fileHandle) {
                const writable = await fileInfo.fileHandle.createWritable();
                await writable.write(content);
                await writable.close();
                
                // 获取更新后的文件对象
                const updatedFile = await fileInfo.fileHandle.getFile();
                
                fileInfo.content = content;
                fileInfo.isDirty = false;
                fileInfo.file = updatedFile; // 更新文件对象
                
                // 更新文件树中的文件引用（名称相同但文件对象需要更新）
                this.updateFileTreeReference(fileInfo.name, fileInfo.name, updatedFile);
                
                this.updateTab(fileInfo);
                this.updateStatusBar();
                
                this.showNotification(`文件 "${fileInfo.name}" 保存成功`, 'success');
            } else {
                // 降级方案：提示用户下载更新的文件
                this.showNotification('浏览器不支持直接保存，将下载更新的文件', 'warning');
                this.downloadFile(fileInfo.name, content);
                
                // 标记为已保存（虽然是下载方式）
                fileInfo.content = content;
                fileInfo.isDirty = false;
                this.updateTab(fileInfo);
                this.updateStatusBar();
            }
        } catch (error) {
            console.error('Save error:', error);
            this.showNotification(`保存失败: ${error.message}`, 'error');
        }
    }

    // 下载文件
    downloadFile(filename, content) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // 另存为
    async saveAsFile() {
        if (!this.currentFile) {
            this.showNotification('没有打开的文件', 'warning');
            return;
        }

        const fileInfo = this.files.get(this.currentFile);
        const content = this.editor.getValue();
        
        if ('showSaveFilePicker' in window) {
            try {
                const fileHandle = await window.showSaveFilePicker({
                    suggestedName: fileInfo.name,
                    types: [
                        {
                            description: '文本文件',
                            accept: {
                                'text/*': ['.txt', '.js', '.html', '.css', '.json', '.md', '.py', '.xml', '.yml', '.yaml']
                            }
                        }
                    ]
                });
                
                const writable = await fileHandle.createWritable();
                await writable.write(content);
                await writable.close();
                
                // 获取新的文件对象
                const newFile = await fileHandle.getFile();
                
                // 更新文件信息
                const oldName = fileInfo.name;
                fileInfo.name = fileHandle.name || fileInfo.name;
                fileInfo.content = content;
                fileInfo.isDirty = false;
                fileInfo.isNew = false;
                fileInfo.fileHandle = fileHandle;
                fileInfo.file = newFile; // 更新文件对象
                fileInfo.path = fileInfo.name;
                
                // 更新文件树中的文件引用
                this.updateFileTreeReference(oldName, fileInfo.name, newFile);
                
                this.updateTab(fileInfo);
                this.updateStatusBar();
                this.showNotification(`文件另存为 "${fileInfo.name}" 成功`, 'success');
                
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error('Save as error:', error);
                    this.showNotification(`另存为失败: ${error.message}`, 'error');
                }
            }
        } else {
            // 降级方案：下载文件
            this.downloadFile(fileInfo.name, content);
            
            // 更新文件状态
            fileInfo.isDirty = false;
            fileInfo.isNew = false;
            this.updateTab(fileInfo);
            this.updateStatusBar();
            
            this.showNotification(`文件 "${fileInfo.name}" 已下载`, 'success');
        }
    }

    // 关闭当前文件
    closeCurrentFile() {
        if (!this.currentFile) return;
        
        const fileInfo = this.files.get(this.currentFile);
        
        if (fileInfo.isDirty) {
            const result = confirm(`文件 "${fileInfo.name}" 有未保存的更改。\n\n点击"确定"保存并关闭\n点击"取消"直接关闭（不保存）\n关闭此对话框则取消关闭操作`);
            
            if (result === true) {
                // 用户选择保存并关闭
                if (fileInfo.isNew || !fileInfo.fileHandle) {
                    // 新文件需要另存为
                    this.saveAsFile().then(() => {
                        this.closeFile(this.currentFile);
                    }).catch((error) => {
                        if (error.name !== 'AbortError') {
                            console.error('Save failed:', error);
                        }
                    });
                } else {
                    // 已有文件直接保存
                    this.saveFile().then(() => {
                        this.closeFile(this.currentFile);
                    }).catch((error) => {
                        console.error('Save failed:', error);
                        // 保存失败也继续关闭
                        this.closeFile(this.currentFile);
                    });
                }
                return;
            } else if (result === false) {
                // 用户选择直接关闭（不保存）
                this.closeFile(this.currentFile);
                return;
            }
            // result为null表示用户取消了操作，不执行任何操作
            return;
        }

        // 文件没有未保存的更改，直接关闭
        this.closeFile(this.currentFile);
    }

    // 带提示的关闭文件
    closeFileWithPrompt(fileId) {
        const fileInfo = this.files.get(fileId);
        if (!fileInfo) return;
        
        if (fileInfo.isDirty) {
            const result = confirm(`文件 "${fileInfo.name}" 有未保存的更改。\n\n点击"确定"保存并关闭\n点击"取消"直接关闭（不保存）\n关闭此对话框则取消关闭操作`);
            
            if (result === true) {
                // 用户选择保存并关闭
                const originalCurrentFile = this.currentFile;
                this.currentFile = fileId; // 临时切换到要关闭的文件
                
                if (fileInfo.isNew || !fileInfo.fileHandle) {
                    // 新文件需要另存为
                    this.saveAsFile().then(() => {
                        this.closeFile(fileId);
                        if (originalCurrentFile && originalCurrentFile !== fileId) {
                            this.switchToFile(originalCurrentFile);
                        }
                    }).catch((error) => {
                        if (error.name !== 'AbortError') {
                            console.error('Save failed:', error);
                        }
                        this.currentFile = originalCurrentFile; // 恢复原来的当前文件
                    });
                } else {
                    // 已有文件直接保存
                    this.saveFile().then(() => {
                        this.closeFile(fileId);
                        if (originalCurrentFile && originalCurrentFile !== fileId) {
                            this.switchToFile(originalCurrentFile);
                        }
                    }).catch((error) => {
                        console.error('Save failed:', error);
                        // 保存失败也继续关闭
                        this.closeFile(fileId);
                        if (originalCurrentFile && originalCurrentFile !== fileId) {
                            this.switchToFile(originalCurrentFile);
                        }
                    });
                }
                return;
            } else if (result === false) {
                // 用户选择直接关闭（不保存）
                this.closeFile(fileId);
                return;
            }
            // result为null表示用户取消了操作，不执行任何操作
            return;
        }

        // 文件没有未保存的更改，直接关闭
        this.closeFile(fileId);
    }

    // 关闭文件
    closeFile(fileId) {
        const fileInfo = this.files.get(fileId);
        if (!fileInfo) return;

        // 移除标签
        const tab = document.querySelector(`[data-file-id="${fileId}"]`);
        if (tab) {
            tab.remove();
        }

        // 从文件列表中移除
        this.files.delete(fileId);

        // 如果是当前文件，切换到其他文件
        if (this.currentFile === fileId) {
            const remainingFiles = Array.from(this.files.keys());
            if (remainingFiles.length > 0) {
                this.switchToFile(remainingFiles[0]);
            } else {
                this.currentFile = null;
                this.hideEditor();
                this.updateStatusBar();
            }
        }
    }

    // 关闭所有标签
    closeAllTabs() {
        const dirtyFiles = Array.from(this.files.values()).filter(f => f.isDirty);
        
        if (dirtyFiles.length > 0) {
            const fileNames = dirtyFiles.map(f => f.name).join(', ');
            if (!confirm(`以下文件有未保存的更改：${fileNames}\n\n确定要关闭所有标签吗？`)) {
                return;
            }
        }

        // 清空所有文件和标签
        this.files.clear();
        document.getElementById('tabs').innerHTML = '';
        this.currentFile = null;
        this.hideEditor();
        this.updateStatusBar();
        this.showNotification('所有标签已关闭', 'success');
    }

    // 创建标签
    createTab(fileInfo) {
        const tabsContainer = document.getElementById('tabs');
        
        const tab = document.createElement('div');
        tab.className = 'tab';
        tab.dataset.fileId = fileInfo.id;
        
        tab.innerHTML = `
            <span class="tab-name">${fileInfo.name}</span>
            <span class="tab-dirty" style="display: none;">●</span>
            <button class="tab-close" title="关闭">
                <i class="fas fa-times"></i>
            </button>
        `;

        // 标签点击事件
        tab.addEventListener('click', (e) => {
            if (!e.target.closest('.tab-close')) {
                this.switchToFile(fileInfo.id);
            }
        });

        // 关闭按钮事件
        tab.querySelector('.tab-close').addEventListener('click', (e) => {
            e.stopPropagation();
            this.closeFileWithPrompt(fileInfo.id);
        });

        tabsContainer.appendChild(tab);
    }

    // 切换到文件
    switchToFile(fileId) {
        const fileInfo = this.files.get(fileId);
        if (!fileInfo) return;

        this.currentFile = fileId;

        // 更新编辑器内容
        this.editor.setValue(fileInfo.content);
        this.editor.setOption('mode', this.getEditorMode(fileInfo.type));

        // 更新标签状态
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.fileId === fileId);
        });

        this.showEditor();
        this.updateStatusBar();
        this.editor.focus();
    }

    // 标记文件为已修改
    markFileDirty(fileId) {
        const fileInfo = this.files.get(fileId);
        if (!fileInfo) return;

        fileInfo.isDirty = true;
        fileInfo.content = this.editor.getValue();
        this.updateTab(fileInfo);
    }

    // 更新标签显示
    updateTab(fileInfo) {
        const tab = document.querySelector(`[data-file-id="${fileInfo.id}"]`);
        if (!tab) return;

        const dirtyIndicator = tab.querySelector('.tab-dirty');
        dirtyIndicator.style.display = fileInfo.isDirty ? 'inline' : 'none';
    }

    // 显示/隐藏编辑器
    showEditor() {
        document.getElementById('welcome-screen').style.display = 'none';
        document.getElementById('codemirror-container').style.display = 'block';
        this.editor.refresh();
    }

    hideEditor() {
        document.getElementById('welcome-screen').style.display = 'flex';
        document.getElementById('codemirror-container').style.display = 'none';
    }

    // AI面板相关方法
    openAIPanel(mode) {
        const panel = document.getElementById('ai-panel');
        panel.classList.add('open');

        // 设置AI模式
        this.selectAIMode(mode);

        // 获取选中的文本
        const selectedText = this.editor ? this.editor.getSelection() : '';
        document.getElementById('text-preview').textContent = selectedText || '(未选择文本)';
    }

    closeAIPanel() {
        document.getElementById('ai-panel').classList.remove('open');
    }

    selectAIMode(mode) {
        document.querySelectorAll('.ai-mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });
    }

    async generateAIContent() {
        const selectedText = this.editor.getSelection();
        const mode = document.querySelector('.ai-mode-btn.active').dataset.mode;
        
        if (!selectedText && mode === 'expand') {
            this.showNotification('请先选择要扩写的文本', 'warning');
            return;
        }

        const generateBtn = document.getElementById('generate-ai-content');
        const originalText = generateBtn.textContent;
        
        try {
            generateBtn.textContent = '生成中...';
            generateBtn.disabled = true;

            const response = await fetch('/api/ai/' + mode, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: selectedText,
                    context: this.editor.getValue()
                })
            });

            if (!response.ok) {
                throw new Error('AI服务请求失败');
            }

            const result = await response.json();
            document.getElementById('ai-result-content').textContent = result.content;
            this.showNotification('AI内容生成成功', 'success');

        } catch (error) {
            this.showNotification(`AI生成失败: ${error.message}`, 'error');
        } finally {
            generateBtn.textContent = originalText;
            generateBtn.disabled = false;
        }
    }

    applyAIResult() {
        const aiContent = document.getElementById('ai-result-content').textContent;
        if (!aiContent) {
            this.showNotification('没有可应用的AI内容', 'warning');
            return;
        }

        const mode = document.querySelector('.ai-mode-btn.active').dataset.mode;
        
        if (mode === 'complete') {
            // 文本补全：在选中文本之后插入内容（不替换选中文本）
            const selectedText = this.editor.getSelection();
            const cursor = this.editor.getCursor();
            
            if (selectedText) {
                // 如果有选中文本，在选中文本后插入补全内容
                const doc = this.editor.getDoc();
                const startPos = doc.getCursor('start');
                const endPos = doc.getCursor('end');
                
                // 在选中文本的结尾位置插入补全内容
                doc.replaceRange(selectedText + aiContent, startPos, endPos);
                
                // 将光标设置到插入内容的末尾
                const newEndPos = {
                    line: endPos.line,
                    ch: endPos.ch + aiContent.length
                };
                doc.setCursor(newEndPos);
            } else {
                // 如果没有选中文本，直接在光标位置插入
                this.editor.replaceSelection(aiContent);
            }
        } else if (mode === 'expand') {
            // 文本扩写：替换选中的内容
            const selectedText = this.editor.getSelection();
            if (selectedText) {
                this.editor.replaceSelection(aiContent);
            } else {
                this.editor.replaceSelection(aiContent);
            }
        }

        this.showNotification('AI内容已应用', 'success');
        this.closeAIPanel();
    }

    copyAIResult() {
        const aiContent = document.getElementById('ai-result-content').textContent;
        if (!aiContent) {
            this.showNotification('没有可复制的内容', 'warning');
            return;
        }

        navigator.clipboard.writeText(aiContent).then(() => {
            this.showNotification('内容已复制到剪贴板', 'success');
        }).catch(() => {
            this.showNotification('复制失败', 'error');
        });
    }

    // 文件树相关方法
    buildFileTree(files) {
        const tree = {};
        
        files.forEach(file => {
            const pathParts = file.webkitRelativePath.split('/');
            let current = tree;
            
            pathParts.forEach((part, index) => {
                if (!current[part]) {
                    current[part] = {
                        name: part,
                        type: index === pathParts.length - 1 ? 'file' : 'folder',
                        children: {},
                        file: index === pathParts.length - 1 ? file : null
                    };
                }
                current = current[part].children;
            });
        });

        this.fileTree = tree;
        this.renderFileTree();
        this.showNotification('文件夹加载成功', 'success');
    }

    renderFileTree() {
        const container = document.getElementById('file-tree');
        container.innerHTML = '';
        
        if (!this.fileTree || Object.keys(this.fileTree).length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <p>打开文件夹以查看文件</p>
                </div>
            `;
            return;
        }

        const renderNode = (node, container, level = 0) => {
            const item = document.createElement('div');
            item.className = `file-tree-item ${node.type}`;
            item.style.paddingLeft = `${level * 16 + 16}px`;
            
            const icon = node.type === 'folder' ? 
                (level === 0 ? 'fas fa-folder' : 'fas fa-angle-right') : 
                this.getFileIcon(node.name);
                
            item.innerHTML = `
                ${node.type === 'folder' && level > 0 ? '<i class="fas fa-angle-right expand-icon"></i>' : ''}
                <i class="${icon}"></i>
                <span>${node.name}</span>
            `;

            if (node.type === 'file') {
                item.addEventListener('click', () => this.loadFile(node.file));
            } else {
                item.addEventListener('click', () => this.toggleFolder(item, node));
            }

            container.appendChild(item);

            if (node.type === 'folder') {
                const childContainer = document.createElement('div');
                childContainer.className = 'folder-children';
                childContainer.style.display = level === 0 ? 'block' : 'none';
                
                Object.values(node.children).forEach(child => {
                    renderNode(child, childContainer, level + 1);
                });
                
                container.appendChild(childContainer);
            }
        };

        Object.values(this.fileTree).forEach(node => {
            renderNode(node, container);
        });
    }

    toggleFolder(item, node) {
        const expandIcon = item.querySelector('.expand-icon');
        const childContainer = item.nextElementSibling;
        
        if (childContainer && childContainer.classList.contains('folder-children')) {
            const isExpanded = childContainer.style.display === 'block';
            childContainer.style.display = isExpanded ? 'none' : 'block';
            if (expandIcon) {
                expandIcon.classList.toggle('expanded', !isExpanded);
            }
        }
    }

    refreshFileTree() {
        if (this.fileTree) {
            this.renderFileTree();
            this.showNotification('文件树已刷新', 'success');
        }
    }

    collapseFileTree() {
        document.querySelectorAll('.folder-children').forEach(folder => {
            folder.style.display = 'none';
        });
        document.querySelectorAll('.expand-icon').forEach(icon => {
            icon.classList.remove('expanded');
        });
        this.showNotification('文件树已折叠', 'success');
    }

    // 从文件树打开文件
    openFileFromTree(fileItem) {
        const fileName = fileItem.querySelector('span').textContent;
        const filePath = this.getFilePathFromTreeItem(fileItem);
        
        // 在文件树数据中查找对应的文件
        const fileNode = this.findFileNodeByPath(filePath);
        if (fileNode && fileNode.file) {
            this.loadFile(fileNode.file);
        } else {
            this.showNotification(`无法打开文件: ${fileName}`, 'error');
        }
    }

    // 重命名文件树中的文件
    renameFileInTree(fileItem) {
        const currentName = fileItem.querySelector('span').textContent;
        const isFolder = fileItem.classList.contains('folder');
        
        if (isFolder) {
            this.showNotification('浏览器环境下无法重命名文件夹', 'warning');
            return;
        }
        
        const newName = prompt(`重命名文件:`, currentName);
        
        if (!newName || newName === currentName) {
            return;
        }

        // 检查新名称是否有效
        if (!/^[^<>:"/\\|?*]+$/.test(newName)) {
            this.showNotification('文件名包含非法字符', 'error');
            return;
        }

        // 检查文件是否已经在编辑器中打开
        const filePath = this.getFilePathFromTreeItem(fileItem);
        const openedFile = this.findFileByPath(filePath);
        
        if (openedFile) {
            // 更新已打开文件的信息
            openedFile.name = newName;
            openedFile.path = newName;
            this.files.set(openedFile.id, openedFile);
            this.updateTab(openedFile);
        }

        // 更新显示的名称
        fileItem.querySelector('span').textContent = newName;
        
        // 更新文件树数据结构中的名称
        this.updateFileTreeNodeName(filePath, currentName, newName);
        
        this.showNotification(`文件重命名为 "${newName}"（仅在编辑器中生效）`, 'success');
    }

    // 从文件树删除文件
    deleteFileFromTree(fileItem) {
        const fileName = fileItem.querySelector('span').textContent;
        const isFolder = fileItem.classList.contains('folder');
        const itemType = isFolder ? '文件夹' : '文件';
        
        if (!confirm(`确定要从编辑器中删除${itemType} "${fileName}" 吗？\n注意：这只会从编辑器中移除，不会删除实际文件。`)) {
            return;
        }

        // 如果是已打开的文件，先关闭它
        if (!isFolder) {
            const filePath = this.getFilePathFromTreeItem(fileItem);
            const openedFile = this.findFileByPath(filePath);
            if (openedFile) {
                this.closeFile(openedFile.id);
            }
        }

        // 从DOM中移除
        const nextSibling = fileItem.nextElementSibling;
        if (nextSibling && nextSibling.classList.contains('folder-children')) {
            nextSibling.remove(); // 移除文件夹的子内容
        }
        fileItem.remove();

        // 从文件树数据结构中移除
        const filePath = this.getFilePathFromTreeItem(fileItem);
        this.removeFileTreeNode(filePath);
        
        this.showNotification(`${itemType} "${fileName}" 已从编辑器中移除`, 'success');
    }

    // 获取文件树项目的完整路径
    getFilePathFromTreeItem(item) {
        const pathParts = [];
        let currentItem = item;
        
        while (currentItem && currentItem.classList.contains('file-tree-item')) {
            const name = currentItem.querySelector('span').textContent;
            pathParts.unshift(name);
            
            // 向上查找父级文件夹
            let parent = currentItem.previousElementSibling;
            while (parent && (!parent.classList.contains('file-tree-item') || 
                   parent.style.paddingLeft >= currentItem.style.paddingLeft)) {
                parent = parent.previousElementSibling;
            }
            
            currentItem = parent;
        }
        
        return pathParts.join('/');
    }

    // 在文件树数据中查找文件节点
    findFileNodeByPath(path) {
        const parts = path.split('/');
        let current = this.fileTree;
        
        for (const part of parts) {
            if (current[part]) {
                current = current[part];
                if (current.type === 'file') {
                    return current;
                } else {
                    current = current.children;
                }
            } else {
                return null;
            }
        }
        
        return current;
    }

    // 更新文件树节点名称
    updateFileTreeNodeName(path, oldName, newName) {
        const parts = path.split('/');
        let current = this.fileTree;
        
        // 导航到父级
        for (let i = 0; i < parts.length - 1; i++) {
            if (current[parts[i]]) {
                current = current[parts[i]].children;
            }
        }
        
        // 重命名节点
        if (current[oldName]) {
            current[newName] = current[oldName];
            current[newName].name = newName;
            delete current[oldName];
        }
    }

    // 从文件树数据中移除节点
    removeFileTreeNode(path) {
        const parts = path.split('/');
        let current = this.fileTree;
        
        // 导航到父级
        for (let i = 0; i < parts.length - 1; i++) {
            if (current[parts[i]]) {
                current = current[parts[i]].children;
            }
        }
        
        // 删除节点
        const fileName = parts[parts.length - 1];
        if (current[fileName]) {
            delete current[fileName];
        }
    }

    // 更新文件树中的文件引用
    updateFileTreeReference(oldName, newName, newFile) {
        const updateNodeFile = (node) => {
            if (node.type === 'file' && node.name === oldName) {
                node.name = newName;
                node.file = newFile;
                return true;
            } else if (node.children) {
                for (const childName in node.children) {
                    if (updateNodeFile(node.children[childName])) {
                        // 如果名称变了，需要重新组织树结构
                        if (oldName !== newName) {
                            node.children[newName] = node.children[oldName];
                            delete node.children[oldName];
                        }
                        return true;
                    }
                }
            }
            return false;
        };
        
        // 从根节点开始更新
        for (const rootName in this.fileTree) {
            if (updateNodeFile(this.fileTree[rootName])) {
                if (oldName !== newName && this.fileTree[oldName]) {
                    this.fileTree[newName] = this.fileTree[oldName];
                    delete this.fileTree[oldName];
                }
                // 重新渲染文件树
                this.renderFileTree();
                break;
            }
        }
    }

    // 工具方法
    getFileType(fileName) {
        const ext = fileName.split('.').pop().toLowerCase();
        const types = {
            'js': 'text/javascript',
            'html': 'text/html',
            'css': 'text/css',
            'json': 'application/json',
            'md': 'text/x-markdown',
            'py': 'text/x-python',
            'txt': 'text/plain'
        };
        return types[ext] || 'text/plain';
    }

    getEditorMode(fileType) {
        const modes = {
            'text/javascript': 'javascript',
            'text/html': 'xml',
            'text/css': 'css',
            'application/json': 'javascript',
            'text/x-markdown': 'markdown',
            'text/x-python': 'python'
        };
        return modes[fileType] || 'text/plain';
    }

    getFileIcon(fileName) {
        const ext = fileName.split('.').pop().toLowerCase();
        const icons = {
            'js': 'fab fa-js-square',
            'html': 'fab fa-html5',
            'css': 'fab fa-css3-alt',
            'json': 'fas fa-code',
            'md': 'fab fa-markdown',
            'py': 'fab fa-python',
            'txt': 'fas fa-file-alt'
        };
        return icons[ext] || 'fas fa-file';
    }

    isTextFile(fileName) {
        const textExts = ['txt', 'js', 'html', 'css', 'json', 'md', 'py', 'xml', 'yml', 'yaml'];
        const ext = fileName.split('.').pop().toLowerCase();
        return textExts.includes(ext);
    }

    // 菜单相关方法
    toggleDropdown(menuItem) {
        const dropdown = menuItem.querySelector('.dropdown-menu');
        const isVisible = dropdown.classList.contains('show');
        
        this.hideAllDropdowns();
        
        if (!isVisible) {
            dropdown.classList.add('show');
            menuItem.classList.add('active');
        }
    }

    hideAllDropdowns() {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.classList.remove('show');
        });
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
    }

    showContextMenu(event, menuId, data = null) {
        const menu = document.getElementById(menuId);
        menu.classList.add('show');
        menu.style.left = event.pageX + 'px';
        menu.style.top = event.pageY + 'px';
        
        if (data) {
            menu.dataset.contextData = JSON.stringify(data);
        }
    }

    hideContextMenu() {
        document.querySelectorAll('.context-menu').forEach(menu => {
            menu.classList.remove('show');
        });
    }

    // 键盘快捷键处理
    handleKeyboardShortcut(event) {
        const { ctrlKey, shiftKey, key } = event;
        
        if (ctrlKey && !shiftKey && key === 's') {
            event.preventDefault();
            this.saveFile();
        } else if (ctrlKey && !shiftKey && key === 'n') {
            event.preventDefault();
            this.newFile();
        } else if (ctrlKey && !shiftKey && key === 'o') {
            event.preventDefault();
            this.openFile();
        } else if (ctrlKey && shiftKey && key === 'O') {
            event.preventDefault();
            this.openFolder();
        }
    }

    // 自动保存
    startAutoSaveTimer() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }

        // 初始化倒计时
        this.nextAutoSave = this.autoSaveDelay / 1000;

        this.autoSaveInterval = setInterval(() => {
            this.nextAutoSave = Math.max(0, this.nextAutoSave - 1);
            
            // 检查是否需要自动保存
            if (this.nextAutoSave === 0) {
                if (this.autoSaveEnabled) {
                    this.autoSaveAllFiles();
                }
                // 重置倒计时
                this.nextAutoSave = this.autoSaveDelay / 1000;
            }
            
            this.updateAutoSaveTimer();
        }, 1000);
    }

    // 自动保存所有文件
    async autoSaveAllFiles() {
        const filesToSave = [];
        
        // 收集需要保存的文件
        for (const [fileId, fileInfo] of this.files) {
            if (fileInfo.isDirty && !fileInfo.isNew) {
                filesToSave.push(fileInfo);
            }
        }
        
        if (filesToSave.length === 0) return;

        try {
            // 更新当前编辑器内容到当前文件
            if (this.currentFile) {
                const currentFileInfo = this.files.get(this.currentFile);
                if (currentFileInfo) {
                    currentFileInfo.content = this.editor.getValue();
                }
            }

            // 保存所有需要保存的文件
            let savedCount = 0;
            for (const fileInfo of filesToSave) {
                // 在真实环境中调用保存API
                fileInfo.isDirty = false;
                this.updateTab(fileInfo);
                savedCount++;
            }
            
            // 更新状态栏
            this.updateStatusBar();
            
            // 显示一次性通知
            if (savedCount === 1) {
                this.showNotification(`自动保存: ${filesToSave[0].name}`, 'success');
                savedCount = 0;
            } else {
                this.showNotification(`自动保存: ${savedCount} 个文件`, 'success');
            }
            
            console.log(`Auto-saved ${savedCount} files:`, filesToSave.map(f => f.name));
        } catch (error) {
            console.error('Auto-save failed:', error);
            this.showNotification('自动保存失败', 'error');
        }
    }

    updateAutoSaveTimer() {
        const timerElement = document.getElementById('auto-save-timer');
        if (!timerElement) return;
        
        if (this.autoSaveEnabled) {
            // 检查是否有需要保存的文件
            const hasUnsavedFiles = Array.from(this.files.values()).some(f => f.isDirty && !f.isNew);
            
            if (hasUnsavedFiles) {
                timerElement.textContent = `下次保存: ${this.nextAutoSave}s`;
            } else {
                timerElement.textContent = '自动保存: 无需保存';
            }
        } else {
            timerElement.textContent = '自动保存已禁用';
        }
    }

    // 状态栏更新
    updateStatusBar() {
        const fileTypeEl = document.getElementById('file-type');
        const cursorPosEl = document.getElementById('cursor-position');
        const saveStatusEl = document.getElementById('save-status');

        if (this.currentFile && this.editor) {
            const fileInfo = this.files.get(this.currentFile);
            const cursor = this.editor.getCursor();
            
            fileTypeEl.textContent = this.getFileTypeName(fileInfo.type);
            cursorPosEl.textContent = `行 ${cursor.line + 1}, 列 ${cursor.ch + 1}`;
            saveStatusEl.textContent = fileInfo.isDirty ? '未保存' : '已保存';
        } else {
            fileTypeEl.textContent = 'Plain Text';
            cursorPosEl.textContent = '行 1, 列 1';
            saveStatusEl.textContent = '已保存';
        }
    }

    getFileTypeName(type) {
        const names = {
            'text/javascript': 'JavaScript',
            'text/html': 'HTML',
            'text/css': 'CSS',
            'application/json': 'JSON',
            'text/x-markdown': 'Markdown',
            'text/x-python': 'Python'
        };
        return names[type] || 'Plain Text';
    }

    // 剪贴板操作方法
    async cutText() {
        if (!this.editor) return;
        
        const selectedText = this.editor.getSelection();
        if (selectedText) {
            try {
                await navigator.clipboard.writeText(selectedText);
                this.editor.replaceSelection('');
                this.showNotification('文本已剪切到剪贴板', 'success');
            } catch (error) {
                console.error('剪切失败:', error);
                this.showNotification('剪切失败', 'error');
            }
        } else {
            this.showNotification('没有选中的文本', 'warning');
        }
    }

    async copyText() {
        if (!this.editor) return;
        
        const selectedText = this.editor.getSelection();
        if (selectedText) {
            try {
                await navigator.clipboard.writeText(selectedText);
                this.showNotification('文本已复制到剪贴板', 'success');
            } catch (error) {
                console.error('复制失败:', error);
                this.showNotification('复制失败', 'error');
            }
        } else {
            this.showNotification('没有选中的文本', 'warning');
        }
    }

    async pasteText() {
        if (!this.editor) return;
        
        try {
            const clipboardText = await navigator.clipboard.readText();
            if (clipboardText) {
                this.editor.replaceSelection(clipboardText);
                this.showNotification('文本已粘贴', 'success');
            } else {
                this.showNotification('剪贴板为空', 'warning');
            }
        } catch (error) {
            console.error('粘贴失败:', error);
            this.showNotification('粘贴失败，可能需要授权访问剪贴板', 'error');
        }
    }

    // 切换自动保存状态
    toggleAutoSave() {
        this.autoSaveEnabled = !this.autoSaveEnabled;
        const statusElement = document.querySelector('.auto-save-status');
        
        if (statusElement) {
            statusElement.textContent = this.autoSaveEnabled ? '开启' : '关闭';
        }
        
        if (this.autoSaveEnabled) {
            this.startAutoSaveTimer();
            this.showNotification('自动保存已开启', 'success');
        } else {
            if (this.autoSaveInterval) {
                clearInterval(this.autoSaveInterval);
            }
            this.showNotification('自动保存已关闭', 'warning');
        }
        
        this.updateAutoSaveTimer();
    }

    // 通知系统
    showNotification(message, type = 'success') {
        const container = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icon = type === 'success' ? 'fas fa-check' : 
                    type === 'warning' ? 'fas fa-exclamation-triangle' : 
                    'fas fa-times';
        
        notification.innerHTML = `
            <i class="${icon}"></i>
            <span>${message}</span>
            <button class="close-notification">
                <i class="fas fa-times"></i>
            </button>
        `;

        // 关闭按钮事件
        notification.querySelector('.close-notification').addEventListener('click', () => {
            notification.remove();
        });

        container.appendChild(notification);

        // 3秒后自动消失
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    // 格式化
    formatCode() {
        if (!this.currentFile || !this.editor) {
            this.showNotification('没有打开的文件', 'warning');
            return;
        }

        try {
            const content = this.editor.getValue();
            // 简单的格式化（在实际项目中可以集成Prettier等工具）
            const formatted = this.simpleFormat(content);
            this.editor.setValue(formatted);
            this.showNotification('格式化完成', 'success');
        } catch (error) {
            this.showNotification('格式化失败', 'error');
        }
    }

    simpleFormat(code) {
        // 简单的格式化逻辑
        return code
            .split('\n')
            .map(line => line.trim())
            .join('\n')
            .replace(/\{/g, ' {\n')
            .replace(/\}/g, '\n}\n')
            .replace(/;/g, ';\n')
            .split('\n')
            .map(line => line.trim())
            .filter(line => line)
            .join('\n');
    }

    // 显示快捷键帮助
    showShortcuts() {
        const shortcuts = [
            'Ctrl+N - 新建文件',
            'Ctrl+O - 打开文件',
            'Ctrl+Shift+O - 打开文件夹',
            'Ctrl+S - 保存文件',
            'Ctrl+Z - 撤销',
            'Ctrl+Y - 重做',
            'Ctrl+/ - 切换注释'
        ];
        
        alert('快捷键参考：\n\n' + shortcuts.join('\n'));
    }

    // 显示关于信息
    showAbout() {
        alert('Cursor Writing v1.0\n\n基于CodeMirror构建的现代文本编辑器\n支持语法高亮、AI辅助等功能');
    }

    // 切换注释
    toggleComment() {
        if (!this.editor) return;
        
        const doc = this.editor.getDoc();
        const from = doc.getCursor('start');
        const to = doc.getCursor('end');
        
        for (let i = from.line; i <= to.line; i++) {
            const line = doc.getLine(i);
            if (line.trim().startsWith('//')) {
                doc.replaceRange(line.replace('//', ''), {line: i, ch: 0}, {line: i, ch: line.length});
            } else {
                doc.replaceRange('//' + line, {line: i, ch: 0}, {line: i, ch: line.length});
            }
        }
    }
}

// 初始化应用程序
document.addEventListener('DOMContentLoaded', () => {
    new TextEditor();
});