from app.services.ingestion.ingestion_service import IngestionService
from app.services.embeddings.embeddings_service import EmbeddingsService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.ranking.ranking_service import RankingService
from app.services.explainability.explainability_service import ExplainabilityService


def get_ingestion_service() -> IngestionService:
    return IngestionService()


def get_embeddings_service() -> EmbeddingsService:
    return EmbeddingsService()


_retrieval_service = None

def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service


_ranking_service = None

def get_ranking_service() -> RankingService:
    global _ranking_service
    if _ranking_service is None:
        _ranking_service = RankingService()
    return _ranking_service


_explainability_service = None

def get_explainability_service() -> ExplainabilityService:
    global _explainability_service
    if _explainability_service is None:
        _explainability_service = ExplainabilityService()
    return _explainability_service

