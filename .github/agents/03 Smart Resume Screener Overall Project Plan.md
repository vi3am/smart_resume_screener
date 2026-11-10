# 03 Smart Resume Screener Overall Project Plan

## FT SD E 17 Graduation Project 2026

Project period: Sep 8, 2026 to Dec 8, 2026  
Official submission deadline: Dec 10, 2026  
Mentor: Mr. Chau Magn  
Official consultations: 4 sessions

# Project Objective

Deliver a focused, working and well-tested Smart Resume Screener with clear documentation and evidence. The student must complete core functionality before optional features and maintain traceable progress through Trello, GitHub and Google Drive.

# Project Management System

* Trello — tasks, owners, deadlines, workflow and mentor review  
* GitHub — source code, commits, branches and pull requests  
* Google Drive — Proposal, designs, weekly reports, testing evidence, final report, guides, presentation and video

# Overall Timeline

## Phase 1 — Scope and Planning · Weeks 1–2

* Confirm the official project name, problem statement and target users.  
* Define the realistic MVP, optional features and Future Work.  
* Confirm Roeun Keovisal’s individual ownership and weekly workload.  
* Revise and submit the Project Proposal.  
* Create the GitHub repository and initial use cases.

Milestone 1 deadline: Sep 20, 2026

## Phase 2 — System Design and Foundation · Weeks 3–5

* Prepare system architecture, use cases, UI wireframes and ERD.  
* Lock the backend and database stack at S1: use FastAPI with PostgreSQL if a working endpoint and schema exist; otherwise use Django REST with MySQL 8\.  
* Create migrations, seed data and authentication.  
* Complete one working vertical slice from UI to API to database.  
* Confirm that the project runs from a clean clone in a second clean environment.

Milestone 2 deadline: Oct 9, 2026

## Phase 3 — Core Development · Weeks 6–9

* Implement recruiter authentication, job-posting CRUD and structured job requirements.  
* Implement resume upload with a five-file limit, processing states and clear failure handling.  
* Implement PDF and DOCX parsing for contact details, skills, education and years of experience; detect and reject scanned PDFs.  
* Implement explainable hybrid matching, stored scoring runs and a ranking dashboard with matched and missing skills.  
* Build the fixed labelled dataset and evaluation harness with random, skill-overlap and hybrid baselines, P@5, MRR and one ablation.

Milestone 3 deadline: Nov 6, 2026

## Phase 4 — Integration and Quality · Weeks 10–11

* Integrate frontend, backend and database components.  
* Test authentication, uploads, parsing, scoring, ranking metrics, validation and failure cases.  
* Resolve critical defects and remove unfinished optional features.  
* Update ERD, architecture and API documentation to match the running system.  
* Continue writing the final report and user guide.

## Phase 5 — Finalization and Submission · Weeks 12–13

* Conduct the mock defence and apply mentor feedback.  
* Freeze source code after final approved corrections.  
* Complete the project report, test report, guides, slides and five-minute demo video.  
* Verify sharing permissions, file names, repository setup and clean-clone instructions.  
* Prepare the complete final-submission package.

Mock defence readiness milestone: Nov 28, 2026  
Internal submission target: Dec 5, 2026  
Official submission deadline: Dec 10, 2026

# Mentoring Schedule

* Session 1 — Scope Lock: Sep 14, 2026 to Sep 19, 2026  
* Session 2 — Vertical Slice Review: Oct 5, 2026 to Oct 10, 2026  
* Session 3 — Feature Freeze Review: Nov 2, 2026 to Nov 7, 2026  
* Session 4 — Mock Defence: Nov 23, 2026 to Nov 28, 2026

Forty-eight hours before each consultation, the student must provide a short screen recording, current Trello status, completed evidence, blockers and questions requiring mentor decisions.

# Weekly Operating Rhythm

1. Monday — select realistic cards from Product Backlog and move them to This Week.  
2. During the week — move started work to In Progress and blocked work to Blocked.  
3. When work is ready — attach evidence and move the card to Ready for Mentor Review.  
4. Sunday before 8:00 PM — submit the Weekly Report with individual contributions and next-week plans.  
5. After feedback — correct cards in Revision Required and resubmit them for review.

# Quality Gates

* Each active card has one responsible student and a deadline.  
* Acceptance criteria and the checklist are complete.  
* Coding work includes a commit or pull-request link.  
* Documents and testing evidence are stored in Google Drive.  
* The system runs from a clean clone.  
* Core workflows include validation, error handling and testing.  
* Only mentor-approved work is moved to Completed.

# Success Criteria

* The approved MVP works end to end.  
* The database and diagrams match the implemented system.  
* Roeun Keovisal has visible and consistent contributions across the project period.  
* The repository can be installed and run using the README.  
* Required documentation and presentation materials are complete.  
* The full project package is ready before the official deadline.

