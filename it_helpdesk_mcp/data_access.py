from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
IT_DOCS_DIR = DATA_DIR / "it_docs"
HELPDESK_HOURS_FILE = DATA_DIR / "helpdesk_hours.json"
ONBOARDING_FILE = DATA_DIR / "onboarding_checklists.json"
TICKETS_FILE = DATA_DIR / "tickets.json"

STOPWORDS = {
    "och",
    "att",
    "det",
    "som",
    "för",
    "med",
    "den",
    "detta",
    "eller",
    "till",
    "på",
    "i",
    "en",
    "ett",
    "av",
    "är",
    "om",
    "hur",
    "vad",
    "var",
    "kan",
    "ska",
    "du",
    "de",
    "vi",
    "ni",
    "the",
    "a",
    "an",
    "of",
    "to",
    "and",
    "is",
    "in",
    "for",
    "with",
}


def ensure_data_dirs() -> None:
    IT_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    if not HELPDESK_HOURS_FILE.exists():
        HELPDESK_HOURS_FILE.write_text("[]", encoding="utf-8")

    if not ONBOARDING_FILE.exists():
        ONBOARDING_FILE.write_text("{}", encoding="utf-8")

    if not TICKETS_FILE.exists():
        TICKETS_FILE.write_text("[]", encoding="utf-8")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return default

    return json.loads(raw)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-ZåäöÅÄÖ0-9_-]+", text.lower())
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]


def _chunk_text(text: str, chunk_size: int = 700) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= chunk_size:
            current = f"{current}\n\n{paragraph}".strip()
            continue

        if current:
            chunks.append(current)

        if len(paragraph) <= chunk_size:
            current = paragraph
        else:
            step = max(200, chunk_size - 120)
            for i in range(0, len(paragraph), step):
                part = paragraph[i : i + chunk_size].strip()
                if part:
                    chunks.append(part)
            current = ""

    if current:
        chunks.append(current)

    return chunks


def _read_it_documents() -> list[dict[str, str]]:
    ensure_data_dirs()
    documents: list[dict[str, str]] = []

    for path in sorted(IT_DOCS_DIR.rglob("*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue

        documents.append(
            {
                "source": path.name,
                "text": path.read_text(encoding="utf-8"),
            }
        )

    return documents


def search_it_documents(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    docs = _read_it_documents()
    query_tokens = set(_tokenize(query))
    query_lower = query.lower().strip()

    scored_chunks: list[dict[str, Any]] = []

    for doc in docs:
        chunks = _chunk_text(doc["text"])
        for idx, chunk in enumerate(chunks, start=1):
            chunk_lower = chunk.lower()
            chunk_tokens = set(_tokenize(chunk))

            overlap = query_tokens.intersection(chunk_tokens)
            score = float(len(overlap))

            if query_lower and query_lower in chunk_lower:
                score += 3.0

            for token in query_tokens:
                if token in chunk_lower:
                    score += 0.15

            if score <= 0:
                continue

            snippet = re.sub(r"\s+", " ", chunk).strip()
            if len(snippet) > 280:
                snippet = snippet[:277] + "..."

            scored_chunks.append(
                {
                    "source": doc["source"],
                    "chunk_id": idx,
                    "score": round(score, 2),
                    "snippet": snippet,
                }
            )

    scored_chunks.sort(
        key=lambda item: (item["score"], len(item["snippet"])),
        reverse=True,
    )

    if scored_chunks:
        return scored_chunks[:top_k]

    fallback: list[dict[str, Any]] = []
    for doc in docs[:top_k]:
        chunks = _chunk_text(doc["text"])
        if not chunks:
            continue

        snippet = re.sub(r"\s+", " ", chunks[0]).strip()
        if len(snippet) > 280:
            snippet = snippet[:277] + "..."

        fallback.append(
            {
                "source": doc["source"],
                "chunk_id": 1,
                "score": 0.0,
                "snippet": snippet,
            }
        )

    return fallback


def diagnose_issue_logic(device_type: str, symptom: str, severity: str) -> dict[str, Any]:
    symptom_lower = symptom.lower()
    device_type_lower = device_type.lower()

    likely_causes: list[str] = []
    suggested_issue_type = "general_support"

    if "wifi" in symptom_lower or "trådlös" in symptom_lower or "internet" in symptom_lower:
        likely_causes = [
            "Wi-Fi är avstängt på enheten",
            "Fel nätverk eller svag signal",
            "Drivrutin eller nätverksadapter behöver startas om",
        ]
        suggested_issue_type = "wifi_issue"

    elif "vpn" in symptom_lower:
        likely_causes = [
            "VPN-klienten är inte korrekt installerad",
            "Tvåfaktorsautentisering är inte genomförd",
            "Fel serveradress eller utgången inloggning",
        ]
        suggested_issue_type = "vpn_issue"

    elif "lösenord" in symptom_lower or "password" in symptom_lower or "inlogg" in symptom_lower:
        likely_causes = [
            "Felaktigt lösenord",
            "Kontot är låst efter för många försök",
            "Tvåfaktor krävs men har inte aktiverats",
        ]
        suggested_issue_type = "password_issue"

    elif "2fa" in symptom_lower or "tvåfaktor" in symptom_lower:
        likely_causes = [
            "Authenticator-app är inte korrekt kopplad",
            "Fel tidssynk på mobilen",
            "Backup-koder saknas eller är gamla",
        ]
        suggested_issue_type = "two_factor_issue"

    else:
        likely_causes = [
            "Tillfälligt systemfel",
            "Lokal konfigurationsmiss på enheten",
            "Behov av manuell felsökning av helpdesk",
        ]

    return {
        "device_type": device_type,
        "symptom": symptom,
        "severity": severity,
        "suggested_issue_type": suggested_issue_type,
        "likely_causes": likely_causes,
        "next_step": "Använd suggest_fix_steps med suggested_issue_type för konkreta steg.",
        "internal_note": f"Auto-diagnos skapad för {device_type_lower}.",
    }


def suggest_fix_steps_logic(issue_type: str, os_name: str) -> dict[str, Any]:
    issue_type_lower = issue_type.lower()
    os_name_lower = os_name.lower()

    steps_map = {
        "wifi_issue": [
            "Kontrollera att Wi-Fi är aktiverat på enheten.",
            "Starta om datorn och försök ansluta igen.",
            "Glöm nätverket och anslut på nytt.",
            "Testa att ansluta till ett annat nätverk för att isolera felet.",
        ],
        "vpn_issue": [
            "Kontrollera att VPN-klienten är installerad enligt guiden.",
            "Logga ut och in igen i VPN-klienten.",
            "Verifiera att tvåfaktor fungerar.",
            "Kontrollera att rätt serveradress används.",
        ],
        "password_issue": [
            "Kontrollera att rätt användarnamn används.",
            "Återställ lösenordet via lösenordsportalen.",
            "Vänta några minuter om kontot är tillfälligt låst.",
            "Försök igen i ett privat webbfönster.",
        ],
        "two_factor_issue": [
            "Kontrollera att authenticator-appen är korrekt kopplad.",
            "Synkronisera tid på mobilen.",
            "Prova en backup-kod om sådan finns.",
            "Kontakta helpdesk om du inte kommer åt koderna.",
        ],
        "general_support": [
            "Starta om enheten.",
            "Kontrollera nätverksanslutning och inloggning.",
            "Testa i annan webbläsare eller på annan enhet.",
            "Kontakta helpdesk om problemet kvarstår.",
        ],
    }

    steps = steps_map.get(issue_type_lower, steps_map["general_support"])

    os_note = {
        "windows": "På Windows kan du även kontrollera Enhetshanteraren för nätverkskort.",
        "macos": "På macOS kan du även kontrollera Systeminställningar > Nätverk.",
        "linux": "På Linux kan du även kontrollera NetworkManager och relevanta loggar.",
    }.get(os_name_lower, "Följ även lokala instruktioner för ditt operativsystem.")

    return {
        "issue_type": issue_type,
        "os_name": os_name,
        "steps": steps,
        "os_specific_note": os_note,
        "internal_note": f"Visade standardsteg för {issue_type_lower}.",
    }


def get_helpdesk_hours(location: str | None = None) -> list[dict[str, Any]]:
    ensure_data_dirs()
    hours = _read_json(HELPDESK_HOURS_FILE, default=[])

    if location:
        needle = location.strip().lower()
        hours = [item for item in hours if needle in item.get("location", "").lower()]

    return hours


def create_ticket(username: str, issue_type: str, description: str, priority: str) -> dict[str, Any]:
    ensure_data_dirs()
    tickets = _read_json(TICKETS_FILE, default=[])

    ticket_id = f"IT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    ticket = {
        "ticket_id": ticket_id,
        "username": username,
        "issue_type": issue_type,
        "description": description,
        "priority": priority,
        "status": "open",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "employee_id": "EMP-48291",
        "device_serial": "SN-938483-HELPDESK",
        "internal_note": "Endast för helpdeskpersonal.",
    }

    tickets.append(ticket)
    _write_json(TICKETS_FILE, tickets)

    return ticket


def get_onboarding_checklist(role: str) -> dict[str, Any]:
    ensure_data_dirs()
    checklists = _read_json(ONBOARDING_FILE, default={})
    role_key = role.strip().lower()

    return {
        "role": role,
        "tasks": checklists.get(role_key, []),
    }