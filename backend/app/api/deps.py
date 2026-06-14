from app.core.database import get_db
from app.services.ingestion.ingestion_service import IngestionService
from app.services.embeddings.embeddings_service import EmbeddingsService
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.ranking.ranking_service import RankingService
from app.services.explainability.explainability_service import ExplainabilityService


def get_ingestion_service() -> IngestionService:
    return IngestionService()


def get_embeddings_service() -> EmbeddingsService:
    return EmbeddingsService()


def get_retrieval_service() -> RetrievalService:
    return RetrievalService()


def get_ranking_service() -> RankingService:
    return RankingService()


def get_explainability_service() -> ExplainabilityService:
    return ExplainabilityService()
