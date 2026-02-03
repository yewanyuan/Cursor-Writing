import { useState, useEffect } from "react"

type Theme = "light" | "dark" | "system"

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    // 从 localStorage 读取保存的主题
    const saved = localStorage.getItem("theme") as Theme | null
    return saved || "system"
  })

  useEffect(() => {
    const root = window.document.documentElement

    // 移除旧的主题类
    root.classList.remove("light", "dark")

    // 确定实际主题
    let actualTheme: "light" | "dark"
    if (theme === "system") {
      actualTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
    } else {
      actualTheme = theme
    }

    // 应用主题
    root.classList.add(actualTheme)

    // 保存到 localStorage
    localStorage.setItem("theme", theme)
  }, [theme])

  // 监听系统主题变化
  useEffect(() => {
    if (theme !== "system") return

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
    const handleChange = () => {
      const root = window.document.documentElement
      root.classList.remove("light", "dark")
      root.classList.add(mediaQuery.matches ? "dark" : "light")
    }

    mediaQuery.addEventListener("change", handleChange)
    return () => mediaQuery.removeEventListener("change", handleChange)
  }, [theme])

  return { theme, setTheme }
}
