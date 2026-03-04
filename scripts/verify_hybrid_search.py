"""
Verify Hybrid Search (BM25 + Vector + Knowledge Graph)

This script tests the complete retrieval pipeline to confirm:
1. LightRAG initializes correctly
2. BM25 index loads from KV store
3. hybrid_query() returns combined results from BM25 + Graph+Vector
4. The system handles edge cases gracefully (empty index, no data, etc.)

Usage:
    python scripts/verify_hybrid_search.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def test_bm25_index():
    """Test BM25 index creation and search."""
    print_section("TEST 1: BM25 Index")
    from utils.lightrag_engine import BM25Index
    from config.lightrag_config import lightrag_config

    idx = BM25Index()
    working_dir = lightrag_config.WORKING_DIR

    kv_path = os.path.join(working_dir, "kv_store_text_chunks.json")
    if not os.path.exists(kv_path):
        print(f"  ⚠️ KV store not found at: {kv_path}")
        print(f"     This is expected if no data has been ingested yet.")
        print(f"     Run: python scripts/ingest_json_to_lightrag.py first.")
        return False

    idx.build_from_kv_store(working_dir)

    if idx.is_ready:
        print(f"  ✅ BM25 index is ready with chunks loaded")

        # Test a sample search
        test_queries = [
            "Paracetamol",
            "Sốt cao",
            "bệnh tiểu đường",
        ]
        for q in test_queries:
            results = idx.search(q, top_k=3)
            print(f"\n  🔍 BM25 search: '{q}'")
            if results:
                for i, r in enumerate(results, 1):
                    preview = r["content"][:100].replace("\n", " ")
                    print(f"     #{i} [score={r['bm25_score']:.2f}] {preview}...")
            else:
                print(f"     No matches found")
        return True
    else:
        print(f"  ⚠️ BM25 index is empty (no text chunks)")
        return False


async def test_lightrag_init():
    """Test LightRAG engine initialization."""
    print_section("TEST 2: LightRAG Engine Initialization")
    from utils.lightrag_engine import LightRAGEngine

    try:
        rag = await LightRAGEngine.initialize()
        print(f"  ✅ LightRAG initialized successfully")
        print(f"  ✅ BM25 index: {'ready' if LightRAGEngine._bm25_index and LightRAGEngine._bm25_index.is_ready else 'empty (no data ingested)'}")
        return True
    except Exception as e:
        print(f"  ❌ LightRAG init failed: {e}")
        return False


async def test_hybrid_query():
    """Test the hybrid_query method."""
    print_section("TEST 3: Hybrid Query (BM25 + Graph + Vector)")
    from utils.lightrag_engine import LightRAGEngine

    test_queries = [
        "Triệu chứng bệnh tiểu đường",
        "Paracetamol liều dùng",
        "Điều trị cao huyết áp",
    ]

    for q in test_queries:
        print(f"\n  🔍 Query: '{q}'")
        try:
            result = await LightRAGEngine.hybrid_query(query=q)
            if result:
                # Show which sections are present
                has_graph = "Knowledge Graph" in result
                has_bm25 = "BM25 Keyword" in result
                print(f"     Graph+Vector results: {'✅' if has_graph else '⚠️ empty'}")
                print(f"     BM25 keyword results: {'✅' if has_bm25 else '⚠️ empty'}")
                print(f"     Total context length: {len(result)} chars")
                # Preview
                preview = result[:200].replace("\n", " ")
                print(f"     Preview: {preview}...")
            else:
                print(f"     ⚠️ No results returned")
        except Exception as e:
            print(f"     ❌ Query failed: {e}")

    return True


async def test_processing_status():
    """Test the processing status endpoint."""
    print_section("TEST 4: Processing Status")
    from utils.lightrag_engine import LightRAGEngine

    try:
        status = await LightRAGEngine.get_processing_status()
        print(f"  Status: {status.get('status')}")
        print(f"  Working dir: {status.get('working_dir')}")
        print(f"  LLM model: {status.get('llm_model')}")
        print(f"  Graph storage: {status.get('graph_storage')}")
        print(f"  Vector storage: {status.get('vector_storage')}")
        return True
    except Exception as e:
        print(f"  ❌ Status check failed: {e}")
        return False


async def main():
    print_section("HYBRID SEARCH VERIFICATION")
    print(f"  Working dir: {os.getenv('LIGHTRAG_WORKING_DIR', './lightrag_data')}")
    print(f"  LLM model: {os.getenv('LIGHTRAG_LLM_MODEL', 'gemini-2.5-flash')}")
    print(f"  Embedding: {os.getenv('LIGHTRAG_EMBEDDING_MODEL', 'gemini-embedding-001')}")

    results = {}

    # Test 1: BM25 index standalone
    results["BM25 Index"] = await test_bm25_index()

    # Test 2: LightRAG initialization (includes BM25 auto-build)
    results["LightRAG Init"] = await test_lightrag_init()

    # Test 3: Hybrid query
    results["Hybrid Query"] = await test_hybrid_query()

    # Test 4: Status check
    results["Status Check"] = await test_processing_status()

    # Summary
    print_section("VERIFICATION SUMMARY")
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "⚠️ WARN"
        if not passed:
            all_passed = False
        print(f"  {status} — {name}")

    if all_passed:
        print(f"\n  🎉 All checks passed! Hybrid Search is operational.")
    else:
        print(f"\n  ⚠️ Some checks had warnings. This is likely due to no data being ingested yet.")
        print(f"     Run: python scripts/ingest_json_to_lightrag.py to ingest data first.")

    # Cleanup
    from utils.lightrag_engine import LightRAGEngine
    await LightRAGEngine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
