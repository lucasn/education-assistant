"""
Script to populate the vector database with text files from the data folder.
This script processes plain text files, splits them into chunks, embeds them,
and inserts them into the PostgreSQL vector database with an "evaluation" keyword.
"""

import sys
from pathlib import Path

# Add parent directory to path to import from api folder
sys.path.append(str(Path(__file__).parent.parent))
from dotenv import load_dotenv

load_dotenv("./api/.env")
import os
os.environ["VECTOR_DB_URL"] = "postgresql://root:root@localhost:5433/vector_db"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

from api.data_processing import FileIngestion
from uuid import uuid4

from os import getenv

# Get configuration from environment
DOCUMENTS_COLLECTION_NAME = getenv("DOCUMENTS_COLLECTION_NAME")

# File paths
DATA_FOLDER = Path(__file__).parent.parent / "data"
FILES_TO_PROCESS = [
    "file1-OS.txt",
    "file2-distributed.txt",
    "file3-javascript.txt"
]


class DatabasePopulator:
    def __init__(self):
        """Initialize the database populator using FileIngestion"""
        print("Initializing Database Populator...")
        self.file_ingestion = FileIngestion()
        print("Initialization complete!\n")

    def read_text_file(self, filepath: Path) -> str:
        """Read a plain text file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def process_file(self, filepath: Path):
        """Process a single file: read, split, embed, and insert with evaluation keyword"""
        filename = filepath.name
        print(f"\n{'='*60}")
        print(f"Processing: {filename}")
        print(f"{'='*60}")

        # Generate unique file ID
        file_id = str(uuid4())

        # Read text file
        print("Reading file...")
        text = self.read_text_file(filepath)
        print(f"File size: {len(text)} characters")

        # Use FileIngestion's embed_text method to split and embed
        print("Splitting and embedding text...")
        chunks, embeddings = self.file_ingestion.embed_text(text)
        print(f"Created {len(chunks)} chunks")

        # Insert into database with "evaluation" keyword
        print(f"Inserting {len(chunks)} chunks into database...")
        with self.file_ingestion.conn.cursor() as cur:
            for chunk, embedding in zip(chunks, embeddings):
                cur.execute(
                    f"""
                    INSERT INTO {DOCUMENTS_COLLECTION_NAME}
                    (vector, text, file_id, filename, keywords)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (embedding, chunk, file_id, filename, ["evaluation"])
                )

        print(f"✓ Completed processing {filename}")
        print(f"  File ID: {file_id}")
        print(f"  Total chunks: {len(chunks)}")

    def process_all_files(self):
        """Process all specified files"""
        print("\n" + "="*60)
        print("VECTOR DATABASE POPULATION SCRIPT")
        print("="*60)
        print(f"\nFiles to process: {len(FILES_TO_PROCESS)}")
        for filename in FILES_TO_PROCESS:
            print(f"  - {filename}")
        print()

        for filename in FILES_TO_PROCESS:
            filepath = DATA_FOLDER / filename

            if not filepath.exists():
                print(f"⚠ Warning: File not found: {filepath}")
                continue

            try:
                self.process_file(filepath)
            except Exception as e:
                print(f"✗ Error processing {filename}: {e}")
                import traceback
                traceback.print_exc()

        print("\n" + "="*60)
        print("DATABASE POPULATION COMPLETE!")
        print("="*60)


def main():
    """Main entry point for the script"""
    populator = DatabasePopulator()
    populator.process_all_files()


if __name__ == "__main__":
    main()
