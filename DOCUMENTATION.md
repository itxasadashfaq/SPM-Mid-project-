# Project Documentation

## 1. Introduction
The Smart Healthcare Project Management System is a browser-based project management application for planning and monitoring development of a healthcare platform serving five hospitals. It addresses project charter, requirements, schedule, resources, budget, earned value, quality, risks, change control, reporting and audit history.

## 2. Problem statement
The project has a 16-week baseline and a PKR 5,000,000 approved budget. New AI diagnosis and mobile application requests add PKR 800,000 and three weeks. Critical defects also exist in appointment scheduling and patient records. A project manager needs a central system to control scope, cost, schedule and quality.

## 3. Objectives
- Store and update project charter and management plan information.
- Separate proposed requirements from approved scope.
- Record change requests and prevent pending/rejected changes from modifying the baseline.
- Approve changes in a controlled way and reflect their impact on budget, deadline, scope and schedule.
- Track activities, dependencies, resources, dates and completion.
- Calculate PV, EV, AC, CPI and SPI programmatically.
- Track defects, quality inspections and risk response actions.
- Generate an executive summary and audit trail.

## 4. Technology stack
- Frontend: HTML, CSS, Jinja templates, browser forms.
- Backend: Python 3 and Flask.
- Database: SQLite.
- Charts: CSS-based Gantt-style timeline and KPI bars.

## 5. Main modules
### Project Initiation and Integration
The project charter stores objectives, stakeholders, scope boundaries, budget, start date, deadline, status and closure notes.

### Scope Management and WBS
The requirements register stores title, description, priority and status. Only approved requirements have `approved_scope = 1`. A hierarchical WBS groups work into initiation, core system, integration/testing/deployment, and proposed change deliverables.

### Schedule and Resource Management
Activities store WBS code, duration, start/end dates, predecessor, owner, planned and actual costs, completion and milestone status. When adding a task with a dependency, the start date is moved after the predecessor's end date if needed. The timeline highlights overdue unfinished activities.

### Cost Management and EVM
PV is calculated from planned task costs. EV is calculated as planned cost multiplied by completion percentage. AC is the sum of actual costs. CPI = EV/AC and SPI = EV/PV. Threshold warnings are shown when CPI or SPI is below 0.90, and a budget warning is shown when AC exceeds the approved budget.

### Quality and Risk Control
Defects store severity, owner and status. Quality inspections store deliverable, checklist item, result and notes. Risk score is likelihood multiplied by impact, both rated 1 to 5. The response field acts as a Process Decision Program Chart (PDPC)-style corrective/preventive response.

### Integration and Reporting
All modules use one SQLite database. The dashboard and executive report summarize budget, progress, pending changes, overdue activities and unresolved critical defects. Audit entries are recorded for key actions; reports can be exported as JSON.

## 6. Change-control demonstration
The sample AI/mobile request begins as Pending. Pending and rejected requests do not change the project baseline. Approving it increases the budget by PKR 800,000, extends the deadline by three weeks, shifts task dates by three weeks, approves the linked requirement, and creates an audit entry.

## 7. Database schema
- `project`: one baseline/charter row.
- `requirements`: project requirements and approved-scope flag.
- `changes`: change request, justification, cost/schedule impacts, decision.
- `tasks`: WBS activity, duration, dependency, resource, costs and progress.
- `defects`: quality defects and resolution status.
- `quality_checks`: checklist and inspection outcomes.
- `risks`: likelihood, impact, response, owner and status.
- `audit_log`: timestamped record of important actions.

## 8. Validation and error handling
Required fields are checked; budgets and costs must be non-negative/positive as appropriate; deadlines cannot precede start dates; durations must be at least one day; completion must be 0–100; risk likelihood/impact must be 1–5; invalid change decisions are rejected; duplicate decisions are blocked; missing records display an error message.

## 9. Running the application
See README.md. On Windows, create a virtual environment, install `requirements.txt`, run `python app.py`, then browse to `http://127.0.0.1:5000`.

## 10. Demonstration sequence
1. Show Dashboard and explain the case-study baseline.
2. Show Project Charter and the management plan.
3. Show approved versus proposed requirements and WBS.
4. Show the pending AI/mobile request and unchanged baseline.
5. Approve the change and demonstrate the new PKR 5,800,000 budget and three-week extension.
6. Show the schedule timeline and team resources.
7. Update task actual cost/completion and explain EVM formulas.
8. Show critical defects, quality checklist and risk matrix/PDPC responses.
9. Show executive report, audit trail and JSON export.

## 11. Limitations
This is an academic prototype using fictional data, not a production medical system. Authentication, permissions, production deployment, full critical-path scheduling, and time-phased PV are outside this prototype's scope. The student should run the application and record observed test outcomes before submission.
