import { useRef, useEffect, useCallback, forwardRef, useImperativeHandle } from "react"

export interface AIContentRange {
  start: number
  end: number
}

interface HighlightEditorProps {
  value: string
  onChange: (value: string) => void
  onAIRangeChange?: (range: AIContentRange | null) => void
  aiContentRange: AIContentRange | null
  placeholder?: string
  className?: string
  disabled?: boolean
}

export interface HighlightEditorRef {
  getSelectionStart: () => number
  focus: () => void
}

/**
 * 支持AI内容高亮的编辑器组件
 * 使用 textarea + 背景层实现高亮效果
 *
 * 关键点：
 * 1. 背景层的文字必须是透明的，只显示高亮背景
 * 2. 背景层必须与 textarea 完全同步滚动
 * 3. 两层的字体、行高、padding 必须完全一致
 */
const HighlightEditor = forwardRef<HighlightEditorRef, HighlightEditorProps>(
  ({ value, onChange, onAIRangeChange, aiContentRange, placeholder, className, disabled }, ref) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null)
    const backdropRef = useRef<HTMLDivElement>(null)
    const prevValueRef = useRef(value)

    useImperativeHandle(ref, () => ({
      getSelectionStart: () => textareaRef.current?.selectionStart ?? 0,
      focus: () => textareaRef.current?.focus(),
    }))

    // 同步滚动 - 使用 requestAnimationFrame 确保平滑同步
    const syncScroll = useCallback(() => {
      if (textareaRef.current && backdropRef.current) {
        backdropRef.current.scrollTop = textareaRef.current.scrollTop
        backdropRef.current.scrollLeft = textareaRef.current.scrollLeft
      }
    }, [])

    useEffect(() => {
      const textarea = textareaRef.current
      if (textarea) {
        // 使用 passive listener 提高性能
        textarea.addEventListener("scroll", syncScroll, { passive: true })
        // 初始同步
        syncScroll()
        return () => textarea.removeEventListener("scroll", syncScroll)
      }
    }, [syncScroll])

    // 当 value 改变时也同步滚动位置
    useEffect(() => {
      // 使用 RAF 确保在 DOM 更新后同步
      requestAnimationFrame(syncScroll)
    }, [value, syncScroll])

    // 处理内容变化，更新高亮范围
    const handleChange = (newValue: string) => {
      const oldValue = prevValueRef.current
      prevValueRef.current = newValue

      // 如果有高亮范围且内容发生变化，需要调整范围
      if (aiContentRange && onAIRangeChange && newValue !== oldValue) {
        const cursorPos = textareaRef.current?.selectionStart ?? 0
        const lengthDiff = newValue.length - oldValue.length

        // 计算新的高亮范围
        let newRange: AIContentRange | null = { ...aiContentRange }

        if (cursorPos <= aiContentRange.start) {
          // 编辑在高亮区域之前，整体移动
          newRange.start += lengthDiff
          newRange.end += lengthDiff
        } else if (cursorPos <= aiContentRange.end) {
          // 编辑在高亮区域内，扩展/收缩结束位置
          newRange.end += lengthDiff
        }
        // 编辑在高亮区域之后，不影响范围

        // 验证范围有效性
        if (newRange.start < 0) newRange.start = 0
        if (newRange.end <= newRange.start) {
          newRange = null // 高亮区域被完全删除
        }
        if (newRange && newRange.end > newValue.length) {
          newRange.end = newValue.length
        }

        onAIRangeChange(newRange)
      }

      onChange(newValue)
    }

    // 渲染高亮内容 - 关键：文字必须透明，只显示背景
    const renderHighlightedContent = () => {
      // 确保末尾有换行符以匹配 textarea 的行为
      const displayValue = value.endsWith("\n") ? value + " " : value || " "

      if (!aiContentRange || aiContentRange.start >= aiContentRange.end) {
        // 没有AI内容范围，显示纯文本占位（透明色）
        return <span className="highlight-text-transparent">{displayValue}</span>
      }

      const { start, end } = aiContentRange
      const safeStart = Math.max(0, Math.min(start, value.length))
      const safeEnd = Math.max(safeStart, Math.min(end, value.length))

      const beforeAI = value.slice(0, safeStart)
      const aiContent = value.slice(safeStart, safeEnd)
      const afterAI = value.slice(safeEnd)
      // 确保末尾有空格以匹配 textarea 高度
      const afterDisplay = afterAI.endsWith("\n") ? afterAI + " " : afterAI || ""

      return (
        <>
          <span className="highlight-text-transparent">{beforeAI}</span>
          <mark className="ai-highlight-mark">{aiContent}</mark>
          <span className="highlight-text-transparent">{afterDisplay}</span>
        </>
      )
    }

    return (
      <div className={`highlight-editor-container ${className || ""}`}>
        {/* 背景层：只显示高亮背景，文字透明 */}
        <div
          ref={backdropRef}
          className="highlight-editor-backdrop"
          aria-hidden="true"
        >
          <div className="highlight-editor-highlights">
            {renderHighlightedContent()}
          </div>
        </div>

        {/* 前景层：实际的 textarea */}
        <textarea
          ref={textareaRef}
          className="highlight-editor-textarea"
          value={value}
          onChange={(e) => handleChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          onScroll={syncScroll}
        />

        <style>{`
          .highlight-editor-container {
            position: relative;
            width: 100%;
            height: 100%;
            min-height: 500px;
          }

          .highlight-editor-backdrop {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            overflow: auto;
            pointer-events: none;
            z-index: 1;
            /* 隐藏滚动条但保持可滚动 */
            scrollbar-width: none;
            -ms-overflow-style: none;
          }

          .highlight-editor-backdrop::-webkit-scrollbar {
            display: none;
          }

          .highlight-editor-highlights {
            padding: 0.75rem;
            font-family: inherit;
            font-size: 1rem;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-wrap: break-word;
            color: transparent;
            /* 确保宽度与 textarea 一致 */
            box-sizing: border-box;
            min-height: 100%;
          }

          .highlight-text-transparent {
            color: transparent;
          }

          .highlight-editor-textarea {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            padding: 0.75rem;
            margin: 0;
            font-family: inherit;
            font-size: 1rem;
            line-height: 1.5;
            color: hsl(var(--foreground));
            background: transparent;
            border: none;
            outline: none;
            resize: none;
            overflow: auto;
            z-index: 2;
            caret-color: hsl(var(--foreground));
            box-sizing: border-box;
          }

          .highlight-editor-textarea::placeholder {
            color: hsl(var(--muted-foreground));
          }

          .highlight-editor-textarea:focus {
            outline: none;
            box-shadow: none;
          }

          /* AI 内容高亮样式 - 只有背景色，文字透明 */
          .ai-highlight-mark {
            background-color: rgba(59, 130, 246, 0.25);
            color: transparent;
            border-radius: 2px;
          }

          /* 深色模式下的高亮颜色 */
          .dark .ai-highlight-mark {
            background-color: rgba(96, 165, 250, 0.3);
          }
        `}</style>
      </div>
    )
  }
)

HighlightEditor.displayName = "HighlightEditor"

export default HighlightEditor
