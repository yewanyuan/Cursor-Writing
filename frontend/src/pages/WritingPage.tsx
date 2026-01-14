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
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { projectApi, cardApi, sessionApi, draftApi } from "@/api"
import type { Project, CharacterCard, SessionStatus } from "@/types"

const STATUS_TEXT: Record<string, string> = {
  idle: "空闲",
  briefing: "AI 收集素材中...",
  writing: "AI 正在创作...",
  reviewing: "AI 正在审阅...",
  editing: "AI 正在修改...",
  waiting: "等待你的反馈",
  completed: "创作完成",
  error: "出现错误",
}

export default function WritingPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

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

  // Form state
  const [chapter, setChapter] = useState(searchParams.get("chapter") || "第一章")
  const [chapterTitle, setChapterTitle] = useState("")
  const [chapterGoal, setChapterGoal] = useState("")
  const [selectedChars, setSelectedChars] = useState<string[]>([])
  const [targetWords, setTargetWords] = useState(2000)

  const addMessage = useCallback((role: string, content: string) => {
    setMessages((prev) => [...prev, { role, content }])
  }, [])

  // WebSocket 连接
  useEffect(() => {
    if (!projectId) return

    const connectWs = () => {
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

          // 添加消息
          if (data.message) {
            addMessage("assistant", data.message)
          }

          // 处理完成状态
          if (data.status === "completed" || data.status === "waiting") {
            // 加载最新草稿
            try {
              const draftRes = await draftApi.get(projectId, chapter)
              setContent(draftRes.data.content)
              if (data.status === "completed") {
                addMessage("assistant", `创作完成！共 ${draftRes.data.word_count} 字`)
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
        // 尝试重连
        setTimeout(connectWs, 3000)
      }

      ws.onerror = (err) => {
        console.error("WebSocket error:", err)
        ws.close()
      }
    }

    connectWs()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [projectId, chapter, addMessage])

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
          setChapter(chapterParam)
        } catch {
          // 草稿不存在，忽略
        }
      }
    } catch (err) {
      console.error("Failed to load data:", err)
    }
  }

  const startWriting = async () => {
    if (!projectId || !chapter || !chapterTitle) return

    try {
      setStatus({ status: "briefing" })
      addMessage("user", `开始创作 ${chapter}: ${chapterTitle}`)
      addMessage("assistant", "开始准备素材和背景知识...")

      await sessionApi.start({
        project_id: projectId,
        chapter,
        chapter_title: chapterTitle,
        chapter_goal: chapterGoal,
        characters: selectedChars,
        target_words: targetWords,
      })

      // WebSocket 会自动接收状态更新，不需要轮询
    } catch (err) {
      console.error("Failed to start writing:", err)
      setStatus({ status: "error", message: "启动失败" })
      addMessage("assistant", "创作启动失败，请重试")
    }
  }

  const handleFeedback = async (action: "confirm" | "revise") => {
    if (!projectId) return

    try {
      if (action === "confirm") {
        addMessage("user", "确认通过")
      } else {
        addMessage("user", `修改意见: ${feedback}`)
      }

      await sessionApi.feedback(projectId, action, action === "revise" ? feedback : undefined)
      setFeedback("")
      // WebSocket 会自动接收状态更新
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
      addMessage("assistant", "保存成功")
    } catch (err) {
      console.error("Failed to save:", err)
    }
  }

  const toggleChar = (name: string) => {
    setSelectedChars((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    )
  }

  const isWorking = ["briefing", "writing", "reviewing", "editing"].includes(status.status)

  return (
    <div className="min-h-screen bg-background flex">
      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b px-4 py-3 flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(`/project/${projectId}`)}>
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
            保存
          </Button>
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
          <Textarea
            className="writing-editor w-full h-full min-h-[500px] resize-none border-0 focus-visible:ring-0 text-base"
            placeholder="开始你的创作..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
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
          <span>{content.length} 字</span>
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
              <h2 className="font-medium">AI 写作助手</h2>
            </div>

            {/* Settings panel */}
            {status.status === "idle" && (
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                  <div className="grid gap-2">
                    <Label>章节编号</Label>
                    <Input
                      value={chapter}
                      onChange={(e) => setChapter(e.target.value)}
                      placeholder="如：第一章"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>章节标题</Label>
                    <Input
                      value={chapterTitle}
                      onChange={(e) => setChapterTitle(e.target.value)}
                      placeholder="本章标题"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>章节目标</Label>
                    <Textarea
                      value={chapterGoal}
                      onChange={(e) => setChapterGoal(e.target.value)}
                      placeholder="本章要达成的剧情目标"
                      rows={3}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>目标字数</Label>
                    <Input
                      type="number"
                      value={targetWords}
                      onChange={(e) => setTargetWords(Number(e.target.value))}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>出场角色</Label>
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
                    开始创作
                  </Button>
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

                {/* Feedback panel */}
                {status.status === "waiting" && (
                  <div className="p-4 border-t space-y-3">
                    <Textarea
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                      placeholder="输入修改意见..."
                      rows={2}
                    />
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        className="flex-1"
                        onClick={() => handleFeedback("revise")}
                      >
                        <RefreshCw className="w-4 h-4 mr-1" />
                        修改
                      </Button>
                      <Button className="flex-1" onClick={() => handleFeedback("confirm")}>
                        <CheckCircle className="w-4 h-4 mr-1" />
                        通过
                      </Button>
                    </div>
                  </div>
                )}

                {/* Restart button */}
                {(status.status === "completed" || status.status === "error") && (
                  <div className="p-4 border-t">
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => {
                        setStatus({ status: "idle" })
                        setMessages([])
                      }}
                    >
                      开始新章节
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
