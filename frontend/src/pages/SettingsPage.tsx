import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import {
  ArrowLeft,
  Save,
  Loader2,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { settingsApi } from "@/api"
import type {
  ProviderInfo,
  AgentInfo,
  LLMProviderSettings,
  AgentSettings,
} from "@/types"

export default function SettingsPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testingProvider, setTestingProvider] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)

  // Data states
  const [providers, setProviders] = useState<ProviderInfo[]>([])
  const [agents, setAgents] = useState<AgentInfo[]>([])

  // Edit states
  const [defaultProvider, setDefaultProvider] = useState("")
  const [providerSettings, setProviderSettings] = useState<Record<string, LLMProviderSettings>>({})
  const [agentSettings, setAgentSettings] = useState<Record<string, AgentSettings>>({})
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({})

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [settingsRes, providersRes, agentsRes] = await Promise.all([
        settingsApi.get(),
        settingsApi.getProviders(),
        settingsApi.getAgents(),
      ])

      setProviders(providersRes.data.providers)
      setAgents(agentsRes.data.agents)

      // Initialize edit states
      setDefaultProvider(settingsRes.data.default_provider)
      setProviderSettings(settingsRes.data.providers)
      setAgentSettings(settingsRes.data.agents)
    } catch (err) {
      console.error("Failed to load settings:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await settingsApi.update({
        default_provider: defaultProvider,
        providers: providerSettings,
        agents: agentSettings,
      })
      // Reload to get fresh data
      await loadData()
      setTestResult({ success: true, message: "设置已保存" })
      setTimeout(() => setTestResult(null), 3000)
    } catch (err) {
      console.error("Failed to save settings:", err)
      setTestResult({ success: false, message: "保存失败" })
    } finally {
      setSaving(false)
    }
  }

  const handleTestConnection = async (providerId: string) => {
    const providerConfig = providerSettings[providerId]
    if (!providerConfig) return

    setTestingProvider(providerId)
    setTestResult(null)

    try {
      // Only send the API key if it's not masked
      const apiKey = providerConfig.api_key.startsWith("*") ? "" : providerConfig.api_key
      const res = await settingsApi.testConnection(
        providerId,
        apiKey,
        providerConfig.base_url,
        providerConfig.model
      )
      setTestResult(res.data)
    } catch (err) {
      setTestResult({ success: false, message: "连接测试失败" })
    } finally {
      setTestingProvider(null)
    }
  }

  const updateProviderSetting = (
    providerId: string,
    field: keyof LLMProviderSettings,
    value: string | number
  ) => {
    setProviderSettings((prev) => ({
      ...prev,
      [providerId]: {
        ...prev[providerId],
        [field]: value,
      },
    }))
  }

  const updateAgentSetting = (
    agentId: string,
    field: keyof AgentSettings,
    value: string | number
  ) => {
    setAgentSettings((prev) => ({
      ...prev,
      [agentId]: {
        ...prev[agentId],
        [field]: value,
      },
    }))
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">设置</h1>
              <p className="text-muted-foreground">配置 LLM 提供商和智能体参数</p>
            </div>
          </div>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            保存设置
          </Button>
        </div>

        {/* Status message */}
        {testResult && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
              testResult.success
                ? "bg-green-500/10 text-green-600"
                : "bg-red-500/10 text-red-600"
            }`}
          >
            {testResult.success ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <XCircle className="w-5 h-5" />
            )}
            {testResult.message}
          </motion.div>
        )}

        <Tabs defaultValue="providers" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="providers">LLM 提供商</TabsTrigger>
            <TabsTrigger value="agents">智能体</TabsTrigger>
          </TabsList>

          {/* Providers Tab */}
          <TabsContent value="providers" className="space-y-6">
            {/* Default Provider */}
            <Card>
              <CardHeader>
                <CardTitle>默认提供商</CardTitle>
                <CardDescription>选择默认使用的 LLM 提供商</CardDescription>
              </CardHeader>
              <CardContent>
                <Select value={defaultProvider} onValueChange={setDefaultProvider}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="选择提供商" />
                  </SelectTrigger>
                  <SelectContent>
                    {providers.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            {/* Provider Configurations */}
            {providers.map((provider) => (
              <Card key={provider.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>{provider.name}</CardTitle>
                      <CardDescription>
                        {provider.id === "custom" ? "自定义 OpenAI 兼容 API" : `${provider.name} API 配置`}
                      </CardDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTestConnection(provider.id)}
                      disabled={testingProvider === provider.id}
                    >
                      {testingProvider === provider.id ? (
                        <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                      ) : (
                        <Zap className="w-4 h-4 mr-1" />
                      )}
                      测试连接
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* API Key */}
                  <div className="grid gap-2">
                    <Label>API Key</Label>
                    <div className="flex gap-2">
                      <Input
                        type={showApiKeys[provider.id] ? "text" : "password"}
                        value={providerSettings[provider.id]?.api_key || ""}
                        onChange={(e) =>
                          updateProviderSetting(provider.id, "api_key", e.target.value)
                        }
                        placeholder="sk-..."
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() =>
                          setShowApiKeys((prev) => ({
                            ...prev,
                            [provider.id]: !prev[provider.id],
                          }))
                        }
                      >
                        {showApiKeys[provider.id] ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Base URL (for custom provider) */}
                  {(provider.id === "custom" || provider.id === "deepseek") && (
                    <div className="grid gap-2">
                      <Label>Base URL</Label>
                      <Input
                        value={providerSettings[provider.id]?.base_url || ""}
                        onChange={(e) =>
                          updateProviderSetting(provider.id, "base_url", e.target.value)
                        }
                        placeholder="https://api.example.com/v1"
                      />
                    </div>
                  )}

                  {/* Model Selection */}
                  <div className="grid gap-2">
                    <Label>模型</Label>
                    {provider.models.length > 0 ? (
                      <Select
                        value={providerSettings[provider.id]?.model || ""}
                        onValueChange={(v) => updateProviderSetting(provider.id, "model", v)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择模型" />
                        </SelectTrigger>
                        <SelectContent>
                          {provider.models.map((model) => (
                            <SelectItem key={model} value={model}>
                              {model}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        value={providerSettings[provider.id]?.model || ""}
                        onChange={(e) =>
                          updateProviderSetting(provider.id, "model", e.target.value)
                        }
                        placeholder="输入模型名称"
                      />
                    )}
                  </div>

                  {/* Max Tokens */}
                  <div className="grid gap-2">
                    <Label>最大 Token 数</Label>
                    <Input
                      type="number"
                      value={providerSettings[provider.id]?.max_tokens || 8000}
                      onChange={(e) =>
                        updateProviderSetting(provider.id, "max_tokens", Number(e.target.value))
                      }
                    />
                  </div>

                  {/* Temperature */}
                  <div className="grid gap-2">
                    <div className="flex items-center justify-between">
                      <Label>温度 (Temperature)</Label>
                      <span className="text-sm text-muted-foreground">
                        {providerSettings[provider.id]?.temperature?.toFixed(2) || "0.70"}
                      </span>
                    </div>
                    <Slider
                      value={[providerSettings[provider.id]?.temperature || 0.7]}
                      onValueChange={([v]: number[]) =>
                        updateProviderSetting(provider.id, "temperature", v)
                      }
                      min={0}
                      max={2}
                      step={0.01}
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          {/* Agents Tab */}
          <TabsContent value="agents" className="space-y-6">
            {agents.map((agent) => (
              <Card key={agent.id}>
                <CardHeader>
                  <CardTitle>{agent.name}</CardTitle>
                  <CardDescription>{agent.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Provider Selection */}
                  <div className="grid gap-2">
                    <Label>使用的提供商</Label>
                    <Select
                      value={agentSettings[agent.id]?.provider || defaultProvider}
                      onValueChange={(v) => updateAgentSetting(agent.id, "provider", v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择提供商" />
                      </SelectTrigger>
                      <SelectContent>
                        {providers.map((p) => (
                          <SelectItem key={p.id} value={p.id}>
                            {p.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Temperature Override */}
                  <div className="grid gap-2">
                    <div className="flex items-center justify-between">
                      <Label>温度 (Temperature)</Label>
                      <span className="text-sm text-muted-foreground">
                        {agentSettings[agent.id]?.temperature?.toFixed(2) || "0.70"}
                      </span>
                    </div>
                    <Slider
                      value={[agentSettings[agent.id]?.temperature || 0.7]}
                      onValueChange={([v]: number[]) => updateAgentSetting(agent.id, "temperature", v)}
                      min={0}
                      max={2}
                      step={0.01}
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
