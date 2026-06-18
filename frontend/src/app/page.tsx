import Link from "next/link";
import Image from "next/image";

const EXAMPLE_QUERIES = [
  "When can I switch from Stamp 2 to Stamp 1G?",
  "Am I eligible for Jobseeker's Benefit after being made redundant?",
  "What's the VAT registration threshold for SaaS in Ireland?",
  "How do I apply for a PPSN?",
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Ask in plain English",
    text: "No jargon needed. Ask exactly as you would ask a knowledgeable friend who knows Irish bureaucracy inside out.",
  },
  {
    step: "02",
    title: "AI searches official sources",
    text: "Revenue, Citizens Information, ISD, DSP, HSE — the relevant official guidance is located and synthesised in seconds.",
  },
  {
    step: "03",
    title: "Get a cited answer",
    text: "Every claim links to its original source. Verify anything at any time, or bring it to a professional.",
  },
];

const SOURCES = [
  { name: "Citizens Information", abbr: "CI" },
  { name: "Revenue.ie", abbr: "Rev" },
  { name: "Gov.ie", abbr: "Gov" },
  { name: "Irish Immigration", abbr: "ISD" },
  { name: "Dept. Social Protection", abbr: "DSP" },
  { name: "HSE", abbr: "HSE" },
];

const TRUST_POINTS = [
  {
    title: "Official sources only",
    body: "Every answer draws from Revenue, Citizens Information, Gov.ie, ISD, DSP, or HSE — not general internet content.",
  },
  {
    title: "Every claim is cited",
    body: "Source links appear alongside each answer. Click any citation to verify the original guidance yourself.",
  },
  {
    title: "Free, always",
    body: "No account required. No paywall. Built as a public good for anyone navigating the Irish public services system.",
  },
];

const STATS = [
  { value: "100%", label: "Recall@5" },
  { value: "1.0", label: "Avg rank" },
  { value: "0.93", label: "Faithfulness" },
  { value: "1,640", label: "Documents" },
  { value: "$0", label: "Hosting / mo" },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-cream-100 font-sans">

      {/* ── Navigation ─────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 bg-forest-800">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image
              src="/harp.svg"
              alt="Irish harp"
              width={14}
              height={22}
              className="opacity-70 brightness-0 invert"
            />
            <span className="font-serif text-white text-[0.95rem] tracking-[0.01em]">
              Ireland Public Services Advisor
            </span>
            <span className="hidden sm:inline-block text-[10px] font-semibold text-forest-300 bg-forest-700 border border-forest-600 rounded px-2 py-0.5 tracking-wide">
              v0.4
            </span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#about" className="hidden md:block text-sm text-forest-300 hover:text-white transition-colors">
              About
            </a>
            <a href="#story" className="hidden md:block text-sm text-forest-300 hover:text-white transition-colors">
              Story
            </a>
            <a href="#terms" className="hidden md:block text-sm text-forest-300 hover:text-white transition-colors">
              Terms &amp; Privacy
            </a>
            <Link
              href="/chat"
              className="bg-white hover:bg-cream-100 text-forest-800 text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              Ask a question
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 pt-24 pb-20">
        <p className="text-forest-600 text-xs font-semibold uppercase tracking-[0.15em] mb-7">
          Free · Open Source · Always Cited
        </p>
        <h1 className="font-serif text-5xl md:text-[3.75rem] text-stone-950 leading-[1.08] mb-7 max-w-2xl">
          Navigate Irish<br />
          public services<br />
          <em className="not-italic text-forest-700">with confidence.</em>
        </h1>
        <p className="text-[1.05rem] text-stone-500 leading-relaxed mb-10 max-w-lg">
          Clear, grounded answers about immigration, tax, welfare, and healthcare.
          Every response cites its official source so you can verify anything.
        </p>
        <Link
          href="/chat"
          className="inline-flex items-center gap-2 bg-forest-800 hover:bg-forest-900 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors shadow-sm"
        >
          Start asking
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </Link>

        {/* Example queries */}
        <div className="mt-14">
          <p className="text-xs text-stone-400 mb-4 font-semibold uppercase tracking-widest">Try asking:</p>
          <div className="flex flex-wrap gap-2.5">
            {EXAMPLE_QUERIES.map((q) => (
              <Link
                key={q}
                href={`/chat?q=${encodeURIComponent(q)}`}
                className="bg-white border border-stone-200 hover:border-forest-400 hover:bg-forest-50 text-stone-600 text-sm px-4 py-2.5 rounded-lg transition-colors shadow-sm leading-snug"
              >
                {q}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ───────────────────────────────────────── */}
      <section className="border-t border-stone-200 bg-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="text-forest-600 text-xs font-semibold uppercase tracking-[0.15em] mb-4">How it works</p>
          <h2 className="font-serif text-3xl text-stone-950 mb-14">
            Three steps from question to source.
          </h2>
          <div className="grid md:grid-cols-3 gap-10">
            {HOW_IT_WORKS.map((item) => (
              <div key={item.step}>
                <span className="font-serif text-[5rem] leading-none text-forest-100 block mb-4">
                  {item.step}
                </span>
                <div className="w-8 h-px bg-forest-300 mb-5" />
                <h3 className="text-base font-semibold text-stone-900 mb-2">{item.title}</h3>
                <p className="text-stone-500 leading-relaxed text-sm">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── About ──────────────────────────────────────────────── */}
      <section id="about" className="max-w-5xl mx-auto px-6 py-20">
        <div className="grid md:grid-cols-2 gap-16 items-start">
          <div>
            <p className="text-forest-600 text-xs font-semibold uppercase tracking-[0.15em] mb-5">
              About
            </p>
            <h2 className="font-serif text-3xl md:text-4xl text-stone-950 leading-tight mb-7">
              Built for everyone navigating Irish bureaucracy.
            </h2>
            <div className="space-y-4 text-stone-500 leading-relaxed text-sm">
              <p>
                The Irish public services landscape is vast. Revenue, Citizens Information,
                ISD, DSP, HSE — each with their own portals, eligibility rules, and processes.
                Most people don&apos;t know where to start.
              </p>
              <p>
                This tool brings it together. Ask a question in plain English and get an answer
                grounded in the latest official guidance, with sources you can click and verify
                — or bring to a professional for a second opinion.
              </p>
            </div>
          </div>
          <div className="flex flex-col gap-3">
            {TRUST_POINTS.map((item) => (
              <div
                key={item.title}
                className="flex items-start gap-4 p-5 rounded-xl bg-white border border-stone-200"
              >
                <span className="w-7 h-7 rounded-full bg-forest-800 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </span>
                <div>
                  <p className="font-semibold text-stone-900 text-sm mb-1">{item.title}</p>
                  <p className="text-stone-500 text-sm leading-relaxed">{item.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Story ──────────────────────────────────────────────── */}
      <section id="story" className="bg-forest-800 text-white relative overflow-hidden">
        {/* decorative circles — like infographic left panel */}
        <div className="absolute bottom-[-80px] right-[-80px] w-64 h-64 rounded-full bg-forest-700 opacity-40 pointer-events-none" />
        <div className="absolute top-[-50px] left-[-50px] w-40 h-40 rounded-full bg-white opacity-[0.04] pointer-events-none" />
        <div className="max-w-5xl mx-auto px-6 py-20 relative z-10">
          <div className="flex items-start gap-8 max-w-2xl">
            <Image
              src="/harp.svg"
              alt="Irish harp"
              width={28}
              height={44}
              className="opacity-40 brightness-0 invert mt-1 flex-shrink-0"
            />
            <div>
              <p className="text-forest-300 text-xs font-semibold uppercase tracking-[0.15em] mb-5">
                The Story
              </p>
              <h2 className="font-serif text-3xl md:text-4xl leading-tight mb-8">
                It started with a question<br /><em>no one could quickly answer.</em>
              </h2>
              <div className="space-y-5 text-forest-100 leading-relaxed text-[0.95rem]">
                <p>
                  Navigating Irish public services as a new arrival — or even as a long-term resident
                  — means bouncing between a dozen different websites, reading dense policy documents,
                  and still not being sure whether the answer applies to your specific situation.
                </p>
                <p>
                  The information exists. Citizens Information, Revenue, ISD, DSP, and HSE all publish
                  thorough guidance. But it&apos;s scattered, written in official language, and requires
                  you to already understand the system just to find what you need.
                </p>
                <p>
                  This tool bridges that gap. An AI that knows where to look, surfaces the right
                  information, and shows you exactly where it comes from so you can verify it or
                  bring it to a professional.
                </p>
              </div>
              <p className="text-forest-400 text-xs italic border-t border-forest-700 pt-5 mt-8">
                Not legal advice. Always verify with the relevant authority or a qualified professional.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Official Sources ───────────────────────────────────── */}
      <section className="bg-white border-b border-stone-200">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <p className="text-forest-600 text-xs font-semibold uppercase tracking-[0.15em] mb-3">Sources</p>
          <h2 className="font-serif text-2xl text-stone-900 mb-2">
            Official sources only.
          </h2>
          <p className="text-stone-400 text-sm mb-10">
            Every answer is grounded in guidance from these Irish authorities.
          </p>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
            {SOURCES.map((source) => (
              <div
                key={source.name}
                className="flex flex-col items-center justify-center gap-2 p-4 rounded-xl bg-cream-100 border border-stone-200 text-center"
              >
                <span className="w-9 h-9 rounded-full bg-forest-800 text-white text-xs font-bold flex items-center justify-center">
                  {source.abbr}
                </span>
                <span className="text-xs font-medium text-stone-600 leading-tight">{source.name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Contact ────────────────────────────────────────────── */}
      <section id="contact" className="max-w-5xl mx-auto px-6 py-20">
        <div className="max-w-lg">
          <p className="text-forest-600 text-xs font-semibold uppercase tracking-[0.15em] mb-5">
            Contact
          </p>
          <h2 className="font-serif text-3xl text-stone-950 mb-4">
            Get in touch.
          </h2>
          <p className="text-stone-500 leading-relaxed mb-8 text-sm">
            Found an incorrect answer? Want to suggest a source we should add?
            Spotted a gap in coverage? We&apos;d genuinely love to hear from you.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <a
              href="https://github.com/saisrikardevasani/eu-ireland-public-services-ai-advisor"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 bg-stone-900 hover:bg-stone-800 text-white font-medium text-sm px-5 py-3 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
              View on GitHub
            </a>
            <a
              href="mailto:saisrikardevasani@gmail.com"
              className="inline-flex items-center justify-center gap-2 bg-white border border-stone-200 hover:border-forest-400 hover:bg-forest-50 text-stone-700 font-medium text-sm px-5 py-3 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
              </svg>
              Send feedback
            </a>
          </div>
        </div>
      </section>

      {/* ── Terms & Privacy ────────────────────────────────────── */}
      <section id="terms" className="border-t border-stone-200 bg-stone-50">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <p className="text-forest-600 text-xs font-semibold uppercase tracking-[0.15em] mb-4">Terms &amp; Privacy</p>
          <h2 className="font-serif text-2xl text-stone-900 mb-8">
            How this service works and what you should know.
          </h2>
          <div className="grid md:grid-cols-2 gap-8">

            <div className="space-y-5">
              <div>
                <h3 className="text-sm font-semibold text-stone-900 mb-2">Not legal or professional advice</h3>
                <p className="text-stone-500 text-sm leading-relaxed">
                  All answers are informational summaries of publicly available official guidance.
                  Nothing here constitutes legal, tax, immigration, or financial advice.
                  Always verify with the relevant authority (Revenue, DSP, Citizens Information,
                  the RTB, WRC, etc.) or consult a qualified professional before acting on any information.
                </p>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-900 mb-2">AI can make mistakes</h3>
                <p className="text-stone-500 text-sm leading-relaxed">
                  This tool uses large language models to interpret and summarise source material.
                  Rates, thresholds, eligibility rules, and procedures change regularly.
                  Always click through to the cited source to verify you have the most current information.
                </p>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-900 mb-2">No guarantee of accuracy or completeness</h3>
                <p className="text-stone-500 text-sm leading-relaxed">
                  The knowledge base is updated periodically but may not reflect the very latest
                  guidance. Do not rely solely on this tool for decisions with significant legal,
                  financial, or health consequences.
                </p>
              </div>
            </div>

            <div className="space-y-5">
              <div>
                <h3 className="text-sm font-semibold text-stone-900 mb-2">How your questions are processed</h3>
                <p className="text-stone-500 text-sm leading-relaxed">
                  When you send a question, it is transmitted to <strong>NVIDIA&apos;s AI inference API</strong>
                  {" "}(running Meta&apos;s Llama 3.3 70B model) to generate a response.
                  NVIDIA operates in the United States. By using this service you acknowledge that
                  your query is processed by a US-based third party. See{" "}
                  <a href="https://www.nvidia.com/en-us/about-nvidia/privacy-policy/" target="_blank" rel="noopener noreferrer" className="underline text-forest-600 hover:text-forest-800">
                    NVIDIA&apos;s privacy policy
                  </a>.
                </p>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-900 mb-2">What we do not store</h3>
                <p className="text-stone-500 text-sm leading-relaxed">
                  This service does not log, store, or retain your questions or answers.
                  No user accounts, no session history, no analytics tied to your queries.
                  The only data stored is the curated knowledge base of official Irish guidance.
                </p>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-900 mb-2">Do not include personal information</h3>
                <p className="text-stone-500 text-sm leading-relaxed">
                  Do not include PPS numbers, addresses, passport numbers, financial account
                  details, health information, or other sensitive personal data in your questions.
                  Phrase queries in general terms — e.g. &ldquo;am I eligible for Jobseeker&apos;s
                  Benefit if I was made redundant?&rdquo; rather than including personal identifiers.
                </p>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ── Footer / Stats ─────────────────────────────────────── */}
      <footer className="bg-forest-800">
        <div className="max-w-5xl mx-auto px-6 py-5 flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Stats row */}
          <div className="flex items-center gap-0 divide-x divide-forest-700">
            {STATS.map((s) => (
              <div key={s.label} className="flex flex-col items-center px-5 first:pl-0 last:pr-0">
                <span className="font-serif text-lg text-forest-200 leading-none">{s.value}</span>
                <span className="text-[9px] font-semibold text-forest-400 uppercase tracking-wider mt-1">{s.label}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <Image src="/harp.svg" alt="" width={11} height={17} className="opacity-30 brightness-0 invert" />
            <p className="text-xs text-forest-400 text-center sm:text-right max-w-xs leading-relaxed">
              Informational only. Not legal advice. Always verify with the relevant authority.
            </p>
          </div>
        </div>
      </footer>

    </div>
  );
}
