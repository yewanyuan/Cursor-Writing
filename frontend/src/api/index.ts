import axios from "axios"
import type { Project, ProjectCreate, CharacterCard, WorldCard, StyleCard, RulesCard, Draft, WritingSession, Fact, TimelineEvent, CharacterState, SettingsResponse, ProviderInfo, AgentInfo, LLMProviderSettings, AgentSettings } from "@/types"

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 300000, // 5分钟超时（AI 写作需要较长时间）
})

// Projects
export const projectApi = {
  list: () => api.get<Project[]>("/projects"),
  get: (id: string) => api.get<Project>(`/projects/${id}`),
  create: (data: ProjectCreate) => api.post<Project>("/projects", data),
  update: (id: string, data: Partial<ProjectCreate>) => api.put<Project>(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
}

// Cards
export const cardApi = {
  // 角色卡
  getCharacters: (projectId: string) => api.get<CharacterCard[]>(`/projects/${projectId}/cards/characters`),
  getCharacter: (projectId: string, name: string) => api.get<CharacterCard>(`/projects/${projectId}/cards/characters/${name}`),
  saveCharacter: (projectId: string, card: CharacterCard) => api.post(`/projects/${projectId}/cards/characters`, card),
  deleteCharacter: (projectId: string, name: string) => api.delete(`/projects/${projectId}/cards/characters/${name}`),

  // 世界观卡
  getWorlds: (projectId: string) => api.get<WorldCard[]>(`/projects/${projectId}/cards/worlds`),
  getWorld: (projectId: string, name: string) => api.get<WorldCard>(`/projects/${projectId}/cards/worlds/${name}`),
  saveWorld: (projectId: string, card: WorldCard) => api.post(`/projects/${projectId}/cards/worlds`, card),
  deleteWorld: (projectId: string, name: string) => api.delete(`/projects/${projectId}/cards/worlds/${name}`),

  // 文风卡
  getStyle: (projectId: string) => api.get<StyleCard>(`/projects/${projectId}/cards/style`),
  saveStyle: (projectId: string, card: StyleCard) => api.put<StyleCard>(`/projects/${projectId}/cards/style`, card),

  // 规则卡
  getRules: (projectId: string) => api.get<RulesCard>(`/projects/${projectId}/cards/rules`),
  saveRules: (projectId: string, card: RulesCard) => api.put<RulesCard>(`/projects/${projectId}/cards/rules`, card),
}

// Drafts
export const draftApi = {
  list: (projectId: string) => api.get<Draft[]>(`/projects/${projectId}/drafts`),
  get: (projectId: string, chapter: string, version?: number) =>
    api.get<Draft>(`/projects/${projectId}/drafts/${chapter}`, { params: { version } }),
  save: (projectId: string, draft: Partial<Draft>) => api.post(`/projects/${projectId}/drafts`, draft),
  getVersions: (projectId: string, chapter: string) => api.get<number[]>(`/projects/${projectId}/drafts/${chapter}/versions`),
}

// Session
export const sessionApi = {
  start: (data: WritingSession) => api.post("/session/start", data),
  getStatus: (projectId: string) => api.get(`/session/status/${projectId}`),
  feedback: (projectId: string, action: "confirm" | "revise", content?: string) =>
    api.post(`/session/feedback/${projectId}`, { action, content }),
  continue: (data: {
    project_id: string
    chapter: string
    existing_content: string
    instruction: string
    target_words?: number
    insert_position?: number | null
  }) => api.post("/session/continue", data),
}

// Canon 事实表
export const canonApi = {
  // 事实
  getFacts: (projectId: string) => api.get<Fact[]>(`/projects/${projectId}/canon/facts`),
  addFact: (projectId: string, fact: Partial<Fact>) => api.post<Fact>(`/projects/${projectId}/canon/facts`, fact),
  updateFact: (projectId: string, factId: string, fact: Partial<Fact>) => api.put<Fact>(`/projects/${projectId}/canon/facts/${factId}`, fact),
  deleteFact: (projectId: string, factId: string) => api.delete(`/projects/${projectId}/canon/facts/${factId}`),
  batchDeleteFacts: (projectId: string, ids: string[]) =>
    api.post<{ success: boolean; deleted_count: number; message: string }>(
      `/projects/${projectId}/canon/facts/batch-delete`, { ids }
    ),

  // 时间线
  getTimeline: (projectId: string) => api.get<TimelineEvent[]>(`/projects/${projectId}/canon/timeline`),
  addTimelineEvent: (projectId: string, event: Partial<TimelineEvent>) => api.post<TimelineEvent>(`/projects/${projectId}/canon/timeline`, event),
  updateTimelineEvent: (projectId: string, eventId: string, event: Partial<TimelineEvent>) => api.put<TimelineEvent>(`/projects/${projectId}/canon/timeline/${eventId}`, event),
  deleteTimelineEvent: (projectId: string, eventId: string) => api.delete(`/projects/${projectId}/canon/timeline/${eventId}`),
  batchDeleteTimeline: (projectId: string, ids: string[]) =>
    api.post<{ success: boolean; deleted_count: number; message: string }>(
      `/projects/${projectId}/canon/timeline/batch-delete`, { ids }
    ),

  // 角色状态
  getCharacterStates: (projectId: string) => api.get<CharacterState[]>(`/projects/${projectId}/canon/states`),
  getCharacterState: (projectId: string, character: string) => api.get<CharacterState>(`/projects/${projectId}/canon/states/${character}`),
  updateCharacterState: (projectId: string, state: Partial<CharacterState>) => api.post<CharacterState>(`/projects/${projectId}/canon/states`, state),
  editCharacterState: (projectId: string, character: string, chapter: string, state: Partial<CharacterState>) =>
    api.put<CharacterState>(`/projects/${projectId}/canon/states/${encodeURIComponent(character)}/${encodeURIComponent(chapter)}`, state),
  deleteCharacterState: (projectId: string, character: string, chapter: string) =>
    api.delete(`/projects/${projectId}/canon/states/${encodeURIComponent(character)}/${encodeURIComponent(chapter)}`),
  batchDeleteStates: (projectId: string, keys: Array<{ character: string; chapter: string }>) =>
    api.post<{ success: boolean; deleted_count: number; message: string }>(
      `/projects/${projectId}/canon/states/batch-delete`, { keys }
    ),

  // AI 提取
  extractFromChapter: (projectId: string, chapter: string, content?: string) =>
    api.post<{
      success: boolean
      facts_count: number
      timeline_count: number
      states_count: number
      message: string
    }>(`/projects/${projectId}/canon/extract`, { chapter, content }),

  // 清空
  clear: (projectId: string) => api.delete(`/projects/${projectId}/canon/clear`),
}

// Settings 设置
export const settingsApi = {
  get: () => api.get<SettingsResponse>("/settings"),
  update: (data: {
    default_provider?: string
    providers?: Record<string, Partial<LLMProviderSettings>>
    agents?: Record<string, AgentSettings>
  }) => api.put("/settings", data),
  getProviders: () => api.get<{ providers: ProviderInfo[] }>("/settings/providers"),
  getAgents: () => api.get<{ agents: AgentInfo[] }>("/settings/agents"),
  testConnection: (provider: string, apiKey: string, baseUrl?: string, model?: string) =>
    api.post<{ success: boolean; message: string }>("/settings/test-connection", null, {
      params: { provider, api_key: apiKey, base_url: baseUrl, model }
    }),
}

// Export 导出
export const exportApi = {
  // 获取导出信息
  getInfo: (projectId: string) => api.get<{
    total_words: number
    chapter_count: number
    available_formats: string[]
  }>(`/export/${projectId}/info`),

  // 导出项目
  export: (projectId: string, format: "txt" | "markdown" | "epub", useFinal: boolean = true) =>
    api.post(`/export/${projectId}`, { format, use_final: useFinal }, {
      responseType: "blob"
    }),

  // 预览导出
  preview: (projectId: string, format: "txt" | "markdown", useFinal: boolean = true, maxChars: number = 5000) =>
    api.get<{
      preview: string
      total_words: number
      chapter_count: number
      truncated: boolean
    }>(`/export/${projectId}/preview`, {
      params: { format, use_final: useFinal, max_chars: maxChars }
    }),
}

// Statistics 统计
export const statsApi = {
  // 获取概览
  getOverview: (projectId: string) => api.get<{
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
  }>(`/stats/${projectId}/overview`),

  // 获取字数趋势
  getTrend: (projectId: string, days: number = 30) => api.get<{
    date: string
    words: number
    daily_words: number
  }[]>(`/stats/${projectId}/trend`, { params: { days } }),

  // 获取章节进度
  getProgress: (projectId: string) => api.get<{
    chapter: string
    word_count: number
    status: string
    version_count: number
    progress: number
  }[]>(`/stats/${projectId}/progress`),

  // 获取完整统计
  getFull: (projectId: string) => api.get(`/stats/${projectId}`),
}

export default api
