# 🏠 Family Hub Planner App (Backend)

This is the backend API for the **Family Hub Planner App** — a lightweight personal and family planner that manages:
- ✅ Daily tasks
- 🍽️ Meals and nutrition tracking
- 🏋️ Workouts
- 👨‍👩‍👧‍👦 Multi-user support (family members)
- 🔐 JWT authentication (login / register)

---
Weekly Workflow Status:
[![Generate Next Week's Google Sheet](https://github.com/Stezoscu/planner_app/actions/workflows/weekly_sheet.yml/badge.svg)](https://github.com/Stezoscu/planner_app/actions/workflows/weekly_sheet.yml)


## 🚀 Quick Start

### 1. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
2. Install dependencies
bash
Copy code
pip install -r requirements.txt
3. Initialize the database
bash
Copy code
python db_init.py
This will create the instance/family_hub.db SQLite database and populate it with sample data.

4. Run the development server
bash
Copy code
python run.py
By default, the API will be available at:

cpp
Copy code
http://127.0.0.1:5000
🔑 Authentication
The app uses JWT tokens for authentication.

Register
POST /api/auth/register

Example JSON:

json
Copy code
{
  "name": "SteveO",
  "email": "steveo@example.com",
  "password": "password123" #not my real pass
}
Login
POST /api/auth/login

Example JSON:

json
Copy code
{
  "email": "steveo@example.com",
  "password": "password123"
}
Response:

json
Copy code
{
  "access_token": "<your_jwt_token>"
}
You’ll use this token in Postman or your frontend for protected routes:

makefile
Copy code
Authorization: Bearer <your_jwt_token>
📡 API Routes Overview
Area	Endpoint	Method	Auth	Description
🧍 Users	/api/users	GET	✅	List users
✅ Tasks	/api/tasks	GET/POST/PUT/DELETE	✅	Manage tasks
🍽️ Meals	/api/meals	GET/POST/PUT/DELETE	✅	Manage meals
🏋️ Workouts	/api/workouts	GET/POST/PUT/DELETE	✅	Manage workouts
❤️ Health	/api/health	GET	❌	Simple server check

🧱 Project Structure
bash
Copy code
Planner_App2/
│
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── extensions.py      # db, cors, jwt
│   ├── models/            # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── core_models.py
│   ├── routes/            # Blueprints (API endpoints)
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── tasks.py
│   │   ├── meals.py
│   │   └── workouts.py
│   └── utils/             # (Optional) helper modules
│
├── instance/
│   └── family_hub.db      # SQLite database (auto-created)
│
├── db_init.py             # Setup script
├── run.py                 # Entry point for Flask
├── requirements.txt
└── README.md