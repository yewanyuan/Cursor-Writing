import { createContext, useContext, useState, useEffect } from "react"
import type { ReactNode } from "react"
import { translations } from "./translations"
import type { Language, Translations } from "./translations"

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: Translations
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

const LANGUAGE_KEY = "phantom-pen-language"

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    // Try to get from localStorage
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(LANGUAGE_KEY)
      if (saved === "en" || saved === "zh") {
        return saved
      }
      // Detect browser language
      const browserLang = navigator.language.toLowerCase()
      if (browserLang.startsWith("zh")) {
        return "zh"
      }
    }
    return "en" // Default to English
  })

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
    localStorage.setItem(LANGUAGE_KEY, lang)
  }

  useEffect(() => {
    // Update document lang attribute
    document.documentElement.lang = language
  }, [language])

  const t = translations[language]

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error("useLanguage must be used within a LanguageProvider")
  }
  return context
}
