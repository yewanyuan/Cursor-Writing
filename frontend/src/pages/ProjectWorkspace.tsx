import { useState, useEffect } from "react"
import { useParams, useNavigate, useSearchParams } from "react-router-dom"
import { motion } from "framer-motion"
import { ArrowLeft, Plus, User, Globe, FileText, Pen, Trash2, Edit, BookOpen, Shield, Database, Clock, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { projectApi, cardApi, draftApi, canonApi } from "@/api"
import type { Project, CharacterCard, WorldCard, StyleCard, RulesCard, Draft, Fact, TimelineEvent, CharacterState } from "@/types"

export default function ProjectWorkspace() {
  const { projectId } = useParams<{ projectId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
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
    title: "",
    outline: "",
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
    if (!projectId || !confirm(`确定删除角色 "${name}"？`)) return
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
    if (!projectId || !confirm(`确定删除设定 "${name}"？`)) return
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
      alert("文风设置已保存")
    } catch (err) {
      console.error("Failed to save style:", err)
    }
  }

  // 规则卡保存
  const handleSaveRules = async () => {
    if (!projectId) return
    try {
      await cardApi.saveRules(projectId, rules)
      alert("规则设置已保存")
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
    if (!projectId || !confirm("确定删除此事实？")) return
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
    if (!projectId || !confirm("确定删除此事件？")) return
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
    if (!projectId || !confirm(`确定删除 ${character} 在 ${chapter} 的状态？`)) return
    try {
      await canonApi.deleteCharacterState(projectId, character, chapter)
      loadData()
    } catch (err) {
      console.error("Failed to delete character state:", err)
    }
  }

  // 章节相关
  const openNewChapterDialog = () => {
    // 自动生成下一章的标题
    const nextChapterNum = drafts.length + 1
    setChapterForm({
      title: `第${nextChapterNum}章`,
      outline: "",
    })
    setChapterDialogOpen(true)
  }

  const handleStartWriting = () => {
    if (!projectId || !chapterForm.title) return
    // 跳转到写作页面，带上章节标题和大纲
    const params = new URLSearchParams({
      chapter: chapterForm.title,
      ...(chapterForm.outline && { outline: chapterForm.outline }),
    })
    setChapterDialogOpen(false)
    navigate(`/write/${projectId}?${params.toString()}`)
  }

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">加载中...</div>
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
            <div className="flex-1">
              <h1 className="text-xl font-semibold">{project.name}</h1>
              <p className="text-sm text-muted-foreground">{project.genre}</p>
            </div>
            <Button onClick={() => navigate(`/write/${projectId}`)}>
              <Pen className="w-4 h-4 mr-2" />
              开始写作
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="characters" className="gap-2">
              <User className="w-4 h-4" />
              角色
            </TabsTrigger>
            <TabsTrigger value="world" className="gap-2">
              <Globe className="w-4 h-4" />
              世界观
            </TabsTrigger>
            <TabsTrigger value="style" className="gap-2">
              <BookOpen className="w-4 h-4" />
              文风
            </TabsTrigger>
            <TabsTrigger value="rules" className="gap-2">
              <Shield className="w-4 h-4" />
              规则
            </TabsTrigger>
            <TabsTrigger value="canon" className="gap-2">
              <Database className="w-4 h-4" />
              事实表
            </TabsTrigger>
            <TabsTrigger value="drafts" className="gap-2">
              <FileText className="w-4 h-4" />
              章节
            </TabsTrigger>
          </TabsList>

          {/* 角色 Tab */}
          <TabsContent value="characters" className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">角色设定</h2>
              <Button size="sm" onClick={openNewCharDialog}>
                <Plus className="w-4 h-4 mr-1" />
                添加角色
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
                      <p className="text-sm line-clamp-3">{char.background || "暂无背景介绍"}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </TabsContent>

          {/* 世界观 Tab */}
          <TabsContent value="world" className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">世界观设定</h2>
              <Button size="sm" onClick={openNewWorldDialog}>
                <Plus className="w-4 h-4 mr-1" />
                添加设定
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
            <div className="max-w-2xl space-y-6">
              <h2 className="text-lg font-medium">文风设定</h2>

              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label>叙事距离</Label>
                  <select
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                    value={style.narrative_distance}
                    onChange={(e) => setStyle({ ...style, narrative_distance: e.target.value })}
                  >
                    <option value="close">近距离（第一人称/深度内心）</option>
                    <option value="medium">中距离（有限第三人称）</option>
                    <option value="far">远距离（全知视角）</option>
                  </select>
                </div>

                <div className="grid gap-2">
                  <Label>叙事节奏</Label>
                  <select
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                    value={style.pacing}
                    onChange={(e) => setStyle({ ...style, pacing: e.target.value })}
                  >
                    <option value="fast">快节奏（动作密集）</option>
                    <option value="moderate">中等节奏（平衡）</option>
                    <option value="slow">慢节奏（细腻描写）</option>
                  </select>
                </div>

                <div className="grid gap-2">
                  <Label>句式偏好</Label>
                  <Textarea
                    value={style.sentence_style}
                    onChange={(e) => setStyle({ ...style, sentence_style: e.target.value })}
                    placeholder="描述你偏好的句式风格，如：短句为主、多用比喻、少用被动语态等"
                    rows={2}
                  />
                </div>

                <div className="grid gap-2">
                  <Label>常用词汇（每行一个）</Label>
                  <Textarea
                    value={style.vocabulary.join("\n")}
                    onChange={(e) => setStyle({ ...style, vocabulary: e.target.value.split("\n").filter(Boolean) })}
                    placeholder="希望 AI 多使用的词汇"
                    rows={3}
                  />
                </div>

                <div className="grid gap-2">
                  <Label>禁用词汇（每行一个）</Label>
                  <Textarea
                    value={style.taboo_words.join("\n")}
                    onChange={(e) => setStyle({ ...style, taboo_words: e.target.value.split("\n").filter(Boolean) })}
                    placeholder="禁止 AI 使用的词汇"
                    rows={3}
                  />
                </div>

                <div className="grid gap-2">
                  <Label>范文片段（每段用空行分隔）</Label>
                  <Textarea
                    value={style.example_passages.join("\n\n")}
                    onChange={(e) => setStyle({ ...style, example_passages: e.target.value.split("\n\n").filter(Boolean) })}
                    placeholder="粘贴你喜欢的文风示例，AI 会参考模仿"
                    rows={6}
                  />
                </div>
              </div>

              <Button onClick={handleSaveStyle}>保存文风设置</Button>
            </div>
          </TabsContent>

          {/* 规则 Tab */}
          <TabsContent value="rules" className="mt-6">
            <div className="max-w-2xl space-y-6">
              <h2 className="text-lg font-medium">写作规则</h2>

              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label>必须遵守（每行一条）</Label>
                  <Textarea
                    value={rules.dos.join("\n")}
                    onChange={(e) => setRules({ ...rules, dos: e.target.value.split("\n").filter(Boolean) })}
                    placeholder="例如：每章必须有冲突、对话要推动剧情"
                    rows={4}
                  />
                </div>

                <div className="grid gap-2">
                  <Label>禁止事项（每行一条）</Label>
                  <Textarea
                    value={rules.donts.join("\n")}
                    onChange={(e) => setRules({ ...rules, donts: e.target.value.split("\n").filter(Boolean) })}
                    placeholder="例如：不许写死主角、不许出现现代用语"
                    rows={4}
                  />
                </div>

                <div className="grid gap-2">
                  <Label>质量标准（每行一条）</Label>
                  <Textarea
                    value={rules.quality_standards.join("\n")}
                    onChange={(e) => setRules({ ...rules, quality_standards: e.target.value.split("\n").filter(Boolean) })}
                    placeholder="例如：对话占比不超过50%、描写要有画面感"
                    rows={4}
                  />
                </div>
              </div>

              <Button onClick={handleSaveRules}>保存规则设置</Button>
            </div>
          </TabsContent>

          {/* Canon 事实表 Tab */}
          <TabsContent value="canon" className="mt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium">事实表</h2>
                <p className="text-sm text-muted-foreground">记录故事中已发生的事实，保持一致性</p>
              </div>

              {/* 子标签页 */}
              <div className="flex gap-2 border-b pb-2">
                <Button
                  variant={canonSubTab === "facts" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCanonSubTab("facts")}
                >
                  <Database className="w-4 h-4 mr-1" />
                  事实 ({facts.length})
                </Button>
                <Button
                  variant={canonSubTab === "timeline" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCanonSubTab("timeline")}
                >
                  <Clock className="w-4 h-4 mr-1" />
                  时间线 ({timeline.length})
                </Button>
                <Button
                  variant={canonSubTab === "states" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCanonSubTab("states")}
                >
                  <Activity className="w-4 h-4 mr-1" />
                  角色状态 ({characterStates.length})
                </Button>
              </div>

              {/* 事实列表 */}
              {canonSubTab === "facts" && (
                <div className="space-y-4">
                  <div className="flex justify-end">
                    <Button size="sm" onClick={openNewFactDialog}>
                      <Plus className="w-4 h-4 mr-1" />
                      添加事实
                    </Button>
                  </div>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {facts.length === 0 ? (
                        <div className="text-center py-10 text-muted-foreground">
                          暂无事实记录
                        </div>
                      ) : (
                        facts.map((fact) => (
                          <Card key={fact.id} className="group cursor-pointer hover:bg-accent/50" onClick={() => openEditFactDialog(fact)}>
                            <CardContent className="flex items-start justify-between py-3">
                              <div className="flex-1">
                                <p className="text-sm">{fact.statement}</p>
                                <div className="flex gap-2 mt-1 text-xs text-muted-foreground">
                                  {fact.source && <span>来源: {fact.source}</span>}
                                  <span>置信度: {(fact.confidence * 100).toFixed(0)}%</span>
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
                  <div className="flex justify-end">
                    <Button size="sm" onClick={openNewTimelineDialog}>
                      <Plus className="w-4 h-4 mr-1" />
                      添加事件
                    </Button>
                  </div>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {timeline.length === 0 ? (
                        <div className="text-center py-10 text-muted-foreground">
                          暂无时间线事件
                        </div>
                      ) : (
                        timeline.map((event) => (
                          <Card key={event.id} className="group cursor-pointer hover:bg-accent/50" onClick={() => openEditTimelineDialog(event)}>
                            <CardContent className="flex items-start justify-between py-3">
                              <div className="flex-1">
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
                  <div className="flex justify-end">
                    <Button size="sm" onClick={openNewStateDialog}>
                      <Plus className="w-4 h-4 mr-1" />
                      添加状态
                    </Button>
                  </div>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {characterStates.length === 0 ? (
                        <div className="text-center py-10 text-muted-foreground">
                          暂无角色状态记录
                        </div>
                      ) : (
                        characterStates.map((state, idx) => (
                          <Card key={`${state.character}-${state.chapter}-${idx}`} className="group cursor-pointer hover:bg-accent/50" onClick={() => openEditStateDialog(state)}>
                            <CardContent className="py-3">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{state.character}</span>
                                  <span className="text-xs text-muted-foreground">截止 {state.chapter}</span>
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
                                {state.location && <div><span className="text-muted-foreground">位置:</span> {state.location}</div>}
                                {state.emotional_state && <div><span className="text-muted-foreground">情绪:</span> {state.emotional_state}</div>}
                                {state.goals.length > 0 && <div className="col-span-2"><span className="text-muted-foreground">目标:</span> {state.goals.join(", ")}</div>}
                                {state.injuries.length > 0 && <div className="col-span-2"><span className="text-muted-foreground">伤势:</span> {state.injuries.join(", ")}</div>}
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
              <h2 className="text-lg font-medium">章节列表</h2>
              <Button size="sm" onClick={openNewChapterDialog}>
                <Plus className="w-4 h-4 mr-1" />
                添加章节
              </Button>
            </div>
            <ScrollArea className="h-[500px]">
              <div className="space-y-2">
                {drafts.length === 0 ? (
                  <div className="text-center py-10 text-muted-foreground">
                    暂无章节，点击上方"添加章节"开始创作
                  </div>
                ) : (
                  drafts.map((draft) => (
                    <Card
                      key={`${draft.chapter}-${draft.version}`}
                      className="cursor-pointer hover:bg-accent/50 transition-colors"
                      onClick={() => navigate(`/write/${projectId}?chapter=${draft.chapter}`)}
                    >
                      <CardContent className="flex items-center justify-between py-4">
                        <div>
                          <p className="font-medium">{draft.chapter}</p>
                          <p className="text-sm text-muted-foreground">
                            {draft.word_count} 字 · 版本 {draft.version}
                          </p>
                        </div>
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            draft.status === "final"
                              ? "bg-green-100 text-green-700"
                              : draft.status === "reviewed"
                              ? "bg-blue-100 text-blue-700"
                              : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {draft.status === "final" ? "定稿" : draft.status === "reviewed" ? "已审" : "草稿"}
                        </span>
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
            <DialogTitle>{editingCharName ? "编辑角色" : "添加角色"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>名称</Label>
              <Input
                value={charForm.name}
                onChange={(e) => setCharForm({ ...charForm, name: e.target.value })}
                placeholder="角色名称"
              />
            </div>
            <div className="grid gap-2">
              <Label>身份</Label>
              <Input
                value={charForm.identity}
                onChange={(e) => setCharForm({ ...charForm, identity: e.target.value })}
                placeholder="如：主角、反派"
              />
            </div>
            <div className="grid gap-2">
              <Label>语言风格</Label>
              <Input
                value={charForm.speech_pattern}
                onChange={(e) => setCharForm({ ...charForm, speech_pattern: e.target.value })}
                placeholder="角色的说话方式"
              />
            </div>
            <div className="grid gap-2">
              <Label>背景</Label>
              <Textarea
                value={charForm.background}
                onChange={(e) => setCharForm({ ...charForm, background: e.target.value })}
                placeholder="角色的背景故事"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCharDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSaveCharacter}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* World Dialog */}
      <Dialog open={worldDialogOpen} onOpenChange={setWorldDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingWorldName ? "编辑世界观设定" : "添加世界观设定"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>名称</Label>
              <Input
                value={worldForm.name}
                onChange={(e) => setWorldForm({ ...worldForm, name: e.target.value })}
                placeholder="设定名称"
              />
            </div>
            <div className="grid gap-2">
              <Label>分类</Label>
              <Input
                value={worldForm.category}
                onChange={(e) => setWorldForm({ ...worldForm, category: e.target.value })}
                placeholder="如：修炼体系、地理环境"
              />
            </div>
            <div className="grid gap-2">
              <Label>描述</Label>
              <Textarea
                value={worldForm.description}
                onChange={(e) => setWorldForm({ ...worldForm, description: e.target.value })}
                placeholder="详细描述"
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setWorldDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSaveWorld}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Fact Dialog */}
      <Dialog open={factDialogOpen} onOpenChange={setFactDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingFactId ? "编辑事实" : "添加事实"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>事实陈述</Label>
              <Textarea
                value={factForm.statement}
                onChange={(e) => setFactForm({ ...factForm, statement: e.target.value })}
                placeholder="描述一个已经发生的事实"
                rows={3}
              />
            </div>
            <div className="grid gap-2">
              <Label>来源章节</Label>
              <Input
                value={factForm.source}
                onChange={(e) => setFactForm({ ...factForm, source: e.target.value })}
                placeholder="如：第一章"
              />
            </div>
            <div className="grid gap-2">
              <Label>置信度 ({((factForm.confidence || 1) * 100).toFixed(0)}%)</Label>
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
              取消
            </Button>
            <Button onClick={handleSaveFact}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Timeline Dialog */}
      <Dialog open={timelineDialogOpen} onOpenChange={setTimelineDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingTimelineId ? "编辑时间线事件" : "添加时间线事件"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>时间</Label>
              <Input
                value={timelineForm.time}
                onChange={(e) => setTimelineForm({ ...timelineForm, time: e.target.value })}
                placeholder="如：第一天清晨、三年前"
              />
            </div>
            <div className="grid gap-2">
              <Label>事件描述</Label>
              <Textarea
                value={timelineForm.event}
                onChange={(e) => setTimelineForm({ ...timelineForm, event: e.target.value })}
                placeholder="发生了什么"
                rows={3}
              />
            </div>
            <div className="grid gap-2">
              <Label>地点</Label>
              <Input
                value={timelineForm.location}
                onChange={(e) => setTimelineForm({ ...timelineForm, location: e.target.value })}
                placeholder="事件发生地点"
              />
            </div>
            <div className="grid gap-2">
              <Label>参与者（每行一个）</Label>
              <Textarea
                value={(timelineForm.participants || []).join("\n")}
                onChange={(e) => setTimelineForm({ ...timelineForm, participants: e.target.value.split("\n").filter(Boolean) })}
                placeholder="参与此事件的角色"
                rows={2}
              />
            </div>
            <div className="grid gap-2">
              <Label>来源章节</Label>
              <Input
                value={timelineForm.source}
                onChange={(e) => setTimelineForm({ ...timelineForm, source: e.target.value })}
                placeholder="如：第一章"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTimelineDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSaveTimeline}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Character State Dialog */}
      <Dialog open={stateDialogOpen} onOpenChange={setStateDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingStateKey ? "编辑角色状态" : "添加角色状态"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>角色</Label>
                <select
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                  value={stateForm.character}
                  onChange={(e) => setStateForm({ ...stateForm, character: e.target.value })}
                >
                  <option value="">选择角色</option>
                  {characters.map((c) => (
                    <option key={c.name} value={c.name}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid gap-2">
                <Label>截止章节</Label>
                <Input
                  value={stateForm.chapter}
                  onChange={(e) => setStateForm({ ...stateForm, chapter: e.target.value })}
                  placeholder="如：第一章"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>当前位置</Label>
                <Input
                  value={stateForm.location}
                  onChange={(e) => setStateForm({ ...stateForm, location: e.target.value })}
                  placeholder="角色当前所在地"
                />
              </div>
              <div className="grid gap-2">
                <Label>情绪状态</Label>
                <Input
                  value={stateForm.emotional_state}
                  onChange={(e) => setStateForm({ ...stateForm, emotional_state: e.target.value })}
                  placeholder="如：愤怒、悲伤"
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>当前目标（每行一个）</Label>
              <Textarea
                value={(stateForm.goals || []).join("\n")}
                onChange={(e) => setStateForm({ ...stateForm, goals: e.target.value.split("\n").filter(Boolean) })}
                placeholder="角色当前的目标"
                rows={2}
              />
            </div>
            <div className="grid gap-2">
              <Label>伤势（每行一个）</Label>
              <Textarea
                value={(stateForm.injuries || []).join("\n")}
                onChange={(e) => setStateForm({ ...stateForm, injuries: e.target.value.split("\n").filter(Boolean) })}
                placeholder="角色当前的伤势"
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setStateDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSaveState}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Chapter Dialog */}
      <Dialog open={chapterDialogOpen} onOpenChange={setChapterDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>创建新章节</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>章节标题</Label>
              <Input
                value={chapterForm.title}
                onChange={(e) => setChapterForm({ ...chapterForm, title: e.target.value })}
                placeholder="如：第一章 初入江湖"
              />
            </div>
            <div className="grid gap-2">
              <Label>章节大纲（可选）</Label>
              <Textarea
                value={chapterForm.outline}
                onChange={(e) => setChapterForm({ ...chapterForm, outline: e.target.value })}
                placeholder="描述这一章的主要情节和要点，AI 会根据大纲进行创作"
                rows={5}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setChapterDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleStartWriting}>
              <Pen className="w-4 h-4 mr-1" />
              开始创作
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
