# Big Data Hackathon Competition

Welcome to the **SMARTSAVE** project repository for the Big Data Hackathon Competition.

SMARTSAVE is a youth-led circular food ecosystem platform for Rwanda — connecting farmers, buyers, food-recovery partners, and youth innovators into a single digital marketplace so that every harvest creates value instead of loss.

> **From Harvest to Hope 🌱**

## Repository structure

This is a monorepo holding the full project. Each subfolder is a complete, independently versioned project with its own full git history.

| Folder | Project | What it is |
|---|---|---|
| [`SmartSave-frontend/`](./SmartSave-frontend) | Frontend | Static HTML/CSS/JS website (marketplace, farmers portal, food recovery, innovation hub, blog, auth pages) + JS API client |
| [`SmartSave-backend/`](./SmartSave-backend) | Backend | Django REST API (accounts/auth, marketplace, recovery, orders, messaging, notifications, innovation, blog) deployed with Gunicorn |

## Quick start

### Frontend
```bash
cd SmartSave-frontend
# Open index.html in a browser (or serve the folder statically)
# API URL is configured in js/config.js
```

### Backend
```bash
cd SmartSave-backend
python -m venv venv
# Windows: venv\Scripts\activate    |    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# API available at http://localhost:8000/api/
```

See each subfolder's own `README.md` for full setup and deployment instructions.

## Original repositories
- Frontend: https://github.com/Abelkwi/SmartSave-frontend
- Backend: https://github.com/Abelkwi/SmartSave-backend