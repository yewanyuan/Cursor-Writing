export interface Project {
  id: string
  name: string
  author: string
  genre: string
  description?: string
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  author: string
  genre: string
  description?: string
}

export interface CharacterCard {
  name: string
  identity: string
  personality: string[]
  speech_pattern: string
  background?: string
  relationships?: Record<string, string>
}

export interface WorldCard {
  name: string
  category: string
  description: string
  rules?: string[]
  locations?: string[]
}

export interface StyleCard {
  narrative_distance: string  // close/medium/far
  pacing: string              // fast/moderate/slow
  sentence_style: string
  vocabulary: string[]
  taboo_words: string[]
  example_passages: string[]
}

export interface RulesCard {
  dos: string[]
  donts: string[]
  quality_standards: string[]
}

export interface Draft {
  project_id: string
  chapter: string
  version: number
  content: string
  word_count: number
  status: "draft" | "reviewed" | "final"
  created_at: string
  notes?: string
}

export interface SessionStatus {
  status: "idle" | "briefing" | "writing" | "reviewing" | "editing" | "waiting" | "completed" | "error"
  current_chapter?: string
  progress?: number
  message?: string
}

export interface WritingSession {
  project_id: string
  chapter: string
  chapter_title: string
  chapter_goal: string
  characters: string[]
  target_words: number
}

// Canon 事实表
export interface Fact {
  id: string
  statement: string
  source: string
  confidence: number
}

export interface TimelineEvent {
  id: string
  time: string
  event: string
  participants: string[]
  location: string
  source: string
}

export interface CharacterState {
  character: string
  chapter: string
  location: string
  emotional_state: string
  goals: string[]
  inventory: string[]
  injuries: string[]
  relationships: Record<string, string>
}

// Settings 设置
export interface LLMProviderSettings {
  api_key: string
  base_url?: string
  model: string
  max_tokens: number
  temperature: number
}

export interface AgentSettings {
  provider: string
  temperature: number
}

export interface SettingsResponse {
  default_provider: string
  providers: Record<string, LLMProviderSettings>
  agents: Record<string, AgentSettings>
}

export interface ProviderInfo {
  id: string
  name: string
  models: string[]
}

export interface AgentInfo {
  id: string
  name: string
  description: string
}
