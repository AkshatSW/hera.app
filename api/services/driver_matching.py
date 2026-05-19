"""
Driver matching service.

Matches imported route rows to existing Driver records using intelligent heuristics.
"""
import logging
from difflib import SequenceMatcher
from api.models import Driver

logger = logging.getLogger(__name__)


def normalize_driver_name(name):
    """
    Normalize driver name for matching.

    - Strip whitespace
    - Convert to lowercase
    - Collapse multiple spaces
    """
    if not name:
        return ""
    return " ".join(name.strip().lower().split())


def similarity_ratio(a, b):
    """Calculate string similarity ratio (0.0 to 1.0)."""
    return SequenceMatcher(None, a, b).ratio()


def find_driver_matches(user, driver_name, transporter_id=None, dsp=None):
    """
    Find potential Driver matches for the given criteria.

    Returns a dict with:
    - candidates: list of (driver, match_type, confidence) tuples
    - match_type: 'exact_transporter', 'exact_dsp', 'name_only', 'fuzzy'
    - confidence: 0-1 score
    """
    candidates = []
    candidate_ids = set()  # Track IDs to avoid duplicates
    norm_name = normalize_driver_name(driver_name)

    if not norm_name:
        return {"candidates": candidates}

    # Priority 1: Match by transporter_id + driver name
    if transporter_id:
        matches = Driver.objects.filter(
            user=user,
            transporter_id=transporter_id,
            status='active',
        )
        for driver in matches:
            if driver.id in candidate_ids:
                continue
            driver_norm_name = normalize_driver_name(driver.name)
            if driver_norm_name == norm_name:
                candidates.append({
                    "driver": driver,
                    "match_type": "exact_transporter",
                    "confidence": 1.0,
                })
                candidate_ids.add(driver.id)
            else:
                ratio = similarity_ratio(norm_name, driver_norm_name)
                if ratio > 0.8:
                    candidates.append({
                        "driver": driver,
                        "match_type": "transporter_fuzzy",
                        "confidence": ratio,
                    })
                    candidate_ids.add(driver.id)

    # Priority 2: Match by DSP + driver name (only if no exact transporter match found)
    if dsp and not any(c["confidence"] == 1.0 for c in candidates):
        matches = Driver.objects.filter(
            user=user,
            dsp=dsp,
            status='active',
        )
        for driver in matches:
            if driver.id in candidate_ids:
                continue
            driver_norm_name = normalize_driver_name(driver.name)
            if driver_norm_name == norm_name:
                candidates.append({
                    "driver": driver,
                    "match_type": "exact_dsp",
                    "confidence": 1.0,
                })
                candidate_ids.add(driver.id)
            else:
                ratio = similarity_ratio(norm_name, driver_norm_name)
                if ratio > 0.8:
                    candidates.append({
                        "driver": driver,
                        "match_type": "dsp_fuzzy",
                        "confidence": ratio,
                    })
                    candidate_ids.add(driver.id)

    # Priority 3: Exact name match (any driver) (only if no exact matches yet)
    if not any(c["confidence"] == 1.0 for c in candidates):
        matches = Driver.objects.filter(user=user, status='active')
        for driver in matches:
            if driver.id in candidate_ids:
                continue
            driver_norm_name = normalize_driver_name(driver.name)
            if driver_norm_name == norm_name:
                candidates.append({
                    "driver": driver,
                    "match_type": "exact_name",
                    "confidence": 1.0,
                })
                candidate_ids.add(driver.id)

    # Priority 4: Fuzzy name match (any driver) - only if no exact matches yet
    if not any(c["confidence"] == 1.0 for c in candidates):
        matches = Driver.objects.filter(user=user, status='active')
        for driver in matches:
            if driver.id in candidate_ids:
                continue
            driver_norm_name = normalize_driver_name(driver.name)
            ratio = similarity_ratio(norm_name, driver_norm_name)
            if ratio > 0.75:
                candidates.append({
                    "driver": driver,
                    "match_type": "fuzzy_name",
                    "confidence": ratio,
                })
                candidate_ids.add(driver.id)

    # Return candidates sorted by confidence (highest first)
    candidates.sort(key=lambda x: x["confidence"], reverse=True)

    return {"candidates": candidates}


def match_driver(user, driver_name, transporter_id=None, dsp=None):
    """
    Attempt to match a driver to an imported row.

    Returns a dict with:
    - driver: Driver object or None
    - match_status: 'matched', 'unmatched', or 'ambiguous'
    - match_notes: String explaining the match result
    """
    results = find_driver_matches(user, driver_name, transporter_id, dsp)
    candidates = results["candidates"]

    if not candidates:
        return {
            "driver": None,
            "match_status": "unmatched",
            "match_notes": f"No driver found matching '{driver_name}'",
        }

    # If we have high-confidence exact matches, use the first one
    exact_matches = [c for c in candidates if c["confidence"] == 1.0]
    if exact_matches:
        driver = exact_matches[0]["driver"]
        match_type = exact_matches[0]["match_type"]
        if len(exact_matches) > 1:
            # Multiple exact matches - ambiguous
            names = ", ".join([c["driver"].name for c in exact_matches])
            return {
                "driver": None,
                "match_status": "ambiguous",
                "match_notes": f"Multiple exact matches found: {names}",
            }
        return {
            "driver": driver,
            "match_status": "matched",
            "match_notes": f"Matched by {match_type} (confidence: 1.0)",
        }

    # If we have fuzzy matches, check confidence
    top_match = candidates[0]
    if top_match["confidence"] > 0.85:
        return {
            "driver": top_match["driver"],
            "match_status": "matched",
            "match_notes": f"Fuzzy matched by {top_match['match_type']} (confidence: {top_match['confidence']:.2f})",
        }
    elif top_match["confidence"] > 0.75:
        # Multiple reasonable candidates - ambiguous
        if len([c for c in candidates if c["confidence"] > 0.75]) > 1:
            return {
                "driver": None,
                "match_status": "ambiguous",
                "match_notes": f"Multiple possible matches with similar confidence",
            }
        return {
            "driver": top_match["driver"],
            "match_status": "matched",
            "match_notes": f"Weak fuzzy match by {top_match['match_type']} (confidence: {top_match['confidence']:.2f})",
        }

    return {
        "driver": None,
        "match_status": "unmatched",
        "match_notes": f"Best match has low confidence: {top_match['confidence']:.2f}",
    }
