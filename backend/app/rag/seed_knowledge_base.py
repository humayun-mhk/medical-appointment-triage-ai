from pathlib import Path

from app.db.database import SessionLocal
from app.rag.document_loader import chunk_document, load_documents_from_folder, save_chunks_to_db, save_document_to_db


def run() -> None:
    root = Path(__file__).resolve().parents[2]
    folder = root / "knowledge_base"
    db = SessionLocal()
    try:
        count = 0
        for document_data in load_documents_from_folder(str(folder)):
            document = save_document_to_db(
                document_data["title"],
                document_data["category"],
                document_data["source"],
                document_data["content"],
                document_data["metadata"],
                db,
            )
            chunks = chunk_document(document.content)
            save_chunks_to_db(document.id, chunks, db)
            count += 1
        db.commit()
        print(f"Seeded {count} knowledge base documents.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
