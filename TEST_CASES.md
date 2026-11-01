# Test Cases — Smart Healthcare PMS

| ID | Test | Steps / Input | Expected result | Actual result |
|---|---|---|---|---|
| TC-01 | Initial database setup | Run `python app.py` for the first time | SQLite DB is created and sample project, requirements, tasks, defects, checks, risks and change request are seeded | To be recorded during student's local execution |
| TC-02 | Dashboard loads | Open `/` | KPI cards and warnings are displayed without error | To be recorded during student's local execution |
| TC-03 | Invalid budget | Project Charter: enter budget 0 | Validation error; invalid baseline is not saved | To be recorded during student's local execution |
| TC-04 | Requirement scope gate | Add a Proposed requirement | Requirement is stored but shown as not in approved scope | To be recorded during student's local execution |
| TC-05 | Approve requirement | Change requirement status to Approved | `approved_scope` becomes 1 | To be recorded during student's local execution |
| TC-06 | Pending change baseline | Open Change Requests before approval | Budget remains PKR 5,000,000; original deadline unchanged | To be recorded during student's local execution |
| TC-07 | Approve case-study change | Approve AI/mobile request (+PKR 800,000, +3 weeks) | Budget becomes PKR 5,800,000; deadline moves 3 weeks; schedule dates shift 3 weeks; linked requirement enters scope; audit event is recorded | To be recorded during student's local execution |
| TC-08 | Reject change | Submit a new request and reject it | Budget, deadline and task dates remain unchanged | To be recorded during student's local execution |
| TC-09 | EVM calculations | Change a task's actual cost and completion | PV, EV, AC, CPI and SPI recalculate using documented formulas | To be recorded during student's local execution |
| TC-10 | Invalid completion | Enter -1 or 101 percent | Validation error; record is not updated | To be recorded during student's local execution |
| TC-11 | Defect status | Mark a critical defect Resolved | Defect register and dashboard unresolved-critical count update | To be recorded during student's local execution |
| TC-12 | Quality checklist | Add a Failed inspection | Inspection is stored and visible in quality register | To be recorded during student's local execution |
| TC-13 | Risk score | Add risk with likelihood 4 and impact 5 | Score is 20 and priority is High | To be recorded during student's local execution |
| TC-14 | JSON report export | Click Export report data | Browser downloads JSON with application records | To be recorded during student's local execution |
| TC-15 | Persistent storage | Stop and restart application | Previously created records remain in SQLite | To be recorded during student's local execution |

## Important
Run every test locally and replace “To be recorded during student's local execution” with the observed result. Do not claim a test passed until you have actually run it.
