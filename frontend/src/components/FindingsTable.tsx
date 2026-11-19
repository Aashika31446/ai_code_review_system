import React, { useState, useMemo } from 'react';
import { Finding } from '../types';
import SeverityBadge from './SeverityBadge';
import FindingDetail from './FindingDetail';
import {
  ChevronDown,
  ChevronRight,
  Filter,
  ArrowUpDown,
  Search,
  FileCode2,
  Sparkles,
  ChevronLeft,
  ChevronsLeft,
  ChevronsRight,
  Inbox,
} from 'lucide-react';

interface FindingsTableProps {
  findings: Finding[];
  onUpdateFinding?: (updated: Finding) => void;
}

const SEVERITY_WEIGHT: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

export const FindingsTable: React.FC<FindingsTableProps> = ({
  findings,
  onUpdateFinding,
}) => {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'desc' | 'asc'>('desc');
  const [expandedRows, setExpandedRows] = useState<Set<string | number>>(new Set());
  const [currentPage, setCurrentPage] = useState<number>(1);
  const itemsPerPage = 10;

  // Extract unique categories for filter dropdown
  const categories = useMemo(() => {
    const set = new Set<string>();
    findings.forEach((f) => {
      if (f.category) set.add(f.category);
    });
    return Array.from(set);
  }, [findings]);

  // Toggle single row expand
  const toggleRow = (id: string | number) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Toggle sort direction
  const handleSortBySeverity = () => {
    setSortDirection((prev) => (prev === 'desc' ? 'asc' : 'desc'));
  };

  // Filter and sort findings
  const filteredFindings = useMemo(() => {
    return findings
      .filter((finding) => {
        // Severity filter
        if (
          selectedSeverity !== 'all' &&
          finding.severity.toLowerCase() !== selectedSeverity.toLowerCase()
        ) {
          return false;
        }

        // Category filter
        if (
          selectedCategory !== 'all' &&
          finding.category.toLowerCase() !== selectedCategory.toLowerCase()
        ) {
          return false;
        }

        // Search query
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchFile = finding.file_path.toLowerCase().includes(q);
          const matchRule = finding.rule_id.toLowerCase().includes(q) || (finding.rule_name && finding.rule_name.toLowerCase().includes(q));
          const matchMsg = finding.message.toLowerCase().includes(q);
          if (!matchFile && !matchRule && !matchMsg) return false;
        }

        return true;
      })
      .sort((a, b) => {
        const weightA = SEVERITY_WEIGHT[a.severity.toLowerCase()] || 0;
        const weightB = SEVERITY_WEIGHT[b.severity.toLowerCase()] || 0;
        return sortDirection === 'desc' ? weightB - weightA : weightA - weightB;
      });
  }, [findings, selectedSeverity, selectedCategory, searchQuery, sortDirection]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredFindings.length / itemsPerPage));
  const paginatedFindings = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredFindings.slice(start, start + itemsPerPage);
  }, [filteredFindings, currentPage]);

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Table Filters & Search Bar */}
      <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between glass p-4 rounded-xl">
        <div className="flex flex-wrap items-center gap-3">
          {/* Severity Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={selectedSeverity}
              onChange={(e) => {
                setSelectedSeverity(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-[#12121a] text-xs text-slate-200 border border-slate-700/80 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-[#12121a] text-xs text-slate-200 border border-slate-700/80 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="all">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.replace(/_/g, ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Sort Button */}
          <button
            onClick={handleSortBySeverity}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#12121a] hover:bg-slate-800 text-xs text-slate-300 border border-slate-700/80 rounded-lg transition-colors"
            title="Sort by Severity"
          >
            <ArrowUpDown className="w-3.5 h-3.5 text-indigo-400" />
            <span>Severity ({sortDirection === 'desc' ? 'High-to-Low' : 'Low-to-High'})</span>
          </button>
        </div>

        {/* Search Input */}
        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Search files, rules, messages..."
            className="w-full bg-[#12121a] text-xs text-slate-200 placeholder-slate-500 pl-9 pr-4 py-2 border border-slate-700/80 rounded-lg focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
      </div>

      {/* Table Container */}
      <div className="glass rounded-xl overflow-hidden border border-slate-800 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800/80 bg-[#12121e]/80 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                <th className="py-3.5 px-4 w-12 text-center">#</th>
                <th className="py-3.5 px-4 w-32 cursor-pointer select-none hover:text-slate-200" onClick={handleSortBySeverity}>
                  <div className="flex items-center gap-1.5">
                    <span>Severity</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th className="py-3.5 px-4 min-w-[200px]">File & Location</th>
                <th className="py-3.5 px-4 w-32">Category</th>
                <th className="py-3.5 px-4 min-w-[160px]">Rule ID</th>
                <th className="py-3.5 px-4 min-w-[300px]">Issue Description</th>
                <th className="py-3.5 px-4 w-28 text-right">Actions</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-800/60">
              {paginatedFindings.length > 0 ? (
                paginatedFindings.map((finding) => {
                  const isExpanded = expandedRows.has(finding.id);
                  const hasAIReview = !!finding.ai_review;

                  return (
                    <React.Fragment key={finding.id}>
                      <tr
                        onClick={() => toggleRow(finding.id)}
                        className={`group cursor-pointer transition-colors duration-150 ${
                          isExpanded
                            ? 'bg-indigo-950/20'
                            : 'hover:bg-slate-800/40 bg-transparent'
                        }`}
                      >
                        {/* Expand Icon */}
                        <td className="py-3.5 px-4 text-center">
                          <button
                            type="button"
                            className="p-1 rounded text-slate-400 group-hover:text-indigo-400 transition-colors"
                          >
                            {isExpanded ? (
                              <ChevronDown className="w-4 h-4 text-indigo-400" />
                            ) : (
                              <ChevronRight className="w-4 h-4" />
                            )}
                          </button>
                        </td>

                        {/* Severity */}
                        <td className="py-3.5 px-4">
                          <SeverityBadge severity={finding.severity} />
                        </td>

                        {/* File & Line */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            <FileCode2 className="w-4 h-4 text-cyan-400 shrink-0" />
                            <div className="font-mono text-xs text-slate-300 truncate max-w-[260px]" title={finding.file_path}>
                              {finding.file_path}
                              <span className="text-indigo-400 font-semibold ml-1">
                                :{finding.line_number}
                              </span>
                            </div>
                          </div>
                        </td>

                        {/* Category */}
                        <td className="py-3.5 px-4">
                          <span className="inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700/60 capitalize">
                            {finding.category.replace(/_/g, ' ')}
                          </span>
                        </td>

                        {/* Rule */}
                        <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                          <span className="text-slate-300 font-medium">
                            {finding.rule_id}
                          </span>
                        </td>

                        {/* Message */}
                        <td className="py-3.5 px-4 text-xs text-slate-300">
                          <p className="line-clamp-2">{finding.message}</p>
                        </td>

                        {/* Actions */}
                        <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => toggleRow(finding.id)}
                            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                              hasAIReview
                                ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30'
                                : 'bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700'
                            }`}
                          >
                            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                            <span>{isExpanded ? 'Hide' : 'Review'}</span>
                          </button>
                        </td>
                      </tr>

                      {/* Expanded AI Review & Details */}
                      {isExpanded && (
                        <tr>
                          <td colSpan={7} className="p-0 border-b border-indigo-500/20">
                            <FindingDetail
                              finding={finding}
                              onUpdateFinding={onUpdateFinding}
                            />
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="py-16 text-center">
                    <div className="flex flex-col items-center justify-center gap-3">
                      <div className="p-4 rounded-full bg-slate-800/60 border border-slate-700/50 text-slate-400">
                        <Inbox className="w-8 h-8" />
                      </div>
                      <h4 className="text-base font-semibold text-slate-300">
                        No findings match your criteria
                      </h4>
                      <p className="text-xs text-slate-500 max-w-sm">
                        Try adjusting your severity or category filters, or search term to see more results.
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {filteredFindings.length > 0 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-6 py-4 bg-[#12121e]/80 border-t border-slate-800 text-xs text-slate-400">
            <div>
              Showing{' '}
              <span className="font-semibold text-slate-200">
                {(currentPage - 1) * itemsPerPage + 1}
              </span>{' '}
              to{' '}
              <span className="font-semibold text-slate-200">
                {Math.min(currentPage * itemsPerPage, filteredFindings.length)}
              </span>{' '}
              of{' '}
              <span className="font-semibold text-slate-200">
                {filteredFindings.length}
              </span>{' '}
              findings
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => handlePageChange(1)}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 disabled:opacity-40 disabled:hover:bg-transparent"
                title="First Page"
              >
                <ChevronsLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 disabled:opacity-40 disabled:hover:bg-transparent"
                title="Previous Page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <div className="px-3 py-1 font-semibold text-slate-200">
                Page {currentPage} of {totalPages}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 disabled:opacity-40 disabled:hover:bg-transparent"
                title="Next Page"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => handlePageChange(totalPages)}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 disabled:opacity-40 disabled:hover:bg-transparent"
                title="Last Page"
              >
                <ChevronsRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FindingsTable;
