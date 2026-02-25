import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { LanguageProvider } from "@/i18n"
import ProjectList from "@/pages/ProjectList"
import ProjectWorkspace from "@/pages/ProjectWorkspace"
import WritingPage from "@/pages/WritingPage"
import SettingsPage from "@/pages/SettingsPage"
import StatsPage from "@/pages/StatsPage"

function App() {
  return (
    <LanguageProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ProjectList />} />
          <Route path="/project/:projectId" element={<ProjectWorkspace />} />
          <Route path="/write/:projectId" element={<WritingPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/stats/:projectId" element={<StatsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </LanguageProvider>
  )
}

export default App
