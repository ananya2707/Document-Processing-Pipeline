import os
import time
import boto3
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.client import Config as BotocoreConfig
from celery import Celery
from dotenv import load_dotenv

# Import local modules
from . import models, schemas
from .database import SessionLocal, engine

# Define a max file size in bytes (e.g., 200 MB)
MAX_FILE_SIZE = 25 * 1024 * 1024

# --- Initial Setup ---
# Load environment variables from .env file
load_dotenv()

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

# --- App Configuration ---
BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'documents')

# --- Celery Configuration ---
celery_app = Celery(
    __name__,
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)
celery_app.conf.update(
    task_track_started=True,
)

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI Lifespan (for startup/shutdown events) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Initializing MinIO connection...")
    minio_client = None
    retries = 5
    delay = 2

    # Get cleaned environment variables
    endpoint = os.getenv('MINIO_ENDPOINT', 'minio').strip()
    user = os.getenv('MINIO_ROOT_USER', '').strip()
    password = os.getenv('MINIO_ROOT_PASSWORD', '').strip()
    
    # Correctly build the endpoint URL
    endpoint_url = f"http://{endpoint}:9000"
    
    print(f"Attempting to connect to MinIO at: {endpoint_url}")

    for i in range(retries):
        try:
            minio_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=user,
                aws_secret_access_key=password,
                config=BotocoreConfig(s3={'addressing_style': 'path'}, signature_version='s3v4')
            )
            
            minio_client.head_bucket(Bucket=BUCKET_NAME)
            print(f"✅ Successfully connected to MinIO. Bucket '{BUCKET_NAME}' found.")
            break
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"Bucket '{BUCKET_NAME}' not found. Creating it...")
                minio_client.create_bucket(Bucket=BUCKET_NAME)
                print(f"✅ Bucket '{BUCKET_NAME}' created. Connection successful.")
                break
            else:
                print(f"Attempt {i + 1}/{retries} failed with a ClientError: {e}. Retrying in {delay}s...")
                time.sleep(delay)
        except Exception as e:
            print(f"Attempt {i + 1}/{retries} failed to connect to MinIO: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    
    if minio_client is None:
        raise RuntimeError("Could not connect to MinIO after several retries.")

    yield # The application runs here

    print("Application shutdown.")

# --- FastAPI App Initialization ---
app = FastAPI(title="Document Upload Service", lifespan=lifespan)

# --- API Endpoints ---
@app.post("/upload/", response_model=schemas.Document)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Uploads a file, saves it to MinIO, creates a database record,
    and queues a processing task.
    """
    # === NEW: File Size Check ===
    # To get the file size, we need to read the content length from the header.
    # This is more reliable than file.size which may not be available for streams.
    content_length = request.headers.get('content-length')
    if not content_length:
        raise HTTPException(status_code=411, detail="Content-Length header required.")
    
    file_size = int(content_length)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, # 413 Payload Too Large
            detail=f"File is too large. Limit is {MAX_FILE_SIZE / 1024 / 1024} MB."
        )
    # ============================

    endpoint = os.getenv('MINIO_ENDPOINT', 'minio').strip()
    user = os.getenv('MINIO_ROOT_USER', '').strip()
    password = os.getenv('MINIO_ROOT_PASSWORD', '').strip()
    endpoint_url = f"http://{endpoint}:9000"

    minio_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=user,
        aws_secret_access_key=password,
        config=BotocoreConfig(s3={'addressing_style': 'path'}, signature_version='s3v4')
    )
    s3_key = file.filename

    try:
        minio_client.upload_fileobj(file.file, BUCKET_NAME, s3_key)
        print(f"Successfully uploaded '{file.filename}' to MinIO.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during upload: {e}")

    db_document = models.Document(filename=file.filename, s3_path=s3_key)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    process_document.delay(db_document.id)
    print(f"Queued task for '{file.filename}' in Redis.")
    return db_document

@app.get("/status/{document_id}", response_model=schemas.Document)
def get_document_status(document_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the status and details of a specific document.
    """
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@app.get("/")
def read_root():
    return {"message": "Welcome to the Document Processing API"}

# --- Celery Task ---
@celery_app.task(name="process_document")
def process_document(document_id: int):
    """
    Celery task to process a document with robust database handling.
    """
    db = SessionLocal()
    doc = None
    try:
        doc = db.query(models.Document).filter(models.Document.id == document_id).first()
        if not doc:
            print(f"Document with ID {document_id} not found.")
            return

        doc.status = models.DocumentStatus.PROCESSING
        db.commit()
        print(f"Processing document: {doc.filename} (ID: {doc.id})")

        endpoint = os.getenv('MINIO_ENDPOINT', 'minio').strip()
        user = os.getenv('MINIO_ROOT_USER', '').strip()
        password = os.getenv('MINIO_ROOT_PASSWORD', '').strip()
        endpoint_url = f"http://{endpoint}:9000"

        minio_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=user,
            aws_secret_access_key=password,
            config=BotocoreConfig(s3={'addressing_style': 'path'}, signature_version='s3v4')
        )
        
        response = minio_client.get_object(Bucket=BUCKET_NAME, Key=doc.filename)
        file_content = response['Body'].read()

        # --- YOUR ACTUAL DOCUMENT PROCESSING LOGIC WOULD GO HERE ---
        # For example, using PyMuPDF (fitz) to extract text from a PDF:
        # if doc.filename.lower().endswith('.pdf'):
        #     with fitz.open(stream=file_content, filetype="pdf") as pdf_doc:
        #         text = "".join(page.get_text() for page in pdf_doc)
        #     print(f"Extracted {len(text)} characters from PDF.")

        print(f"--- Extracted content from {doc.filename}, {len(file_content)} bytes ---")

        doc.status = models.DocumentStatus.PROCESSED
        print(f"Finished processing document: {doc.filename}")
    except Exception as e:
        print(f"Failed to process document {document_id}. Error: {e}")
        db.rollback()
        if doc:
            doc.status = models.DocumentStatus.FAILED
    finally:
        if db.is_active:
            db.commit()
        db.close()
        print(f"Database session closed for document {document_id}.")
