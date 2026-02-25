import { useState, useEffect, useRef, useCallback } from "react"
import { useParams, useNavigate, useSearchParams } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  ArrowLeft,
  Send,
  Loader2,
  CheckCircle,
  XCircle,
  RefreshCw,
  Save,
  PanelRightOpen,
  PanelRightClose,
  Wifi,
  WifiOff,
  PenLine,
  Plus,
  Clock,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ThemeToggle } from "@/components/ThemeToggle"
import { LanguageToggle } from "@/components/LanguageToggle"
import { useLanguage } from "@/i18n"
import HighlightEditor, { type AIContentRange, type HighlightEditorRef } from "@/components/HighlightEditor"
import { projectApi, cardApi, sessionApi, draftApi } from "@/api"
import type { Project, CharacterCard, SessionStatus } from "@/types"

type WriteMode = "new" | "continue" | "insert"

export default function WritingPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { t } = useLanguage()

  // Ref for translations to use in WebSocket callback
  const tRef = useRef(t)
  tRef.current = t

  const STATUS_TEXT: Record<string, string> = {
    idle: t.writing.statusIdle,
    briefing: t.writing.statusBriefing,
    writing: t.writing.statusWriting,
    reviewing: t.writing.statusReviewing,
    editing: t.writing.statusEditing,
    waiting: t.writing.statusWaiting,
    completed: t.writing.statusCompleted,
    error: t.writing.statusError,
  }

  const [project, setProject] = useState<Project | null>(null)
  const [characters, setCharacters] = useState<CharacterCard[]>([])
  const [content, setContent] = useState("")
  const [status, setStatus] = useState<SessionStatus>({ status: "idle" })
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [feedback, setFeedback] = useState("")
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const editorRef = useRef<HighlightEditorRef>(null)

  // AI content highlight range
  const [aiContentRange, setAiContentRange] = useState<AIContentRange | null>(null)

  // Form state
  const [chapter, setChapter] = useState(searchParams.get("chapter") || t.writing.chapterNumberPlaceholder.replace("e.g., ", "").replace("如：", ""))
  const [chapterTitle, setChapterTitle] = useState("")
  const [chapterGoal, setChapterGoal] = useState(searchParams.get("outline") || "")
  const [selectedChars, setSelectedChars] = useState<string[]>([])
  const [targetWords, setTargetWords] = useState(2000)

  // Continue writing state
  const [writeMode, setWriteMode] = useState<WriteMode>("new")
  const [continueInstruction, setContinueInstruction] = useState("")
  const [continueTargetWords, setContinueTargetWords] = useState(500)
  const [insertPosition, setInsertPosition] = useState<number | null>(null)
  const skipNextDraftLoad = useRef(false)
  const skipNextHighlight = useRef(false)
  const isRevisionMode = useRef(false)

  // 自动保存相关状态
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true)  // 自动保存开关
  const [autoSaveStatus, setAutoSaveStatus] = useState<"idle" | "saving" | "saved">("idle")
  const [lastSavedContent, setLastSavedContent] = useState("")  // 上次保存的内容，用于检测变化
  const autoSaveIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const addMessage = useCallback((role: string, content: string) => {
    setMessages((prev) => [...prev, { role, content }])
  }, [])

  // WebSocket 连接
  const chapterRef = useRef(chapter)
  chapterRef.current = chapter

  useEffect(() => {
    if (!projectId) return

    let isCancelled = false
    let reconnectTimer: ReturnType<typeof setTimeout>

    const connectWs = () => {
      if (isCancelled) return

      const ws = new WebSocket(`ws://localhost:8000/api/ws/${projectId}/session`)
      wsRef.current = ws

      ws.onopen = () => {
        console.log("WebSocket connected")
        setWsConnected(true)
      }

      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log("WS message:", data)

          // 更新状态
          if (data.status) {
            setStatus({ status: data.status, message: data.message })
          }

          // 添加消息（去重：只有内容变化时才添加）
          if (data.message) {
            setMessages((prev) => {
              const last = prev[prev.length - 1]
              if (last && last.role === "assistant" && last.content === data.message) {
                return prev // 重复消息，不添加
              }
              return [...prev, { role: "assistant", content: data.message }]
            })
          }

          // 处理完成状态
          if (data.status === "completed" || data.status === "waiting") {
            // 如果是续写/插入后的状态更新，跳过草稿加载（已在 handleContinueWriting 中更新）
            if (skipNextDraftLoad.current) {
              skipNextDraftLoad.current = false
              return
            }
            try {
              const draftRes = await draftApi.get(projectId, chapterRef.current)
              const newContent = draftRes.data.content
              setContent(newContent)

              // 只有在非修订模式且非跳过高亮时才设置全文高亮
              if (!skipNextHighlight.current && !isRevisionMode.current && newContent && newContent.length > 0) {
                setAiContentRange({
                  start: 0,
                  end: newContent.length,
                })
              }

              // 修订完成后清除旧的高亮范围并重置标志
              // 因为编辑器返回的是完整修订后的全文，旧的高亮位置已不再准确
              if (isRevisionMode.current) {
                setAiContentRange(null)
                isRevisionMode.current = false
              }

              if (data.status === "completed") {
                setMessages((prev) => [
                  ...prev,
                  { role: "assistant", content: `${tRef.current.writing.creationComplete} ${draftRes.data.word_count} ${tRef.current.common.words}` }
                ])
              }
            } catch (err) {
              console.error("Failed to load draft:", err)
            }
          }
        } catch (err) {
          console.error("Failed to parse WS message:", err)
        }
      }

      ws.onclose = () => {
        console.log("WebSocket disconnected")
        setWsConnected(false)
        if (!isCancelled) {
          reconnectTimer = setTimeout(connectWs, 3000)
        }
      }

      ws.onerror = (err) => {
        console.error("WebSocket error:", err)
        ws.close()
      }
    }

    connectWs()

    return () => {
      isCancelled = true
      clearTimeout(reconnectTimer)
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [projectId])

  useEffect(() => {
    if (projectId) loadData()
  }, [projectId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const loadData = async () => {
    if (!projectId) return
    try {
      const [projRes, charRes] = await Promise.all([
        projectApi.get(projectId),
        cardApi.getCharacters(projectId),
      ])
      setProject(projRes.data)
      setCharacters(charRes.data)

      // 如果 URL 中有 chapter 参数，加载该章节的草稿
      const chapterParam = searchParams.get("chapter")
      if (chapterParam) {
        try {
          const draftRes = await draftApi.get(projectId, chapterParam)
          setContent(draftRes.data.content)
          setLastSavedContent(draftRes.data.content)  // 初始化已保存内容
          setChapter(chapterParam)
        } catch {
          // 草稿不存在，忽略
        }
      }
    } catch (err) {
      console.error("Failed to load data:", err)
    }
  }

  // 自动保存函数
  const performAutoSave = useCallback(async () => {
    if (!projectId || !content || !chapter) return
    // 内容没有变化时不保存
    if (content === lastSavedContent) return

    try {
      setAutoSaveStatus("saving")
      await draftApi.save(projectId, {
        chapter,
        content,
        word_count: content.length,
        status: "draft",
      })
      setLastSavedContent(content)
      setAutoSaveStatus("saved")
      // 3秒后恢复为 idle 状态
      setTimeout(() => setAutoSaveStatus("idle"), 3000)
    } catch (err) {
      console.error("Auto save failed:", err)
      setAutoSaveStatus("idle")
    }
  }, [projectId, chapter, content, lastSavedContent])

  // 定时自动保存（每30秒）
  useEffect(() => {
    // 清理之前的定时器
    if (autoSaveIntervalRef.current) {
      clearInterval(autoSaveIntervalRef.current)
      autoSaveIntervalRef.current = null
    }

    // 仅在开启时设置定时器
    if (autoSaveEnabled) {
      autoSaveIntervalRef.current = setInterval(() => {
        performAutoSave()
      }, 30000)  // 30秒
    }

    return () => {
      if (autoSaveIntervalRef.current) {
        clearInterval(autoSaveIntervalRef.current)
      }
    }
  }, [performAutoSave, autoSaveEnabled])

  // 页面离开前提醒（浏览器关闭/刷新时）
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (content && content !== lastSavedContent) {
        e.preventDefault()
        e.returnValue = ""
      }
    }

    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => window.removeEventListener("beforeunload", handleBeforeUnload)
  }, [content, lastSavedContent])

  const startWriting = async () => {
    if (!projectId || !chapter) {
      console.log("Missing required fields:", { projectId, chapter })
      return
    }

    try {
      setStatus({ status: "briefing" })
      skipNextHighlight.current = false
      addMessage("user", `${t.writing.startCreatingChapter} ${chapter}: ${chapterTitle}`)
      addMessage("assistant", t.writing.preparingMaterials)

      await sessionApi.start({
        project_id: projectId,
        chapter,
        chapter_title: chapterTitle,
        chapter_goal: chapterGoal,
        characters: selectedChars,
        target_words: targetWords,
      })

    } catch (err) {
      console.error("Failed to start writing:", err)
      setStatus({ status: "error", message: t.writing.startFailed })
      addMessage("assistant", t.writing.creationFailed)
    }
  }

  const handleFeedback = async (action: "confirm" | "revise") => {
    if (!projectId) return

    try {
      if (action === "confirm") {
        addMessage("user", t.writing.confirmPass)
        setAiContentRange(null)
        skipNextHighlight.current = true
        isRevisionMode.current = false
      } else {
        addMessage("user", `${t.writing.reviseComment}: ${feedback}`)
        skipNextDraftLoad.current = false
        isRevisionMode.current = true
      }

      await sessionApi.feedback(projectId, action, action === "revise" ? feedback : undefined)
      setFeedback("")
    } catch (err) {
      console.error("Failed to send feedback:", err)
    }
  }

  const handleSave = async () => {
    if (!projectId || !content) return
    try {
      await draftApi.save(projectId, {
        chapter,
        content,
        word_count: content.length,
        status: "draft",
      })
      setLastSavedContent(content)
      addMessage("assistant", t.writing.saveSuccess)
    } catch (err) {
      console.error("Failed to save:", err)
    }
  }

  const toggleChar = (name: string) => {
    setSelectedChars((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    )
  }

  // 获取光标位置
  const getCursorPosition = () => {
    if (editorRef.current) {
      return editorRef.current.getSelectionStart()
    }
    return null
  }

  const handleContinueWriting = async () => {
    if (!projectId || !content || !continueInstruction) {
      console.log("Missing required fields for continue writing")
      return
    }

    try {
      setStatus({ status: "writing" })
      skipNextHighlight.current = false
      const modeText = writeMode === "continue" ? t.writing.writingContinue : t.writing.writingInsert
      addMessage("user", `${modeText}: ${continueInstruction}`)
      addMessage("assistant", `${t.writing.aiWriting}${modeText}...`)

      const result = await sessionApi.continue({
        project_id: projectId,
        chapter,
        existing_content: content,
        instruction: continueInstruction,
        target_words: continueTargetWords,
        insert_position: writeMode === "insert" ? insertPosition : null,
      })

      if (result.data.success) {
        skipNextDraftLoad.current = true
        skipNextHighlight.current = true
        const newContent = result.data.draft.content
        setContent(newContent)

        if (result.data.ai_content_range) {
          setAiContentRange({
            start: result.data.ai_content_range.start,
            end: result.data.ai_content_range.end,
          })
        }

        const newLength = result.data.new_content?.length || 0
        addMessage("assistant", `${modeText}${t.writing.writeComplete} ${newLength} ${t.common.words}`)
        setStatus({ status: "waiting" })
      }

      setContinueInstruction("")
    } catch (err) {
      console.error("Failed to continue writing:", err)
      setStatus({ status: "error", message: t.writing.writeFailed })
      addMessage("assistant", t.writing.writeFailed)
    }
  }

  // 切换到插入模式时记录光标位置
  const switchToInsertMode = () => {
    const pos = getCursorPosition()
    setInsertPosition(pos)
    setWriteMode("insert")
  }

  // 检查是否有未保存的内容
  const hasUnsavedChanges = content && content !== lastSavedContent

  const handleBack = () => {
    if (hasUnsavedChanges) {
      const confirmed = window.confirm(t.writing.unsavedWarning)
      if (!confirmed) return
    }
    navigate(`/project/${projectId}?tab=drafts`)
  }

  const isWorking = ["briefing", "writing", "reviewing", "editing"].includes(status.status)
  const hasContent = content.length > 0

  return (
    <div className="min-h-screen bg-background flex">
      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b px-4 py-3 flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <h1 className="font-medium">{project?.name}</h1>
            <p className="text-sm text-muted-foreground">{chapter}</p>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            {wsConnected ? (
              <Wifi className="w-4 h-4 text-green-500" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-500" />
            )}
          </div>
          <Button variant="outline" size="sm" onClick={handleSave} disabled={!content}>
            <Save className="w-4 h-4 mr-1" />
            {t.common.save}
          </Button>
          <Button
            variant={autoSaveEnabled ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoSaveEnabled(!autoSaveEnabled)}
            title={autoSaveEnabled ? t.writing.autoSaveOn : t.writing.autoSaveOff}
          >
            <Clock className="w-4 h-4 mr-1" />
            {autoSaveEnabled ? t.writing.autoSaveOn : t.writing.autoSaveOff}
          </Button>
          <LanguageToggle />
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <PanelRightClose className="w-5 h-5" /> : <PanelRightOpen className="w-5 h-5" />}
          </Button>
        </div>

        {/* Editor */}
        <div className="flex-1 p-6">
          <HighlightEditor
            ref={editorRef}
            className="writing-editor w-full h-full min-h-[500px] border rounded-md"
            placeholder={t.writing.editorPlaceholder}
            value={content}
            onChange={setContent}
            aiContentRange={aiContentRange}
            onAIRangeChange={setAiContentRange}
          />
        </div>

        {/* Status bar */}
        <div className="border-t px-4 py-2 flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            {isWorking && <Loader2 className="w-4 h-4 animate-spin" />}
            {status.status === "completed" && <CheckCircle className="w-4 h-4 text-green-500" />}
            {status.status === "error" && <XCircle className="w-4 h-4 text-red-500" />}
            <span>{STATUS_TEXT[status.status]}</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1 text-xs">
              {autoSaveStatus === "saving" && (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>{t.writing.autoSaving}</span>
                </>
              )}
              {autoSaveStatus === "saved" && (
                <>
                  <Clock className="w-3 h-3 text-green-500" />
                  <span className="text-green-600">{t.writing.autoSaved}</span>
                </>
              )}
            </div>
            <span>{content.length} {t.common.words}</span>
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 360, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="border-l bg-muted/30 flex flex-col"
          >
            <div className="p-4 border-b">
              <h2 className="font-medium">{t.writing.aiAssistant}</h2>
            </div>

            {/* Settings panel */}
            {status.status === "idle" && (
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                  {hasContent && (
                    <div className="flex gap-2 p-1 bg-muted rounded-lg">
                      <Button
                        variant={writeMode === "new" ? "default" : "ghost"}
                        size="sm"
                        className="flex-1"
                        onClick={() => setWriteMode("new")}
                      >
                        <Send className="w-3 h-3 mr-1" />
                        {t.writing.newChapter}
                      </Button>
                      <Button
                        variant={writeMode === "continue" ? "default" : "ghost"}
                        size="sm"
                        className="flex-1"
                        onClick={() => setWriteMode("continue")}
                      >
                        <PenLine className="w-3 h-3 mr-1" />
                        {t.writing.continue}
                      </Button>
                      <Button
                        variant={writeMode === "insert" ? "default" : "ghost"}
                        size="sm"
                        className="flex-1"
                        onClick={switchToInsertMode}
                      >
                        <Plus className="w-3 h-3 mr-1" />
                        {t.writing.insert}
                      </Button>
                    </div>
                  )}

                  {(writeMode === "new" || !hasContent) && (
                    <>
                      <div className="grid gap-2">
                        <Label>{t.writing.chapterNumber}</Label>
                        <Input
                          value={chapter}
                          onChange={(e) => setChapter(e.target.value)}
                          placeholder={t.writing.chapterNumberPlaceholder}
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>{t.writing.chapterTitle}</Label>
                        <Input
                          value={chapterTitle}
                          onChange={(e) => setChapterTitle(e.target.value)}
                          placeholder={t.writing.chapterTitlePlaceholder}
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>{t.writing.chapterGoal}</Label>
                        <Textarea
                          value={chapterGoal}
                          onChange={(e) => setChapterGoal(e.target.value)}
                          placeholder={t.writing.chapterGoalPlaceholder}
                          rows={3}
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>{t.writing.targetWords}</Label>
                        <Input
                          type="number"
                          value={targetWords}
                          onChange={(e) => setTargetWords(Number(e.target.value))}
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>{t.writing.appearingCharacters}</Label>
                        <div className="flex flex-wrap gap-2">
                          {characters.map((char) => (
                            <Button
                              key={char.name}
                              variant={selectedChars.includes(char.name) ? "default" : "outline"}
                              size="sm"
                              onClick={() => toggleChar(char.name)}
                            >
                              {char.name}
                            </Button>
                          ))}
                        </div>
                      </div>
                      <Button className="w-full" onClick={startWriting}>
                        <Send className="w-4 h-4 mr-2" />
                        {t.writing.startCreating}
                      </Button>
                    </>
                  )}

                  {writeMode === "continue" && hasContent && (
                    <>
                      <div className="p-3 bg-muted/50 rounded-lg text-sm">
                        <p className="text-muted-foreground">
                          {t.writing.continueHint}
                        </p>
                      </div>
                      <div className="grid gap-2">
                        <Label>{t.writing.continueDescription}</Label>
                        <Textarea
                          value={continueInstruction}
                          onChange={(e) => setContinueInstruction(e.target.value)}
                          placeholder={t.writing.continuePlaceholder}
                          rows={4}
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>{t.writing.targetWords}</Label>
                        <Input
                          type="number"
                          value={continueTargetWords}
                          onChange={(e) => setContinueTargetWords(Number(e.target.value))}
                        />
                      </div>
                      <Button
                        className="w-full"
                        onClick={handleContinueWriting}
                        disabled={!continueInstruction}
                      >
                        <PenLine className="w-4 h-4 mr-2" />
                        {t.writing.startContinue}
                      </Button>
                    </>
                  )}

                  {writeMode === "insert" && hasContent && (
                    <>
                      <div className="p-3 bg-muted/50 rounded-lg text-sm space-y-2">
                        <p className="text-muted-foreground">
                          {t.writing.insertHint}
                        </p>
                        <p className="font-medium">
                          {t.writing.insertPosition} {insertPosition ?? 0} {t.writing.charPosition}
                          {insertPosition !== null && insertPosition > 0 && (
                            <span className="text-muted-foreground ml-2">
                              (...{content.slice(Math.max(0, insertPosition - 20), insertPosition)}|)
                            </span>
                          )}
                        </p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setInsertPosition(getCursorPosition())}
                        >
                          {t.writing.updateInsertPosition}
                        </Button>
                      </div>
                      <div className="grid gap-2">
                        <Label>{t.writing.insertDescription}</Label>
                        <Textarea
                          value={continueInstruction}
                          onChange={(e) => setContinueInstruction(e.target.value)}
                          placeholder={t.writing.insertPlaceholder}
                          rows={4}
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>{t.writing.targetWords}</Label>
                        <Input
                          type="number"
                          value={continueTargetWords}
                          onChange={(e) => setContinueTargetWords(Number(e.target.value))}
                        />
                      </div>
                      <Button
                        className="w-full"
                        onClick={handleContinueWriting}
                        disabled={!continueInstruction || insertPosition === null}
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        {t.writing.insertContent}
                      </Button>
                    </>
                  )}
                </div>
              </ScrollArea>
            )}

            {/* Messages panel */}
            {status.status !== "idle" && (
              <>
                <ScrollArea className="flex-1 p-4">
                  <div className="space-y-3">
                    {messages.map((msg, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`p-3 rounded-lg text-sm ${
                          msg.role === "user"
                            ? "bg-primary text-primary-foreground ml-8"
                            : "bg-muted mr-8"
                        }`}
                      >
                        {msg.content}
                      </motion.div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                </ScrollArea>

                {status.status === "waiting" && (
                  <div className="p-4 border-t space-y-3">
                    <Textarea
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                      placeholder={t.writing.feedbackPlaceholder}
                      rows={2}
                    />
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        className="flex-1"
                        onClick={() => handleFeedback("revise")}
                      >
                        <RefreshCw className="w-4 h-4 mr-1" />
                        {t.writing.revise}
                      </Button>
                      <Button className="flex-1" onClick={() => handleFeedback("confirm")}>
                        <CheckCircle className="w-4 h-4 mr-1" />
                        {t.writing.pass}
                      </Button>
                    </div>
                    <Button
                      variant="ghost"
                      className="w-full text-muted-foreground"
                      onClick={() => {
                        setStatus({ status: "idle" })
                        setMessages([])
                        setContinueInstruction("")
                        setFeedback("")
                      }}
                    >
                      {t.writing.continueCreating}
                    </Button>
                  </div>
                )}

                {(status.status === "completed" || status.status === "error") && (
                  <div className="p-4 border-t">
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => {
                        setStatus({ status: "idle" })
                        setMessages([])
                        setContinueInstruction("")
                        setFeedback("")
                      }}
                    >
                      {t.writing.continueCreating}
                    </Button>
                  </div>
                )}
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
