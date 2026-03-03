import logging
from core.pocketflow import AsyncFlow 

# Configure logging for this module with Vietnam timezone
from utils.timezone_utils import setup_vietnam_logging
from config.logging_config import logging_config
from tracing import trace_flow, TracingConfig
from ..nodes import (
    IngestQuery, 
    DecideSummarizeConversationToRetriveOrDirectlyAnswer, 
    RagAgent, 
    ComposeAnswer,
    FallbackNode,
    QueryCreatingForRetrievalAgent,
    RetrieveFromKBWithDemuc,
    TopicClassifyAgent,
)
# Import Memory nodes
from ..nodes.RetrieveFromMemory import RetrieveFromMemory
from ..nodes.MemoryManager import MemoryManager
from ..nodes.AddMemory import AddMemory
from ..nodes.UpdateMemory import UpdateMemory
from ..nodes.DeleteMemory import DeleteMemory

if logging_config.USE_VIETNAM_TIMEZONE:
    logger = setup_vietnam_logging(__name__, 
                                 level=getattr(logging, logging_config.LOG_LEVEL.upper()),
                                 format_str=logging_config.LOG_FORMAT)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, logging_config.LOG_LEVEL.upper()))
    

@trace_flow(flow_name="MedFlow")
class MedFlow(AsyncFlow):
    def __init__(self):
        # Initialize all nodes
        ingest = IngestQuery()
        retrieve_memory = RetrieveFromMemory(max_retries=3)

        topic_classify = TopicClassifyAgent(max_retries=2)

        main_decision = DecideSummarizeConversationToRetriveOrDirectlyAnswer(max_retries=3)
        fallback = FallbackNode()
        rag_agent = RagAgent(max_retries=2)
        compose_answer = ComposeAnswer()

        # Memory Architecture: Manager + Workers
        memory_manager = MemoryManager(max_retries=3)
        add_memory = AddMemory(max_retries=3)
        update_memory = UpdateMemory(max_retries=3)
        delete_memory = DeleteMemory(max_retries=3)

        better_retrieval_query = QueryCreatingForRetrievalAgent()
        retrieve_with_demuc = RetrieveFromKBWithDemuc()

        # ============= FLOW DEFINITION =============

        # Step 1: Ingest -> Memory Retrieval -> Main Decision
        ingest >> retrieve_memory >> main_decision

        # Step 2: From MainDecision
        main_decision - "retrieve_kb" >> rag_agent
        main_decision - "default" >> memory_manager  # Direct response -> manage memory

        # Path 1: Retrieval with Demuc (create_retrieval_query -> compose_answer)
        rag_agent - "create_retrieval_query" >> better_retrieval_query >> retrieve_with_demuc
        retrieve_with_demuc - "compose" >> compose_answer  # From better_query path

        # Path 2: Retrieval loop (retrieve_kb -> loop back to rag_agent with attempts counter)
        rag_agent - "retrieve_kb" >> topic_classify >> retrieve_with_demuc
        retrieve_with_demuc - "loop" >> rag_agent  # Loop back to rag_agent

        # Path 3: Direct Compose from RagAgent
        rag_agent - "compose_answer" >> compose_answer
        compose_answer >> memory_manager
        # ============= MEMORY MANAGEMENT =============
        memory_manager - "default" >> add_memory >> update_memory >> delete_memory  
        memory_manager - "skip" >> None  # No operations needed, end flow

        # Fallback paths
        main_decision - "fallback" >> fallback
        rag_agent - "fallback" >> fallback
        compose_answer - "fallback" >> fallback
        better_retrieval_query - "fallback" >> fallback

        super().__init__(start=ingest)
