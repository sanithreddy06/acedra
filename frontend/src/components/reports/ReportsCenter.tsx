import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  PlusCircle,
  FileSpreadsheet,
  Calendar,
  CheckCircle2,
  Clock,
  Building2,
  Layers,
  ArrowDownToLine,
  Filter
} from 'lucide-react';
import { api } from '../../api/client';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';

export const ReportsCenter: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedType, setSelectedType] = useState<string>('STUDENT_PROGRESS');
  const [fileFormat, setFileFormat] = useState<string>('CSV');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadReports = async () => {
    setIsLoading(true);
    try {
      const res = await api.getInstitutionalReports();
      setReports(res || []);
    } catch {
      setReports([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    setSuccessMessage(null);
    try {
      const newReport = await api.exportInstitutionalReport({
        report_type: selectedType,
        file_format: fileFormat,
      });
      setSuccessMessage(`Report '${newReport.file_name}' generated successfully.`);
      await loadReports();
    } catch (err: any) {
      alert(err.message || 'Failed to generate report export');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = (reportId: number) => {
    const url = api.getReportDownloadUrl(reportId);
    window.open(url, '_blank');
  };

  const reportDescriptions: Record<string, string> = {
    STUDENT_PROGRESS: 'Comprehensive student dossier: USN, SRN, semester SGPA, CGPA, verified attendance, and backlogs.',
    MENTOR_INTERVENTIONS: 'Mentorship action plans, scheduled counseling sessions, and completed case resolution summaries.',
    DEPARTMENT_SUMMARY: 'Faculty cohort breakdown, average department CGPA, attendance averages, and overall backlogs count.',
    RISK_SUMMARY: 'Early-warning indicators, detected academic/attendance thresholds, severity distribution, and active alerts.',
    PLACEMENT_READINESS: 'Placement cohort benchmarks, student readiness scores, applications pipeline, and hiring statistics.',
  };

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-brand-900 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <FileSpreadsheet className="w-6 h-6 text-emerald-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-brand-200">
              Module 6 &bull; Institutional Intelligence & Compliance Center
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight mt-1">
            Data Export & Governance Reports
          </h1>
          <p className="text-xs text-brand-100 max-w-2xl mt-1">
            Generate and download certified institutional audit datasets, academic performance distributions, and mentor intervention audits for compliance and accreditation.
          </p>
        </div>
      </div>

      {/* Report Generator Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
          <PlusCircle className="w-4 h-4 text-brand-600" />
          <span>Generate New Compliance Dataset / Audit Report</span>
        </h2>

        {successMessage && (
          <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-2xl text-xs text-emerald-800 dark:text-emerald-300 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{successMessage}</span>
          </div>
        )}

        <form onSubmit={handleGenerate} className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block text-slate-500 mb-1 font-medium">Select Intelligence Report Type</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs font-medium text-slate-900 dark:text-slate-100"
            >
              <option value="STUDENT_PROGRESS">Student Academic Progress Dossier</option>
              <option value="MENTOR_INTERVENTIONS">Mentor Interventions & Support Audit</option>
              <option value="DEPARTMENT_SUMMARY">Institutional Department Performance</option>
              <option value="RISK_SUMMARY">Early-Warning Academic Risk Distribution</option>
              <option value="PLACEMENT_READINESS">Placement Readiness & Career Benchmarks</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-500 mb-1 font-medium">Export File Format</label>
            <select
              value={fileFormat}
              onChange={(e) => setFileFormat(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs font-medium text-slate-900 dark:text-slate-100"
            >
              <option value="CSV">CSV (Spreadsheet / Excel Compatible)</option>
              <option value="JSON">JSON (Machine-Readable Payload)</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={isGenerating}
              className="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-xl text-xs flex items-center justify-center space-x-2 shadow-sm transition disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              <span>{isGenerating ? 'Compiling Dataset...' : 'Generate & Export Report'}</span>
            </button>
          </div>
        </form>

        <p className="text-xs text-slate-500 dark:text-slate-400 italic bg-slate-50 dark:bg-slate-800/40 p-3 rounded-2xl border border-slate-100 dark:border-slate-800">
          <strong>Report Scope:</strong> {reportDescriptions[selectedType]}
        </p>
      </div>

      {/* Generated Reports History Table */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
            <Clock className="w-4 h-4 text-brand-600" />
            <span>Generated Export Archives ({reports.length})</span>
          </h2>
          <span className="text-xs text-slate-400">Institutional records retained for governance</span>
        </div>

        {isLoading ? (
          <LoadingSpinner label="Fetching reports archive..." />
        ) : reports.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">No reports generated yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-3">Report Title & Type</th>
                  <th className="py-3 px-3">File Name</th>
                  <th className="py-3 px-3">Generated By</th>
                  <th className="py-3 px-3">Size</th>
                  <th className="py-3 px-3">Timestamp</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {reports.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
                    <td className="py-3 px-3 font-semibold text-slate-800 dark:text-slate-100">
                      <div>{r.title}</div>
                      <Badge variant="brand" size="sm">
                        {r.report_type}
                      </Badge>
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-500">{r.file_name}</td>
                    <td className="py-3 px-3 text-slate-600 dark:text-slate-300">{r.generated_by_name || 'System Admin'}</td>
                    <td className="py-3 px-3 text-slate-500 font-mono text-[11px]">
                      {r.file_size_bytes > 1024 ? `${(r.file_size_bytes / 1024).toFixed(1)} KB` : `${r.file_size_bytes} B`}
                    </td>
                    <td className="py-3 px-3 text-slate-400">
                      {new Date(r.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => handleDownload(r.id)}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-brand-50 hover:bg-brand-100 text-brand-700 dark:bg-brand-950/60 dark:hover:bg-brand-900 dark:text-brand-300 font-semibold text-xs transition"
                      >
                        <ArrowDownToLine className="w-3.5 h-3.5 mr-1" />
                        <span>Download</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
