#!/usr/bin/env python3
"""Verify literature authenticity, quote accuracy, and positive quality signals."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import html
import json
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


TOOL_VERSION = "1.0.0"
DEFAULT_TIMEOUT = 20
USER_AGENT = "doubao-academic-polish/1.0 (mailto:literature-verification@example.invalid)"
REVERIFY_FLAGS = {"MISSING_URL", "METADATA_ONLY", "NO_AUTHORITY_CREDENTIAL", "DOI_MISMATCH"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = normalize_space(value).casefold()
    value = re.sub(r"[\W_]+", " ", value)
    return normalize_space(value)


def normalize_doi(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.I)
    value = re.sub(r"^doi:\s*", "", value, flags=re.I)
    return value.strip().lower()


def safe_id(ref: Dict[str, Any], index: int) -> str:
    return str(ref.get("id") or ref.get("doi") or ref.get("title") or f"reference-{index + 1}")[:120]


def title_similarity(a: str, b: str) -> float:
    na, nb = normalize_text(a), normalize_text(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def family_name(name: str) -> str:
    name = normalize_space(name)
    if not name:
        return ""
    if "," in name:
        return normalize_text(name.split(",", 1)[0])
    parts = name.split()
    return normalize_text(parts[-1])


def institutional_author_name(name: str) -> str:
    normalized = normalize_text(name)
    markers = {
        "administration", "agency", "association", "bank", "center", "centers",
        "centre", "committee", "council", "department", "foundation",
        "government", "institute", "ministry", "office", "organization",
        "nations", "society", "university",
    }
    return re.sub(r"^the\s+", "", normalized) if set(normalized.split()) & markers else ""


def first_author_matches(expected: str, candidates: Iterable[str]) -> Tuple[bool, Optional[str]]:
    candidate_list = list(candidates)
    if not candidate_list:
        return False, None
    first_candidate = candidate_list[0]
    expected_institution = institutional_author_name(expected)
    candidate_institution = institutional_author_name(first_candidate)
    if expected_institution or candidate_institution:
        return (
            bool(expected_institution)
            and expected_institution == candidate_institution,
            first_candidate,
        )
    expected_norm = family_name(expected)
    if not expected_norm:
        return False, None
    candidate_norm = family_name(first_candidate)
    return candidate_norm == expected_norm, first_candidate


def clean_abstract(value: str) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"</?jats:[^>]+>", " ", value)
    value = re.sub(r"<[^>]+>", " ", value)
    return normalize_space(value)


def reconstruct_openalex_abstract(inverted: Optional[Dict[str, List[int]]]) -> str:
    if not inverted:
        return ""
    positions: Dict[int, str] = {}
    for word, indexes in inverted.items():
        for idx in indexes:
            positions[int(idx)] = word
    return normalize_space(" ".join(positions[i] for i in sorted(positions)))


@dataclass
class ApiCall:
    provider: str
    endpoint: str
    status: str
    http_status: Optional[int] = None
    error: Optional[str] = None


@dataclass
class Trace:
    run_id: str
    started_at: str
    input_sha256: str
    tool_version: str = TOOL_VERSION
    python_version: str = field(default_factory=lambda: sys.version.split()[0])
    api_calls: List[ApiCall] = field(default_factory=list)
    attempts: List[Dict[str, Any]] = field(default_factory=list)

    def add_call(self, provider: str, endpoint: str, status: str, http_status: Optional[int] = None, error: Optional[str] = None) -> None:
        self.api_calls.append(ApiCall(provider, endpoint, status, http_status, error))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": now_iso(),
            "tool_version": self.tool_version,
            "python_version": self.python_version,
            "input_sha256": self.input_sha256,
            "api_calls": [call.__dict__ for call in self.api_calls],
            "attempts": self.attempts,
        }


class HttpClient:
    def __init__(self, trace: Trace, timeout: int = DEFAULT_TIMEOUT, contact_email: str = ""):
        self.trace = trace
        self.timeout = timeout
        self.user_agent = USER_AGENT
        if contact_email:
            self.user_agent = f"doubao-academic-polish/1.0 (mailto:{contact_email})"

    def json_get(self, provider: str, url: str) -> Optional[Dict[str, Any]]:
        req = Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/json"})
        try:
            with urlopen(req, timeout=self.timeout) as response:
                payload = response.read()
                self.trace.add_call(provider, redact_url(url), "ok", getattr(response, "status", None))
                return json.loads(payload.decode("utf-8", errors="replace"))
        except HTTPError as exc:
            self.trace.add_call(provider, redact_url(url), "http_error", exc.code, str(exc))
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            self.trace.add_call(provider, redact_url(url), "error", None, str(exc))
        return None

    def text_get(self, provider: str, url: str) -> Optional[str]:
        req = Request(url, headers={"User-Agent": self.user_agent, "Accept": "text/html, text/plain;q=0.9,*/*;q=0.1"})
        try:
            with urlopen(req, timeout=self.timeout) as response:
                content_type = response.headers.get("content-type", "")
                payload = response.read(3_000_000)
                self.trace.add_call(provider, redact_url(url), "ok", getattr(response, "status", None))
                if "pdf" in content_type.lower():
                    return ""
                return payload.decode("utf-8", errors="replace")
        except HTTPError as exc:
            self.trace.add_call(provider, redact_url(url), "http_error", exc.code, str(exc))
        except (URLError, TimeoutError) as exc:
            self.trace.add_call(provider, redact_url(url), "error", None, str(exc))
        return None


def redact_url(url: str) -> str:
    parsed = urlparse(url)
    query = []
    for item in parsed.query.split("&"):
        if item.startswith("mailto="):
            query.append("mailto=REDACTED")
        elif item:
            query.append(item)
    return parsed._replace(query="&".join(query)).geturl()


def crossref_by_doi(client: HttpClient, doi: str, contact_email: str = "") -> Optional[Dict[str, Any]]:
    doi = normalize_doi(doi)
    if not doi:
        return None
    params = {"mailto": contact_email} if contact_email else {}
    url = f"https://api.crossref.org/works/{quote(doi)}"
    if params:
        url += "?" + urlencode(params)
    data = client.json_get("crossref", url)
    if data and data.get("message"):
        return data["message"]
    return None


def crossref_search(client: HttpClient, title: str, first_author: str = "", contact_email: str = "") -> List[Dict[str, Any]]:
    params = {"query.title": title, "rows": "5"}
    if first_author:
        params["query.author"] = first_author
    if contact_email:
        params["mailto"] = contact_email
    url = "https://api.crossref.org/works?" + urlencode(params)
    data = client.json_get("crossref", url)
    if data and data.get("message", {}).get("items"):
        return data["message"]["items"]
    return []


def openalex_by_doi(client: HttpClient, doi: str) -> Optional[Dict[str, Any]]:
    doi = normalize_doi(doi)
    if not doi:
        return None
    url = "https://api.openalex.org/works/" + quote(f"https://doi.org/{doi}", safe="")
    return client.json_get("openalex", url)


def openalex_search(client: HttpClient, title: str) -> List[Dict[str, Any]]:
    url = "https://api.openalex.org/works?" + urlencode({"search": title, "per-page": "5"})
    data = client.json_get("openalex", url)
    if data and data.get("results"):
        return data["results"]
    return []


def semantic_scholar_by_doi(client: HttpClient, doi: str) -> Optional[Dict[str, Any]]:
    doi = normalize_doi(doi)
    if not doi:
        return None
    fields = "title,authors,year,venue,url,externalIds,citationCount,influentialCitationCount,abstract"
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{quote(doi)}?" + urlencode({"fields": fields})
    return client.json_get("semantic_scholar", url)


def semantic_scholar_search(client: HttpClient, title: str) -> List[Dict[str, Any]]:
    fields = "title,authors,year,venue,url,externalIds,citationCount,influentialCitationCount,abstract"
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urlencode({"query": title, "limit": "5", "fields": fields})
    data = client.json_get("semantic_scholar", url)
    if data and data.get("data"):
        return data["data"]
    return []


def crossref_authors(item: Dict[str, Any]) -> List[str]:
    authors = []
    for author in item.get("author") or []:
        name = normalize_space(" ".join(part for part in [author.get("given", ""), author.get("family", "")] if part))
        if name:
            authors.append(name)
    return authors


def openalex_authors(item: Dict[str, Any]) -> List[str]:
    authors = []
    for authorship in item.get("authorships") or []:
        display_name = (authorship.get("author") or {}).get("display_name")
        if display_name:
            authors.append(display_name)
    return authors


def s2_authors(item: Dict[str, Any]) -> List[str]:
    return [a.get("name", "") for a in item.get("authors") or [] if a.get("name")]


def first(values: Iterable[Any]) -> str:
    for value in values:
        if isinstance(value, str) and value:
            return value
        if isinstance(value, list) and value:
            return str(value[0])
    return ""


def year_from_crossref(item: Dict[str, Any]) -> Optional[int]:
    for key in ("published-print", "published-online", "published", "issued"):
        parts = (item.get(key) or {}).get("date-parts") or []
        if parts and parts[0]:
            try:
                return int(parts[0][0])
            except (TypeError, ValueError):
                pass
    return None


def collect_metadata(ref: Dict[str, Any], client: HttpClient, contact_email: str) -> Dict[str, Any]:
    title = ref.get("title", "")
    first_author = ref.get("first_author", "")
    doi = normalize_doi(ref.get("doi", ""))
    candidates: List[Dict[str, Any]] = []

    crossref_doi = crossref_by_doi(client, doi, contact_email) if doi else None
    if crossref_doi:
        candidates.append({
            "provider": "crossref_doi",
            "title": first([crossref_doi.get("title")]),
            "doi": normalize_doi(crossref_doi.get("DOI", "")),
            "authors": crossref_authors(crossref_doi),
            "year": year_from_crossref(crossref_doi),
            "url": crossref_doi.get("URL", ""),
            "container_title": first([crossref_doi.get("container-title")]),
            "issn": crossref_doi.get("ISSN") or [],
            "abstract": clean_abstract(crossref_doi.get("abstract", "")),
            "raw": crossref_doi,
        })

    openalex_doi = openalex_by_doi(client, doi) if doi else None
    if openalex_doi and not openalex_doi.get("error"):
        candidates.append({
            "provider": "openalex_doi",
            "title": openalex_doi.get("display_name", ""),
            "doi": normalize_doi(openalex_doi.get("doi", "")),
            "authors": openalex_authors(openalex_doi),
            "year": openalex_doi.get("publication_year"),
            "url": first([
                (openalex_doi.get("primary_location") or {}).get("landing_page_url", ""),
                openalex_doi.get("id", ""),
            ]),
            "container_title": ((openalex_doi.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
            "issn": ((openalex_doi.get("primary_location") or {}).get("source") or {}).get("issn") or [],
            "citations": openalex_doi.get("cited_by_count"),
            "abstract": reconstruct_openalex_abstract(openalex_doi.get("abstract_inverted_index")),
            "raw": openalex_doi,
        })

    s2_doi = semantic_scholar_by_doi(client, doi) if doi else None
    if s2_doi and not s2_doi.get("error"):
        candidates.append({
            "provider": "semantic_scholar_doi",
            "title": s2_doi.get("title", ""),
            "doi": normalize_doi((s2_doi.get("externalIds") or {}).get("DOI", "")),
            "authors": s2_authors(s2_doi),
            "year": s2_doi.get("year"),
            "url": s2_doi.get("url", ""),
            "container_title": s2_doi.get("venue", ""),
            "citations": s2_doi.get("citationCount"),
            "influential_citations": s2_doi.get("influentialCitationCount"),
            "abstract": s2_doi.get("abstract", ""),
            "raw": s2_doi,
        })

    search_terms = [title] + [frag for frag in ref.get("key_fragments") or [] if frag]
    for term in search_terms[:3]:
        for item in crossref_search(client, term, first_author, contact_email):
            candidates.append({
                "provider": "crossref_search",
                "title": first([item.get("title")]),
                "doi": normalize_doi(item.get("DOI", "")),
                "authors": crossref_authors(item),
                "year": year_from_crossref(item),
                "url": item.get("URL", ""),
                "container_title": first([item.get("container-title")]),
                "issn": item.get("ISSN") or [],
                "abstract": clean_abstract(item.get("abstract", "")),
                "raw": item,
            })
        for item in openalex_search(client, term):
            candidates.append({
                "provider": "openalex_search",
                "title": item.get("display_name", ""),
                "doi": normalize_doi(item.get("doi", "")),
                "authors": openalex_authors(item),
                "year": item.get("publication_year"),
                "url": first([(item.get("primary_location") or {}).get("landing_page_url", ""), item.get("id", "")]),
                "container_title": ((item.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                "issn": ((item.get("primary_location") or {}).get("source") or {}).get("issn") or [],
                "citations": item.get("cited_by_count"),
                "abstract": reconstruct_openalex_abstract(item.get("abstract_inverted_index")),
                "raw": item,
            })
        for item in semantic_scholar_search(client, term):
            candidates.append({
                "provider": "semantic_scholar_search",
                "title": item.get("title", ""),
                "doi": normalize_doi((item.get("externalIds") or {}).get("DOI", "")),
                "authors": s2_authors(item),
                "year": item.get("year"),
                "url": item.get("url", ""),
                "container_title": item.get("venue", ""),
                "citations": item.get("citationCount"),
                "influential_citations": item.get("influentialCitationCount"),
                "abstract": item.get("abstract", ""),
                "raw": item,
            })

    best = choose_best_candidate(ref, candidates)
    return {"candidates": strip_raw(candidates), "best": strip_raw_one(best) if best else None, "best_raw": best}


def choose_best_candidate(ref: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    expected_title = ref.get("title", "")
    expected_author = ref.get("first_author", "")
    expected_doi = normalize_doi(ref.get("doi", ""))
    expected_year = safe_int(ref.get("year"))

    def score(candidate: Dict[str, Any]) -> float:
        title_score = title_similarity(expected_title, candidate.get("title", "")) * 60
        author_ok, _ = first_author_matches(expected_author, candidate.get("authors") or [])
        author_score = 25 if author_ok else 0
        doi_score = 15 if expected_doi and normalize_doi(candidate.get("doi", "")) == expected_doi else 0
        candidate_year = safe_int(candidate.get("year"))
        year_score = (
            10
            if expected_year and candidate_year == expected_year
            else -20
            if expected_year and candidate_year and candidate_year != expected_year
            else 0
        )
        provider_bonus = 5 if candidate.get("provider", "").endswith("_doi") else 0
        return title_score + author_score + doi_score + year_score + provider_bonus

    if not candidates:
        return None
    return max(candidates, key=score)


def strip_raw(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [strip_raw_one(c) for c in candidates[:20]]


def strip_raw_one(candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in candidate.items() if k != "raw"}


def verify_authenticity(ref: Dict[str, Any], best: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    checks = []
    flags = []
    expected_title = ref.get("title", "")
    expected_author = ref.get("first_author", "")
    expected_doi = normalize_doi(ref.get("doi", ""))
    expected_year = safe_int(ref.get("year"))

    if not best:
        return {
            "status": "failed",
            "checks": [{"name": "metadata_lookup", "status": "failed", "detail": "No matching metadata found."}],
            "flags": ["METADATA_NOT_FOUND", "METADATA_ONLY"],
            "matched_metadata": None,
        }

    sim = title_similarity(expected_title, best.get("title", ""))
    checks.append({"name": "title_match", "status": "passed" if sim >= 0.88 else "failed", "score": round(sim, 3), "matched_title": best.get("title", "")})
    if sim < 0.88:
        flags.append("TITLE_MISMATCH")

    author_ok, matched_author = first_author_matches(expected_author, best.get("authors") or [])
    checks.append({"name": "first_author_match", "status": "passed" if author_ok else "failed", "expected": expected_author, "matched": matched_author})
    if expected_author and not author_ok:
        flags.append("AUTHOR_MISMATCH")

    matched_year = safe_int(best.get("year"))
    if expected_year is not None:
        year_ok = matched_year == expected_year
        checks.append(
            {
                "name": "year_match",
                "status": "passed" if year_ok else "failed",
                "expected": expected_year,
                "matched": matched_year,
            }
        )
        if not year_ok:
            flags.append("YEAR_MISMATCH")

    matched_doi = normalize_doi(best.get("doi", ""))
    if expected_doi and matched_doi:
        doi_ok = expected_doi == matched_doi
        checks.append({"name": "doi_reverse_lookup", "status": "passed" if doi_ok else "failed", "expected": expected_doi, "matched": matched_doi})
        if not doi_ok:
            flags.append("DOI_MISMATCH")
    elif expected_doi and not matched_doi:
        checks.append({"name": "doi_reverse_lookup", "status": "failed", "expected": expected_doi, "matched": ""})
        flags.append("DOI_MISMATCH")
    else:
        checks.append({"name": "doi_reverse_lookup", "status": "not_applicable", "detail": "No DOI provided."})

    matched_url = best.get("url") or ref.get("url") or ""
    if matched_url:
        checks.append({"name": "url_present", "status": "passed", "url": matched_url})
    else:
        checks.append({"name": "url_present", "status": "failed"})
        flags.append("MISSING_URL")

    passed_required = (
        sim >= 0.88
        and (not expected_author or author_ok)
        and "DOI_MISMATCH" not in flags
        and "YEAR_MISMATCH" not in flags
    )
    status = "verified" if passed_required else "partial" if sim >= 0.75 else "failed"
    return {"status": status, "checks": checks, "flags": flags, "matched_metadata": strip_raw_one(best)}


def verify_quotes(ref: Dict[str, Any], best: Optional[Dict[str, Any]], client: HttpClient) -> Dict[str, Any]:
    quoted_claims = ref.get("quoted_claims") or []
    if not quoted_claims:
        return {"status": "not_requested", "checks": [], "metadata_only": False}

    source_texts = []
    if best and best.get("abstract"):
        source_texts.append(("abstract_metadata", best.get("abstract", "")))

    url = ref.get("url") or (best or {}).get("url") or ""
    if url and url.startswith("http"):
        html_text = client.text_get("source_url", url)
        if html_text:
            source_texts.append(("source_url", html_to_text(html_text)))

    checks = []
    metadata_only = bool(source_texts) and all(name == "abstract_metadata" for name, _ in source_texts)
    for claim in quoted_claims:
        quote_text = normalize_space(claim.get("quote", ""))
        best_match = find_best_quote_match(quote_text, source_texts)
        status = "passed" if best_match["score"] >= 0.92 else "partial" if best_match["score"] >= 0.78 else "failed"
        checks.append({
            "id": claim.get("id", ""),
            "status": status,
            "score": best_match["score"],
            "source": best_match["source"],
            "matched_excerpt": best_match["excerpt"],
        })

    if not source_texts:
        return {"status": "failed", "checks": checks, "metadata_only": True, "flags": ["QUOTE_SOURCE_UNAVAILABLE", "METADATA_ONLY"]}

    if all(check["status"] == "passed" for check in checks):
        status = "verified"
    elif any(check["status"] in {"passed", "partial"} for check in checks):
        status = "partial"
    else:
        status = "failed"
    flags = ["METADATA_ONLY"] if metadata_only else []
    if status != "verified":
        flags.append("QUOTE_UNVERIFIED")
    return {"status": status, "checks": checks, "metadata_only": metadata_only, "flags": flags}


def html_to_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value)
    value = re.sub(r"<[^>]+>", " ", value)
    return normalize_space(html.unescape(value))


def find_best_quote_match(quote_text: str, source_texts: List[Tuple[str, str]]) -> Dict[str, Any]:
    norm_quote = normalize_text(quote_text)
    if not norm_quote or not source_texts:
        return {"score": 0.0, "source": "", "excerpt": ""}

    best = {"score": 0.0, "source": "", "excerpt": ""}
    q_words = norm_quote.split()
    window = max(8, len(q_words) + 4)
    for source_name, text in source_texts:
        norm_text = normalize_text(text)
        if norm_quote in norm_text:
            excerpt = excerpt_around(text, quote_text)
            return {"score": 1.0, "source": source_name, "excerpt": excerpt}
        words = norm_text.split()
        for i in range(0, max(1, len(words) - window + 1)):
            candidate = " ".join(words[i:i + window])
            score = difflib.SequenceMatcher(None, norm_quote, candidate).ratio()
            if score > best["score"]:
                best = {"score": round(score, 3), "source": source_name, "excerpt": " ".join(words[i:i + window])[:360]}
    return best


def excerpt_around(text: str, quote_text: str, radius: int = 180) -> str:
    lower = text.casefold()
    idx = lower.find(quote_text.casefold())
    if idx < 0:
        return normalize_space(text[: radius * 2])
    start = max(0, idx - radius)
    end = min(len(text), idx + len(quote_text) + radius)
    return normalize_space(text[start:end])


def load_quality_registry(path: str) -> Dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def verify_quality(ref: Dict[str, Any], best: Optional[Dict[str, Any]], registry: Dict[str, Any], current_year: int) -> Dict[str, Any]:
    credentials = ***REDACTED***
    flags = []
    matched = best or {}
    venue_name = normalize_space(matched.get("container_title", ""))
    source_url = matched.get("url", "")
    issn_values = set(normalize_issn(v) for v in ((best or {}).get("issn") or []) if v)

    venue_match = match_venue(venue_

... [Content truncated, total 44,970 chars] ...