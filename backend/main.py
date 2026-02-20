from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from collections import defaultdict

from database import init_db, get_db
from models import InvoiceDB, ExpenseDB
from schemas import (
    InvoiceCreate, InvoiceUpdate, InvoiceOut,
    ExpenseCreate, ExpenseUpdate, ExpenseOut,
)

app = FastAPI(title="TVA Manager Pro API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()
    print("✅ Base de données initialisée")


# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"app": "TVA Manager Pro", "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}



# ── OCR ───────────────────────────────────────────────────────────────────────
import io, re, tempfile, os
from fastapi import UploadFile, File
import pytesseract
from PIL import Image

def parse_ocr_text(txt: str) -> dict:
    """Extrait les champs d'une facture depuis le texte OCR brut."""
    
    # Montant HT
    amount_ht = None
    for pattern in [
        r"(?:total\s*)?ht\s*[:\-]?\s*(\d[\d\s]*[.,]\d{2})",
        r"(?:montant|sous[-\s]?total)\s*[:\-]?\s*(\d[\d\s]*[.,]\d{2})",
        r"(\d{1,3}(?:[\s]\d{3})*[.,]\d{2})\s*(?:€|eur|HT)",
    ]:
        m = re.search(pattern, txt, re.IGNORECASE)
        if m:
            n = float(m.group(1).replace(" ","").replace(",","."))
            if n >= 10:
                amount_ht = n
                break
    if not amount_ht:
        nums = sorted(
            [float(m.replace(" ","").replace(",",".")) 
             for m in re.findall(r"\b\d{1,3}(?:[\s]\d{3})*[.,]\d{2}\b", txt)
             if 10 <= float(m.replace(" ","").replace(",",".")) < 1_000_000],
            reverse=True
        )
        if nums:
            amount_ht = nums[0]

    # Taux TVA
    vat_rate = 20.0
    m = re.search(r"tva\s*[:\-@]?\s*(20|10|5[,.]5|0)\s*%?", txt, re.IGNORECASE)
    if m:
        r = float(m.group(1).replace(",","."))
        if r in [0, 5.5, 10, 20]:
            vat_rate = r

    # Numéro de facture
    number = ""
    m = re.search(r"(?:n[°o]?\s*(?:de\s*)?facture|invoice\s*#?|ref\.?|référence)\s*[:\-]?\s*([A-Z0-9][\w\-\/]{2,20})", txt, re.IGNORECASE)
    if not m:
        m = re.search(r"\b((?:FA|FAC|INV|F|DEP|FACT|AV)[-\s]?\d[\d\-\/]{1,12})\b", txt, re.IGNORECASE)
    if m:
        number = m.group(1).strip().upper()

    # Date
    from datetime import date
    today = date.today().isoformat()
    MOIS = {"janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,
            "juillet":7,"août":8,"aout":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12}
    parsed_date = today
    m = re.search(r"(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(20\d{2})", txt, re.IGNORECASE)
    if m:
        mo = MOIS[m.group(2).lower()]
        parsed_date = f"{m.group(3)}-{mo:02d}-{int(m.group(1)):02d}"
    else:
        m = re.search(r"\b(20\d{2})[/\-\.](0?[1-9]|1[0-2])[/\-\.](0?[1-9]|[12]\d|3[01])\b", txt)
        if m:
            parsed_date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        else:
            m = re.search(r"\b(0?[1-9]|[12]\d|3[01])[/\-\.](0?[1-9]|1[0-2])[/\-\.](20\d{2})\b", txt)
            if m:
                parsed_date = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"

    # Catégorie
    CAT_MAP = {
        "Logiciel":    r"adobe|figma|notion|slack|github|office|microsoft|google|ovh|aws|heroku|logiciel|software|licence",
        "Matériel":    r"fnac|amazon|apple|dell|lenovo|hp|ecran|clavier|souris|ordinateur|imprimante",
        "Transport":   r"sncf|ratp|uber|billet|train|avion|taxi|transport|air.?france",
        "Téléphone":   r"sfr|orange|bouygues|free|mobile|forfait|telecom",
        "Fournitures": r"papier|fourniture|cartouche|toner|bureau",
        "Loyer":       r"loyer|bail|location|immobilier|coworking",
    }
    category = "Autre"
    for cat, pattern in CAT_MAP.items():
        if re.search(pattern, txt, re.IGNORECASE):
            category = cat
            break

    # Nom (client/fournisseur)
    name = ""
    for pattern in [
        r"(?:client|facturé\s*à|bill(?:ed)?\s*to|à\s*l.attention\s*de)\s*[:\-]?\s*(.+)",
        r"(?:fournisseur|émetteur|société|de\s*la\s*part\s*de)\s*[:\-]?\s*(.+)",
    ]:
        m = re.search(pattern, txt, re.IGNORECASE)
        if m:
            name = m.group(1).strip().split("\n")[0].strip()
            break
    if not name:
        for line in txt.split("\n")[:8]:
            line = line.strip()
            if 3 < len(line) < 60 and re.search(r"[a-zA-ZÀ-ÿ]{3}", line) and not re.search(r"facture|invoice|date|tva|total|montant", line, re.IGNORECASE):
                name = line
                break

    return {
        "name": name,
        "number": number,
        "date": parsed_date,
        "amount_ht": amount_ht,
        "vat_rate": vat_rate,
        "category": category,
    }


@app.post("/api/ocr")
async def ocr_file(file: UploadFile = File(...)):
    """Reçoit un fichier image ou PDF et retourne les champs extraits par OCR."""
    try:
        contents = await file.read()
        images = []

        filename = (file.filename or "").lower()
        content_type = (file.content_type or "")

        if "pdf" in content_type or filename.endswith(".pdf"):
            # PDF → images via pdf2image
            from pdf2image import convert_from_bytes
            imgs = convert_from_bytes(contents, dpi=200, first_page=1, last_page=1)
            images = imgs
        else:
            # Image directe
            images = [Image.open(io.BytesIO(contents))]

        if not images:
            raise HTTPException(status_code=400, detail="Impossible de lire le fichier")

        # OCR sur la première page
        text = pytesseract.image_to_string(images[0], lang="fra", config="--psm 6")

        fields = parse_ocr_text(text)
        return {"success": True, "fields": fields, "raw_text": text[:500]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur OCR: {str(e)}")

# ── INVOICES ──────────────────────────────────────────────────────────────────

@app.get("/api/invoices", response_model=List[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    return db.query(InvoiceDB).order_by(InvoiceDB.date.desc()).all()


@app.post("/api/invoices", response_model=InvoiceOut, status_code=201)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    inv = InvoiceDB(**payload.model_dump())
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@app.get("/api/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(InvoiceDB).filter(InvoiceDB.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    return inv


@app.put("/api/invoices/{invoice_id}", response_model=InvoiceOut)
def update_invoice(invoice_id: int, payload: InvoiceUpdate, db: Session = Depends(get_db)):
    inv = db.query(InvoiceDB).filter(InvoiceDB.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(inv, k, v)
    inv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(inv)
    return inv


@app.delete("/api/invoices/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(InvoiceDB).filter(InvoiceDB.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    db.delete(inv)
    db.commit()


# ── EXPENSES ──────────────────────────────────────────────────────────────────

@app.get("/api/expenses", response_model=List[ExpenseOut])
def list_expenses(db: Session = Depends(get_db)):
    return db.query(ExpenseDB).order_by(ExpenseDB.date.desc()).all()


@app.post("/api/expenses", response_model=ExpenseOut, status_code=201)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    exp = ExpenseDB(**payload.model_dump())
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@app.get("/api/expenses/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    exp = db.query(ExpenseDB).filter(ExpenseDB.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Dépense introuvable")
    return exp


@app.put("/api/expenses/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, payload: ExpenseUpdate, db: Session = Depends(get_db)):
    exp = db.query(ExpenseDB).filter(ExpenseDB.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Dépense introuvable")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(exp, k, v)
    exp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(exp)
    return exp


@app.delete("/api/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    exp = db.query(ExpenseDB).filter(ExpenseDB.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Dépense introuvable")
    db.delete(exp)
    db.commit()


# ── STATS ─────────────────────────────────────────────────────────────────────

def vat(ht, rate):
    return round(ht * rate / 100, 2)

MONTHS_S    = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
MONTHS_LONG = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]


@app.get("/api/stats/dashboard")
def dashboard_stats(db: Session = Depends(get_db)):
    invoices = db.query(InvoiceDB).all()
    expenses = db.query(ExpenseDB).all()

    total_collected  = sum(vat(i.amount_ht, i.vat_rate) for i in invoices)
    total_deductible = sum(vat(e.amount_ht, e.vat_rate) for e in expenses)
    ca_encaisse      = sum(i.amount_ht for i in invoices if i.is_paid)
    pending_ttc      = sum(i.amount_ht + vat(i.amount_ht, i.vat_rate) for i in invoices if not i.is_paid)
    total_exp_ttc    = sum(e.amount_ht + vat(e.amount_ht, e.vat_rate) for e in expenses)

    monthly = defaultdict(lambda: {"ca": 0.0, "tva": 0.0})
    for i in invoices:
        if i.date:
            k = i.date[:7]
            monthly[k]["ca"]  += i.amount_ht
            monthly[k]["tva"] += vat(i.amount_ht, i.vat_rate)

    chart = []
    for k in sorted(monthly.keys())[-6:]:
        mi = int(k[5:7]) - 1
        chart.append({"month": MONTHS_S[mi], "ca": round(monthly[k]["ca"], 2), "tva": round(monthly[k]["tva"], 2)})

    return {
        "ca_encaisse":       round(ca_encaisse, 2),
        "pending_ttc":       round(pending_ttc, 2),
        "total_collected":   round(total_collected, 2),
        "total_deductible":  round(total_deductible, 2),
        "net_vat":           round(total_collected - total_deductible, 2),
        "total_exp_ttc":     round(total_exp_ttc, 2),
        "invoices_paid":     sum(1 for i in invoices if i.is_paid),
        "invoices_unpaid":   sum(1 for i in invoices if not i.is_paid),
        "chart_data":        chart,
    }


@app.get("/api/stats/vat")
def vat_stats(db: Session = Depends(get_db)):
    invoices = db.query(InvoiceDB).all()
    expenses = db.query(ExpenseDB).all()

    month_map = defaultdict(lambda: {"collected": 0.0, "deductible": 0.0})
    for i in invoices:
        if i.date:
            month_map[i.date[:7]]["collected"] += vat(i.amount_ht, i.vat_rate)
    for e in expenses:
        if e.date:
            month_map[e.date[:7]]["deductible"] += vat(e.amount_ht, e.vat_rate)

    months = []
    for k in sorted(month_map.keys()):
        mi = int(k[5:7]) - 1
        d  = month_map[k]
        months.append({
            "key": k,
            "label":      f"{MONTHS_LONG[mi]} {k[:4]}",
            "short":      f"{MONTHS_S[mi]} {k[2:4]}",
            "collected":  round(d["collected"],  2),
            "deductible": round(d["deductible"], 2),
            "net":        round(d["collected"] - d["deductible"], 2),
        })

    by_rate = defaultdict(lambda: {"c": 0.0, "d": 0.0})
    for i in invoices:
        by_rate[f"{i.vat_rate}%"]["c"] += vat(i.amount_ht, i.vat_rate)
    for e in expenses:
        by_rate[f"{e.vat_rate}%"]["d"] += vat(e.amount_ht, e.vat_rate)

    rate_data = [
        {"rate": r, "collected": round(v["c"], 2), "deductible": round(v["d"], 2), "net": round(v["c"] - v["d"], 2)}
        for r, v in by_rate.items()
    ]

    tot_c = sum(m["collected"]  for m in months)
    tot_d = sum(m["deductible"] for m in months)
    return {
        "months":             months,
        "by_rate":            rate_data,
        "total_collected":    round(tot_c, 2),
        "total_deductible":   round(tot_d, 2),
        "total_net":          round(tot_c - tot_d, 2),
    }


@app.get("/api/stats/revenue")
def revenue_stats(year: int = 0, db: Session = Depends(get_db)):
    all_invoices = db.query(InvoiceDB).all()
    years = sorted(set(i.date[:4] for i in all_invoices if i.date), reverse=True)

    if not year and years:
        year = int(years[0])

    invoices = [i for i in all_invoices if i.date and i.date.startswith(str(year))] if year else all_invoices

    monthly = []
    for idx in range(12):
        m_str = str(idx + 1).zfill(2)
        rows  = [i for i in invoices if i.date and i.date[5:7] == m_str]
        ca    = sum(i.amount_ht for i in rows)
        paid  = sum(i.amount_ht for i in rows if i.is_paid)
        v     = sum(vat(i.amount_ht, i.vat_rate) for i in rows)
        monthly.append({
            "month": MONTHS_S[idx],
            "label": MONTHS_LONG[idx],
            "ca":    round(ca, 2),
            "paid":  round(paid, 2),
            "vat":   round(v, 2),
            "count": len(rows),
        })

    return {
        "monthly":         monthly,
        "total_ca":        round(sum(m["ca"]   for m in monthly), 2),
        "total_paid":      round(sum(m["paid"] for m in monthly), 2),
        "total_vat":       round(sum(m["vat"]  for m in monthly), 2),
        "total_invoices":  len(invoices),
        "years":           years,
    }
