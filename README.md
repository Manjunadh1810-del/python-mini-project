# SmartRecruit AI

### Intelligent Recruitment & Candidate Matching Platform

> Status: Phases 1-16 complete (project setup through deployment prep). Full polished README with screenshots, architecture diagrams, and API docs lands in Phase 19.

See also: [`TESTING.md`](TESTING.md) for the test suite guide, [`DEPLOYMENT.md`](DEPLOYMENT.md) for deploying to Render/Railway/PythonAnywhere.

## Quick Start (Windows + Anaconda)

```bat
conda create -n smartrecruit python=3.10 -y
conda activate smartrecruit
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit http://127.0.0.1:8000/

## Tech Stack
- Backend: Django, Django REST Framework
- Frontend: Bootstrap 5, vanilla JS
- Database: SQLite (dev) / PostgreSQL (prod)
- AI/ML: TF-IDF, Cosine Similarity, rule-based skill matching (scikit-learn)
- Resume parsing: pypdf, python-docx

## Apps
accounts, candidates, recruiters, companies, jobs, applications, resumes, matching, notifications

Full README sections (features, architecture, API docs, screenshots) will be filled in during later phases per the project plan.
