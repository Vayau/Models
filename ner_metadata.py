import spacy
from spacy.matcher import Matcher
import re

nlp = spacy.load("en_core_web_trf")
matcher = Matcher(nlp.vocab)

# HR Patterns
matcher.add("RECRUITMENT_ADV_NO", [[{"TEXT": {"REGEX": r"HR/\d{4}/\d+"}}]])
matcher.add("GRADE_PAY", [[{"TEXT": {"REGEX": r"Grade\s?[A-Z0-9]+"}}]])
matcher.add("JOB_TITLE", [[{"LOWER": {"IN": ["engineer", "manager", "officer", "assistant"]}}]])

# Procurement Patterns
matcher.add("TENDER_ID", [[{"TEXT": {"REGEX": r"Tender\s?No\.\s?\d+/\d+"}}]])
matcher.add("PURCHASE_ORDER_NO", [[{"TEXT": {"REGEX": r"PO\s?\d{3,}"}}]])
matcher.add("CONTRACT_ID", [[{"TEXT": {"REGEX": r"Contract\s?No\.\s?\w+"}}]])

# Legal Patterns
matcher.add("CASE_NO", [[{"TEXT": {"REGEX": r"(W\.P\.|C\.R\.|O\.S\.)\s?\d+/\d+"}}]])
matcher.add("COURT_NAME", [[{"LOWER": {"IN": ["supreme", "high", "district", "tribunal"]}}]])
matcher.add("LAW_SECTION", [[{"TEXT": {"REGEX": r"(Section|Article)\s?\d+[A-Za-z]?"}}]])

def extract_metadata(text):
    doc = nlp(text)
    matches = matcher(doc)
    metadata = {
        "general": {"PERSON": [], "ORG": [], "DATE": [], "AMOUNT": [], "LOCATION": []},
        "HR": {"EMPLOYEE_ID": [], "JOB_TITLE": [], "GRADE_PAY": [], "RECRUITMENT_ADV_NO": []},
        "Procurement": {"TENDER_ID": [], "PURCHASE_ORDER_NO": [], "BIDDER_NAME": [], "CONTRACT_ID": [], "ITEM_SERVICE": [], "DEADLINE": []},
        "Legal": {"CASE_NO": [], "COURT_NAME": [], "LAW_SECTION": [], "PARTY_NAME": [], "SOP_CLAUSE": []}
    }

    for ent in doc.ents:
        if ent.label_ in metadata["general"]:
            metadata["general"][ent.label_].append(ent.text)

    for match_id, start, end in matches:
        label = nlp.vocab.strings[match_id]
        span = doc[start:end].text
        for dept in metadata:
            if label in metadata[dept]:
                metadata[dept][label].append(span)
    
    return metadata

def classify_department_with_confidence(metadata, full_text=""):
    scores = {
        "HR": 0.0,
        "Procurement": 0.0,
        "Legal": 0.0,
        "Finance": 0.0,
        "Engineering": 0.0,
        "Regulatory": 0.0
    }

    # HR Scoring
    if metadata["HR"]["RECRUITMENT_ADV_NO"]:
        scores["HR"] += 0.4
    if metadata["HR"]["JOB_TITLE"]:
        scores["HR"] += 0.3
    if metadata["HR"]["GRADE_PAY"]:
        scores["HR"] += 0.3

    # Procurement Scoring
    if metadata["Procurement"]["TENDER_ID"]:
        scores["Procurement"] += 0.4
    if metadata["Procurement"]["PURCHASE_ORDER_NO"]:
        scores["Procurement"] += 0.3
    if metadata["Procurement"]["CONTRACT_ID"]:
        scores["Procurement"] += 0.3
    if metadata["Procurement"]["ITEM_SERVICE"]:
        scores["Procurement"] += 0.2

    # Legal Scoring
    if metadata["Legal"]["CASE_NO"]:
        scores["Legal"] += 0.4
    if metadata["Legal"]["COURT_NAME"]:
        scores["Legal"] += 0.3
    if metadata["Legal"]["LAW_SECTION"]:
        scores["Legal"] += 0.3
    if metadata["Legal"]["PARTY_NAME"]:
        scores["Legal"] += 0.2
    
    text = full_text.lower()
    if "tax" in text:
        scores["Finance"] += 0.6
    if "annual report" in text:
        scores["Finance"] += 0.5
    if "safety" in text or "directive" in text or "eia" in text:
        scores["Regulatory"] += 0.6
    if "rolling stock" in text or "maximo" in text:
        scores["Engineering"] += 0.7
    if "report" in text:
        scores["Engineering"] += 0.3
    
    max_score = max(scores.values())
    if max_score > 0:
        for dept in scores:
            scores[dept] = round(scores[dept] / max_score, 2)

    predicted = {dept: score for dept, score in scores.items() if score > 0} #only keep depts with >0
    return predicted


sample_text = """
Applications are invited for the post of Assistant Engineer in Pay Band-3 
with Grade A under Advertisement No. HR/2024/05. 
Sealed bids are invited under Tender No. 05/2024 for supply of Locomotive Spare Parts. 
In the matter of Case No. W.P. 123/2024 before the Supreme Court of India, 
between ABC Ltd. and XYZ Corp. under Section 138 of the Negotiable Instruments Act.
"""

metadata = extract_metadata(sample_text)
predicted = classify_department_with_confidence(metadata, full_text=sample_text)

print("Predicted Departments with Confidence:", predicted)