import React, { useEffect, useState } from 'react';
import {
  ArrowPathIcon,
  ArrowUpTrayIcon,
  CheckCircleIcon,
  CircleStackIcon,
  ClipboardDocumentListIcon,
  DocumentPlusIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  PaperClipIcon,
  PlayIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import apiService from '../services/api';
import { EmptyState, ErrorState, LoadingState } from '../components/AdminState';
import { useAuth } from '../contexts/AuthContext';

const DOCUMENT_STATUSES = [
  'draft',
  'awaiting_validation',
  'processing',
  'indexed',
  'approved',
  'active',
  'failed',
  'archived',
  'superseded',
];

const CONTENT_TYPES = ['txt', 'markdown', 'pdf', 'structured'];

const SUGGESTED_SCOPE_OPTIONS = [
  'rogerian_theory',
  'approved_psychoeducation',
  'therapeutic_chat',
  'session_generation',
  'safety',
  'coping_strategies',
  'onboarding',
  'clinical_guidelines',
];

const REVIEW_POLICY_OPTIONS = [
  { value: '', label: 'No explicit review policy' },
  { value: 'standard_admin_review', label: 'Standard admin review' },
  { value: 'clinical_review_required', label: 'Clinical review required' },
  { value: 'source_verification_required', label: 'Source verification required' },
  { value: 'legal_review_required', label: 'Legal review required' },
  { value: 'copyright_review_required', label: 'Copyright review required' },
];

const initialCreateForm = {
  title: '',
  source: 'manual',
  source_uri: '',
  content_type: 'txt',
  language: 'en',
  tags: '',
  scopes: '',
  review_policy: '',
  created_by: '',
  // content ingestion fields (used when tab !== 'metadata')
  content: '',
  section: '',
};

const initialIngestForm = {
  content: '',
  content_type: 'txt',
  section: '',
  ingested_by: '',
};

const initialStatusForm = {
  status: 'draft',
  updated_by: '',
  reason: '',
};

const initialRetrievalForm = {
  query: '',
  chat_id: '',
  prompt_key: '',
  prompt_version: '',
  allowed_scopes: '',
  language: 'en',
  top_k: 6,
  trace_id: '',
};

function parseCommaSeparated(value) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function toggleCommaSeparatedValue(currentValue, nextValue) {
  const currentItems = parseCommaSeparated(currentValue);
  const hasValue = currentItems.includes(nextValue);
  const nextItems = hasValue
    ? currentItems.filter((item) => item !== nextValue)
    : [...currentItems, nextValue];

  return nextItems.join(', ');
}

function formatDate(value) {
  if (!value) return 'Unavailable';
  return new Date(value).toLocaleString('en-US');
}

function getStatusTone(status) {
  const tones = {
    draft: 'bg-slate-100 text-slate-700 ring-slate-200',
    awaiting_validation: 'bg-amber-100 text-amber-800 ring-amber-200',
    processing: 'bg-sky-100 text-sky-700 ring-sky-200',
    indexed: 'bg-indigo-100 text-indigo-700 ring-indigo-200',
    approved: 'bg-emerald-100 text-emerald-700 ring-emerald-200',
    active: 'bg-green-100 text-green-700 ring-green-200',
    failed: 'bg-rose-100 text-rose-700 ring-rose-200',
    archived: 'bg-zinc-100 text-zinc-700 ring-zinc-200',
    superseded: 'bg-orange-100 text-orange-700 ring-orange-200',
  };

  return tones[status] || 'bg-gray-100 text-gray-700 ring-gray-200';
}

function StatCard({ title, value, subtitle, icon: Icon, tone }) {
  const toneClasses = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    amber: 'bg-amber-50 text-amber-700',
    slate: 'bg-slate-100 text-slate-700',
  };

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{value}</p>
          <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
        </div>
        <div className={`flex h-11 w-11 items-center justify-center rounded-lg ${toneClasses[tone] || toneClasses.blue}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

function SectionHeader({ title, description, action }) {
  return (
    <div className="flex flex-col gap-3 border-b border-gray-200 pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        <p className="mt-1 text-sm text-gray-500">{description}</p>
      </div>
      {action}
    </div>
  );
}

function SuggestionToggleGroup({ label, options, value, onToggle, helperText }) {
  const selected = parseCommaSeparated(value);

  return (
    <div className="space-y-3">
      <div>
        <span className="block text-sm font-medium text-gray-700">{label}</span>
        {helperText ? <p className="mt-1 text-xs text-gray-500">{helperText}</p> : null}
      </div>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const active = selected.includes(option);
          return (
            <button
              key={option}
              type="button"
              onClick={() => onToggle(option)}
              className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${active
                ? 'border-sky-300 bg-sky-50 text-sky-700'
                : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50'
                }`}
            >
              {option}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Tab pill component for the create form ───────────────────────────────────
function CreateTab({ id, label, icon: Icon, active, onClick }) {
  return (
    <button
      type="button"
      onClick={() => onClick(id)}
      className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${active
        ? 'bg-slate-950 text-white shadow-sm'
        : 'border border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50'
        }`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}

export default function KnowledgeBase() {
  const { user } = useAuth();
  const actorName = user?.email || user?.name || 'admin';

  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState('');
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [auditEvents, setAuditEvents] = useState([]);
  const [retrievalResponse, setRetrievalResponse] = useState(null);
  const [lastUploadResult, setLastUploadResult] = useState(null);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [auditLoading, setAuditLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [scopeFilter, setScopeFilter] = useState('');

  // "Add document" tab: 'upload' | 'text' | 'metadata'
  const [createTab, setCreateTab] = useState('upload');
  const [selectedCreateFile, setSelectedCreateFile] = useState(null);
  const [isDragActiveCreate, setIsDragActiveCreate] = useState(false);

  // "Add more content" upload state (for existing documents)
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const [createForm, setCreateForm] = useState(() => ({ ...initialCreateForm, created_by: actorName }));
  const [ingestForm, setIngestForm] = useState(() => ({ ...initialIngestForm, ingested_by: actorName }));
  const [statusForm, setStatusForm] = useState(() => ({ ...initialStatusForm, updated_by: actorName }));
  const [retrievalForm, setRetrievalForm] = useState(initialRetrievalForm);
  const [submitting, setSubmitting] = useState({
    create: false,
    ingest: false,
    status: false,
    retrieve: false,
  });

  useEffect(() => {
    setCreateForm((current) => ({ ...current, created_by: current.created_by || actorName }));
    setIngestForm((current) => ({ ...current, ingested_by: current.ingested_by || actorName }));
    setStatusForm((current) => ({ ...current, updated_by: current.updated_by || actorName }));
  }, [actorName]);

  useEffect(() => {
    loadDocuments();
    loadAuditEvents();
  }, [statusFilter, scopeFilter]);

  useEffect(() => {
    if (!selectedDocumentId) {
      setSelectedDocument(null);
      setChunks([]);
      setSelectedFile(null);
      setLastUploadResult(null);
      return;
    }

    loadDocumentDetails(selectedDocumentId);
  }, [selectedDocumentId]);

  async function loadDocuments(preferredDocumentId) {
    try {
      setDocumentsLoading(true);
      setError(null);
      const response = await apiService.getKnowledgeDocuments({
        status: statusFilter || undefined,
        scope: scopeFilter || undefined,
      });
      const nextDocuments = response?.data?.documents || [];
      setDocuments(nextDocuments);

      const nextSelectedId = preferredDocumentId || selectedDocumentId;
      if (nextDocuments.length === 0) {
        setSelectedDocumentId('');
        return;
      }

      if (nextSelectedId && nextDocuments.some((document) => document.document_id === nextSelectedId)) {
        setSelectedDocumentId(nextSelectedId);
        return;
      }

      setSelectedDocumentId(nextDocuments[0].document_id);
    } catch (requestError) {
      setError(apiService.formatError(requestError, 'Failed to load knowledge documents.'));
      setDocuments([]);
      setSelectedDocumentId('');
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function loadDocumentDetails(documentId) {
    try {
      setDetailsLoading(true);
      const [documentResponse, chunksResponse] = await Promise.all([
        apiService.getKnowledgeDocument(documentId),
        apiService.getKnowledgeDocumentChunks(documentId),
      ]);

      const documentData = documentResponse?.data || null;
      const chunkData = chunksResponse?.data?.chunks || [];

      setSelectedDocument(documentData);
      setChunks(chunkData);
      setStatusForm((current) => ({
        ...current,
        status: documentData?.status || current.status,
        updated_by: current.updated_by || actorName,
      }));
      setRetrievalForm((current) => ({
        ...current,
        allowed_scopes: documentData?.scopes?.join(', ') || current.allowed_scopes,
      }));
    } catch (requestError) {
      setError(apiService.formatError(requestError, 'Failed to load document details.'));
      setSelectedDocument(null);
      setChunks([]);
    } finally {
      setDetailsLoading(false);
    }
  }

  async function loadAuditEvents() {
    try {
      setAuditLoading(true);
      const response = await apiService.getKnowledgeAuditEvents();
      setAuditEvents(response?.data?.events || []);
    } catch (requestError) {
      setError(apiService.formatError(requestError, 'Failed to load audit events.'));
      setAuditEvents([]);
    } finally {
      setAuditLoading(false);
    }
  }

  async function refreshKnowledgeWorkspace(documentId) {
    await Promise.all([
      loadDocuments(documentId || selectedDocumentId),
      loadAuditEvents(),
    ]);
  }

  /**
   * Unified "Add document" handler.
   * Step 1: always registers the document record.
   * Step 2: optionally chains ingest based on the active tab.
   *   - 'upload' → uploads the selected file
   *   - 'text'   → ingests the pasted content
   *   - 'metadata' → no content ingestion; document stays in draft
   */
  async function handleCreateAndIngest(event) {
    event.preventDefault();
    try {
      setSubmitting((current) => ({ ...current, create: true }));
      setError(null);

      // ── Step 1: register the document record ──
      const createResponse = await apiService.createKnowledgeDocument({
        title: createForm.title.trim(),
        source: createForm.source.trim(),
        source_uri: createForm.source_uri.trim() || null,
        content_type: createForm.content_type,
        language: createForm.language.trim() || 'en',
        tags: parseCommaSeparated(createForm.tags),
        scopes: parseCommaSeparated(createForm.scopes),
        review_policy: createForm.review_policy.trim() || null,
        created_by: createForm.created_by.trim() || actorName,
      });

      const createdDocumentId = createResponse?.data?.document_id;

      // ── Step 2: chain content ingestion when the tab supplies content ──
      if (createdDocumentId && createTab === 'upload' && selectedCreateFile) {
        const uploadResponse = await apiService.uploadKnowledgeDocumentFile(createdDocumentId, {
          file: selectedCreateFile,
          section: createForm.section.trim() || null,
          ingested_by: createForm.created_by.trim() || actorName,
        });
        setLastUploadResult(uploadResponse?.data?.upload || null);
      } else if (createdDocumentId && createTab === 'text' && createForm.content.trim()) {
        await apiService.ingestKnowledgeDocumentContent(createdDocumentId, {
          content: createForm.content,
          content_type: createForm.content_type,
          section: createForm.section.trim() || null,
          ingested_by: createForm.created_by.trim() || actorName,
        });
      }

      setCreateForm({ ...initialCreateForm, created_by: actorName });
      setSelectedCreateFile(null);
      await refreshKnowledgeWorkspace(createdDocumentId);
    } catch (requestError) {
      setError(apiService.formatError(requestError, 'Failed to create the document.'));
    } finally {
      setSubmitting((current) => ({ ...current, create: false }));
    }
  }

  // ── "Add more content" handlers (for existing selected document) ──────────

  async function handleIngestContent(event) {
    event.preventDefault();
    if (!selectedDocumentId) return;

    try {
      setSubmitting((current) => ({ ...current, ingest: true }));
      setError(null);

      await apiService.ingestKnowledgeDocumentContent(selectedDocumentId, {
        content: ingestForm.content,
        content_type: ingestForm.content_type,
        section: ingestForm.section.trim() || null,
        ingested_by: ingestForm.ingested_by.trim() || actorName,
      });

      setIngestForm({ ...initialIngestForm, ingested_by: actorName });
      setLastUploadResult(null);
      await Promise.all([
        refreshKnowledgeWorkspace(selectedDocumentId),
        loadDocumentDetails(selectedDocumentId),
      ]);
    } catch (requestError) {
      setError(apiService.formatError(requestError, 'Failed to ingest document content.'));
    } finally {
      setSubmitting((current) => ({ ...current, ingest: false }));
    }
  }

  async function handleUploadFile(event) {
    event.preventDefault();
    if (!selectedDocumentId || !selectedFile) return;

    try {
      setSubmitting((current) => ({ ...current, ingest: true }));
      setError(null);

      const response = await apiService.uploadKnowledgeDocumentFile(selectedDocumentId, {
        file: selectedFile,
        section: ingestForm.section.trim() || null,
        ingested_by: ingestForm.ingested_by.trim() || actorName,
      });

      setLastUploadResult(response?.data?.upload || null);
      setSelectedFile(null);
      setIngestForm((current) => ({
        ...current,
        content: '',
        content_type: 'txt',
      }));
      await Promise.all([
        refreshKnowledgeWorkspace(selectedDocumentId),
        loadDocumentDetails(selectedDocumentId),
      ]);
    } catch (requestError) {
      setError(apiService.formatError(requestError, 'Failed to upload and ingest the file.'));
      setLastUploadResult(null);
    } finally {
      setSubmitting((current) => ({ ...current, ingest: false }));
      setIsDragActive(false);
    }
  }

  function handleFileSelection(file) {
    if (!file) return;
    setSelectedFile(file);
    setLastUploadResult(null);
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragActive(false);
    const file = event.dataTransfer.files?.[0];
    handleFileSelection(file);
  }

  async function handleStatusUpdate(event) {
    event.preventDefault();
    if (!selectedDocumentId) return;

    try {
      setSubmitting((current) => ({ ...current, status: true }));
      setError(null);

      await apiService.updateKnowledgeDocumentStatus(selectedDocumentId, {
        status: statusForm.status,
        updated_by: statusForm.updated_by.trim() || actorName,
        reason: statusForm.reason.trim() || null,
      });

      setStatusForm((current) => ({ ...current, reason: '' }));
      await Promise.all([
        refreshKnowledgeWorkspace(selectedDocumentId),
        loadDocumentDetails(selectedDocumentId),
      ]);
    } catch (requestError) {
      setError(apiService.formatError(requestError, 'Failed to update document status.'));
    } finally {
      setSubmitting((current) => ({ ...current, status: false }));
    }
  }

  async function handleRetrieve(event) {
    event.preventDefault();
    try {
      setSubmitting((current) => ({ ...current, retrieve: true }));
      setError(null);

      const response = await apiService.retrieveKnowledge({
        query: retrievalForm.query.trim(),
        chat_id: retrievalForm.chat_id.trim() || null,
        prompt_key: retrievalForm.prompt_key.trim() || null,
        prompt_version: retrievalForm.prompt_version ? Number(retrievalForm.prompt_version) : null,
        allowed_scopes: parseCommaSeparated(retrievalForm.allowed_scopes),
        language: retrievalForm.language.trim() || null,
        top_k: Number(retrievalForm.top_k) || 6,
        trace_id: retrievalForm.trace_id.trim() || null,
      });

      setRetrievalResponse(response);
      await loadAuditEvents();
    } catch (requestError) {
      setError(apiService.formatError(requestError, 'Failed to execute retrieval.'));
      setRetrievalResponse(null);
    } finally {
      setSubmitting((current) => ({ ...current, retrieve: false }));
    }
  }

  const filteredDocuments = documents.filter((document) => {
    if (!searchTerm.trim()) return true;

    const haystack = [
      document.title,
      document.document_id,
      document.source,
      ...(document.tags || []),
      ...(document.scopes || []),
    ]
      .join(' ')
      .toLowerCase();

    return haystack.includes(searchTerm.trim().toLowerCase());
  });

  const scopeOptions = Array.from(
    new Set(
      documents.flatMap((document) => document.scopes || [])
    )
  ).sort();

  const totalChunks = documents.reduce((sum, document) => sum + (document.chunk_count || 0), 0);
  const activeDocuments = documents.filter((document) => document.status === 'active').length;
  const indexedDocuments = documents.filter((document) => ['indexed', 'approved', 'active'].includes(document.status)).length;
  const selectedDocumentEvents = selectedDocument
    ? auditEvents.filter((event) => event.document_id === selectedDocument.document_id)
    : [];

  if (documentsLoading && documents.length === 0 && !error) {
    return <LoadingState message="Loading Knowledge workspace..." />;
  }

  return (
    <div className="space-y-8">
      {/* ── Page header ─────────────────────────────────────────────────────── */}
      <div className="rounded-2xl border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#eef4ff_52%,#ecfeff_100%)] p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-sky-700">Knowledge Admin</p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-950">Knowledge Base</h1>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Add documents (register metadata and attach content in one step), manage the document lifecycle,
              inspect chunks, review the audit trail, and test retrieval — all in one workspace.
            </p>
          </div>
          <button
            type="button"
            onClick={() => refreshKnowledgeWorkspace()}
            className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
          >
            <ArrowPathIcon className="mr-2 h-4 w-4" />
            Refresh workspace
          </button>
        </div>
      </div>

      {error && <ErrorState message={error} onRetry={() => refreshKnowledgeWorkspace()} />}

      {/* ── Stats row ───────────────────────────────────────────────────────── */}
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Documents"
          value={documents.length}
          subtitle="Registered in the current filtered view"
          icon={ClipboardDocumentListIcon}
          tone="blue"
        />
        <StatCard
          title="Active"
          value={activeDocuments}
          subtitle="Ready for prompt-controlled retrieval"
          icon={CheckCircleIcon}
          tone="green"
        />
        <StatCard
          title="Indexed"
          value={indexedDocuments}
          subtitle="Chunked and ready for downstream indexing"
          icon={SparklesIcon}
          tone="amber"
        />
        <StatCard
          title="Chunks"
          value={totalChunks}
          subtitle="Generated semantic chunks"
          icon={CircleStackIcon}
          tone="slate"
        />
      </div>

      {/* ── Main workspace grid ─────────────────────────────────────────────── */}
      <div className="grid gap-8 xl:grid-cols-[1fr_1.5fr]">

        {/* LEFT column ─────────────────────────────────────────────────────── */}
        <div className="space-y-8">

          {/* ── Add document (unified register + optional ingest) ─────────── */}
          <section className="card space-y-6 p-6">
            <SectionHeader
              title="Add document"
              description="Register metadata and optionally attach content in one step."
            />

            {/* Tab switcher */}
            <div className="flex flex-wrap gap-2">
              <CreateTab
                id="upload"
                label="Upload file"
                icon={ArrowUpTrayIcon}
                active={createTab === 'upload'}
                onClick={setCreateTab}
              />
              <CreateTab
                id="text"
                label="Paste text"
                icon={DocumentTextIcon}
                active={createTab === 'text'}
                onClick={setCreateTab}
              />
              <CreateTab
                id="metadata"
                label="Metadata only"
                icon={PaperClipIcon}
                active={createTab === 'metadata'}
                onClick={setCreateTab}
              />
            </div>

            {/* Tab hint */}
            <p className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
              {createTab === 'upload' && (
                <>
                  <span className="font-medium text-slate-800">Upload file:</span>{' '}
                  Upload a PDF, TXT, or Markdown file. The service extracts the text and generates semantic chunks automatically.
                </>
              )}
              {createTab === 'text' && (
                <>
                  <span className="font-medium text-slate-800">Paste text:</span>{' '}
                  Use this when the text was already extracted or curated outside the platform. Paste it below and the service will chunk it.
                </>
              )}
              {createTab === 'metadata' && (
                <>
                  <span className="font-medium text-slate-800">Metadata only:</span>{' '}
                  Register the document record in <em>draft</em> status without attaching content yet. You can add content later from the "Add content" panel on the right.
                </>
              )}
            </p>

            <form className="space-y-5" onSubmit={handleCreateAndIngest}>
              {/* ── Metadata fields (always shown) ───────────────────────── */}
              <div className="space-y-4">
                <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-400">Document metadata</h3>

                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Title <span className="text-rose-500">*</span></span>
                    <input
                      className="input-field"
                      value={createForm.title}
                      onChange={(event) => setCreateForm((current) => ({ ...current, title: event.target.value }))}
                      placeholder="e.g. Rogerian Core Conditions"
                      required
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Source</span>
                    <input
                      className="input-field"
                      value={createForm.source}
                      onChange={(event) => setCreateForm((current) => ({ ...current, source: event.target.value }))}
                      placeholder="manual, upload, url…"
                      required
                    />
                  </label>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Source URI</span>
                    <input
                      className="input-field"
                      value={createForm.source_uri}
                      onChange={(event) => setCreateForm((current) => ({ ...current, source_uri: event.target.value }))}
                      placeholder="https://... or internal reference"
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Review policy</span>
                    <select
                      className="input-field"
                      value={createForm.review_policy}
                      onChange={(event) => setCreateForm((current) => ({ ...current, review_policy: event.target.value }))}
                    >
                      {REVIEW_POLICY_OPTIONS.map((option) => (
                        <option key={option.value || 'none'} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Content type</span>
                    <select
                      className="input-field"
                      value={createForm.content_type}
                      onChange={(event) => setCreateForm((current) => ({ ...current, content_type: event.target.value }))}
                    >
                      {CONTENT_TYPES.map((contentType) => (
                        <option key={contentType} value={contentType}>
                          {contentType}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Language</span>
                    <input
                      className="input-field"
                      value={createForm.language}
                      onChange={(event) => setCreateForm((current) => ({ ...current, language: event.target.value }))}
                      placeholder="en"
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Created by</span>
                    <input
                      className="input-field"
                      value={createForm.created_by}
                      onChange={(event) => setCreateForm((current) => ({ ...current, created_by: event.target.value }))}
                    />
                  </label>
                </div>

                <label className="block text-sm">
                  <span className="mb-1 block font-medium text-gray-700">Tags</span>
                  <input
                    className="input-field"
                    value={createForm.tags}
                    onChange={(event) => setCreateForm((current) => ({ ...current, tags: event.target.value }))}
                    placeholder="care, onboarding, policy"
                  />
                </label>

                <SuggestionToggleGroup
                  label="Scopes"
                  options={SUGGESTED_SCOPE_OPTIONS}
                  value={createForm.scopes}
                  helperText="Toggle suggested scopes, or type custom ones in the field below."
                  onToggle={(scope) =>
                    setCreateForm((current) => ({
                      ...current,
                      scopes: toggleCommaSeparatedValue(current.scopes, scope),
                    }))
                  }
                />

                <label className="block text-sm">
                  <span className="mb-1 block font-medium text-gray-700">Custom scopes</span>
                  <input
                    className="input-field"
                    value={createForm.scopes}
                    onChange={(event) => setCreateForm((current) => ({ ...current, scopes: event.target.value }))}
                    placeholder="session_generation, safety, coping"
                  />
                </label>
              </div>

              {/* ── Content section: shown when tab is not 'metadata' ─────── */}
              {createTab !== 'metadata' && (
                <div className="space-y-4 border-t border-gray-200 pt-5">
                  <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-400">Content</h3>

                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Section label <span className="text-gray-400 font-normal">(optional)</span></span>
                    <input
                      className="input-field"
                      value={createForm.section}
                      onChange={(event) => setCreateForm((current) => ({ ...current, section: event.target.value }))}
                      placeholder="chapter-1, faq, introduction…"
                    />
                  </label>

                  {/* Upload file tab */}
                  {createTab === 'upload' && (
                    <>
                      <div
                        onDragOver={(event) => { event.preventDefault(); setIsDragActiveCreate(true); }}
                        onDragLeave={() => setIsDragActiveCreate(false)}
                        onDrop={(event) => {
                          event.preventDefault();
                          setIsDragActiveCreate(false);
                          const file = event.dataTransfer.files?.[0];
                          if (file) setSelectedCreateFile(file);
                        }}
                        className={`rounded-2xl border-2 border-dashed p-8 transition ${isDragActiveCreate
                          ? 'border-sky-400 bg-sky-50'
                          : 'border-slate-300 bg-slate-50/70 hover:border-slate-400 hover:bg-slate-50'
                          }`}
                      >
                        <div className="flex flex-col items-center text-center">
                          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white shadow-sm">
                            <ArrowUpTrayIcon className="h-6 w-6 text-sky-600" />
                          </div>
                          <h3 className="mt-4 text-base font-semibold text-slate-900">Drop a file here</h3>
                          <p className="mt-2 text-sm text-slate-600">
                            Supports PDF, TXT, and Markdown files.
                          </p>
                          <label className="mt-4 inline-flex cursor-pointer items-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50">
                            Choose file
                            <input
                              type="file"
                              accept=".pdf,.txt,.md,.markdown,text/plain,application/pdf,text/markdown"
                              className="hidden"
                              onChange={(event) => {
                                const file = event.target.files?.[0];
                                if (file) setSelectedCreateFile(file);
                              }}
                            />
                          </label>
                        </div>
                      </div>

                      {selectedCreateFile && (
                        <div className="flex items-center justify-between rounded-xl border border-sky-200 bg-sky-50 px-4 py-3">
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-slate-900">{selectedCreateFile.name}</p>
                            <p className="mt-0.5 text-xs text-slate-500">
                              {Math.max(1, Math.round(selectedCreateFile.size / 1024))} KB
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => setSelectedCreateFile(null)}
                            className="ml-4 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50"
                          >
                            Remove
                          </button>
                        </div>
                      )}
                    </>
                  )}

                  {/* Paste text tab */}
                  {createTab === 'text' && (
                    <label className="block text-sm">
                      <span className="mb-1 block font-medium text-gray-700">Normalized text content</span>
                      <textarea
                        className="input-field min-h-[200px] resize-y"
                        value={createForm.content}
                        onChange={(event) => setCreateForm((current) => ({ ...current, content: event.target.value }))}
                        placeholder="Paste the extracted or curated text here. The service will chunk it and attach it to the new document."
                      />
                    </label>
                  )}
                </div>
              )}

              {/* ── Submit ─────────────────────────────────────────────────── */}
              <div className="flex items-center justify-between border-t border-gray-200 pt-5">
                <p className="text-xs text-gray-500">
                  {createTab === 'metadata' && 'Creates a draft document record — add content later.'}
                  {createTab === 'upload' && (selectedCreateFile ? `Will register + upload "${selectedCreateFile.name}"` : 'Select a file above to attach it on creation.')}
                  {createTab === 'text' && (createForm.content.trim() ? 'Will register + ingest the pasted text.' : 'Paste text above to attach it on creation.')}
                </p>
                <button
                  type="submit"
                  className="inline-flex items-center rounded-lg bg-slate-950 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={submitting.create}
                >
                  <DocumentPlusIcon className="mr-2 h-4 w-4" />
                  {submitting.create
                    ? (createTab === 'metadata' ? 'Registering…' : 'Creating…')
                    : (createTab === 'metadata' ? 'Register document' : 'Register & add content')}
                </button>
              </div>
            </form>
          </section>

          {/* ── Document inventory ────────────────────────────────────────── */}
          <section className="card space-y-5 p-6">
            <SectionHeader
              title="Document inventory"
              description="Filter and select the document you want to inspect or manage."
            />

            <div className="grid gap-3 md:grid-cols-[1.4fr_1fr_1fr]">
              <label className="relative block text-sm">
                <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  className="input-field pl-9"
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  placeholder="Search title, scope, tag, id…"
                />
              </label>
              <select
                className="input-field"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
              >
                <option value="">All statuses</option>
                {DOCUMENT_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
              <select
                className="input-field"
                value={scopeFilter}
                onChange={(event) => setScopeFilter(event.target.value)}
              >
                <option value="">All scopes</option>
                {scopeOptions.map((scope) => (
                  <option key={scope} value={scope}>
                    {scope}
                  </option>
                ))}
              </select>
            </div>

            {documentsLoading ? (
              <LoadingState message="Refreshing document list…" />
            ) : filteredDocuments.length === 0 ? (
              <EmptyState
                title="No documents found"
                message="Change the filters or add the first document using the form above."
              />
            ) : (
              <div className="space-y-3">
                {filteredDocuments.map((document) => {
                  const isSelected = document.document_id === selectedDocumentId;
                  return (
                    <button
                      type="button"
                      key={document.document_id}
                      onClick={() => setSelectedDocumentId(document.document_id)}
                      className={`w-full rounded-xl border p-4 text-left transition ${isSelected
                        ? 'border-sky-400 bg-sky-50/70 shadow-sm'
                        : 'border-gray-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                        }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-900">{document.title}</p>
                          <p className="mt-1 text-xs text-slate-500">{document.document_id}</p>
                        </div>
                        <span className={`shrink-0 inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ring-inset ${getStatusTone(document.status)}`}>
                          {document.status}
                        </span>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(document.scopes || []).slice(0, 3).map((scope) => (
                          <span key={scope} className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">
                            {scope}
                          </span>
                        ))}
                        {document.scopes?.length > 3 && (
                          <span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">
                            +{document.scopes.length - 3}
                          </span>
                        )}
                      </div>
                      <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                        <span>{document.chunk_count || 0} chunks</span>
                        <span>Updated {formatDate(document.updated_at)}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </section>
        </div>

        {/* RIGHT column ────────────────────────────────────────────────────── */}
        <div className="space-y-8">

          {/* ── Document details ──────────────────────────────────────────── */}
          <section className="card space-y-6 p-6">
            <SectionHeader
              title="Document details"
              description="Inspect metadata, quality signals, and lifecycle state for the selected document."
            />

            {detailsLoading ? (
              <LoadingState message="Loading document details…" />
            ) : !selectedDocument ? (
              <EmptyState
                title="Select a document"
                message="Pick a document from the inventory on the left to inspect it here."
              />
            ) : (
              <div className="space-y-6">
                <div className="flex flex-col gap-5 rounded-xl border border-slate-200 bg-slate-50/70 p-5 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-xl font-semibold text-slate-950">{selectedDocument.title}</h3>
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ring-inset ${getStatusTone(selectedDocument.status)}`}>
                        {selectedDocument.status}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                      {selectedDocument.source}
                      {selectedDocument.source_uri ? ` • ${selectedDocument.source_uri}` : ''}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">{selectedDocument.document_id}</p>
                  </div>
                  <div className="grid min-w-[220px] gap-3 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
                    <div className="flex items-center justify-between gap-3">
                      <span>Version</span>
                      <span className="font-medium text-slate-900">{selectedDocument.document_version}</span>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <span>Language</span>
                      <span className="font-medium text-slate-900">{selectedDocument.language}</span>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <span>Chunks</span>
                      <span className="font-medium text-slate-900">{selectedDocument.chunk_count || 0}</span>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <span>Indexed</span>
                      <span className="font-medium text-slate-900">{formatDate(selectedDocument.last_indexed_at)}</span>
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-xl border border-gray-200 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">Scopes</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(selectedDocument.scopes || []).length ? (
                        selectedDocument.scopes.map((scope) => (
                          <span key={scope} className="rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
                            {scope}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-gray-500">No scopes assigned.</span>
                      )}
                    </div>
                  </div>

                  <div className="rounded-xl border border-gray-200 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">Tags</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(selectedDocument.tags || []).length ? (
                        selectedDocument.tags.map((tag) => (
                          <span key={tag} className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                            {tag}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-gray-500">No tags assigned.</span>
                      )}
                    </div>
                  </div>
                </div>

                {selectedDocument.quality_warnings?.length > 0 && (
                  <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                    <div className="flex items-start gap-3">
                      <ExclamationTriangleIcon className="mt-0.5 h-5 w-5 text-amber-600" />
                      <div>
                        <p className="text-sm font-medium text-amber-900">Quality warnings</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {selectedDocument.quality_warnings.map((warning) => (
                            <span key={warning} className="rounded-md bg-white px-2 py-1 text-xs text-amber-800 ring-1 ring-inset ring-amber-200">
                              {warning}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* ── Sections that need a selected document ─────────────────────── */}
          {selectedDocument && (
            <>
              {/* ── Lifecycle controls ────────────────────────────────────── */}
              <section className="card space-y-5 p-6">
                <SectionHeader
                  title="Lifecycle controls"
                  description="Move the selected document through its administrative lifecycle and record an audit reason."
                />
                <form className="space-y-4" onSubmit={handleStatusUpdate}>
                  <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-[1fr_1fr_1.4fr]">
                    <label className="block text-sm">
                      <span className="mb-1 block font-medium text-gray-700">Target status</span>
                      <select
                        className="input-field"
                        value={statusForm.status}
                        onChange={(event) => setStatusForm((current) => ({ ...current, status: event.target.value }))}
                      >
                        {DOCUMENT_STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="block text-sm">
                      <span className="mb-1 block font-medium text-gray-700">Updated by</span>
                      <input
                        className="input-field"
                        value={statusForm.updated_by}
                        onChange={(event) => setStatusForm((current) => ({ ...current, updated_by: event.target.value }))}
                      />
                    </label>
                    <label className="block text-sm xl:col-span-1">
                      <span className="mb-1 block font-medium text-gray-700">Reason</span>
                      <input
                        className="input-field"
                        value={statusForm.reason}
                        onChange={(event) => setStatusForm((current) => ({ ...current, reason: event.target.value }))}
                        placeholder="Why this transition matters"
                      />
                    </label>
                  </div>
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      className="rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={submitting.status}
                    >
                      {submitting.status ? 'Updating…' : 'Apply status'}
                    </button>
                  </div>
                </form>
              </section>

              {/* ── Add more content (for existing document) ──────────────── */}
              <section className="card space-y-6 p-6">
                <SectionHeader
                  title="Add content"
                  description={`Attach additional content to "${selectedDocument.title}". Use this to add a second section, replace extracted text, or supplement the document after creation.`}
                />

                <div className="grid gap-4 sm:grid-cols-3">
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Content type</span>
                    <select
                      className="input-field"
                      value={ingestForm.content_type}
                      onChange={(event) => setIngestForm((current) => ({ ...current, content_type: event.target.value }))}
                    >
                      {CONTENT_TYPES.map((contentType) => (
                        <option key={contentType} value={contentType}>
                          {contentType}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Section</span>
                    <input
                      className="input-field"
                      value={ingestForm.section}
                      onChange={(event) => setIngestForm((current) => ({ ...current, section: event.target.value }))}
                      placeholder="chapter-2, faq, appendix…"
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Ingested by</span>
                    <input
                      className="input-field"
                      value={ingestForm.ingested_by}
                      onChange={(event) => setIngestForm((current) => ({ ...current, ingested_by: event.target.value }))}
                    />
                  </label>
                </div>

                {/* Upload file for existing doc */}
                <form className="space-y-4" onSubmit={handleUploadFile}>
                  <div
                    onDragOver={(event) => { event.preventDefault(); setIsDragActive(true); }}
                    onDragLeave={() => setIsDragActive(false)}
                    onDrop={handleDrop}
                    className={`rounded-2xl border-2 border-dashed p-6 transition ${isDragActive
                      ? 'border-sky-400 bg-sky-50'
                      : 'border-slate-300 bg-slate-50/70 hover:border-slate-400 hover:bg-slate-50'
                      }`}
                  >
                    <div className="flex flex-col items-center text-center">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-sm">
                        <ArrowUpTrayIcon className="h-5 w-5 text-sky-600" />
                      </div>
                      <p className="mt-3 text-sm font-medium text-slate-900">Upload a file</p>
                      <p className="mt-1 text-xs text-slate-500">PDF, TXT, or Markdown</p>
                      <label className="mt-3 inline-flex cursor-pointer items-center rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50">
                        Choose file
                        <input
                          type="file"
                          accept=".pdf,.txt,.md,.markdown,text/plain,application/pdf,text/markdown"
                          className="hidden"
                          onChange={(event) => handleFileSelection(event.target.files?.[0])}
                        />
                      </label>
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-4 py-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-900">
                        {selectedFile ? selectedFile.name : 'No file selected'}
                      </p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {selectedFile
                          ? `${Math.max(1, Math.round(selectedFile.size / 1024))} KB • ${selectedFile.type || 'unknown type'}`
                          : 'Select a file or drop it into the upload zone above.'}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {selectedFile && (
                        <button
                          type="button"
                          onClick={() => setSelectedFile(null)}
                          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
                        >
                          Clear
                        </button>
                      )}
                      <button
                        type="submit"
                        className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={submitting.ingest || !selectedFile}
                      >
                        {submitting.ingest ? 'Uploading…' : 'Upload & ingest'}
                      </button>
                    </div>
                  </div>

                  {lastUploadResult && (
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
                      <p className="font-medium">File processed successfully.</p>
                      <p className="mt-1 text-xs">
                        {lastUploadResult.filename} · {lastUploadResult.extracted_characters} chars extracted · saved at {lastUploadResult.stored_uri}
                      </p>
                    </div>
                  )}
                </form>

                {/* Paste text for existing doc */}
                <form className="space-y-4 border-t border-gray-200 pt-5" onSubmit={handleIngestContent}>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700">Or paste text directly</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Use this when the content was extracted or curated outside the platform.
                    </p>
                  </div>
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-gray-700">Normalized text content</span>
                    <textarea
                      className="input-field min-h-[200px] resize-y"
                      value={ingestForm.content}
                      onChange={(event) => setIngestForm((current) => ({ ...current, content: event.target.value }))}
                      placeholder="Paste extracted text here. The Knowledge Service will chunk it and attach it to the selected document."
                      required
                    />
                  </label>
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      className="rounded-lg bg-sky-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={submitting.ingest}
                    >
                      {submitting.ingest ? 'Ingesting…' : 'Ingest & chunk text'}
                    </button>
                  </div>
                </form>
              </section>

              {/* ── Retrieval lab ─────────────────────────────────────────── */}
              <section className="card space-y-6 p-6">
                <SectionHeader
                  title="Retrieval lab"
                  description="Exercise the retrieval contract with real allowed scopes and inspect the live response from the Knowledge Service."
                />
                <form className="space-y-5" onSubmit={handleRetrieve}>
                  <div className="grid gap-6 md:grid-cols-2">
                    <label className="block text-sm">
                      <span className="mb-1 block font-medium text-gray-700">Query</span>
                      <textarea
                        className="input-field min-h-[120px] resize-y"
                        value={retrievalForm.query}
                        onChange={(event) => setRetrievalForm((current) => ({ ...current, query: event.target.value }))}
                        placeholder="What knowledge should this prompt retrieve?"
                        required
                      />
                    </label>
                    <div className="space-y-4">
                      <SuggestionToggleGroup
                        label="Allowed scopes"
                        options={Array.from(new Set([...SUGGESTED_SCOPE_OPTIONS, ...scopeOptions]))}
                        value={retrievalForm.allowed_scopes}
                        helperText="Use the same scope language that prompts and documents share."
                        onToggle={(scope) =>
                          setRetrievalForm((current) => ({
                            ...current,
                            allowed_scopes: toggleCommaSeparatedValue(current.allowed_scopes, scope),
                          }))
                        }
                      />
                      <label className="block text-sm">
                        <span className="mb-1 block font-medium text-gray-700">Custom allowed scopes</span>
                        <input
                          className="input-field"
                          value={retrievalForm.allowed_scopes}
                          onChange={(event) => setRetrievalForm((current) => ({ ...current, allowed_scopes: event.target.value }))}
                          placeholder="safety, coping, onboarding"
                        />
                      </label>
                    </div>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
                    <label className="block text-sm">
                      <span className="mb-1 block font-medium text-gray-700">Prompt key</span>
                      <input
                        className="input-field"
                        value={retrievalForm.prompt_key}
                        onChange={(event) => setRetrievalForm((current) => ({ ...current, prompt_key: event.target.value }))}
                        placeholder="session_generation_v1"
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="mb-1 block font-medium text-gray-700">Prompt version</span>
                      <input
                        type="number"
                        min="1"
                        className="input-field"
                        value={retrievalForm.prompt_version}
                        onChange={(event) => setRetrievalForm((current) => ({ ...current, prompt_version: event.target.value }))}
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="mb-1 block font-medium text-gray-700">Language</span>
                      <input
                        className="input-field"
                        value={retrievalForm.language}
                        onChange={(event) => setRetrievalForm((current) => ({ ...current, language: event.target.value }))}
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="mb-1 block font-medium text-gray-700">Top K</span>
                      <input
                        type="number"
                        min="1"
                        max="20"
                        className="input-field"
                        value={retrievalForm.top_k}
                        onChange={(event) => setRetrievalForm((current) => ({ ...current, top_k: event.target.value }))}
                      />
                    </label>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <label className="block text-sm">
                      <span className="mb-1 block font-medium text-gray-700">Chat ID</span>
                      <input
                        className="input-field"
                        value={retrievalForm.chat_id}
                        onChange={(event) => setRetrievalForm((current) => ({ ...current, chat_id: event.target.value }))}
                        placeholder="optional"
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="mb-1 block font-medium text-gray-700">Trace ID</span>
                      <input
                        className="input-field"
                        value={retrievalForm.trace_id}
                        onChange={(event) => setRetrievalForm((current) => ({ ...current, trace_id: event.target.value }))}
                        placeholder="optional trace identifier"
                      />
                    </label>
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      className="inline-flex items-center rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={submitting.retrieve}
                    >
                      <PlayIcon className="mr-2 h-4 w-4" />
                      {submitting.retrieve ? 'Running…' : 'Run retrieval'}
                    </button>
                  </div>
                </form>

                {retrievalResponse && (
                  <div className="space-y-4 rounded-xl border border-violet-200 bg-violet-50/60 p-5">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm font-semibold text-violet-950">Retrieval response</p>
                        <p className="mt-1 text-xs text-violet-700">
                          index version: {retrievalResponse.index_version || 'Unavailable'}
                        </p>
                      </div>
                      <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-violet-700 ring-1 ring-inset ring-violet-200">
                        {retrievalResponse.results?.length || 0} result(s)
                      </span>
                    </div>

                    {(retrievalResponse.warnings || []).length > 0 && (
                      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                        {(retrievalResponse.warnings || []).map((warning) => (
                          <p key={warning}>{warning}</p>
                        ))}
                      </div>
                    )}

                    {(retrievalResponse.results || []).length === 0 ? (
                      <EmptyState
                        title="No chunks returned"
                        message="This is the live contract response from the Knowledge Service."
                      />
                    ) : (
                      <div className="space-y-3">
                        {retrievalResponse.results.map((result) => (
                          <div key={result.chunk_id} className="rounded-xl border border-white/80 bg-white p-4">
                            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                              <div>
                                <p className="text-sm font-semibold text-slate-900">{result.citation?.title || result.chunk_id}</p>
                                <p className="mt-1 text-xs text-slate-500">
                                  {result.citation?.document_id} · section {result.citation?.section || 'n/a'}
                                </p>
                              </div>
                              <span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">
                                final score {result.scores?.final ?? 'n/a'}
                              </span>
                            </div>
                            <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{result.content}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </section>
            </>
          )}
        </div>
      </div>

      {/* ── Audit stream (full width) ────────────────────────────────────────── */}
      <section className="card space-y-5 p-6">
        <SectionHeader
          title="Audit stream"
          description="Lifecycle and retrieval events recorded by the Knowledge Service."
          action={
            <button
              type="button"
              onClick={loadAuditEvents}
              className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
            >
              <ArrowPathIcon className="mr-2 h-4 w-4" />
              Refresh audit
            </button>
          }
        />

        {auditLoading ? (
          <LoadingState message="Loading audit events…" />
        ) : auditEvents.length === 0 ? (
          <EmptyState
            title="No audit events yet"
            message="Events appear here after document creation, content ingestion, status changes, or retrieval attempts."
          />
        ) : selectedDocument && selectedDocumentEvents.length === 0 ? (
          <EmptyState
            title="No events for the selected document"
            message="This record has no audit entries yet in the current in-memory Knowledge Service."
          />
        ) : (
          <div className="space-y-3">
            {(selectedDocument ? selectedDocumentEvents : auditEvents).map((event, index) => (
              <div key={`${event.created_at}-${event.action}-${index}`} className="rounded-xl border border-gray-200 p-4">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{event.action}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      document {event.document_id} · actor {event.actor || 'system'}
                    </p>
                  </div>
                  <span className="text-xs text-slate-500">{formatDate(event.created_at)}</span>
                </div>
                <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-950 p-3 text-xs leading-6 text-slate-100">
                  {JSON.stringify(event.details, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
