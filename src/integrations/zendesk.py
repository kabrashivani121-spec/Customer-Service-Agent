"""Zendesk integration stub.

Implement by calling Zendesk REST APIs to create/update tickets.
Keep this module as a boundary so you can swap vendors later.
"""
from __future__ import annotations
from typing import Optional, Dict

def create_ticket(subject: str, description: str, requester_email: str | None = None) -> Dict:
    # TODO: Add Zendesk credentials + API call
    return {"status": "not_configured", "subject": subject}
