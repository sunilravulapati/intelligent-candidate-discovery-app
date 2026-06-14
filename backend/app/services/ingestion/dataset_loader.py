import os
import json
import logging
from typing import Generator, List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatasetLoader:
    """
    Utility loader class to automatically ingest candidate profile datasets from
    JSON, JSONL, CSV, or Parquet formats. Supports streaming for large datasets.
    """
    
    @staticmethod
    def stream_jsonl(file_path: str) -> Generator[Dict[str, Any], None, None]:
        """Streams records line-by-line from a JSONL file."""
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)

    @staticmethod
    def load_json(file_path: str) -> List[Dict[str, Any]]:
        """Loads all records from a standard JSON array file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            return []

    @staticmethod
    def stream_csv(file_path: str, chunk_size: int = 1000) -> Generator[Dict[str, Any], None, None]:
        """Streams records from a CSV file in chunks using pandas."""
        try:
            import pandas as pd
        except ImportError:
            logger.error("pandas is required to load CSV files. Please install it first.")
            return

        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            # Parse any nested JSON columns if they exist
            for idx, row in chunk.iterrows():
                record = row.to_dict()
                # Attempt to parse json fields
                for col in ["skills", "career_history", "education", "redrob_signals", "profile"]:
                    if col in record and isinstance(record[col], str):
                        try:
                            record[col] = json.loads(record[col])
                        except Exception:
                            pass
                yield record

    @staticmethod
    def stream_parquet(file_path: str, chunk_size: int = 1000) -> Generator[Dict[str, Any], None, None]:
        """Streams records from a Parquet file in chunks using pandas."""
        try:
            import pandas as pd
        except ImportError:
            logger.error("pandas is required to load Parquet files.")
            return

        try:
            df = pd.read_parquet(file_path)
            for idx, row in df.iterrows():
                record = row.to_dict()
                for col in ["skills", "career_history", "education", "redrob_signals", "profile"]:
                    if col in record and isinstance(record[col], str):
                        try:
                            record[col] = json.loads(record[col])
                        except Exception:
                            pass
                yield record
        except Exception as e:
            logger.error(f"Error reading Parquet file: {e}")

    @classmethod
    def stream_dataset(cls, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """
        Dynamically detects file format and streams candidate profile dictionaries.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found at: {file_path}")
            
        ext = os.path.splitext(file_path)[1].lower()
        logger.info(f"Loading dataset file: {file_path} with extension {ext}")
        
        if ext == ".jsonl":
            yield from cls.stream_jsonl(file_path)
        elif ext == ".json":
            yield from cls.load_json(file_path)
        elif ext == ".csv":
            yield from cls.stream_csv(file_path)
        elif ext in [".parquet", ".pq"]:
            yield from cls.stream_parquet(file_path)
        else:
            raise ValueError(f"Unsupported dataset format: {ext}")

    @classmethod
    def load_dataset(cls, file_path: str, limit: int = -1) -> List[Dict[str, Any]]:
        """
        Loads all candidate records into memory. Use limit to prevent high memory usage.
        """
        records = []
        count = 0
        for record in cls.stream_dataset(file_path):
            records.append(record)
            count += 1
            if 0 < limit <= count:
                break
        return records
