"""
Contextualize JSON documents before LightRAG ingestion.

Contextual Retrieval adds a "context header" to each document chunk
so that the LightRAG engine can better understand what each chunk
is about — even when the chunk alone is ambiguous.

Usage:
    python scripts/contextualize_json.py --input data/processed/book.json --output data/processed/book_ctx.json
    python scripts/contextualize_json.py --input-dir data/processed/ --output-dir data/contextualized/

How it works:
    1. Reads JSON file(s) with format: {"source": "...", "page": N, "content": "..."}
    2. Uses Gemini to generate a 1-2 sentence context summary for each document
    3. Prepends the context to the content field
    4. Saves the contextualized JSON for ingestion via ingest_json_to_lightrag.py
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


async def generate_context(content: str, source: str = "") -> str:
    """
    Use Gemini to generate a short context header for a document chunk.
    """
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)

    prompt = f"""Bạn là trợ lý AI chuyên xử lý tài liệu Y khoa. 
Hãy đọc đoạn văn bản dưới đây và viết MỘT câu ngắn gọn mô tả ngữ cảnh của đoạn văn.
Câu này sẽ được gắn vào đầu đoạn văn để giúp hệ thống AI hiểu rõ hơn nội dung.

Quy tắc:
- Viết bằng Tiếng Việt
- Chỉ 1-2 câu, tối đa 50 từ
- Bao gồm: chủ đề chính, loại tài liệu (nếu biết), đối tượng áp dụng
- KHÔNG giải thích, chỉ viết câu ngữ cảnh

Nguồn: {source}

Nội dung:
{content[:1500]}

Câu ngữ cảnh:"""

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=os.getenv("LIGHTRAG_LLM_MODEL", "gemini-2.5-flash"),
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"   ⚠️ LLM context generation failed: {e}")
        return f"Tài liệu y khoa từ nguồn: {source}"


async def contextualize_file(input_path: str, output_path: str, limit: int = None):
    """Contextualize a single JSON file."""
    print(f"\n📄 Processing: {input_path}")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"   ❌ Error reading: {e}")
        return 0

    # Handle both single object and array
    if isinstance(data, dict):
        docs = [data]
        was_single = True
    elif isinstance(data, list):
        docs = data
        was_single = False
    else:
        print(f"   ❌ Invalid JSON format")
        return 0

    total = len(docs)
    if limit:
        docs = docs[:limit]
        print(f"   Documents: {len(docs)} (limited from {total})")
    else:
        print(f"   Documents: {total}")

    contextualized = []
    for i, doc in enumerate(docs):
        content = doc.get("content", "").strip()
        source = doc.get("source", "Unknown")

        if not content:
            contextualized.append(doc)
            continue

        # Generate context header
        context_header = await generate_context(content, source)
        print(f"   [{i+1}/{len(docs)}] Context: {context_header[:80]}...")

        # Prepend context to content
        new_doc = dict(doc)
        new_doc["content"] = f"[Ngữ cảnh: {context_header}]\n\n{content}"
        new_doc["_context"] = context_header  # Save separately for reference
        contextualized.append(new_doc)

    # Save output
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    output_data = contextualized[0] if was_single else contextualized
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"   ✅ Saved {len(contextualized)} contextualized docs → {output_path}")
    return len(contextualized)


async def main():
    parser = argparse.ArgumentParser(description="Add context headers to medical JSON documents")
    parser.add_argument("--input", type=str, help="Single JSON input file")
    parser.add_argument("--output", type=str, help="Single JSON output file")
    parser.add_argument("--input-dir", type=str, help="Directory of JSON input files")
    parser.add_argument("--output-dir", type=str, default="data/contextualized",
                        help="Directory for contextualized output (default: data/contextualized)")
    parser.add_argument("--limit", type=int, help="Max documents per file (for testing)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Contextual Retrieval — Document Preprocessor")
    print("=" * 60)

    if args.input:
        # Single file mode
        output = args.output or args.input.replace(".json", "_ctx.json")
        await contextualize_file(args.input, output, limit=args.limit)
    elif args.input_dir:
        # Directory mode
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        json_files = sorted(input_dir.glob("*.json"))
        if not json_files:
            print(f"❌ No JSON files in {input_dir}")
            return

        total = 0
        for jf in json_files:
            out_path = output_dir / f"{jf.stem}_ctx.json"
            count = await contextualize_file(str(jf), str(out_path), limit=args.limit)
            total += count

        print(f"\n✅ COMPLETE: Contextualized {total} documents from {len(json_files)} files")
        print(f"   Output directory: {output_dir}")
        print(f"\n   Next step: python scripts/ingest_json_to_lightrag.py --data-dir {output_dir}")
    else:
        parser.print_help()
        print("\nExample:")
        print("  python scripts/contextualize_json.py --input data/processed/book.json")
        print("  python scripts/contextualize_json.py --input-dir data/processed/ --output-dir data/contextualized/")


if __name__ == "__main__":
    asyncio.run(main())
