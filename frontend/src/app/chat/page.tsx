"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";

import { ChatInput } from "@/components/ChatInput";
import { ChatMessage } from "@/components/ChatMessage";
import { streamChat } from "@/lib/api";
import type { Message } from "@/types";

const SUGGESTED_QUESTIONS = [
  "When can I switch from Stamp 2 to Stamp 1G?",
  "How do I apply for a PPSN?",
  "Am I eligible for Jobseeker's Benefit?",
  "What is the VAT threshold for SaaS in Ireland?",
];

type WarmupState = "checking" | "slow" | "ready";

function ChatContent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [warmup, setWarmup] = useState<WarmupState>("checking");
  const bottomRef = useRef<HTMLDivElement>(null);
  const searchParams = useSearchParams();

  // Wake up the HF Spaces backend as soon as the chat page loads.
  // Free-tier containers sleep after ~15 min of inactivity; pinging /health
  // starts the container so it's warm by the time the user hits Send.
  useEffect(() => {
    const slow = setTimeout(() => setWarmup("slow"), 3000);

    fetch("/api/v1/health")
      .then(() => setWarmup("ready"))
      .catch(() => setWarmup("ready"))
      .finally(() => clearTimeout(slow));

    return () => clearTimeout(slow);
  }, []);

  useEffect(() => {
    const q = searchParams.get("q");
    if (q) setInput(q);
  }, [searchParams]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit() {
    const question = input.trim();
    if (!question || isStreaming) return;

    setInput("");
    setIsStreaming(true);

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", isStreaming: true },
    ]);

    await streamChat(question, {
      onToken: (token) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          updated[updated.length - 1] = { ...last, content: last.content + token };
          return updated;
        });
      },
      onCitations: (citations) => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { ...updated[updated.length - 1], citations };
          return updated;
        });
      },
      onDone: () => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { ...updated[updated.length - 1], isStreaming: false };
          return updated;
        });
        setIsStreaming(false);
      },
      onError: (message) => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: `Error: ${message}`,
            isStreaming: false,
          };
          return updated;
        });
        setIsStreaming(false);
      },
    });
  }

  return (
    <div className="flex flex-col h-screen bg-cream-100">

      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="bg-forest-800 px-5 h-14 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="text-forest-300 hover:text-white transition-colors p-1 -ml-1 rounded"
            aria-label="Back to home"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div className="w-px h-5 bg-forest-600" />
          <Image
            src="/harp.svg"
            alt="Irish harp"
            width={12}
            height={19}
            className="opacity-60 brightness-0 invert"
          />
          <span className="font-serif text-white text-[0.95rem] tracking-[0.01em]">
            Ireland Public Services Advisor
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-forest-300 inline-block" />
          <span className="text-xs text-forest-300 hidden sm:block">Sources cited</span>
        </div>
      </header>

      {/* ── Cold-start banner ──────────────────────────────────── */}
      {warmup === "slow" && (
        <div className="shrink-0 bg-amber-50 border-b border-amber-200 px-5 py-2 flex items-center gap-2">
          <span className="w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin shrink-0" />
          <p className="text-xs text-amber-700">
            <strong>Waking up the backend</strong> — free-tier cold start (~30s). Subsequent messages are instant.
          </p>
        </div>
      )}

      {/* ── Messages ───────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-4 py-8">

          {/* Empty state */}
          {messages.length === 0 && (
            <div className="mt-4">
              <div className="text-center mb-10">
                <div className="w-16 h-16 rounded-2xl bg-forest-800 flex items-center justify-center mx-auto mb-5 shadow-sm">
                  <span className="text-3xl">🏛️</span>
                </div>
                <h2 className="font-serif text-2xl font-bold text-stone-950 mb-2">
                  Ask about Irish public services
                </h2>
                <p className="text-stone-500 text-sm max-w-sm mx-auto leading-relaxed">
                  Every answer is grounded in official sources —
                  Citizens Information, Revenue, ISD, DSP, HSE.
                </p>
              </div>

              <div className="grid sm:grid-cols-2 gap-3">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => setInput(q)}
                    className="text-left p-4 rounded-xl bg-white border border-stone-200 hover:border-forest-400 hover:bg-forest-50 transition-colors text-sm text-stone-700 shadow-sm leading-relaxed"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* ── Input bar ──────────────────────────────────────────── */}
      <div className="shrink-0 bg-cream-100 border-t border-stone-200 px-4 py-4">
        <div className="max-w-2xl mx-auto">
          <ChatInput
            value={input}
            onChange={setInput}
            onSubmit={handleSubmit}
            disabled={isStreaming}
          />
          <p className="text-center text-xs text-stone-400 mt-3 leading-relaxed">
            Informational only · Not legal advice · Sources cited for every claim
          </p>
        </div>
      </div>

    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatContent />
    </Suspense>
  );
}
