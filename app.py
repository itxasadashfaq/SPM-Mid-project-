from flask import Flask, request, redirect, url_for, render_template_string, flash
import sqlite3, os, json
from datetime import date, timedelta, datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("PMS_DB", os.path.join(APP_DIR, "healthcare_pms.db"))
app = Flask(__name__)
app.secret_key = "change-this-secret-key"

SCHEMA = """
CREATE TABLE IF NOT EXISTS project (
 id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL, objectives TEXT NOT NULL,
 stakeholders TEXT NOT NULL, scope_in TEXT NOT NULL, scope_out TEXT NOT NULL,
 budget REAL NOT NULL, start_date TEXT NOT NULL, deadline TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'In Progress', closure_notes TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS requirements (
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT DEFAULT '',
 priority TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Proposed', approved_scope INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS changes (
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, justification TEXT NOT NULL,
 cost_impact REAL NOT NULL DEFAULT 0, weeks_impact INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'Pending', requirement_id INTEGER,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, decision_notes TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS tasks (
 id INTEGER PRIMARY KEY AUTOINCREMENT, wbs TEXT NOT NULL, name TEXT NOT NULL,
 duration INTEGER NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL,
 dependency_id INTEGER, assigned_to TEXT NOT NULL, planned_cost REAL NOT NULL DEFAULT 0,
 actual_cost REAL NOT NULL DEFAULT 0, percent_complete INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'Not Started', milestone INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS defects (
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT DEFAULT '',
 severity TEXT NOT NULL, assigned_to TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Open',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS quality_checks (
 id INTEGER PRIMARY KEY AUTOINCREMENT, deliverable TEXT NOT NULL, checklist_item TEXT NOT NULL,
 result TEXT NOT NULL, notes TEXT DEFAULT '', inspected_by TEXT NOT NULL,
 inspected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS risks (
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, likelihood INTEGER NOT NULL,
 impact INTEGER NOT NULL, response TEXT NOT NULL, owner TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Open'
);
CREATE TABLE IF NOT EXISTS audit_log (
 id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, details TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def log(conn, action, details):
    conn.execute("INSERT INTO audit_log(action,details) VALUES(?,?)", (action, details))

def init_db():
    conn=db()
    conn.executescript(SCHEMA)
    exists=conn.execute("SELECT id FROM project WHERE id=1").fetchone()
    if not exists:
        today=date.today()
        deadline=today+timedelta(weeks=16)
        conn.execute("""INSERT INTO project(id,name,objectives,stakeholders,scope_in,scope_out,budget,start_date,deadline,status)
        VALUES(1,?,?,?,?,?,?,?,?,?)""", (
            "Smart Healthcare Project Management and Monitoring System",
            "Deliver a secure, reliable healthcare management platform for five hospitals within approved time and cost.",
            "Hospital management; doctors; patients; laboratory staff; billing staff; development team",
            "Appointments, laboratory reports, doctor schedules, online consultations, hospital billing, project monitoring",
            "AI diagnosis and mobile application are excluded until formally approved as changes.",
            5000000, today.isoformat(), deadline.isoformat(), "In Progress"))
        reqs=[
            ("Patient appointment management","Book, update and cancel patient appointments.","High","Approved",1),
            ("Laboratory reports","Store and view laboratory reports securely.","High","Approved",1),
            ("Doctor schedules","Manage doctor availability and shifts.","High","Approved",1),
            ("Online consultations","Support remote patient-doctor consultations.","Medium","Approved",1),
            ("Hospital billing","Generate and track patient bills.","High","Approved",1),
            ("AI preliminary diagnosis","Provide preliminary AI-assisted assessment; not a final medical diagnosis.","High","Proposed",0),
            ("Mobile application","Provide mobile access to core healthcare features.","Medium","Proposed",0)]
        conn.executemany("INSERT INTO requirements(title,description,priority,status,approved_scope) VALUES(?,?,?,?,?)",reqs)
        tasks=[
            ("1.1","Requirements and project charter",2,0,"Project Manager",250000,250000,100,None,1),
            ("1.2","System architecture and UI design",2,2,"Frontend Developer 1",400000,350000,100,1,0),
            ("1.3","Database design",2,4,"Database Developer",350000,300000,100,1,0),
            ("2.1","Backend API development",4,6,"Backend Developer 1",1100000,700000,60,2,0),
            ("2.2","Frontend development",4,6,"Frontend Developer 1",900000,450000,40,2,0),
            ("2.3","Integration and consultation module",2,10,"Backend Developer 2",550000,100000,10,4,0),
            ("3.1","System testing and defect fixing",2,12,"QA Engineer",600000,100000,10,5,0),
            ("3.2","Deployment and training",2,14,"Project Manager",300000,0,0,7,1),
            ("3.3","Project closure",1,16,"Project Manager",150000,0,0,8,1)]
        for wbs,name,dur,offset,owner,cost,actual,complete,dep,milestone in tasks:
            st=today+timedelta(weeks=offset)
            en=st+timedelta(weeks=dur)
            conn.execute("""INSERT INTO tasks(wbs,name,duration,start_date,end_date,dependency_id,assigned_to,planned_cost,actual_cost,percent_complete,status,milestone)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(wbs,name,dur,st.isoformat(),en.isoformat(),dep,owner,cost,actual,complete,
            "Completed" if complete==100 else ("In Progress" if complete>0 else "Not Started"),milestone))
        conn.executemany("INSERT INTO defects(title,description,severity,assigned_to,status) VALUES(?,?,?,?,?)",[
            ("Appointment scheduling conflict","Overlapping appointments can be assigned to the same doctor.","Critical","Backend Developer 1","Open"),
            ("Patient record update failure","Updated patient details are not consistently saved.","Critical","Backend Developer 2","Open"),
            ("Billing layout issue","Invoice total alignment is incorrect on a small screen.","Medium","Frontend Developer 2","In Progress")])
        conn.executemany("INSERT INTO quality_checks(deliverable,checklist_item,result,notes,inspected_by) VALUES(?,?,?,?,?)",[
            ("Appointment module","Prevent double booking","Fail","Critical defect is open.","QA Engineer"),
            ("Patient records","Verify record updates persist","Fail","Retest after fix.","QA Engineer"),
            ("Billing module","Verify invoice totals","Pass","Sample invoices checked.","QA Engineer")])
        conn.executemany("INSERT INTO risks(title,likelihood,impact,response,owner,status) VALUES(?,?,?,?,?,?)",[
            ("Critical defects delay release",4,5,"Run defect triage daily; block release until critical tests pass.","QA Engineer","Open"),
            ("Uncontrolled scope expansion",4,4,"Require change approval and update baseline before work begins.","Project Manager","Open"),
            ("Budget overrun",3,5,"Review CPI and actual expenditure weekly.","Project Manager","Open")])
        conn.execute("INSERT INTO changes(title,justification,cost_impact,weeks_impact,status,requirement_id,decision_notes) VALUES(?,?,?,?,?,?,?)",
                     ("AI diagnosis and mobile application","Hospital management requested additional digital services.",800000,3,"Pending",6,"Awaiting change control approval."))
        log(conn,"INITIALIZE","Seeded case-study sample records.")
        conn.commit()
    conn.close()

def rows(sql, args=()):
    conn=db()
    data=conn.execute(sql,args).fetchall()
    conn.close()
    return data

def one(sql,args=()):
    conn=db(); data=conn.execute(sql,args).fetchone(); conn.close(); return data

def money(x):
    return "PKR {:,.0f}".format(x or 0)

BASE = """
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} | Smart Healthcare PMS</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root{--ink:#17243b;--navy:#102a43;--blue:#167d9a;--teal:#16a085;--light:#f4f8fb;--line:#d9e5ec;--green:#218c68;--red:#c44949;--amber:#d28a24}
*{box-sizing:border-box}body{margin:0;font:15px "DM Sans",Arial,sans-serif;background:linear-gradient(135deg,#f4f8fb 0%,#edf5f5 100%);color:var(--ink)}
header{background:linear-gradient(120deg,#102a43,#176b7c);color:#fff;padding:28px 24px;position:relative;overflow:hidden}header:after{content:"";position:absolute;width:260px;height:260px;border:35px solid #ffffff14;border-radius:50%;right:-65px;top:-150px}header h1{font:700 25px "Space Grotesk",sans-serif;letter-spacing:-.4px;margin:0 0 6px;position:relative;z-index:1}header p{margin:0;color:#d8f1f3;position:relative;z-index:1}
nav{display:flex;flex-wrap:wrap;gap:7px;background:#fff;padding:12px 20px;border-bottom:1px solid var(--line);box-shadow:0 3px 14px #102a4310;position:sticky;top:0;z-index:5}
nav a{padding:9px 12px;text-decoration:none;color:#466076;border-radius:8px;font-weight:600;transition:.2s}nav a:hover{background:#e5f4f5;color:#10677c;transform:translateY(-1px)}
main{max-width:1250px;margin:28px auto;padding:0 16px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:19px;margin-bottom:18px;box-shadow:0 8px 24px #153b4d0b;transition:box-shadow .2s,transform .2s}.card:hover{box-shadow:0 12px 28px #153b4d17}
.kpi{font:700 25px "Space Grotesk",sans-serif;margin:9px 0;color:var(--navy)}.muted{color:#647789;font-size:13px}
h2{font:700 23px "Space Grotesk",sans-serif;margin:0 0 16px;color:var(--navy)}h3{font:700 17px "Space Grotesk",sans-serif;color:#214158}table{width:100%;border-collapse:separate;border-spacing:0;background:#fff;overflow:hidden}th,td{padding:11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:#eaf4f5;color:#28576c;font-size:12px;text-transform:uppercase;letter-spacing:.35px}tr:last-child td{border-bottom:0}tr:hover td{background:#fbfefe}form.inline{display:inline}
input,select,textarea{width:100%;padding:10px 11px;border:1px solid #bfd0da;border-radius:8px;font:inherit;background:#fbfdfe;color:var(--ink);transition:border .2s,box-shadow .2s}input:focus,select:focus,textarea:focus{outline:0;border-color:var(--teal);box-shadow:0 0 0 3px #16a0851c}textarea{min-height:85px}
label{font-weight:600;font-size:13px;display:block;margin:10px 0 5px;color:#36566a}.formgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
button,.btn{background:linear-gradient(135deg,var(--blue),#12627d);color:white;border:0;border-radius:8px;padding:10px 15px;cursor:pointer;text-decoration:none;display:inline-block;margin-top:10px;font-weight:600;box-shadow:0 4px 10px #167d9a26;transition:.2s}button:hover,.btn:hover{filter:brightness(1.08);transform:translateY(-1px)}button.secondary{background:#657889}button.danger{background:var(--red)}
.badge{display:inline-block;padding:5px 9px;border-radius:20px;background:#e3f3f2;color:#176b70;font-size:12px;font-weight:600}.dangertext{color:var(--red);font-weight:bold}.good{color:var(--green);font-weight:bold}
.flash{background:#fff6df;color:#805c16;padding:12px 14px;border:1px solid #f0d48d;border-radius:9px;margin-bottom:14px}
.bar{height:13px;background:#e2edf0;border-radius:10px;overflow:hidden;min-width:90px}.bar span{display:block;height:100%;background:linear-gradient(90deg,var(--teal),#54c5a5);border-radius:10px}
.small{font-size:12px}.timeline{display:grid;grid-template-columns:170px 1fr;gap:8px;align-items:center;margin:12px 0}.track{height:24px;background:#edf3f5;border-radius:7px;position:relative}.taskbar{height:100%;background:linear-gradient(90deg,#168aa0,#36b59c);border-radius:7px;color:white;font-size:11px;padding:5px;white-space:nowrap;overflow:hidden}.late{background:linear-gradient(90deg,#c44949,#e0775c)}.pass{color:var(--green)}.fail{color:var(--red)}
@media(max-width:650px){.timeline{grid-template-columns:1fr;gap:3px}header{padding:22px 16px}header h1{font-size:21px}nav{padding:9px 12px}nav a{font-size:13px;padding:8px 9px}main{margin-top:20px;padding:0 12px}.card{padding:15px;border-radius:11px}table{display:block;overflow-x:auto;white-space:nowrap}}
</style></head><body>
<header><h1>Smart Healthcare Project Management System</h1><p>Software Project Management · COMSATS University Islamabad, Sahiwal Campus</p></header>
<nav><a href="/">Dashboard</a><a href="/project">Project Charter</a><a href="/requirements">Scope & WBS</a><a href="/changes">Change Requests</a><a href="/schedule">Schedule & Resources</a><a href="/cost">Cost & EVM</a><a href="/quality">Quality & Risks</a><a href="/reports">Reports / Audit</a></nav>
<main>{% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{% endif %}{% endwith %}
{{ body|safe }}
<p class="muted small">Educational demonstration app. Sample records are fictional. AI diagnosis is a proposed feature only, not medical advice.</p></main></body></html>
"""
def page(title, body, **ctx):
    return render_template_string(BASE, title=title, body=render_template_string(body, **ctx))

@app.route("/")
def dashboard():
    p=one("SELECT * FROM project WHERE id=1")
    req=one("SELECT COUNT(*) n FROM requirements WHERE approved_scope=1")["n"]
    pending=one("SELECT COUNT(*) n FROM changes WHERE status='Pending'")["n"]
    delayed=rows("SELECT * FROM tasks WHERE status!='Completed' AND end_date < ?",(date.today().isoformat(),))
    critical=one("SELECT COUNT(*) n FROM defects WHERE severity='Critical' AND status!='Resolved'")["n"]
    spent=one("SELECT COALESCE(SUM(actual_cost),0) n FROM tasks")["n"]
    planned=one("SELECT COALESCE(SUM(planned_cost),0) n FROM tasks")["n"]
    completed=one("SELECT COALESCE(AVG(percent_complete),0) n FROM tasks")["n"]
    body="""<h2>Project Dashboard</h2><div class="grid">
    <div class="card"><div class="muted">Approved Budget</div><div class="kpi">{{money(p['budget'])}}</div><div class="muted">Current baseline</div></div>
    <div class="card"><div class="muted">Actual Expenditure</div><div class="kpi">{{money(spent)}}</div><div class="muted">Across all activities</div></div>
    <div class="card"><div class="muted">Average Task Completion</div><div class="kpi">{{'%.0f' % completed}}%</div><div class="bar"><span style="width:{{completed}}%"></span></div></div>
    <div class="card"><div class="muted">Approved Requirements</div><div class="kpi">{{req}}</div><div class="muted">Pending changes: {{pending}}</div></div>
    <div class="card"><div class="muted">Overdue Activities</div><div class="kpi">{{delayed|length}}</div><div class="muted">Based on planned end date</div></div>
    <div class="card"><div class="muted">Unresolved Critical Defects</div><div class="kpi">{{critical}}</div><div class="muted">Release risk</div></div></div>
    <div class="card"><h2>Project overview</h2><p><b>{{p['name']}}</b></p><p>{{p['objectives']}}</p><p>Start: {{p['start_date']}} · Deadline: {{p['deadline']}} · Status: <span class="badge">{{p['status']}}</span></p>
    {% if spent > p['budget'] %}<p class="dangertext">WARNING: actual expenditure exceeds the approved budget.</p>{% endif %}
    {% if critical %}<p class="dangertext">WARNING: unresolved critical defects must be addressed before release.</p>{% endif %}
    {% if delayed %}<p class="dangertext">WARNING: one or more activities are overdue.</p>{% endif %}
    </div>
    <div class="card"><h2>Delayed activities</h2>{% if delayed %}<table><tr><th>Activity</th><th>Owner</th><th>Planned end</th><th>Status</th></tr>{% for t in delayed %}<tr><td>{{t['name']}}</td><td>{{t['assigned_to']}}</td><td>{{t['end_date']}}</td><td>{{t['status']}}</td></tr>{% endfor %}</table>{% else %}<p>No activities are currently overdue based on the sample dates.</p>{% endif %}</div>"""
    return page("Dashboard",body,p=p,req=req,pending=pending,delayed=delayed,critical=critical,spent=spent,planned=planned,completed=completed,money=money)

@app.route("/project",methods=["GET","POST"])
def project():
    conn=db()
    if request.method=="POST":
        try:
            budget=float(request.form["budget"]); start=request.form["start_date"]; deadline=request.form["deadline"]
            if budget<=0 or date.fromisoformat(deadline)<date.fromisoformat(start): raise ValueError("Budget must be positive and deadline cannot precede start date.")
            conn.execute("""UPDATE project SET name=?,objectives=?,stakeholders=?,scope_in=?,scope_out=?,budget=?,start_date=?,deadline=?,status=?,closure_notes=? WHERE id=1""",
            (request.form["name"].strip(),request.form["objectives"].strip(),request.form["stakeholders"].strip(),request.form["scope_in"].strip(),request.form["scope_out"].strip(),budget,start,deadline,request.form["status"],request.form["closure_notes"].strip()))
            log(conn,"UPDATE PROJECT CHARTER","Updated project charter and baseline.");conn.commit();flash("Project charter saved.")
        except Exception as e: flash("Validation error: "+str(e))
        finally: conn.close()
        return redirect(url_for("project"))
    p=conn.execute("SELECT * FROM project WHERE id=1").fetchone();conn.close()
    body="""<h2>Project Initiation & Integration</h2><div class="card"><form method="post">
    <label>Project name</label><input name="name" required value="{{p['name']}}">
    <label>Objectives</label><textarea name="objectives" required>{{p['objectives']}}</textarea>
    <label>Stakeholders</label><textarea name="stakeholders" required>{{p['stakeholders']}}</textarea>
    <label>In-scope deliverables</label><textarea name="scope_in" required>{{p['scope_in']}}</textarea>
    <label>Out-of-scope boundaries</label><textarea name="scope_out" required>{{p['scope_out']}}</textarea>
    <div class="formgrid"><div><label>Approved budget (PKR)</label><input type="number" min="1" step="1000" name="budget" required value="{{p['budget']}}"></div>
    <div><label>Start date</label><input type="date" name="start_date" required value="{{p['start_date']}}"></div>
    <div><label>Deadline</label><input type="date" name="deadline" required value="{{p['deadline']}}"></div>
    <div><label>Status</label><select name="status">{% for s in ['In Progress','On Hold','Completed','Cancelled'] %}<option {% if p['status']==s %}selected{% endif %}>{{s}}</option>{% endfor %}</select></div></div>
    <label>Closure notes</label><textarea name="closure_notes">{{p['closure_notes']}}</textarea><button>Save project charter</button></form></div>
    <div class="card"><h3>Management plan</h3><p><b>Scope:</b> see in-scope and out-of-scope fields above.</p><p><b>Schedule:</b> activities and dependencies are managed in Schedule & Resources.</p><p><b>Cost:</b> task budgets and EVM indicators are in Cost & EVM.</p><p><b>Quality:</b> inspection results, defects and risks are tracked in Quality & Risks.</p></div>"""
    return page("Project Charter",body,p=p)

@app.route("/requirements",methods=["GET","POST"])
def requirements():
    if request.method=="POST":
        try:
            title=request.form["title"].strip()
            if not title: raise ValueError("Requirement title is required.")
            status=request.form["status"]; approved=1 if status=="Approved" else 0
            conn=db();conn.execute("INSERT INTO requirements(title,description,priority,status,approved_scope) VALUES(?,?,?,?,?)",(title,request.form["description"].strip(),request.form["priority"],status,approved));log(conn,"ADD REQUIREMENT",title);conn.commit();conn.close();flash("Requirement added.")
        except Exception as e: flash("Validation error: "+str(e))
        return redirect(url_for("requirements"))
    reqs=rows("SELECT * FROM requirements ORDER BY id")
    body="""<h2>Scope Management & Work Breakdown Structure</h2><div class="card"><h3>Add requirement</h3><form method="post"><div class="formgrid"><div><label>Title</label><input name="title" required></div><div><label>Priority</label><select name="priority"><option>High</option><option>Medium</option><option>Low</option></select></div><div><label>Status</label><select name="status"><option>Proposed</option><option>Approved</option><option>Rejected</option></select></div></div><label>Description</label><textarea name="description"></textarea><button>Add requirement</button></form><p class="muted">Only requirements with status Approved are counted in the approved scope.</p></div>
    <div class="card"><h3>Requirements register</h3><table><tr><th>ID</th><th>Requirement</th><th>Priority</th><th>Status</th><th>In approved scope?</th><th>Action</th></tr>{% for r in reqs %}<tr><td>{{r['id']}}</td><td><b>{{r['title']}}</b><br><span class="muted">{{r['description']}}</span></td><td>{{r['priority']}}</td><td>{{r['status']}}</td><td>{{'Yes' if r['approved_scope'] else 'No'}}</td><td><form method="post" action="/requirements/{{r['id']}}/status" class="inline"><select name="status"><option>Proposed</option><option>Approved</option><option>Rejected</option></select><button class="secondary">Update</button></form></td></tr>{% endfor %}</table></div>
    <div class="card"><h3>Hierarchical WBS</h3><table><tr><th>WBS</th><th>Deliverable / Work package</th><th>Scope relationship</th></tr>
    <tr><td>1.0</td><td>Project initiation and planning</td><td>Charter, requirements, plan</td></tr><tr><td>2.0</td><td>Core healthcare system</td><td>Appointments, lab reports, doctor schedules</td></tr><tr><td>2.1</td><td>Appointment management</td><td>Approved requirement</td></tr><tr><td>2.2</td><td>Laboratory report management</td><td>Approved requirement</td></tr><tr><td>2.3</td><td>Doctor scheduling</td><td>Approved requirement</td></tr><tr><td>2.4</td><td>Online consultation and billing</td><td>Approved requirements</td></tr><tr><td>3.0</td><td>Integration, testing and deployment</td><td>Core delivery</td></tr><tr><td>4.0</td><td>AI diagnosis and mobile app</td><td>Excluded until change request is approved</td></tr></table></div>"""
    return page("Scope & WBS",body,reqs=reqs)

@app.route("/requirements/<int:rid>/status",methods=["POST"])
def requirement_status(rid):
    status=request.form.get("status","Proposed")
    if status not in ["Proposed","Approved","Rejected"]: status="Proposed"
    conn=db();cur=conn.execute("UPDATE requirements SET status=?,approved_scope=? WHERE id=?",(status,1 if status=="Approved" else 0,rid))
    if cur.rowcount: log(conn,"REQUIREMENT STATUS",f"Requirement {rid} set to {status}.")
    conn.commit();conn.close();flash("Requirement status updated." if cur.rowcount else "Requirement not found.")
    return redirect(url_for("requirements"))

@app.route("/changes",methods=["GET","POST"])
def changes():
    if request.method=="POST":
        try:
            title=request.form["title"].strip(); justification=request.form["justification"].strip()
            cost=float(request.form["cost_impact"]); weeks=int(request.form["weeks_impact"])
            if not title or not justification or cost<0 or weeks<0: raise ValueError("Title/justification required; cost and weeks cannot be negative.")
            conn=db();conn.execute("INSERT INTO changes(title,justification,cost_impact,weeks_impact,status,requirement_id) VALUES(?,?,?,?,?,?,?)".replace("VALUES(?,?,?,?,?,?,?)","VALUES(?,?,?,?,?,?)"),
             (title,justification,cost,weeks,"Pending",int(request.form["requirement_id"]) if request.form.get("requirement_id") else None))
            log(conn,"NEW CHANGE REQUEST",title);conn.commit();conn.close();flash("Change request submitted for approval.")
        except Exception as e: flash("Validation error: "+str(e))
        return redirect(url_for("changes"))
    changes=rows("SELECT c.*,r.title req_title FROM changes c LEFT JOIN requirements r ON c.requirement_id=r.id ORDER BY c.id DESC")
    reqs=rows("SELECT * FROM requirements")
    body="""<h2>Change Request Management</h2><div class="card"><h3>Submit change request</h3><form method="post"><div class="formgrid"><div><label>Change title</label><input name="title" required></div><div><label>Cost impact (PKR)</label><input type="number" name="cost_impact" min="0" step="1000" value="0" required></div><div><label>Schedule impact (weeks)</label><input type="number" name="weeks_impact" min="0" value="0" required></div><div><label>Related requirement</label><select name="requirement_id"><option value="">None</option>{% for r in reqs %}<option value="{{r['id']}}">{{r['title']}}</option>{% endfor %}</select></div></div><label>Justification</label><textarea name="justification" required></textarea><button>Submit request</button></form></div>
    <div class="card"><h3>Change register</h3><table><tr><th>Change</th><th>Impact</th><th>Status</th><th>Justification</th><th>Decision</th></tr>{% for c in changes %}<tr><td><b>#{{c['id']}} {{c['title']}}</b><br><span class="muted">Requirement: {{c['req_title'] or 'Not linked'}}</span></td><td>{{money(c['cost_impact'])}}<br>{{c['weeks_impact']}} week(s)</td><td>{{c['status']}}</td><td>{{c['justification']}}</td><td>{% if c['status']=='Pending' %}<form method="post" action="/changes/{{c['id']}}/decision"><input name="notes" placeholder="Decision notes"><button name="decision" value="Approved">Approve</button><button class="danger" name="decision" value="Rejected">Reject</button></form>{% else %}{{c['decision_notes']}}{% endif %}</td></tr>{% endfor %}</table></div>
    <div class="card"><h3>Change control rule</h3><p>Pending or rejected changes do not alter the baseline. When approved, the project budget increases by the recorded cost impact, the deadline moves by the schedule impact, the linked requirement is added to approved scope, and an audit record is created.</p></div>"""
    return page("Change Requests",body,changes=changes,reqs=reqs,money=money)

@app.route("/changes/<int:cid>/decision",methods=["POST"])
def change_decision(cid):
    decision=request.form.get("decision")
    if decision not in ("Approved","Rejected"): flash("Invalid decision.");return redirect(url_for("changes"))
    conn=db()
    try:
        c=conn.execute("SELECT * FROM changes WHERE id=?",(cid,)).fetchone()
        if not c: flash("Change request not found.")
        elif c["status"]!="Pending": flash("This request has already been decided.")
        else:
            notes=request.form.get("notes","").strip()
            conn.execute("UPDATE changes SET status=?,decision_notes=? WHERE id=?",(decision,notes,cid))
            if decision=="Approved":
                p=conn.execute("SELECT * FROM project WHERE id=1").fetchone()
                new_budget=p["budget"]+c["cost_impact"]
                new_deadline=(date.fromisoformat(p["deadline"])+timedelta(weeks=c["weeks_impact"])).isoformat()
                conn.execute("UPDATE project SET budget=?,deadline=? WHERE id=1",(new_budget,new_deadline))
                if c["requirement_id"]:
                    conn.execute("UPDATE requirements SET status='Approved',approved_scope=1 WHERE id=?",(c["requirement_id"],))
                # Recalculate end dates for all activities by adding schedule impact to baseline.
                if c["weeks_impact"]:
                    for t in conn.execute("SELECT id,start_date,end_date FROM tasks").fetchall():
                        ns=(date.fromisoformat(t["start_date"])+timedelta(weeks=c["weeks_impact"])).isoformat()
                        ne=(date.fromisoformat(t["end_date"])+timedelta(weeks=c["weeks_impact"])).isoformat()
                        conn.execute("UPDATE tasks SET start_date=?,end_date=? WHERE id=?",(ns,ne,t["id"]))
                log(conn,"APPROVE CHANGE",f"Change #{cid}: budget {money(p['budget'])} -> {money(new_budget)}; deadline {p['deadline']} -> {new_deadline}; schedule +{c['weeks_impact']} weeks.")
                flash(f"Change approved. Budget is now {money(new_budget)} and deadline is {new_deadline}.")
            else:
                log(conn,"REJECT CHANGE",f"Change #{cid} rejected.")
                flash("Change rejected; baseline unchanged.")
        conn.commit()
    except Exception as e:
        conn.rollback();flash("Could not process decision: "+str(e))
    finally: conn.close()
    return redirect(url_for("changes"))

@app.route("/schedule",methods=["GET","POST"])
def schedule():
    if request.method=="POST":
        try:
            name=request.form["name"].strip(); dur=int(request.form["duration"]); cost=float(request.form["planned_cost"])
            if not name or dur<1 or cost<0: raise ValueError("Name is required; duration must be at least one day; cost cannot be negative.")
            st=date.fromisoformat(request.form["start_date"])
            dep=int(request.form["dependency_id"]) if request.form.get("dependency_id") else None
            if dep:
                dep_task=one("SELECT * FROM tasks WHERE id=?",(dep,))
                if not dep_task: raise ValueError("Dependency task does not exist.")
                earliest=date.fromisoformat(dep_task["end_date"])+timedelta(days=1)
                if st<earliest: st=earliest
            en=st+timedelta(days=dur-1)
            conn=db();conn.execute("""INSERT INTO tasks(wbs,name,duration,start_date,end_date,dependency_id,assigned_to,planned_cost,actual_cost,percent_complete,status,milestone)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(request.form["wbs"].strip(),name,dur,st.isoformat(),en.isoformat(),dep,request.form["assigned_to"].strip(),cost,float(request.form.get("actual_cost") or 0),int(request.form.get("percent_complete") or 0),"Not Started",1 if request.form.get("milestone") else 0))
            log(conn,"ADD TASK",name);conn.commit();conn.close();flash("Activity added. Dependency was checked.")
        except Exception as e: flash("Validation error: "+str(e))
        return redirect(url_for("schedule"))
    tasks=rows("SELECT t.*,d.name dependency_name FROM tasks t LEFT JOIN tasks d ON t.dependency_id=d.id ORDER BY t.id")
    p=one("SELECT * FROM project WHERE id=1")
    start=date.fromisoformat(p["start_date"]); end=date.fromisoformat(p["deadline"]); span=max(1,(end-start).days)
    for t in tasks:
        t=dict(t); st=date.fromisoformat(t["start_date"]); en=date.fromisoformat(t["end_date"])
        t["left"]=max(0,min(100,(st-start).days/span*100)); t["width"]=max(2,min(100-t["left"],(en-st).days/span*100+2))
        t["late"]=t["status"]!="Completed" and en<date.today()
        # keep display data in separate list
    timeline=[]
    for t in tasks:
        d=dict(t); st=date.fromisoformat(d["start_date"]); en=date.fromisoformat(d["end_date"])
        d["left"]=max(0,min(100,(st-start).days/span*100));d["width"]=max(2,min(100-d["left"],(en-st).days/span*100+2));d["late"]=d["status"]!="Completed" and en<date.today();timeline.append(d)
    body="""<h2>Schedule & Resource Management</h2><div class="card"><h3>Add activity</h3><form method="post"><div class="formgrid"><div><label>WBS code</label><input name="wbs" required placeholder="2.5"></div><div><label>Activity name</label><input name="name" required></div><div><label>Duration (days)</label><input type="number" min="1" name="duration" required value="5"></div><div><label>Start date</label><input type="date" name="start_date" required value="{{today}}"></div><div><label>Dependency</label><select name="dependency_id"><option value="">No dependency</option>{% for t in tasks %}<option value="{{t['id']}}">#{{t['id']}} {{t['name']}}</option>{% endfor %}</select></div><div><label>Assigned team member</label><input name="assigned_to" required placeholder="QA Engineer"></div><div><label>Planned cost (PKR)</label><input type="number" min="0" name="planned_cost" value="0" required></div><div><label>Actual cost (PKR)</label><input type="number" min="0" name="actual_cost" value="0"></div><div><label>Completion %</label><input type="number" min="0" max="100" name="percent_complete" value="0"></div></div><label><input type="checkbox" name="milestone" style="width:auto"> Milestone</label><button>Add activity</button></form></div>
    <div class="card"><h3>Gantt-style timeline</h3><p class="muted">Bars are positioned against the project baseline. Red bars indicate activities past their planned end date and not marked completed.</p>{% for t in timeline %}<div class="timeline"><div><b>{{t['wbs']}} {{t['name']}}</b><br><span class="muted">{{t['start_date']}} – {{t['end_date']}}</span></div><div class="track"><div class="taskbar {% if t['late'] %}late{% endif %}" style="margin-left:{{t['left']}}%;width:{{t['width']}}%">{{t['percent_complete']}}% · {{t['assigned_to']}}</div></div></div>{% endfor %}</div>
    <div class="card"><h3>Activity register</h3><table><tr><th>WBS / Activity</th><th>Duration</th><th>Dates</th><th>Dependency</th><th>Resource</th><th>Cost (planned / actual)</th><th>Completion</th><th>Status</th></tr>{% for t in tasks %}<tr><td>{{t['wbs']}}<br>{{t['name']}}{% if t['milestone'] %}<br><span class="badge">Milestone</span>{% endif %}</td><td>{{t['duration']}} days</td><td>{{t['start_date']}}<br>{{t['end_date']}}</td><td>{{t['dependency_name'] or 'None'}}</td><td>{{t['assigned_to']}}</td><td>{{money(t['planned_cost'])}}<br>{{money(t['actual_cost'])}}</td><td>{{t['percent_complete']}}%</td><td>{% if t['late'] %}<span class="dangertext">Delayed</span>{% else %}{{t['status']}}{% endif %}</td></tr>{% endfor %}</table></div>"""
    return page("Schedule",body,tasks=tasks,timeline=timeline,today=date.today().isoformat(),money=money)

@app.route("/cost",methods=["GET","POST"])
def cost():
    if request.method=="POST":
        try:
            tid=int(request.form["task_id"]); actual=float(request.form["actual_cost"]); complete=int(request.form["percent_complete"])
            if actual<0 or not 0<=complete<=100: raise ValueError("Actual cost must be non-negative and completion must be 0–100.")
            status="Completed" if complete==100 else ("In Progress" if complete>0 else "Not Started")
            conn=db();cur=conn.execute("UPDATE tasks SET actual_cost=?,percent_complete=?,status=? WHERE id=?",(actual,complete,status,tid))
            if not cur.rowcount: raise ValueError("Activity not found.")
            log(conn,"UPDATE COST / PROGRESS",f"Task {tid}: actual cost {actual}; completion {complete}%.");conn.commit();conn.close();flash("Cost and completion updated.")
        except Exception as e: flash("Validation error: "+str(e))
        return redirect(url_for("cost"))
    p=one("SELECT * FROM project WHERE id=1");tasks=rows("SELECT * FROM tasks")
    pv=sum(t["planned_cost"] for t in tasks); ev=sum(t["planned_cost"]*t["percent_complete"]/100 for t in tasks); ac=sum(t["actual_cost"] for t in tasks)
    cpi=ev/ac if ac else None; spi=ev/pv if pv else None
    variance=ac-p["budget"]
    body="""<h2>Cost Management & Earned Value Analysis</h2><div class="grid">
    <div class="card"><div class="muted">Planned Value (PV)</div><div class="kpi">{{money(pv)}}</div><div class="muted">Total planned activity cost</div></div>
    <div class="card"><div class="muted">Earned Value (EV)</div><div class="kpi">{{money(ev)}}</div><div class="muted">Planned cost × completion %</div></div>
    <div class="card"><div class="muted">Actual Cost (AC)</div><div class="kpi">{{money(ac)}}</div><div class="muted">Recorded expenditure</div></div>
    <div class="card"><div class="muted">CPI</div><div class="kpi">{{'%.2f' % cpi if cpi is not none else 'N/A'}}</div><div class="muted">EV / AC; below 1 means cost inefficiency</div></div>
    <div class="card"><div class="muted">SPI</div><div class="kpi">{{'%.2f' % spi if spi is not none else 'N/A'}}</div><div class="muted">EV / PV; below 1 means behind plan</div></div>
    <div class="card"><div class="muted">Budget variance (AC − baseline)</div><div class="kpi">{{money(variance)}}</div><div class="muted">Positive means actual cost exceeds budget</div></div></div>
    {% if ac>p['budget'] %}<p class="dangertext">WARNING: Actual cost exceeds the approved project budget.</p>{% endif %}{% if cpi is not none and cpi<0.9 %}<p class="dangertext">WARNING: CPI is below 0.90; investigate cost performance.</p>{% endif %}{% if spi is not none and spi<0.9 %}<p class="dangertext">WARNING: SPI is below 0.90; investigate schedule performance.</p>{% endif %}
    <div class="card"><h3>Update activity cost and progress</h3><form method="post"><div class="formgrid"><div><label>Activity</label><select name="task_id">{% for t in tasks %}<option value="{{t['id']}}">#{{t['id']}} {{t['name']}}</option>{% endfor %}</select></div><div><label>Actual cost to date (PKR)</label><input type="number" min="0" step="1000" name="actual_cost" required></div><div><label>Completion (%)</label><input type="number" min="0" max="100" name="percent_complete" required></div></div><button>Update performance</button></form></div>
    <div class="card"><h3>Activity cost register</h3><table><tr><th>Activity</th><th>Planned cost</th><th>Actual cost</th><th>Completion</th><th>Earned value</th></tr>{% for t in tasks %}<tr><td>{{t['name']}}</td><td>{{money(t['planned_cost'])}}</td><td>{{money(t['actual_cost'])}}</td><td>{{t['percent_complete']}}%</td><td>{{money(t['planned_cost']*t['percent_complete']/100)}}</td></tr>{% endfor %}</table></div>
    <div class="card"><h3>Formula reference</h3><p>PV = total planned activity cost; EV = Σ(planned cost × percent complete); AC = Σ actual cost; CPI = EV / AC; SPI = EV / PV.</p><p class="muted">This teaching implementation uses the activity cost baseline as PV. In a production system, PV should be time-phased to the selected status date.</p></div>"""
    return page("Cost & EVM",body,p=p,tasks=tasks,pv=pv,ev=ev,ac=ac,cpi=cpi,spi=spi,variance=variance,money=money)

@app.route("/quality",methods=["GET","POST"])
def quality():
    if request.method=="POST":
        kind=request.form.get("kind")
        conn=db()
        try:
            if kind=="defect":
                title=request.form["title"].strip()
                if not title: raise ValueError("Defect title required.")
                conn.execute("INSERT INTO defects(title,description,severity,assigned_to,status) VALUES(?,?,?,?,?)",(title,request.form["description"],request.form["severity"],request.form["assigned_to"].strip(),request.form["status"]))
                log(conn,"ADD DEFECT",title)
            elif kind=="quality":
                conn.execute("INSERT INTO quality_checks(deliverable,checklist_item,result,notes,inspected_by) VALUES(?,?,?,?,?)",(request.form["deliverable"].strip(),request.form["checklist_item"].strip(),request.form["result"],request.form["notes"],request.form["inspected_by"].strip()))
                log(conn,"QUALITY INSPECTION",request.form["checklist_item"])
            elif kind=="risk":
                l=int(request.form["likelihood"]); i=int(request.form["impact"])
                if not (1<=l<=5 and 1<=i<=5): raise ValueError("Likelihood and impact must be 1–5.")
                conn.execute("INSERT INTO risks(title,likelihood,impact,response,owner,status) VALUES(?,?,?,?,?,?)",(request.form["risk_title"].strip(),l,i,request.form["response"].strip(),request.form["owner"].strip(),request.form["risk_status"]))
                log(conn,"ADD RISK",request.form["risk_title"])
            conn.commit();flash("Record saved.")
        except Exception as e: conn.rollback();flash("Validation error: "+str(e))
        finally: conn.close()
        return redirect(url_for("quality"))
    defects=rows("SELECT * FROM defects ORDER BY CASE severity WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,id")
    checks=rows("SELECT * FROM quality_checks ORDER BY id DESC")
    risks=rows("SELECT * FROM risks ORDER BY likelihood*impact DESC")
    body="""<h2>Quality Management & Risk Control</h2><div class="card"><h3>Record defect</h3><form method="post"><input type="hidden" name="kind" value="defect"><div class="formgrid"><div><label>Defect title</label><input name="title" required></div><div><label>Severity</label><select name="severity"><option>Critical</option><option>High</option><option>Medium</option><option>Low</option></select></div><div><label>Assigned personnel</label><input name="assigned_to" required></div><div><label>Status</label><select name="status"><option>Open</option><option>In Progress</option><option>Resolved</option></select></div></div><label>Description</label><textarea name="description"></textarea><button>Add defect</button></form></div>
    <div class="card"><h3>Defect register</h3><table><tr><th>ID</th><th>Defect</th><th>Severity</th><th>Assigned to</th><th>Status</th><th>Update</th></tr>{% for d in defects %}<tr><td>{{d['id']}}</td><td>{{d['title']}}<br><span class="muted">{{d['description']}}</span></td><td>{% if d['severity']=='Critical' %}<span class="dangertext">Critical</span>{% else %}{{d['severity']}}{% endif %}</td><td>{{d['assigned_to']}}</td><td>{{d['status']}}</td><td><form method="post" action="/defects/{{d['id']}}/status"><select name="status"><option>Open</option><option>In Progress</option><option>Resolved</option></select><button class="secondary">Save</button></form></td></tr>{% endfor %}</table></div>
    <div class="card"><h3>Quality checklist / inspection result</h3><form method="post"><input type="hidden" name="kind" value="quality"><div class="formgrid"><div><label>Deliverable</label><input name="deliverable" required></div><div><label>Checklist item</label><input name="checklist_item" required></div><div><label>Result</label><select name="result"><option>Pass</option><option>Fail</option><option>Blocked</option></select></div><div><label>Inspected by</label><input name="inspected_by" required></div></div><label>Notes</label><textarea name="notes"></textarea><button>Save inspection</button></form>
    <table><tr><th>Deliverable</th><th>Checklist item</th><th>Result</th><th>Notes</th><th>Inspector</th></tr>{% for q in checks %}<tr><td>{{q['deliverable']}}</td><td>{{q['checklist_item']}}</td><td class="{% if q['result']=='Pass' %}pass{% else %}fail{% endif %}">{{q['result']}}</td><td>{{q['notes']}}</td><td>{{q['inspected_by']}}</td></tr>{% endfor %}</table></div>
    <div class="card"><h3>Prioritization matrix / risk register</h3><p class="muted">Risk score = likelihood × impact. Scale: 1–5 for each dimension. Higher scores require earlier attention.</p><table><tr><th>Risk</th><th>Likelihood</th><th>Impact</th><th>Score</th><th>Priority</th><th>Owner / status</th><th>Response (PDPC)</th></tr>{% for r in risks %}<tr><td>{{r['title']}}</td><td>{{r['likelihood']}}</td><td>{{r['impact']}}</td><td>{{r['likelihood']*r['impact']}}</td><td>{% if r['likelihood']*r['impact']>=15 %}<span class="dangertext">High</span>{% elif r['likelihood']*r['impact']>=8 %}Medium{% else %}Low{% endif %}</td><td>{{r['owner']}}<br>{{r['status']}}</td><td>{{r['response']}}</td></tr>{% endfor %}</table>
    <h3>Add risk / PDPC response</h3><form method="post"><input type="hidden" name="kind" value="risk"><div class="formgrid"><div><label>Risk title</label><input name="risk_title" required></div><div><label>Likelihood (1–5)</label><input type="number" name="likelihood" min="1" max="5" required></div><div><label>Impact (1–5)</label><input type="number" name="impact" min="1" max="5" required></div><div><label>Owner</label><input name="owner" required></div><div><label>Status</label><select name="risk_status"><option>Open</option><option>Mitigating</option><option>Closed</option></select></div></div><label>Preventive / corrective action</label><textarea name="response" required></textarea><button>Add risk</button></form></div>"""
    return page("Quality & Risks",body,defects=defects,checks=checks,risks=risks)

@app.route("/defects/<int:did>/status",methods=["POST"])
def defect_status(did):
    status=request.form.get("status")
    if status not in ("Open","In Progress","Resolved"): status="Open"
    conn=db();cur=conn.execute("UPDATE defects SET status=? WHERE id=?",(status,did))
    if cur.rowcount: log(conn,"UPDATE DEFECT",f"Defect {did} status set to {status}.")
    conn.commit();conn.close();flash("Defect updated." if cur.rowcount else "Defect not found.")
    return redirect(url_for("quality"))

@app.route("/reports")
def reports():
    p=one("SELECT * FROM project WHERE id=1")
    tasks=rows("SELECT * FROM tasks ORDER BY id")
    changes=rows("SELECT * FROM changes ORDER BY id DESC")
    defects=rows("SELECT * FROM defects ORDER BY id")
    audit=rows("SELECT * FROM audit_log ORDER BY id DESC LIMIT 50")
    pv=sum(t["planned_cost"] for t in tasks);ev=sum(t["planned_cost"]*t["percent_complete"]/100 for t in tasks);ac=sum(t["actual_cost"] for t in tasks)
    pending=sum(1 for c in changes if c["status"]=="Pending")
    delayed=[t for t in tasks if t["status"]!="Completed" and t["end_date"]<date.today().isoformat()]
    critical=[d for d in defects if d["severity"]=="Critical" and d["status"]!="Resolved"]
    body="""<h2>Reports, Validation & Audit Trail</h2><div class="card"><h3>Executive report</h3><p><b>Project:</b> {{p['name']}}</p><p><b>Baseline budget:</b> {{money(p['budget'])}} · <b>Deadline:</b> {{p['deadline']}}</p><p><b>PV:</b> {{money(pv)}} · <b>EV:</b> {{money(ev)}} · <b>AC:</b> {{money(ac)}}</p><p><b>Pending change requests:</b> {{pending}} · <b>Delayed activities:</b> {{delayed|length}} · <b>Unresolved critical defects:</b> {{critical|length}}</p>
    {% if pending or delayed or critical %}<p class="dangertext">Management attention required: review pending changes, schedule variance and critical defects.</p>{% else %}<p class="good">No pending change requests, delayed activities or unresolved critical defects detected.</p>{% endif %}</div>
    <div class="card"><h3>Change request report</h3><table><tr><th>ID</th><th>Request</th><th>Cost impact</th><th>Weeks</th><th>Status</th></tr>{% for c in changes %}<tr><td>{{c['id']}}</td><td>{{c['title']}}</td><td>{{money(c['cost_impact'])}}</td><td>{{c['weeks_impact']}}</td><td>{{c['status']}}</td></tr>{% endfor %}</table></div>
    <div class="card"><h3>Audit trail (latest 50)</h3><table><tr><th>Timestamp</th><th>Action</th><th>Details</th></tr>{% for a in audit %}<tr><td>{{a['created_at']}}</td><td>{{a['action']}}</td><td>{{a['details']}}</td></tr>{% endfor %}</table></div>
    <div class="card"><a class="btn" href="/export.json">Export report data (JSON)</a></div>"""
    return page("Reports",body,p=p,tasks=tasks,changes=changes,defects=defects,audit=audit,pv=pv,ev=ev,ac=ac,pending=pending,delayed=delayed,critical=critical,money=money)

@app.route("/export.json")
def export_json():
    from flask import jsonify
    conn=db()
    data={}
    for table in ["project","requirements","changes","tasks","defects","quality_checks","risks","audit_log"]:
        data[table]=[dict(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
    conn.close()
    return app.response_class(json.dumps(data,indent=2),mimetype="application/json",headers={"Content-Disposition":"attachment; filename=healthcare_pms_report.json"})

@app.errorhandler(404)
def not_found(e): return page("Not found","<div class='card'><h2>Record not found</h2><p>The requested record or page does not exist.</p><a class='btn' href='/'>Back to dashboard</a></div>"),404
@app.errorhandler(500)
def server_error(e): return page("Error","<div class='card'><h2>Unexpected error</h2><p>The request could not be completed. Check the terminal log and retry.</p></div>"),500

init_db()
if __name__=="__main__":
    app.run(debug=False, host="127.0.0.1", port=int(os.environ.get("PORT","5000")))
