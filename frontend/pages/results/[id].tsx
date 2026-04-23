import Head from "next/head";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Layout } from "@/components/ui/Layout";
import { SegmentCard } from "@/components/dashboard/SegmentCard";
import { PriceChart } from "@/components/dashboard/PriceChart";
import { Spinner } from "@/components/ui/Spinner";
import { getJobResults, getApiError } from "@/lib/api";
import { formatQuarter } from "@/lib/utils";
import type { JobResults } from "@/types";

export default function ResultsPage() {
  const router = useRouter();
  const { id } = router.query;
  const [results, setResults] = useState<JobResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id || typeof id !== "string") return;
    getJobResults(id)
      .then(setResults)
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-32">
          <Spinner size="lg" />
        </div>
      </Layout>
    );
  }

  if (error || !results) {
    return (
      <Layout maxWidth="md">
        <div className="card p-8 text-center">
          <p className="text-stone-500 mb-4">{error || "Results not found."}</p>
          <Link href="/dashboard" className="btn-secondary">
            Back to dashboard
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <>
      <Head>
        <title>
          {results.ticker} {formatQuarter(results.quarter, results.year)} — QuarterWatch
        </title>
      </Head>

      <Layout maxWidth="xl">
        {/* Header */}
        <div className="flex items-start justify-between mb-8 animate-in">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Link
                href="/dashboard"
                className="text-stone-400 hover:text-stone-600 transition-colors text-sm flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Dashboard
              </Link>
            </div>
            <h1 className="font-display text-4xl font-semibold text-stone-900">
              <span className="font-mono">{results.ticker}</span>
            </h1>
            <p className="text-stone-500 mt-1">
              {formatQuarter(results.quarter, results.year)} earnings call
            </p>
          </div>

          <div className="text-right">
            <p className="text-xs text-stone-400 mb-1">Segments analysed</p>
            <p className="font-display text-3xl font-semibold text-stone-900">
              {results.segments.length}
            </p>
          </div>
        </div>

        {/* Segmentation notice */}
        {results.segmentation_notice && (
          <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-100 rounded-xl mb-6 animate-in">
            <svg className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M12 3a9 9 0 110 18A9 9 0 0112 3z" />
            </svg>
            <p className="text-sm text-amber-800">{results.segmentation_notice}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Segments column */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="font-semibold text-stone-900 text-sm uppercase tracking-wider mb-4">
              Transcript segments
            </h2>
            {results.segments
              .sort((a, b) => a.order_index - b.order_index)
              .map((segment, i) => (
                <SegmentCard key={segment.id} segment={segment} index={i} />
              ))}
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            <h2 className="font-semibold text-stone-900 text-sm uppercase tracking-wider mb-4">
              Market reaction
            </h2>
            {results.price_data ? (
              <PriceChart priceData={results.price_data} ticker={results.ticker} />
            ) : (
              <div className="card p-6">
                <h3 className="font-display font-semibold text-stone-900 mb-3">
                  Price movement
                </h3>
                <p className="text-sm text-stone-400">
                  Price data is fetched nightly. Check back shortly.
                </p>
              </div>
            )}

            {/* Quick stats */}
            <div className="card p-6">
              <h3 className="font-semibold text-stone-700 text-sm mb-4">
                Pipeline summary
              </h3>
              <div className="space-y-3">
                {[
                  {
                    label: "Verified summaries",
                    value: results.segments.filter(
                      (s) => s.summary?.faithfulness_status === "verified"
                    ).length,
                    total: results.segments.filter((s) => s.summary).length,
                  },
                  {
                    label: "Segments with entities",
                    value: results.segments.filter((s) => s.entities.length > 0).length,
                    total: results.segments.length,
                  },
                  {
                    label: "Sentiment scored",
                    value: results.segments.filter(
                      (s) => s.sentiment?.status === "available"
                    ).length,
                    total: results.segments.length,
                  },
                ].map((stat) => (
                  <div key={stat.label} className="flex items-center justify-between">
                    <span className="text-sm text-stone-500">{stat.label}</span>
                    <span className="text-sm font-medium text-stone-900 font-mono">
                      {stat.value}/{stat.total}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
