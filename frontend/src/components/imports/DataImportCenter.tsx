import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  Upload,
  Download,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowRight,
  RefreshCw,
  FileText
} from 'lucide-react';
import { api } from '../../api/client';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';

export const DataImportCenter: React.FC = () => {
  const [importType, setImportType] = useState<string>('students');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewResult, setPreviewResult] = useState<any | null>(null);
  const [importJobs, setImportJobs] = useState<any[]>([]);

  const [isPreviewing, setIsPreviewing] = useState<boolean>(false);
  const [isCommitting, setIsCommitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadJobs = async () => {
    try {
      const jobs = await api.getImportJobs();
      setImportJobs(jobs);
    } catch (err: any) {
      console.warn('Could not load import history', err);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setPreviewResult(null);
      setError(null);
      setSuccessMessage(null);
    }
  };

  const handlePreview = async () => {
    if (!selectedFile) return;
    setIsPreviewing(true);
    setError(null);
    try {
      const preview = await api.previewImport(selectedFile, importType);
      setPreviewResult(preview);
    } catch (err: any) {
      setError(err.message || 'Error processing preview');
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleExecuteImport = async () => {
    if (!selectedFile) return;
    setIsCommitting(true);
    setError(null);
    try {
      const job = await api.executeImport(selectedFile, importType);
      setSuccessMessage(
        `Batch ${job.filename} imported successfully! ${job.successful_rows} rows inserted, ${job.failed_rows} errors.`
      );
      setSelectedFile(null);
      setPreviewResult(null);
      await loadJobs();
    } catch (err: any) {
      setError(err.message || 'Error committing batch import');
    } finally {
      setIsCommitting(false);
    }
  };

  const handleDownloadTemplate = async (template: string) => {
    try {
      const blob = await api.downloadTemplate(template);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `template_${template}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(`Could not download template: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center">
            <FileSpreadsheet className="w-5 h-5 mr-2 text-brand-600" />
            Institutional Data Import Center
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Bulk ingest student rosters, semester examination results, and attendance counts via CSV or Excel with duplicate detection and preview checks.
          </p>
        </div>

        {/* Template Downloads */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500 font-semibold hidden md:inline">Download CSV Templates:</span>
          <button
            onClick={() => handleDownloadTemplate('students')}
            className="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 flex items-center shadow-sm"
          >
            <Download className="w-3.5 h-3.5 mr-1" /> Students
          </button>
          <button
            onClick={() => handleDownloadTemplate('academic_records')}
            className="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 flex items-center shadow-sm"
          >
            <Download className="w-3.5 h-3.5 mr-1" /> Marks
          </button>
          <button
            onClick={() => handleDownloadTemplate('attendance')}
            className="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 flex items-center shadow-sm"
          >
            <Download className="w-3.5 h-3.5 mr-1" /> Attendance
          </button>
        </div>
      </div>

      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="font-bold">&times;</button>
        </div>
      )}

      {error && <ErrorAlert message={error} />}

      {/* Upload & Configuration Card */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Data Entity Type *
            </label>
            <select
              value={importType}
              onChange={(e) => {
                setImportType(e.target.value);
                setPreviewResult(null);
              }}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="students">Student Cohort Profiles</option>
              <option value="academic_records">Semester Course Examination Results</option>
              <option value="attendance">Subject Attendance Counts (Attended / Total)</option>
            </select>
          </div>

          <div className="sm:col-span-2">
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Select CSV or Excel (.xlsx) Document *
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="file"
                accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                onChange={handleFileChange}
                className="w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100 dark:file:bg-brand-950 dark:file:text-brand-300 cursor-pointer"
              />
              <button
                type="button"
                disabled={!selectedFile || isPreviewing}
                onClick={handlePreview}
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs flex items-center shadow-sm disabled:opacity-50 whitespace-nowrap"
              >
                {isPreviewing ? <RefreshCw className="w-3.5 h-3.5 animate-spin mr-1.5" /> : <Upload className="w-3.5 h-3.5 mr-1.5" />}
                Validate & Preview
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Preview Section */}
      {previewResult && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center">
                <FileText className="w-4 h-4 mr-2 text-brand-600" />
                Import Preview: {previewResult.filename}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Columns Detected: <strong className="font-mono text-slate-700 dark:text-slate-300">{previewResult.columns_detected.join(', ')}</strong>
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2 text-xs">
                <Badge variant="success" size="sm">
                  {previewResult.valid_rows_count} Valid
                </Badge>
                {previewResult.invalid_rows_count > 0 && (
                  <Badge variant="danger" size="sm">
                    {previewResult.invalid_rows_count} Errors
                  </Badge>
                )}
              </div>

              <button
                onClick={handleExecuteImport}
                disabled={isCommitting || previewResult.valid_rows_count === 0}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center shadow-sm disabled:opacity-50"
              >
                {isCommitting ? 'Committing...' : 'Confirm & Commit Import'}
                <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
              </button>
            </div>
          </div>

          {/* Error Callouts if any */}
          {previewResult.errors && previewResult.errors.length > 0 && (
            <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-xs space-y-1">
              <div className="flex items-center text-rose-800 dark:text-rose-300 font-bold mb-1">
                <AlertTriangle className="w-4 h-4 mr-1.5 text-rose-600" />
                Row-Level Validation Errors Detected:
              </div>
              {previewResult.errors.map((err: any, idx: number) => (
                <div key={idx} className="text-rose-700 dark:text-rose-400 font-mono text-[11px]">
                  &bull; Row #{err.row_number}: {err.error_message}
                </div>
              ))}
            </div>
          )}

          {/* Sample Rows Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                  {previewResult.columns_detected.map((col: string) => (
                    <th key={col} className="pb-2 font-semibold capitalize">{col.replace('_', ' ')}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {previewResult.preview_rows.map((row: any, rIdx: number) => (
                  <tr key={rIdx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    {previewResult.columns_detected.map((col: string) => (
                      <td key={col} className="py-2 text-slate-700 dark:text-slate-300 font-mono text-[11px]">
                        {row[col] !== undefined ? String(row[col]) : '-'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Historical Import Jobs */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center">
            <Clock className="w-4 h-4 mr-2 text-brand-600" />
            Batch Import History & Audit Log
          </h3>
          <button
            onClick={loadJobs}
            className="p-1 rounded-lg text-slate-400 hover:text-brand-600"
            title="Refresh history"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                <th className="pb-2 font-semibold">Job ID</th>
                <th className="pb-2 font-semibold">File Name</th>
                <th className="pb-2 font-semibold">Entity Type</th>
                <th className="pb-2 font-semibold text-center">Successful</th>
                <th className="pb-2 font-semibold text-center">Failed</th>
                <th className="pb-2 font-semibold text-center">Status</th>
                <th className="pb-2 font-semibold text-right">Date & Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {importJobs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-400 italic">
                    No batch imports executed yet.
                  </td>
                </tr>
              ) : (
                importJobs.map((job) => (
                  <tr key={job.id}>
                    <td className="py-2.5 font-mono text-slate-400">#{job.id}</td>
                    <td className="py-2.5 font-medium text-slate-900 dark:text-slate-100">{job.filename}</td>
                    <td className="py-2.5 text-brand-600 capitalize">{job.import_type.replace('_', ' ')}</td>
                    <td className="py-2.5 text-center font-bold text-emerald-600">{job.successful_rows}</td>
                    <td className="py-2.5 text-center font-bold text-rose-600">{job.failed_rows}</td>
                    <td className="py-2.5 text-center">
                      <Badge
                        variant={job.status === 'completed' ? 'success' : job.status === 'partially_completed' ? 'warning' : 'danger'}
                        size="sm"
                      >
                        {job.status}
                      </Badge>
                    </td>
                    <td className="py-2.5 text-right text-slate-400">{new Date(job.created_at).toLocaleString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
