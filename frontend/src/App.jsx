import { useState, useRef, useCallback, useEffect } from "react";
import axios from "axios";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const api = axios.create({ baseURL: API });

const css = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=Geist:wght@300;400;500;600;700&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:#F7F6F3; --surface:#FFFFFF; --surface2:#F2F1EE;
    --border:#E4E2DC; --border2:#D0CEC6;
    --ink:#1A1916; --ink2:#6B6860; --ink3:#A8A59E;
    --green:#1E7C4D; --green-bg:#EDFAF3;
    --red:#C0392B; --red-bg:#FDF2F0;
    --amber:#B45309; --amber-bg:#FEF9EC;
    --blue:#1D4ED8; --blue-bg:#EFF6FF;
    --indigo:#4338CA; --indigo-bg:#EEF2FF;
    --r:10px; --r2:6px;
    --sh:0 1px 3px rgba(0,0,0,.06),0 4px 16px rgba(0,0,0,.04);
    --sh2:0 4px 24px rgba(0,0,0,.10),0 1px 4px rgba(0,0,0,.06);
    --font:'Geist',sans-serif; --mono:'DM Mono',monospace; --serif:'DM Serif Display',serif;
  }
  body { font-family:var(--font); background:var(--bg); color:var(--ink); -webkit-font-smoothing:antialiased; }
  .shell { display:flex; min-height:100vh; }
  .main  { flex:1; min-width:0; }

  /* SIDEBAR */
  .sidebar { width:224px; flex-shrink:0; background:var(--surface); border-right:1px solid var(--border); display:flex; flex-direction:column; padding:24px 12px; position:sticky; top:0; height:100vh; overflow-y:auto; }
  .logo { font-family:var(--serif); font-size:21px; line-height:1.2; padding:0 8px 22px; border-bottom:1px solid var(--border); margin-bottom:16px; }
  .logo em { font-style:italic; color:var(--ink2); }
  .nav-section { font-size:10.5px; font-weight:700; color:var(--ink3); letter-spacing:.09em; text-transform:uppercase; padding:14px 10px 5px; }
  .nav-item { display:flex; align-items:center; gap:10px; padding:9px 10px; border-radius:var(--r2); font-size:13.5px; font-weight:500; cursor:pointer; color:var(--ink2); transition:all .15s; border:none; background:none; width:100%; text-align:left; margin-bottom:2px; }
  .nav-item:hover  { background:var(--surface2); color:var(--ink); }
  .nav-item.active { background:var(--ink); color:#fff; }
  .nav-item .icon  { font-size:15px; width:20px; text-align:center; flex-shrink:0; }
  .sidebar-footer { margin-top:auto; padding:16px 10px 0; border-top:1px solid var(--border); font-size:12px; color:var(--ink2); }
  .sidebar-footer strong { display:block; font-size:14px; color:var(--ink); margin-bottom:2px; }
  .db-badge { margin-top:10px; padding:8px 10px; border-radius:var(--r2); background:var(--green-bg); border:1px solid rgba(30,124,77,.2); font-size:11px; color:var(--green); font-weight:600; }
  .db-badge.err { background:var(--red-bg); border-color:rgba(192,57,43,.2); color:var(--red); }
  .db-badge.wait { background:var(--amber-bg); border-color:rgba(180,83,9,.2); color:var(--amber); }

  /* TOPBAR */
  .topbar { background:var(--surface); border-bottom:1px solid var(--border); padding:16px 32px; display:flex; justify-content:space-between; align-items:center; position:sticky; top:0; z-index:20; }
  .topbar-title { font-size:17px; font-weight:600; }
  .topbar-sub   { font-size:12.5px; color:var(--ink2); margin-top:1px; }

  /* BUTTONS */
  .btn { display:inline-flex; align-items:center; gap:6px; font-family:var(--font); font-size:13px; font-weight:500; padding:8px 14px; border-radius:var(--r2); border:1px solid var(--border); cursor:pointer; background:var(--surface); color:var(--ink); transition:all .15s; }
  .btn:hover        { background:var(--surface2); border-color:var(--border2); }
  .btn:disabled     { opacity:.45; cursor:not-allowed; }
  .btn-primary      { background:var(--ink); color:#fff; border-color:var(--ink); }
  .btn-primary:hover:not(:disabled) { background:#2D2C28; }
  .btn-sm           { padding:5px 10px; font-size:12px; }
  .btn-ghost        { border-color:transparent; }
  .btn-ghost:hover  { background:var(--surface2); border-color:var(--border); }
  .btn-indigo       { background:var(--indigo); color:#fff; border-color:var(--indigo); }
  .btn-indigo:hover { background:#3730A3; }

  /* PAGE */
  .page           { padding:32px; }
  .page-header    { margin-bottom:26px; }
  .page-header h1 { font-family:var(--serif); font-size:27px; font-weight:400; margin-bottom:3px; }
  .page-header p  { font-size:13.5px; color:var(--ink2); }

  /* KPI */
  .kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:13px; margin-bottom:26px; }
  .kpi      { background:var(--surface); border:1px solid var(--border); border-radius:var(--r); padding:18px 20px; box-shadow:var(--sh); }
  .kpi-label { font-size:11.5px; font-weight:600; color:var(--ink2); text-transform:uppercase; letter-spacing:.06em; margin-bottom:7px; }
  .kpi-value { font-size:26px; font-weight:700; letter-spacing:-.02em; line-height:1; }
  .kpi-value.green { color:var(--green); }
  .kpi-value.red   { color:var(--red);   }
  .kpi-value.amber { color:var(--amber); }
  .kpi-sub   { font-size:11.5px; color:var(--ink3); margin-top:5px; }
  .kpi-pill  { display:inline-flex; align-items:center; gap:4px; font-size:11px; font-weight:700; padding:2px 8px; border-radius:99px; margin-top:7px; }
  .pill-green  { background:var(--green-bg);  color:var(--green);  }
  .pill-red    { background:var(--red-bg);    color:var(--red);    }
  .pill-amber  { background:var(--amber-bg);  color:var(--amber);  }

  /* CARDS */
  .card        { background:var(--surface); border:1px solid var(--border); border-radius:var(--r); box-shadow:var(--sh); }
  .card-header { display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid var(--border); }
  .card-header h3 { font-size:14.5px; font-weight:600; }
  .card-body   { padding:20px; }
  .grid-2      { display:grid; grid-template-columns:1fr 1fr; gap:13px; margin-bottom:13px; }

  /* TABLE */
  .table-wrap { overflow-x:auto; }
  table       { width:100%; border-collapse:collapse; font-size:13px; }
  thead th    { text-align:left; font-size:10.5px; font-weight:700; color:var(--ink3); text-transform:uppercase; letter-spacing:.07em; padding:9px 15px; border-bottom:1px solid var(--border); background:var(--surface2); white-space:nowrap; }
  tbody td    { padding:12px 15px; border-bottom:1px solid var(--border); vertical-align:middle; }
  tbody tr:last-child td { border-bottom:none; }
  tbody tr:hover { background:var(--surface2); }
  tfoot td    { padding:11px 15px; background:var(--surface2); border-top:2px solid var(--border2); font-weight:600; font-size:13px; }

  .mono      { font-family:var(--mono); font-size:12.5px; }
  .badge     { display:inline-flex; align-items:center; padding:3px 9px; border-radius:99px; font-size:11px; font-weight:600; gap:5px; }
  .badge-green  { background:var(--green-bg); color:var(--green); }
  .badge-amber  { background:var(--amber-bg); color:var(--amber); }
  .badge-blue   { background:var(--blue-bg);  color:var(--blue);  }
  .badge-red    { background:var(--red-bg);   color:var(--red);   }
  .rate-tag  { display:inline-flex; align-items:center; justify-content:center; background:var(--surface2); border:1px solid var(--border); border-radius:4px; padding:2px 7px; font-family:var(--mono); font-size:11.5px; font-weight:500; }

  /* DRAG & DROP */
  .dropzone { border:2px dashed var(--border2); border-radius:var(--r); background:var(--surface); padding:32px 24px; text-align:center; cursor:pointer; transition:all .2s; margin-bottom:20px; }
  .dropzone:hover, .dropzone.over { border-color:var(--indigo); background:var(--indigo-bg); box-shadow:0 0 0 4px rgba(67,56,202,.08); }
  .dropzone.over { transform:scale(1.003); }
  .dz-icon { width:50px; height:50px; border-radius:12px; background:var(--indigo-bg); border:1px solid rgba(67,56,202,.18); display:flex; align-items:center; justify-content:center; margin:0 auto 12px; font-size:22px; transition:transform .2s; }
  .dropzone.over .dz-icon { transform:scale(1.14) rotate(-6deg); }
  .dropzone h3 { font-size:15px; font-weight:600; margin-bottom:4px; }
  .dropzone p  { font-size:13px; color:var(--ink2); margin-bottom:12px; }
  .dz-formats  { display:flex; gap:6px; justify-content:center; flex-wrap:wrap; }
  .dz-formats span { font-size:11px; font-weight:600; padding:3px 8px; border-radius:4px; background:var(--surface2); border:1px solid var(--border); color:var(--ink2); }

  /* FILE PANEL */
  .file-panel { background:var(--surface); border:1px solid var(--border); border-radius:var(--r); overflow:hidden; margin-bottom:14px; box-shadow:var(--sh); animation:slideIn .25s ease; }
  @keyframes slideIn { from{opacity:0;transform:translateY(-6px)} to{opacity:1;transform:translateY(0)} }
  .fp-header { display:flex; align-items:center; justify-content:space-between; padding:13px 20px; background:var(--surface2); border-bottom:1px solid var(--border); }
  .fp-header-left { display:flex; align-items:center; gap:10px; }
  .fp-icon { font-size:22px; }
  .fp-name { font-size:13.5px; font-weight:600; }
  .fp-hint { font-size:11.5px; color:var(--ink2); margin-top:1px; }
  .fp-body { padding:20px; }
  .fp-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; margin-bottom:16px; }
  .fp-field { display:flex; flex-direction:column; gap:5px; }
  .fp-field label { font-size:11px; font-weight:700; color:var(--ink3); text-transform:uppercase; letter-spacing:.06em; }
  .fp-field input, .fp-field select { font-family:var(--font); font-size:13.5px; color:var(--ink); background:var(--surface2); border:1px solid var(--border2); border-radius:var(--r2); padding:8px 11px; transition:border-color .15s; width:100%; }
  .fp-field input:focus, .fp-field select:focus { outline:none; border-color:var(--indigo); box-shadow:0 0 0 3px rgba(67,56,202,.10); }
  .fp-computed { display:flex; margin-bottom:16px; background:var(--surface2); border-radius:var(--r2); border:1px solid var(--border); overflow:hidden; }
  .fp-computed-item { flex:1; padding:12px 16px; text-align:center; }
  .fp-computed-item+.fp-computed-item { border-left:1px solid var(--border); }
  .fp-computed-label { font-size:10.5px; font-weight:600; color:var(--ink3); text-transform:uppercase; letter-spacing:.06em; margin-bottom:4px; }
  .fp-computed-value { font-family:var(--mono); font-size:16px; font-weight:700; }
  .fp-actions { display:flex; gap:8px; justify-content:flex-end; }

  /* MODAL */
  .modal-backdrop { position:fixed; inset:0; background:rgba(0,0,0,.32); display:flex; align-items:center; justify-content:center; z-index:100; backdrop-filter:blur(3px); }
  .modal { background:var(--surface); border-radius:14px; box-shadow:var(--sh2); width:520px; max-width:95vw; max-height:90vh; overflow-y:auto; }
  .modal-header { display:flex; justify-content:space-between; align-items:center; padding:20px 24px; border-bottom:1px solid var(--border); }
  .modal-header h3 { font-size:16px; font-weight:600; }
  .modal-body  { padding:22px 24px; }
  .modal-footer { display:flex; justify-content:flex-end; gap:8px; padding:14px 24px; border-top:1px solid var(--border); }
  .form-grid   { display:grid; grid-template-columns:1fr 1fr; gap:15px; }
  .form-group  { display:flex; flex-direction:column; gap:5px; }
  .form-group.full { grid-column:1/-1; }
  label        { font-size:11.5px; font-weight:600; color:var(--ink2); }
  input, select { font-family:var(--font); font-size:13.5px; color:var(--ink); background:var(--surface2); border:1px solid var(--border2); border-radius:var(--r2); padding:8px 11px; width:100%; transition:border-color .15s; }
  input:focus, select:focus { outline:none; border-color:var(--indigo); box-shadow:0 0 0 3px rgba(67,56,202,.10); }
  .divider { border:none; border-top:1px solid var(--border); margin:18px 0; }

  /* TOGGLE */
  .toggle { display:flex; align-items:center; gap:8px; cursor:pointer; user-select:none; }
  .toggle-track { width:36px; height:20px; border-radius:10px; background:var(--border2); position:relative; transition:background .2s; flex-shrink:0; }
  .toggle-track.on { background:var(--green); }
  .toggle-thumb { width:16px; height:16px; border-radius:50%; background:white; position:absolute; top:2px; left:2px; transition:left .2s; box-shadow:0 1px 3px rgba(0,0,0,.2); }
  .toggle-track.on .toggle-thumb { left:18px; }
  .toggle-label { font-size:13px; color:var(--ink2); }

  /* ALERTS */
  .alert { display:flex; align-items:flex-start; gap:11px; padding:13px 17px; border-radius:var(--r); border:1px solid; margin-bottom:16px; font-size:13.5px; }
  .alert-amber  { background:var(--amber-bg); border-color:#FDE68A; color:var(--amber); }
  .alert-green  { background:var(--green-bg); border-color:#A7F3D0; color:var(--green); }
  .alert-red    { background:var(--red-bg);   border-color:#FECACA; color:var(--red);   }
  .alert-icon   { font-size:17px; flex-shrink:0; margin-top:1px; }

  /* PROGRESS */
  .progress     { background:var(--surface2); border-radius:99px; height:5px; overflow:hidden; }
  .progress-bar { height:100%; border-radius:99px; transition:width .4s; }
  .pg-green { background:var(--green); }
  .pg-amber { background:var(--amber); }

  /* SKELETON */
  @keyframes shimmer { from{background-position:-200% 0} to{background-position:200% 0} }
  .skeleton { background:linear-gradient(90deg,var(--surface2) 25%,var(--border) 50%,var(--surface2) 75%); background-size:200% 100%; animation:shimmer 1.4s infinite; border-radius:4px; height:16px; margin-bottom:8px; }

  /* SPINNER */
  @keyframes spin { to{transform:rotate(360deg)} }
  .spinner { display:inline-block; width:14px; height:14px; border:2px solid rgba(0,0,0,.1); border-top-color:var(--indigo); border-radius:50%; animation:spin .7s linear infinite; }

  /* EMPTY */
  .empty      { text-align:center; padding:44px 24px; color:var(--ink3); }
  .empty-icon { font-size:34px; margin-bottom:9px; }
  .empty h4   { font-size:15px; font-weight:600; color:var(--ink2); margin-bottom:3px; }
  .empty p    { font-size:13px; }

  /* TOOLTIP */
  .c-tip { background:var(--ink); color:white; border-radius:8px; padding:9px 13px; font-size:12px; }
  .c-tip-label { color:rgba(255,255,255,.55); margin-bottom:2px; }
  .c-tip-value { font-weight:700; font-size:14px; }

  /* TOAST */
  .toast { position:fixed; bottom:24px; right:24px; z-index:999; background:var(--red); color:white; padding:12px 18px; border-radius:var(--r); font-size:13.5px; box-shadow:var(--sh2); animation:slideIn .25s ease; max-width:360px; }
  .loading-center { display:flex; justify-content:center; align-items:center; padding:64px; }
`;

// ── Helpers ────────────────────────────────────────────────────────────────────
const VAT_RATES   = [0, 5.5, 10, 20];
const CATEGORIES  = ["Logiciel","Matériel","Transport","Téléphone","Fournitures","Loyer","Autre"];
const MONTHS_LONG = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"];
const MONTHS_S    = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"];

const fmt    = n => new Intl.NumberFormat("fr-FR",{style:"currency",currency:"EUR",minimumFractionDigits:2}).format(n||0);
const fmtPct = n => `${(n??0).toFixed(1)} %`;

function computeVAT(ht, rate) {
  const vatAmount = parseFloat((ht * rate / 100).toFixed(2));
  return { vatAmount, ttc: parseFloat((ht + vatAmount).toFixed(2)) };
}
function getFileIcon(name="") {
  const ext = name.split(".").pop().toLowerCase();
  return ext==="pdf" ? "📕" : ["jpg","jpeg","png","webp"].includes(ext) ? "🖼️" : "📄";
}
// ── OCR via backend FastAPI (pytesseract) ────────────────────────────────────
async function runOCR(file, onProgress) {
  onProgress && onProgress(10);

  const formData = new FormData();
  formData.append("file", file);

  onProgress && onProgress(30);

  const resp = await api.post("/api/ocr", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: e => {
      if (e.total) onProgress && onProgress(Math.round((e.loaded / e.total) * 50));
    },
  });

  onProgress && onProgress(100);

  const { fields } = resp.data;
  return {
    name:       fields.name       || "",
    number:     fields.number     || "",
    date:       fields.date       || new Date().toISOString().slice(0,10),
    amount_ht:  fields.amount_ht  || "",
    vat_rate:   fields.vat_rate   || 20,
    category:   fields.category   || "Autre",
  };
}

// ── Shared atoms ───────────────────────────────────────────────────────────────
function Toggle({ value, onChange, label }) {
  return (
    <label className="toggle" onClick={() => onChange(!value)}>
      <div className={`toggle-track ${value?"on":""}`}><div className="toggle-thumb"/></div>
      {label && <span className="toggle-label">{label}</span>}
    </label>
  );
}
function CTip({ active, payload, label }) {
  if (!active||!payload?.length) return null;
  return (
    <div className="c-tip">
      <div className="c-tip-label">{label}</div>
      {payload.map((p,i) => <div key={i} className="c-tip-value" style={{color:p.color}}>{fmt(p.value)}</div>)}
    </div>
  );
}
function Toast({ msg, onClose }) {
  useEffect(() => { const t=setTimeout(onClose,4000); return ()=>clearTimeout(t); }, []);
  return <div className="toast">⚠ {msg}</div>;
}
function SkeletonTable() {
  return (
    <div style={{padding:24}}>
      {[1,2,3].map(i=><div key={i} className="skeleton" style={{height:40,marginBottom:6}}/>)}
    </div>
  );
}

// ── DropZone ───────────────────────────────────────────────────────────────────
function DropZone({ onFiles, label }) {
  const [over, setOver] = useState(false);
  const ref = useRef();
  const pick = useCallback(files => {
    const v = files.filter(f => /\.(pdf|jpe?g|png|webp)$/i.test(f.name));
    if (v.length) onFiles(v);
  }, [onFiles]);
  return (
    <div
      className={`dropzone${over?" over":""}`}
      onClick={() => ref.current?.click()}
      onDragOver={e => { e.preventDefault(); setOver(true); }}
      onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget)) setOver(false); }}
      onDrop={e => { e.preventDefault(); setOver(false); pick(Array.from(e.dataTransfer.files)); }}
    >
      <input ref={ref} type="file" multiple hidden accept=".pdf,.jpg,.jpeg,.png,.webp"
        onChange={e => { pick(Array.from(e.target.files)); e.target.value=""; }}/>
      <div className="dz-icon">📂</div>
      <h3>{label||"Déposer un fichier"}</h3>
      <p>Glissez-déposez ou cliquez — un formulaire s'ouvre pour chaque fichier</p>
      <div className="dz-formats"><span>PDF</span><span>JPG</span><span>PNG</span><span>WEBP</span></div>
    </div>
  );
}

// ── FileEntryPanel — avec OCR Tesseract.js ─────────────────────────────────────
function FileEntryPanel({ file, type, onConfirm, onDiscard, saving }) {
  const isInvoice = type==="invoice";
  const today = new Date().toISOString().slice(0,10);

  const [form, setForm] = useState({
    client:"", supplier:"", number:"", date:today,
    desc:"", amount_ht:"", vat_rate:20, is_paid:false, category:"Autre",
  });
  const [ocr, setOcr] = useState({ status:"idle", progress:0, error:null });
  // status: idle | loading | done | error

  const set = (k,v) => setForm(f=>({...f,[k]:v}));
  const ht   = parseFloat(form.amount_ht)||0;
  const rate = parseFloat(form.vat_rate)||0;
  const { vatAmount, ttc } = computeVAT(ht, rate);
  const ck = isInvoice ? "client" : "supplier";

  // Lance l'OCR dès que le composant est monté
  useEffect(() => {
    let cancelled = false;
    setOcr({ status:"loading", progress:0, error:null });

    (async () => {
      try {
        const extracted = await runOCR(file, pct => {
          if (!cancelled) setOcr(o => ({ ...o, progress: pct }));
        });

        if (cancelled) return;

        setForm(f => ({
          ...f,
          [ck]:       extracted.name       || f[ck],
          number:     extracted.number     || f.number,
          date:       extracted.date       || f.date,
          amount_ht:  extracted.amount_ht  !== "" ? extracted.amount_ht : f.amount_ht,
          vat_rate:   extracted.vat_rate   || f.vat_rate,
          category:   extracted.category   || f.category,
        }));

        setOcr({ status:"done", progress:100, error:null });
      } catch (err) {
        if (!cancelled) setOcr({ status:"error", progress:0, error: err.message });
      }
    })();

    return () => { cancelled = true; };
  }, []);

  const ocrBadge = () => {
    if (ocr.status === "loading") return (
      <div style={{display:"flex",alignItems:"center",gap:8,fontSize:12,color:"var(--indigo)",background:"var(--indigo-bg)",padding:"6px 12px",borderRadius:"var(--r2)",border:"1px solid rgba(67,56,202,.18)"}}>
        <span className="spinner"/>
        Analyse OCR en cours… {ocr.progress > 0 ? `${ocr.progress}%` : ""}
      </div>
    );
    if (ocr.status === "done") return (
      <div style={{display:"flex",alignItems:"center",gap:6,fontSize:12,color:"var(--green)",background:"var(--green-bg)",padding:"6px 12px",borderRadius:"var(--r2)",border:"1px solid rgba(30,124,77,.18)"}}>
        ✓ OCR terminé — vérifiez et corrigez si besoin
      </div>
    );
    if (ocr.status === "error") return (
      <div style={{display:"flex",alignItems:"center",gap:6,fontSize:12,color:"var(--amber)",background:"var(--amber-bg)",padding:"6px 12px",borderRadius:"var(--r2)",border:"1px solid rgba(180,83,9,.18)"}}>
        ⚠ OCR indisponible — saisie manuelle
      </div>
    );
    return null;
  };

  return (
    <div className="file-panel">
      <div className="fp-header">
        <div className="fp-header-left">
          <span className="fp-icon">{getFileIcon(file.name)}</span>
          <div>
            <div className="fp-name">{file.name}</div>
            <div className="fp-hint">Tesseract OCR — extraction automatique des champs</div>
          </div>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={onDiscard}>✕</button>
      </div>
      <div className="fp-body">
        {/* Bandeau statut OCR */}
        <div style={{marginBottom:14}}>{ocrBadge()}</div>

        <div className="fp-grid">
          <div className="fp-field">
            <label>{isInvoice?"Client":"Fournisseur"}</label>
            <input value={form[ck]} onChange={e=>set(ck,e.target.value)}
              placeholder={ocr.status==="loading"?"Extraction…":isInvoice?"Nom du client":"Nom du fournisseur"}
              disabled={ocr.status==="loading"}/>
          </div>
          <div className="fp-field">
            <label>N° Facture</label>
            <input value={form.number} onChange={e=>set("number",e.target.value)}
              placeholder={ocr.status==="loading"?"Extraction…":"FA-2025-001"}
              disabled={ocr.status==="loading"}/>
          </div>
          <div className="fp-field">
            <label>Date</label>
            <input type="date" value={form.date} onChange={e=>set("date",e.target.value)}
              disabled={ocr.status==="loading"}/>
          </div>
          <div className="fp-field">
            <label>Taux TVA</label>
            <select value={form.vat_rate} onChange={e=>set("vat_rate",Number(e.target.value))}
              disabled={ocr.status==="loading"}>
              {VAT_RATES.map(r=><option key={r} value={r}>{r}%{r===20?" (std)":r===10?" (inter.)":r===5.5?" (réduit)":r===0?" (exo.)":""}</option>)}
            </select>
          </div>
          <div className="fp-field">
            <label>Montant HT (€)</label>
            <input type="number" step="0.01" min="0" value={form.amount_ht}
              onChange={e=>set("amount_ht",e.target.value)}
              placeholder={ocr.status==="loading"?"Extraction…":"0.00"}
              disabled={ocr.status==="loading"}/>
          </div>
          <div className="fp-field">
            <label>Description</label>
            <input value={form.desc} onChange={e=>set("desc",e.target.value)} placeholder="Objet (optionnel)"/>
          </div>
          {!isInvoice&&(
            <div className="fp-field">
              <label>Catégorie</label>
              <select value={form.category} onChange={e=>set("category",e.target.value)}>
                {CATEGORIES.map(c=><option key={c}>{c}</option>)}
              </select>
            </div>
          )}
          {isInvoice&&(
            <div className="fp-field" style={{justifyContent:"flex-end"}}>
              <label>Statut</label>
              <Toggle value={form.is_paid} onChange={v=>set("is_paid",v)} label="Marquer payée"/>
            </div>
          )}
        </div>
        <div className="fp-computed">
          <div className="fp-computed-item">
            <div className="fp-computed-label">HT</div>
            <div className="fp-computed-value">{fmt(ht)}</div>
          </div>
          <div className="fp-computed-item">
            <div className="fp-computed-label">TVA {rate}%</div>
            <div className="fp-computed-value" style={{color:isInvoice?"var(--green)":"var(--red)"}}>{fmt(vatAmount)}</div>
          </div>
          <div className="fp-computed-item">
            <div className="fp-computed-label">TTC</div>
            <div className="fp-computed-value">{fmt(ttc)}</div>
          </div>
        </div>
        <div className="fp-actions">
          <button className="btn btn-sm" onClick={onDiscard}>Ignorer</button>
          <button className="btn btn-indigo btn-sm"
            disabled={ht<=0 || saving || ocr.status==="loading"}
            onClick={()=>onConfirm({...form,amount_ht:ht,vat_rate:rate})}>
            {saving?<span className="spinner"/>:"✓"}&nbsp;Enregistrer en base
          </button>
        </div>
      </div>
    </div>
  );
}

// ── EntryModal ─────────────────────────────────────────────────────────────────
function EntryModal({ type, onClose, onSave }) {
  const isInvoice = type==="invoice";
  const [form,setForm] = useState({date:new Date().toISOString().slice(0,10),client:"",supplier:"",number:"",desc:"",amount_ht:"",vat_rate:20,is_paid:false,category:"Logiciel"});
  const [saving,setSaving] = useState(false);
  const ht=parseFloat(form.amount_ht)||0, rate=parseFloat(form.vat_rate)||0;
  const { vatAmount, ttc } = computeVAT(ht,rate);
  const set=(k,v)=>setForm(f=>({...f,[k]:v}));
  const handleSave=async()=>{
    if(ht<=0) return;
    setSaving(true);
    await onSave({...form,amount_ht:ht,vat_rate:rate});
    setSaving(false);
    onClose();
  };
  return (
    <div className="modal-backdrop" onClick={e=>e.target===e.currentTarget&&onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3>{isInvoice?"➕ Nouvelle facture client":"➕ Nouvelle dépense"}</h3>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div className="form-grid">
            <div className="form-group"><label>Date</label><input type="date" value={form.date} onChange={e=>set("date",e.target.value)}/></div>
            <div className="form-group"><label>N° Facture</label><input placeholder="FA-2025-001" value={form.number} onChange={e=>set("number",e.target.value)}/></div>
            <div className="form-group full">
              <label>{isInvoice?"Client":"Fournisseur"}</label>
              <input placeholder={isInvoice?"Nom du client":"Nom du fournisseur"}
                value={isInvoice?form.client:form.supplier}
                onChange={e=>set(isInvoice?"client":"supplier",e.target.value)}/>
            </div>
            <div className="form-group full"><label>Description</label><input placeholder="Description" value={form.desc} onChange={e=>set("desc",e.target.value)}/></div>
            {!isInvoice&&<div className="form-group full"><label>Catégorie</label><select value={form.category} onChange={e=>set("category",e.target.value)}>{CATEGORIES.map(c=><option key={c}>{c}</option>)}</select></div>}
            <div className="form-group"><label>Montant HT (€)</label><input type="number" step="0.01" min="0" placeholder="0.00" value={form.amount_ht} onChange={e=>set("amount_ht",e.target.value)}/></div>
            <div className="form-group"><label>Taux TVA</label><select value={form.vat_rate} onChange={e=>set("vat_rate",e.target.value)}>{VAT_RATES.map(r=><option key={r} value={r}>{r}%</option>)}</select></div>
          </div>
          <hr className="divider"/>
          <div style={{background:"var(--surface2)",borderRadius:"var(--r)",padding:"13px 17px"}}>
            <div style={{display:"flex",justifyContent:"space-between",fontSize:13,color:"var(--ink2)",marginBottom:5}}><span>HT</span><span className="mono">{fmt(ht)}</span></div>
            <div style={{display:"flex",justifyContent:"space-between",fontSize:13,color:"var(--ink2)",marginBottom:5}}><span>TVA {rate}%</span><span className="mono" style={{color:isInvoice?"var(--green)":"var(--red)"}}>{fmt(vatAmount)}</span></div>
            <div style={{display:"flex",justifyContent:"space-between",fontSize:15,fontWeight:600,borderTop:"1px solid var(--border)",paddingTop:8}}><span>TTC</span><span className="mono">{fmt(ttc)}</span></div>
          </div>
          {isInvoice&&<div style={{marginTop:13}}><Toggle value={form.is_paid} onChange={v=>set("is_paid",v)} label="Marquer comme payée"/></div>}
        </div>
        <div className="modal-footer">
          <button className="btn" onClick={onClose}>Annuler</button>
          <button className="btn btn-primary" disabled={ht<=0||saving} onClick={handleSave}>
            {saving&&<span className="spinner"/>} Enregistrer
          </button>
        </div>
      </div>
    </div>
  );
}

// ── InvoicesPage ───────────────────────────────────────────────────────────────
function InvoicesPage({ showToast }) {
  const [invoices,  setInvoices]  = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [pending,   setPending]   = useState([]);
  const [saving,    setSaving]    = useState({});

  const load = async () => {
    try { setLoading(true); const {data}=await api.get("/api/invoices"); setInvoices(data); }
    catch { showToast("Erreur chargement factures"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const enriched  = invoices.map(inv => ({...inv,...computeVAT(inv.amount_ht,inv.vat_rate)}));
  const totalHT   = enriched.reduce((s,i)=>s+i.amount_ht,0);
  const totalVAT  = enriched.reduce((s,i)=>s+i.vatAmount,0);
  const totalTTC  = enriched.reduce((s,i)=>s+i.ttc,0);
  const totalPaid = enriched.filter(i=>i.is_paid).reduce((s,i)=>s+i.ttc,0);

  const onFiles = useCallback(files => {
    setPending(p=>[...p,...files.map(f=>({id:`${Date.now()}-${Math.random()}`,file:f}))]);
  },[]);

  const confirmFile = async (panelId, formData) => {
    setSaving(s=>({...s,[panelId]:true}));
    try { await api.post("/api/invoices",formData); setPending(p=>p.filter(x=>x.id!==panelId)); await load(); }
    catch { showToast("Erreur sauvegarde facture"); }
    finally { setSaving(s=>({...s,[panelId]:false})); }
  };

  const saveManual = async (data) => {
    try { await api.post("/api/invoices",data); await load(); }
    catch { showToast("Erreur sauvegarde"); }
  };

  const togglePaid = async (inv) => {
    try { await api.put(`/api/invoices/${inv.id}`,{is_paid:!inv.is_paid}); await load(); }
    catch { showToast("Erreur mise à jour"); }
  };

  const deleteInv = async (id) => {
    if (!confirm("Supprimer cette facture ?")) return;
    try { await api.delete(`/api/invoices/${id}`); await load(); }
    catch { showToast("Erreur suppression"); }
  };

  const exportCSV = () => {
    const rows=[["Date","Client","N°","Description","HT","Taux TVA","TVA","TTC","Statut"],
      ...enriched.map(i=>[i.date,i.client,i.number,i.desc,i.amount_ht,`${i.vat_rate}%`,i.vatAmount,i.ttc,i.is_paid?"Payée":"En attente"])];
    const a=document.createElement("a");
    a.href=URL.createObjectURL(new Blob(["\uFEFF"+rows.map(r=>r.join(";")).join("\n")],{type:"text/csv;charset=utf-8"}));
    a.download="factures.csv"; a.click();
  };

  return (
    <div className="page">
      {showModal&&<EntryModal type="invoice" onClose={()=>setShowModal(false)} onSave={saveManual}/>}
      <div className="page-header"><h1>Factures clients</h1><p>Déposez vos fichiers — données persistées en PostgreSQL</p></div>
      <DropZone onFiles={onFiles} label="Déposer une facture client (PDF, image)"/>
      {pending.map(item=>(
        <FileEntryPanel key={item.id} file={item.file} type="invoice" saving={!!saving[item.id]}
          onConfirm={data=>confirmFile(item.id,data)}
          onDiscard={()=>setPending(p=>p.filter(x=>x.id!==item.id))}/>
      ))}
      <div className="kpi-grid">
        <div className="kpi"><div className="kpi-label">CA Total HT</div><div className="kpi-value">{fmt(totalHT)}</div></div>
        <div className="kpi"><div className="kpi-label">TVA collectée</div><div className="kpi-value green">{fmt(totalVAT)}</div></div>
        <div className="kpi"><div className="kpi-label">Total TTC</div><div className="kpi-value">{fmt(totalTTC)}</div></div>
        <div className="kpi"><div className="kpi-label">Encaissé</div><div className="kpi-value green">{fmt(totalPaid)}</div><div className="kpi-sub">{enriched.filter(i=>i.is_paid).length} payées</div></div>
      </div>
      {/* ── CA par client ─────────────────────────────────────────────────── */}
      {enriched.length > 0 && (() => {
        const byClient = enriched.reduce((acc, inv) => {
          acc[inv.client] = (acc[inv.client] || 0) + inv.amount_ht;
          return acc;
        }, {});
        const total = Object.values(byClient).reduce((s, v) => s + v, 0);
        const data  = Object.entries(byClient)
          .map(([name, value]) => ({ name, value }))
          .sort((a, b) => b.value - a.value);
        const COLORS = ["#1A1916","#1E7C4D","#B45309","#1D4ED8","#4338CA","#C0392B","#A8A59E"];
        return (
          <div className="grid-2" style={{marginBottom:13}}>
            <div className="card">
              <div className="card-header"><h3>CA par client</h3></div>
              <div className="card-body">
                <ResponsiveContainer width="100%" height={210}>
                  <PieChart>
                    <Pie data={data} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" paddingAngle={2}>
                      {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]}/>)}
                    </Pie>
                    <Tooltip formatter={v => fmt(v)}/>
                    <Legend formatter={v => <span style={{fontSize:12,color:"var(--ink2)"}}>{v}</span>}/>
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="card">
              <div className="card-header"><h3>Répartition clients</h3></div>
              <div className="table-wrap">
                <table>
                  <thead><tr><th></th><th>Client</th><th>CA HT</th><th>Part</th></tr></thead>
                  <tbody>
                    {data.map((row, i) => (
                      <tr key={row.name}>
                        <td style={{width:14}}>
                          <div style={{width:9,height:9,borderRadius:"50%",background:COLORS[i%COLORS.length]}}/>
                        </td>
                        <td style={{fontWeight:500}}>{row.name||"—"}</td>
                        <td className="mono" style={{fontWeight:600}}>{fmt(row.value)}</td>
                        <td style={{minWidth:110}}>
                          <div style={{display:"flex",alignItems:"center",gap:7}}>
                            <div style={{flex:1,background:"var(--surface2)",borderRadius:99,height:4,overflow:"hidden"}}>
                              <div style={{width:`${(row.value/total)*100}%`,height:"100%",background:COLORS[i%COLORS.length],borderRadius:99}}/>
                            </div>
                            <span style={{fontSize:11.5,color:"var(--ink2)",minWidth:38,textAlign:"right"}}>
                              {((row.value/total)*100).toFixed(1)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr>
                      <td/>
                      <td>TOTAL</td>
                      <td className="mono">{fmt(total)}</td>
                      <td style={{fontSize:11,color:"var(--ink2)"}}>100%</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </div>
        );
      })()}

      <div className="card">
        <div className="card-header">
          <h3>Toutes les factures ({enriched.length})</h3>
          <div style={{display:"flex",gap:8}}>
            <button className="btn btn-sm" onClick={exportCSV}>⬇ CSV</button>
            <button className="btn btn-primary btn-sm" onClick={()=>setShowModal(true)}>+ Saisie manuelle</button>
          </div>
        </div>
        <div className="table-wrap">
          {loading ? <SkeletonTable/> : enriched.length===0 ? (
            <div className="empty"><div className="empty-icon">📄</div><h4>Aucune facture</h4><p>Déposez un fichier ou utilisez la saisie manuelle.</p></div>
          ) : (
            <table>
              <thead><tr><th>Date</th><th>Client</th><th>N°</th><th>Description</th><th>HT</th><th>Taux</th><th>TVA</th><th>TTC</th><th>Payée</th><th></th></tr></thead>
              <tbody>
                {enriched.map(inv=>(
                  <tr key={inv.id}>
                    <td className="mono">{inv.date}</td>
                    <td style={{fontWeight:500}}>{inv.client}</td>
                    <td className="mono" style={{color:"var(--ink2)"}}>{inv.number}</td>
                    <td style={{color:"var(--ink2)",fontSize:12.5}}>{inv.desc}</td>
                    <td className="mono">{fmt(inv.amount_ht)}</td>
                    <td><span className="rate-tag">{inv.vat_rate}%</span></td>
                    <td className="mono" style={{color:"var(--green)",fontWeight:500}}>{fmt(inv.vatAmount)}</td>
                    <td className="mono" style={{fontWeight:600}}>{fmt(inv.ttc)}</td>
                    <td><Toggle value={inv.is_paid} onChange={()=>togglePaid(inv)}/></td>
                    <td><button className="btn btn-ghost btn-sm" style={{color:"var(--red)"}} onClick={()=>deleteInv(inv.id)}>✕</button></td>
                  </tr>
                ))}
              </tbody>
              <tfoot><tr>
                <td colSpan={4} style={{color:"var(--ink2)",fontSize:11}}>TOTAL — {enriched.length} facture{enriched.length>1?"s":""}</td>
                <td className="mono">{fmt(totalHT)}</td><td/>
                <td className="mono" style={{color:"var(--green)"}}>{fmt(totalVAT)}</td>
                <td className="mono">{fmt(totalTTC)}</td><td colSpan={2}/>
              </tr></tfoot>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

// ── ExpensesPage ───────────────────────────────────────────────────────────────
function ExpensesPage({ showToast }) {
  const [expenses,  setExpenses]  = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [pending,   setPending]   = useState([]);
  const [saving,    setSaving]    = useState({});
  const COLORS = ["#1A1916","#A8A59E","#1E7C4D","#B45309","#1D4ED8","#4338CA","#C0392B"];

  const load = async () => {
    try { setLoading(true); const {data}=await api.get("/api/expenses"); setExpenses(data); }
    catch { showToast("Erreur chargement dépenses"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const enriched = expenses.map(e=>({...e,...computeVAT(e.amount_ht,e.vat_rate)}));
  const totalHT  = enriched.reduce((s,e)=>s+e.amount_ht,0);
  const totalVAT = enriched.reduce((s,e)=>s+e.vatAmount,0);
  const totalTTC = enriched.reduce((s,e)=>s+e.ttc,0);
  const byCat    = enriched.reduce((acc,e)=>{const k=e.category||"Autre";acc[k]=(acc[k]||0)+e.ttc;return acc;},{});
  const catData  = Object.entries(byCat).map(([name,value])=>({name,value}));

  const onFiles = useCallback(files => {
    setPending(p=>[...p,...files.map(f=>({id:`${Date.now()}-${Math.random()}`,file:f}))]);
  },[]);

  const confirmFile = async (panelId, data) => {
    setSaving(s=>({...s,[panelId]:true}));
    try { await api.post("/api/expenses",data); setPending(p=>p.filter(x=>x.id!==panelId)); await load(); }
    catch { showToast("Erreur sauvegarde dépense"); }
    finally { setSaving(s=>({...s,[panelId]:false})); }
  };

  const saveManual = async (data) => {
    try { await api.post("/api/expenses",data); await load(); }
    catch { showToast("Erreur sauvegarde"); }
  };

  const deleteExp = async (id) => {
    if (!confirm("Supprimer cette dépense ?")) return;
    try { await api.delete(`/api/expenses/${id}`); await load(); }
    catch { showToast("Erreur suppression"); }
  };

  const exportCSV = () => {
    const rows=[["Date","Fournisseur","N°","Catégorie","Description","HT","Taux TVA","TVA","TTC"],
      ...enriched.map(e=>[e.date,e.supplier,e.number,e.category,e.desc,e.amount_ht,`${e.vat_rate}%`,e.vatAmount,e.ttc])];
    const a=document.createElement("a");
    a.href=URL.createObjectURL(new Blob(["\uFEFF"+rows.map(r=>r.join(";")).join("\n")],{type:"text/csv;charset=utf-8"}));
    a.download="depenses.csv"; a.click();
  };

  return (
    <div className="page">
      {showModal&&<EntryModal type="expense" onClose={()=>setShowModal(false)} onSave={saveManual}/>}
      <div className="page-header"><h1>Dépenses</h1><p>Déposez vos justificatifs — TVA déductible persistée en PostgreSQL</p></div>
      <DropZone onFiles={onFiles} label="Déposer un justificatif (PDF, image)"/>
      {pending.map(item=>(
        <FileEntryPanel key={item.id} file={item.file} type="expense" saving={!!saving[item.id]}
          onConfirm={data=>confirmFile(item.id,data)}
          onDiscard={()=>setPending(p=>p.filter(x=>x.id!==item.id))}/>
      ))}
      <div className="kpi-grid">
        <div className="kpi"><div className="kpi-label">Total HT</div><div className="kpi-value">{fmt(totalHT)}</div></div>
        <div className="kpi"><div className="kpi-label">TVA déductible</div><div className="kpi-value red">{fmt(totalVAT)}</div></div>
        <div className="kpi"><div className="kpi-label">Total TTC</div><div className="kpi-value">{fmt(totalTTC)}</div></div>
        <div className="kpi"><div className="kpi-label">Économie TVA</div><div className="kpi-value green">{fmt(totalVAT)}</div><div className="kpi-sub">Récupérable</div></div>
      </div>
      <div className="grid-2">
        <div className="card">
          <div className="card-header"><h3>Par catégorie</h3></div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={catData} cx="50%" cy="50%" innerRadius={48} outerRadius={78} dataKey="value" paddingAngle={2}>
                  {catData.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
                </Pie>
                <Legend formatter={v=><span style={{fontSize:12,color:"var(--ink2)"}}>{v}</span>}/>
                <Tooltip formatter={v=>fmt(v)}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card">
          <div className="card-header"><h3>Top catégories</h3></div>
          <div className="card-body">
            {catData.sort((a,b)=>b.value-a.value).map((cat,i)=>(
              <div key={cat.name} style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:11}}>
                <div style={{display:"flex",alignItems:"center",gap:9}}>
                  <div style={{width:9,height:9,borderRadius:"50%",background:COLORS[i%COLORS.length],flexShrink:0}}/>
                  <span style={{fontSize:13}}>{cat.name}</span>
                </div>
                <span className="mono" style={{fontWeight:600}}>{fmt(cat.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="card">
        <div className="card-header">
          <h3>Toutes les dépenses ({enriched.length})</h3>
          <div style={{display:"flex",gap:8}}>
            <button className="btn btn-sm" onClick={exportCSV}>⬇ CSV</button>
            <button className="btn btn-primary btn-sm" onClick={()=>setShowModal(true)}>+ Saisie manuelle</button>
          </div>
        </div>
        <div className="table-wrap">
          {loading ? <SkeletonTable/> : enriched.length===0 ? (
            <div className="empty"><div className="empty-icon">💸</div><h4>Aucune dépense</h4><p>Déposez un justificatif ci-dessus.</p></div>
          ) : (
            <table>
              <thead><tr><th>Date</th><th>Fournisseur</th><th>N°</th><th>Catégorie</th><th>HT</th><th>Taux</th><th>TVA</th><th>TTC</th><th></th></tr></thead>
              <tbody>
                {enriched.map(exp=>(
                  <tr key={exp.id}>
                    <td className="mono">{exp.date}</td>
                    <td style={{fontWeight:500}}>{exp.supplier}</td>
                    <td className="mono" style={{color:"var(--ink2)"}}>{exp.number}</td>
                    <td><span className="badge badge-blue">{exp.category}</span></td>
                    <td className="mono">{fmt(exp.amount_ht)}</td>
                    <td><span className="rate-tag">{exp.vat_rate}%</span></td>
                    <td className="mono" style={{color:"var(--red)",fontWeight:500}}>{fmt(exp.vatAmount)}</td>
                    <td className="mono" style={{fontWeight:600}}>{fmt(exp.ttc)}</td>
                    <td><button className="btn btn-ghost btn-sm" style={{color:"var(--red)"}} onClick={()=>deleteExp(exp.id)}>✕</button></td>
                  </tr>
                ))}
              </tbody>
              <tfoot><tr>
                <td colSpan={4} style={{color:"var(--ink2)",fontSize:11}}>TOTAL</td>
                <td className="mono">{fmt(totalHT)}</td><td/>
                <td className="mono" style={{color:"var(--red)"}}>{fmt(totalVAT)}</td>
                <td className="mono">{fmt(totalTTC)}</td><td/>
              </tr></tfoot>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

// ── VATPage ────────────────────────────────────────────────────────────────────
function VATPage({ showToast }) {
  const [stats,setStats] = useState(null);
  const [loading,setLoading] = useState(true);
  useEffect(()=>{
    api.get("/api/stats/vat").then(r=>setStats(r.data))
      .catch(()=>showToast("Erreur stats TVA")).finally(()=>setLoading(false));
  },[]);

  if (loading) return <div className="page"><div className="loading-center"><div className="spinner"/></div></div>;
  if (!stats) return null;
  const {months,by_rate,total_collected:totC,total_deductible:totD,total_net:totN} = stats;

  return (
    <div className="page">
      <div className="page-header"><h1>Déclaration TVA</h1><p>TVA collectée, déductible et solde net à reverser</p></div>
      <div className="kpi-grid">
        <div className="kpi"><div className="kpi-label">TVA collectée</div><div className="kpi-value green">{fmt(totC)}</div><div className="kpi-sub">Sur ventes</div></div>
        <div className="kpi"><div className="kpi-label">TVA déductible</div><div className="kpi-value red">{fmt(totD)}</div><div className="kpi-sub">Sur achats</div></div>
        <div className="kpi">
          <div className="kpi-label">TVA nette</div>
          <div className={`kpi-value ${totN>0?"red":"green"}`}>{fmt(Math.abs(totN))}</div>
          <span className={`kpi-pill pill-${totN>0?"red":"green"}`}>{totN>0?"⬆ À reverser":"⬇ Crédit TVA"}</span>
        </div>
        <div className="kpi"><div className="kpi-label">Taux déduction</div><div className="kpi-value">{fmtPct(totC>0?(totD/totC)*100:0)}</div></div>
      </div>
      <div className="card" style={{marginBottom:13}}>
        <div className="card-header"><h3>Évolution mensuelle</h3></div>
        <div className="card-body">
          <ResponsiveContainer width="100%" height={230}>
            <AreaChart data={months.map(m=>({name:m.short,collectée:m.collected,déductible:m.deductible}))}>
              <defs>
                <linearGradient id="gc" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#1E7C4D" stopOpacity={.15}/><stop offset="95%" stopColor="#1E7C4D" stopOpacity={0}/></linearGradient>
                <linearGradient id="gd" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#C0392B" stopOpacity={.10}/><stop offset="95%" stopColor="#C0392B" stopOpacity={0}/></linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false}/>
              <XAxis dataKey="name" tick={{fontSize:12,fill:"var(--ink3)"}} axisLine={false} tickLine={false}/>
              <YAxis tick={{fontSize:11,fill:"var(--ink3)"}} axisLine={false} tickLine={false} tickFormatter={v=>`${v}€`}/>
              <Tooltip content={<CTip/>}/><Legend/>
              <Area type="monotone" dataKey="collectée"  stroke="#1E7C4D" fill="url(#gc)" strokeWidth={2} dot={{r:4,fill:"#1E7C4D"}}/>
              <Area type="monotone" dataKey="déductible" stroke="#C0392B" fill="url(#gd)" strokeWidth={2} dot={{r:4,fill:"#C0392B"}}/>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <div className="card-header"><h3>Tableau mensuel</h3></div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Mois</th><th>Collectée</th><th>Déductible</th><th>Solde</th></tr></thead>
              <tbody>
                {months.map(m=>(
                  <tr key={m.key}>
                    <td style={{fontWeight:500}}>{m.label}</td>
                    <td className="mono" style={{color:"var(--green)"}}>{fmt(m.collected)}</td>
                    <td className="mono" style={{color:"var(--red)"}}>{fmt(m.deductible)}</td>
                    <td className="mono" style={{fontWeight:600,color:m.net>0?"var(--red)":"var(--green)"}}>{fmt(Math.abs(m.net))}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot><tr>
                <td>TOTAL</td>
                <td className="mono" style={{color:"var(--green)"}}>{fmt(totC)}</td>
                <td className="mono" style={{color:"var(--red)"}}>{fmt(totD)}</td>
                <td className="mono" style={{fontWeight:700,color:totN>0?"var(--red)":"var(--green)"}}>{fmt(Math.abs(totN))}</td>
              </tr></tfoot>
            </table>
          </div>
        </div>
        <div className="card">
          <div className="card-header"><h3>Par taux de TVA</h3></div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Taux</th><th>Collectée</th><th>Déductible</th><th>Net</th></tr></thead>
              <tbody>
                {by_rate.map(r=>(
                  <tr key={r.rate}>
                    <td><span className="rate-tag">{r.rate}</span></td>
                    <td className="mono" style={{color:"var(--green)"}}>{fmt(r.collected)}</td>
                    <td className="mono" style={{color:"var(--red)"}}>{fmt(r.deductible)}</td>
                    <td className="mono" style={{fontWeight:600}}>{fmt(r.net)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card-body" style={{paddingTop:0}}>
            <div className={`alert alert-${totN>0?"red":"green"}`} style={{marginBottom:0}}>
              <span className="alert-icon">{totN>0?"📋":"💚"}</span>
              <div>
                <strong>{totN>0?"À déclarer sur votre CA3":"Crédit de TVA"}</strong>
                <div style={{fontSize:12,marginTop:2}}>{totN>0?`Montant : ${fmt(totN)}`:`Remboursement : ${fmt(Math.abs(totN))}`}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── RevenuePage ────────────────────────────────────────────────────────────────
function RevenuePage({ showToast }) {
  const [year,  setYear]  = useState(new Date().getFullYear());
  const [stats, setStats] = useState(null);
  const [loading,setLoading] = useState(true);

  useEffect(()=>{
    setLoading(true);
    api.get(`/api/stats/revenue?year=${year}`)
      .then(r=>{ setStats(r.data); if(r.data.years?.length&&!r.data.years.includes(String(year))) setYear(Number(r.data.years[0])); })
      .catch(()=>showToast("Erreur stats CA")).finally(()=>setLoading(false));
  },[year]);

  if (loading) return <div className="page"><div className="loading-center"><div className="spinner"/></div></div>;
  if (!stats) return null;
  const {monthly,total_ca,total_paid,total_vat,total_invoices,years} = stats;

  return (
    <div className="page">
      <div className="page-header">
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
          <div><h1>Chiffre d'affaires</h1><p>Analyse CA mensuelle et annuelle</p></div>
          <div style={{display:"flex",alignItems:"center",gap:8,marginTop:4}}>
            <span style={{fontSize:13,color:"var(--ink2)"}}>Année</span>
            <select value={year} onChange={e=>setYear(Number(e.target.value))} style={{width:"auto"}}>
              {(years||[]).map(y=><option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        </div>
      </div>
      <div className="kpi-grid">
        <div className="kpi"><div className="kpi-label">CA Annuel HT</div><div className="kpi-value green">{fmt(total_ca)}</div><div className="kpi-sub">{total_invoices} factures</div></div>
        <div className="kpi"><div className="kpi-label">CA Encaissé</div><div className="kpi-value green">{fmt(total_paid)}</div><div className="kpi-sub">{fmtPct(total_ca>0?(total_paid/total_ca)*100:0)}</div></div>
        <div className="kpi"><div className="kpi-label">Moyenne mensuelle</div><div className="kpi-value">{fmt(total_ca/12)}</div><div className="kpi-sub">HT / mois</div></div>
        <div className="kpi"><div className="kpi-label">TVA générée</div><div className="kpi-value">{fmt(total_vat)}</div><div className="kpi-sub">{fmtPct(total_ca>0?(total_vat/total_ca)*100:0)} du CA HT</div></div>
      </div>
      <div className="card" style={{marginBottom:13}}>
        <div className="card-header"><h3>CA mensuel {year}</h3></div>
        <div className="card-body">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={monthly.map(m=>({name:m.month,"CA HT":m.ca,"Encaissé":m.paid}))} barGap={3}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false}/>
              <XAxis dataKey="name" tick={{fontSize:12,fill:"var(--ink3)"}} axisLine={false} tickLine={false}/>
              <YAxis tick={{fontSize:11,fill:"var(--ink3)"}} axisLine={false} tickLine={false} tickFormatter={v=>`${(v/1000).toFixed(0)}k`}/>
              <Tooltip content={<CTip/>}/><Legend/>
              <Bar dataKey="CA HT"    fill="#1A1916" radius={[3,3,0,0]}/>
              <Bar dataKey="Encaissé" fill="#1E7C4D" radius={[3,3,0,0]}/>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card">
        <div className="card-header"><h3>Détail mensuel {year}</h3></div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Mois</th><th>Factures</th><th>CA HT</th><th>TVA</th><th>CA TTC</th><th>Encaissé</th><th>Taux</th></tr></thead>
            <tbody>
              {monthly.map((m,i)=>(
                <tr key={i} style={{opacity:m.ca===0?.38:1}}>
                  <td style={{fontWeight:500}}>{m.label}</td>
                  <td style={{color:"var(--ink2)"}}>{m.count||"—"}</td>
                  <td className="mono">{m.ca>0?fmt(m.ca):"—"}</td>
                  <td className="mono" style={{color:"var(--green)"}}>{m.vat>0?fmt(m.vat):"—"}</td>
                  <td className="mono">{m.ca>0?fmt(m.ca+m.vat):"—"}</td>
                  <td className="mono" style={{color:"var(--green)",fontWeight:500}}>{m.paid>0?fmt(m.paid):"—"}</td>
                  <td>{m.ca>0?(<div style={{display:"flex",alignItems:"center",gap:8}}>
                    <div className="progress" style={{flex:1}}><div className="progress-bar pg-green" style={{width:`${Math.min(100,(m.paid/m.ca)*100)}%`}}/></div>
                    <span style={{fontSize:11.5,color:"var(--ink2)",minWidth:34}}>{fmtPct((m.paid/m.ca)*100)}</span>
                  </div>):"—"}</td>
                </tr>
              ))}
            </tbody>
            <tfoot><tr>
              <td>TOTAL {year}</td><td>{total_invoices}</td>
              <td className="mono">{fmt(total_ca)}</td>
              <td className="mono" style={{color:"var(--green)"}}>{fmt(total_vat)}</td>
              <td className="mono">{fmt(total_ca+total_vat)}</td>
              <td className="mono" style={{color:"var(--green)"}}>{fmt(total_paid)}</td>
              <td><span className="badge badge-green">{fmtPct(total_ca>0?(total_paid/total_ca)*100:0)}</span></td>
            </tr></tfoot>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Dashboard ──────────────────────────────────────────────────────────────────
function Dashboard({ showToast }) {
  const [stats,setStats]   = useState(null);
  const [loading,setLoading] = useState(true);
  const [dbOk,setDbOk]     = useState(null);

  useEffect(()=>{
    api.get("/health").then(()=>setDbOk(true)).catch(()=>setDbOk(false));
    api.get("/api/stats/dashboard")
      .then(r=>setStats(r.data))
      .catch(()=>showToast("Erreur chargement dashboard"))
      .finally(()=>setLoading(false));
  },[]);

  const now = new Date();
  if (loading) return <div className="page"><div className="loading-center"><div className="spinner"/></div></div>;
  if (!stats) return null;
  const {ca_encaisse,pending_ttc,total_collected,total_deductible,net_vat,total_exp_ttc,invoices_paid,invoices_unpaid,chart_data} = stats;
  const vc = net_vat>0?"red":"green";

  return (
    <div className="page">
      <div className="page-header"><h1>Tableau de bord</h1><p>Synthèse financière — {MONTHS_LONG[now.getMonth()]} {now.getFullYear()}</p></div>
      <div className="alert alert-amber">
        <span className="alert-icon">📅</span>
        <span>Prochaine déclaration TVA CA3 — TVA nette estimée : <strong>{fmt(net_vat)}</strong></span>
      </div>
      <div className="kpi-grid">
        <div className="kpi"><div className="kpi-label">CA encaissé</div><div className="kpi-value green">{fmt(ca_encaisse)}</div><div className="kpi-sub">{invoices_paid} factures payées</div></div>
        <div className="kpi"><div className="kpi-label">En attente</div><div className="kpi-value amber">{fmt(pending_ttc)}</div><div className="kpi-sub">{invoices_unpaid} impayées</div></div>
        <div className="kpi"><div className="kpi-label">TVA collectée</div><div className="kpi-value">{fmt(total_collected)}</div></div>
        <div className="kpi"><div className="kpi-label">TVA déductible</div><div className="kpi-value">{fmt(total_deductible)}</div></div>
        <div className="kpi">
          <div className="kpi-label">TVA nette</div>
          <div className={`kpi-value ${vc}`}>{fmt(Math.abs(net_vat))}</div>
          <span className={`kpi-pill pill-${vc}`}>{net_vat>0?"⬆ À reverser":"⬇ Crédit"}</span>
        </div>
        <div className="kpi"><div className="kpi-label">Dépenses TTC</div><div className="kpi-value">{fmt(total_exp_ttc)}</div></div>
      </div>
      <div className="grid-2">
        <div className="card">
          <div className="card-header"><h3>CA & TVA — 6 derniers mois</h3></div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chart_data} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false}/>
                <XAxis dataKey="month" tick={{fontSize:12,fill:"var(--ink3)"}} axisLine={false} tickLine={false}/>
                <YAxis tick={{fontSize:11,fill:"var(--ink3)"}} axisLine={false} tickLine={false} tickFormatter={v=>`${(v/1000).toFixed(0)}k`}/>
                <Tooltip content={<CTip/>}/>
                <Bar dataKey="ca"  name="CA HT" fill="#1A1916" radius={[3,3,0,0]}/>
                <Bar dataKey="tva" name="TVA"   fill="#A8A59E" radius={[3,3,0,0]}/>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card">
          <div className="card-header"><h3>Solde TVA</h3></div>
          <div className="card-body">
            <div style={{display:"flex",flexDirection:"column",gap:13}}>
              <div>
                <div style={{display:"flex",justifyContent:"space-between",fontSize:13,marginBottom:5}}><span>Collectée</span><strong className="mono">{fmt(total_collected)}</strong></div>
                <div className="progress"><div className="progress-bar pg-green" style={{width:"100%"}}/></div>
              </div>
              <div>
                <div style={{display:"flex",justifyContent:"space-between",fontSize:13,marginBottom:5}}><span>Déductible</span><strong className="mono">{fmt(total_deductible)}</strong></div>
                <div className="progress"><div className="progress-bar pg-amber" style={{width:`${Math.min(100,total_collected>0?(total_deductible/total_collected)*100:0)}%`}}/></div>
              </div>
              <hr style={{border:"none",borderTop:"1px solid var(--border)"}}/>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                <span style={{fontWeight:600}}>Solde net</span>
                <span className={`mono kpi-value ${vc}`} style={{fontSize:20}}>{fmt(Math.abs(net_vat))}</span>
              </div>
              <div className={`alert alert-${vc}`} style={{marginBottom:0}}>
                <span className="alert-icon">{net_vat>0?"⚠️":"✅"}</span>
                <span style={{fontSize:13}}>{net_vat>0?`Vous devez ${fmt(net_vat)} à l'État`:`L'État vous doit ${fmt(Math.abs(net_vat))}`}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── App Shell ──────────────────────────────────────────────────────────────────
const TABS = [
  {id:"dashboard", icon:"◈",  label:"Dashboard"},
  {id:"invoices",  icon:"📄", label:"Factures clients"},
  {id:"expenses",  icon:"💸", label:"Dépenses"},
  {id:"vat",       icon:"🧾", label:"TVA"},
  {id:"revenue",   icon:"📈", label:"Chiffre d'affaires"},
];

export default function App() {
  const [tab,   setTab]   = useState("dashboard");
  const [toast, setToast] = useState(null);
  const [dbOk,  setDbOk]  = useState(null);
  const showToast = msg => setToast(msg);

  useEffect(()=>{
    api.get("/health").then(()=>setDbOk(true)).catch(()=>setDbOk(false));
  },[]);

  const current = TABS.find(t=>t.id===tab);
  const renderPage = () => {
    switch(tab) {
      case "dashboard": return <Dashboard showToast={showToast}/>;
      case "invoices":  return <InvoicesPage showToast={showToast}/>;
      case "expenses":  return <ExpensesPage showToast={showToast}/>;
      case "vat":       return <VATPage showToast={showToast}/>;
      case "revenue":   return <RevenuePage showToast={showToast}/>;
      default: return null;
    }
  };

  return (
    <>
      <style>{css}</style>
      {toast && <Toast msg={toast} onClose={()=>setToast(null)}/>}
      <div className="shell">
        <aside className="sidebar">
          <div className="logo">TVA<br/><em>Manager</em></div>
          <div className="nav-section">Navigation</div>
          {TABS.map(t=>(
            <button key={t.id} className={`nav-item${tab===t.id?" active":""}`} onClick={()=>setTab(t.id)}>
              <span className="icon">{t.icon}</span>{t.label}
            </button>
          ))}
          <div className="sidebar-footer">
            <strong>2025</strong>
            Régime réel mensuel
            <div className={`db-badge${dbOk===false?" err":dbOk===null?" wait":""}`}>
              {dbOk===null?"⏳ Connexion…":dbOk?"🟢 PostgreSQL connecté":"🔴 Base déconnectée"}
            </div>
          </div>
        </aside>
        <div className="main">
          <div className="topbar">
            <div>
              <div className="topbar-title">{current?.label}</div>
              <div className="topbar-sub">{new Date().toLocaleDateString("fr-FR",{weekday:"long",year:"numeric",month:"long",day:"numeric"})}</div>
            </div>
          </div>
          {renderPage()}
        </div>
      </div>
    </>
  );
}
