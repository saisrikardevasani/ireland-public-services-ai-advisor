"use client";

import type { Citation, Message } from "@/types";

function CitationChip({ citation }: { citation: Citation }) {
  return (
    <a
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      title={citation.snippet}
      className="inline-flex items-center gap-1 text-xs bg-forest-50 border border-forest-200 text-forest-700 rounded-md px-2 py-1 hover:bg-forest-100 transition-colors font-medium"
    >
      [{citation.n}] {citation.title}
    </a>
  );
}

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 mb-7 ${isUser ? "flex-row-reverse" : "flex-row"}`}>

      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 ${
          isUser ? "bg-stone-800 text-white" : "bg-forest-800 text-white"
        }`}
      >
        {isUser ? "U" : "AI"}
      </div>

      <div className={`max-w-[78%] flex flex-col gap-1.5 ${isUser ? "items-end" : "items-start"}`}>
        <span className="text-xs text-stone-400 font-medium px-1">
          {isUser ? "You" : "Advisor"}
        </span>

        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-stone-900 text-stone-50 rounded-tr-sm"
              : "bg-white border border-stone-200 text-stone-800 rounded-tl-sm shadow-sm"
          } ${message.isStreaming ? "streaming-cursor" : ""}`}
        >
          {message.content || (message.isStreaming ? "" : "…")}
        </div>

        {/* Citations */}
        {!isUser && message.citations && message.citations.length > 0 && !message.isStreaming && (
          <div className="flex flex-wrap gap-1.5 px-1 mt-0.5">
            <span className="text-xs text-stone-400 self-center mr-0.5">Sources:</span>
            {message.citations.map((c) => (
              <CitationChip key={c.n} citation={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
