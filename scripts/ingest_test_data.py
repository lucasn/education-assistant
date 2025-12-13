#!/usr/bin/env python3
"""
Script to ingest test data files into the vector database with evaluation flag.
Reads all PDF files from scripts/test_data and ingests them using FileIngestion.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

os.environ["EMBEDDING_MODEL"]="qwen3-embedding:0.6b"
os.environ["OLLAMA_BASE_URL"]="http://localhost:11434"
os.environ["VECTOR_DB_URL"]="postgresql://root:root@localhost:5433/vector_db"
os.environ["DOCUMENTS_COLLECTION_NAME"]="documents_collection"
os.environ["DOCUMENTS_VECTOR_DIMENSION"]="1024"
os.environ["TEXT_SPLITTER_CHUNK_SIZE"]="1000"
os.environ["DIFFICULTIES_VECTOR_DIMENSION"]="1024"
os.environ["DIFFICULTIES_COLLECTION_NAME"]="difficulties_collection"
os.environ["EVALUATION"]="0"  # Disable evaluation mode filtering

# Add api directory to Python path to import data_processing module
api_path = Path(__file__).parent.parent / "api"
sys.path.insert(0, str(api_path))

from data_processing import FileIngestion

def main():
    # Path to test data directory
    test_data_dir = Path(__file__).parent / "test_data"

    if not test_data_dir.exists():
        print(f"Error: Test data directory not found at {test_data_dir}")
        sys.exit(1)

    # Get all PDF files
    pdf_files = list(test_data_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {test_data_dir}")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF files to ingest")
    print("-" * 80)

    # Initialize FileIngestion
    try:
        file_ingestion = FileIngestion()
        print("FileIngestion initialized successfully")
        print("-" * 80)
    except Exception as e:
        print(f"Error initializing FileIngestion: {e}")
        sys.exit(1)

    # Ingest each PDF file
    success_count = 0
    error_count = 0

    for pdf_file in pdf_files:
        try:
            print(f"Processing: {pdf_file.name}")

            # Read file as bytes
            with open(pdf_file, 'rb') as f:
                file_bytes = f.read()

            # Ingest with evaluation=True
            file_ingestion.ingest(
                file_bytes=file_bytes,
                filename=pdf_file.name,
                evaluation=True
            )

            success_count += 1
            print(f"✓ Successfully ingested: {pdf_file.name}")
            print("-" * 80)

        except Exception as e:
            error_count += 1
            print(f"✗ Error ingesting {pdf_file.name}: {e}")
            print("-" * 80)

    # Summary
    print("\nIngestion Summary:")
    print(f"Total files: {len(pdf_files)}")
    print(f"Successfully ingested: {success_count}")
    print(f"Errors: {error_count}")


if __name__ == "__main__":
    main()
