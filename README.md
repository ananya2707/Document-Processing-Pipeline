# 📄 Document Processor API

A **FastAPI-based application** designed to process and store document information. The project is fully containerized with **Docker & Docker Compose**, making it easy to set up, run, and extend.

---

## 📂 Project Structure

<img width="859" height="540" alt="Screenshot 2025-09-22 034137" src="https://github.com/user-attachments/assets/f6f992bd-53f5-46cb-a666-864e6d0acedb" />


---

## ⚡ Features

- 🚀 **FastAPI** for building high-performance APIs.  
- 🗄 **PostgreSQL + SQLAlchemy** for robust data persistence.  
- 🔍 **Pydantic** schemas for strict validation & serialization.  
- 🐳 **Dockerized** for consistent environment setup.  
- 📂 API endpoints for **uploading, processing & storing documents**.  
- 🔄 Transaction-safe operations with rollback support.  

---

## 🛠 Prerequisites

- [Docker](https://docs.docker.com/get-docker/)  
- [Docker Compose](https://docs.docker.com/compose/)  

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone <your-repository-url>
cd DOC_PROCESSOR
```

2️⃣ Configure Environment Variables

Create a .env file with the following:
```env
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=doc_processor_db
DATABASE_URL=postgresql://user:password@db:5432/doc_processor_db
```
3️⃣ Build and Run with Docker Compose
```bash
docker-compose up --build -d
```
API → http://localhost:8000
Interactive docs → http://localhost:8000/docs


⚙️ How It Works (Processing Flow)

- Client Request → Send file(s) via /upload/ endpoint.

- FastAPI Endpoint (main.py) → Validates request using Pydantic schemas.

- Data Processing → Extracts metadata, reads content, applies transformations.

 - Database Interaction (database.py, models.py) → Data converted into ORM objects.

- Transaction Commit → Records saved into PostgreSQL. Rollback on failure.

- Response → Returns saved data to client with 200 OK or 201 Created.

📡 Usage
Run the API inside Docker
```bash
./start-api.sh
```
Upload a Document (via curl)
```bash
curl -X POST -F "files=@/path/to/your/file.txt" http://localhost:8000/upload
Upload Multiple Documents
```
```bash
./upload_many.sh
```

| Component      | File(s)                            | Description                     |
| -------------- | ---------------------------------- | ------------------------------- |
| **FastAPI**    | `main.py`                          | API routes & endpoints          |
| **SQLAlchemy** | `models.py`, `database.py`         | ORM models & DB session mgmt    |
| **Pydantic**   | `schemas.py`                       | Data validation & serialization |
| **Docker**     | `Dockerfile`, `docker-compose.yml` | Containerization setup          |
| **Scripts**    | `start-api.sh`, `wait-for-it.sh`   | API startup orchestration       |


🐳 Orchestration with Docker

- db service → PostgreSQL instance.

- api service → FastAPI container (depends on db).

- wait-for-it.sh → Ensures DB is ready before API starts.

- start-api.sh → Runs DB migrations (if any) & launches Uvicorn server.


📜 API Documentation

Once running, visit:

1. Swagger UI → http://localhost:8000/docs

2. ReDoc → http://localhost:8000/redoc


🤝 Contributing

1. Fork the repo

2. Create a feature branch:
```bash
git checkout -b feature-name
```
3. Commit changes:
```bash
git commit -m "Add new feature"
```
4. Push and open a Pull Request 🚀
