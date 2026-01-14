import { BrowserRouter, Routes, Route } from "react-router-dom"
import ProjectList from "@/pages/ProjectList"
import ProjectWorkspace from "@/pages/ProjectWorkspace"
import WritingPage from "@/pages/WritingPage"
import SettingsPage from "@/pages/SettingsPage"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ProjectList />} />
        <Route path="/project/:projectId" element={<ProjectWorkspace />} />
        <Route path="/write/:projectId" element={<WritingPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
