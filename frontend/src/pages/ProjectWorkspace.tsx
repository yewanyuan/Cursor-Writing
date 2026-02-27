import { useState, useEffect } from "react"
import { useParams, useNavigate, useSearchParams } from "react-router-dom"
import { motion } from "framer-motion"
import { ArrowLeft, Plus, User, Globe, FileText, Pen, Trash2, Edit, BookOpen, Shield, Database, Clock, Activity, Download, Loader2, BarChart3, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Checkbox } from "@/components/ui/checkbox"
import { TagInput } from "@/components/ui/tag-input"
import { ListInput } from "@/components/ui/list-input"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ThemeToggle } from "@/components/ThemeToggle"
import { LanguageToggle } from "@/components/LanguageToggle"
import { useLanguage } from "@/i18n"
import { projectApi, cardApi, draftApi, canonApi, exportApi } from "@/api"
import type { Project, CharacterCard, WorldCard, StyleCard, RulesCard, Draft, Fact, TimelineEvent, CharacterState } from "@/types"

export default function ProjectWorkspace() {
  const { projectId } = useParams<{ projectId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { t } = useLanguage()
  const [project, setProject] = useState<Project | null>(null)
  const [characters, setCharacters] = useState<CharacterCard[]>([])
  const [worlds, setWorlds] = useState<WorldCard[]>([])
  const [style, setStyle] = useState<StyleCard>({
    narrative_distance: "close",
    pacing: "moderate",
    sentence_style: "",
    vocabulary: [],
    taboo_words: [],
    example_passages: [],
  })
  const [rules, setRules] = useState<RulesCard>({
    dos: [],
    donts: [],
    quality_standards: [],
  })
  const [drafts, setDrafts] = useState<Draft[]>([])
  // 从 URL 参数读取初始 tab，默认为 characters
  const [activeTab, setActiveTab] = useState(searchParams.get("tab") || "characters")

  // Canon 状态
  const [facts, setFacts] = useState<Fact[]>([])
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [characterStates, setCharacterStates] = useState<CharacterState[]>([])
  const [canonSubTab, setCanonSubTab] = useState<"facts" | "timeline" | "states">("facts")

  // 角色对话框状态
  const [charDialogOpen, setCharDialogOpen] = useState(false)
  const [editingCharName, setEditingCharName] = useState<string | null>(null)
  const [charForm, setCharForm] = useState<CharacterCard>({
    name: "",
    identity: "",
    personality: [],
    speech_pattern: "",
    background: "",
  })

  // 世界观对话框状态
  const [worldDialogOpen, setWorldDialogOpen] = useState(false)
  const [editingWorldName, setEditingWorldName] = useState<string | null>(null)
  const [worldForm, setWorldForm] = useState<WorldCard>({
    name: "",
    category: "",
    description: "",
  })

  // 事实对话框状态
  const [factDialogOpen, setFactDialogOpen] = useState(false)
  const [editingFactId, setEditingFactId] = useState<string | null>(null)
  const [factForm, setFactForm] = useState<Partial<Fact>>({
    statement: "",
    source: "",
    confidence: 1.0,
  })

  // 时间线对话框状态
  const [timelineDialogOpen, setTimelineDialogOpen] = useState(false)
  const [editingTimelineId, setEditingTimelineId] = useState<string | null>(null)
  const [timelineForm, setTimelineForm] = useState<Partial<TimelineEvent>>({
    time: "",
    event: "",
    participants: [],
    location: "",
    source: "",
  })

  // 角色状态对话框
  const [stateDialogOpen, setStateDialogOpen] = useState(false)
  const [editingStateKey, setEditingStateKey] = useState<{ character: string; chapter: string } | null>(null)
  const [stateForm, setStateForm] = useState<Partial<CharacterState>>({
    character: "",
    chapter: "",
    location: "",
    emotional_state: "",
    goals: [],
    inventory: [],
    injuries: [],
    relationships: {},
  })

  // 章节对话框状态
  const [chapterDialogOpen, setChapterDialogOpen] = useState(false)
  const [chapterForm, setChapterForm] = useState({
    number: "",
    title: "",
    outline: "",
  })

  // 导出对话框状态
  const [exportDialogOpen, setExportDialogOpen] = useState(false)
  const [exportFormat, setExportFormat] = useState<"txt" | "markdown" | "epub">("txt")
  const [exportUseFinal, setExportUseFinal] = useState(true)
  const [exportInfo, setExportInfo] = useState<{ total_words: number; chapter_count: number } | null>(null)
  const [exporting, setExporting] = useState(false)

  // AI 提取状态
  const [extractDialogOpen, setExtractDialogOpen] = useState(false)
  const [extractChapter, setExtractChapter] = useState("")
  const [extracting, setExtracting] = useState(false)

  // 批量选择状态
  const [selectedFactIds, setSelectedFactIds] = useState<Set<string>>(new Set())
  const [selectedTimelineIds, setSelectedTimelineIds] = useState<Set<string>>(new Set())
  const [selectedStateKeys, setSelectedStateKeys] = useState<Set<string>>(new Set())  // "character|chapter" 格式
  const [batchDeleting, setBatchDeleting] = useState(false)

  // 项目编辑对话框状态
  const [projectDialogOpen, setProjectDialogOpen] = useState(false)
  const [projectForm, setProjectForm] = useState({
    name: "",
    author: "",
    genre: "",
    description: "",
  })

  useEffect(() => {
    if (projectId) loadData()
  }, [projectId])

  const loadData = async () => {
    if (!projectId) return
    try {
      const [projRes, charRes, worldRes, styleRes, rulesRes, draftRes, factsRes, timelineRes, statesRes] = await Promise.all([
        projectApi.get(projectId),
        cardApi.getCharacters(projectId),
        cardApi.getWorlds(projectId),
        cardApi.getStyle(projectId),
        cardApi.getRules(projectId),
        draftApi.list(projectId),
        canonApi.getFacts(projectId),
        canonApi.getTimeline(projectId),
        canonApi.getCharacterStates(projectId),
      ])
      setProject(projRes.data)
      setCharacters(charRes.data)
      setWorlds(worldRes.data)
      setStyle(styleRes.data)
      setRules(rulesRes.data)
      setDrafts(draftRes.data)
      setFacts(factsRes.data)
      setTimeline(timelineRes.data)
      setCharacterStates(statesRes.data)
    } catch (err) {
      console.error("Failed to load data:", err)
    }
  }

  // 项目编辑相关
  const openEditProjectDialog = () => {
    if (!project) return
    setProjectForm({
      name: project.name,
      author: project.author || "",
      genre: project.genre || "",
      description: project.description || "",
    })
    setProjectDialogOpen(true)
  }

  const handleSaveProject = async () => {
    if (!projectId || !projectForm.name) return
    try {
      const res = await projectApi.update(projectId, projectForm)
      setProject(res.data)
      setProjectDialogOpen(false)
    } catch (err) {
      console.error("Failed to update project:", err)
    }
  }

  // 角色相关
  const openNewCharDialog = () => {
    setEditingCharName(null)
    setCharForm({ name: "", identity: "", personality: [], speech_pattern: "", background: "" })
    setCharDialogOpen(true)
  }

  const openEditCharDialog = (char: CharacterCard) => {
    setEditingCharName(char.name)
    setCharForm({ ...char })
    setCharDialogOpen(true)
  }

  const handleSaveCharacter = async () => {
    if (!projectId || !charForm.name) return
    try {
      if (editingCharName && editingCharName !== charForm.name) {
        await cardApi.deleteCharacter(projectId, editingCharName)
      }
      await cardApi.saveCharacter(projectId, {
        ...charForm,
        personality: charForm.personality.length ? charForm.personality : [],
      })
      setCharDialogOpen(false)
      loadData()
    } catch (err) {
      console.error("Failed to save character:", err)
    }
  }

  const handleDeleteChar = async (name: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!projectId || !confirm(`${t.workspace.deleteCharConfirm} "${name}"?`)) return
    try {
      await cardApi.deleteCharacter(projectId, name)
      loadData()
    } catch (err) {
      console.error("Failed to delete character:", err)
    }
  }

  // 世界观相关
  const openNewWorldDialog = () => {
    setEditingWorldName(null)
    setWorldForm({ name: "", category: "", description: "" })
    setWorldDialogOpen(true)
  }

  const openEditWorldDialog = (world: WorldCard) => {
    setEditingWorldName(world.name)
    setWorldForm({ ...world })
    setWorldDialogOpen(true)
  }

  const handleSaveWorld = async () => {
    if (!projectId || !worldForm.name) return
    try {
      if (editingWorldName && editingWorldName !== worldForm.name) {
        await cardApi.deleteWorld(projectId, editingWorldName)
      }
      await cardApi.saveWorld(projectId, worldForm)
      setWorldDialogOpen(false)
      loadData()
    } catch (err) {
      console.error("Failed to save world:", err)
    }
  }

  const handleDeleteWorld = async (name: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!projectId || !confirm(`${t.workspace.deleteSettingConfirm} "${name}"?`)) return
    try {
      await cardApi.deleteWorld(projectId, name)
      loadData()
    } catch (err) {
      console.error("Failed to delete world:", err)
    }
  }

  // 文风卡保存
  const handleSaveStyle = async () => {
    if (!projectId) return
    try {
      await cardApi.saveStyle(projectId, style)
      alert(t.workspace.styleSaved)
    } catch (err) {
      console.error("Failed to save style:", err)
    }
  }

  // 规则卡保存
  const handleSaveRules = async () => {
    if (!projectId) return
    try {
      await cardApi.saveRules(projectId, rules)
      alert(t.workspace.rulesSaved)
    } catch (err) {
      console.error("Failed to save rules:", err)
    }
  }

  // Canon 相关
  const openNewFactDialog = () => {
    setEditingFactId(null)
    setFactForm({ statement: "", source: "", confidence: 1.0 })
    setFactDialogOpen(true)
  }

  const openEditFactDialog = (fact: Fact) => {
    setEditingFactId(fact.id)
    setFactForm({ ...fact })
    setFactDialogOpen(true)
  }

  const handleSaveFact = async () => {
    if (!projectId || !factForm.statement) return
    try {
      if (editingFactId) {
        await canonApi.updateFact(projectId, editingFactId, factForm)
      } else {
        await canonApi.addFact(projectId, factForm)
      }
      setFactDialogOpen(false)
      loadData()
    } catch (err) {
      console.error("Failed to save fact:", err)
    }
  }

  const handleDeleteFact = async (factId: string) => {
    if (!projectId || !confirm(t.workspace.deleteFactConfirm)) return
    try {
      await canonApi.deleteFact(projectId, factId)
      loadData()
    } catch (err) {
      console.error("Failed to delete fact:", err)
    }
  }

  const openNewTimelineDialog = () => {
    setEditingTimelineId(null)
    setTimelineForm({ time: "", event: "", participants: [], location: "", source: "" })
    setTimelineDialogOpen(true)
  }

  const openEditTimelineDialog = (event: TimelineEvent) => {
    setEditingTimelineId(event.id)
    setTimelineForm({ ...event })
    setTimelineDialogOpen(true)
  }

  const handleSaveTimeline = async () => {
    if (!projectId || !timelineForm.event) return
    try {
      if (editingTimelineId) {
        await canonApi.updateTimelineEvent(projectId, editingTimelineId, timelineForm)
      } else {
        await canonApi.addTimelineEvent(projectId, timelineForm)
      }
      setTimelineDialogOpen(false)
      loadData()
    } catch (err) {
      console.error("Failed to save timeline event:", err)
    }
  }

  const handleDeleteTimelineEvent = async (eventId: string) => {
    if (!projectId || !confirm(t.workspace.deleteEventConfirm)) return
    try {
      await canonApi.deleteTimelineEvent(projectId, eventId)
      loadData()
    } catch (err) {
      console.error("Failed to delete timeline event:", err)
    }
  }

  const openNewStateDialog = () => {
    setEditingStateKey(null)
    setStateForm({
      character: "",
      chapter: "",
      location: "",
      emotional_state: "",
      goals: [],
      inventory: [],
      injuries: [],
      relationships: {},
    })
    setStateDialogOpen(true)
  }

  const openEditStateDialog = (state: CharacterState) => {
    setEditingStateKey({ character: state.character, chapter: state.chapter })
    setStateForm({ ...state })
    setStateDialogOpen(true)
  }

  const handleSaveState = async () => {
    if (!projectId || !stateForm.character || !stateForm.chapter) return
    try {
      if (editingStateKey) {
        await canonApi.editCharacterState(projectId, editingStateKey.character, editingStateKey.chapter, stateForm)
      } else {
        await canonApi.updateCharacterState(projectId, stateForm)
      }
      setStateDialogOpen(false)
      loadData()
    } catch (err) {
      console.error("Failed to save character state:", err)
    }
  }

  const handleDeleteState = async (character: string, chapter: string) => {
    if (!projectId || !confirm(`${t.workspace.deleteStateConfirm} ${character} ${t.workspace.stateAt}`)) return
    try {
      await canonApi.deleteCharacterState(projectId, character, chapter)
      loadData()
    } catch (err) {
      console.error("Failed to delete character state:", err)
    }
  }

  // AI 提取相关
  const openExtractDialog = () => {
    // 默认选择第一个章节
    if (drafts.length > 0) {
      setExtractChapter(drafts[0].chapter)
    }
    setExtractDialogOpen(true)
  }

  const handleAIExtract = async () => {
    if (!projectId || !extractChapter) return
    setExtracting(true)
    try {
      const res = await canonApi.extractFromChapter(projectId, extractChapter)
      if (res.data.success) {
        alert(res.data.message)
        setExtractDialogOpen(false)
        loadData()  // 刷新数据
      } else {
        alert(`${t.common.error}: ` + res.data.message)
      }
    } catch (err: unknown) {
      console.error("Failed to extract:", err)
      const errorMessage = err instanceof Error ? err.message : t.projectList.unknownError
      alert(`${t.common.error}: ` + errorMessage)
    } finally {
      setExtracting(false)
    }
  }

  // 批量删除相关
  const toggleFactSelection = (factId: string) => {
    setSelectedFactIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(factId)) {
        newSet.delete(factId)
      } else {
        newSet.add(factId)
      }
      return newSet
    })
  }

  const toggleTimelineSelection = (eventId: string) => {
    setSelectedTimelineIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(eventId)) {
        newSet.delete(eventId)
      } else {
        newSet.add(eventId)
      }
      return newSet
    })
  }

  const toggleStateSelection = (character: string, chapter: string) => {
    const key = `${character}|${chapter}`
    setSelectedStateKeys(prev => {
      const newSet = new Set(prev)
      if (newSet.has(key)) {
        newSet.delete(key)
      } else {
        newSet.add(key)
      }
      return newSet
    })
  }

  const selectAllFacts = () => {
    if (selectedFactIds.size === facts.length) {
      setSelectedFactIds(new Set())
    } else {
      setSelectedFactIds(new Set(facts.map(f => f.id)))
    }
  }

  const selectAllTimeline = () => {
    if (selectedTimelineIds.size === timeline.length) {
      setSelectedTimelineIds(new Set())
    } else {
      setSelectedTimelineIds(new Set(timeline.map(e => e.id)))
    }
  }

  const selectAllStates = () => {
    if (selectedStateKeys.size === characterStates.length) {
      setSelectedStateKeys(new Set())
    } else {
      setSelectedStateKeys(new Set(characterStates.map(s => `${s.character}|${s.chapter}`)))
    }
  }

  const handleBatchDeleteFacts = async () => {
    if (!projectId || selectedFactIds.size === 0) return
    if (!confirm(`${t.common.batchDelete} ${selectedFactIds.size} ${t.common.items}?`)) return
    setBatchDeleting(true)
    try {
      const res = await canonApi.batchDeleteFacts(projectId, Array.from(selectedFactIds))
      if (res.data.success) {
        alert(res.data.message)
        setSelectedFactIds(new Set())
        loadData()
      }
    } catch (err) {
      console.error("Failed to batch delete facts:", err)
      alert(t.common.error)
    } finally {
      setBatchDeleting(false)
    }
  }

  const handleBatchDeleteTimeline = async () => {
    if (!projectId || selectedTimelineIds.size === 0) return
    if (!confirm(`${t.common.batchDelete} ${selectedTimelineIds.size} ${t.common.items}?`)) return
    setBatchDeleting(true)
    try {
      const res = await canonApi.batchDeleteTimeline(projectId, Array.from(selectedTimelineIds))
      if (res.data.success) {
        alert(res.data.message)
        setSelectedTimelineIds(new Set())
        loadData()
      }
    } catch (err) {
      console.error("Failed to batch delete timeline:", err)
      alert(t.common.error)
    } finally {
      setBatchDeleting(false)
    }
  }

  const handleBatchDeleteStates = async () => {
    if (!projectId || selectedStateKeys.size === 0) return
    if (!confirm(`${t.common.batchDelete} ${selectedStateKeys.size} ${t.common.items}?`)) return
    setBatchDeleting(true)
    try {
      const keys = Array.from(selectedStateKeys).map(key => {
        const [character, chapter] = key.split("|")
        return { character, chapter }
      })
      const res = await canonApi.batchDeleteStates(projectId, keys)
      if (res.data.success) {
        alert(res.data.message)
        setSelectedStateKeys(new Set())
        loadData()
      }
    } catch (err) {
      console.error("Failed to batch delete states:", err)
      alert(t.common.error)
    } finally {
      setBatchDeleting(false)
    }
  }

  // 章节相关
  const openNewChapterDialog = () => {
    const nextChapterNum = drafts.length + 1
    setChapterForm({
      number: t.workspace.defaultChapterTitle.replace("{n}", String(nextChapterNum)),
      title: "",
      outline: "",
    })
    setChapterDialogOpen(true)
  }

  const handleStartWriting = () => {
    if (!projectId || !chapterForm.number) return
    const params = new URLSearchParams({
      chapter: chapterForm.number,
      ...(chapterForm.title && { chapter_title: chapterForm.title }),
      ...(chapterForm.outline && { outline: chapterForm.outline }),
    })
    setChapterDialogOpen(false)
    navigate(`/write/${projectId}?${params.toString()}`)
  }

  const handleDeleteChapter = async (chapter: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!projectId) return
    if (!confirm(t.workspace.deleteChapterConfirm)) return
    try {
      await draftApi.delete(projectId, chapter)
      setDrafts((prev) => prev.filter((d) => d.chapter !== chapter))
    } catch (err) {
      console.error("Failed to delete chapter:", err)
    }
  }

  // 导出相关
  const openExportDialog = async () => {
    if (!projectId) return
    setExportDialogOpen(true)
    try {
      const res = await exportApi.getInfo(projectId)
      setExportInfo(res.data)
    } catch (err) {
      console.error("Failed to get export info:", err)
    }
  }

  const handleExport = async () => {
    if (!projectId) return
    setExporting(true)
    try {
      const response = await exportApi.export(projectId, exportFormat, exportUseFinal)

      // 检查响应是否为错误（blob 类型的错误需要特殊处理）
      if (response.data instanceof Blob && response.data.type === "application/json") {
        const text = await response.data.text()
        const error = JSON.parse(text)
        throw new Error(error.detail || t.common.error)
      }

      // 创建下载链接
      const blob = response.data instanceof Blob
        ? response.data
        : new Blob([response.data], { type: response.headers["content-type"] })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url

      // 从响应头获取文件名，或使用默认值
      const ext = exportFormat === "markdown" ? "md" : exportFormat
      a.download = `${project?.name || "novel"}.${ext}`

      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setExportDialogOpen(false)
    } catch (err: any) {
      console.error("Failed to export:", err)
      const message = err?.response?.data?.detail || err?.message || t.common.error
      alert(message)
    } finally {
      setExporting(false)
    }
  }

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">{t.common.loading}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex-1 flex items-center gap-2">
              <div>
                <h1 className="text-xl font-semibold">{project.name}</h1>
                <p className="text-sm text-muted-foreground">{project.genre}</p>
              </div>
              <Button variant="ghost" size="icon" onClick={openEditProjectDialog} title={t.workspace.editProjectTitle}>
                <Edit className="w-4 h-4" />
              </Button>
            </div>
            <Button variant="outline" onClick={() => navigate(`/stats/${projectId}?from=${activeTab}`)}>
              <BarChart3 className="w-4 h-4 mr-2" />
              {t.workspace.statistics}
            </Button>
            <Button onClick={() => navigate(`/write/${projectId}`)}>
              <Pen className="w-4 h-4 mr-2" />
              {t.workspace.startWriting}
            </Button>
            <LanguageToggle />
            <ThemeToggle />
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="characters" className="gap-2">
              <User className="w-4 h-4" />
              {t.workspace.characters}
            </TabsTrigger>
            <TabsTrigger value="world" className="gap-2">
              <Globe className="w-4 h-4" />
              {t.workspace.world}
            </TabsTrigger>
            <TabsTrigger value="style" className="gap-2">
              <BookOpen className="w-4 h-4" />
              {t.workspace.style}
            </TabsTrigger>
            <TabsTrigger value="rules" className="gap-2">
              <Shield className="w-4 h-4" />
              {t.workspace.rules}
            </TabsTrigger>
            <TabsTrigger value="canon" className="gap-2">
              <Database className="w-4 h-4" />
              {t.workspace.canon}
            </TabsTrigger>
            <TabsTrigger value="drafts" className="gap-2">
              <FileText className="w-4 h-4" />
              {t.workspace.drafts}
            </TabsTrigger>
          </TabsList>

          {/* 角色 Tab */}
          <TabsContent value="characters" className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">{t.workspace.characterSettings}</h2>
              <Button size="sm" onClick={openNewCharDialog}>
                <Plus className="w-4 h-4 mr-1" />
                {t.workspace.addCharacter}
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {characters.map((char) => (
                <motion.div
                  key={char.name}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  <Card
                    className="group cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => openEditCharDialog(char)}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-base">{char.name}</CardTitle>
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={(e) => { e.stopPropagation(); openEditCharDialog(char) }}>
                            <Edit className="w-3 h-3" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={(e) => handleDeleteChar(char.name, e)}>
                            <Trash2 className="w-3 h-3 text-destructive" />
                          </Button>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">{char.identity}</p>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm line-clamp-3">{char.background || t.workspace.noBackground}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </TabsContent>

          {/* 世界观 Tab */}
          <TabsContent value="world" className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">{t.workspace.worldSettings}</h2>
              <Button size="sm" onClick={openNewWorldDialog}>
                <Plus className="w-4 h-4 mr-1" />
                {t.workspace.addSetting}
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {worlds.map((world) => (
                <motion.div
                  key={world.name}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  <Card
                    className="group cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => openEditWorldDialog(world)}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-base">{world.name}</CardTitle>
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={(e) => { e.stopPropagation(); openEditWorldDialog(world) }}>
                            <Edit className="w-3 h-3" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={(e) => handleDeleteWorld(world.name, e)}>
                            <Trash2 className="w-3 h-3 text-destructive" />
                          </Button>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">{world.category}</p>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm line-clamp-3">{world.description}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </TabsContent>

          {/* 文风 Tab */}
          <TabsContent value="style" className="mt-6">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-medium">{t.workspace.styleSettings}</h2>
                  <p className="text-sm text-muted-foreground">{t.workspace.styleDescription}</p>
                </div>
                <Button onClick={handleSaveStyle}>{t.workspace.saveStyleSettings}</Button>
              </div>

              {/* 基础设定卡片 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="overflow-hidden">
                  <CardHeader className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                      {t.workspace.narrativeDistance}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="flex flex-col gap-2">
                      {[
                        { value: "close", label: t.workspace.close, desc: t.workspace.closeDesc },
                        { value: "medium", label: t.workspace.medium, desc: t.workspace.mediumDesc },
                        { value: "far", label: t.workspace.far, desc: t.workspace.farDesc },
                      ].map((option) => (
                        <label
                          key={option.value}
                          className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                            style.narrative_distance === option.value
                              ? "border-primary bg-primary/5"
                              : "border-transparent bg-muted/50 hover:bg-muted"
                          }`}
                        >
                          <input
                            type="radio"
                            name="narrative_distance"
                            value={option.value}
                            checked={style.narrative_distance === option.value}
                            onChange={(e) => setStyle({ ...style, narrative_distance: e.target.value })}
                            className="sr-only"
                          />
                          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                            style.narrative_distance === option.value ? "border-primary" : "border-muted-foreground/30"
                          }`}>
                            {style.narrative_distance === option.value && (
                              <div className="w-2 h-2 rounded-full bg-primary"></div>
                            )}
                          </div>
                          <div>
                            <div className="font-medium text-sm">{option.label}</div>
                            <div className="text-xs text-muted-foreground">{option.desc}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="overflow-hidden">
                  <CardHeader className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                      {t.workspace.pacing}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="flex flex-col gap-2">
                      {[
                        { value: "fast", label: t.workspace.fast, desc: t.workspace.fastDesc },
                        { value: "moderate", label: t.workspace.moderate, desc: t.workspace.moderateDesc },
                        { value: "slow", label: t.workspace.slow, desc: t.workspace.slowDesc },
                      ].map((option) => (
                        <label
                          key={option.value}
                          className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                            style.pacing === option.value
                              ? "border-primary bg-primary/5"
                              : "border-transparent bg-muted/50 hover:bg-muted"
                          }`}
                        >
                          <input
                            type="radio"
                            name="pacing"
                            value={option.value}
                            checked={style.pacing === option.value}
                            onChange={(e) => setStyle({ ...style, pacing: e.target.value })}
                            className="sr-only"
                          />
                          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                            style.pacing === option.value ? "border-primary" : "border-muted-foreground/30"
                          }`}>
                            {style.pacing === option.value && (
                              <div className="w-2 h-2 rounded-full bg-primary"></div>
                            )}
                          </div>
                          <div>
                            <div className="font-medium text-sm">{option.label}</div>
                            <div className="text-xs text-muted-foreground">{option.desc}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* 句式偏好 */}
              <Card className="overflow-hidden">
                <CardHeader className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                    {t.workspace.sentenceStyle}
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <Textarea
                    value={style.sentence_style}
                    onChange={(e) => setStyle({ ...style, sentence_style: e.target.value })}
                    placeholder={t.workspace.sentenceStylePlaceholder}
                    rows={2}
                    className="resize-none"
                  />
                </CardContent>
              </Card>

              {/* 词汇设定 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="overflow-hidden">
                  <CardHeader className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-green-500"></span>
                      {t.workspace.vocabulary}
                      <span className="text-xs font-normal text-muted-foreground ml-auto">
                        {style.vocabulary.length} {t.workspace.itemCount}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <TagInput
                      value={style.vocabulary}
                      onChange={(v) => setStyle({ ...style, vocabulary: v })}
                      placeholder={t.workspace.vocabularyPlaceholder}
                      tagClassName="bg-green-500/10 text-green-700 border-green-500/20 hover:bg-green-500/20"
                    />
                    <p className="text-xs text-muted-foreground mt-2">
                      {t.workspace.vocabularyHint}
                    </p>
                  </CardContent>
                </Card>

                <Card className="overflow-hidden">
                  <CardHeader className="bg-gradient-to-r from-red-500/10 to-rose-500/10 pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-red-500"></span>
                      {t.workspace.tabooWords}
                      <span className="text-xs font-normal text-muted-foreground ml-auto">
                        {style.taboo_words.length} {t.workspace.itemCount}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <TagInput
                      value={style.taboo_words}
                      onChange={(v) => setStyle({ ...style, taboo_words: v })}
                      placeholder={t.workspace.tabooWordsPlaceholder}
                      tagClassName="bg-red-500/10 text-red-700 border-red-500/20 hover:bg-red-500/20"
                    />
                    <p className="text-xs text-muted-foreground mt-2">
                      {t.workspace.tabooWordsHint}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* 范文片段 */}
              <Card className="overflow-hidden">
                <CardHeader className="bg-gradient-to-r from-indigo-500/10 to-violet-500/10 pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                    {t.workspace.examplePassages}
                    <span className="text-xs font-normal text-muted-foreground ml-auto">
                      {style.example_passages.length} {t.workspace.passageCount}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <Textarea
                    value={style.example_passages.join("\n\n")}
                    onChange={(e) => setStyle({ ...style, example_passages: e.target.value.split("\n\n").filter(Boolean) })}
                    placeholder={t.workspace.examplePassagesPlaceholder}
                    rows={6}
                    className="resize-none"
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    {t.workspace.examplePassagesHint}
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* 规则 Tab */}
          <TabsContent value="rules" className="mt-6">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-medium">{t.workspace.writingRules}</h2>
                  <p className="text-sm text-muted-foreground">{t.workspace.rulesDescription}</p>
                </div>
                <Button onClick={handleSaveRules}>{t.workspace.saveRulesSettings}</Button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* 必须遵守 */}
                <Card className="overflow-hidden">
                  <CardHeader className="bg-gradient-to-br from-green-500/10 via-green-500/5 to-transparent pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div>
                        <div>{t.workspace.dos}</div>
                        <div className="text-xs font-normal text-muted-foreground">{t.workspace.dosLabel}</div>
                      </div>
                      <span className="text-xs font-normal text-muted-foreground ml-auto bg-green-500/10 px-2 py-0.5 rounded-full">
                        {rules.dos.length} {t.workspace.rulesCount}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <ListInput
                      value={rules.dos}
                      onChange={(v) => setRules({ ...rules, dos: v })}
                      placeholder={t.workspace.dosPlaceholder}
                      addButtonText={t.common.add}
                    />
                  </CardContent>
                </Card>

                {/* 禁止事项 */}
                <Card className="overflow-hidden">
                  <CardHeader className="bg-gradient-to-br from-red-500/10 via-red-500/5 to-transparent pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
                        <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </div>
                      <div>
                        <div>{t.workspace.donts}</div>
                        <div className="text-xs font-normal text-muted-foreground">{t.workspace.dontsLabel}</div>
                      </div>
                      <span className="text-xs font-normal text-muted-foreground ml-auto bg-red-500/10 px-2 py-0.5 rounded-full">
                        {rules.donts.length} {t.workspace.rulesCount}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <ListInput
                      value={rules.donts}
                      onChange={(v) => setRules({ ...rules, donts: v })}
                      placeholder={t.workspace.dontsPlaceholder}
                      addButtonText={t.common.add}
                    />
                  </CardContent>
                </Card>

                {/* 质量标准 */}
                <Card className="overflow-hidden">
                  <CardHeader className="bg-gradient-to-br from-amber-500/10 via-amber-500/5 to-transparent pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                        <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                        </svg>
                      </div>
                      <div>
                        <div>{t.workspace.qualityStandards}</div>
                        <div className="text-xs font-normal text-muted-foreground">{t.workspace.qualityStandardsLabel}</div>
                      </div>
                      <span className="text-xs font-normal text-muted-foreground ml-auto bg-amber-500/10 px-2 py-0.5 rounded-full">
                        {rules.quality_standards.length} {t.workspace.rulesCount}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <ListInput
                      value={rules.quality_standards}
                      onChange={(v) => setRules({ ...rules, quality_standards: v })}
                      placeholder={t.workspace.standardsPlaceholder}
                      addButtonText={t.common.add}
                    />
                  </CardContent>
                </Card>
              </div>

              {/* 规则提示 */}
              <Card className="bg-muted/30 border-dashed">
                <CardContent className="py-4">
                  <div className="flex gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <BookOpen className="w-5 h-5 text-primary" />
                    </div>
                    <div className="text-sm text-muted-foreground">
                      <p className="font-medium text-foreground mb-1">{t.workspace.rulesTips}</p>
                      <ul className="space-y-1">
                        <li>• <strong>{t.workspace.dos}</strong>: {t.workspace.dosTip}</li>
                        <li>• <strong>{t.workspace.donts}</strong>: {t.workspace.dontsTip}</li>
                        <li>• <strong>{t.workspace.qualityStandards}</strong>: {t.workspace.standardsTip}</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Canon 事实表 Tab */}
          <TabsContent value="canon" className="mt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium">{t.workspace.canonTitle}</h2>
                <p className="text-sm text-muted-foreground">{t.workspace.canonDescription}</p>
              </div>

              {/* 子标签页 */}
              <div className="flex gap-2 border-b pb-2">
                <Button
                  variant={canonSubTab === "facts" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCanonSubTab("facts")}
                >
                  <Database className="w-4 h-4 mr-1" />
                  {t.workspace.facts} ({facts.length})
                </Button>
                <Button
                  variant={canonSubTab === "timeline" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCanonSubTab("timeline")}
                >
                  <Clock className="w-4 h-4 mr-1" />
                  {t.workspace.timeline} ({timeline.length})
                </Button>
                <Button
                  variant={canonSubTab === "states" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCanonSubTab("states")}
                >
                  <Activity className="w-4 h-4 mr-1" />
                  {t.workspace.characterStates} ({characterStates.length})
                </Button>
              </div>

              {/* 事实列表 */}
              {canonSubTab === "facts" && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center gap-2">
                    <div className="flex items-center gap-2">
                      {facts.length > 0 && (
                        <>
                          <Checkbox
                            checked={selectedFactIds.size === facts.length && facts.length > 0}
                            onCheckedChange={selectAllFacts}
                          />
                          <span className="text-sm text-muted-foreground">
                            {selectedFactIds.size > 0 ? `${t.common.selected} ${selectedFactIds.size} ${t.common.items}` : t.common.selectAll}
                          </span>
                          {selectedFactIds.size > 0 && (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={handleBatchDeleteFacts}
                              disabled={batchDeleting}
                            >
                              {batchDeleting ? (
                                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                              ) : (
                                <Trash2 className="w-4 h-4 mr-1" />
                              )}
                              {t.common.batchDelete}
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={openExtractDialog} disabled={drafts.length === 0}>
                        <Sparkles className="w-4 h-4 mr-1" />
                        {t.workspace.autoExtract}
                      </Button>
                      <Button size="sm" onClick={openNewFactDialog}>
                        <Plus className="w-4 h-4 mr-1" />
                        {t.workspace.addFact}
                      </Button>
                    </div>
                  </div>
                  <ScrollArea className="h-[calc(100vh-320px)] min-h-[300px]">
                    <div className="space-y-2">
                      {facts.length === 0 ? (
                        <div className="text-center py-10 text-muted-foreground">
                          {t.workspace.noFacts}
                        </div>
                      ) : (
                        facts.map((fact) => (
                          <Card key={fact.id} className="group hover:bg-accent/50">
                            <CardContent className="flex items-start gap-3 py-3">
                              <Checkbox
                                checked={selectedFactIds.has(fact.id)}
                                onCheckedChange={() => toggleFactSelection(fact.id)}
                                onClick={(e) => e.stopPropagation()}
                                className="mt-1"
                              />
                              <div className="flex-1 cursor-pointer" onClick={() => openEditFactDialog(fact)}>
                                <p className="text-sm">{fact.statement}</p>
                                <div className="flex gap-2 mt-1 text-xs text-muted-foreground">
                                  {fact.source && <span>{t.workspace.source}: {fact.source}</span>}
                                  <span>{t.workspace.confidence}: {(fact.confidence * 100).toFixed(0)}%</span>
                                </div>
                              </div>
                              <div className="flex gap-1 opacity-0 group-hover:opacity-100">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6"
                                  onClick={(e) => { e.stopPropagation(); openEditFactDialog(fact) }}
                                >
                                  <Edit className="w-3 h-3" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6"
                                  onClick={(e) => { e.stopPropagation(); handleDeleteFact(fact.id) }}
                                >
                                  <Trash2 className="w-3 h-3 text-destructive" />
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </div>
              )}

              {/* 时间线列表 */}
              {canonSubTab === "timeline" && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center gap-2">
                    <div className="flex items-center gap-2">
                      {timeline.length > 0 && (
                        <>
                          <Checkbox
                            checked={selectedTimelineIds.size === timeline.length && timeline.length > 0}
                            onCheckedChange={selectAllTimeline}
                          />
                          <span className="text-sm text-muted-foreground">
                            {selectedTimelineIds.size > 0 ? `${t.common.selected} ${selectedTimelineIds.size} ${t.common.items}` : t.common.selectAll}
                          </span>
                          {selectedTimelineIds.size > 0 && (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={handleBatchDeleteTimeline}
                              disabled={batchDeleting}
                            >
                              {batchDeleting ? (
                                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                              ) : (
                                <Trash2 className="w-4 h-4 mr-1" />
                              )}
                              {t.common.batchDelete}
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={openExtractDialog} disabled={drafts.length === 0}>
                        <Sparkles className="w-4 h-4 mr-1" />
                        {t.workspace.autoExtract}
                      </Button>
                      <Button size="sm" onClick={openNewTimelineDialog}>
                        <Plus className="w-4 h-4 mr-1" />
                        {t.workspace.addEvent}
                      </Button>
                    </div>
                  </div>
                  <ScrollArea className="h-[calc(100vh-320px)] min-h-[300px]">
                    <div className="space-y-2">
                      {timeline.length === 0 ? (
                        <div className="text-center py-10 text-muted-foreground">
                          {t.workspace.noTimeline}
                        </div>
                      ) : (
                        timeline.map((event) => (
                          <Card key={event.id} className="group hover:bg-accent/50">
                            <CardContent className="flex items-start gap-3 py-3">
                              <Checkbox
                                checked={selectedTimelineIds.has(event.id)}
                                onCheckedChange={() => toggleTimelineSelection(event.id)}
                                onClick={(e) => e.stopPropagation()}
                                className="mt-1"
                              />
                              <div className="flex-1 cursor-pointer" onClick={() => openEditTimelineDialog(event)}>
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-medium text-primary">{event.time}</span>
                                  {event.location && <span className="text-xs text-muted-foreground">@ {event.location}</span>}
                                </div>
                                <p className="text-sm mt-1">{event.event}</p>
                                {event.participants.length > 0 && (
                                  <div className="flex gap-1 mt-1">
                                    {event.participants.map((p) => (
                                      <span key={p} className="text-xs bg-muted px-1.5 py-0.5 rounded">{p}</span>
                                    ))}
                                  </div>
                                )}
                              </div>
                              <div className="flex gap-1 opacity-0 group-hover:opacity-100">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6"
                                  onClick={(e) => { e.stopPropagation(); openEditTimelineDialog(event) }}
                                >
                                  <Edit className="w-3 h-3" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6"
                                  onClick={(e) => { e.stopPropagation(); handleDeleteTimelineEvent(event.id) }}
                                >
                                  <Trash2 className="w-3 h-3 text-destructive" />
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </div>
              )}

              {/* 角色状态列表 */}
              {canonSubTab === "states" && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center gap-2">
                    <div className="flex items-center gap-2">
                      {characterStates.length > 0 && (
                        <>
                          <Checkbox
                            checked={selectedStateKeys.size === characterStates.length && characterStates.length > 0}
                            onCheckedChange={selectAllStates}
                          />
                          <span className="text-sm text-muted-foreground">
                            {selectedStateKeys.size > 0 ? `${t.common.selected} ${selectedStateKeys.size} ${t.common.items}` : t.common.selectAll}
                          </span>
                          {selectedStateKeys.size > 0 && (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={handleBatchDeleteStates}
                              disabled={batchDeleting}
                            >
                              {batchDeleting ? (
                                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                              ) : (
                                <Trash2 className="w-4 h-4 mr-1" />
                              )}
                              {t.common.batchDelete}
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={openExtractDialog} disabled={drafts.length === 0}>
                        <Sparkles className="w-4 h-4 mr-1" />
                        {t.workspace.autoExtract}
                      </Button>
                      <Button size="sm" onClick={openNewStateDialog}>
                        <Plus className="w-4 h-4 mr-1" />
                        {t.workspace.addState}
                      </Button>
                    </div>
                  </div>
                  <ScrollArea className="h-[calc(100vh-320px)] min-h-[300px]">
                    <div className="space-y-2">
                      {characterStates.length === 0 ? (
                        <div className="text-center py-10 text-muted-foreground">
                          {t.workspace.noStates}
                        </div>
                      ) : (
                        characterStates.map((state, idx) => (
                          <Card key={`${state.character}-${state.chapter}-${idx}`} className="group hover:bg-accent/50">
                            <CardContent className="py-3">
                              <div className="flex items-start gap-3">
                                <Checkbox
                                  checked={selectedStateKeys.has(`${state.character}|${state.chapter}`)}
                                  onCheckedChange={() => toggleStateSelection(state.character, state.chapter)}
                                  onClick={(e) => e.stopPropagation()}
                                  className="mt-1"
                                />
                                <div className="flex-1 cursor-pointer" onClick={() => openEditStateDialog(state)}>
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <span className="font-medium">{state.character}</span>
                                      <span className="text-xs text-muted-foreground">{t.workspace.asOf} {state.chapter}</span>
                                    </div>
                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100">
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-6 w-6"
                                        onClick={(e) => { e.stopPropagation(); openEditStateDialog(state) }}
                                      >
                                        <Edit className="w-3 h-3" />
                                      </Button>
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-6 w-6"
                                        onClick={(e) => { e.stopPropagation(); handleDeleteState(state.character, state.chapter) }}
                                      >
                                        <Trash2 className="w-3 h-3 text-destructive" />
                                      </Button>
                                    </div>
                                  </div>
                                  <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                                    {state.location && <div><span className="text-muted-foreground">{t.workspace.locationLabel}:</span> {state.location}</div>}
                                    {state.emotional_state && <div><span className="text-muted-foreground">{t.workspace.emotionLabel}:</span> {state.emotional_state}</div>}
                                    {state.goals.length > 0 && <div className="col-span-2"><span className="text-muted-foreground">{t.workspace.goalsLabel}:</span> {state.goals.join(", ")}</div>}
                                    {state.injuries.length > 0 && <div className="col-span-2"><span className="text-muted-foreground">{t.workspace.injuriesLabel}:</span> {state.injuries.join(", ")}</div>}
                                    {state.inventory && state.inventory.length > 0 && <div className="col-span-2"><span className="text-muted-foreground">{t.workspace.inventoryLabel}:</span> {state.inventory.join(", ")}</div>}
                                    {state.relationships && Object.keys(state.relationships).length > 0 && (
                                      <div className="col-span-2">
                                        <span className="text-muted-foreground">{t.workspace.relationshipsLabel}:</span>{" "}
                                        {Object.entries(state.relationships).map(([name, rel]) => `${name}(${rel})`).join(", ")}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </div>
          </TabsContent>

          {/* 章节 Tab */}
          <TabsContent value="drafts" className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">{t.workspace.chapterList}</h2>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={openExportDialog}>
                  <Download className="w-4 h-4 mr-1" />
                  {t.workspace.exportNovel}
                </Button>
                <Button size="sm" onClick={openNewChapterDialog}>
                  <Plus className="w-4 h-4 mr-1" />
                  {t.workspace.addChapter}
                </Button>
              </div>
            </div>
            <ScrollArea className="h-[calc(100vh-320px)] min-h-[300px]">
              <div className="space-y-2">
                {drafts.length === 0 ? (
                  <div className="text-center py-10 text-muted-foreground">
                    {t.workspace.noChapters}
                  </div>
                ) : (
                  drafts.map((draft) => (
                    <Card
                      key={`${draft.chapter}-${draft.version}`}
                      className="cursor-pointer hover:bg-accent/50 transition-colors"
                      onClick={() => navigate(`/write/${projectId}?chapter=${encodeURIComponent(draft.chapter)}`)}
                    >
                      <CardContent className="flex items-center justify-between py-4">
                        <div>
                          <p className="font-medium">{draft.chapter}</p>
                          <p className="text-sm text-muted-foreground">
                            {draft.word_count} {t.common.words} · {t.workspace.version} {draft.version}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-xs px-2 py-1 rounded-full ${
                              draft.status === "final"
                                ? "bg-green-100 text-green-700"
                                : draft.status === "reviewed"
                                ? "bg-blue-100 text-blue-700"
                                : "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {draft.status === "final" ? t.workspace.final : draft.status === "reviewed" ? t.workspace.reviewed : t.workspace.draft}
                          </span>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
                            onClick={(e) => handleDeleteChapter(draft.chapter, e)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </div>

      {/* Character Dialog */}
      <Dialog open={charDialogOpen} onOpenChange={setCharDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingCharName ? t.workspace.editCharacter : t.workspace.addCharacter}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t.workspace.characterName}</Label>
              <Input
                value={charForm.name}
                onChange={(e) => setCharForm({ ...charForm, name: e.target.value })}
                placeholder={t.workspace.characterNamePlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.identity}</Label>
              <Input
                value={charForm.identity}
                onChange={(e) => setCharForm({ ...charForm, identity: e.target.value })}
                placeholder={t.workspace.identityPlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.speechPattern}</Label>
              <Input
                value={charForm.speech_pattern}
                onChange={(e) => setCharForm({ ...charForm, speech_pattern: e.target.value })}
                placeholder={t.workspace.speechPatternPlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.background}</Label>
              <Textarea
                value={charForm.background}
                onChange={(e) => setCharForm({ ...charForm, background: e.target.value })}
                placeholder={t.workspace.backgroundPlaceholder}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCharDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={handleSaveCharacter}>{t.common.save}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* World Dialog */}
      <Dialog open={worldDialogOpen} onOpenChange={setWorldDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingWorldName ? t.workspace.editSetting : t.workspace.addWorldSetting}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t.workspace.settingName}</Label>
              <Input
                value={worldForm.name}
                onChange={(e) => setWorldForm({ ...worldForm, name: e.target.value })}
                placeholder={t.workspace.settingNamePlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.category}</Label>
              <Input
                value={worldForm.category}
                onChange={(e) => setWorldForm({ ...worldForm, category: e.target.value })}
                placeholder={t.workspace.categoryPlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.settingDescription}</Label>
              <Textarea
                value={worldForm.description}
                onChange={(e) => setWorldForm({ ...worldForm, description: e.target.value })}
                placeholder={t.workspace.detailDescription}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setWorldDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={handleSaveWorld}>{t.common.save}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Fact Dialog */}
      <Dialog open={factDialogOpen} onOpenChange={setFactDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingFactId ? t.workspace.editFact : t.workspace.addFact}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t.workspace.factStatement}</Label>
              <Textarea
                value={factForm.statement}
                onChange={(e) => setFactForm({ ...factForm, statement: e.target.value })}
                placeholder={t.workspace.factStatementPlaceholder}
                rows={3}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.sourceChapter}</Label>
              <Input
                value={factForm.source}
                onChange={(e) => setFactForm({ ...factForm, source: e.target.value })}
                placeholder={t.workspace.sourceChapterPlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.confidence} ({((factForm.confidence || 1) * 100).toFixed(0)}%)</Label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={factForm.confidence}
                onChange={(e) => setFactForm({ ...factForm, confidence: parseFloat(e.target.value) })}
                className="w-full"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setFactDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={handleSaveFact}>{t.common.save}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Timeline Dialog */}
      <Dialog open={timelineDialogOpen} onOpenChange={setTimelineDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingTimelineId ? t.workspace.editEvent : t.workspace.addTimelineEvent}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t.workspace.time}</Label>
              <Input
                value={timelineForm.time}
                onChange={(e) => setTimelineForm({ ...timelineForm, time: e.target.value })}
                placeholder={t.workspace.timePlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.eventDescription}</Label>
              <Textarea
                value={timelineForm.event}
                onChange={(e) => setTimelineForm({ ...timelineForm, event: e.target.value })}
                placeholder={t.workspace.eventDescriptionPlaceholder}
                rows={3}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.location}</Label>
              <Input
                value={timelineForm.location}
                onChange={(e) => setTimelineForm({ ...timelineForm, location: e.target.value })}
                placeholder={t.workspace.locationPlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.participants}</Label>
              <Textarea
                value={(timelineForm.participants || []).join("\n")}
                onChange={(e) => setTimelineForm({ ...timelineForm, participants: e.target.value.split("\n").filter(Boolean) })}
                placeholder={t.workspace.participantsPlaceholder}
                rows={2}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.sourceChapter}</Label>
              <Input
                value={timelineForm.source}
                onChange={(e) => setTimelineForm({ ...timelineForm, source: e.target.value })}
                placeholder={t.workspace.sourceChapterPlaceholder}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTimelineDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={handleSaveTimeline}>{t.common.save}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Character State Dialog */}
      <Dialog open={stateDialogOpen} onOpenChange={setStateDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingStateKey ? t.workspace.editState : t.workspace.addState}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>{t.workspace.character}</Label>
                <select
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                  value={stateForm.character}
                  onChange={(e) => setStateForm({ ...stateForm, character: e.target.value })}
                >
                  <option value="">{t.workspace.selectCharacter}</option>
                  {characters.map((c) => (
                    <option key={c.name} value={c.name}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid gap-2">
                <Label>{t.workspace.chapter}</Label>
                <Input
                  value={stateForm.chapter}
                  onChange={(e) => setStateForm({ ...stateForm, chapter: e.target.value })}
                  placeholder={t.workspace.sourceChapterPlaceholder}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>{t.workspace.currentLocation}</Label>
                <Input
                  value={stateForm.location}
                  onChange={(e) => setStateForm({ ...stateForm, location: e.target.value })}
                  placeholder={t.workspace.currentLocationPlaceholder}
                />
              </div>
              <div className="grid gap-2">
                <Label>{t.workspace.emotionalState}</Label>
                <Input
                  value={stateForm.emotional_state}
                  onChange={(e) => setStateForm({ ...stateForm, emotional_state: e.target.value })}
                  placeholder={t.workspace.emotionalStatePlaceholder}
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.currentGoals}</Label>
              <Textarea
                value={(stateForm.goals || []).join("\n")}
                onChange={(e) => setStateForm({ ...stateForm, goals: e.target.value.split("\n").filter(Boolean) })}
                placeholder={t.workspace.currentGoalsPlaceholder}
                rows={2}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.injuries}</Label>
              <Textarea
                value={(stateForm.injuries || []).join("\n")}
                onChange={(e) => setStateForm({ ...stateForm, injuries: e.target.value.split("\n").filter(Boolean) })}
                placeholder={t.workspace.injuriesPlaceholder}
                rows={2}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.inventory}</Label>
              <Textarea
                value={(stateForm.inventory || []).join("\n")}
                onChange={(e) => setStateForm({ ...stateForm, inventory: e.target.value.split("\n").filter(Boolean) })}
                placeholder={t.workspace.inventoryPlaceholder}
                rows={2}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.relationships}</Label>
              <Textarea
                value={Object.entries(stateForm.relationships || {}).map(([k, v]) => `${k}:${v}`).join("\n")}
                onChange={(e) => {
                  const relationships: Record<string, string> = {}
                  e.target.value.split("\n").filter(Boolean).forEach(line => {
                    const [name, ...rest] = line.split(":")
                    if (name && rest.length > 0) {
                      relationships[name.trim()] = rest.join(":").trim()
                    }
                  })
                  setStateForm({ ...stateForm, relationships })
                }}
                placeholder={t.workspace.relationshipsPlaceholder}
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setStateDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={handleSaveState}>{t.common.save}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Chapter Dialog */}
      <Dialog open={chapterDialogOpen} onOpenChange={setChapterDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.workspace.createChapter}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t.writing.chapterNumber}</Label>
              <Input
                value={chapterForm.number}
                onChange={(e) => setChapterForm({ ...chapterForm, number: e.target.value })}
                placeholder={t.writing.chapterNumberPlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.chapterTitle}</Label>
              <Input
                value={chapterForm.title}
                onChange={(e) => setChapterForm({ ...chapterForm, title: e.target.value })}
                placeholder={t.workspace.chapterTitlePlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.workspace.chapterOutline}</Label>
              <Textarea
                value={chapterForm.outline}
                onChange={(e) => setChapterForm({ ...chapterForm, outline: e.target.value })}
                placeholder={t.workspace.chapterOutlinePlaceholder}
                rows={5}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setChapterDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={handleStartWriting}>
              <Pen className="w-4 h-4 mr-1" />
              {t.workspace.startCreating}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.workspace.exportTitle}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {exportInfo && (
              <div className="p-4 bg-muted rounded-lg">
                <div className="flex justify-between text-sm">
                  <span>{t.workspace.chapterCount}</span>
                  <span className="font-medium">{exportInfo.chapter_count} {t.common.chapters}</span>
                </div>
                <div className="flex justify-between text-sm mt-2">
                  <span>{t.workspace.totalWords}</span>
                  <span className="font-medium">{exportInfo.total_words.toLocaleString()} {t.common.words}</span>
                </div>
              </div>
            )}

            <div className="grid gap-2">
              <Label>{t.workspace.exportFormat}</Label>
              <div className="flex gap-2">
                <Button
                  variant={exportFormat === "txt" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setExportFormat("txt")}
                >
                  TXT
                </Button>
                <Button
                  variant={exportFormat === "markdown" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setExportFormat("markdown")}
                >
                  Markdown
                </Button>
                <Button
                  variant={exportFormat === "epub" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setExportFormat("epub")}
                >
                  EPUB
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                {exportFormat === "txt" && t.workspace.txtDescription}
                {exportFormat === "markdown" && t.workspace.markdownDescription}
                {exportFormat === "epub" && t.workspace.epubDescription}
              </p>
            </div>

            <div className="grid gap-2">
              <Label>{t.workspace.contentSource}</Label>
              <div className="flex gap-2">
                <Button
                  variant={exportUseFinal ? "default" : "outline"}
                  size="sm"
                  onClick={() => setExportUseFinal(true)}
                >
                  {t.workspace.finalFirst}
                </Button>
                <Button
                  variant={!exportUseFinal ? "default" : "outline"}
                  size="sm"
                  onClick={() => setExportUseFinal(false)}
                >
                  {t.workspace.latestDraft}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                {exportUseFinal
                  ? t.workspace.finalFirstDesc
                  : t.workspace.latestDraftDesc}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setExportDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={handleExport} disabled={exporting || !exportInfo?.chapter_count}>
              {exporting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                  {t.workspace.exporting}
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-1" />
                  {t.workspace.export}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 自动提取对话框 */}
      <Dialog open={extractDialogOpen} onOpenChange={setExtractDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.workspace.extractTitle}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t.workspace.selectChapter}</Label>
              <Select value={extractChapter} onValueChange={setExtractChapter}>
                <SelectTrigger>
                  <SelectValue placeholder={t.workspace.selectChapterPlaceholder} />
                </SelectTrigger>
                <SelectContent>
                  {drafts.map((draft) => (
                    <SelectItem key={draft.chapter} value={draft.chapter}>
                      {draft.chapter}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {t.workspace.extractHint}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setExtractDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={handleAIExtract} disabled={extracting || !extractChapter}>
              {extracting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                  {t.workspace.extracting}
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-1" />
                  {t.workspace.startExtract}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 项目编辑对话框 */}
      <Dialog open={projectDialogOpen} onOpenChange={setProjectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.workspace.editProjectTitle}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t.projectList.projectName}</Label>
              <Input
                value={projectForm.name}
                onChange={(e) => setProjectForm({ ...projectForm, name: e.target.value })}
                placeholder={t.projectList.projectNamePlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.projectList.author}</Label>
              <Input
                value={projectForm.author}
                onChange={(e) => setProjectForm({ ...projectForm, author: e.target.value })}
                placeholder={t.projectList.authorPlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.projectList.genre}</Label>
              <Input
                value={projectForm.genre}
                onChange={(e) => setProjectForm({ ...projectForm, genre: e.target.value })}
                placeholder={t.projectList.genrePlaceholder}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t.projectList.description}</Label>
              <Textarea
                value={projectForm.description}
                onChange={(e) => setProjectForm({ ...projectForm, description: e.target.value })}
                placeholder={t.projectList.descriptionPlaceholder}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setProjectDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={handleSaveProject}>{t.common.save}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
