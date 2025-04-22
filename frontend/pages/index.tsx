import Head from "next/head";
import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/router";
import { isAuthenticated } from "@/lib/auth";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) router.replace("/dashboard");
  }, [router]);

  return (
    <>
      <Head>
        <title>QuarterWatch — Earnings call intelligence</title>
      </Head>

      <div className="min-h-screen bg-stone-25 flex flex-col">
        {/* Nav */}
        <header className="px-8 py-5 flex items-center justify-between max-w-6xl mx-auto w-full">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-stone-900 flex items-center justify-center">
              <span className="text-amber-400 text-sm font-bold font-mono">Q</span>
            </div>
            <span className="font-display font-semibold text-stone-900 text-base">
              QuarterWatch
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/auth/login" className="btn-secondary">
              Sign in
            </Link>
            <Link href="/auth/register" className="btn-primary">
              Get started
            </Link>
          </div>
        </header>

        {/* Hero */}
        <main className="flex-1 flex flex-col items-center justify-center px-6 text-center pb-24">
          <div className="animate-in max-w-2xl">
            <div className="inline-flex items-center gap-2 bg-amber-50 border border-amber-100 text-amber-700 text-xs font-medium px-3 py-1.5 rounded-full mb-8">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              Multi-layer pipeline analysis
            </div>

            <h1 className="font-display text-5xl font-semibold text-stone-900 mb-6 text-balance leading-tight">
              Understand what earnings calls actually reveal
            </h1>

            <p className="text-stone-500 text-lg leading-relaxed mb-10 max-w-xl mx-auto">
              Enter a ticker and quarter. QuarterWatch fetches the transcript, segments it by speaker, and runs sentiment, confidence, entity, and faithfulness analysis on every section.
            </p>

            <div className="flex items-center justify-center gap-3">
              <Link href="/auth/register" className="btn-accent px-7 py-3 text-base">
                Start analysing
              </Link>
              <Link href="/auth/login" className="btn-secondary px-7 py-3 text-base">
                Sign in
              </Link>
            </div>
          </div>

          {/* Feature grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-20 max-w-3xl w-full">
            {[
              { label: "Segment sentiment", desc: "Per-section NLP scoring with confidence flags" },
              { label: "Hedging detection", desc: "Gemini-powered confidence and risk language scoring" },
              { label: "Entity extraction", desc: "Financial NER with hallucination filtering" },
              { label: "Price movement", desc: "Closing price on call day, D+1, and D+7" },
            ].map((feat) => (
              <div key={feat.label} className="card p-5 text-left">
                <p className="text-sm font-semibold text-stone-900 mb-1">{feat.label}</p>
                <p className="text-xs text-stone-500 leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </main>
      </div>
    </>
  );
}
