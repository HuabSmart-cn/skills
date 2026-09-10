#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests

GWAS_BASE = "https://www.ebi.ac.uk/gwas/rest/api"
EFO_BASE = "https://www.ebi.ac.uk/ols4/api"
OT_BASE = "https://api.platform.opentargets.org/api/v4/graphql"
GNOMAD_BASE = "https://gnomad.broadinstitute.org/api"
REFSNP_BASE = "https://api.ncbi.nlm.nih.gov/variation/v0/refsnp"

DEFAULT_LOCUS_PADDING_BP = 1_000_000
REFSEQ_CHROMOSOMES = {f"NC_{i:06d}": str(i) for i in range(1, 23)}
REFSEQ_CHROMOSOMES.update({"NC_000023": "X", "NC_000024": "Y", "NC_012920": "MT"})

REPO_ROOT = Path(__file__).resolve().parents[2]
GTEX_EQTL_SCRIPT = REPO_ROOT / "gtex-eqtl-skill" / "scripts" / "gtex_eqtl.py"
GENEBASS_GENE_BURDEN_SCRIPT = (
    REPO_ROOT / "genebass-gene-burden-skill" / "scripts" / "genebass_gene_burden.py"
)

TOKEN_STOPWORDS = ***REDACTED***
    "disease",
    "disorder",
    "trait",
    "syndrome",
    "chronic",
    "acute",
    "self",
    "reported",
    "unknown",
}

DEFAULT_TRAIT_SEED_RSIDS: dict[str, list[str]] = {
    "type 2 diabetes": ["rs7903146", "rs13266634", "rs7756992", "rs5219", "rs1801282", "rs4402960"],
    "type ii diabetes": [
        "rs7903146",
        "rs13266634",
        "rs7756992",
        "rs5219",
        "rs1801282",
        "rs4402960",
    ],
    "t2d": ["rs7903146", "rs13266634", "rs7756992", "rs5219", "rs1801282", "rs4402960"],
    "coronary artery disease": [
        "rs1333049",
        "rs4977574",
        "rs9349379",
        "rs6725887",
        "rs1746048",
        "rs3184504",
    ],
    "cad": ["rs1333049", "rs4977574", "rs9349379", "rs6725887", "rs1746048", "rs3184504"],
    "body mass index": [
        "rs9939609",
        "rs17782313",
        "rs6548238",
        "rs10938397",
        "rs7498665",
        "rs7138803",
    ],
    "bmi": ["rs9939609", "rs17782313", "rs6548238", "rs10938397", "rs7498665", "rs7138803"],
    "asthma": ["rs7216389", "rs2305480", "rs9273349"],
    "rheumatoid arthritis": ["rs2476601", "rs3761847", "rs660895"],
    "alzheimer disease": ["rs429358", "rs7412", "rs6733839", "rs11136000", "rs3851179"],
    "alzheimers disease": ["rs429358", "rs7412", "rs6733839", "rs11136000", "rs3851179"],
    "ldl cholesterol": ["rs7412", "rs429358", "rs6511720", "rs629301", "rs12740374", "rs11591147"],
    "total cholesterol": [
        "rs7412",
        "rs429358",
        "rs6511720",
        "rs629301",
        "rs12740374",
        "rs11591147",
    ],
}

SEARCH_STUDY_QUERY = """
query searchStudy($q: String!, $page: Pagination) {
  search(queryString: $q, entityNames: ["study"], page: $page) {
    total
    hits {
      score
      object {
        ... on Study {
          id
          projectId
          traitFromSource
          hasSumstats
        }
      }
    }
  }
}
"""

STUDY_CREDIBLE_SETS_QUERY = """
query studyCredibleSets($studyId: String!, $page: Pagination) {
  study(studyId: $studyId) {
    id
    projectId
    traitFromSource
    credibleSets(page: $page) {
      count
      rows {
        studyLocusId
        chromosome
        position
        pValueExponent
        pValueMantissa
        variant { id rsIds }
      }
    }
  }
}
"""

CREDIBLE_SETS_DETAIL_BATCH_QUERY = """
query l2gAndColoc($studyLocusIds: [String!]!) {
  credibleSets(studyLocusIds: $studyLocusIds) {
    rows {
      studyLocusId
      l2GPredictions {
        rows { score target { id approvedSymbol } }
      }
      colocalisation(page: {index: 0, size: 100}) {
        rows {
          colocalisationMethod
          h4
          clpp
          otherStudyLocus { studyId studyLocusId }
        }
      }
    }
  }
}
"""

SEARCH_TARGET_QUERY = """
query searchTarget($q: String!) {
  search(queryString: $q, entityNames: ["target"], page: {index: 0, size: 10}) {
    hits {
      score
      object {
        ... on Target {
          id
          approvedSymbol
          approvedName
        }
      }
    }
  }
}
"""

GNOMAD_GENE_QUERY = """
query GeneConstraint($geneSymbol: String!, $referenceGenome: ReferenceGenomeId!) {
  gene(gene_symbol: $geneSymbol, reference_genome: $referenceGenome) {
    symbol
    gencode_symbol
    gnomad_constraint {
      exp_lof
      obs_lof
      oe_lof
      oe_lof_lower
      oe_lof_upper
      lof_z
      mis_z
      pLI
    }
  }
}
"""

CODING_SEQUENCE_TERMS = {
    "missense_variant",
    "stop_gained",
    "stop_lost",
    "frameshift_variant",
    "protein_altering_variant",
    "inframe_insertion",
    "inframe_deletion",
    "splice_donor_variant",
    "splice_acceptor_variant",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        s = str(item).strip()
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    s = s.replace(",", "")
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def coerce_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def coerce_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    s = str(value).strip()
    return [s] if s else []


def normalize_rsid(value: str) -> str | None:
    m = re.search(r"(rs\d+)", value.strip(), flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(1).lower().replace("rs", "rs")


def normalize_trait_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def tokenize(value: ***REDACTED***
    tokens = ***REDACTED***
    return {tok for tok in tokens if tok not in TOKEN_STOPWORDS}


def lexical_match_score(text: str, term: str) -> float:
    text_n = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    term_n = re.sub(r"[^a-z0-9]+", " ", term.lower()).strip()
    if not text_n or not term_n:
        return 0.0
    if term_n in text_n:
        return 1.0

    text_tokens = ***REDACTED***
    term_tokens = ***REDACTED***
    if not text_tokens or not term_tokens:
        ***REDACTED***

    overlap = len(text_tokens.intersection(term_tokens))
    if overlap == 0:
        return 0.0

    coverage = overlap / max(len(term_tokens), 1)
    precision = overlap / max(len(text_tokens), 1)
    score = 0.6 * coverage + 0.4 * precision
    if overlap >= 2:
        score += 0.1
    return min(score, 1.0)


def safe_get_json(
    url: str, params: dict[str, Any] | None = None, timeout: int = 45
) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        return payload
    return {"results": payload}


def safe_post_json(url: str, payload: dict[str, Any], timeout: int = 60) -> dict[str, Any]:
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict):
        return data
    return {"results": data}


def run_json_skill_script(
    script_path: Path,
    payload: dict[str, Any],
    limitations: list[str],
    timeout_s: int = 45,
) -> dict[str, Any] | None:
    if not script_path.exists():
        limitations.append(f"Missing skill script: {script_path}")
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
    except Exception as exc:
        limitations.append(f"Failed to execute {script_path.name}: {exc}")
        return None

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        details = stderr or stdout or f"exit_code={proc.returncode}"
        limitations.append(f"{script_path.name} failed: {details}")
        return None

    out = (proc.stdout or "").strip()
    if not out:
        limitations.append(f"{script_path.name} returned empty output")
        return None

    try:
        parsed = json.loads(out)
    except Exception as exc:
        limitations.append(f"{script_path.name} returned non-JSON output: {exc}")
        return None

    if not isinstance(parsed, dict):
        limitations.append(f"{script_path.name} returned unexpected JSON shape")
        return None

    return parsed


def resolve_efo(trait_query: str, warnings: list[str], limitations: list[str]) -> dict[str, Any]:
    if not trait_query:
        return {
            "anchor_label": "",
            "efo_id": None,
            "anchor_iri": None,
            "synonyms": [],
            "descendants": [],
            "resolver_source": "efo-ontology-skill",
        }

    params = {
        "q": trait_query,
        "ontology": "efo",
        "type": "class",
        "queryFields": "label,synonym,short_form,obo_id",
        "rows": 25,
        "exact": "false",
        "local": "true",
    }
    try:
        search_data = safe_get_json(f"{EFO_BASE}/search", params=params)
        docs = (search_data.get("response") or {}).get("docs") or []
        if not docs:
            warnings.append("No EFO hit found for trait_query; continuing with free-text only.")
            return {
                "anchor_label": trait_query,
                "efo_id": None,
                "anchor_iri": None,
                "synonyms": [],
                "descendants": [],
                "resolver_source": "efo-ontology-skill",
            }

        top = coerce_dict(docs[0])
        iri = top.get("iri")
        label = str(top.get("label") or trait_query)
        efo_id = top.get("obo_id")
        synonyms = as_string_list(top.get("synonym"))

        descendants: list[str] = []
        if iri:
            encoded = requests.utils.quote(requests.utils.quote(str(iri), safe=""), safe="")
            page = 0
            total_pages = 1
            while page < total_pages and page < 6:
                desc_data = safe_get_json(
                    f"{EFO_BASE}/ontologies/efo/terms/{encoded}/descendants",
                    params={"size": 200, "page": page},
                )
                rows = (desc_data.get("_embedded") or {}).get("terms") or []
                descendants.extend(
                    [str(row.get("label")).strip() for row in rows if coerce_dict(row).get("label")]
                )
                page_info = coerce_dict(desc_data.get("page"))
                total_pages = int(page_info.get("totalPages", 0) or 0)
                page += 1

        return {
            "anchor_label": label,
            "efo_id": efo_id,
            "anchor_iri": iri,
            "synonyms": dedupe_keep_order(synonyms),
            "descendants": dedupe_keep_order(descendants),
            "resolver_source": "efo-ontology-skill",
        }
    except Exception as exc:
        limitations.append(f"EFO resolver unavailable: {exc}")
        return {
            "anchor_label": trait_query,
            "efo_id": None,
            "anchor_iri": None,
            "synonyms": [],
            "descendants": [],
            "resolver_source": "efo-ontology-skill",
        }


def gwas_iter_associations(
    params: dict[str, Any],
    max_rows: int,
    page_size: int = 200,
    max_pages: int = 25,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page = 0
    total_pages = 1
    while page < total_pages and page < max_pages and len(rows) < max_rows:
        q = dict(params)
        q.update({"size": page_size, "page": page})
        data = safe_get_json(f"{GWAS_BASE}/v2/associations", params=q, timeout=45)
        chunk = (data.get("_embedded") or {}).get("associations") or []
        rows.extend(coerce_list_of_dicts(chunk))
        page_info = coerce_dict(data.get("page"))
        total_pages = int(page_info.get("totalPages", 0) or 0)
        page += 1
        time.sleep(0.05)
    return rows[:max_rows]


def parse_rsid_from_association(row: dict[str, Any]) -> str | None:
    snp_allele = row.get("snp_allele")
    if isinstance(snp_allele, list):
        for item in snp_allele:
            if isinstance(item, dict) and item.get("rs_id"):
                rsid = normalize_rsid(str(item["rs_id"]))
                if rsid:
                    return rsid
    effect = row.get("snp_effect_allele")
    if isinstance(effect, list) and effect:
        token = ***REDACTED***
        rsid = normalize_rsid(token)
        if rsid:
            return rsid
    if row.get("rs_id"):
        rsid = normalize_rsid(str(row["rs_id"]))
        if rsid:
            return rsid
    snp_link = coerce_dict(coerce_dict(row.get("_links")).get("snp")).get("href")
    if isinstance(snp_link, str):
        rsid = normalize_rsid(snp_link)
        if rsid:
            return rsid
    return None


def extract_trait_name(row: dict[str, Any]) -> str:
    efo_traits = row.get("efo_traits")
    if isinstance(efo_traits, list):
        for trait in efo_traits:
            if isinstance(trait, dict) and trait.get("efo_trait"):
                return str(trait["efo_trait"])
    reported_trait = row.get("reported_trait")
    if isinstance(reported_trait, list) and reported_trait:
        return str(reported_trait[0])
    if isinstance(reported_trait, str):
        return reported_trait
    return ""


def extract_mapped_genes(row: dict[str, Any]) -> list[str]:
    mapped = row.get("mapped_genes")
    out: list[str] = []
    if isinstance(mapped, list):
        for entry in mapped:
            if isinstance(entry, str):
                parts = [p.strip() for p in entry.split(",") if p.strip()]
                out.extend(parts)
    return dedupe_keep_order(out)


def normalize_anchor_row(row: dict[str, Any]) -> dict[str, Any] | None:
    rsid = parse_rsid_from_association(row)
    if not rsid:
        return None
    p_value = safe_float(row.get("p_value"))
    trait_name = extract_trait_name(row)
    return {
        "rsid": rsid,
        "lead_trait": trait_name,
        "p_value": p_value,
        "cohort": "",
        "accession_id": row.get("accession_id"),
        "mapped_genes": extract_mapped_genes(row),
        "association_id": row.get("association_id"),
    }


def fetch_gwas_study_metadata(
    accession_ids: list[str], limitations: list[str]
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for accession_id in sorted(set(accession_ids)):
        if not accession_id:
            continue
        try:
            data = safe_get_json(f"{GWAS_BASE}/v2/studies/{accession_id}", timeout=45)
            out[accession_id] = {
                "cohort": ", ".join(as_string_list(data.get("cohort"))),
                "discovery_ancestry": ", ".join(as_string_list(data.get("discovery_ancestry"))),
                "initial_sample_size": data.get("initial_sample_size"),
            }
            time.sleep(0.03)
        except Exception as exc:
            limitations.append(f"GWAS study metadata unavailable for {accession_id}: {exc}")
    return out


def chromosome_from_refseq(seq_id: str) -> str | None:
    accession = seq_id.split(".", 1)[0]
    return REFSEQ_CHROMOSOMES.get(accession)


def assembly_key_from_traits(traits: list[dict[str, Any]]) -> str | None:
    for trait in traits:
        assembly_name = str(trait.get("assembly_name") or "")
        if assembly_name.startswith("GRCh38"):
            return "grch38"
        if assembly_name.startswith("GRCh37"):
            return "grch37"
    return None


def coordinate_from_placement(placement: dict[str, Any]) -> dict[str, Any] | None:
    seq_id = str(placement.get("seq_id") or "")
    chrom = chromosome_from_refseq(seq_id)
    if not chrom:
        return None

    placement_annot = coerce_dict(placement.get("placement_annot"))
    traits = coerce_list_of_dicts(placement_annot.get("seq_id_traits_by_assembly"))
    if not traits:
        return None

    # Prefer primary top-level chromosome placements over alt loci or patches.
    if not any(
        trait.get("is_top_level")
        and trait.get("is_chromosome")
        and not trait.get("is_alt")
        and not trait.get("is_patch")
        for trait in traits
    ):
        return None

    spdis: list[dict[str, Any]] = []
    for allele in coerce_list_of_dicts(placement.get("alleles")):
        spdi = coerce_dict(coerce_dict(allele.get("allele")).get("spdi"))
        if spdi:
            spdis.append(spdi)
    if not spdis:
        return None

    positions = {spdi.get("position") for spdi in spdis if spdi.get("position") is not None}
    if not positions:
        return None
    try:
        pos = int(sorted(positions)[0]) + 1
    except Exception:
        return None

    deleted_sequences = [
        str(spdi.get("deleted_sequence") or "")
        for spdi in spdis
        if str(spdi.get("deleted_sequence") or "")
    ]
    if not deleted_sequences:
        return None
    ref = deleted_sequences[0]

    alternate_alleles = sorted(
        {
            str(spdi.get("inserted_sequence") or "")
            for spdi in spdis
            if str(spdi.get("inserted_sequence") or "")
            and str(spdi.get("inserted_sequence") or "") != str(spdi.get("deleted_sequence") or "")
        }
    )
    alt = alternate_alleles[-1] if alternate_alleles else ref

    assembly_name = str(traits[0].get("assembly_name") or "")
    return {
        "chr": chrom,
        "pos": pos,
        "ref": ref,
        "alt": alt,
        "alternate_alleles": alternate_alleles,
        "seq_id": seq_id,
        "assembly": assembly_name,
    }


def fetch_refsnp_payload(rsid: str, limitations: list[str]) -> dict[str, Any] | None:
    digits = "".join(ch for ch in rsid if ch.isdigit())
    if not digits:
        return None
    try:
        return safe_get_json(f"{REFSNP_BASE}/{digits}", timeout=35)
    except Exception as exc:
        limitations.append(f"RefSNP lookup failed for {rsid}: {exc}")
        return None


def resolve_refsnp_coordinates(
    rsid: str, warnings: list[str], limitations: list[str]
) -> dict[str, dict[str, Any]]:
    payload = fetch_refsnp_payload(rsid, limitations)
    if not payload:
        return {}

    coords: dict[str, dict[str, Any]] = {}
    snapshot = coerce_dict(payload.get("primary_snapshot_data"))
    for placement in coerce_list_of_dicts(snapshot.get("placements_with_allele")):
        traits = coerce_list_of_dicts(
            coerce_dict(placement.get("placement_annot")).get("seq_id_traits_by_assembly")
        )
        assembly_key = assembly_key_from_traits(traits)
        if not assembly_key or assembly_key in coords:
            continue
        coord = coordinate_from_placement(placement)
        if coord:
            coords[assembly_key] = coord

    if "grch38" not in coords:
        warnings.append(f"Coordinate lookup did not find a GRCh38 top-level placement for {rsid}.")
    return coords


def resolve_anchor_coordinates(
    anchors: list[dict[str, Any]], warnings: list[str], limitations: list[str]
) -> None:
    for anchor in anchors:
        rsid = str(anchor.get("rsid") or "")
        if not rsid:
            continue
        coord_result = resolve_refsnp_coordinates(rsid, warnings, limitations)
        g38 = coerce_dict(coord_result.get("grch38"))
        g37 = coerce_dict(coord_result.get("grch37"))
        anchor["grch38"] = g38 if g38 else None
        anchor["grch37"] = g37 if g37 else None

        chr_ = g38.get("chr")
        pos = g38.get("pos")
        if chr_ is not None and pos is not None:
            try:
                pos_i = int(pos)
                start = max(1, pos_i - DEFAULT_LOCUS_PADDING_BP)
                end = pos_i + DEFAULT_LOCUS_PADDING_BP
                anchor["locus_id"] = f"chr{str(chr_).upper()}:{start}-{end}"
            except Exception:
                anchor["locus_id"] = f"rsid:{rsid}"
        else:
            anchor["locus_id"] = f"rsid:{rsid}"


def ot_query(query: str, variables: dict[str, Any], limitations: list[str]) -> dict[str, Any]:
    try:
        payload = safe_post_json(OT_BASE, {"query": query, "variables": variables}, timeout=120)
    except Exception as exc:
        limitations.append(f"Open Targets request failed: {exc}")
        return {}

    if payload.get("errors"):
        limitations.append(f"Open Targets GraphQL error: {payload.get('errors')}")
        return {}

    return coerce_dict(payload.get("data"))


def search_ot_studies(
    terms: list[str],
    max_studies: int,
    limitations: list[str],
) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for term in terms:
        if not term:
            continue
        data = ot_query(
            SEARCH_STUDY_QUERY, {"q": term, "page": {"index": 0, "size": 25}}, limitations
        )
        hits = coerce_list_of_dicts(coerce_dict(data.get("search")).get("hits"))
        for hit in hits:
            obj = coerce_dict(hit.get("object"))
            study_id = obj.get("id")
            if not study_id:
                continue
            study = by_id.get(study_id)
            score = safe_float(hit.get("score")) or 0.0
            if study is None:
                by_id[study_id] = {
                    "id": study_id,
                    "projectId": obj.get("projectId"),
                    "traitFromSource": obj.get("traitFromSource"),
                    "hasSumstats": bool(obj.get("hasSumstats")),
                    "best_score": score,
                    "matched_terms": [term],
                }
            else:
                study["best_score"] = max(float(study.get("best_score") or 0.0), score)
                if term not in study["matched_terms"]:
                    study["matched_terms"].append(term)

    studies = sorted(
        by_id.values(), key=lambda row: float(row.get("best_score") or 0.0), reverse=True
    )
    if not studies:
        return []

    with_sumstats = [s for s in studies if s.get("hasSumstats")]
    chosen = with_sumstats[:max_studies] if with_sumstats else studies[:max_studies]
    return chosen


def fetch_ot_l2g_coloc_for_anchors(
    anchor_rsids: list[str],
    trait_terms: list[str],
    max_coloc_rows_per_locus: int,
    limitations: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "per_anchor": {rsid: {"l2g": [], "coloc": []} for rsid in anchor_rsids},
        "studies_used": [],
        "matched_study_loci": 0,
    }
    if not anchor_rsids or not trait_terms:
        return result

    studies = search_ot_studies(trait_terms, max_studies=8, limitations=limitations)
    if not studies:
        warnings.append(
            "No Open Targets studies found for trait terms; L2G/coloc components may be sparse."
        )
        return result

    anchor_set = set(anchor_rsids)
    study_locus_to_anchors: dict[str, set[str]] = {}

    for study in studies:
        study_id = str(study.get("id") or "")
        if not study_id:
            continue
        data = ot_query(
            STUDY_CREDIBLE_SETS_QUERY,
            {"studyId": study_id, "page": {"index": 0, "size": 800}},
            limitations,
        )
        study_payload = coerce_dict(data.get("study"))
        cs_rows = coerce_list_of_dicts(coerce_dict(study_payload.get("credibleSets")).get("rows"))
        for row in cs_rows:
            study_locus_id = row.get("studyLocusId")
            if not study_locus_id:
                continue
            variant = coerce_dict(row.get("variant"))
            rsids = [normalize_rsid(str(r)) for r in as_string_list(variant.get("rsIds"))]
            matched = {r for r in rsids if r and r in anchor_set}
            if not matched:
                continue
            study_locus_to_anchors.setdefault(str(study_locus_id), set()).update(matched)

        result["studies_used"].append(
            {
                "id": study_id,
                "projectId": study.get("projectId"),
                "traitFromSource": study.get("traitFromSource"),
                "matched_terms": study.get("matched_terms", []),
                "credible_set_count": len(cs_rows),
 

... [Content truncated, total 79,824 chars] ...