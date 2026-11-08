import React, { useState, useEffect } from 'react';
import {
  FileText,
  UploadCloud,
  Search,
  RefreshCw,
  Trash2,
  Eye,
  CheckCircle2,
  Shield,
  Layers,
  Sparkles,
  Database,
  Plus,
  AlertTriangle,
  Info,
  Clock,
  ExternalLink
} from 'lucide-react';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';

export const RAGDocumentManager: React.FC = () => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Upload modal state
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState<string>('');
  const [uploadCategory, setUploadCategory] = useState<string>('ACADEMIC_REGULATIONS');
  const [uploadPermission, setUploadPermission] = useState<string>('PUBLIC');
  const [uploadDescription, setUploadDescription] = useState<string>('');
  const [isUploading, setIsUploading] = useState<boolean>(false);

  // View chunks modal state
  const [selectedDocDetails, setSelectedDocDetails] = useState<any | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);

  // Semantic test search state
  const [testSearchQuery, setTestSearchQuery] = useState<string>('');
  const [testSearchResults, setTestSearchResults] = useState<any | null>(null);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const data = await api.getRAGDocuments(selectedCategory || undefined, searchQuery || undefined);
      setDocuments(data);
    } catch (err) {
      console.error('Failed to load documents', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [selectedCategory]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadTitle.trim()) {
      alert('Please specify a title and select a valid document file.');
      return;
    }

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('title', uploadTitle);
    formData.append('category', uploadCategory);
    formData.append('access_permission', uploadPermission);
    if (uploadDescription) formData.append('description', uploadDescription);

    setIsUploading(true);
    try {
      await api.uploadRAGDocument(formData);
      setIsUploadOpen(false);
      setUploadFile(null);
      setUploadTitle('');
      setUploadDescription('');
      loadDocuments();
    } catch (err: any) {
      alert(err.message || 'Document upload and indexing failed.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleViewChunks = async (docId: number) => {
    setIsDetailLoading(true);
    try {
      const details = await api.getDocumentDetails(docId);
      setSelectedDocDetails(details);
    } catch (err: any) {
      alert(err.message || 'Failed to fetch chunks');
    } finally {
      setIsDetailLoading(false);
    }
  };

  const handleReindex = async (docId: number) => {
    try {
      await api.reindexRAGDocument(docId);
      alert('Document re-indexed successfully with refreshed vector embeddings.');
      loadDocuments();
    } catch (err: any) {
      alert(err.message || 'Re-indexing failed');
    }
  };

  const handleDelete = async (docId: number) => {
    if (!window.confirm('Delete this document and all its indexed vector chunks from RAG?')) return;
    try {
      await api.deleteRAGDocument(docId);
      setDocuments(prev => prev.filter(d => d.id !== docId));
    } catch (err: any) {
      alert(err.message || 'Delete failed');
    }
  };

  const handleTestSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testSearchQuery.trim()) return;
    setIsSearching(true);
    try {
      const res = await api.searchRAG(testSearchQuery);
      setTestSearchResults(res);
    } catch (err: any) {
      alert(err.message || 'Semantic search failed');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Top Banner */}
      <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-tr from-purple-600 to-indigo-600 rounded-xl text-white shadow-md shadow-indigo-500/20">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                RAG Knowledge Base & Document Management
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300">
                  pgvector & Semantic Search
                </span>
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Manage official institutional handbooks, PDF/DOCX ingestion, text chunking, and similarity vector retrieval
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => setIsUploadOpen(true)}
          className="px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition flex items-center gap-2 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          Upload & Index Document
        </button>
      </div>

      {/* Semantic Search Interactive Tester */}
      <div className="p-5 bg-gradient-to-r from-purple-50/50 to-indigo-50/50 dark:from-slate-900 dark:to-slate-900/60 rounded-2xl border border-purple-200/60 dark:border-purple-950/60 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-purple-900 dark:text-purple-300 uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-purple-600" />
            Live Vector Retrieval Tester
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            Cosine Similarity & Lexical Grounding
          </span>
        </div>

        <form onSubmit={handleTestSearch} className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={testSearchQuery}
              onChange={(e) => setTestSearchQuery(e.target.value)}
              placeholder="Test query: e.g., 'attendance condonation threshold' or 'passing criteria in CIA'..."
              className="w-full pl-10 pr-4 py-2.5 text-xs rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <button
            type="submit"
            disabled={!testSearchQuery.trim() || isSearching}
            className="px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold disabled:opacity-40 transition shrink-0"
          >
            {isSearching ? 'Scoring...' : 'Test Retrieval'}
          </button>
        </form>

        {testSearchResults && (
          <div className="mt-3 p-3.5 bg-white dark:bg-slate-900 rounded-xl border border-purple-100 dark:border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800 dark:text-slate-200">
                Found {testSearchResults.results_count} Relevant Passage{testSearchResults.results_count !== 1 ? 's' : ''}
              </span>
              <button
                onClick={() => setTestSearchResults(null)}
                className="text-slate-400 hover:text-slate-600 text-[11px]"
              >
                Clear
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {testSearchResults.results.map((r: any, idx: number) => (
                <div key={idx} className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-purple-600 dark:text-purple-400 truncate max-w-[200px]">
                      {r.document_title}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 font-bold">
                      {Math.round(r.score * 100)}% Match
                    </span>
                  </div>
                  <h6 className="text-[11px] font-semibold text-slate-800 dark:text-slate-200">
                    {r.chunk.section_heading} (Page {r.chunk.page_number || 1})
                  </h6>
                  <p className="text-[10px] text-slate-600 dark:text-slate-400 line-clamp-3 font-mono">
                    {r.chunk.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">All Knowledge Categories</option>
            <option value="ACADEMIC_REGULATIONS">Academic Regulations</option>
            <option value="ATTENDANCE_GUIDELINES">Attendance Guidelines</option>
            <option value="EXAMINATION_GUIDELINES">Examination Guidelines</option>
            <option value="INTERNSHIP_GUIDELINES">Internship Guidelines</option>
            <option value="PLACEMENT_GUIDELINES">Placement Guidelines</option>
            <option value="CAMPUS_HANDBOOK">Campus Handbook</option>
            <option value="GENERAL_POLICY">General Policy</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadDocuments()}
            placeholder="Filter document title..."
            className="px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <button
            onClick={loadDocuments}
            className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-600 dark:text-slate-300"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Document Title & Description</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">File Type</th>
                <th className="py-3 px-4">Chunks</th>
                <th className="py-3 px-4">Permission</th>
                <th className="py-3 px-4">Indexed At</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-400 text-xs">
                    No documents found matching filters.
                  </td>
                </tr>
              ) : (
                documents.map(doc => (
                  <tr key={doc.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-950 text-purple-600 shrink-0">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="font-bold text-slate-900 dark:text-white">{doc.title}</p>
                          <p className="text-[10px] text-slate-400 truncate max-w-xs">{doc.description || doc.file_name}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {doc.category?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono uppercase text-[10px] text-slate-500">
                      {doc.file_type} &bull; {Math.round(doc.file_size_bytes / 1024)} KB
                    </td>
                    <td className="py-3 px-4 font-bold font-mono text-purple-600 dark:text-purple-400">
                      {doc.chunk_count} chunks
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        doc.access_permission === 'PUBLIC'
                          ? 'bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
                          : 'bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300'
                      }`}>
                        {doc.access_permission}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[10px]">
                      {doc.indexed_at ? new Date(doc.indexed_at).toLocaleDateString() : 'Pending'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleViewChunks(doc.id)}
                          className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-purple-600 transition"
                          title="View Vector Chunks"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleReindex(doc.id)}
                          className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-blue-600 transition"
                          title="Re-index Chunks"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-rose-600 transition"
                          title="Delete Document"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 max-w-md w-full space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <UploadCloud className="w-5 h-5 text-purple-600" />
                Upload Knowledge Document
              </h3>
              <button
                onClick={() => setIsUploadOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleUpload} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Document Title
                </label>
                <input
                  type="text"
                  required
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="e.g., REVA Academic Regulations 2026"
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Knowledge Category
                </label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="ACADEMIC_REGULATIONS">Academic Regulations</option>
                  <option value="ATTENDANCE_GUIDELINES">Attendance Guidelines</option>
                  <option value="EXAMINATION_GUIDELINES">Examination Guidelines</option>
                  <option value="INTERNSHIP_GUIDELINES">Internship Guidelines</option>
                  <option value="PLACEMENT_GUIDELINES">Placement Guidelines</option>
                  <option value="CAMPUS_HANDBOOK">Campus Handbook</option>
                  <option value="GENERAL_POLICY">General Policy</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Access Permission Tier
                </label>
                <select
                  value={uploadPermission}
                  onChange={(e) => setUploadPermission(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="PUBLIC">Public (Accessible without login)</option>
                  <option value="AUTHENTICATED_STUDENT">Authenticated Students & Faculty</option>
                  <option value="FACULTY_ONLY">Faculty & Staff Only</option>
                  <option value="ADMIN_ONLY">Administrative Only</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Attach Document (PDF, DOCX, TXT, MD)
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.docx,.doc,.txt,.md"
                  onChange={(e) => e.target.files && setUploadFile(e.target.files[0])}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Brief Description (Optional)
                </label>
                <textarea
                  rows={2}
                  value={uploadDescription}
                  onChange={(e) => setUploadDescription(e.target.value)}
                  placeholder="Summary of document purpose..."
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsUploadOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUploading}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-40 shadow-sm"
                >
                  {isUploading ? 'Extracting & Indexing...' : 'Upload & Generate Embeddings'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Chunks Modal */}
      {selectedDocDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 max-w-2xl w-full space-y-4 shadow-xl max-h-[85vh] flex flex-col">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-purple-600 dark:text-purple-400">
                  {selectedDocDetails.category}
                </span>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
                  {selectedDocDetails.title}
                </h3>
                <p className="text-xs text-slate-400">
                  {selectedDocDetails.chunk_count} Chunks &bull; Dense 128D Embeddings &bull; Access: {selectedDocDetails.access_permission}
                </p>
              </div>
              <button
                onClick={() => setSelectedDocDetails(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                &times;
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {selectedDocDetails.chunks?.map((chunk: any) => (
                <div key={chunk.id} className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900 dark:text-white">
                      Chunk #{chunk.chunk_index + 1}: {chunk.section_heading}
                    </span>
                    <span className="text-[10px] font-mono text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950 px-2 py-0.5 rounded">
                      Page {chunk.page_number || 1} &bull; {chunk.token_count} words
                    </span>
                  </div>
                  <p className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
                    {chunk.content}
                  </p>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedDocDetails(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-xs font-semibold text-slate-700 dark:text-slate-300 transition"
              >
                Close Chunk Viewer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
