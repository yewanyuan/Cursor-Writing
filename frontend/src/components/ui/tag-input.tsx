import * as React from "react"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

export interface TagInputProps {
  value: string[]
  onChange: (value: string[]) => void
  placeholder?: string
  className?: string
  tagClassName?: string
}

const TagInput = React.forwardRef<HTMLDivElement, TagInputProps>(
  ({ value, onChange, placeholder = "输入后按回车添加", className, tagClassName }, ref) => {
    const [inputValue, setInputValue] = React.useState("")
    const inputRef = React.useRef<HTMLInputElement>(null)

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault()
        const trimmed = inputValue.trim()
        if (trimmed && !value.includes(trimmed)) {
          onChange([...value, trimmed])
          setInputValue("")
        }
      } else if (e.key === "Backspace" && inputValue === "" && value.length > 0) {
        // 当输入框为空时按退格键，删除最后一个标签
        onChange(value.slice(0, -1))
      }
    }

    const handleRemove = (index: number) => {
      onChange(value.filter((_, i) => i !== index))
    }

    const handleContainerClick = () => {
      inputRef.current?.focus()
    }

    return (
      <div
        ref={ref}
        className={cn(
          "flex flex-wrap gap-1.5 p-2 min-h-[80px] border rounded-md bg-background cursor-text",
          "focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2",
          className
        )}
        onClick={handleContainerClick}
      >
        {value.map((tag, index) => (
          <span
            key={`${tag}-${index}`}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-sm",
              "bg-primary/10 text-primary border border-primary/20",
              "transition-colors hover:bg-primary/20",
              tagClassName
            )}
          >
            {tag}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                handleRemove(index)
              }}
              className="hover:bg-primary/30 rounded-full p-0.5 transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={value.length === 0 ? placeholder : ""}
          className={cn(
            "flex-1 min-w-[120px] bg-transparent outline-none text-sm",
            "placeholder:text-muted-foreground"
          )}
        />
      </div>
    )
  }
)

TagInput.displayName = "TagInput"

export { TagInput }
