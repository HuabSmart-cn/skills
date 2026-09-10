"""
Enzyme Pathway Builder for Retrosynthetic Analysis

This module provides tools for constructing enzymatic pathways and
retrosynthetic trees using BRENDA database information.

Key features:
- Find enzymatic pathways for target products
- Build retrosynthetic trees from products
- Suggest enzyme substitutions and alternatives
- Calculate pathway feasibility and thermodynamics
- Optimize pathway conditions (pH, temperature, cofactors)
- Generate detailed pathway reports
- Support for metabolic engineering and synthetic biology

Installation:
    uv pip install networkx matplotlib pandas

Usage:
    from scripts.enzyme_pathway_builder import find_pathway_for_product, build_retrosynthetic_tree

    pathway = find_pathway_for_product("lactate", max_steps=3)
    tree = build_retrosynthetic_tree("lactate", depth=2)
"""

import re
import json
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    print("Warning: networkx not installed. Install with: uv pip install networkx")
    NETWORKX_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("Warning: pandas not installed. Install with: uv pip install pandas")
    PANDAS_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("Warning: matplotlib not installed. Install with: uv pip install matplotlib")
    MATPLOTLIB_AVAILABLE = False

try:
    from brenda_queries import (
        search_enzymes_by_product, search_enzymes_by_substrate,
        get_environmental_parameters, compare_across_organisms,
        get_substrate_specificity, get_cofactor_requirements,
        find_thermophilic_homologs, find_ph_stable_variants
    )
    BRENDA_QUERIES_AVAILABLE = True
except ImportError:
    print("Warning: brenda_queries not available")
    BRENDA_QUERIES_AVAILABLE = False


def validate_dependencies():
    """Validate that required dependencies are installed."""
    missing = []
    if not NETWORKX_AVAILABLE:
        missing.append("networkx")
    if not PANDAS_AVAILABLE:
        missing.append("pandas")
    if not BRENDA_QUERIES_AVAILABLE:
        missing.append("brenda_queries")
    if missing:
        raise ImportError(f"Missing required dependencies: {', '.join(missing)}")


# Common biochemical transformations with typical EC numbers
COMMON_TRANSFORMATIONS = {
    'oxidation': ['1.1.1'],      # Alcohol dehydrogenases
    'reduction': ['1.1.1'],      # Alcohol dehydrogenases
    'hydrolysis': ['3.1.1', '3.1.3'],  # Esterases, phosphatases
    'carboxylation': ['6.4.1'],   # Carboxylases
    'decarboxylation': ['4.1.1'], # Decarboxylases
    'transamination': ['2.6.1'],  # Aminotransferases
    'phosphorylation': ['2.7.1'], # Kinases
    'dephosphorylation': ['3.1.3'], # Phosphatases
    'isomerization': ['5.1.1', '5.3.1'], # Isomerases
    'ligation': ['6.3.1'],       # Ligases
    'transfer': ['2.1.1', '2.2.1', '2.4.1'], # Transferases
    'hydride_transfer': ['1.1.1', '1.2.1'],  # Oxidoreductases
    'group_transfer': ['2.1.1'],  # Methyltransferases
}

# Simple metabolite database (expanded for pathway building)
METABOLITE_DATABASE = {
    # Primary metabolites
    'glucose': {'formula': 'C6H12O6', 'mw': 180.16, 'class': 'sugar'},
    'fructose': {'formula': 'C6H12O6', 'mw': 180.16, 'class': 'sugar'},
    'galactose': {'formula': 'C6H12O6', 'mw': 180.16, 'class': 'sugar'},
    'pyruvate': {'formula': 'C3H4O3', 'mw': 90.08, 'class': 'carboxylic_acid'},
    'lactate': {'formula': 'C3H6O3', 'mw': 90.08, 'class': 'carboxylic_acid'},
    'acetate': {'formula': 'C2H4O2', 'mw': 60.05, 'class': 'carboxylic_acid'},
    'ethanol': {'formula': 'C2H6O', 'mw': 46.07, 'class': 'alcohol'},
    'acetaldehyde': {'formula': 'C2H4O', 'mw': 44.05, 'class': 'aldehyde'},
    'acetone': {'formula': 'C3H6O', 'mw': 58.08, 'class': 'ketone'},
    'glycerol': {'formula': 'C3H8O3', 'mw': 92.09, 'class': 'alcohol'},
    'ammonia': {'formula': 'NH3', 'mw': 17.03, 'class': 'inorganic'},
    'carbon dioxide': {'formula': 'CO2', 'mw': 44.01, 'class': 'inorganic'},
    'water': {'formula': 'H2O', 'mw': 18.02, 'class': 'inorganic'},
    'oxygen': {'formula': 'O2', 'mw': 32.00, 'class': 'inorganic'},
    'hydrogen': {'formula': 'H2', 'mw': 2.02, 'class': 'inorganic'},
    'nitrogen': {'formula': 'N2', 'mw': 28.01, 'class': 'inorganic'},
    'phosphate': {'formula': 'PO4', 'mw': 94.97, 'class': 'inorganic'},
    'sulfate': {'formula': 'SO4', 'mw': 96.06, 'class': 'inorganic'},

    # Amino acids
    'alanine': {'formula': 'C3H7NO2', 'mw': 89.09, 'class': 'amino_acid'},
    'glycine': {'formula': 'C2H5NO2', 'mw': 75.07, 'class': 'amino_acid'},
    'serine': {'formula': 'C3H7NO3', 'mw': 105.09, 'class': 'amino_acid'},
    'threonine': {'formula': 'C4H9NO3', 'mw': 119.12, 'class': 'amino_acid'},
    'aspartate': {'formula': 'C4H7NO4', 'mw': 133.10, 'class': 'amino_acid'},
    'glutamate': {'formula': 'C5H9NO4', 'mw': 147.13, 'class': 'amino_acid'},
    'asparagine': {'formula': 'C4H8N2O3', 'mw': 132.12, 'class': 'amino_acid'},
    'glutamine': {'formula': 'C5H10N2O3', 'mw': 146.15, 'class': 'amino_acid'},
    'lysine': {'formula': 'C6H14N2O2', 'mw': 146.19, 'class': 'amino_acid'},
    'arginine': {'formula': 'C6H14N4O2', 'mw': 174.20, 'class': 'amino_acid'},
    'histidine': {'formula': 'C6H9N3O2', 'mw': 155.16, 'class': 'amino_acid'},
    'phenylalanine': {'formula': 'C9H11NO2', 'mw': 165.19, 'class': 'amino_acid'},
    'tyrosine': {'formula': 'C9H11NO3', 'mw': 181.19, 'class': 'amino_acid'},
    'tryptophan': {'formula': 'C11H12N2O2', 'mw': 204.23, 'class': 'amino_acid'},
    'leucine': {'formula': 'C6H13NO2', 'mw': 131.18, 'class': 'amino_acid'},
    'isoleucine': {'formula': 'C6H13NO2', 'mw': 131.18, 'class': 'amino_acid'},
    'valine': {'formula': 'C5H11NO2', 'mw': 117.15, 'class': 'amino_acid'},
    'methionine': {'formula': 'C5H11NO2S', 'mw': 149.21, 'class': 'amino_acid'},
    'cysteine': {'formula': 'C3H7NO2S', 'mw': 121.16, 'class': 'amino_acid'},
    'proline': {'formula': 'C5H9NO2', 'mw': 115.13, 'class': 'amino_acid'},

    # Nucleotides (simplified)
    'atp': {'formula': 'C10H16N5O13P3', 'mw': 507.18, 'class': 'nucleotide'},
    'adp': {'formula': 'C10H15N5O10P2', 'mw': 427.20, 'class': 'nucleotide'},
    'amp': {'formula': 'C10H14N5O7P', 'mw': 347.22, 'class': 'nucleotide'},
    'nad': {'formula': 'C21H27N7O14P2', 'mw': 663.43, 'class': 'cofactor'},
    'nadh': {'formula': 'C21H29N7O14P2', 'mw': 665.44, 'class': 'cofactor'},
    'nadp': {'formula': 'C21H28N7O17P3', 'mw': 743.44, 'class': 'cofactor'},
    'nadph': {'formula': 'C21H30N7O17P3', 'mw': 745.45, 'class': 'cofactor'},
    'fadh2': {'formula': 'C21H30N7O14P2', 'mw': 785.55, 'class': 'cofactor'},
    'fadx': {'formula': 'C21H20N4O2', 'mw': 350.36, 'class': 'cofactor'},

    # Common organic acids
    'malate': {'formula': 'C4H6O5', 'mw': 134.09, 'class': 'carboxylic_acid'},
    'oxaloacetate': {'formula': 'C4H4O5', 'mw': 132.07, 'class': 'carboxylic_acid'},
    'succinate': {'formula': 'C4H6O4', 'mw': 118.09, 'class': 'carboxylic_acid'},
    'fumarate': {'formula': 'C4H4O4', 'mw': 116.07, 'class': 'carboxylic_acid'},
    'oxalosuccinate': {'formula': 'C6H6O7', 'mw': 190.12, 'class': 'carboxylic_acid'},
    'alpha-ketoglutarate': {'formula': 'C5H6O5', 'mw': 146.11, 'class': 'carboxylic_acid'},

    # Energy carriers
    'acetyl-coa': {'formula': 'C23H38N7O17P3S', 'mw': 809.51, 'class': 'cofactor'},
    'coenzyme-a': {'formula': 'C21H36N7O16P3S', 'mw': 767.54, 'class': 'cofactor'},
}

# Common cofactors and their roles
COFACTOR_ROLES = {
    'nad+': {'role': 'oxidation', 'oxidation_state': '+1'},
    'nadh': {'role': 'reduction', 'oxidation_state': '0'},
    'nadp+': {'role': 'oxidation', 'oxidation_state': '+1'},
    'nadph': {'role': 'reduction', 'oxidation_state': '0'},
    'fadx': {'role': 'oxidation', 'oxidation_state': '0'},
    'fadh2': {'role': 'reduction', 'oxidation_state': '-2'},
    'atp': {'role': 'phosphorylation', 'oxidation_state': '0'},
    'adp': {'role': 'energy', 'oxidation_state': '0'},
    'amp': {'role': 'energy', 'oxidation_state': '0'},
    'acetyl-coa': {'role': 'acetylation', 'oxidation_state': '0'},
    'coenzyme-a': {'role': 'thiolation', 'oxidation_state': '0'},
}


def identify_metabolite(metabolite_name: str) -> Dict[str, Any]:
    """Identify a metabolite from the database or create entry."""
    metabolite_name = metabolite_name.lower().strip()

    # Check if it's in the database
    if metabolite_name in METABOLITE_DATABASE:
        return {'name': metabolite_name, **METABOLITE_DATABASE[metabolite_name]}

    # Simple formula extraction from common patterns
    formula_patterns = {
        r'c(\d+)h(\d+)o(\d+)': lambda m: f"C{m[0]}H{m[1]}O{m[2]}",
        r'c(\d+)h(\d+)n(\d+)o(\d+)': lambda m: f"C{m[0]}H{m[1]}N{m[2]}O{m[3]}",
    }

    for pattern, formatter in formula_patterns.items():
        match = re.search(pattern, metabolite_name)
        if match:
            formula = formatter(match.groups())
            # Estimate molecular weight (C=12, H=1, N=14, O=16)
            mw = 0
            elements = re.findall(r'([A-Z])(\d*)', formula)
            for elem, count in elements:
                count = int(count) if count else 1
                if elem == 'C':
                    mw += count * 12.01
                elif elem == 'H':
                    mw += count * 1.008
                elif elem == 'N':
                    mw += count * 14.01
                elif elem == 'O':
                    mw += count * 16.00
                elif elem == 'P':
                    mw += count * 30.97
                elif elem == 'S':
                    mw += count * 32.07

            return {
                'name': metabolite_name,
                'formula': formula,
                'mw': mw,
                'class': 'unknown'
            }

    # Fallback - unknown metabolite
    return {
        'name': metabolite_name,
        'formula': 'Unknown',
        'mw': 0,
        'class': 'unknown'
    }


def infer_transformation_type(substrate: str, product: str) -> List[str]:
    """Infer the type of transformation based on substrate and product."""
    substrate_info = identify_metabolite(substrate)
    product_info = identify_metabolite(product)

    transformations = []

    # Check for oxidation/reduction patterns
    if 'alcohol' in substrate_info.get('class', '') and 'carboxylic_acid' in product_info.get('class', ''):
        transformations.append('oxidation')
    elif 'aldehyde' in substrate_info.get('class', '') and 'alcohol' in product_info.get('class', ''):
        transformations.append('reduction')
    elif 'alcohol' in substrate_info.get('class', '') and 'aldehyde' in product_info.get('class', ''):
        transformations.append('oxidation')

    # Check for phosphorylation/dephosphorylation
    if 'phosphate' in product and 'phosphate' not in substrate:
        transformations.append('phosphorylation')
    elif 'phosphate' in substrate and 'phosphate' not in product:
        transformations.append('dephosphorylation')

    # Check for carboxylation/decarboxylation
    if 'co2' in product and 'co2' not in substrate:
        transformations.append('carboxylation')
    elif 'co2' in substrate and 'co2' not in product:
        transformations.append('decarboxylation')

    # Check for hydrolysis (simple heuristic)
    if 'ester' in substrate.lower() and ('carboxylic_acid' in product_info.get('class', '') or 'alcohol' in product_info.get('class', '')):
        transformations.append('hydrolysis')

    # Check for transamination
    if 'amino_acid' in product_info.get('class', '') and 'amino_acid' not in substrate_info.get('class', ''):
        transformations.append('transamination')

    # Default to generic transformation
    if not transformations:
        transformations.append('generic')

    return transformations


def find_enzymes_for_transformation(substrate: str, product: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Find enzymes that catalyze a specific transformation."""
    validate_dependencies()

    # Infer transformation types
    transformations = infer_transformation_type(substrate, product)

    all_enzymes = []

    # Try to find enzymes by product
    try:
        product_enzymes = search_enzymes_by_product(product, limit=limit)
        for enzyme in product_enzymes:
            # Check if substrate is in the reactants
            if substrate.lower() in enzyme.get('reaction', '').lower():
                enzyme['transformation'] = transformations[0] if transformations else 'generic'
                enzyme['substrate'] = substrate
                enzyme['product'] = product
                enzyme['confidence'] = 'high'
                all_enzymes.append(enzyme)
        time.sleep(0.5)  # Rate limiting
    except Exception as e:
        print(f"Error searching enzymes by product: {e}")

    # Try to find enzymes by substrate
    try:
        substrate_enzymes = search_enzymes_by_substrate(substrate, limit=limit)
        for enzyme in substrate_enzymes:
            # Check if product is mentioned in substrate data (limited approach)
            enzyme['transformation'] = transformations[0] if transformations else 'generic'
            enzyme['substrate'] = substrate
            enzyme['product'] = product
            enzyme['confidence'] = 'medium'
            all_enzymes.append(enzyme)
        time.sleep(0.5)  # Rate limiting
    except Exception as e:
        print(f"Error searching enzymes by substrate: {e}")

    # If no enzymes found, try common EC numbers for transformation types
    if not all_enzymes and transformations:
        for trans_type in transformations:
            if trans_type in COMMON_TRANSFORMATIONS:
                for ec_prefix in COMMON_TRANSFORMATIONS[trans_type]:
                    # This is a simplified approach - in practice you'd want
                    # to query the specific EC numbers with more detail
                    try:
                        generic_enzymes = search_by_pattern(trans_type, limit=5)
                        for enzyme in generic_enzymes:
                            enzyme['transformation'] = trans_type
                            enzyme['substrate'] = substrate
                            enzyme['product'] = product
                            enzyme['confidence'] = 'low'
                            all_enzymes.append(enzyme)
                        time.sleep(0.5)
                        break
                    except Exception as e:
                        print(f"Error searching for transformation type {trans_type}: {e}")

    # Remove duplicates and sort by confidence
    unique_enzymes = []
    seen = set()
    for enzyme in all_enzymes:
        key = (enzyme.get('ec_number', ''), enzyme.get('organism', ''))
        if key not in seen:
            seen.add(key)
            unique_enzymes.append(enzyme)

    # Sort by confidence (high > medium > low)
    confidence_order = {'high': 3, 'medium': 2, 'low': 1}
    unique_enzymes.sort(key=lambda x: confidence_order.get(x.get('confidence', 'low'), 0), reverse=True)

    return unique_enzymes[:limit]


def find_pathway_for_product(product: str, max_steps: int = 3, starting_materials: List[str] = None) -> Dict[str, Any]:
    """Find enzymatic pathways to synthesize a target product."""
    validate_dependencies()

    if starting_materials is None:
        # Common starting materials
        starting_materials = ['glucose', 'pyruvate', 'acetate', 'ethanol', 'glycerol']

    pathway = {
        'target': product,
        'max_steps': max_steps,
        'starting_materials': starting_materials,
        'steps': [],
        'alternative_pathways': [],
        'warnings': [],
        'confidence': 0
    }

    # Simple breadth-first search for pathway
    from collections import deque

    queue = deque([(product, 0, [product])])  # (current_metabolite, step_count, pathway)
    visited = set()

    while queue and len(pathway['steps']) == 0:
        current_metabolite, step_count, current_path = queue.popleft()

        if current_metabolite in visited or step_count >= max_steps:
            continue

        visited.add(current_metabolite)

        # Check if current metabolite is a starting material
        if current_metabolite.lower() in [sm.lower() for sm in starting_materials]:
            # Found a complete pathway
            pathway['steps'] = []
            for i in range(len(current_path) - 1):
                substrate = current_path[i + 1]
                product_step = current_path[i]
                enzymes = find_enzymes_for_transformation(substrate, product_step, limit=5)

                if enzymes:
                    pathway['steps'].append({
                        'step_number': i + 1,
                        'substrate': substrate,
                        'product': product_step,
                        'enzymes': enzymes,
                        'transformation': infer_transformation_type(substrate, product_step)
                    })
                else:
                    pathway['warnings'].append(f"No enzymes found for step: {substrate} -> {product_step}")

            pathway['confidence'] = 0.8  # High confidence for found pathway
            break

        # Try to find enzymes that produce current metabolite
        if step_count < max_steps:
            # Generate possible substrates (simplified - in practice you'd need metabolic knowledge)
            possible_substrates = []

            # Try common metabolic precursors
            common_precursors = ['glucose', 'pyruvate', 'acetate', 'ethanol', 'acetyl-CoA', 'oxaloacetate']
            for precursor in common_precursors:
                enzymes = find_enzymes_for_transformation(precursor, current_metabolite, limit=2)
                if enzymes:
                    possible_substrates.append(precursor)
                    pathway['alternative_pathways'].append({
                        'precursor': precursor,
                        'product': current_metabolite,
                        'enzymes': enzymes
                    })

            # Add found substrates to queue
            for substrate in possible_substrates:
                if substrate not in current_path:
                    new_path = [substrate] + current_path
                    queue.append((substrate, step_count + 1, new_path))

        time.sleep(0.2)  # Rate limiting

    # If no complete pathway found, create partial pathway
    if not pathway['steps'] and pathway['alternative_pathways']:
        # Create best guess pathway from alternatives
        best_alternative = max(pathway['alternative_pathways'],
                               key=lambda x: len(x.get('enzymes', [])))
        pathway['steps'] = [{
            'step_number': 1,
            'substrate': best_alternative['precursor'],
            'product': best_alternative['product'],
            'enzymes': best_alternative['enzymes'],
            'transformation': infer_transformation_type(best_alternative['precursor'], best_alternative['product'])
        }]
        pathway['confidence'] = 0.3  # Low confidence for partial pathway
        pathway['warnings'].append("Partial pathway only - complete synthesis route not found")

    elif not pathway['steps']:
        pathway['warnings'].append("No enzymatic pathway found for target product")
        pathway['confidence'] = 0.1

    return pathway


def build_retrosynthetic_tree(target: str, depth: int = 2) -> Dict[str, Any]:
    """Build a retrosynthetic tree for a target molecule."""
    validate_dependencies()

    tree = {
        'target': target,
        'depth': depth,
        'nodes': {target: {'level': 0, 'children': [], 'enzymes': []}},
        'edges': [],
        'alternative_routes': []
    }

    # Build tree recursively
    def build_node_recursive(metabolite: str, current_depth: int, parent: str = None) -> None:
        if current_depth >= depth:
            return

        # Find enzymes that can produce this metabolite
        potential_precursors = ['glucose', 'pyruvate', 'acetate', 'ethanol', 'acetyl-CoA',
                                'oxaloacetate', 'alpha-ketoglutarate', 'malate']

        for precursor in potential_precursors:
            enzymes = find_enzymes_for_transformation(precursor, metabolite, limit=3)

            if enzymes:
                # Add precursor as node if not exists
                if precursor not in tree['nodes']:
                    tree['nodes'][precursor] = {
                        'level': current_depth + 1,
                        'children': [],
                        'enzymes': enzymes
                    }
                    tree['nodes'][metabolite]['children'].append(precursor)
                    tree['edges'].append({
                        'from': precursor,
                        'to': metabolite,
                        'enzymes': enzymes,
                        'transformation': infer_transformation_type(precursor, metabolite)
                    })

                # Recursively build tree
                if current_depth + 1 < depth:
                    build_node_recursive(precursor, current_depth + 1, metabolite)

        # Try common metabolic transformations
        if current_depth < depth - 1:
            transformations = ['oxidation', 'reduction', 'hydrolysis', 'carboxylation', 'decarboxylation']
            for trans in transformations:
                try:
                    generic_enzymes = search_by_pattern(trans, limit=2)
                    if generic_enzymes:
                        # Create hypothetical precursor
                        hypothetical_precursor = f"precursor_{trans}_{metabolite}"
                        tree['nodes'][hypothetical_precursor] = {
                            'level': current_depth + 1,
                            'children': [],
                            'enzymes': generic_enzymes,
                            'hypothetical': True
                        }
                        tree['nodes'][metabolite]['children'].append(hypothetical_precursor)
                        tree['edges'].append({
                            'from': hypothetical_precursor,
                            'to': metabolite,
                            'enzymes': generic_enzymes,
                            'transformation': trans,
                            'hypothetical': True
                        })
                except Exception as e:
                    print(f"Error in retrosynthetic search for {trans}: {e}")

        time.sleep(0.3)  # Rate limiting

    # Start building from target
    build_node_recursive(target, 0)

    # Calculate tree statistics
    tree['total_nodes'] = len(tree['nodes'])
    tree['total_edges'] = len(tree['edges'])
    tree['max_depth'] = max(node['level'] for node in tree['nodes'].values()) if tree['nodes'] else 0

    return tree


def suggest_enzyme_substitutions(ec_number: str, criteria: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Suggest alternative enzymes with improved properties."""
    validate_dependencies()

    if criteria is None:
        criteria = {
            'min_temperature': 30,
            'max_temperature': 70,
            'min_ph': 6.0,
            'max_ph': 8.0,
            'min_thermostability': 40,
            'prefer_organisms': ['Escherichia coli', 'Saccharomyces cerevisiae', 'Bacillus subtilis']
        }

    substitutions = []

    # Get organisms for the target enzyme
    try:
        organisms = compare_across_organisms(ec_number, criteria['prefer_organisms'])
        time.sleep(0.5)
    except Exception as e:
        print(f"Error comparing organisms: {e}")
        organisms = []

    # Find thermophilic homologs if temperature is a criterion
    if criteria.get('min_thermostability'):
        try:
            thermophilic = find_thermophilic_homologs(ec_number, criteria['min_thermostability'])
            time.sleep(0.5)

            for enzyme in thermophilic:
                enzyme['substitution_reason'] = f"Thermostable (optimal temp: {enzyme['optimal_temperature']}°C)"
                enzyme['score'] = 8.0 if enzyme['optimal_temperature'] >= criteria['min_thermostability'] else 6.0
                substitutions.append(enzyme)
        except Exception as e:
            print(f"Error finding thermophilic homologs: {e}")

    # Find pH-stable variants
    if criteria.get('min_ph') or criteria.get('max_ph'):
        try:
            ph_stable = find_ph_stable_variants(ec_number, criteria.get('min_ph'), criteria.get('max_ph'))
            time.sleep(0.5)

            for enzyme in ph_stable:
                enzyme['substitution_reason'] = f"pH stable ({enzyme['stability_type']} range: {enzyme['ph_range']})"
                enzyme['score'] = 7.5
                substitutions.append(enzyme)
 

... [Content truncated, total 44,849 chars] ...