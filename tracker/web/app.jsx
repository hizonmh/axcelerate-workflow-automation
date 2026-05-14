/* global React, ReactDOM, Icons, Pill, Kbd, Checkbox, fmtMoney, fmtMoneyPlain, fmtDate, fmtDateFull, sourceCls, methodIcon,
   CalculatorDrawer, UploadDrawer, ImportDrawer, ShortcutsDrawer, API */
const { useState, useEffect, useRef, useMemo, useCallback } = React;
const { createPortal } = ReactDOM;

// =============================================================================
// FLOATING MENU — anchored dropdown that escapes the row's overflow:hidden
// by rendering into <body> via portal and positioning with getBoundingClientRect.
// =============================================================================
function FloatingMenu({ anchorRef, open, onClose, children, align = "left" }) {
  const [pos, setPos] = useState(null);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!open || !anchorRef.current) { setPos(null); return; }
    const r = anchorRef.current.getBoundingClientRect();
    setPos({ top: r.bottom + 4, left: align === "right" ? r.right : r.left });
  }, [open, anchorRef, align]);

  useEffect(() => {
    if (!open) return;
    const onDown = (e) => {
      if (menuRef.current && menuRef.current.contains(e.target)) return;
      if (anchorRef.current && anchorRef.current.contains(e.target)) return;
      onClose();
    };
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, anchorRef, onClose]);

  if (!open || !pos) return null;
  const style = align === "right"
    ? { top: pos.top, right: window.innerWidth - pos.left }
    : { top: pos.top, left: pos.left };
  return createPortal(
    <div ref={menuRef} className="popover floating-menu" style={style}>{children}</div>,
    document.body
  );
}

// =============================================================================
// EDITABLE CELLS
// =============================================================================
function StatusCell({ row, statuses, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  return (
    <>
      <span
        ref={ref}
        className="cell-edit"
        onClick={(e) => { e.stopPropagation(); setOpen((v) => !v); }}
        title="Click to change status"
      >
        <Pill status={row.status} />
      </span>
      <FloatingMenu anchorRef={ref} open={open} onClose={() => setOpen(false)}>
        {statuses.map((s) => (
          <div
            key={s.key}
            className="popover-item"
            onClick={() => { onChange(row.id, "status", s.key); setOpen(false); }}
          >
            <Pill status={s.key} />
            {row.status === s.key && <Icons.Check size={11} style={{ marginLeft: "auto", color: "var(--accent)" }} />}
          </div>
        ))}
      </FloatingMenu>
    </>
  );
}

function MethodCell({ row, methods, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  return (
    <>
      <span
        ref={ref}
        className="cell-edit"
        onClick={(e) => { e.stopPropagation(); setOpen((v) => !v); }}
        title="Click to change payment method"
      >
        <span className="method">
          <span className="method-icon">{methodIcon(row.payment_method)}</span>
          {row.payment_method}
        </span>
      </span>
      <FloatingMenu anchorRef={ref} open={open} onClose={() => setOpen(false)}>
        {methods.map((m) => (
          <div
            key={m}
            className="popover-item"
            onClick={() => { onChange(row.id, "payment_method", m); setOpen(false); }}
          >
            <span className="method-icon">{methodIcon(m)}</span>
            <span>{m}</span>
            {row.payment_method === m && <Icons.Check size={11} style={{ marginLeft: "auto", color: "var(--accent)" }} />}
          </div>
        ))}
      </FloatingMenu>
    </>
  );
}

function StudentCell({ row, onChange }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(row.student || "");
  useEffect(() => { setValue(row.student || ""); }, [row.student]);

  const commit = () => {
    setEditing(false);
    const next = value.trim();
    if (next !== (row.student || "")) onChange(row.id, "student", next);
  };
  const cancel = () => { setValue(row.student || ""); setEditing(false); };

  if (editing) {
    return (
      <input
        autoFocus
        className="cell-edit-input"
        value={value}
        placeholder="Student name or ID"
        onChange={(e) => setValue(e.target.value)}
        onBlur={commit}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          else if (e.key === "Escape") cancel();
        }}
      />
    );
  }
  return (
    <span
      className="cell-edit"
      onClick={(e) => { e.stopPropagation(); setEditing(true); }}
      title="Click to edit student"
    >
      {row.student
        ? <span className="student-name">{row.student}</span>
        : <span className="student-empty"><Icons.UserAdd size={11} /> assign…</span>}
    </span>
  );
}

const INSTANCE_TABS = [
  { id: "MAC-received",      instance: "MAC",      direction: "received", label: "MAC" },
  { id: "NECGC-received",    instance: "NECGC",    direction: "received", label: "NECGC" },
  { id: "NEC-received",      instance: "NEC",      direction: "received", label: "NECTECH" },
  { id: "EZIDEBIT-received", instance: "EZIDEBIT", direction: "received", label: "MAC-EZIDEBIT" },
  { id: "MAC-spent",   instance: "MAC",   direction: "spent", label: "MAC", group: "spent" },
  { id: "NECGC-spent", instance: "NECGC", direction: "spent", label: "NECGC", group: "spent" },
  { id: "NEC-spent",   instance: "NEC",   direction: "spent", label: "NECTECH", group: "spent" },
];

// =============================================================================
// HERO BAND
// =============================================================================
function HeroBand({ txns, instances, lastSync, onUpload }) {
  return (
    <section className="hero">
      <div className="hero-title-row">
        <div className="hero-title">Ready to upload to Axcelerate</div>
        <div className="hero-sync">
          <span className="hero-sync-dot" /> {lastSync}
        </div>
      </div>
      <div className="hero-grid">
        {instances.map((inst) => {
          const set = txns.filter((t) => t.instance === inst.code && t.amount > 0);
          const ready = set.filter((t) => t.status === "OK to Upload");
          const unrec = set.filter((t) => t.status === "Unreconciled");
          const readyTotal = ready.reduce((s, r) => s + (r.upload_amount ?? r.amount), 0);
          const unrecTotal = unrec.reduce((s, r) => s + r.amount, 0);
          const hasReady = ready.length > 0;
          return (
            <article key={inst.code} className={`inst-card ${hasReady ? "has-ready" : ""}`}>
              <div className="inst-card-head">
                <span className={`inst-tag ${inst.cls}`}>{inst.code}</span>
                <span className="inst-card-name">{inst.name}</span>
              </div>
              <div className="inst-card-body">
                <div className="inst-card-ready">
                  <div className="inst-card-ready-label">Ready to upload</div>
                  <div className={`inst-card-ready-count ${ready.length ? "" : "zero"}`}>
                    {ready.length}
                  </div>
                  <div className="inst-card-ready-amount">
                    {ready.length ? fmtMoneyPlain(readyTotal) : "—"}
                  </div>
                </div>
                <button
                  className={hasReady ? "btn btn-primary inst-card-upload" : "btn inst-card-upload"}
                  disabled={!hasReady}
                  onClick={() => onUpload(inst)}
                >
                  <Icons.Upload size={12} />
                  {hasReady ? "Upload" : "Nothing ready"}
                </button>
              </div>
              <div className="inst-card-foot">
                <span className="inst-card-unrec">
                  <strong>{unrec.length}</strong> unreconciled
                  {unrec.length > 0 && <span style={{ color: "var(--text-subtle)" }}> · {fmtMoneyPlain(unrecTotal)}</span>}
                </span>
                {unrec.length > 0 && (
                  <span className="inst-card-unrec" style={{ color: "var(--st-unrec)", display: "inline-flex", alignItems: "center", gap: 4 }}>
                    <Icons.Warning size={11} /> Action needed
                  </span>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

// =============================================================================
// TABS
// =============================================================================
function Tabs({ active, onChange, counts }) {
  const received = INSTANCE_TABS.filter((t) => t.direction === "received");
  const spent = INSTANCE_TABS.filter((t) => t.direction === "spent");
  return (
    <div className="tabs-row" role="tablist">
      {received.map((t) => (
        <button key={t.id} role="tab" aria-selected={active === t.id} className="tab" onClick={() => onChange(t.id)}>
          {t.label}
          <span className="tab-count">{counts[t.id] ?? 0}</span>
        </button>
      ))}
      <span className="tab-sep" />
      <span className="tab-group-label">Spent</span>
      {spent.map((t) => (
        <button key={t.id} role="tab" aria-selected={active === t.id} className="tab" onClick={() => onChange(t.id)}>
          {t.label}
          <span className="tab-count">{counts[t.id] ?? 0}</span>
        </button>
      ))}
    </div>
  );
}

// =============================================================================
// FILTER CHIP
// =============================================================================
function FilterChip({ label, options, selected, onChange, counts, getCls }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    if (open) document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const summary = selected.length === 0 ? "All" : selected.length === options.length ? "All" : `${selected.length} selected`;
  const isActive = selected.length > 0 && selected.length < options.length;

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button className={`chip ${isActive ? "active" : ""}`} onClick={() => setOpen(!open)}>
        <span className="chip-label">{label}</span>
        <span className="chip-value">{summary}</span>
        <Icons.ChevDown size={11} />
      </button>
      {open && (
        <div className="popover">
          {options.map((opt) => {
            const on = selected.includes(opt);
            return (
              <div key={opt} className="popover-item" onClick={() => onChange(on ? selected.filter((x) => x !== opt) : [...selected, opt])}>
                <div className={`popover-checkbox ${on ? "checked" : ""}`}>
                  {on && <Icons.Check size={11} />}
                </div>
                {getCls ? <Pill status={opt} /> : <span>{opt}</span>}
                {counts && <span className="popover-item-count">{counts[opt] ?? 0}</span>}
              </div>
            );
          })}
          {selected.length > 0 && (
            <>
              <div className="divider" />
              <div className="popover-item" onClick={() => onChange([])} style={{ color: "var(--text-muted)" }}>
                <Icons.X size={11} /> Clear
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// TRANSACTION TABLE
// =============================================================================
function TxnTable({ rows, selected, setSelected, cursor, setCursor, onCalcOpen, meta, onUpdateField }) {
  if (rows.length === 0) {
    return (
      <div className="txn-table">
        <div className="txn-empty">
          <Icons.Sparkle size={20} />
          <div style={{ marginTop: 8, fontWeight: 600, color: "var(--text)" }}>Nothing matches your filters</div>
          <div>Try clearing a filter or switching tabs.</div>
        </div>
      </div>
    );
  }

  const allSelected = rows.length > 0 && rows.every((r) => selected.includes(r.id));
  const someSelected = rows.some((r) => selected.includes(r.id));

  const toggleAll = () => {
    if (allSelected) setSelected(selected.filter((id) => !rows.some((r) => r.id === id)));
    else setSelected([...new Set([...selected, ...rows.map((r) => r.id)])]);
  };

  const toggle = (id, e) => {
    if (e?.shiftKey && cursor != null) {
      const ids = rows.map((r) => r.id);
      const a = ids.indexOf(cursor);
      const b = ids.indexOf(id);
      if (a !== -1 && b !== -1) {
        const [lo, hi] = [Math.min(a, b), Math.max(a, b)];
        const range = ids.slice(lo, hi + 1);
        setSelected([...new Set([...selected, ...range])]);
        return;
      }
    }
    setSelected(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  };

  return (
    <div className="txn-table">
      <div className="txn-row header">
        <div className="txn-cell" onClick={toggleAll}>
          <Checkbox checked={allSelected} indeterminate={!allSelected && someSelected} onClick={toggleAll} />
        </div>
        <div />
        <div className="txn-cell">Status</div>
        <div className="txn-cell">Student</div>
        <div className="txn-cell">Payer</div>
        <div className="txn-cell">Date</div>
        <div className="txn-cell right">Amount</div>
        <div className="txn-cell">Method</div>
        <div className="txn-cell">Upload as / Reference</div>
        <div className="txn-cell">Account</div>
        <div />
      </div>

      {rows.map((r) => {
        const sel = selected.includes(r.id);
        const focused = cursor === r.id;
        const stripeCls = r.status === "Check Manually" ? "check" : r.status === "Unreconciled" ? "unrec" : "";
        return (
          <div
            key={r.id}
            className={`txn-row ${sel ? "selected" : ""} ${focused ? "focused" : ""}`}
            onClick={() => setCursor(r.id)}
          >
            <div className="txn-cell" onClick={(e) => { e.stopPropagation(); toggle(r.id, e); }}>
              <Checkbox checked={sel} onClick={() => {}} />
            </div>
            <div className={`stripe ${stripeCls}`} />
            <div className="txn-cell">
              <StatusCell row={r} statuses={meta.statuses} onChange={onUpdateField} />
            </div>
            <div className="txn-cell">
              <StudentCell row={r} onChange={onUpdateField} />
            </div>
            <div className="txn-cell">
              {r.payer_name}
              {r.source && (
                <span className="source" style={{ marginLeft: 6 }}>
                  <span className={`source-dot ${sourceCls(r.source)}`} />
                  {r.source === "Bank CSV" ? "Bank" : r.source === "Ezidebit PDF" ? "Ezi" : r.source}
                </span>
              )}
            </div>
            <div className="txn-cell num subdued" title={fmtDateFull(r.date)}>{fmtDate(r.date)}</div>
            <div className={`txn-cell amount right ${r.amount < 0 ? "neg" : ""}`}>{fmtMoney(r.amount)}</div>
            <div className="txn-cell">
              <MethodCell row={r} methods={meta.payment_methods} onChange={onUpdateField} />
            </div>
            <div className="txn-cell">
              {r.upload_amount != null ? (
                <div className="upload-as">
                  <span className="upload-as-amount">{fmtMoneyPlain(r.upload_amount)}</span>
                  <span className="upload-as-note">{r.upload_description}</span>
                </div>
              ) : (
                <span className="subdued" style={{ fontSize: 12 }}>{r.reference || "—"}</span>
              )}
            </div>
            <div className="txn-cell subdued" style={{ fontSize: 12 }}>{r.bank_account}</div>
            <div className="txn-cell" onClick={(e) => e.stopPropagation()}>
              {r.payment_method === "Agent Deduction" && (
                <button className="icon-btn" title="Open calculator (C)" onClick={() => onCalcOpen(r)}>
                  <Icons.Calculator size={13} />
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// =============================================================================
// FLOATING ACTION BAR
// =============================================================================
function ActionBar({ count, onClear, onStatus, onMethod, onOpenCalc, calcAvailable, meta }) {
  const [statusOpen, setStatusOpen] = useState(false);
  const [methodOpen, setMethodOpen] = useState(false);
  const statusRef = useRef(null);
  const methodRef = useRef(null);

  if (count === 0) return null;
  return (
    <div className="action-bar" role="toolbar">
      <span className="action-bar-count">
        <span className="action-bar-count-num">{count}</span> selected
      </span>
      <span className="action-bar-sep" />
      <button className="action-bar-btn primary" onClick={() => onStatus("OK to Upload")}>
        <Icons.Check size={13} /> OK to Upload <Kbd k="U" />
      </button>
      <button className="action-bar-btn" onClick={() => onStatus("Axcelerate Updated")}>
        Mark Updated <Kbd k="R" />
      </button>
      <button ref={statusRef} className="action-bar-btn" onClick={() => setStatusOpen((v) => !v)}>
        Set status <Icons.ChevDown size={11} />
      </button>
      <FloatingMenu anchorRef={statusRef} open={statusOpen} onClose={() => setStatusOpen(false)}>
        {meta.statuses.map((s) => (
          <div
            key={s.key}
            className="popover-item"
            onClick={() => { onStatus(s.key); setStatusOpen(false); }}
          >
            <Pill status={s.key} />
          </div>
        ))}
      </FloatingMenu>
      <button ref={methodRef} className="action-bar-btn" onClick={() => setMethodOpen((v) => !v)}>
        Set method <Icons.ChevDown size={11} />
      </button>
      <FloatingMenu anchorRef={methodRef} open={methodOpen} onClose={() => setMethodOpen(false)}>
        {meta.payment_methods.map((m) => (
          <div
            key={m}
            className="popover-item"
            onClick={() => { onMethod(m); setMethodOpen(false); }}
          >
            <span className="method-icon">{methodIcon(m)}</span>
            <span>{m}</span>
          </div>
        ))}
      </FloatingMenu>
      {calcAvailable && (
        <button className="action-bar-btn" onClick={onOpenCalc}>
          <Icons.Calculator size={13} /> Calculator <Kbd k="C" />
        </button>
      )}
      <span className="action-bar-sep" />
      <button className="action-bar-btn" onClick={onClear} title="Clear selection">
        <Icons.X size={13} /> <Kbd k="Esc" />
      </button>
    </div>
  );
}

// =============================================================================
// MAIN APP
// =============================================================================
function App() {
  const [txns, setTxns] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [lastSync, setLastSync] = useState("Loading…");

  const [activeTab, setActiveTab] = useState("MAC-received");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState(["Unreconciled", "OK to Upload", "Unallocated", "Check Manually"]);
  const [methodFilter, setMethodFilter] = useState([]);
  const [accountFilter, setAccountFilter] = useState([]);
  const [selected, setSelected] = useState([]);
  const [cursor, setCursor] = useState(null);

  const [calcTxn, setCalcTxn] = useState(null);
  const [calcOpen, setCalcOpen] = useState(false);
  const [uploadInst, setUploadInst] = useState(null);
  const [importOpen, setImportOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  const searchRef = useRef(null);

  const refresh = useCallback(async () => {
    try {
      const [m, t] = await Promise.all([
        meta ? Promise.resolve(meta) : API.meta(),
        API.list(),
      ]);
      if (!meta) {
        setMeta(m);
        window.STATUSES = m.statuses;
        window.PAYMENT_METHODS = m.payment_methods;
        window.INSTANCES = m.instances;
      }
      setTxns(t);
      setLastSync(`Synced ${new Date().toLocaleTimeString("en-AU", { hour: "2-digit", minute: "2-digit" })}`);
      setLoadError(null);
    } catch (e) {
      setLoadError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }, [meta]);

  useEffect(() => { refresh(); }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const tab = INSTANCE_TABS.find((t) => t.id === activeTab);
  const counts = useMemo(() => {
    const c = {};
    INSTANCE_TABS.forEach((t) => {
      c[t.id] = txns.filter((x) =>
        x.instance === t.instance &&
        (t.direction === "received" ? x.amount > 0 : x.amount < 0)
      ).length;
    });
    return c;
  }, [txns]);

  const tabRows = useMemo(() => txns.filter((t) =>
    t.instance === tab.instance &&
    (tab.direction === "received" ? t.amount > 0 : t.amount < 0)
  ), [txns, tab]);

  const accountOptions = useMemo(() => [...new Set(tabRows.map((r) => r.bank_account))], [tabRows]);

  const filtered = useMemo(() => {
    let r = tabRows;
    if (statusFilter.length) r = r.filter((x) => statusFilter.includes(x.status));
    if (methodFilter.length) r = r.filter((x) => methodFilter.includes(x.payment_method));
    if (accountFilter.length) r = r.filter((x) => accountFilter.includes(x.bank_account));
    if (search.trim()) {
      const s = search.toLowerCase();
      r = r.filter((x) =>
        (x.payer_name || "").toLowerCase().includes(s) ||
        (x.student || "").toLowerCase().includes(s) ||
        (x.reference || "").toLowerCase().includes(s) ||
        (x.description || "").toLowerCase().includes(s)
      );
    }
    return r;
  }, [tabRows, statusFilter, methodFilter, accountFilter, search]);

  useEffect(() => {
    if (cursor != null && !filtered.find((r) => r.id === cursor)) {
      setCursor(filtered[0]?.id ?? null);
    }
  }, [filtered, cursor]);

  // Optimistic single-row field update (used by inline cell editors).
  const updateField = useCallback(async (id, field, value) => {
    const before = txns;
    setTxns((t) => t.map((r) => r.id === id ? { ...r, [field]: value } : r));
    try {
      await API.patch(id, { [field]: value });
    } catch (e) {
      setTxns(before);
      alert(`Failed to update ${field}: ${e.message || e}`);
    }
  }, [txns]);

  // Optimistic bulk update — flip local state immediately, then bulk-PATCH.
  const applyBulk = async (fields) => {
    if (!selected.length) return;
    const ids = [...selected];
    const before = txns;
    setTxns((t) => t.map((r) => ids.includes(r.id) ? { ...r, ...fields } : r));
    setSelected([]);
    try {
      await API.bulkPatch(ids, fields);
    } catch (e) {
      setTxns(before);
      alert(`Failed to update: ${e.message || e}`);
    }
  };
  const applyStatus = (status) => applyBulk({ status });
  const applyMethod = (payment_method) => applyBulk({ payment_method });

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.matches("input, textarea, select")) {
        if (e.key === "Escape") e.target.blur();
        return;
      }
      if (e.key === "/") { e.preventDefault(); searchRef.current?.focus(); return; }
      if (e.key === "?") { setShortcutsOpen((s) => !s); return; }
      if (e.key === "Escape") {
        if (calcOpen) setCalcOpen(false);
        else if (uploadInst) setUploadInst(null);
        else if (importOpen) setImportOpen(false);
        else if (shortcutsOpen) setShortcutsOpen(false);
        else setSelected([]);
        return;
      }
      if (e.key === "i") { setImportOpen(true); return; }

      const idx = filtered.findIndex((r) => r.id === cursor);
      const moveTo = (n) => setCursor(filtered[Math.max(0, Math.min(filtered.length - 1, n))]?.id ?? null);

      if (e.key === "j" || e.key === "ArrowDown") { e.preventDefault(); moveTo(idx + 1); return; }
      if (e.key === "k" || e.key === "ArrowUp")   { e.preventDefault(); moveTo(idx - 1); return; }
      if (e.key === "x" && cursor != null) {
        setSelected((s) => s.includes(cursor) ? s.filter((x) => x !== cursor) : [...s, cursor]);
        return;
      }
      if (e.key === "u" && selected.length) { applyStatus("OK to Upload"); return; }
      if (e.key === "r" && selected.length) { applyStatus("Axcelerate Updated"); return; }
      if (e.key === "c") {
        const row = filtered.find((r) => r.id === cursor);
        if (row && row.payment_method === "Agent Deduction") openCalc(row);
        return;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const openCalc = (row) => { setCalcTxn(row); setCalcOpen(true); };

  // Prepare for upload — persists upload_amount + upload_description and flips status server-side.
  const onPrepareUpload = async ({ txn, invoiceTotal, deduction, actual, rate }) => {
    const upload_description = `Agent deducted ${fmtMoneyPlain(deduction).slice(1)} - paid ${fmtMoneyPlain(actual).slice(1)} @ ${rate}%`;
    try {
      const updated = await API.prepareUpload(txn.id, {
        upload_amount: invoiceTotal,
        upload_description,
      });
      setTxns((rows) => rows.map((r) => r.id === txn.id ? updated : r));
      setCalcOpen(false);
    } catch (e) {
      alert(`Failed to prepare for upload: ${e.message || e}`);
    }
  };

  const calcAvailable = selected.length === 1
    && txns.find((x) => x.id === selected[0])?.payment_method === "Agent Deduction";

  if (loading && !meta) {
    return (
      <div className="app">
        <header className="topbar">
          <div className="topbar-left">
            <div className="topbar-logo">B</div>
            <div><div className="topbar-title">Bank Transaction Tracker</div></div>
          </div>
        </header>
        <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
          {loadError ? (
            <>
              <div style={{ color: "var(--st-check)", fontWeight: 600, marginBottom: 8 }}>Could not reach the API</div>
              <div style={{ fontSize: 12 }}>{loadError}</div>
              <button className="btn" style={{ marginTop: 16 }} onClick={refresh}>Retry</button>
            </>
          ) : "Loading transactions…"}
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-left">
          <div className="topbar-logo">B</div>
          <div><div className="topbar-title">Bank Transaction Tracker</div></div>
        </div>
        <div className="topbar-right">
          <button className="btn btn-ghost btn-sm" onClick={refresh} title="Refresh from database">
            <Icons.Refresh size={13} /> Refresh
          </button>
          <button className="btn" onClick={() => setShortcutsOpen(true)} title="Keyboard shortcuts">
            <Icons.Keyboard size={13} /> Shortcuts
          </button>
          <button className="btn" onClick={() => setImportOpen(true)}>
            <Icons.Download size={13} /> Import
            <Kbd k="I" />
          </button>
        </div>
      </header>

      <HeroBand txns={txns} instances={meta.instances} lastSync={lastSync} onUpload={setUploadInst} />

      <Tabs active={activeTab} onChange={(id) => { setActiveTab(id); setSelected([]); }} counts={counts} />

      <div className="toolbar">
        <FilterChip
          label="Status"
          options={meta.statuses.map((s) => s.key)}
          selected={statusFilter}
          onChange={setStatusFilter}
          getCls
          counts={tabRows.reduce((acc, r) => ((acc[r.status] = (acc[r.status] || 0) + 1), acc), {})}
        />
        <FilterChip
          label="Method"
          options={meta.payment_methods}
          selected={methodFilter}
          onChange={setMethodFilter}
          counts={tabRows.reduce((acc, r) => ((acc[r.payment_method] = (acc[r.payment_method] || 0) + 1), acc), {})}
        />
        <FilterChip
          label="Account"
          options={accountOptions}
          selected={accountFilter}
          onChange={setAccountFilter}
          counts={tabRows.reduce((acc, r) => ((acc[r.bank_account] = (acc[r.bank_account] || 0) + 1), acc), {})}
        />
        <div className="toolbar-divider" />
        <div className="toolbar-search">
          <Icons.Search />
          <input
            ref={searchRef}
            placeholder="Search payer, student, reference, description…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <span className="search-kbd"><Kbd k="/" /></span>
        </div>
      </div>

      <div className="table-wrap">
        <div className="table-meta">
          <span>Showing {filtered.length} of {tabRows.length} transactions</span>
          <div className="table-meta-right">
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <Icons.Sparkle size={11} /> Tip: hit <Kbd k="?" /> for shortcuts
            </span>
          </div>
        </div>
        <TxnTable
          rows={filtered}
          selected={selected}
          setSelected={setSelected}
          cursor={cursor}
          setCursor={setCursor}
          onCalcOpen={openCalc}
          meta={meta}
          onUpdateField={updateField}
        />
      </div>

      <ActionBar
        count={selected.length}
        onClear={() => setSelected([])}
        onStatus={applyStatus}
        onMethod={applyMethod}
        meta={meta}
        calcAvailable={calcAvailable}
        onOpenCalc={() => {
          const row = txns.find((x) => x.id === selected[0]);
          if (row) openCalc(row);
        }}
      />

      <CalculatorDrawer
        open={calcOpen}
        txn={calcTxn}
        onClose={() => setCalcOpen(false)}
        onPrepareUpload={onPrepareUpload}
      />
      <UploadDrawer
        open={!!uploadInst}
        instance={uploadInst}
        txns={txns}
        onClose={() => setUploadInst(null)}
        onComplete={refresh}
      />
      <ImportDrawer open={importOpen} onClose={() => setImportOpen(false)} onImported={refresh} />
      <ShortcutsDrawer open={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
