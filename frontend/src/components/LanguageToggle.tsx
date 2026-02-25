import { Languages } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useLanguage } from "@/i18n"

export function LanguageToggle() {
  const { language, setLanguage } = useLanguage()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" title={language === "zh" ? "切换语言" : "Switch Language"}>
          <Languages className="h-[1.2rem] w-[1.2rem]" />
          <span className="sr-only">Toggle language</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setLanguage("zh")}>
          <span className={language === "zh" ? "font-medium" : ""}>中文</span>
          {language === "zh" && <span className="ml-2">✓</span>}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setLanguage("en")}>
          <span className={language === "en" ? "font-medium" : ""}>English</span>
          {language === "en" && <span className="ml-2">✓</span>}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
