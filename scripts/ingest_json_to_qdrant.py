import os
import json
import uuid
import sys
from dotenv import load_dotenv

# 1. Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION (ĐÃ FIX CHO LOCAL) ---
DATA_DIR = os.path.join(root_dir, "data", "processed") 
COLLECTION_NAME = "medical_knowledge_base"

# FIX 1: Ép cứng localhost để chạy từ Terminal Windows
QDRANT_HOST = "localhost" 
QDRANT_PORT = 6333

# Model đồng bộ
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2" 

def extract_content_from_json(data, filename):
    """
    Hàm thông minh: Tự động nhận diện cấu trúc JSON (Flat hoặc Nested)
    Trả về: List các documents (mỗi doc là 1 dict chứa content, tags...)
    """
    extracted_docs = []
    
    # CASE 1: Cấu trúc lồng (Nested) - File _final.json
    if "nodes" in data and isinstance(data["nodes"], list):
        print(f"   ↳ Phát hiện cấu trúc 'nodes' trong {filename}")
        for node in data["nodes"]:
            content = node.get("content", "")
            # Lấy metadata từ node hoặc từ root
            meta = node.get("metadata", {})
            
            if content:
                extracted_docs.append({
                    "content": content,
                    "source": data.get("source_file", filename), # Lấy tên file gốc
                    "page": meta.get("node_index", 0), # Tạm dùng index làm page
                    "tags": meta.get("tags", [])
                })
    
    # CASE 2: Cấu trúc phẳng (Flat) - File _chunk.json
    elif "content" in data:
        extracted_docs.append({
            "content": data.get("content", ""),
            "source": data.get("source", filename),
            "page": data.get("page", 0),
            "tags": data.get("tags", [])
        })
    
    return extracted_docs

def load_and_process_json_files(directory):
    """Quét và xử lý file"""
    final_documents = []
    if not os.path.exists(directory):
        print(f"❌ Thư mục không tồn tại: {directory}")
        return final_documents

    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Gọi hàm trích xuất thông minh
                docs = extract_content_from_json(data, filename)
                
                if docs:
                    final_documents.extend(docs)
                else:
                    print(f"⚠️ Bỏ qua {filename}: Không tìm thấy dữ liệu hợp lệ.")
                    
            except Exception as e:
                print(f"❌ Lỗi khi đọc file {filename}: {e}")
                
    return final_documents

def main():
    print(f"🔄 Đang quét dữ liệu JSON tại: {DATA_DIR}")
    
    # 1. Đọc dữ liệu
    all_docs = load_and_process_json_files(DATA_DIR)
    
    if not all_docs:
        print("🛑 Không tìm thấy dữ liệu nào để nạp. Kiểm tra lại folder data/processed.")
        return

    print(f"✅ Tổng cộng tìm thấy {len(all_docs)} đoạn văn bản cần nạp.")

    # 2. Kết nối Qdrant
    try:
        print(f"🔌 Đang kết nối Qdrant tại {QDRANT_HOST}:{QDRANT_PORT}...")
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        client.get_collections() # Test connection
        print("   -> Kết nối thành công!")
    except Exception as e:
        print(f"❌ Lỗi kết nối Qdrant: {e}")
        print("   -> Hãy chắc chắn bạn đã chạy: docker run -d -p 6333:6333 ...")
        return

    # 3. Tải Model
    print(f"📥 Đang tải mô hình Embedding: {EMBEDDING_MODEL_NAME}...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # 4. Tạo Points
    points = []
    print("⚡ Đang tạo Vector...")
    
    for doc in all_docs:
        content = doc["content"]
        
        # Skip nếu nội dung quá ngắn hoặc rỗng
        if not content or len(content.strip()) < 10:
            continue

        text_to_embed = f"Tags: {doc['tags']}\nContent: {content}"
        vector = model.encode(text_to_embed).tolist()
        
        payload = {
            "CAUHOI": content[:500],       
            "CAUTRALOI": content,          
            "DEMUC": "NỘI KHOA", # Mặc định
            "source": doc["source"],
            "page": doc["page"]
        }
        
        points.append(models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=payload
        ))

    # 5. Upsert
    if points:
        print(f"🚀 Đang đẩy {len(points)} vectors lên Qdrant...")
        try:
            # Recreate collection để xóa dữ liệu cũ (Optional, để sạch sẽ)
            client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )
            
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print("🎉 NẠP DỮ LIỆU THÀNH CÔNG! (Đã reset và nạp mới)")
        except Exception as e:
            print(f"❌ Lỗi khi Upsert: {e}")
    else:
        print("⚠️ Không có vector nào được tạo.")

if __name__ == "__main__":
    main()