import { useState, useEffect } from "react"
import { useParams, useNavigate, useSearchParams } from "react-router-dom"
import {
  ArrowLeft,
  FileText,
  CheckCircle,
  Clock,
  TrendingUp,
  BarChart3,
  Calendar,
  Target,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ThemeToggle } from "@/components/ThemeToggle"
import { LanguageToggle } from "@/components/LanguageToggle"
import { useLanguage } from "@/i18n"
import { statsApi } from "@/api"

interface Overview {
  total_words: number
  total_chapters: number
  completed_chapters: number
  draft_chapters: number
  total_versions: number
  avg_words_per_chapter: number
  writing_days: number
  first_created: string | null
  last_updated: string | null
  completion_rate: number
}

interface TrendItem {
  date: string
  words: number
  daily_words: number
}

interface ProgressItem {
  chapter: string
  word_count: number
  status: string
  version_count: number
  progress: number
}

export default function StatsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { t, language } = useLanguage()
  const fromTab = searchParams.get("from") || "characters"

  const [overview, setOverview] = useState<Overview | null>(null)
  const [trend, setTrend] = useState<TrendItem[]>([])
  const [progress, setProgress] = useState<ProgressItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (projectId) loadData()
  }, [projectId])

  const loadData = async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const [overviewRes, trendRes, progressRes] = await Promise.all([
        statsApi.getOverview(projectId),
        statsApi.getTrend(projectId, 30),
        statsApi.getProgress(projectId),
      ])
      setOverview(overviewRes.data)
      setTrend(trendRes.data)
      setProgress(progressRes.data)
    } catch (err) {
      console.error("Failed to load stats:", err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-"
    return new Date(dateStr).toLocaleDateString(language === "zh" ? "zh-CN" : "en-US")
  }

  // 计算趋势图的最大值
  const maxWords = Math.max(...trend.map((t) => t.words), 1)
  const maxDailyWords = Math.max(...trend.map((t) => t.daily_words), 1)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">{t.common.loading}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(`/project/${projectId}?tab=${fromTab}`)}
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex-1">
              <h1 className="text-xl font-semibold">{t.stats.title}</h1>
              <p className="text-sm text-muted-foreground">
                {t.stats.subtitle}
              </p>
            </div>
            <LanguageToggle />
            <ThemeToggle />
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Overview cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.stats.totalWords}</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {overview?.total_words.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                {t.stats.avgWordsPerChapter} {overview?.avg_words_per_chapter.toLocaleString()} {t.common.words}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.stats.chapterProgress}</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {overview?.completed_chapters}/{overview?.total_chapters}
              </div>
              <p className="text-xs text-muted-foreground">
                {t.stats.completionRate} {overview?.completion_rate}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.stats.writingDays}</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview?.writing_days}</div>
              <p className="text-xs text-muted-foreground">
                {t.stats.totalVersions} {overview?.total_versions} {t.common.versions}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.stats.lastUpdated}</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatDate(overview?.last_updated || null)}
              </div>
              <p className="text-xs text-muted-foreground">
                {t.stats.startedAt} {formatDate(overview?.first_created || null)}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Word Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              {t.stats.wordsTrend}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {trend.length > 0 ? (
              <div className="space-y-4">
                {/* Cumulative words chart */}
                <div>
                  <p className="text-sm text-muted-foreground mb-2">{t.stats.cumulativeWords}</p>
                  <div className="h-32 flex items-end gap-1">
                    {trend.map((item) => (
                      <div
                        key={item.date}
                        className="flex-1 bg-primary/20 hover:bg-primary/40 transition-colors rounded-t relative group"
                        style={{
                          height: `${(item.words / maxWords) * 100}%`,
                          minHeight: "2px",
                        }}
                      >
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                          {item.date.slice(5)}
                          <br />
                          {item.words.toLocaleString()} {t.common.words}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Daily new words chart */}
                <div>
                  <p className="text-sm text-muted-foreground mb-2">{t.stats.dailyNew}</p>
                  <div className="h-20 flex items-end gap-1">
                    {trend.map((item) => (
                      <div
                        key={`daily-${item.date}`}
                        className={`flex-1 rounded-t relative group ${
                          item.daily_words > 0
                            ? "bg-green-500/60 hover:bg-green-500/80"
                            : "bg-muted"
                        }`}
                        style={{
                          height:
                            item.daily_words > 0
                              ? `${Math.max(
                                  (item.daily_words / maxDailyWords) * 100,
                                  5
                                )}%`
                              : "2px",
                        }}
                      >
                        {item.daily_words > 0 && (
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                            {item.date.slice(5)}
                            <br />+{item.daily_words.toLocaleString()} {t.common.words}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-muted-foreground">
                {t.common.noData}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 章节进度 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              {t.stats.chapterDetails}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {progress.length > 0 ? (
              <div className="space-y-3">
                {progress.map((item) => (
                  <div key={item.chapter} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{item.chapter}</span>
                        {item.status === "final" ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            v{item.version_count}
                          </span>
                        )}
                      </div>
                      <span className="text-muted-foreground">
                        {item.word_count.toLocaleString()} {t.common.words}
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          item.status === "final"
                            ? "bg-green-500"
                            : "bg-primary"
                        }`}
                        style={{ width: `${item.progress}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-muted-foreground">
                {t.stats.noChapters}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
