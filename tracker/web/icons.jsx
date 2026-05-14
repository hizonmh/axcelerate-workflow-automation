/* global React */
// Icon set — line icons, 16px default, currentColor.
// One file so every component can grab consistent icons.

const Icon = ({ d, size = 16, fill = "none", stroke = "currentColor", sw = 1.6, children, ...rest }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 16 16"
    fill={fill}
    stroke={stroke}
    strokeWidth={sw}
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    {...rest}
  >
    {d ? <path d={d} /> : children}
  </svg>
);

const Icons = {
  Search: (p) => <Icon size={14} {...p}><circle cx="7" cy="7" r="4" /><path d="m13 13-2.5-2.5" /></Icon>,
  Check: (p) => <Icon {...p} sw={2}><path d="m3.5 8 3 3 6-6" /></Icon>,
  Dash:  (p) => <Icon {...p} sw={2}><path d="M4 8h8" /></Icon>,
  X:     (p) => <Icon {...p}><path d="m4 4 8 8M12 4l-8 8" /></Icon>,
  Plus:  (p) => <Icon {...p}><path d="M8 3v10M3 8h10" /></Icon>,
  ChevDown: (p) => <Icon {...p}><path d="m4 6 4 4 4-4" /></Icon>,
  ChevRight: (p) => <Icon {...p}><path d="m6 4 4 4-4 4" /></Icon>,
  Upload: (p) => <Icon {...p}><path d="M8 11V3M5 6l3-3 3 3M3 12v1.5A.5.5 0 0 0 3.5 14h9a.5.5 0 0 0 .5-.5V12" /></Icon>,
  Download: (p) => <Icon {...p}><path d="M8 3v8M5 8l3 3 3-3M3 12v1.5A.5.5 0 0 0 3.5 14h9a.5.5 0 0 0 .5-.5V12" /></Icon>,
  Calculator: (p) => <Icon {...p}><rect x="3" y="2" width="10" height="12" rx="1.5" /><path d="M5 5h6M5 8h1M7.5 8h1M10 8h1M5 11h1M7.5 11h1M10 11h1" /></Icon>,
  Bolt: (p) => <Icon {...p} fill="currentColor" stroke="none"><path d="M9 1.5 3.5 9h3L7 14.5 12.5 7h-3z" /></Icon>,
  Wallet: (p) => <Icon {...p}><rect x="2" y="4" width="12" height="9" rx="1.5" /><path d="M11 8.5h2" /></Icon>,
  Bank: (p) => <Icon {...p}><path d="M2 13h12M3 6.5h10M4 7v5M6.5 7v5M9.5 7v5M12 7v5M8 1.5 2.5 5h11z" /></Icon>,
  User: (p) => <Icon {...p}><circle cx="8" cy="5.5" r="2.5" /><path d="M3.5 13.5c.5-2.2 2.4-3.5 4.5-3.5s4 1.3 4.5 3.5" /></Icon>,
  UserAdd: (p) => <Icon {...p}><circle cx="6" cy="5.5" r="2.5" /><path d="M2 13.5c.4-2 2.1-3.5 4-3.5s3.6 1.5 4 3.5M12 5v4M10 7h4" /></Icon>,
  Edit: (p) => <Icon {...p}><path d="M11 2.5 13.5 5 6 12.5l-3 .5.5-3z" /></Icon>,
  Filter: (p) => <Icon {...p}><path d="M2 3h12L9.5 8.5v4l-3 1.5v-5.5z" /></Icon>,
  Sparkle: (p) => <Icon {...p}><path d="M8 2v3.5M8 10.5V14M2 8h3.5M10.5 8H14M3.5 3.5l2.5 2.5M10 10l2.5 2.5M3.5 12.5 6 10M10 6l2.5-2.5" /></Icon>,
  Warning: (p) => <Icon {...p}><path d="M8 2 14.5 13h-13zM8 6v3.5M8 11.5v.5" /></Icon>,
  Eye:   (p) => <Icon {...p}><path d="M1.5 8s2.5-4.5 6.5-4.5S14.5 8 14.5 8 12 12.5 8 12.5 1.5 8 1.5 8z" /><circle cx="8" cy="8" r="1.8" /></Icon>,
  Dot: (p) => <Icon {...p} fill="currentColor" stroke="none"><circle cx="8" cy="8" r="2.5" /></Icon>,
  Doc: (p) => <Icon {...p}><path d="M4 1.5h5L12 4.5V14a.5.5 0 0 1-.5.5h-7a.5.5 0 0 1-.5-.5V2a.5.5 0 0 1 .5-.5z" /><path d="M9 1.5V4.5h3" /></Icon>,
  Refresh: (p) => <Icon {...p}><path d="M13 7a5 5 0 1 1-1.5-3.5M13 2v3h-3" /></Icon>,
  Cog: (p) => <Icon {...p}><circle cx="8" cy="8" r="2" /><path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.4 3.4 4.8 4.8M11.2 11.2l1.4 1.4M3.4 12.6 4.8 11.2M11.2 4.8l1.4-1.4" /></Icon>,
  Keyboard: (p) => <Icon {...p}><rect x="1.5" y="4" width="13" height="8" rx="1" /><path d="M4 7h.5M6 7h.5M8 7h.5M10 7h.5M12 7h.5M4 9.5h8" /></Icon>,
  Cmd: (p) => <Icon {...p}><path d="M4 6a1.5 1.5 0 1 1 1.5-1.5V11.5A1.5 1.5 0 1 1 4 10M12 6a1.5 1.5 0 1 0-1.5-1.5V11.5a1.5 1.5 0 1 0 1.5-1.5M5.5 4.5h5M5.5 11.5h5M5.5 6h5v4h-5z" /></Icon>,
  Pin: (p) => <Icon {...p}><path d="M8 1.5v5M5 6.5h6L9.5 9.5h-3z M8 9.5v5" /></Icon>,
  Arrow: (p) => <Icon {...p}><path d="M3 8h10M9 4l4 4-4 4" /></Icon>,
};

// ---- Small atoms ----
const Pill = ({ status }) => {
  const s = window.STATUSES.find((x) => x.key === status);
  if (!s) return null;
  return <span className={`pill ${s.cls}`}>{s.label}</span>;
};

const Kbd = ({ k }) => <span className="kbd">{k}</span>;

const Checkbox = ({ checked, indeterminate, onClick, label }) => {
  const cls = indeterminate ? "checkbox indet" : checked ? "checkbox checked" : "checkbox";
  return (
    <div className={cls} onClick={onClick} role="checkbox" aria-checked={checked} aria-label={label}>
      {indeterminate ? <Icons.Dash size={11} /> : checked ? <Icons.Check size={11} /> : null}
    </div>
  );
};

// Format currency consistently
const fmtMoney = (n) => {
  if (n == null) return "—";
  const s = Math.abs(n).toLocaleString("en-AU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return (n < 0 ? "−$" : "$") + s;
};
const fmtMoneyPlain = (n) =>
  "$" + Math.abs(n).toLocaleString("en-AU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const fmtDate = (iso) => {
  const d = new Date(iso + "T00:00:00");
  const now = new Date();
  const sameYear = d.getFullYear() === now.getFullYear();
  return d.toLocaleDateString("en-AU", {
    day: "2-digit",
    month: "short",
    year: sameYear ? undefined : "2-digit",
  });
};
const fmtDateFull = (iso) => {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-AU", { day: "2-digit", month: "short", year: "numeric" });
};

const sourceCls = (s) =>
  s === "Bank CSV" ? "bank" : s === "Xero" ? "xero" : "ezi";

const methodIcon = (m) => {
  switch (m) {
    case "Direct Deposit": return <Icons.Bank size={12} />;
    case "Agent Deduction": return <Icons.User size={12} />;
    case "Direct Debit": return <Icons.Refresh size={12} />;
    case "Stripe": return <Icons.Bolt size={11} />;
    case "Internal Transfer": return <Icons.Arrow size={11} />;
    default: return <Icons.Wallet size={12} />;
  }
};

// Expose
Object.assign(window, {
  Icon, Icons, Pill, Kbd, Checkbox, fmtMoney, fmtMoneyPlain, fmtDate, fmtDateFull, sourceCls, methodIcon
});
