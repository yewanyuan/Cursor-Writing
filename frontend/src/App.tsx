import { BrowserRouter, Routes, Route } from "react-router-dom"
import ProjectList from "@/pages/ProjectList"
import ProjectWorkspace from "@/pages/ProjectWorkspace"
import WritingPage from "@/pages/WritingPage"
import SettingsPage from "@/pages/SettingsPage"
import StatsPage from "@/pages/StatsPage"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ProjectList />} />
        <Route path="/project/:projectId" element={<ProjectWorkspace />} />
        <Route path="/write/:projectId" element={<WritingPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/stats/:projectId" element={<StatsPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
