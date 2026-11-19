import React, { useState } from 'react';
import { Finding, AIReview } from '../types';
import { scansApi, getErrorMessage } from '../services/api';
import {
  Sparkles,
  AlertTriangle,
  Lightbulb,
  Check,
  Copy,
  Terminal,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';
import toast from 'react-hot-toast';

interface FindingDetailProps {
  finding: Finding;
  onUpdateFinding?: (updatedFinding: Finding) => void;
}

export const FindingDetail: React.FC<FindingDetailProps> = ({
  finding,
  onUpdateFinding,
}) => {
  const [copied, setCopied] = useState(false);
  const [isRequestingAI, setIsRequestingAI] = useState(false);
  const [aiReview, setAiReview] = useState<AIReview | undefined>(
    finding.ai_review
  );

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    toast.success('Code copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleGenerateAIReview = async () => {
    try {
      setIsRequestingAI(true);
      const review = await scansApi.triggerAIReview(finding.id);
      setAiReview(review);
      if (onUpdateFinding) {
        onUpdateFinding({
          ...finding,
          ai_review: review,
        });
      }
      toast.success('AI Review analysis generated!');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsRequestingAI(false);
    }
  };

  return (
    <div className="p-6 bg-[#0f0f18]/90 border-t border-indigo-500/10 space-y-6">
      {/* Original Code Snippet */}
      {finding.code_snippet && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span className="flex items-center gap-1.5 text-indigo-300">
              <Terminal className="w-4 h-4 text-indigo-400" />
              {finding.file_path}:{finding.line_number}
            </span>
            <span className="text-slate-500">Flagged Code</span>
          </div>

          <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-[#07070b]">
            <pre className="p-4 text-xs font-mono text-slate-200 overflow-x-auto leading-relaxed">
              <code>{finding.code_snippet}</code>
            </pre>
          </div>
        </div>
      )}

      {/* AI Review Section */}
      {aiReview ? (
        <div className="rounded-xl border border-indigo-500/20 bg-indigo-950/10 p-5 space-y-5">
          <div className="flex items-center justify-between border-b border-indigo-500/15 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                <Sparkles className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-semibold text-indigo-200 tracking-wide flex items-center gap-2">
                AI Deep Security & Quality Analysis
                {aiReview.confidence && (
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-900/60 text-indigo-300 border border-indigo-500/30 font-normal">
                    {Math.round(aiReview.confidence * 100)}% Confidence
                  </span>
                )}
              </h4>
            </div>

            <button
              onClick={handleGenerateAIReview}
              disabled={isRequestingAI}
              className="text-xs text-slate-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
              title="Regenerate review"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${isRequestingAI ? 'animate-spin' : ''}`}
              />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>

          {/* AI Explanation */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 uppercase tracking-wider">
              <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
              <span>Explanation & Root Cause</span>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed pl-5 font-normal">
              {aiReview.explanation}
            </p>
          </div>

          {/* Potential Impact */}
          {aiReview.impact && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-300 uppercase tracking-wider">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                <span>Security & Reliability Impact</span>
              </div>
              <p className="text-sm text-slate-300/90 leading-relaxed pl-5">
                {aiReview.impact}
              </p>
            </div>
          )}

          {/* Suggested Fix Description */}
          {aiReview.suggested_fix && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-300 uppercase tracking-wider">
                <AlertTriangle className="w-3.5 h-3.5 text-emerald-400" />
                <span>Remediation Advice</span>
              </div>
              <p className="text-sm text-slate-300/90 leading-relaxed pl-5">
                {aiReview.suggested_fix}
              </p>
            </div>
          )}

          {/* Fixed Code Block */}
          {aiReview.fixed_code && (
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                  <Check className="w-4 h-4" />
                  Recommended Fixed Code:
                </span>
                <button
                  onClick={() => handleCopyCode(aiReview.fixed_code!)}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-slate-400" />
                      <span>Copy Fix</span>
                    </>
                  )}
                </button>
              </div>

              <div className="relative rounded-xl overflow-hidden border border-emerald-500/30 bg-[#070b09]">
                <pre className="p-4 text-xs font-mono text-emerald-200 overflow-x-auto leading-relaxed">
                  <code>{aiReview.fixed_code}</code>
                </pre>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-indigo-500/20 bg-indigo-950/5 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-200">
                No AI Review generated yet for this issue
              </h4>
              <p className="text-xs text-slate-400">
                Generate instant AI analysis with explanation, impact, and fixed code.
              </p>
            </div>
          </div>

          <button
            onClick={handleGenerateAIReview}
            disabled={isRequestingAI}
            className="btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 whitespace-nowrap disabled:opacity-50"
          >
            {isRequestingAI ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Analyzing with AI...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate AI Review</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default FindingDetail;
