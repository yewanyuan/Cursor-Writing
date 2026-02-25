import { Moon, Sun, Monitor } from "lucide-react"
import { useTheme } from "@/hooks/useTheme"
import { useLanguage } from "@/i18n"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const { t } = useLanguage()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-9 w-9">
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          onClick={() => setTheme("light")}
          className={theme === "light" ? "bg-muted" : ""}
        >
          <Sun className="mr-2 h-4 w-4" />
          {t.theme.light}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme("dark")}
          className={theme === "dark" ? "bg-muted" : ""}
        >
          <Moon className="mr-2 h-4 w-4" />
          {t.theme.dark}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme("system")}
          className={theme === "system" ? "bg-muted" : ""}
        >
          <Monitor className="mr-2 h-4 w-4" />
          {t.theme.system}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
