"use client";

import { useRef } from "react";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
}

export function ChatInput({ value, onChange, onSubmit, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) onSubmit();
    }
  }

  function handleInput() {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }
  }

  return (
    <div className="flex items-end gap-3 bg-white border border-stone-200 rounded-2xl px-4 py-3 shadow-sm focus-within:border-forest-400 focus-within:ring-2 focus-within:ring-forest-100 transition-all">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        placeholder="Ask about Irish public services, visas, tax, welfare, healthcare…"
        rows={1}
        disabled={disabled}
        className="flex-1 resize-none outline-none text-sm text-stone-900 placeholder-stone-400 bg-transparent leading-relaxed"
      />
      <button
        onClick={onSubmit}
        disabled={disabled || !value.trim()}
        className="shrink-0 bg-forest-800 hover:bg-forest-900 disabled:bg-stone-100 disabled:text-stone-300 text-white rounded-xl w-9 h-9 flex items-center justify-center transition-colors"
        aria-label="Send message"
      >
        {disabled ? (
          <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        )}
      </button>
    </div>
  );
}
