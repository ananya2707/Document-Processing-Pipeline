
DOC_PROCESSOR/
├── app/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── database.py       # Handles database connection and session management
│   ├── main.py           # Main FastAPI application, defines API endpoints
│   ├── models.py         # SQLAlchemy ORM models for database tables
│   ├── schemas.py        # Pydantic schemas for data validation and serialization
│   └── test_files/       # Directory for test documents
├── .env                  # Environment variables configuration
├── docker-compose.yml    # Docker Compose file for orchestrating services
├── Dockerfile            # Dockerfile for building the application image
├── flow.md               # Describes the application flow
├── requirements.txt      # Python dependencies
├── start-api.sh          # Script to start the FastAPI server
├── upload_many.sh        # Example script to upload multiple documents
└── wait-for-it.sh        # Script to wait for a service (e.g., DB) to be ready
