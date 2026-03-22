from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

CURRENT_FILE = Path(__file__).resolve()
REPO_ROOT = CURRENT_FILE.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastmcp import FastMCP
from pydantic import Field

from it_helpdesk_mcp.data_access import (
    create_ticket as create_ticket_record,
    diagnose_issue_logic,
    get_helpdesk_hours as load_helpdesk_hours,
    get_onboarding_checklist as load_onboarding_checklist,
    search_it_documents,
    suggest_fix_steps_logic,
)

mcp = FastMCP("it-helpdesk-mcp")


@mcp.tool(
    annotations={
        "title": "Search IT docs",
        "readOnlyHint": True,
        "openWorldHint": False,
    }
)
def search_it_docs(
    query: Annotated[
        str,
        Field(
            description="Fråga eller söksträng mot IT-dokumentationen",
            min_length=3,
        ),
    ],
    top_k: Annotated[
        int,
        Field(
            description="Antal träffar att returnera",
            ge=1,
            le=5,
        ),
    ] = 3,
) -> dict:
    """Söker relevanta textbitar i lokal IT-dokumentation."""
    matches = search_it_documents(query=query, top_k=top_k)
    return {
        "query": query,
        "match_count": len(matches),
        "matches": matches,
    }


@mcp.tool(
    annotations={
        "title": "Diagnose issue",
        "readOnlyHint": True,
        "openWorldHint": False,
    }
)
def diagnose_issue(
    device_type: Annotated[
        str,
        Field(
            description="Typ av enhet, till exempel laptop, mobil eller desktop",
            min_length=2,
        ),
    ],
    symptom: Annotated[
        str,
        Field(
            description="Beskrivning av problemet",
            min_length=3,
        ),
    ],
    severity: Annotated[
        str,
        Field(
            description="Låg, medium eller hög allvarlighetsgrad",
            pattern="^(low|medium|high)$",
        ),
    ] = "medium",
) -> dict:
    """Ger en enkel diagnos baserat på symptom."""
    return diagnose_issue_logic(
        device_type=device_type,
        symptom=symptom,
        severity=severity,
    )


@mcp.tool(
    annotations={
        "title": "Suggest fix steps",
        "readOnlyHint": True,
        "openWorldHint": False,
    }
)
def suggest_fix_steps(
    issue_type: Annotated[
        str,
        Field(
            description="Typ av problem, till exempel wifi_issue eller vpn_issue",
            min_length=3,
        ),
    ],
    os_name: Annotated[
        str,
        Field(
            description="Operativsystem, till exempel windows, macos eller linux",
            min_length=2,
        ),
    ] = "windows",
) -> dict:
    """Returnerar konkreta steg för att lösa ett problem."""
    return suggest_fix_steps_logic(issue_type=issue_type, os_name=os_name)


@mcp.tool(
    annotations={
        "title": "Get office hours",
        "readOnlyHint": True,
        "openWorldHint": False,
    }
)
def get_office_hours(
    location: Annotated[
        str | None,
        Field(
            description="Valfri plats att filtrera på, till exempel Stockholm",
        ),
    ] = None,
) -> dict:
    """Hämtar helpdeskens öppettider."""
    offices = load_helpdesk_hours(location=location)
    return {
        "location_filter": location,
        "office_count": len(offices),
        "offices": offices,
    }


@mcp.tool(
    annotations={
        "title": "Create IT ticket",
        "readOnlyHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }
)
def create_it_ticket(
    username: Annotated[
        str,
        Field(
            description="Användarnamn för personen som behöver hjälp",
            min_length=2,
        ),
    ],
    issue_type: Annotated[
        str,
        Field(
            description="Typ av problem, till exempel vpn_issue",
            min_length=3,
        ),
    ],
    description: Annotated[
        str,
        Field(
            description="Kort beskrivning av problemet",
            min_length=5,
        ),
    ],
    priority: Annotated[
        str,
        Field(
            description="Prioritet: low, medium eller high",
            pattern="^(low|medium|high)$",
        ),
    ] = "medium",
) -> dict:
    """Skapar ett simulerat IT-supportärende."""
    return create_ticket_record(
        username=username,
        issue_type=issue_type,
        description=description,
        priority=priority,
    )


@mcp.tool(
    annotations={
        "title": "Get onboarding checklist",
        "readOnlyHint": True,
        "openWorldHint": False,
    }
)
def get_onboarding_checklist(
    role: Annotated[
        str,
        Field(
            description="Roll, till exempel developer, designer eller analyst",
            min_length=2,
        ),
    ],
) -> dict:
    """Hämtar onboarding-checklista för en roll."""
    return load_onboarding_checklist(role=role)


if __name__ == "__main__":
    mcp.run(
        transport="stdio",
        show_banner=False,
        log_level="CRITICAL",
    )