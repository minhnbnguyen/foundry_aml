"""
Synthetic AML dataset generator for a Palantir Foundry / AIP build.

Produces five clean CSVs for ingestion (customers, accounts, transactions,
alerts, counterparties) plus a scenario answer-key. Everything is fictional
and randomly generated. No real people or real financial data.

Design goals:
  1. ~90% of alerts are false positives (matches the sourced industry benchmark).
  2. One clean STRUCTURING case (single subject, fan-in of sub-$10k cash).
  3. One LAYERING RING: a source entity fans money to 4 mule *customers*
     (same bank -> traversable in the graph), who funnel out to one external
     shell counterparty. Alerts cluster across ~5 accounts into ONE case.
  4. The false positives are *realistic* so the AIP triage assistant has
     genuine reasoning to do (legit cash business, one-off car sale, etc.).
"""

import csv, random, datetime as dt
from pathlib import Path

random.seed(42)
OUT = Path("/mnt/user-data/outputs")
OUT.mkdir(parents=True, exist_ok=True)

BRANCHES = ["Chicago-Loop", "Chicago-Uptown", "Naperville", "Evanston", "Oak Park"]
START = dt.date(2026, 4, 1)
END = dt.date(2026, 6, 30)

FIRST = ["James","Maria","David","Linda","Robert","Patricia","John","Jennifer","Michael",
         "Elizabeth","William","Susan","Richard","Karen","Thomas","Nancy","Daniel","Lisa",
         "Paul","Betty","Mark","Sandra","Kevin","Ashley","Brian","Emily","George","Grace",
         "Edward","Olivia","Ronald","Sophia","Kenneth","Chloe","Anthony","Hannah"]
LAST = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez",
        "Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor",
        "Moore","Jackson","Martin","Lee","Perez","Thompson","White","Harris","Clark","Lewis",
        "Walker","Hall","Allen","Young","King","Wright","Scott","Green","Adams"]
OCC = ["Teacher","Nurse","Software Engineer","Retail Manager","Accountant","Electrician",
       "Graphic Designer","Sales Rep","Pharmacist","Mechanic","Consultant","Chef",
       "Real Estate Agent","Dental Hygienist","Logistics Coordinator","HR Specialist"]

customers, accounts, transactions, alerts, counterparties = [], [], [], [], []
_tx = [0]; _al = [0]
def tid():
    _tx[0]+=1; return f"T{_tx[0]:05d}"
def aid():
    _al[0]+=1; return f"AL{_al[0]:04d}"
def rdate(a=START, b=END):
    return a + dt.timedelta(days=random.randint(0,(b-a).days))

def add_customer(cid, name, onboard, risk, occ, pep, branch, income, ctype="Individual"):
    customers.append(dict(customer_id=cid, full_name=name, customer_type=ctype,
        date_onboarded=onboard.isoformat(), kyc_risk_rating=risk, occupation=occ,
        pep_flag=pep, home_branch=branch, annual_declared_income=income))

def add_account(acc, cid, atype, opened, bal):
    accounts.append(dict(account_id=acc, customer_id=cid, account_type=atype,
        date_opened=opened.isoformat(), current_balance=bal))

def add_tx(date, amount, channel, frm=None, to=None, party=None, country=None, desc=""):
    transactions.append(dict(transaction_id=tid(), txn_date=date.isoformat(),
        from_account_id=frm or "", to_account_id=to or "", external_party=party or "",
        external_country=country or "", amount=round(amount,2), channel=channel, description=desc))

def add_alert(acc, cid, code, descr, date, score):
    alerts.append(dict(alert_id=aid(), date_generated=date.isoformat(), account_id=acc,
        customer_id=cid, rule_code=code, rule_description=descr, system_score=score, status="New"))

def add_cp(cpid, name, ctype, country, risk):
    counterparties.append(dict(counterparty_id=cpid, name=name, cp_type=ctype,
        country=country, risk_flag=risk))

# ---- external counterparties -----------------------------------------------
add_cp("CP001","Apex Trade Services FZE","Shell / Trade","United Arab Emirates","High")
add_cp("CP002","Meridian Offshore Ltd","Investment","Cyprus","High")
add_cp("CP003","Great Lakes Produce Co","Business","United States","Low")
add_cp("CP004","Fidelity Brokerage","Investment","United States","Low")
add_cp("CP005","Midwest Property Mgmt","Business","United States","Low")

# =========================================================================
#  NORMAL POPULATION  (the noise that generates most false positives)
# =========================================================================
normal_ids = []
for i in range(1, 41):
    cid = f"C{i:04d}"; normal_ids.append(cid)
    name = f"{random.choice(FIRST)} {random.choice(LAST)}"
    onboard = dt.date(random.randint(2011,2024), random.randint(1,12), random.randint(1,28))
    income = random.choice([48000,55000,62000,71000,83000,95000,110000])
    add_customer(cid, name, onboard, random.choice(["Low","Low","Low","Medium"]),
                 random.choice(OCC), "N", random.choice(BRANCHES), income)
    acc = f"A{i:04d}"; add_account(acc, cid, "Personal Checking",
                                    onboard, random.randint(2000,45000))
    # mundane activity: biweekly payroll in, a few bills out
    d = START
    while d < END:
        add_tx(d, round(income/26,2), "ACH", to=acc, party="EMPLOYER PAYROLL", desc="Salary")
        for _ in range(random.randint(2,4)):
            add_tx(d+dt.timedelta(days=random.randint(1,12)), random.randint(40,900),
                   random.choice(["CARD","ACH"]), frm=acc,
                   party=random.choice(["Utility Co","Grocery","Streaming","Rent","Insurer"]),
                   desc="Everyday spend")
        d += dt.timedelta(days=14)

# ---- realistic FALSE-POSITIVE alerts on normal customers -------------------
# FP1 legit cash-intensive business (diner) -> looks like structuring, isn't
add_customer("C0041","Sunrise Diner LLC", dt.date(2015,6,1),"Medium","Restaurant Owner","N",
             "Chicago-Uptown",240000, ctype="Business")
add_account("A0041","C0041","Business Checking", dt.date(2015,6,1), 38000)
d = START
while d < END:
    add_tx(d, random.randint(2200,5800), "CASH", to="A0041",
           party="CASH DEPOSIT", desc="Daily receipts")
    d += dt.timedelta(days=random.randint(1,2))
add_alert("A0041","C0041","STRUCT-CASH","Repeated cash deposits below reporting threshold",
          rdate(), 71)  # FALSE POSITIVE: licensed cash business

# FP2 one-off car sale, single sub-$10k cash deposit
add_alert(f"A0005","C0005","STRUCT-CASH","Single cash deposit just under $10,000 threshold",
          rdate(), 58)
add_tx(rdate(), 9600, "CASH", to="A0005", party="CASH DEPOSIT", desc="Used car sale")

# FP3 property manager, many round-number ACH out
add_customer("C0042","Midwest Property Mgmt", dt.date(2013,3,1),"Medium","Property Manager","N",
             "Naperville",520000, ctype="Business")
add_account("A0042","C0042","Business Checking", dt.date(2013,3,1), 91000)
for _ in range(22):
    add_tx(rdate(), random.choice([1200,1500,1800,2000]), "ACH", frm="A0042",
           party="Tenant Refund", desc="Deposit return")
add_alert("A0042","C0042","VELOCITY","High count of outbound transfers in 30 days", rdate(), 63)

# FP4 retiree consolidating own savings -> internal same-owner transfer
add_customer("C0043","Betty Coleman", dt.date(2009,9,1),"Low","Retired","N","Evanston",40000)
add_account("A0043","C0043","Personal Checking", dt.date(2009,9,1), 12000)
add_account("A0043S","C0043","Personal Savings", dt.date(2009,9,1), 61000)
add_tx(rdate(), 45000, "INTERNAL", frm="A0043S", to="A0043", desc="Move savings for home repair")
add_alert("A0043","C0043","RAPID-MOVE","Large transfer with rapid follow-on movement", rdate(), 66)

# FP5 new private-banking client, big inbound wire from brokerage (legit)
add_customer("C0044","Grace Whitfield", dt.date(2026,4,10),"Medium","Business Owner","N",
             "Chicago-Loop",600000)
add_account("A0044","C0044","Personal Checking", dt.date(2026,4,10), 15000)
add_tx(dt.date(2026,4,20), 250000, "WIRE", to="A0044", party="Fidelity Brokerage",
       country="United States", desc="Brokerage liquidation")
add_alert("A0044","C0044","HIGH-RISK-WIRE","Large inbound wire on newly opened account", rdate(), 74)

# scattered single FP alerts on random normals (pure noise). Tuned so that
# true positives land at ~10% of the queue -> ~90% false-positive rate.
N_NOISE = 76
for _ in range(N_NOISE):
    cid = random.choice(normal_ids)
    acc = "A"+cid[1:]
    code, descr, sc = random.choice([
        ("VELOCITY","Elevated transaction count vs 90-day baseline",52),
        ("HIGH-RISK-WIRE","Wire to/from monitored region",57),
        ("RAPID-MOVE","Funds in and out within 72 hours",49),
        ("STRUCT-CASH","Cash activity near reporting threshold",55),
    ])
    add_alert(acc, cid, code, descr, rdate(), sc)

fp_alert_count = len(alerts)  # everything so far is a false positive

# =========================================================================
#  TRUE POSITIVE 1 — STRUCTURING (single subject, fan-in of sub-$10k cash)
# =========================================================================
add_customer("C9001","Marcus Reilly", dt.date(2025,11,3),"Medium","Rideshare Driver","N",
             "Chicago-Loop",41000)
add_account("A9001","C9001","Personal Checking", dt.date(2025,11,3), 3200)
sd = dt.date(2026,5,4)
struct_alert_ids = []
for k in range(11):
    day = sd + dt.timedelta(days=int(k*1.6))
    amt = random.choice([8200,8600,8900,9100,9400,9600,9750])
    br = "Chicago-Loop" if k % 2 == 0 else "Naperville"  # branch-hopping
    add_tx(day, amt, "CASH", to="A9001", party="CASH DEPOSIT", desc=f"Cash deposit {br}")
# fires a few STRUCT-CASH alerts as the pattern recurs
for day_off in (3, 11, 18):
    a = aid_before = None
    add_alert("A9001","C9001","STRUCT-CASH",
              "Multiple cash deposits below $10k threshold across branches",
              sd+dt.timedelta(days=day_off), 88)
    struct_alert_ids.append(alerts[-1]["alert_id"])

# =========================================================================
#  TRUE POSITIVE 2 — LAYERING RING (source -> 4 mules -> external shell)
# =========================================================================
# Source: business that receives a large high-risk inbound, then fans out fast
add_customer("C9100","Northgate Consulting LLC", dt.date(2026,3,20),"Medium","Consulting","N",
             "Chicago-Loop",180000, ctype="Business")
add_account("A9100","C9100","Business Checking", dt.date(2026,3,20), 22000)

# Mules: recently onboarded, low declared income (the tell)
mules = [
    ("C9101","Katie Brennan","A9101",34000),
    ("C9102","Samuel Osei","A9102",31000),
    ("C9103","Lucas Grant","A9103",38000),
    ("C9104","Nadia Farah","A9104",29000),
]
for cid,name,acc,inc in mules:
    add_customer(cid, name, dt.date(2026,4,15),"Medium","Part-time Retail","N",
                 random.choice(BRANCHES), inc)
    add_account(acc, cid, "Personal Checking", dt.date(2026,4,15), random.randint(500,2500))

ring_alert_ids = []
# 1) dirty money in: high-risk offshore wire into the source
in_day = dt.date(2026,6,2)
add_tx(in_day, 320000, "WIRE", to="A9100", party="Meridian Offshore Ltd",
       country="Cyprus", desc="Inbound consulting fee")
add_alert("A9100","C9100","HIGH-RISK-WIRE","Large inbound wire from high-risk jurisdiction",
          in_day, 82); ring_alert_ids.append(alerts[-1]["alert_id"])

# 2) rapid fan-out to the 4 mules (internal, within ~48h)
for j,(cid,name,acc,inc) in enumerate(mules):
    fan_day = in_day + dt.timedelta(days=1+ (j%2))
    add_tx(fan_day, round(320000/4 - random.randint(500,2500),2), "INTERNAL",
           frm="A9100", to=acc, desc="Project disbursement")
add_alert("A9100","C9100","RAPID-MOVE","Inbound funds dispersed to multiple parties within 48h",
          in_day+dt.timedelta(days=2), 90); ring_alert_ids.append(alerts[-1]["alert_id"])

# 3) each mule funnels out to the SAME external shell within ~72h (the common node)
for j,(cid,name,acc,inc) in enumerate(mules):
    out_day = in_day + dt.timedelta(days=3+ (j%3))
    add_tx(out_day, round(320000/4 - random.randint(3000,6000),2), "WIRE",
           frm=acc, party="Apex Trade Services FZE", country="United Arab Emirates",
           desc="Vendor payment")
    add_alert(acc, cid, "RAPID-MOVE","Pass-through: funds received and wired out within 72h",
              out_day, 86); ring_alert_ids.append(alerts[-1]["alert_id"])

ring_true_count = len(ring_alert_ids)
struct_true_count = len(struct_alert_ids)
tp_total = ring_true_count + struct_true_count
total_alerts = len(alerts)
fp_rate = 100*(total_alerts - tp_total)/total_alerts

# ---- write CSVs -------------------------------------------------------------
def dump(name, rows, fields):
    with open(OUT/name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

dump("customers.csv", customers,
     ["customer_id","full_name","customer_type","date_onboarded","kyc_risk_rating",
      "occupation","pep_flag","home_branch","annual_declared_income"])
dump("accounts.csv", accounts,
     ["account_id","customer_id","account_type","date_opened","current_balance"])
dump("transactions.csv", transactions,
     ["transaction_id","txn_date","from_account_id","to_account_id","external_party",
      "external_country","amount","channel","description"])
dump("alerts.csv", alerts,
     ["alert_id","date_generated","account_id","customer_id","rule_code",
      "rule_description","system_score","status"])
dump("counterparties.csv", counterparties,
     ["counterparty_id","name","cp_type","country","risk_flag"])

print(f"customers      {len(customers)}")
print(f"accounts       {len(accounts)}")
print(f"transactions   {len(transactions)}")
print(f"alerts         {len(alerts)}")
print(f"counterparties {len(counterparties)}")
print(f"true positives {tp_total}  (ring {ring_true_count}, structuring {struct_true_count})")
print(f"false-positive rate  {fp_rate:.1f}%")
print("RING alerts:", ring_alert_ids)
print("STRUCT alerts:", struct_alert_ids)
