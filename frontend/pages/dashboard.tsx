import Head from "next/head";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Layout } from "@/components/ui/Layout";
import { JobForm } from "@/components/forms/JobForm";
import { useAuth } from "@/hooks/useAuth";
import { listJobs, getApiError } from "@/lib/api";
import { formatQuarter, formatDate } from "@/lib/utils";
import type { JobListItem, JobStatus } from "@/types";

const statusLabel: Record<JobStatus, string> = {
  pending: "Pending",
  processing: "Processing",
  awaiting_upload: "Needs transcript",
  complete: "Complete",
  failed: "Failed",
};

const statusStyles: Record<JobStatus, string> = {
  pending: "badge-neutral",
  processing: "badge-warning animate-pulse-soft",
  awaiting_upload: "badge-warning",
  complete: "badge-positive",
  failed: "badge-negative",
};

export default function DashboardPage() {
  const { user } = useAuth(true);
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(true);

  useEffect(() => {
    listJobs()
      .then(setJobs)
      .catch(() => {})
      .finally(() => setLoadingJobs(false));
  }, []);

  return (
    <>
      <Head>
        <title>Dashboard — QuarterWatch</title>
      </Head>

      <Layout>
        <div className="mb-8">
          <h1 className="font-display text-3xl font-semibold text-stone-900 mb-1">
            {user?.name ? `Good to see you, ${user.name.split(" ")[0]}.` : "Dashboard"}
          </h1>
          <p className="text-stone-500">
            Run a new analysis or pick up a previous one below.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Job form */}
          <div className="lg:col-span-2">
            <JobForm />
          </div>

          {/* Job history */}
          <div className="lg:col-span-3">
            <h2 className="font-semibold text-stone-900 mb-4 text-sm uppercase tracking-wider">
              Recent analyses
            </h2>

            {loadingJobs ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="card p-4">
                    <div className="h-4 shimmer rounded w-24 mb-2" />
                    <div className="h-3 shimmer rounded w-16" />
                  </div>
                ))}
              </div>
            ) : jobs.length === 0 ? (
              <div className="card p-8 text-center">
                <p className="text-stone-400 text-sm">
                  No analyses yet. Submit your first ticker above.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {jobs.map((job) => (
                  <Link
                    key={job.id}
                    href={job.status === "complete" ? `/results/${job.id}` : "#"}
                    className={`card p-4 flex items-center justify-between group transition-shadow hover:shadow-card-hover ${
                      job.status !== "complete" ? "cursor-default" : ""
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-semibold text-stone-900 text-sm">
                        {job.ticker}
                      </span>
                      <span className="text-stone-400 text-sm">
                        {formatQuarter(job.quarter, job.year)}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-stone-400">
                        {formatDate(job.created_at)}
                      </span>
                      <span className={`badge ${statusStyles[job.status]}`}>
                        {statusLabel[job.status]}
                      </span>
                      {job.status === "complete" && (
                        <svg
                          className="w-4 h-4 text-stone-300 group-hover:text-stone-500 transition-colors"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </Layout>
    </>
  );
}
