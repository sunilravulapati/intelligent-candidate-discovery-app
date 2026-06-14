import logging
from typing import Dict, Any, Tuple, List, Optional
from pydantic import ValidationError
from app.models.domain import Candidate
from app.services.ingestion.anomaly_detection import detect_temporal_anomalies, detect_profile_inconsistencies

logger = logging.getLogger(__name__)

def validate_candidate_record(raw_record: Dict[str, Any]) -> Tuple[Optional[Candidate], List[str]]:
    """
    Validates a raw candidate profile record against the Pydantic schema.
    
    Returns:
        A tuple of (validated_candidate, list_of_errors). If valid, validated_candidate is returned, 
        else None. Errors list details schema parse failures.
    """
    errors = []
    candidate = None
    try:
        candidate = Candidate.model_validate(raw_record)
    except ValidationError as ve:
        for error in ve.errors():
            loc = " -> ".join(str(l) for l in error["loc"])
            errors.append(f"Schema Error [{loc}]: {error['msg']}")
    except Exception as e:
        errors.append(f"Unexpected Validation Error: {str(e)}")
        
    return candidate, errors

def is_honeypot_candidate(candidate: Candidate, founding_dates: Optional[Dict[str, int]] = None) -> Tuple[bool, List[str]]:
    """
    Evaluates whether a candidate is a honeypot trap based on temporal anomalies or profile inconsistencies.
    If a startup founding year is violated, it is classified as a honeypot.
    
    Returns:
        A tuple of (is_honeypot, reasons_list).
    """
    reasons = []
    
    # 1. Run temporal anomalies checks
    temp_anomalies = detect_temporal_anomalies(candidate, founding_dates)
    for anom in temp_anomalies:
        # Startup founding year violations are strong indicators of honeypots
        if "founded" in anom:
            reasons.append(anom)
            
    # 2. Run other critical logical checks
    # (Optional: check if expert skills zero duration can flag honeypots)
    inconsistencies = detect_profile_inconsistencies(candidate)
    for incons in inconsistencies:
        if "expert/advanced proficiency but 0 duration" in incons:
            reasons.append(incons)
            
    # If any founding year violations or severe zero-duration skills inconsistencies are found
    is_trap = len(reasons) > 0
    return is_trap, reasons
