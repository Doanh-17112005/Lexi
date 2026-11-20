import React, { useEffect, useState, useRef } from "react";
import { DataTable } from "../components/DataTable";
import { SectionHeader } from "../components/SectionHeader";
import { EmptyState } from "../components/EmptyState";
import { StatusPill } from "../components/StatusPill";
import {
  listVocabulary,
  createVocabulary,
  updateVocabulary,
  deleteVocabulary,
  bulkImportVocabulary,
  type VocabItem,
} from "../lib/adminApi";
import { useI18n } from "../lib/i18n";
import { downloadCSV } from "../lib/csvExport";

const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;

const POS_OPTIONS = ["noun", "verb", "adjective", "adverb", "pronoun", "preposition", "conjunction", "interjection"];
const LEVEL_OPTIONS = ["A1", "A2", "B1", "B2", "C1", "C2"];
const TOPIC_OPTIONS = ["general", "travel", "business", "daily", "science", "technology"];
const QA_STATUS_OPTIONS = ["NEEDS_REVIEW", "VERIFIED", "UNREVIEWED"];
const PAGE_SIZE = 100;

const levelColor: Record<string, "info" | "success" | "warning" | "danger"> = {
  A1: "info",
  A2: "info",
  B1: "success",
  B2: "success",
  C1: "warning",
  C2: "danger",
};

const qaTone: Record<string, "success" | "warning" | "neutral"> = {
  VERIFIED: "success",
  NEEDS_REVIEW: "warning",
  UNREVIEWED: "neutral",
};

export const VocabularyPage = () => {
  const { t } = useI18n();
  const [items, setItems] = useState<VocabItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [topicFilter, setTopicFilter] = useState("");
  const [qaFilter, setQaFilter] = useState("");
  const [page, setPage] = useState(0);

  // Form
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    word: "",
    definition: "",
    translation: "",
    part_of_speech: "noun",
    pronunciation: "",
    difficulty_level: "A1",
    topics: ["general"] as string[],
    qa_status: "NEEDS_REVIEW",
    source_reference: "",
  });

  // Bulk import
  const [importResult, setImportResult] = useState<{ created: number; skipped: number; errors: string[] } | null>(null);
  const [importing, setImporting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const resetForm = () => {
    setForm({
      word: "",
      definition: "",
      translation: "",
      part_of_speech: "noun",
      pronunciation: "",
      difficulty_level: "A1",
      topics: ["general"],
      qa_status: "NEEDS_REVIEW",
      source_reference: "",
    });
    setEditingId(null);
  };

  const loadItems = async (targetPage = page) => {
    setLoading(true);
    setError(null);
    try {
      const res = await listVocabulary(PAGE_SIZE, targetPage * PAGE_SIZE, {
        search,
        difficulty_level: levelFilter || undefined,
        topic: topicFilter || undefined,
        qa_status: qaFilter || undefined,
      });
      setItems(res.data || []);
    } catch (err: any) {
      setError(err?.message || t.vocabulary.loadFailed);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadItems(page);
  }, [page, levelFilter, topicFilter, qaFilter]);

  const handleEdit = (item: VocabItem) => {
    setEditingId(item.id);
    setForm({
      word: item.word,
      definition: item.definition || "",
      translation: typeof item.translation === "object" ? (item.translation?.vi || "") : String(item.translation || ""),
      part_of_speech: item.part_of_speech || "noun",
      pronunciation: item.pronunciation || "",
      difficulty_level: item.difficulty_level || "A1",
      topics: item.topics && item.topics.length > 0 ? item.topics : ["general"],
      qa_status: item.qa_status || "NEEDS_REVIEW",
      source_reference: item.source_reference || "",
    });
    setShowForm(true);
  };

  const toggleFormTopic = (topic: string) => {
    setForm((prev) => {
      const exists = prev.topics.includes(topic);
      const next = exists ? prev.topics.filter((x) => x !== topic) : [...prev.topics, topic];
      return { ...prev, topics: next.length > 0 ? next : ["general"] };
    });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    const payload = {
      word: form.word,
      definition: form.definition,
      translation: form.translation,
      part_of_speech: form.part_of_speech,
      pronunciation: form.pronunciation,
      difficulty_level: form.difficulty_level,
      topics: form.topics.join(","),
      qa_status: form.qa_status,
      source_reference: form.source_reference || undefined,
    };
    try {
      if (editingId) {
        await updateVocabulary(editingId, payload);
      } else {
        await createVocabulary(payload);
      }
      resetForm();
      setShowForm(false);
      await loadItems(page);
    } catch (err: any) {
      setError(err?.message || t.common.saveFailed);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(t.vocabulary.deleteWord)) return;
    try {
      await deleteVocabulary(id);
      await loadItems();
    } catch (err: any) {
      setError(err?.message || t.common.deleteFailed);
    }
  };

  const handleBulkImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > MAX_UPLOAD_BYTES) {
      setError("File vượt quá 5 MB.");
      if (fileRef.current) fileRef.current.value = "";
      return;
    }
    setImporting(true);
    setError(null);
    setImportResult(null);
    try {
      const res = await bulkImportVocabulary(file);
      setImportResult(res.data || null);
      await loadItems();
    } catch (err: any) {
      setError(err?.message || "Import thất bại");
    } finally {
      setImporting(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleExport = () => {
    downloadCSV(
      "vocabulary.csv",
      ["word", "definition", "translation", "part_of_speech", "pronunciation", "difficulty_level", "topics", "qa_status"],
      items.map((v) => [
        v.word,
        v.definition || "",
        typeof v.translation === "object" ? v.translation?.vi || "" : v.translation || "",
        v.part_of_speech,
        v.pronunciation || "",
        v.difficulty_level,
        (v.topics || []).join(","),
        v.qa_status || "UNREVIEWED",
      ])
    );
  };

  // Client-side search matches current page immediately; Enter or button queries backend across all rows
  const filtered = search
    ? items.filter(
        (v) =>
          v.word.toLowerCase().includes(search.toLowerCase()) ||
          (v.definition || "").toLowerCase().includes(search.toLowerCase())
      )
    : items;

  return (
    <div className="stack">
      <SectionHeader title={t.vocabulary.title} description={`${items.length} ${t.vocabulary.description}`} />

      {error && <div className="form-error">{error}</div>}

      {importResult && (
        <div className="panel" style={{ padding: "12px 16px", background: "#f0fdf4" }}>
          <strong>Import hoàn tất:</strong> {importResult.created} tạo mới, {importResult.skipped} bỏ qua
          {importResult.errors.length > 0 && (
            <ul style={{ margin: "4px 0 0", paddingLeft: 20, color: "#b91c1c" }}>
              {importResult.errors.slice(0, 5).map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          )}
        </div>
      )}

      <div className="panel filter-panel">
        <div className="filter-bar">
          <input
            className="search-input"
            placeholder={t.vocabulary.searchPlaceholder}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setPage(0);
                void loadItems(0);
              }
            }}
          />
          <select
            className="filter-select"
            aria-label="Lọc cấp độ CEFR"
            value={levelFilter}
            onChange={(e) => { setPage(0); setLevelFilter(e.target.value); }}
          >
            <option value="">Tất cả CEFR</option>
            {LEVEL_OPTIONS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
          <select
            className="filter-select"
            aria-label="Lọc chủ đề"
            value={topicFilter}
            onChange={(e) => { setPage(0); setTopicFilter(e.target.value); }}
          >
            <option value="">Tất cả chủ đề</option>
            {TOPIC_OPTIONS.map((topic) => <option key={topic} value={topic}>{topic}</option>)}
          </select>
          <select
            className="filter-select"
            aria-label="Lọc trạng thái QA"
            value={qaFilter}
            onChange={(e) => { setPage(0); setQaFilter(e.target.value); }}
          >
            <option value="">Tất cả QA</option>
            {QA_STATUS_OPTIONS.map((qa) => <option key={qa} value={qa}>{qa}</option>)}
          </select>
          <input type="file" accept=".csv,.pdf" ref={fileRef} onChange={handleBulkImport} style={{ display: "none" }} />
          <button type="button" className="ghost-button" onClick={() => { setPage(0); void loadItems(0); }}>
            Tìm
          </button>
          <button type="button" className="ghost-button" onClick={() => fileRef.current?.click()} disabled={importing}>
            {importing ? "Đang import..." : "Import CSV/PDF"}
          </button>
          <button type="button" className="ghost-button" onClick={handleExport} disabled={items.length === 0}>
            Export CSV
          </button>
          <button type="button" className="primary-button" onClick={() => { resetForm(); setShowForm(true); }}>
            {t.vocabulary.createWord}
          </button>
        </div>
      </div>

      <div className="panel">
        {loading ? (
          <div className="loading">{t.common.loading}</div>
        ) : filtered.length === 0 ? (
          <EmptyState title={t.vocabulary.noWords} description={t.vocabulary.noWordsDesc} />
        ) : (
          <DataTable
            columns={[
              {
                header: t.vocabulary.word,
                render: (row) => (
                  <div>
                    <div className="table-title">{row.word}</div>
                    <div className="table-sub">{row.pronunciation || "—"}</div>
                  </div>
                ),
              },
              {
                header: "Định nghĩa",
                render: (row) => <span>{row.definition || "—"}</span>,
              },
              {
                header: "Dịch nghĩa",
                render: (row) => {
                  if (!row.translation) return "—";
                  if (typeof row.translation === "string") return row.translation;
                  return row.translation.vi || "—";
                },
              },
              {
                header: "Loại từ",
                render: (row) => <span className="table-meta">{row.part_of_speech || "—"}</span>,
                align: "center",
              },
              {
                header: "Level",
                render: (row) => (
                  <StatusPill
                    tone={levelColor[row.difficulty_level] || "info"}
                    label={row.difficulty_level || "A1"}
                  />
                ),
                align: "center",
              },
              {
                header: "Chủ đề",
                render: (row) => (
                  <span className="table-meta">
                    {row.topics && row.topics.length > 0 ? row.topics.join(", ") : "—"}
                  </span>
                ),
                align: "center",
              },
              {
                header: "QA",
                render: (row) => {
                  const status = row.qa_status || "UNREVIEWED";
                  return <StatusPill tone={qaTone[status] || "neutral"} label={status} />;
                },
                align: "center",
              },
              {
                header: t.common.actions,
                render: (row) => (
                  <div className="table-actions">
                    <button type="button" className="ghost-button small" onClick={() => handleEdit(row)}>{t.common.edit}</button>
                    <button type="button" className="ghost-button small danger" onClick={() => handleDelete(row.id)}>{t.common.delete}</button>
                  </div>
                ),
                align: "right",
              },
            ]}
            rows={filtered}
          />
        )}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span className="table-meta">Trang {page + 1}</span>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" className="ghost-button small" onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}>
            Trước
          </button>
          <button type="button" className="ghost-button small" onClick={() => setPage((p) => p + 1)} disabled={items.length < PAGE_SIZE}>
            Tiếp
          </button>
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showForm && (
        <div className="modal-overlay" role="dialog" aria-modal="true" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 540 }}>
            <h3>{editingId ? t.vocabulary.editWord : t.vocabulary.createNew}</h3>
            <form className="form" onSubmit={handleSave}>
              <label>
                Từ *
                <input value={form.word} onChange={(e) => setForm({ ...form, word: e.target.value })} required />
              </label>
              <label>
                Định nghĩa *
                <textarea rows={2} value={form.definition} onChange={(e) => setForm({ ...form, definition: e.target.value })} required />
              </label>
              <label>
                Dịch nghĩa (Tiếng Việt)
                <input value={form.translation} onChange={(e) => setForm({ ...form, translation: e.target.value })} />
              </label>
              <label>
                Phát âm
                <input value={form.pronunciation} onChange={(e) => setForm({ ...form, pronunciation: e.target.value })} placeholder="/prəˌnʌnsiˈeɪʃn/" />
              </label>
              <div className="form-row">
                <label>
                  Loại từ
                  <select value={form.part_of_speech} onChange={(e) => setForm({ ...form, part_of_speech: e.target.value })}>
                    {POS_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </label>
                <label>
                  Cấp độ
                  <select value={form.difficulty_level} onChange={(e) => setForm({ ...form, difficulty_level: e.target.value })}>
                    {LEVEL_OPTIONS.map((l) => <option key={l} value={l}>{l}</option>)}
                  </select>
                </label>
              </div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 6 }}>Chủ đề (tối thiểu 1)</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {TOPIC_OPTIONS.map((topic) => {
                    const active = form.topics.includes(topic);
                    return (
                      <button
                        key={topic}
                        type="button"
                        className={active ? "primary-button small" : "ghost-button small"}
                        onClick={() => toggleFormTopic(topic)}
                      >
                        {topic}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div className="form-row">
                <label>
                  Trạng thái QA
                  <select value={form.qa_status} onChange={(e) => setForm({ ...form, qa_status: e.target.value })}>
                    <option value="NEEDS_REVIEW">NEEDS_REVIEW</option>
                    <option value="VERIFIED">VERIFIED (yêu cầu nguồn)</option>
                  </select>
                </label>
                <label>
                  Nguồn tham chiếu (Oxford / Cambridge...)
                  <input
                    value={form.source_reference}
                    onChange={(e) => setForm({ ...form, source_reference: e.target.value })}
                    placeholder="Cambridge Dictionary..."
                  />
                </label>
              </div>
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                <button className="ghost-button" type="button" onClick={() => setShowForm(false)}>{t.common.cancel}</button>
                <button className="primary-button" type="submit" disabled={saving}>
                  {saving ? t.common.saving : editingId ? t.common.update : t.common.create}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
