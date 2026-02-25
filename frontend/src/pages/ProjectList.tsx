import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { Plus, BookOpen, Trash2, Calendar, User, Settings, Upload, FileText, Loader2, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { ThemeToggle } from "@/components/ThemeToggle"
import { LanguageToggle } from "@/components/LanguageToggle"
import { useLanguage } from "@/i18n"
import { projectApi, importApi } from "@/api"
import type { Project, ProjectCreate } from "@/types"

export default function ProjectList() {
  const navigate = useNavigate()
  const { t } = useLanguage()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [newProject, setNewProject] = useState<ProjectCreate>({
    name: "",
    author: "",
    genre: "",
    description: "",
  })

  // 导入相关状态
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [importStep, setImportStep] = useState<"upload" | "preview" | "importing">("upload")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewData, setPreviewData] = useState<{
    title: string
    author: string
    description: string
    chapter_count: number
    total_words: number
    chapters: Array<{ chapter_name: string; title: string; word_count: number }>
  } | null>(null)
  const [importOptions, setImportOptions] = useState({
    projectName: "",
    genre: "",
    analyze: true,
  })
  const [importing, setImporting] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const res = await projectApi.list()
      setProjects(res.data)
    } catch (err) {
      console.error("Failed to load projects:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!newProject.name || !newProject.author || !newProject.genre) return
    try {
      await projectApi.create(newProject)
      setDialogOpen(false)
      setNewProject({ name: "", author: "", genre: "", description: "" })
      loadProjects()
    } catch (err) {
      console.error("Failed to create project:", err)
    }
  }

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm(t.projectList.deleteConfirm)) return
    try {
      await projectApi.delete(id)
      loadProjects()
    } catch (err) {
      console.error("Failed to delete project:", err)
    }
  }

  // 导入相关函数
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setSelectedFile(file)
    setPreviewLoading(true)

    try {
      const res = await importApi.preview(file)
      if (res.data.success) {
        setPreviewData(res.data)
        setImportOptions(prev => ({
          ...prev,
          projectName: res.data.title,
        }))
        setImportStep("preview")
      } else {
        alert(`${t.projectList.parseFailed}: ${res.data.message}`)
        resetImportDialog()
      }
    } catch (err: unknown) {
      console.error("Failed to preview:", err)
      const errorMessage = err instanceof Error ? err.message : t.projectList.unknownError
      alert(`${t.projectList.parseFailed}: ${errorMessage}`)
      resetImportDialog()
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleImport = async () => {
    if (!selectedFile) return

    setImporting(true)
    setImportStep("importing")

    try {
      const res = await importApi.import(selectedFile, {
        projectName: importOptions.projectName || previewData?.title,
        genre: importOptions.genre || undefined,
        analyze: importOptions.analyze,
      })

      if (res.data.success) {
        alert(res.data.message)
        setImportDialogOpen(false)
        resetImportDialog()
        loadProjects()
        // 导入成功后跳转到项目页面
        navigate(`/project/${res.data.project_id}`)
      } else {
        alert(t.projectList.importFailed)
        setImportStep("preview")
      }
    } catch (err: unknown) {
      console.error("Failed to import:", err)
      const errorMessage = err instanceof Error ? err.message : t.projectList.unknownError
      alert(`${t.projectList.importFailed}: ${errorMessage}`)
      setImportStep("preview")
    } finally {
      setImporting(false)
    }
  }

  const resetImportDialog = () => {
    setImportStep("upload")
    setSelectedFile(null)
    setPreviewData(null)
    setImportOptions({ projectName: "", genre: "", analyze: true })
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const openImportDialog = () => {
    resetImportDialog()
    setImportDialogOpen(true)
  }

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  }

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t.projectList.title}</h1>
            <p className="text-muted-foreground mt-1">{t.projectList.subtitle}</p>
          </div>
          <div className="flex gap-2">
            <LanguageToggle />
            <ThemeToggle />
            <Button variant="outline" size="icon" onClick={() => navigate("/settings")}>
              <Settings className="w-4 h-4" />
            </Button>
            <Button variant="outline" onClick={openImportDialog}>
              <Upload className="w-4 h-4 mr-2" />
              {t.projectList.importNovel}
            </Button>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  {t.projectList.newProject}
                </Button>
              </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t.projectList.createTitle}</DialogTitle>
                <DialogDescription>{t.projectList.createDescription}</DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">{t.projectList.projectName}</Label>
                  <Input
                    id="name"
                    value={newProject.name}
                    onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                    placeholder={t.projectList.projectNamePlaceholder}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="author">{t.projectList.author}</Label>
                  <Input
                    id="author"
                    value={newProject.author}
                    onChange={(e) => setNewProject({ ...newProject, author: e.target.value })}
                    placeholder={t.projectList.authorPlaceholder}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="genre">{t.projectList.genre}</Label>
                  <Input
                    id="genre"
                    value={newProject.genre}
                    onChange={(e) => setNewProject({ ...newProject, genre: e.target.value })}
                    placeholder={t.projectList.genrePlaceholder}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">{t.projectList.description}</Label>
                  <Textarea
                    id="description"
                    value={newProject.description}
                    onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                    placeholder={t.projectList.descriptionPlaceholder}
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)}>
                  {t.common.cancel}
                </Button>
                <Button onClick={handleCreate}>{t.common.create}</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="animate-pulse">
                <CardHeader>
                  <div className="h-6 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-1/2 mt-2" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 bg-muted rounded w-full" />
                  <div className="h-4 bg-muted rounded w-2/3 mt-2" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-20">
            <BookOpen className="w-16 h-16 mx-auto text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-medium">{t.projectList.noProjects}</h3>
            <p className="text-muted-foreground mt-1">{t.projectList.noProjectsHint}</p>
          </div>
        ) : (
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            variants={container}
            initial="hidden"
            animate="show"
          >
            {projects.map((project) => (
              <motion.div key={project.id} variants={item}>
                <Card
                  className="cursor-pointer hover:shadow-lg transition-shadow group"
                  onClick={() => navigate(`/project/${project.id}`)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="group-hover:text-primary transition-colors">
                          {project.name}
                        </CardTitle>
                        <CardDescription className="mt-1">{project.genre}</CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => handleDelete(project.id, e)}
                      >
                        <Trash2 className="w-4 h-4 text-destructive" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {project.description || t.projectList.noDescription}
                    </p>
                    <div className="flex items-center gap-4 mt-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {project.author}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {new Date(project.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>

      {/* 导入小说对话框 */}
      <Dialog open={importDialogOpen} onOpenChange={(open) => {
        if (!open) resetImportDialog()
        setImportDialogOpen(open)
      }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{t.projectList.importTitle}</DialogTitle>
            <DialogDescription>
              {importStep === "upload" && t.projectList.importUploadHint}
              {importStep === "preview" && t.projectList.importPreviewHint}
              {importStep === "importing" && t.projectList.importingHint}
            </DialogDescription>
          </DialogHeader>

          {/* 上传步骤 */}
          {importStep === "upload" && (
            <div className="py-8">
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md,.markdown,.epub,.pdf"
                onChange={handleFileSelect}
                className="hidden"
              />
              <div
                className="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:border-primary transition-colors"
                onClick={() => fileInputRef.current?.click()}
              >
                {previewLoading ? (
                  <>
                    <Loader2 className="w-12 h-12 mx-auto text-muted-foreground animate-spin" />
                    <p className="mt-4 text-muted-foreground">{t.projectList.parsingFile}</p>
                  </>
                ) : (
                  <>
                    <Upload className="w-12 h-12 mx-auto text-muted-foreground" />
                    <p className="mt-4 text-muted-foreground">{t.projectList.uploadHint}</p>
                    <p className="text-xs text-muted-foreground mt-2">{t.projectList.supportedFormats}</p>
                  </>
                )}
              </div>
            </div>
          )}

          {/* 预览步骤 */}
          {importStep === "preview" && previewData && (
            <div className="grid gap-4 py-4">
              <div className="p-4 bg-muted rounded-lg">
                <div className="flex justify-between text-sm">
                  <span>{t.projectList.parseResult}</span>
                  <span className="font-medium">{previewData.chapter_count} {t.common.chapters} / {previewData.total_words.toLocaleString()} {t.common.words}</span>
                </div>
              </div>

              <div className="grid gap-2">
                <Label>{t.projectList.projectName}</Label>
                <Input
                  value={importOptions.projectName}
                  onChange={(e) => setImportOptions(prev => ({ ...prev, projectName: e.target.value }))}
                  placeholder={previewData.title}
                />
              </div>

              <div className="grid gap-2">
                <Label>{t.projectList.novelType}</Label>
                <Input
                  value={importOptions.genre}
                  onChange={(e) => setImportOptions(prev => ({ ...prev, genre: e.target.value }))}
                  placeholder={t.projectList.genrePlaceholder}
                />
              </div>

              <div className="flex items-center gap-2">
                <Checkbox
                  id="analyze"
                  checked={importOptions.analyze}
                  onCheckedChange={(checked) => setImportOptions(prev => ({ ...prev, analyze: !!checked }))}
                />
                <Label htmlFor="analyze" className="flex items-center gap-2 cursor-pointer">
                  <Sparkles className="w-4 h-4" />
                  {t.projectList.aiAnalyze}
                </Label>
              </div>

              <div className="grid gap-2">
                <Label>{t.projectList.chapterList}</Label>
                <ScrollArea className="h-48 border rounded-lg">
                  <div className="p-2 space-y-1">
                    {previewData.chapters.map((ch, idx) => (
                      <div key={idx} className="flex justify-between text-sm py-1 px-2 hover:bg-muted rounded">
                        <span>
                          <span className="font-medium">{ch.chapter_name}</span>
                          {ch.title && <span className="text-muted-foreground ml-2">{ch.title}</span>}
                        </span>
                        <span className="text-muted-foreground">{ch.word_count} {t.common.words}</span>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            </div>
          )}

          {/* 导入中步骤 */}
          {importStep === "importing" && (
            <div className="py-12 text-center">
              <Loader2 className="w-12 h-12 mx-auto text-primary animate-spin" />
              <p className="mt-4 text-muted-foreground">
                {importOptions.analyze ? t.projectList.importingWithAI : t.projectList.importingSimple}
              </p>
              {importOptions.analyze && (
                <p className="text-xs text-muted-foreground mt-2">
                  {t.projectList.aiAnalyzeHint}
                </p>
              )}
            </div>
          )}

          <DialogFooter>
            {importStep === "upload" && (
              <Button variant="outline" onClick={() => setImportDialogOpen(false)}>
                {t.common.cancel}
              </Button>
            )}
            {importStep === "preview" && (
              <>
                <Button variant="outline" onClick={resetImportDialog}>
                  {t.common.reselect}
                </Button>
                <Button onClick={handleImport} disabled={importing}>
                  <FileText className="w-4 h-4 mr-2" />
                  {t.projectList.startImport}
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
