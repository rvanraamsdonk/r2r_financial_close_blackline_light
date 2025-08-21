"""
Smart ML-based transaction matching algorithm with pattern recognition.
"""
from __future__ import annotations
from ..state import CloseState, Match
from ..console import Console
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import re

def node_smart_match(state: CloseState, *, console: Console) -> CloseState:
    """Enhanced transaction matching with ML-based algorithms."""
    console.banner("Smart Transaction Matching")
    
    data = state.get("data", {})
    period = state["period"]
    matches = []
    
    if not data or "ar" not in data or "bank" not in data:
        return {"matches": matches}
    
    ar = data["ar"][data["ar"].period == period].copy()
    bank = data["bank"][data["bank"].period == period].copy()
    
    if ar.empty or bank.empty:
        return {"matches": matches}
    
    # Multi-stage matching algorithm
    matches.extend(exact_amount_matching(ar, bank, console))
    matches.extend(fuzzy_amount_matching(ar, bank, console))
    matches.extend(pattern_based_matching(ar, bank, console))
    matches.extend(ml_similarity_matching(ar, bank, console))
    
    console.line("smart_matching", "Complete", "success", auto=True,
                details=f"Total matches found: {len(matches)}")
    
    return {"matches": matches}

def exact_amount_matching(ar: pd.DataFrame, bank: pd.DataFrame, console: Console) -> List[Match]:
    """Stage 1: Exact amount matching with date tolerance."""
    matches = []
    
    for _, ar_row in ar.iterrows():
        # Look for exact amount matches within date tolerance
        amount_matches = bank[
            (abs(bank['amount'] - ar_row['amount']) < 0.01) &
            (bank['entity'] == ar_row['entity'])
        ]
        
        if not amount_matches.empty:
            # Find best date match within tolerance
            ar_date = pd.to_datetime(ar_row['invoice_date'])
            
            for _, bank_row in amount_matches.iterrows():
                bank_date = pd.to_datetime(bank_row['date'])
                date_diff = abs((bank_date - ar_date).days)
                
                if date_diff <= 45:  # 45-day tolerance
                    confidence = calculate_match_confidence(ar_row, bank_row, "exact_amount")
                    
                    match = Match(
                        id=f"MATCH-{ar_row['invoice_id']}-{bank_row['bank_txn_id']}",
                        ar_id=ar_row['invoice_id'],
                        bank_id=bank_row['bank_txn_id'],
                        amount=ar_row['amount'],
                        match_type="exact_amount",
                        confidence=confidence,
                        date_diff=date_diff
                    )
                    matches.append(match)
                    
                    console.line("smart_matching", "Exact", "matched", auto=True,
                               details=f"{ar_row['entity']} ${ar_row['amount']:,.0f} confidence={confidence:.2f}")
                    break  # Take first/best match
    
    return matches

def fuzzy_amount_matching(ar: pd.DataFrame, bank: pd.DataFrame, console: Console) -> List[Match]:
    """Stage 2: Fuzzy amount matching for partial payments or fees."""
    matches = []
    tolerance_pct = 0.05  # 5% tolerance
    
    # Get unmatched AR items (simplified - in production would track matched items)
    for _, ar_row in ar.iterrows():
        # Look for amounts within tolerance percentage
        amount_min = ar_row['amount'] * (1 - tolerance_pct)
        amount_max = ar_row['amount'] * (1 + tolerance_pct)
        
        fuzzy_matches = bank[
            (bank['amount'] >= amount_min) &
            (bank['amount'] <= amount_max) &
            (bank['entity'] == ar_row['entity'])
        ]
        
        if not fuzzy_matches.empty:
            for _, bank_row in fuzzy_matches.iterrows():
                ar_date = pd.to_datetime(ar_row['invoice_date'])
                bank_date = pd.to_datetime(bank_row['date'])
                date_diff = abs((bank_date - ar_date).days)
                
                if date_diff <= 60:  # Longer tolerance for fuzzy matches
                    confidence = calculate_match_confidence(ar_row, bank_row, "fuzzy_amount")
                    
                    match = Match(
                        id=f"MATCH-{ar_row['invoice_id']}-{bank_row['bank_txn_id']}",
                        ar_id=ar_row['invoice_id'],
                        bank_id=bank_row['bank_txn_id'],
                        amount=bank_row['amount'],  # Use actual bank amount
                        match_type="fuzzy_amount",
                        confidence=confidence,
                        date_diff=date_diff
                    )
                    matches.append(match)
                    
                    console.line("smart_matching", "Fuzzy", "matched", auto=True,
                               details=f"{ar_row['entity']} ${bank_row['amount']:,.0f} confidence={confidence:.2f}")
                    break
    
    return matches

def pattern_based_matching(ar: pd.DataFrame, bank: pd.DataFrame, console: Console) -> List[Match]:
    """Stage 3: Pattern-based matching using customer names and references."""
    matches = []
    
    for _, ar_row in ar.iterrows():
        customer_name = ar_row.get('customer_name', '').upper()
        if not customer_name:
            continue
        
        # Extract key words from customer name for matching
        customer_keywords = extract_keywords(customer_name)
        
        for _, bank_row in bank.iterrows():
            if bank_row['entity'] != ar_row['entity']:
                continue
            
            # Check description and counterparty fields
            bank_desc = str(bank_row.get('description', '')).upper()
            bank_counterparty = str(bank_row.get('counterparty', '')).upper()
            
            # Calculate text similarity
            desc_similarity = calculate_text_similarity(customer_keywords, bank_desc)
            counterparty_similarity = calculate_text_similarity(customer_keywords, bank_counterparty)
            
            max_similarity = max(desc_similarity, counterparty_similarity)
            
            if max_similarity > 0.7:  # 70% similarity threshold
                ar_date = pd.to_datetime(ar_row['invoice_date'])
                bank_date = pd.to_datetime(bank_row['date'])
                date_diff = abs((bank_date - ar_date).days)
                
                if date_diff <= 90:  # Extended tolerance for pattern matches
                    confidence = calculate_match_confidence(ar_row, bank_row, "pattern_based")
                    confidence *= max_similarity  # Adjust by text similarity
                    
                    match = Match(
                        id=f"MATCH-{ar_row['invoice_id']}-{bank_row['bank_txn_id']}",
                        ar_id=ar_row['invoice_id'],
                        bank_id=bank_row['bank_txn_id'],
                        amount=bank_row['amount'],
                        match_type="pattern_based",
                        confidence=confidence,
                        date_diff=date_diff
                    )
                    matches.append(match)
                    
                    console.line("smart_matching", "Pattern", "matched", auto=True,
                               details=f"{ar_row['entity']} {customer_name[:20]} confidence={confidence:.2f}")
                    break
    
    return matches

def ml_similarity_matching(ar: pd.DataFrame, bank: pd.DataFrame, console: Console) -> List[Match]:
    """Stage 4: ML-based similarity matching using multiple features."""
    matches = []
    
    # Feature engineering for ML matching
    for _, ar_row in ar.iterrows():
        best_match = None
        best_score = 0.0
        
        for _, bank_row in bank.iterrows():
            if bank_row['entity'] != ar_row['entity']:
                continue
            
            # Calculate composite similarity score
            features = calculate_ml_features(ar_row, bank_row)
            similarity_score = calculate_composite_score(features)
            
            if similarity_score > best_score and similarity_score > 0.6:  # 60% threshold
                best_score = similarity_score
                best_match = bank_row
        
        if best_match is not None:
            ar_date = pd.to_datetime(ar_row['invoice_date'])
            bank_date = pd.to_datetime(best_match['date'])
            date_diff = abs((bank_date - ar_date).days)
            
            confidence = best_score * 0.9  # Slightly conservative for ML matches
            
            match = Match(
                id=f"MATCH-{ar_row['invoice_id']}-{best_match['bank_txn_id']}",
                ar_id=ar_row['invoice_id'],
                bank_id=best_match['bank_txn_id'],
                amount=best_match['amount'],
                match_type="ml_similarity",
                confidence=confidence,
                date_diff=date_diff
            )
            matches.append(match)
            
            console.line("smart_matching", "ML", "matched", ai=True,
                        details=f"{ar_row['entity']} ML_score={best_score:.2f}")
    
    return matches

def calculate_match_confidence(ar_row, bank_row, match_type: str) -> float:
    """Calculate confidence score for a match."""
    confidence = 0.5  # Base confidence
    
    # Amount similarity
    amount_diff = abs(ar_row['amount'] - bank_row['amount']) / ar_row['amount']
    if amount_diff < 0.01:  # Within 1%
        confidence += 0.3
    elif amount_diff < 0.05:  # Within 5%
        confidence += 0.2
    elif amount_diff < 0.1:  # Within 10%
        confidence += 0.1
    
    # Date proximity
    ar_date = pd.to_datetime(ar_row['invoice_date'])
    bank_date = pd.to_datetime(bank_row['date'])
    date_diff = abs((bank_date - ar_date).days)
    
    if date_diff <= 7:
        confidence += 0.2
    elif date_diff <= 30:
        confidence += 0.1
    elif date_diff <= 60:
        confidence += 0.05
    
    # Match type adjustment
    type_adjustments = {
        "exact_amount": 0.0,
        "fuzzy_amount": -0.1,
        "pattern_based": -0.05,
        "ml_similarity": -0.15
    }
    confidence += type_adjustments.get(match_type, 0)
    
    return min(max(confidence, 0.1), 0.95)  # Clamp between 10% and 95%

def extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text for matching."""
    # Remove common words and extract meaningful terms
    stop_words = {'INC', 'LLC', 'CORP', 'LTD', 'CO', 'THE', 'AND', 'OF'}
    words = re.findall(r'\b[A-Z]{2,}\b', text)
    return [word for word in words if word not in stop_words and len(word) >= 3]

def calculate_text_similarity(keywords: List[str], text: str) -> float:
    """Calculate similarity between keywords and text."""
    if not keywords or not text:
        return 0.0
    
    matches = sum(1 for keyword in keywords if keyword in text)
    return matches / len(keywords)

def calculate_ml_features(ar_row, bank_row) -> Dict[str, float]:
    """Calculate ML features for similarity scoring."""
    features = {}
    
    # Amount similarity (normalized)
    amount_ratio = min(ar_row['amount'], bank_row['amount']) / max(ar_row['amount'], bank_row['amount'])
    features['amount_similarity'] = amount_ratio
    
    # Date proximity (normalized to 0-1, where 1 is same day)
    ar_date = pd.to_datetime(ar_row['invoice_date'])
    bank_date = pd.to_datetime(bank_row['date'])
    date_diff = abs((bank_date - ar_date).days)
    features['date_proximity'] = max(0, 1 - (date_diff / 90))  # 90-day window
    
    # Text similarity
    customer_name = ar_row.get('customer_name', '').upper()
    bank_desc = str(bank_row.get('description', '')).upper()
    bank_counterparty = str(bank_row.get('counterparty', '')).upper()
    
    if customer_name:
        keywords = extract_keywords(customer_name)
        desc_sim = calculate_text_similarity(keywords, bank_desc)
        counterparty_sim = calculate_text_similarity(keywords, bank_counterparty)
        features['text_similarity'] = max(desc_sim, counterparty_sim)
    else:
        features['text_similarity'] = 0.0
    
    # Amount magnitude (larger amounts get slight boost)
    features['amount_magnitude'] = min(1.0, ar_row['amount'] / 100000)  # Normalize to $100K
    
    return features

def calculate_composite_score(features: Dict[str, float]) -> float:
    """Calculate weighted composite similarity score."""
    weights = {
        'amount_similarity': 0.4,
        'date_proximity': 0.3,
        'text_similarity': 0.2,
        'amount_magnitude': 0.1
    }
    
    score = sum(features.get(key, 0) * weight for key, weight in weights.items())
    return min(score, 1.0)
