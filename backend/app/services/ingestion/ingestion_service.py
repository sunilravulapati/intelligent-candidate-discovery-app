import os
import logging
from typing import Generator, List, Dict, Any, Tuple, Union
from app.core.config import settings
from app.models.domain import Candidate
from app.services.ingestion.dataset_loader import DatasetLoader
from app.services.ingestion.preprocess import preprocess_candidate
from app.services.ingestion.validators import validate_candidate_record, is_honeypot_candidate
from app.services.ingestion.anomaly_detection import detect_temporal_anomalies, detect_profile_inconsistencies

logger = logging.getLogger(__name__)

class IngestionService:
    """
    Orchestrates candidate profile ingestion, schema validation, data preprocessing,
    and honeypot anomaly detection.
    """

    def __init__(self, data_dir: str = settings.DATA_DIR, challenge_dir: str = settings.CHALLENGE_DATA_DIR):
        self.data_dir = settings.get_absolute_path(data_dir)
        self.challenge_dir = settings.get_absolute_path(challenge_dir)

    def get_candidate_files_status(self) -> dict:
        """
        Validates availability of candidate dataset files and returns status.
        """
        paths_to_check = {
            "challenge_jsonl": os.path.join(self.challenge_dir, "candidates.jsonl"),
            "challenge_sample": os.path.join(self.challenge_dir, "sample_candidates.json"),
            "local_raw_jsonl_gz": os.path.join(self.data_dir, "raw", "candidates.jsonl.gz"),
            "local_raw_jsonl": os.path.join(self.data_dir, "raw", "candidates.jsonl"),
        }

        status = {}
        for key, path in paths_to_check.items():
            exists = os.path.exists(path)
            size = os.path.getsize(path) if exists else 0
            status[key] = {
                "exists": exists,
                "path": path,
                "size_mb": round(size / (1024 * 1024), 2)
            }
        
        # Decide active source
        active_source = None
        if status["challenge_jsonl"]["exists"]:
            active_source = "challenge_jsonl"
        elif status["local_raw_jsonl"]["exists"] and status["local_raw_jsonl"]["size_mb"] > 10.0:
            active_source = "local_raw_jsonl"
        elif status["local_raw_jsonl_gz"]["exists"]:
            active_source = "local_raw_jsonl_gz"
        elif status["local_raw_jsonl"]["exists"]:
            active_source = "local_raw_jsonl"
        elif status["challenge_sample"]["exists"]:
            active_source = "challenge_sample"
            
        status["active_source"] = active_source
        return status

    def stream_candidates(self, limit: int = -1, validate: bool = True, preprocess: bool = True, exclude_honeypots: bool = False, as_dict: bool = True) -> Generator[Union[Dict[str, Any], Candidate], None, None]:
        """
        Streams candidate profiles from the active file source, validating and preprocessing them.
        
        Args:
            limit: Maximum candidates to stream. -1 means no limit.
            validate: Whether to run Pydantic schema validation.
            preprocess: Whether to run text and skill normalization.
            exclude_honeypots: Whether to filter out detected honeypots.
            as_dict: If True, yields candidate profiles as dictionary objects to match API expectations.
        """
        status = self.get_candidate_files_status()
        source = status.get("active_source")
        
        if not source:
            logger.error("No candidate dataset files found. Please place datasets in data/ or challenge folders.")
            return

        path = status[source]["path"]
        logger.info(f"Streaming candidates from source: {source} ({path})")

        count = 0
        try:
            for raw_record in DatasetLoader.stream_dataset(path):
                # 1. Validation
                if validate:
                    candidate, errors = validate_candidate_record(raw_record)
                    if errors:
                        logger.warning(f"Validation errors on record {raw_record.get('candidate_id')}: {errors}")
                        continue
                else:
                    candidate = Candidate.model_validate(raw_record)

                if not candidate:
                    continue

                # 2. Honeypot check
                if exclude_honeypots:
                    is_trap, reasons = is_honeypot_candidate(candidate)
                    if is_trap:
                        logger.info(f"Filtered out honeypot candidate {candidate.candidate_id}: {reasons}")
                        continue

                # 3. Preprocessing
                if preprocess:
                    candidate = preprocess_candidate(candidate)

                if as_dict:
                    yield candidate.model_dump()
                else:
                    yield candidate

                count += 1
                if 0 < limit <= count:
                    break
        except Exception as e:
            logger.error(f"Error streaming candidates: {e}")

    def load_all_candidates(self, limit: int = -1, validate: bool = True, preprocess: bool = True, exclude_honeypots: bool = False, as_dict: bool = True) -> List[Union[Dict[str, Any], Candidate]]:
        """
        Loads all parsed and validated candidates into a list in memory.
        """
        return list(self.stream_candidates(limit=limit, validate=validate, preprocess=preprocess, exclude_honeypots=exclude_honeypots, as_dict=as_dict))
