# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""NCBI E-utilities wrapper for protein and nucleotide sequence retrieval.

Provides subcommands for the core NCBI E-utilities operations needed for
protein sequence retrieval: efetch, esearch, elink, CDS translation,
patent sequence search, and gene-to-protein lookup.

Rate-limited to 3 requests/second (10/s with NCBI_API_KEY).
"""

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "polite-http",
#   "python-dotenv",
# ]
# ///

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import dotenv
from polite_http import http_client

_CODON_TABLE = {
    'ATA': 'I',
    'ATC': 'I',
    'ATT': 'I',
    'ATG': 'M',
    'ACA': 'T',
    'ACC': 'T',
    'ACG': 'T',
    'ACT': 'T',
    'AAC': 'N',
    'AAT': 'N',
    'AAA': 'K',
    'AAG': 'K',
    'AGC': 'S',
    'AGT': 'S',
    'AGA': 'R',
    'AGG': 'R',
    'CTA': 'L',
    'CTC': 'L',
    'CTG': 'L',
    'CTT': 'L',
    'CCA': 'P',
    'CCC': 'P',
    'CCG': 'P',
    'CCT': 'P',
    'CAC': 'H',
    'CAT': 'H',
    'CAA': 'Q',
    'CAG': 'Q',
    'CGA': 'R',
    'CGC': 'R',
    'CGG': 'R',
    'CGT': 'R',
    'GTA': 'V',
    'GTC': 'V',
    'GTG': 'V',
    'GTT': 'V',
    'GCA': 'A',
    'GCC': 'A',
    'GCG': 'A',
    'GCT': 'A',
    'GAC': 'D',
    'GAT': 'D',
    'GAA': 'E',
    'GAG': 'E',
    'GGA': 'G',
    'GGC': 'G',
    'GGG': 'G',
    'GGT': 'G',
    'TCA': 'S',
    'TCC': 'S',
    'TCG': 'S',
    'TCT': 'S',
    'TTC': 'F',
    'TTT': 'F',
    'TTA': 'L',
    'TTG': 'L',
    'TAC': 'Y',
    'TAT': 'Y',
    'TAA': '*',
    'TAG': '*',
    'TGC': 'C',
    'TGT': 'C',
    'TGA': '*',
    'TGG': 'W',
}


EUTILS_BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'

_CLIENT = None


def get_api_client():
  """Returns the lazily initialized HttpClient."""
  global _CLIENT
  if _CLIENT is None:
    api_key = ***REDACTED***
    qps = 10.0 if api_key else 3.0
    _CLIENT = http_client.HttpClient(EUTILS_BASE, qps=qps)
  return _CLIENT


def _eutils_get(endpoint: str, params: dict[str, str | int]) -> str | None:
  """Sends a GET request to an NCBI E-utilities endpoint.

  Handles rate limiting, retries with backoff, and API key
  injection.

  Args:
    endpoint: E-utilities endpoint name (e.g. 'efetch.fcgi').
    params: Query parameters as a dict.

  Returns:
    Response text or None on failure.
  """
  api_key = ***REDACTED***
  if api_key:
    ***REDACTED***

  query_string = urllib.parse.urlencode(params)
  full_url = f'{EUTILS_BASE}/{endpoint}'
  if query_string:
    full_url += f'?{query_string}'

  try:
    return get_api_client().fetch_text(full_url)
  except http_client.HttpError as e:
    print(f'{endpoint} error after all retires: {e}', file=sys.stderr)
    return None


def efetch(
    db: str,
    db_id: str | int,
    retmode: str = 'text',
    rettype: str = 'fasta',
) -> str | None:
  """Fetches data from NCBI efetch endpoint.

  Args:
    db: Database name (protein, nuccore, gene, pubmed, etc.)
    db_id: One or more comma-separated IDs.
    retmode: Return mode (text, xml, json).
    rettype: Return type (fasta, gb, gp, fasta_cds_aa, etc.)

  Returns:
    Response text or None on failure.
  """
  return _eutils_get(
      'efetch.fcgi',
      {
          'db': db,
          'id': str(db_id),
          'rettype': rettype,
          'retmode': retmode,
      },
  )


def esearch(
    db: str,
    term: str,
    retmax: int = 20,
) -> tuple[list[str], int]:
  """Searches NCBI esearch endpoint.

  Args:
    db: Database name (protein, nuccore, gene, pubmed, etc.)
    term: Search query using Entrez syntax.
    retmax: Maximum results to return.

  Returns:
    Tuple of (list of ID strings, total count).
  """
  text = _eutils_get(
      'esearch.fcgi',
      {
          'db': db,
          'term': term,
          'retmode': 'json',
          'retmax': retmax,
      },
  )
  if text:
    try:
      data = json.loads(text)
      result = data.get('esearchresult', {})
      return result.get('idlist', []), int(result.get('count', 0))
    except (json.JSONDecodeError, ValueError) as e:
      print(f'esearch parse error: {e}', file=sys.stderr)
  return [], 0


def elink(dbfrom: str, db: str, link_id: str) -> list[str]:
  """Follows cross-database links via NCBI elink.

  Args:
    dbfrom: Source database (e.g., pubmed).
    db: Target database (e.g., protein).
    link_id: ID in the source database.

  Returns:
    List of linked IDs in the target database.
  """
  text = _eutils_get(
      'elink.fcgi',
      {
          'dbfrom': dbfrom,
          'db': db,
          'id': link_id,
          'retmode': 'json',
      },
  )
  if text:
    try:
      data = json.loads(text)
      linksets = data.get('linksets', [])
      if linksets:
        linksetdbs = linksets[0].get('linksetdbs', [])
        if linksetdbs:
          return linksetdbs[0].get('links', [])
    except (json.JSONDecodeError, ValueError) as e:
      print(f'elink parse error: {e}', file=sys.stderr)
  return []


def esummary(db: str, ids: str | list[str]) -> dict[str, Any]:
  """Fetches summary info for one or more IDs.

  Args:
    db: Database name.
    ids: Comma-separated ID string or list.

  Returns:
    Dict of id -> summary info.
  """
  if isinstance(ids, list):
    ids = ','.join(str(i) for i in ids)
  text = _eutils_get(
      'esummary.fcgi',
      {
          'db': db,
          'id': ids,
          'retmode': 'json',
      },
  )
  if text:
    try:
      data = json.loads(text)
      return data.get('result', {})
    except (json.JSONDecodeError, ValueError) as e:
      print(f'esummary parse error: {e}', file=sys.stderr)
  return {}


def parse_fasta(text: str | None) -> list[tuple[str, str]]:
  """Parses FASTA text into list of (header, sequence) tuples."""
  if not text:
    return []
  entries = []
  current_header = None
  current_seq = []
  for line in text.strip().splitlines():
    line = line.strip()
    if line.startswith('>'):
      if current_header is not None:
        entries.append((current_header, ''.join(current_seq)))
      current_header = line
      current_seq = []
    else:
      current_seq.append(line)
  if current_header is not None:
    entries.append((current_header, ''.join(current_seq)))
  return entries


def translate_dna(seq: str) -> str:
  """Translates a DNA sequence to protein using the standard codon table."""
  protein = []
  seq = seq.upper().replace('\n', '').replace(' ', '')
  for i in range(0, len(seq) - len(seq) % 3, 3):
    codon = seq[i : i + 3]
    if 'N' in codon:
      protein.append('X')
    else:
      aa = _CODON_TABLE.get(codon, 'X')
      protein.append(aa)
  return ''.join(protein).rstrip('*')


def get_longest_orf(seq: str, min_len: int = 75) -> str | None:
  """Finds the longest open reading frame in a DNA sequence.

  Searches all 6 reading frames (3 forward + 3 reverse complement).

  Args:
    seq: DNA sequence string.
    min_len: Minimum ORF length in amino acids.

  Returns:
    Longest ORF protein sequence, or None.
  """
  rev_comp = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
  rev_seq = ''.join(rev_comp.get(b, 'N') for b in reversed(seq.upper()))

  longest = ''
  for s in [seq.upper(), rev_seq]:
    for frame in range(3):
      translated = translate_dna(s[frame:])
      # Split on stop codons
      peptides = translated.split('*')
      for pep in peptides:
        idx = pep.find('M')
        if idx != -1:
          orf = pep[idx:]
          if len(orf) >= min_len and len(orf) > len(longest):
            longest = orf
  return longest if longest else None


def extract_cds_translations(
    xml_text: str | None,
    identifier: str | None = None,
    target_len: int = 0,
) -> list[dict[str, str]]:
  """Extracts CDS translations from GenBank XML.

  Args:
    xml_text: GenBank XML string from efetch.
    identifier: Optional gene name to filter by.
    target_len: Optional target protein length for best-match selection.

  Returns:
    List of dicts with keys: translation, product,
    gene, locus_tag, protein_id
  """
  del identifier, target_len  # Reserved for future filtering.
  if not xml_text:
    return []
  results = []
  try:
    root = ET.fromstring(xml_text)
    for seq in root.findall('.//GBSeq'):
      for feat in seq.findall('.//GBFeature'):
        key = feat.find('GBFeature_key')
        if key is None or key.text != 'CDS':
          continue
        entry = {
            'translation': '',
            'product': '',
            'gene': '',
            'locus_tag': '',
            'protein_id': '',
            'note': '',
        }
        for qual in feat.findall('.//GBQualifier'):
          name = qual.find('GBQualifier_name')
          val = qual.find('GBQualifier_value')
          if name is not None and val is not None and val.text:
            if name.text == 'translation':
              entry['translation'] = val.text.upper()
            elif name.text in [
                'product',
                'gene',
                'locus_tag',
                'protein_id',
                'note',
            ]:
              entry[name.text] = val.text
        if entry['translation']:
          results.append(entry)
  except ET.ParseError as e:
    print(f'XML parse error: {e}', file=sys.stderr)
  return results


def is_genomic_record(xml_text: str) -> bool:
  """Checks if a GenBank XML record is genomic DNA (not mRNA/CDS)."""
  try:
    root = ET.fromstring(xml_text)
    moltype = root.find('.//GBSeq_moltype')
    if moltype is not None and moltype.text:
      if 'genomic' in moltype.text.lower():
        return True
    for feat in root.iter('GBFeature'):
      k = feat.find('GBFeature_key')
      if k is not None and k.text == 'source':
        for qual in feat.iter('GBQualifier'):
          n = qual.find('GBQualifier_name')
          v = qual.find('GBQualifier_value')
          if (
              n is not None
              and n.text == 'mol_type'
              and v is not None
              and v.text
              and 'genomic' in v.text.lower()
          ):
            return True
        break
  except ET.ParseError:
    pass
  return False


def cmd_fetch_protein(args: argparse.Namespace) -> None:
  """Fetches protein sequence by accession ID."""
  results = []
  for acc in args.accession:
    fasta = efetch('protein', acc)
    entries = parse_fasta(fasta) if fasta else []
    if entries:
      for header, seq in entries:
        results.append({
            'accession': acc,
            'header': header,
            'sequence': seq,
            'length': len(seq),
        })
    else:
      # Try with dot variant
      if '_' in acc:
        fasta = efetch('protein', acc.replace('_', '.'))
        entries = parse_fasta(fasta) if fasta else []
        for header, seq in entries:
          results.append({
              'accession': acc,
              'header': header,
              'sequence': seq,
              'length': len(seq),
          })
      if not any(r['accession'] == acc for r in results):
        results.append({
            'accession': acc,
            'error': 'Not found',
        })
  _write_output(results, args.output)


def cmd_fetch_nucleotide(args: argparse.Namespace) -> None:
  """Fetches nucleotide sequence by accession ID."""
  results = []
  for acc in args.accession:
    fasta = efetch('nuccore', acc)
    entries = parse_fasta(fasta) if fasta else []
    if entries:
      for header, seq in entries:
        results.append({
            'accession': acc,
            'header': header,
            'sequence': seq,
            'length': len(seq),
        })
    else:
      results.append({'accession': acc, 'error': 'Not found'})
  _write_output(results, args.output)


def cmd_cds_translate(args: argparse.Namespace) -> None:
  """Fetches CDS and translates to protein sequence.

  Tries multiple approaches:
  1. NCBI fasta_cds_aa (pre-translated CDS protein)
  2. GenBank XML CDS translation annotations
  3. Raw nucleotide to 6-frame ORF finding (if not genomic)

  Args:
    args: Parsed CLI args with accession, target_length, and output attributes.
  """
  results = []
  for acc in args.accession:
    result = {'accession': acc}

    # Approach 1: Pre-translated CDS protein
    fasta = efetch('nuccore', acc, rettype='fasta_cds_aa')
    if fasta:
      entries = parse_fasta(fasta)
      if entries:
        best = _pick_best_by_length(entries, args.target_length)
        if best:
          header, seq = best
          seq = seq.replace('*', '')
          # Check for dominant isoform if multiple entries
          if len(entries) > 1 and not args.target_length:
            dom = _get_dominant_cds(acc)
            if dom:
              seq = dom
              header = f'>dominant_isoform_{acc}'
          result['header'] = header
          result['sequence'] = seq
          result['length'] = len(seq)
          result['method'] = 'fasta_cds_aa'
          results.append(result)
          continue

    # Approach 2: GenBank XML CDS translations
    xml_data = efetch('nuccore', acc, retmode='xml', rettype='gb')
    if xml_data:
      genomic = is_genomic_record(xml_data)
      cds_list = extract_cds_translations(xml_data)
      if cds_list:
        if args.target_length:
          best_cds = min(
              cds_list,
              key=lambda c: abs(len(c['translation']) - args.target_length),
          )
        else:
          best_cds = max(
              cds_list,
              key=lambda c: len(c['translation']),
          )
        result['header'] = (
            f'>{best_cds["gene"]}'
            f'|{best_cds["product"]}'
            f'|{best_cds["protein_id"]}'
        )
        result['sequence'] = best_cds['translation']
        result['length'] = len(best_cds['translation'])
        result['method'] = 'genbank_xml_cds'
        result['cds_info'] = best_cds
        if genomic:
          result['is_genomic'] = True
        results.append(result)
        continue
      if genomic:
        result['is_genomic'] = True

    # Approach 3: Raw nucleotide ORF finding
    fasta = efetch('nuccore', acc)
    if fasta:
      entries = parse_fasta(fasta)
      if entries:
        _, dna_seq = entries[0]
        orf = get_longest_orf(dna_seq)
        if orf:
          tl = args.target_length
          if tl == 0 or abs(len(orf) - tl) < 50:
            result['header'] = f'>ORF_{acc}'
            result['sequence'] = orf
            result['length'] = len(orf)
            result['method'] = 'orf_translation'
            results.append(result)
            continue

    result['error'] = 'No CDS translation found'
    results.append(result)

  _write_output(results, args.output)


def cmd_search(args: argparse.Namespace) -> None:
  """Searches an NCBI database by query terms."""
  ids, count = esearch(args.database, args.query, retmax=args.retmax)
  result = {
      'database': args.database,
      'query': args.query,
      'total_count': count,
      'returned_count': len(ids),
      'ids': ids,
  }

  # Optionally fetch FASTA for returned IDs
  if args.fetch_sequences and ids:
    sequences = []
    batch_size = 20
    for i in range(0, len(ids), batch_size):
      batch = ids[i : i + batch_size]
      fasta = efetch(args.database, ','.join(batch))
      if fasta:
        entries = parse_fasta(fasta)
        for header, seq in entries:
          sequences.append({
              'header': header,
              'sequence': seq,
              'length': len(seq),
          })
    result['sequences'] = sequences
  _write_output(result, args.output)


def cmd_elink(args: argparse.Namespace) -> None:
  """Follows cross-database links from one NCBI database to another."""
  linked_ids = elink(args.dbfrom, args.db, args.id)
  result = {
      'source_db': args.dbfrom,
      'target_db': args.db,
      'source_id': args.id,
      'linked_ids': linked_ids,
      'count': len(linked_ids),
  }

  if args.fetch_sequences and linked_ids:
    sequences = []
    batch_size = 20
    for i in range(0, len(linked_ids), batch_size):
      batch = linked_ids[i : i + batch_size]
      fasta = efetch(args.db, ','.join(batch))
      if fasta:
        entries = parse_fasta(fasta)
        for header, seq in entries:
          sequences.append({
              'header': header,
              'sequence': seq,
              'length': len(seq),
          })
    result['sequences'] = sequences

  _write_output(result, args.output)


def cmd_gene_protein(args: argparse.Namespace) -> None:
  """Searches for protein sequence by gene name and organism.

  Tries NCBI Protein database with gene name + organism
  filter. Optionally filters by sequence length.

  Args:
    args: Parsed CLI args with gene, organism, target_length, retmax, and output
      attributes.
  """
  gene = args.gene
  organism = args.organism
  results = []

  # Search NCBI Protein
  query = f'{gene}[Gene Name] AND {organism}[Organism]'
  if args.target_length:
    lo = args.target_length - 25
    hi = args.target_length + 25
    query += f' AND {lo}:{hi}[Sequence Length]'

  ids, count = esearch('protein', query, retmax=args.retmax)
  if ids:
    for uid in ids[: args.retmax]:
      fasta = efetch('protein', uid)
      if fasta:
        entries = parse_fasta(fasta)
        for header, seq in entries:
          results.append({
              'uid': uid,
              'header': header,
              'sequence': seq,
              'length': len(seq),
          })

  output = {
      'gene': gene,
      'organism': organism,
      'query': query,
      'total_count': count,
      'results': results,
  }
  _write_output(output, args.output)


def cmd_locus_protein(args: argparse.Namespace) -> None:
  """Searches for protein sequence by locus tag.

  Tries:
  1. NCBI Protein search by gene name + organism
  2. NCBI Nuccore search for GenBank records with CDS
     translations

  Args:
    args: Parsed CLI args with locus, organism, retmax, and output attributes.
  """
  locus = args.locus
  organism = args.organism
  results = []

  # Try NCBI Protein
  query = f'{locus}[Gene Name]'
  if organism:
    query += f' AND {organism}[Organism]'
  ids, _ = esearch('protein', query, retmax=args.retmax)
  if ids:
    for uid in ids[: args.retmax]:
      fasta = efetch('protein', uid)
      if fasta:
        entries = parse_fasta(fasta)
        for header, seq in entries:
          if len(seq) >= 50:
            results.append({
                'uid': uid,
                'header': header,
                'sequence': seq,
                'length': len(seq),
                'source': 'protein_db',
            })

  # Try NCBI Nuccore for CDS translations
  nuc_query = f'{locus}[Accession] OR {locus}[All Fields]'
  nuc_ids, _ = esearch('nuccore', nuc_query, retmax=10)
  if nuc_ids:
    xml_data = efetch(
        'nuccore',
        ','.join(nuc_ids),
        retmode='xml',
        rettype='gb',
    )
    if xml_data:
      cds_list = extract_cds_translations(xml_data, identifier=locus)
      for cds in cds_list:
        results.append({
            'header': f'>{cds["gene"]}|{cds["product"]}|{cds["protein_id"]}',
            'sequence': cds['translation'],
            'length': len(cds['translation']),
            'source': 'nuccore_cds',
            'gene': cds['gene'],
            'locus_tag': cds['locus_tag'],
        })

  output = {
      'locus': locus,
      'organism': organism or '',
      'total_results': len(results),
      'results': results,
  }
  _write_output(output, args.output)


def cmd_pubmed_proteins(args: argparse.Namespace) -> None:
  """Finds protein sequences linked to a PubMed article.

  Searches:
  1. NCBI Protein records with PMID filter
  2. NCBI elink PubMed to Protein
  3. NCBI Nuccore records with PMID for CDS
     translations

  Args:
    args: Parsed CLI args with pmid, identifier, and output attributes.
  """
  pmid = args.pmid
  identifier = args.identifier
  results = []

  # Step 1: Protein db search by PMID
  prot_ids, _ = esearch('protein', f'{pmid}[PMID]', retmax=100)

  # Step 2: elink PubMed→Protein if no direct hits
  if not prot_ids:
    prot_ids = elink('pubmed', 'protein', pmid)

  if prot_ids:
    batch_size = 20
    for i in range(0, len(prot_ids), batch_size):
      batch = prot_ids[i : i + batch_size]
      xml_data = efetch('protein', ','.join(batch), retmode='xml', rettype='gp')
      if xml_data:
        try:
          root = ET.fromstring(xml_data)
          # NCBI returns GBSeq or INSDSeq depending on format
          seq_els = root.findall('.//GBSeq')
          pfx = 'GBSeq'
          if not seq_els:
            seq_els = root.findall('.//INSDSeq')
            pfx = 'INSDSeq'
          for gb_seq in seq_els:
            defn = gb_seq.find(f'{pfx}_definition')
            acc = gb_seq.find(f'{pfx}_primary-accession')
            seq_el = gb_seq.find(f'{pfx}_sequence')
            if seq_el is not None and seq_el.text:
              defn_text = (defn.text or '') if defn is not None else ''
              entry = {
                  'accession': acc.text if acc is not None else '',
                  'definition': defn_text,
                  'sequence': seq_el.text.upper(),
                  'length': len(seq_el.text),
                  'source': 'protein_db',
              }
              if identifier:
                entry['matches_identifier'] = (
                    identifier.lower() in defn_text.lower()
                )
              results.append(entry)
        except (ET.ParseError, AttributeError):
          pass

  # Step 3: Nuccore records for CDS translations
  nuc_ids, _ = esearch('nuccore', f'{pmid}[PMID]', retmax=100)
  if nuc_ids:
    for i in range(0, len(nuc_ids), 10):
      batch = nuc_ids[i : i + 10]
      xml_data = efetch('nuccore', ','.join(batch), retmode='xml', rettype='gb')
      if xml_data:
        cds_list = extract_cds_translations(xml_data, identifier=identifier)
        for cds in cds_list:
          entry = {
              'gene': cds['gene'],
              'product': cds['product'],
              'protein_id': cds['protein_id'],
              'sequence': cds['translation'],
              'length': len(cds['translation']),
              'source': 'nuccore_cds',
          }
          if identifier:
            entry['matches_identifier'] = (
                identifier.lower() in cds['gene'].lower()
                or identifier.lower() in cds['product'].lower()
                or identifier.lower() in cds['protein_id'].lower()
            )
          results.append(entry)

  output = {
      'pmid': pmid,
      'identifier': identifier or '',
      'total_results': len(results),
      'results': results,
  }
  _write_output(output, args.output)


def cmd_patent_search(args: argparse.Namespace) -> None:
  """Searches for protein sequences from patents.

  Two modes:
  1. By patent number: fetches all protein sequences
     from a specific patent
  2. By keywords: searches NCBI Protein with
     patent[Properties] filter

  Args:
    args: Parsed CLI args with patent_number, keywords, organism, retmax, and
      output attributes.
  """
  results = []

  if args.patent_number:
    # Mode 1: Search by patent number
    patent = args.patent_number.strip()

    # Extract the core 7-10 digit number, ignoring prefixes like US/WO/EP
    # and suffixes like B2/A1
    digit_match = re.search(r'(\d{7,10})', patent)
    digits = digit_match.group(1) if digit_match else ''

    # Build queries in priority order: most specific first.
    # Avoid broad text searches like 'patent {patent}' which match millions
    # of unrelated records and pollute the ID list.
    queries = []
    if digits:
      queries.append(f'{digits}[Patent Publication Number]')

    # Extract country prefix (e.g. US, WO, EP) for exact phrase search
    prefix_match = re.match(r'^([A-Za-z]{2})\s*', patent)
    if prefix_match and digits:
      country = prefix_match.group(1).upper()
      queries.append(f'"{country} {digits}"')

    # Handle international patents
    if re.search(r'^(WO|EP)', patent, re.IGNORECASE):
      stripped = re.sub(r'^(WO|EP)', '', patent)
      queries.append(f'patent {stripped}')

    # Fallback: broad text search only if no specific queries matched
    if not queries:
      queries.append(f'patent {patent}')

    all_ids = []
    for q in queries:
      ids, _ = e

... [Content truncated, total 35,651 chars] ...