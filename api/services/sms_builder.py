"""
SMS message builder for DailyRoute records.

Generates SMS messages for route assignments.
"""


def build_route_sms(daily_route):
    """
    Build an SMS message for a DailyRoute.

    Args:
        daily_route: DailyRoute instance

    Returns:
        A string containing the SMS message, or None if route is not eligible.
    """
    if not daily_route.driver or not daily_route.driver.phone:
        return None

    # Build message with route details
    message = f"Hello {daily_route.driver.name},\n\n"
    message += f"Route Assignment: {daily_route.route_code}\n\n"

    # DSP and Transporter info
    if daily_route.dsp:
        message += f"DSP: {daily_route.dsp}\n"
    if daily_route.transporter_id:
        message += f"Transporter ID: {daily_route.transporter_id}\n"

    # Service and route details
    if daily_route.delivery_service_type:
        message += f"Service: {daily_route.get_delivery_service_type_display()}\n"
    if daily_route.route_duration:
        message += f"Duration: {daily_route.route_duration}\n"

    # Stop information
    message += f"\nStops: {daily_route.all_stops} total\n"
    message += f"Completed: {daily_route.stops_completed}\n"
    message += f"Remaining: {daily_route.not_started_stops}\n"

    # Route status
    if daily_route.route_progress:
        message += f"\nStatus: {daily_route.get_route_progress_display()}"

    return message
