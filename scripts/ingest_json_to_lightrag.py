"""
Ingest parsed medical JSON data into LightRAG knowledge base.

Usage:
    python scripts/ingest_json_to_lightrag.py                          # Ingest all JSONs
    python scripts/ingest_json_to_lightrag.py --file book.json         # Ingest one file
    python scripts/ingest_json_to_lightrag.py --file book.json --limit 10  # Test with 10 documents

JSON format expected:
    {
        "source": "Harrison_Internal_Medicine.pdf",
        "page": 15,
        "content": "Nội dung văn bản đã làm sạch..."
    }
    (Can be an array of objects or a single JSON object)
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()


def format_doc_as_text(doc) -> str:
    """Convert a JSON document into a rich text string for LightRAG ingestion."""
    if not isinstance(doc, dict):
        return ""
        
    source = doc.get("source", "Unknown Source")
    page = doc.get("page", "")
    content = doc.get("content", "").strip()

    if not content:
        return ""

    header = f"Source: {source}"
    if page:
        header += f" (Page {page})"

    return f"{header}\nContent:\n{content}"


async def ingest_file(filepath: str, limit: int = None, batch_size: int = 5):
    """Ingest a single JSON file into LightRAG."""
    from utils.lightrag_engine import LightRAGEngine

    print(f"\n📄 Reading: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return 0

    # Handle both single object and array of objects
    if isinstance(data, dict):
        raw_docs = [data]
    elif isinstance(data, list):
        raw_docs = data
    else:
        print(f"   ❌ Invalid JSON format in {filepath}")
        return 0

    total = len(raw_docs)

    if limit:
        raw_docs = raw_docs[:limit]
        print(f"   Documents: {len(raw_docs)} (limited from {total})")
    else:
        print(f"   Documents: {total}")

    # Convert JSON to text documents
    documents = []
    for doc in raw_docs:
        text = format_doc_as_text(doc)
        if text.strip():
            documents.append(text)

    if not documents:
        print("   ⚠️ No valid content found in file.")
        return 0

    print(f"   Valid documents to ingest: {len(documents)}")
    print(f"   Total chars: {sum(len(d) for d in documents):,}")

    # Ingest in batches
    ingested = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        for doc in batch:
            try:
                await LightRAGEngine.insert_text(doc)
                ingested += 1
            except Exception as e:
                print(f"   ❌ Error inserting doc {ingested + 1}: {e}")

        print(f"   ✅ Progress: {ingested}/{len(documents)} documents ingested")

    print(f"   🎉 Done! Ingested {ingested}/{len(documents)} documents from {Path(filepath).name}")
    return ingested


async def main():
    parser = argparse.ArgumentParser(description="Ingest medical JSON data into LightRAG")
    parser.add_argument("--file", type=str, help="Specific JSON filename (e.g., data.json)")
    parser.add_argument("--limit", type=int, help="Max documents per file (for testing)")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size (default: 5)")
    parser.add_argument("--data-dir", type=str, default="data/processed",
                        help="Directory containing JSON files")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    
    # Create directory if it doesn't exist
    if not data_dir.exists():
        print(f"⚠️ Data directory not found: {data_dir}. Creating it now...")
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"❌ Please place your .json files in {data_dir} and run this script again.")
        sys.exit(0)

    # Find JSON files
    if args.file:
        json_files = [data_dir / args.file]
        if not json_files[0].exists():
            print(f"❌ File not found: {json_files[0]}")
            sys.exit(1)
    else:
        json_files = sorted(data_dir.glob("*.json"))

    if not json_files:
        print(f"❌ No JSON files found in {data_dir}!")
        sys.exit(1)

    print("=" * 60)
    print("  LightRAG JSON Data Ingestion")
    print("=" * 60)
    print(f"  Data dir: {data_dir}")
    print(f"  Files: {len(json_files)}")
    if args.limit:
        print(f"  Limit: {args.limit} docs per file")
    print()

    # Initialize LightRAG
    print("🔄 Initializing LightRAG engine...")
    from utils.lightrag_engine import LightRAGEngine
    await LightRAGEngine.initialize()
    print("✅ LightRAG ready!\n")

    # Ingest each file
    total_ingested = 0
    for json_file in json_files:
        count = await ingest_file(str(json_file), limit=args.limit, batch_size=args.batch_size)
        total_ingested += count

    print("\n" + "=" * 60)
    print(f"  ✅ COMPLETE: Ingested {total_ingested} documents from {len(json_files)} files")
    print("=" * 60)

    # Shutdown
    await LightRAGEngine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
