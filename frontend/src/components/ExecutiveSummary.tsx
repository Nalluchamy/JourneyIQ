import React, { useState } from 'react';
import { FileText, Download, RefreshCw, Eye } from 'lucide-react';
import { copilotApi } from '../services/api';

export const ExecutiveSummary: React.FC = () => {
  const [reportType, setReportType] = useState<'daily' | 'weekly' | 'monthly'>('weekly');
  const [reportFormat, setReportFormat] = useState<'markdown' | 'json' | 'pdf'>('markdown');
  const [loading, setLoading] = useState(false);
  const [reportPreview, setReportPreview] = useState<string>('');

  const handleGenerateReport = async () => {
    setLoading(true);
    try {
      const res = await copilotApi.getReport(reportType, reportFormat);
      if (reportFormat === 'json') {
        setReportPreview(JSON.stringify(res.report, null, 2));
      } else {
        setReportPreview(res.report);
      }
    } catch (err) {
      console.error(err);
      setReportPreview('Failed to generate report. Please check database connectivity.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = () => {
    if (!reportPreview) return;
    
    let filename = `journeyiq_${reportType}_report`;
    let mimeType = 'text/plain';
    let content = reportPreview;
    
    if (reportFormat === 'json') {
      filename += '.json';
      mimeType = 'application/json';
    } else if (reportFormat === 'pdf') {
      filename += '.html';
      mimeType = 'text/html';
    } else {
      filename += '.md';
      mimeType = 'text/markdown';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-[#111827] p-5 space-y-4">
      <div className="flex items-center gap-2">
        <span className="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/25">
          <FileText className="w-4 h-4" />
        </span>
        <h4 className="font-bold text-white text-sm">Executive Performance Reports</h4>
      </div>

      <div className="flex flex-wrap gap-3 items-center text-xs font-semibold">
        <div className="flex flex-col gap-1">
          <span className="text-[10px] text-slate-500 uppercase font-black">Type</span>
          <select 
            value={reportType}
            onChange={(e) => setReportType(e.target.value as any)}
            className="bg-slate-900 border border-slate-850 rounded px-2.5 py-1.5 text-white outline-none cursor-pointer"
          >
            <option value="daily">Daily Briefing</option>
            <option value="weekly">Weekly Report</option>
            <option value="monthly">Monthly Summary</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-[10px] text-slate-500 uppercase font-black">Format</span>
          <select 
            value={reportFormat}
            onChange={(e) => setReportFormat(e.target.value as any)}
            className="bg-slate-900 border border-slate-850 rounded px-2.5 py-1.5 text-white outline-none cursor-pointer"
          >
            <option value="markdown">Markdown</option>
            <option value="json">Structured JSON</option>
            <option value="pdf">HTML/PDF Print</option>
          </select>
        </div>

        <div className="flex gap-2 self-end mt-2 md:mt-0 ml-auto">
          <button
            onClick={handleGenerateReport}
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Eye className="w-3.5 h-3.5" />}
            Generate Report
          </button>

          {reportPreview && (
            <button
              onClick={handleDownloadReport}
              className="bg-slate-800 hover:bg-slate-850 text-slate-200 px-3.5 py-2 rounded-lg flex items-center gap-1.5 border border-slate-700 transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              Download
            </button>
          )}
        </div>
      </div>

      {reportPreview ? (
        <div className="rounded-lg border border-slate-850 bg-slate-950 p-4 max-h-[300px] overflow-y-auto font-mono text-[11px] leading-relaxed text-slate-300 border-l-2 border-l-indigo-500 whitespace-pre-wrap select-all">
          {reportPreview}
        </div>
      ) : (
        <div className="rounded-lg border border-slate-850 bg-slate-950 p-6 text-center text-xs text-slate-500 font-semibold border-dashed">
          No report preview generated yet. Click "Generate Report" above to compile data.
        </div>
      )}
    </div>
  );
};
