/* global React, Icons, Pill, Kbd, Checkbox, fmtMoney, fmtMoneyPlain, fmtDate, sourceCls, methodIcon, API */
const { useState, useEffect, useRef, useMemo } = React;

// =============================================================================
// CALCULATOR DRAWER
// Mirrors agent_calculator.verify_payment_all_rates — shows 3 rates side by side.
// =============================================================================
function CalculatorDrawer({ open, txn, onClose, onPrepareUpload }) {
  const [actual, setActual] = useState(0);
  const [tuition, setTuition] = useState(0);
  const [admin, setAdmin] = useState(0);
  const [material, setMaterial] = useState(0);
  const [waiver, setWaiver] = useState(false);
  const [bonus, setBonus] = useState(0);

  useEffect(() => {
    if (txn) {
      setActual(txn.amount);
      setTuition(5000);
      setAdmin(200);
      setMaterial(0);
      setWaiver(false);
      setBonus(0);
    }
  }, [txn]);

  const calc = (rate) => {
    const commission = tuition * rate;
    const gst = commission * 0.1;
    const totalCommission = commission + gst;
    const waiverAmt = waiver ? admin : 0;
    const totalDeduction = totalCommission + waiverAmt + (bonus || 0);
    const invoiceTotal = tuition + admin + material;
    const expected = invoiceTotal - totalDeduction;
    const discrepancy = +(actual - expected).toFixed(2);
    return { rate, commission, gst, totalCommission, waiverAmt, totalDeduction, invoiceTotal, expected, discrepancy };
  };

  const rates = [0.30, 0.35, 0.40].map(calc);
  const invoiceTotal = tuition + admin + material;
  const hasInput = tuition > 0 || actual > 0;

  if (!open) return null;

  return (
    <>
      <div className="scrim" onClick={onClose} />
      <aside className="drawer wide" role="dialog" aria-label="Agent Commission Calculator">
        <div className="drawer-head">
          <div>
            <div className="drawer-title">Agent Commission Calculator</div>
            <div className="drawer-sub">Verify what the agent kept against three commission rates.</div>
          </div>
          <button className="btn btn-icon btn-ghost" onClick={onClose} aria-label="Close">
            <Icons.X />
          </button>
        </div>
        <div className="drawer-body">
          {txn && (
            <div className="calc-context">
              <Icons.User size={14} />
              <div className="calc-context-text">
                Loaded from <strong>{txn.payer_name}</strong>
                <span className="upload-row-meta"> · {fmtDate(txn.date)} · {txn.student || "no student"}</span>
              </div>
              <div className="calc-context-amount">{fmtMoneyPlain(txn.amount)}</div>
            </div>
          )}

          <div className="calc-row two">
            <div className="field">
              <label className="field-label">Payment Received</label>
              <div className="field-prefix">
                <span className="field-prefix-icon">$</span>
                <input type="number" step="0.01" value={actual} onChange={(e) => setActual(+e.target.value || 0)} />
              </div>
            </div>
            <div className="field">
              <label className="field-label">Bonus pre-deducted</label>
              <div className="field-prefix">
                <span className="field-prefix-icon">$</span>
                <input type="number" step="50" value={bonus} onChange={(e) => setBonus(+e.target.value || 0)} />
              </div>
            </div>
          </div>

          <div className="field-label" style={{ marginTop: 16, marginBottom: 6 }}>Invoice line items</div>
          <div className="calc-grid">
            <div className="field">
              <label className="field-label" style={{ textTransform: "none", letterSpacing: 0, color: "var(--text-muted)", fontWeight: 500 }}>Tuition fee</label>
              <div className="field-prefix">
                <span className="field-prefix-icon">$</span>
                <input type="number" step="0.01" value={tuition} onChange={(e) => setTuition(+e.target.value || 0)} />
              </div>
            </div>
            <div className="field">
              <label className="field-label" style={{ textTransform: "none", letterSpacing: 0, color: "var(--text-muted)", fontWeight: 500 }}>Admin fee</label>
              <div className="field-prefix">
                <span className="field-prefix-icon">$</span>
                <input type="number" step="0.01" value={admin} onChange={(e) => setAdmin(+e.target.value || 0)} />
              </div>
            </div>
            <div className="field">
              <label className="field-label" style={{ textTransform: "none", letterSpacing: 0, color: "var(--text-muted)", fontWeight: 500 }}>Material fee</label>
              <div className="field-prefix">
                <span className="field-prefix-icon">$</span>
                <input type="number" step="0.01" value={material} onChange={(e) => setMaterial(+e.target.value || 0)} />
              </div>
            </div>
          </div>

          <div className={`toggle-row ${waiver ? "on" : ""}`} style={{ marginTop: 12 }} onClick={() => setWaiver(!waiver)}>
            <div className="toggle-box">{waiver && <Icons.Check size={11} />}</div>
            <span>Agent pre-deducted the admin fee (waiver)</span>
          </div>

          {hasInput && (
            <>
              <div className="invoice-summary">
                <div>
                  <div className="upload-row-meta">Invoice total</div>
                  <div className="invoice-summary-total">{fmtMoneyPlain(invoiceTotal)}</div>
                </div>
                <div className="invoice-summary-bd">
                  Tuition {fmtMoneyPlain(tuition)} · Admin {fmtMoneyPlain(admin)} · Material {fmtMoneyPlain(material)}
                </div>
              </div>

              <div className="rate-grid">
                {rates.map((r) => {
                  const pct = Math.round(r.rate * 100);
                  const match = r.discrepancy === 0;
                  return (
                    <div key={pct} className={`rate-card ${match ? "match" : ""}`}>
                      <div className="rate-card-head">
                        <span className="rate-card-title">{pct}% commission</span>
                        {match && <Icons.Check size={14} style={{ color: "var(--st-ok)" }} />}
                      </div>
                      <div className="rate-card-line"><span>Commission</span><strong>{fmtMoneyPlain(r.commission)}</strong></div>
                      <div className="rate-card-line"><span>GST (10%)</span><strong>{fmtMoneyPlain(r.gst)}</strong></div>
                      {waiver && <div className="rate-card-line"><span>AF waiver</span><strong>{fmtMoneyPlain(r.waiverAmt)}</strong></div>}
                      {bonus > 0 && <div className="rate-card-line"><span>Bonus</span><strong>{fmtMoneyPlain(bonus)}</strong></div>}
                      <div className="rate-card-total"><span>Total deduction</span><strong className="num">{fmtMoneyPlain(r.totalDeduction)}</strong></div>
                      <div className="rate-card-line" style={{ marginTop: 4 }}><span>Expected paid</span><strong>{fmtMoneyPlain(r.expected)}</strong></div>
                      <div className={`rate-card-disc ${match ? "match" : r.discrepancy > 0 ? "over" : "under"}`}>
                        {match ? <Icons.Check size={12} /> : <Icons.Warning size={12} />}
                        {match
                          ? "Exact match"
                          : r.discrepancy > 0
                            ? `Overpaid by ${fmtMoneyPlain(r.discrepancy)}`
                            : `Underpaid by ${fmtMoneyPlain(Math.abs(r.discrepancy))}`}
                      </div>
                      {match && txn && (
                        <button
                          className="btn btn-primary btn-sm"
                          style={{ marginTop: 8, justifyContent: "center" }}
                          onClick={() => onPrepareUpload({
                            txn,
                            invoiceTotal: r.invoiceTotal,
                            deduction: r.totalDeduction,
                            actual,
                            rate: pct,
                          })}
                        >
                          <Icons.Check size={12} /> Prepare for upload
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
        <div className="drawer-foot">
          <span className="upload-row-meta">
            <Icons.Sparkle size={12} /> Picks the matching rate automatically when one lines up exactly
          </span>
          <button className="btn" onClick={onClose}>Close <Kbd k="Esc" /></button>
        </div>
      </aside>
    </>
  );
}

// =============================================================================
// UPLOAD REVIEW DRAWER
// Posts to /api/upload/{instance} — server spawns bulk_payment.py.
// =============================================================================
function UploadDrawer({ open, instance, txns, onClose, onComplete }) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!open) { setRunning(false); setResult(null); setError(null); }
  }, [open]);

  if (!open || !instance) return null;

  const rows = txns.filter((t) => t.instance === instance.code && t.status === "OK to Upload");
  const total = rows.reduce((s, r) => s + (r.upload_amount ?? r.amount), 0);

  const handleConfirm = async () => {
    setRunning(true);
    setError(null);
    try {
      const r = await API.upload(instance.code);
      setResult(r);
      onComplete?.();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setRunning(false);
    }
  };

  return (
    <>
      <div className="scrim" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label={`Upload ${instance.name}`}>
        <div className="drawer-head">
          <div>
            <div className="drawer-title">
              <span className={`inst-tag ${instance.cls}`} style={{ marginRight: 8 }}>{instance.name}</span>
              Confirm Axcelerate upload
            </div>
            <div className="drawer-sub">Every row below will post to Axcelerate when you confirm.</div>
          </div>
          <button className="btn btn-icon btn-ghost" onClick={onClose} aria-label="Close"><Icons.X /></button>
        </div>
        <div className="drawer-body">
          <div className="upload-summary">
            <div className="upload-summary-card">
              <div className="upload-summary-label">Transactions</div>
              <div className="upload-summary-value">{rows.length}</div>
            </div>
            <div className="upload-summary-card">
              <div className="upload-summary-label">Total upload</div>
              <div className="upload-summary-value">{fmtMoneyPlain(total)}</div>
            </div>
          </div>

          {result ? (
            <div
              className="import-result"
              style={result.returncode === 0 ? undefined : {
                background: "var(--st-check-bg)",
                borderColor: "oklch(0.85 0.08 25)",
              }}
            >
              <strong style={{ display: "flex", alignItems: "center", gap: 6 }}>
                {result.returncode === 0
                  ? <><Icons.Check size={14} /> bulk_payment.py finished</>
                  : <><Icons.Warning size={14} /> bulk_payment.py exited with code {result.returncode}</>}
              </strong>
              <div className="import-result-row upload-row-meta">
                Review rows now — each one shows its updated status (Axcelerate Updated / Unallocated / Check Manually).
              </div>
              {result.stdout && (
                <pre style={{ marginTop: 8, padding: 10, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 11, fontFamily: "var(--font-mono)", maxHeight: 220, overflow: "auto", whiteSpace: "pre-wrap" }}>{result.stdout}</pre>
              )}
              {result.stderr && (
                <pre style={{ marginTop: 8, padding: 10, background: "var(--st-check-bg)", border: "1px solid oklch(0.85 0.08 25)", borderRadius: 6, fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--st-check)", maxHeight: 160, overflow: "auto", whiteSpace: "pre-wrap" }}>{result.stderr}</pre>
              )}
            </div>
          ) : error ? (
            <div className="import-result" style={{ background: "var(--st-check-bg)", borderColor: "oklch(0.85 0.08 25)", color: "var(--st-check)" }}>
              <strong style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Icons.Warning size={14} /> Upload failed
              </strong>
              <div className="import-result-row">{error}</div>
            </div>
          ) : (
            <>
              <div className="field-label" style={{ marginBottom: 8 }}>Review rows ({rows.length})</div>
              <div>
                {rows.map((r, i) => {
                  const amt = r.upload_amount ?? r.amount;
                  return (
                    <div key={r.id} className="upload-row">
                      <div className="upload-row-num">{i + 1}</div>
                      <div>
                        <div className="upload-row-name">{r.student || r.payer_name}</div>
                        <div className="upload-row-meta">{r.reference || r.description}</div>
                      </div>
                      <div className="upload-row-meta">
                        {r.upload_description || r.payment_method}
                        <div>{fmtDate(r.date)} · {r.bank_account}</div>
                      </div>
                      <div className="upload-row-amount">{fmtMoneyPlain(amt)}</div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
        <div className="drawer-foot">
          {result ? (
            <>
              <span className="upload-row-meta">Output captured from subprocess</span>
              <button className="btn btn-primary" onClick={onClose}>Done</button>
            </>
          ) : (
            <>
              <span className="upload-row-meta">
                <Icons.Cog size={12} /> Runs bulk_payment.py --instance {instance.code}
              </span>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn" onClick={onClose} disabled={running}>Cancel</button>
                <button className="btn btn-primary" onClick={handleConfirm} disabled={running || rows.length === 0}>
                  {running ? (
                    <>
                      <span className="upload-row-num" style={{ background: "transparent", width: 14, height: 14, animation: "spin 1s linear infinite", borderRadius: "50%", borderTop: "2px solid white", borderRight: "2px solid transparent" }} />
                      Uploading…
                    </>
                  ) : (
                    <>
                      <Icons.Upload size={13} /> Upload {rows.length} to Axcelerate
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </div>
      </aside>
    </>
  );
}

// =============================================================================
// IMPORT DRAWER
// Posts files to /api/import — server runs the real parsers + upsert.
// =============================================================================
function ImportDrawer({ open, onClose, onImported }) {
  const [drag, setDrag] = useState(false);
  const [files, setFiles] = useState([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!open) { setFiles([]); setResult(null); setError(null); setRunning(false); }
  }, [open]);

  const onPick = (list) => setFiles([...list]);

  const runImport = async () => {
    if (!files.length) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const r = await API.importFiles(files);
      setResult(r);
      onImported?.();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setRunning(false);
    }
  };

  if (!open) return null;

  return (
    <>
      <div className="scrim" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label="Import transactions">
        <div className="drawer-head">
          <div>
            <div className="drawer-title">Import transactions</div>
            <div className="drawer-sub">Bank CSVs, Xero Excel, and Ezidebit PDFs.</div>
          </div>
          <button className="btn btn-icon btn-ghost" onClick={onClose} aria-label="Close"><Icons.X /></button>
        </div>
        <div className="drawer-body">
          <div
            className={`dropzone ${drag ? "drag" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              onPick(e.dataTransfer.files);
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <Icons.Upload size={22} />
            <div className="dropzone-strong">Drop files here, or click to browse</div>
            <div>Bank CSV, Xero Excel (.xlsx), Ezidebit PDF</div>
            <div className="dropzone-formats">.csv · .xlsx · .pdf</div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".csv,.xlsx,.pdf"
              style={{ display: "none" }}
              onChange={(e) => onPick(e.target.files)}
            />
          </div>

          {files.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <div className="field-label" style={{ marginBottom: 6 }}>{files.length} file(s) queued</div>
              {files.map((f) => (
                <div key={f.name} className="upload-row" style={{ gridTemplateColumns: "24px 1fr 80px" }}>
                  <Icons.Doc size={14} />
                  <div className="upload-row-name">{f.name}</div>
                  <div className="upload-row-meta" style={{ textAlign: "right" }}>queued</div>
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="import-result" style={{ background: "var(--st-check-bg)", borderColor: "oklch(0.85 0.08 25)", color: "var(--st-check)" }}>
              <strong style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Icons.Warning size={14} /> Import failed
              </strong>
              <div className="import-result-row">{error}</div>
            </div>
          )}

          {result && (
            <div className="import-result">
              <strong style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Icons.Check size={14} /> Imported {result.files.length} file(s)
              </strong>
              <div className="import-result-row"><span>New transactions</span><strong className="num">{result.total.inserted}</strong></div>
              <div className="import-result-row"><span>Updated (Bank CSV enriched Xero)</span><strong className="num">{result.total.updated}</strong></div>
              <div className="import-result-row"><span>Skipped (already imported)</span><strong className="num">{result.total.skipped}</strong></div>
              {result.errors && result.errors.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div className="field-label" style={{ color: "var(--st-check)", marginBottom: 4 }}>{result.errors.length} file error(s)</div>
                  {result.errors.map((e, i) => (
                    <div key={i} className="import-result-row" style={{ color: "var(--st-check)", fontSize: 11.5 }}>
                      <span>{e.file}</span><span>{e.error}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
        <div className="drawer-foot">
          <span className="upload-row-meta"><Icons.Sparkle size={12} /> Dedup keys keep re-imports safe</span>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn" onClick={onClose}>Close</button>
            <button className="btn btn-primary" onClick={runImport} disabled={running || !files.length}>
              {running ? (
                <>
                  <span className="upload-row-num" style={{ background: "transparent", width: 14, height: 14, animation: "spin 1s linear infinite", borderRadius: "50%", borderTop: "2px solid white", borderRight: "2px solid transparent" }} />
                  Importing…
                </>
              ) : (
                <><Icons.Download size={13} /> Import {files.length || ""}</>
              )}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

// =============================================================================
// SHORTCUTS DRAWER
// =============================================================================
function ShortcutsDrawer({ open, onClose }) {
  if (!open) return null;
  const items = [
    { keys: ["/"], label: "Focus search" },
    { keys: ["J"], label: "Move cursor down" },
    { keys: ["K"], label: "Move cursor up" },
    { keys: ["X"], label: "Select / deselect row at cursor" },
    { keys: ["⇧", "X"], label: "Range-select" },
    { keys: ["U"], label: "Mark selected as OK to Upload" },
    { keys: ["R"], label: "Mark selected as Axcelerate Updated" },
    { keys: ["C"], label: "Open calculator (single agent row)" },
    { keys: ["I"], label: "Open import drawer" },
    { keys: ["Esc"], label: "Close drawer / clear selection" },
    { keys: ["?"], label: "Toggle this panel" },
  ];
  return (
    <>
      <div className="scrim" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label="Keyboard shortcuts" style={{ width: 420 }}>
        <div className="drawer-head">
          <div>
            <div className="drawer-title">Keyboard shortcuts</div>
            <div className="drawer-sub">Get through batches without the mouse.</div>
          </div>
          <button className="btn btn-icon btn-ghost" onClick={onClose}><Icons.X /></button>
        </div>
        <div className="drawer-body">
          {items.map((s) => (
            <div key={s.label} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--border)", fontSize: 13 }}>
              <span>{s.label}</span>
              <span style={{ display: "flex", gap: 4 }}>
                {s.keys.map((k, i) => <Kbd key={i} k={k} />)}
              </span>
            </div>
          ))}
        </div>
      </aside>
    </>
  );
}

Object.assign(window, { CalculatorDrawer, UploadDrawer, ImportDrawer, ShortcutsDrawer });
