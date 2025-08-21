from __future__ import annotations
import numpy as np, pandas as pd, random
from faker import Faker
from datetime import datetime, timedelta

def make_entities(n:int=6, seed:int=42):
    fake = Faker(); Faker.seed(seed); random.seed(seed)
    ents = [f"ENT{100+i}" for i in range(n)]
    currencies = ["USD","EUR","GBP","JPY","CHF","CAD"]
    home_ccy = {e: random.choice(currencies) for e in ents}
    return pd.DataFrame({"entity":ents,"home_ccy":[home_ccy[e] for e in ents]})

def make_coa(seed:int=42):
    np.random.seed(seed)
    rows=[]
    acct_types = [
        ("1000","Cash","cash"),
        ("1200","AR","asset"),
        ("2000","AP","liability"),
        ("2100","IC_REC","asset"),
        ("2200","IC_PAY","liability"),
        ("3000","Revenue","revenue"),
        ("5000","COGS","expense"),
        ("5100","OPEX","expense"),
        ("6000","FX_GAIN_LOSS","expense"),
        ("7000","Accruals","liability"),
        ("8000","Prepaid","asset"),
    ]
    for code,name,cls in acct_types:
        rows.append((code,name,cls))
    return pd.DataFrame(rows, columns=["account","name","class"])

def make_fx(period:str, seed:int=42):
    np.random.seed(seed)
    base = {"USD":1.0,"EUR":1.09,"GBP":1.28,"JPY":0.0068,"CHF":1.12,"CAD":0.74}
    drift = {k: v*(1+np.random.normal(0,0.02)) for k,v in base.items()}
    return pd.DataFrame([{"period":period,"ccy":k,"usd":v} for k,v in drift.items()])

def make_budget(entities, coa, period:str, seed:int=42):
    np.random.seed(seed); rows=[]
    for _,e in entities.iterrows():
        for _,a in coa.iterrows():
            base = {"cash":50000,"asset":40000,"liability":-35000,"revenue":120000,"expense":-80000}.get(a["class"], 0)
            val = base*(1+np.random.normal(0,0.25))
            rows.append((period, e.entity, a.account, round(val,2)))
    return pd.DataFrame(rows, columns=["period","entity","account","budget"])

def make_gl(entities, coa, period:str, seed:int=42):
    np.random.seed(seed); rows=[]
    for _,e in entities.iterrows():
        for _,a in coa.iterrows():
            mean = {"cash":60000,"asset":45000,"liability":-40000,"revenue":150000,"expense":-90000}.get(a["class"], 0)
            noise = np.random.normal(0, abs(mean)*0.15 if mean else 8000)
            bal = mean + noise
            rows.append((period, e.entity, a.account, round(float(bal),2)))
    gl = pd.DataFrame(rows, columns=["period","entity","account","balance"])
    tweak = gl.sample(frac=0.05, random_state=seed).index
    gl.loc[tweak,"balance"] = gl.loc[tweak,"balance"] * 1.10
    return gl

def make_subledgers(entities, period:str, seed:int=42):
    np.random.seed(seed); rows_ap=[]; rows_ar=[]
    base_date = datetime.strptime(period+"-01","%Y-%m-%d")
    counterparties = [f"CUST{i:03d}" for i in range(1,60)]
    vendors = [f"VEND{i:03d}" for i in range(1,60)]
    for _,e in entities.iterrows():
        for i in range(np.random.randint(120,200)):
            amt = round(float(np.random.gamma(2, 1500)),2)
            inv_day = int(np.random.uniform(0,27))
            inv_date = (base_date + timedelta(days=inv_day)).date().isoformat()
            days = int(np.random.normal(15,10))
            rows_ar.append((period, e.entity, f"INV{period}-{i:04d}", amt, "USD", days, inv_date, np.random.choice(counterparties)))
        for i in range(np.random.randint(100,180)):
            amt = round(float(np.random.gamma(2.2, 1300)),2)
            inv_day = int(np.random.uniform(0,27))
            bill_date = (base_date + timedelta(days=inv_day)).date().isoformat()
            days = int(np.random.normal(20,12))
            rows_ap.append((period, e.entity, f"BILL{period}-{i:04d}", amt, "USD", days, bill_date, np.random.choice(vendors)))
    ar = pd.DataFrame(rows_ar, columns=["period","entity","invoice_id","amount","currency","age_days","invoice_date","counterparty"])
    ap = pd.DataFrame(rows_ap, columns=["period","entity","bill_id","amount","currency","age_days","bill_date","counterparty"])
    return ar, ap

def make_bank(entities, period:str, seed:int=42):
    np.random.seed(seed); rows=[]
    for _,e in entities.iterrows():
        for i in range(np.random.randint(300,500)):
            amt = round(float(np.random.normal(0, 4000)),2)
            dt = datetime.strptime(period+"-01","%Y-%m-%d") + timedelta(days=int(np.random.uniform(0,27)))
            rows.append((period, e.entity, f"BNK{period}-{i:05d}", dt.date().isoformat(), amt, "USD",
                         random.choice(["ACH","WIRE","CARD","FEE"])))
    return pd.DataFrame(rows, columns=["period","entity","bank_txn_id","date","amount","currency","method"])

def make_ic_docs(entities, period:str, seed:int=42):
    np.random.seed(seed); ents = list(entities["entity"]); rows=[]
    pairs = [(a,b) for i,a in enumerate(ents) for b in ents[i+1:]]
    for a,b in pairs:
        for i in range(np.random.randint(4,9)):
            amt = round(float(np.random.normal(20000, 15000)),2)
            leak = amt * np.random.choice([0.0, 0.02, -0.03])
            rows.append((period, a, b, f"IC-{a}-{b}-{i:03d}", amt, amt+leak, "USD"))
    return pd.DataFrame(rows, columns=["period","entity_src","entity_dst","doc_id","amount_src","amount_dst","currency"])
