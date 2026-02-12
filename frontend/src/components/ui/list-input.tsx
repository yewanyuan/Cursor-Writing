import * as React from "react"
import { Plus, X, GripVertical } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./button"
import { Input } from "./input"

export interface ListInputProps {
  value: string[]
  onChange: (value: string[]) => void
  placeholder?: string
  addButtonText?: string
  className?: string
  itemClassName?: string
}

const ListInput = React.forwardRef<HTMLDivElement, ListInputProps>(
  ({ value, onChange, placeholder = "输入内容", addButtonText = "添加", className, itemClassName }, ref) => {
    const [inputValue, setInputValue] = React.useState("")
    const inputRef = React.useRef<HTMLInputElement>(null)

    const handleAdd = () => {
      const trimmed = inputValue.trim()
      if (trimmed && !value.includes(trimmed)) {
        onChange([...value, trimmed])
        setInputValue("")
        inputRef.current?.focus()
      }
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault()
        handleAdd()
      }
    }

    const handleRemove = (index: number) => {
      onChange(value.filter((_, i) => i !== index))
    }

    const handleItemChange = (index: number, newValue: string) => {
      const newList = [...value]
      newList[index] = newValue
      onChange(newList)
    }

    return (
      <div ref={ref} className={cn("space-y-2", className)}>
        {/* 已有项目列表 */}
        {value.length > 0 && (
          <div className="space-y-1.5">
            {value.map((item, index) => (
              <div
                key={index}
                className={cn(
                  "flex items-center gap-2 group",
                  itemClassName
                )}
              >
                <GripVertical className="w-4 h-4 text-muted-foreground/50 flex-shrink-0" />
                <Input
                  value={item}
                  onChange={(e) => handleItemChange(index, e.target.value)}
                  className="flex-1 h-8 text-sm"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 opacity-50 hover:opacity-100 hover:bg-destructive/10 hover:text-destructive"
                  onClick={() => handleRemove(index)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* 添加新项 */}
        <div className="flex items-center gap-2">
          <Input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="flex-1 h-8 text-sm"
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAdd}
            disabled={!inputValue.trim()}
            className="h-8 px-3"
          >
            <Plus className="w-4 h-4 mr-1" />
            {addButtonText}
          </Button>
        </div>

        {value.length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-2">
            输入内容后按回车或点击添加按钮
          </p>
        )}
      </div>
    )
  }
)

ListInput.displayName = "ListInput"

export { ListInput }
