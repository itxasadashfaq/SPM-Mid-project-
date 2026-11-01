# Smart Healthcare Project Management System

A local Flask + SQLite web application built for the COMSATS Software Project Management mid-term case study.

## Features
- Project charter and baseline management
- Requirements register with explicit scope approval and hierarchical WBS
- Change requests with approve/reject workflow; approval changes budget, deadline, schedule dates and linked requirement scope
- Task/resource register with dependencies, date calculations and Gantt-style timeline
- Cost tracking and Earned Value Management (PV, EV, AC, CPI, SPI)
- Defect register, quality inspection checklist, risk prioritization matrix and PDPC-style response actions
- Dashboard, executive report, audit trail and JSON export
- SQLite persistent database and realistic sample records

## Requirements
- Python 3.10 or later
- Internet connection only for installing Flask the first time (or install Flask in advance)

## Run on Windows
1. Extract the ZIP.
2. Open the extracted `smart_healthcare_pms` folder.
3. In the address bar of File Explorer, type `cmd` and press Enter.
4. Run:
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   py -m pip install -r requirements.txt
   py app.py
   ```
5. Open `http://127.0.0.1:5000` in your browser.
6. Stop the server with `Ctrl+C`.

If `py` is not recognized, use `python` instead. The database `healthcare_pms.db` is created automatically on first launch and persists between runs.

## Case-study demonstration
1. Open Change Requests. The AI preliminary diagnosis and mobile application request is initially Pending with PKR 800,000 and 3 weeks of impact.
2. Confirm the request is Pending. The baseline budget and deadline must not yet change.
3. Approve it. The project budget increases from PKR 5,000,000 to PKR 5,800,000; deadline extends by three weeks; schedule dates shift by three weeks; the linked requirement is approved into scope; the action is written to the audit trail.
4. Open Cost & EVM. Change an activity's actual cost or completion percentage and observe PV, EV, AC, CPI and SPI recalculate.
5. Open Quality & Risks. Resolve a critical defect or add a quality inspection/risk.
6. Open Reports / Audit to review the executive summary and change history.

## Calculation notes
- PV = sum of task planned costs (simplified baseline for this educational implementation).
- EV = sum of planned task cost × percent complete.
- AC = sum of task actual cost.
- CPI = EV / AC; SPI = EV / PV. Values are N/A if their denominator is zero.
- Risk score = likelihood × impact on a 1–5 scale.
- Overdue activities are unfinished activities with a planned end date earlier than the current date.
- Dates are calculated for task durations in days. Project case-study deadline is represented in weeks via the start date and deadline fields.

## Database
SQLite file: `healthcare_pms.db`. Tables: `project`, `requirements`, `changes`, `tasks`, `defects`, `quality_checks`, `risks`, `audit_log`.

## Known educational limitations
- This is a local academic prototype, not a production medical system.
- It has no authentication/authorization, cloud deployment, or real patient data.
- PV is not time-phased; a production EVM system would calculate PV at a status date.
- Task dependency handling validates the selected predecessor and pushes a new task's start date after the predecessor's end date. Existing task network recalculation and critical-path analysis are not implemented.
- Approval shifts all activity dates by the requested number of weeks to demonstrate baseline impact; a real project would update only affected work packages using a reviewed schedule.
