"""
SMS eligibility logic.

Determines whether a DailyRoute can have SMS sent based on matching status, phone, etc.
"""


def is_route_sms_eligible(daily_route):
    """
    Check if a DailyRoute is eligible for SMS sending.

    A route is eligible if:
    - It is matched to a driver
    - The driver has a valid phone
    - SMS has not already been sent (status != 'sent')

    Returns a dict with:
    - eligible: bool
    - reason: str explaining why (not) eligible
    """
    # Check match status
    if daily_route.match_status != "matched":
        return {
            "eligible": False,
            "reason": f"Match status is '{daily_route.match_status}', not 'matched'",
        }

    # Check driver exists
    if not daily_route.driver:
        return {
            "eligible": False,
            "reason": "No driver linked to this route",
        }

    # Check driver has phone
    if not daily_route.driver.phone:
        return {
            "eligible": False,
            "reason": f"Driver '{daily_route.driver.name}' has no phone number",
        }

    # Check SMS hasn't already been sent
    if daily_route.sms_status in ["sent", "delivered"]:
        return {
            "eligible": False,
            "reason": "SMS has already been sent",
        }

    # All checks passed
    return {
        "eligible": True,
        "reason": "Route is eligible for SMS",
    }


def evaluate_sms_status(daily_route):
    """
    Evaluate and determine the SMS status for a DailyRoute.

    Returns one of:
    - 'pending': Not yet eligible (not matched, etc.)
    - 'ready': Eligible for sending
    - 'blocked': Permanently blocked (no phone, unmatched)
    - 'sent': Already sent
    """
    if daily_route.sms_status in ["sent", "delivered"]:
        return "sent"

    eligibility = is_route_sms_eligible(daily_route)
    if eligibility["eligible"]:
        return "ready"

    # Determine if it's temporarily pending or permanently blocked
    if daily_route.match_status == "unmatched":
        return "blocked"
    if daily_route.match_status == "ambiguous":
        return "blocked"
    if daily_route.driver and not daily_route.driver.phone:
        return "blocked"

    return "pending"
