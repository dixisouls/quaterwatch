import { useState } from "react";
import { cn, sentimentLabel, sentimentColor, confidenceLabel } from "@/lib/utils";
import type { Segment } from "@/types";

function highlightText(
  text: string,
  keyPhrases: string[],
  hedgingPhrases: string[]
): React.ReactNode[] {
  type Range = { start: number; end: number; type: "assertive" | "hedging" };
  const ranges: Range[] = [];
  const lower = text.toLowerCase();

  const collect = (phrases: string[], type: Range["type"]) => {
    for (const phrase of phrases) {
      const lp = phrase.toLowerCase();
      let idx = lower.indexOf(lp);
      while (idx !== -1) {
        ranges.push({ start: idx, end: idx + phrase.length, type });
        idx = lower.indexOf(lp, idx + 1);
      }
    }
  };

  collect(keyPhrases, "assertive");
  collect(hedgingPhrases, "hedging");
  ranges.sort((a, b) => a.start - b.start);

  const merged: Range[] = [];
  for (const r of ranges) {
    if (merged.length === 0 || r.start >= merged[merged.length - 1].end) {
      merged.push(r);
    }
  }

  const nodes: React.ReactNode[] = [];
  let cursor = 0;
  for (const { start, end, type } of merged) {
    if (cursor < start) nodes.push(text.slice(cursor, start));
    nodes.push(
      <mark
        key={start}
        className={cn(
          "rounded-sm px-0.5",
          type === "assertive" ? "bg-green-100 text-green-900" : "bg-amber-100 text-amber-900"
        )}
      >
        {text.slice(start, end)}
      </mark>
    );
    cursor = end;
  }
  if (cursor < text.length) nodes.push(text.slice(cursor));
  return nodes;
}

interface SegmentCardProps {
  segment: Segment;
  index: number;
}

export function SegmentCard({ segment, index }: SegmentCardProps) {
  const [expanded, setExpanded] = useState(false);

  const sentiment = segment.sentiment;
  const confidence = segment.confidence;
  const summary = segment.summary;
  const entities = segment.entities;

  const sColor = sentimentColor(sentiment?.score ?? null);

  return (
    <div
      className="card overflow-hidden animate-in"
      style={{ animationDelay: `${index * 0.08}s` }}
    >
      {/* Header */}
      <div className="px-6 py-5 border-b border-stone-50">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-stone-400 bg-stone-50 border border-stone-100 rounded-md px-2 py-0.5">
              {String(index + 1).padStart(2, "0")}
            </span>
            <h3 className="font-display font-semibold text-stone-900 text-base">
              {segment.name}
            </h3>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-xs text-stone-400 font-mono">
              {segment.word_count.toLocaleString()} words
            </span>
          </div>
        </div>

        {/* Signal badges row */}
        <div className="flex flex-wrap items-center gap-2 mt-4">
          {/* Sentiment */}
          {sentiment?.status === "available" ? (
            <span
              className={cn(
                "badge",
                sColor === "positive" && "badge-positive",
                sColor === "negative" && "badge-negative",
                sColor === "neutral" && "badge-neutral"
              )}
            >
              <span className={cn(
                "w-1.5 h-1.5 rounded-full",
                sColor === "positive" && "bg-green-500",
                sColor === "negative" && "bg-red-500",
                sColor === "neutral" && "bg-stone-400"
              )} />
              {sentimentLabel(sentiment.score)} sentiment
              {sentiment.score !== null && (
                <span className="opacity-60 ml-0.5">
                  ({sentiment.score > 0 ? "+" : ""}{sentiment.score?.toFixed(2)}
                  {sentiment.magnitude !== null && ` · mag ${sentiment.magnitude.toFixed(1)}`})
                </span>
              )}
            </span>
          ) : (
            <span className="badge badge-neutral">
              Sentiment {sentiment?.status === "insufficient_data" ? "insufficient data" : "unavailable"}
            </span>
          )}

          {/* Confidence */}
          {confidence ? (
            <span className={cn(
              "badge",
              confidence.scoring_method === "heuristic" ? "badge-heuristic" : "badge-neutral"
            )}>
              {confidenceLabel(confidence.score)} confidence
              {confidence.score !== null && (
                <span className="opacity-60 ml-0.5">({confidence.score?.toFixed(1)}/10)</span>
              )}
              {confidence.scoring_method === "heuristic" && (
                <span className="ml-1 opacity-70">heuristic</span>
              )}
            </span>
          ) : null}

          {/* Faithfulness */}
          {summary && (
            <span className={cn(
              "badge",
              summary.faithfulness_status === "verified" && "badge-positive",
              summary.faithfulness_status === "partially_verified" && "badge-warning",
              summary.faithfulness_status === "unverified" && "badge-negative"
            )}>
              {summary.faithfulness_status === "verified" && "Verified"}
              {summary.faithfulness_status === "partially_verified" && "Partially verified"}
              {summary.faithfulness_status === "unverified" && "Unverified"}
            </span>
          )}

          {/* Summary method */}
          {summary?.summary_method === "extractive" && (
            <span className="badge badge-warning">Extractive summary</span>
          )}
        </div>

        {/* Confidence phrases */}
        {confidence && ((confidence.key_phrases?.length ?? 0) > 0 || (confidence.hedging_phrases?.length ?? 0) > 0) && (
          <div className="flex flex-wrap items-start gap-x-4 gap-y-2 mt-3">
            {(confidence.key_phrases?.length ?? 0) > 0 && (
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-xs text-stone-400 mr-0.5">assertive</span>
                {confidence.key_phrases!.map((phrase, i) => (
                  <span key={i} className="text-xs bg-green-50 text-green-700 border border-green-100 rounded-md px-2 py-0.5">
                    {phrase}
                  </span>
                ))}
              </div>
            )}
            {(confidence.hedging_phrases?.length ?? 0) > 0 && (
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-xs text-stone-400 mr-0.5">hedging</span>
                {confidence.hedging_phrases!.map((phrase, i) => (
                  <span key={i} className="text-xs bg-amber-50 text-amber-700 border border-amber-100 rounded-md px-2 py-0.5">
                    {phrase}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Summary */}
      {summary ? (
        <div className="px-6 py-5 border-b border-stone-50">
          {summary.faithfulness_status === "unverified" && (
            <div className="flex items-start gap-2.5 mb-3 p-3 bg-red-50 border border-red-100 rounded-xl">
              <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M12 3a9 9 0 110 18A9 9 0 0112 3z" />
              </svg>
              <p className="text-xs text-red-700">
                This summary could not be fully verified against the source text.
              </p>
            </div>
          )}
          {summary.faithfulness_status === "partially_verified" && summary.flagged_claims && summary.flagged_claims.length > 0 && (
            <div className="flex items-start gap-2.5 mb-3 p-3 bg-amber-50 border border-amber-100 rounded-xl">
              <svg className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M12 3a9 9 0 110 18A9 9 0 0112 3z" />
              </svg>
              <div>
                <p className="text-xs text-amber-700">
                  Some claims in this summary could not be fully verified.
                </p>
                <ul className="mt-2 space-y-0.5">
                  {summary.flagged_claims.map((claim, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-xs text-amber-800">
                      <span className="mt-1.5 w-1 h-1 rounded-full bg-amber-500 flex-shrink-0" />
                      {claim}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
          <p className="text-sm text-stone-700 leading-relaxed">{summary.text}</p>

          {summary.key_points && summary.key_points.length > 0 && (
            <ul className="mt-3 space-y-1.5">
              {summary.key_points.map((point, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-stone-600">
                  <span className="w-1 h-1 rounded-full bg-amber-400 flex-shrink-0 mt-2" />
                  {point}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      {/* Entities */}
      {entities.length > 0 && (() => {
        const grouped = entities.reduce<Record<string, typeof entities>>((acc, e) => {
          const key = e.entity_type ?? "Other";
          (acc[key] ??= []).push(e);
          return acc;
        }, {});
        const sortedGroups = Object.entries(grouped).sort((a, b) => b[1].length - a[1].length);
        const multipleGroups = sortedGroups.length > 1;

        return (
          <div className="px-6 py-4 border-b border-stone-50">
            <p className="text-xs font-medium text-stone-400 uppercase tracking-wider mb-3">
              Entities
            </p>
            <div className="space-y-3">
              {sortedGroups.map(([type, group]) => (
                <div key={type}>
                  {multipleGroups && (
                    <p className="text-xs text-stone-400 mb-1.5">{type}</p>
                  )}
                  <div className="flex flex-wrap gap-1.5">
                    {group.map((entity, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center text-xs bg-stone-50 border border-stone-100 text-stone-700 rounded-lg px-2.5 py-1"
                      >
                        <span className="font-medium">{entity.name}</span>
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      {/* Expand source text */}
      <div className="px-6 py-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 text-xs text-stone-400 hover:text-stone-600 transition-colors"
        >
          <svg
            className={cn("w-3.5 h-3.5 transition-transform", expanded && "rotate-90")}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          {expanded ? "Hide source text" : "Show source text"}
        </button>

        {expanded && (
          <div className="mt-3 p-4 bg-stone-25 border border-stone-100 rounded-xl">
            <p className="text-xs font-mono text-stone-600 leading-relaxed whitespace-pre-wrap">
              {highlightText(
                segment.text,
                confidence?.key_phrases ?? [],
                confidence?.hedging_phrases ?? []
              )}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
