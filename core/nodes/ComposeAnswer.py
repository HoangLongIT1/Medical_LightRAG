# Core framework import
from pocketflow import Node

# Standard library imports
import logging
import re

# Third-party imports
from utils.role_enum import RoleEnum, PERSONA_BY_ROLE
from utils.llm import call_llm
from utils.parsing import parse_yaml_with_schema
from utils.llm.call_llm import APIOverloadException
from config.timeout_config import timeout_config
from config.chat_config import chat_config

# Configure logging for this module with Vietnam timezone
from utils.timezone_utils import setup_vietnam_logging
from config.logging_config import logging_config
from typing import List
if logging_config.USE_VIETNAM_TIMEZONE:
    logger = setup_vietnam_logging(__name__, 
                                 level=getattr(logging, logging_config.LOG_LEVEL.upper()),
                                 format_str=logging_config.LOG_FORMAT)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, logging_config.LOG_LEVEL.upper()))


class ComposeAnswer(Node):
    def prep(self, shared):
        context_summary = shared.get("context_summary", "")
        role = shared.get("role", "")
        
        # Prioritize retrieval_query over query for KB retrieval
        query = shared.get("retrieval_query") or shared.get("query")
        
        # Get LightRAG retrieved context (set by RetrieveFromKBWithDemuc)
        retrieved_context = shared.get("retrieved_context", "")
        
        # Get relevant memories
        relevant_memories = shared.get("relevant_memories", [])

        logger.info(f"✍️ [ComposeAnswer] PREP - Role: '{role}', Query: '{query[:50] if query else 'None'}...'")
        logger.info(f"✍️ [ComposeAnswer] PREP - LightRAG context length: {len(retrieved_context)} chars")

        return {
            "role": role,
            "query": query,
            "retrieved_context": retrieved_context,
            "context_summary": context_summary,
            "relevant_memories": relevant_memories
        }

    def exec(self, inputs):
        role = inputs["role"]
        query = inputs["query"]
        retrieved_context = inputs["retrieved_context"]
        context_summary = inputs["context_summary"]
        relevant_memories = inputs.get("relevant_memories", [])

        # Handle missing or invalid role with fallback
        if role not in PERSONA_BY_ROLE:
            logger.warning(f"✍️ [ComposeAnswer] EXEC - Invalid role '{role}', using default patient_diabetes role")
            role = "patient_diabetes"  # Default fallback role

        persona = PERSONA_BY_ROLE[role]

        # Build memory context
        memory_context = ""
        if relevant_memories:
            memory_list = "\n".join([f"- {m.get('query', '')}" for m in relevant_memories[:3]])
            memory_context = f"\nThông tin từ các câu hỏi trước đây của người dùng (tham khảo thêm):\n{memory_list}\n"

        # Use LightRAG context directly (includes entities, relationships, and text chunks)
        kb_context = retrieved_context if retrieved_context else "Không có thông tin từ cơ sở tri thức."

        prompt = f"""
Hay cung cấp tri thức y khoa dựa trên cơ sở tri thức do bác sĩ biên soạn.
User là :{ persona["audience"] }
Câu hỏi cần trả lời: {query}

Thông tin truy xuất từ Knowledge Graph (LightRAG):
{kb_context}

{memory_context}

Lưu ý quan trọng:
1) Phong cách: { persona["tone"]}.
2) Kết thúc bằng một dòng tóm lược bắt đầu bằng "👉 Tóm lại,".

```yaml
explanation: |
  <viết câu trả lời trực tiếp vào vấn đề dựa vào thông tin từ Knowledge Graph; KHÔNG bắt đầu bằng Chào bạn; dùng **nhấn mạnh** cho các từ khoá quan trọng>
  👉 Tóm lại, <tóm lược ngắn gọn>
suggestion_questions:
  - "Câu hỏi gợi ý 1"
  - "Câu hỏi gợi ý 2"
  - "Câu hỏi gợi ý 3"
```

Trả về chính xác cấu trúc yaml như ở trên (chú ý suggestion_questions là list, KHÔNG có dấu |):
"""
        # Log prompt with truncation to avoid flooding logs
        logger.info(f"✍️ [ComposeAnswer] EXEC - Full prompt: {prompt}")

        # Use proper timeout from config instead of hardcoded 1 second
        result = call_llm(prompt, max_retry_time=timeout_config.LLM_RETRY_TIMEOUT)
        logger.info(f"✍️ [ComposeAnswer] EXEC - LLM response received: {result}")
        # Parse and validate response structure
        parsed_result = parse_yaml_with_schema(
            result, 
            required_fields=["explanation", "suggestion_questions"], 
            field_types={"explanation": str, "suggestion_questions": list}
        )
        return parsed_result
        

    def post(self, shared, prep_res, exec_res):
        # Handle None exec_res (unhandled exceptions)
        if exec_res is None:
            shared["answer_obj"] = {
                "explanation": "Xin lỗi, đã có lỗi xảy ra khi xử lý câu trả lời.",
                "suggestion_questions": []
            }
            shared["explain"] = "Xin lỗi, đã có lỗi xảy ra khi xử lý câu trả lời."
            shared["suggestion_questions"] = []
            return "fallback"

        logger.info("✍️ [ComposeAnswer] POST - Lưu answer object")
        shared["answer_obj"] = exec_res
        explanation = exec_res.get("explanation", "")

        # ============= SAFETY DISCLAIMER LAYER =============
        # Append disclaimer when response involves medication, dosage,
        # or sensitive specialist advice
        specialist_ctx = shared.get("specialist_context", {})
        specialist_name = specialist_ctx.get("specialist", "")
        routing_decision = shared.get("routing_decision", "")

        # Detect medication/dosage keywords in the answer
        med_keywords = [
            r"\bmg\b", r"\bliều\b", r"\bthuốc\b", r"\bviên\b", r"\buống\b",
            r"\btiêm\b", r"\btruyền\b", r"\bkháng sinh\b", r"\bparacetamol\b",
            r"\bibuprofen\b", r"\bamoxicillin\b", r"\bđơn thuốc\b", r"\bchỉ định\b",
            r"\bchống chỉ định\b", r"\btác dụng phụ\b", r"\btương tác\b",
        ]
        has_med_content = any(re.search(kw, explanation, re.IGNORECASE) for kw in med_keywords)

        # Specialists that always need disclaimer
        sensitive_specialists = {"Dược Lý", "Tâm Thần", "Sản Khoa"}
        is_sensitive = specialist_name in sensitive_specialists

        if has_med_content or is_sensitive:
            disclaimer = (
                "\n\n⚠️ **Lưu ý:** Thông tin do AI cung cấp có thể chưa hoàn toàn chính xác. "
                "Vui lòng tham khảo thêm ý kiến của chuyên gia trong lĩnh vực liên quan "
                "trước khi áp dụng bất kỳ phương pháp điều trị nào."
            )
            explanation += disclaimer
            logger.info(f"✍️ [ComposeAnswer] POST - Safety disclaimer appended (specialist={specialist_name}, med_content={has_med_content})")

        shared["explain"] = explanation
        shared["suggestion_questions"] = exec_res.get("suggestion_questions", [])
        logger.info(f"✍️ [ComposeAnswer] POST - Answer keys: {list(exec_res.keys())}")

        # Log answer preview with safe truncation
        answer_preview = exec_res.get('explain', '')
        preview_text = answer_preview[:100] if answer_preview else 'None'
        logger.info(f"✍️ [ComposeAnswer] POST - Answer preview: {preview_text}...")

        # Check if API overload occurred and route to fallback
        if exec_res.get("api_overload", False):
            logger.info("✍️ [ComposeAnswer] POST - API overloaded, routing to fallback")
            return "fallback"

        return "default"

