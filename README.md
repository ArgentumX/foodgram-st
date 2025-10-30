# 🍽️ Foodgram API — Django REST Framework Project

REST API for **Foodgram**, a platform where users can publish recipes, follow authors, add recipes to favorites, and generate shopping lists.

---

## 🚀 Quick Start with Docker

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ArgentumX/foodgram-st.git  
   cd foodgram-st
   ```

2. **Create the `.env` file**:
   ```bash
   cp ./backend/.env.Example.Docker ./backend/.env
   ```

3. **Start the services**:
   ```bash
   docker compose up --build -d
   ```

4. **Run migrations**:
   ```bash
   docker compose exec backend python manage.py migrate
   ```

5. **Create a superuser**:
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

6. **Load test data**:
   ```bash
   docker compose exec backend python manage.py load_test_data
   ```

---

## 🌐 Available Endpoints

- **Main site (frontend)**: [http://localhost:8000](http://localhost:8000)  
- **API Documentation (Swagger UI)**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)  
- **Django Admin**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## 💻 Local Setup Without Docker (Backend Only)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ArgentumX/foodgram-st.git  
   cd foodgram-st
   ```

2. Ensure you have Python 3.9+ and `pip` installed.

3. Create and activate a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create `.env` from the template:
   ```bash
   cp .env.Example.Local .env
   ```

6. Run migrations and load data:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py load_test_data
   ```

7. Start the development server:
   ```bash
   python manage.py runserver
   ```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.9+, Django 3.x, Django REST Framework  
- **Database**: PostgreSQL 17 (Docker setup)  
- **Containerization**: Docker, Docker Compose

---

## 👤 Contacts

Author: **Srebrodolsky D.V**  
- 🔗 [Telegram](https://t.me/tovarish_comissar) 
- 🔗 [GitHub](https://github.com/ArgentumX/)

---
