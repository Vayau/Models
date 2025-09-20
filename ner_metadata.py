import spacy
from spacy.matcher import Matcher
import re
import pdfplumber
from collections import defaultdict

nlp = spacy.load("en_core_web_trf")
matcher = Matcher(nlp.vocab)

# HR Patterns
matcher.add("RECRUITMENT_ADV_NO", [[{"TEXT": {"REGEX": r"HR/\d{4}/\d+"}}]])
matcher.add("GRADE_PAY", [[{"TEXT": {"REGEX": r"Grade\s?[A-Z0-9]+"}}]])
matcher.add("JOB_TITLE", [[{"LOWER": {"IN": ["engineer", "manager", "officer", "assistant"]}}]])

# Procurement Patterns
matcher.add("TENDER_ID", [[{"TEXT": {"REGEX": r"(Tender\s?No\.|Tender\s?No)\s?[:\-]?\s?\d+[/\-\w]*"}}]])
matcher.add("PURCHASE_ORDER_NO", [[{"TEXT": {"REGEX": r"\bP\.?O\.?\s?\d{2,}|\bPurchase Order No\.?\b"}}]])
matcher.add("CONTRACT_ID", [[{"TEXT": {"REGEX": r"(Contract\s?No\.?|Contract\s?ID)\s?[:\-]?\s?[\w\-\/]+"}}]])

# Legal Patterns
matcher.add("CASE_NO", [[{"TEXT": {"REGEX": r"\b(?:W\.P\.|WPC|C\.R\.|O\.S\.|C\.A\.)\s?\d+[/\-\w]*\b"}}]])
matcher.add("COURT_NAME", [[{"LOWER": {"IN": ["supreme", "high", "district", "tribunal", "court"]}}]])
matcher.add("LAW_SECTION", [[{"TEXT": {"REGEX": r"\b(?:Section|Article)\s?\d+[A-Za-z]?\b"}}]])

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

def classify_department_improved(metadata, full_text="", debug=False):
    text = (full_text or "").lower()
    raw = defaultdict(float)
    reasons = defaultdict(list)

    #Procurement
    proc_matches = (
        len(metadata["Procurement"]["TENDER_ID"])
        + len(metadata["Procurement"]["PURCHASE_ORDER_NO"])
        + len(metadata["Procurement"]["CONTRACT_ID"])
    )
    procurement_phrases = [
        "tender document", "notice inviting tender", "form of tender",
        "bill of quantities", "tender security", "tenderer", "earnest money",
        "emd", "bid", "bidder", "purchase order", "contract no",
        "evaluation of tender", "tender opening", "tender validity"
    ]
    proc_kw_hits = sum(1 for kw in procurement_phrases if kw in text)

    if proc_matches:
        raw["Procurement"] += proc_matches * 3.0
        reasons["Procurement"].append(f"explicit_proc_matches={proc_matches}")
    if proc_kw_hits:
        raw["Procurement"] += proc_kw_hits * 1.2
        reasons["Procurement"].append(f"procurement_phrase_hits={proc_kw_hits}")
    if any(k in text for k in ["notice inviting tender", "form of tender", "bill of quantities"]):
        raw["Procurement"] += 3.0
        reasons["Procurement"].append("strong_proc_indicator_phrase")

    #HR
    if metadata["HR"]["RECRUITMENT_ADV_NO"]:
        raw["HR"] += 3.0
        reasons["HR"].append("RECRUITMENT_ADV_NO")
    if metadata["HR"]["JOB_TITLE"]:
        raw["HR"] += len(metadata["HR"]["JOB_TITLE"]) * 1.0
        reasons["HR"].append("JOB_TITLE_found")
    if metadata["HR"]["GRADE_PAY"]:
        raw["HR"] += 1.0
        reasons["HR"].append("GRADE_PAY_found")

    #Legal
    if metadata["Legal"]["CASE_NO"]:
        raw["Legal"] += len(metadata["Legal"]["CASE_NO"]) * 3.0
        reasons["Legal"].append("CASE_NO_found")
    if metadata["Legal"]["COURT_NAME"]:
        raw["Legal"] += len(metadata["Legal"]["COURT_NAME"]) * 0.8
        reasons["Legal"].append("COURT_NAME_found")
    if metadata["Legal"]["LAW_SECTION"]:
        raw["Legal"] += len(metadata["Legal"]["LAW_SECTION"]) * 0.6
        reasons["Legal"].append("LAW_SECTION_found")

    legal_phrases = ["petitioner", "respondent", "writ petition", "tribunal order", "appeal", "arbitration clause"]
    legal_phrase_hits = sum(1 for k in legal_phrases if k in text)
    if legal_phrase_hits:
        raw["Legal"] += legal_phrase_hits * 0.8
        reasons["Legal"].append(f"legal_phrase_hits={legal_phrase_hits}")

    #Finance
    if "tax reimbursement" in text or "tax return" in text or "tax refund" in text:
        raw["Finance"] += 3.0
        reasons["Finance"].append("tax_term_found")
    if "annual report" in text or "balance sheet" in text or "audited" in text:
        raw["Finance"] += 2.0
        reasons["Finance"].append("financial_statement_found")
    if "invoice" in text:
        raw["Finance"] += 1.5
        reasons["Finance"].append("invoice_found")
    if "profit and loss" in text or "p&l account" in text:
        raw["Finance"] += 2.0
        reasons["Finance"].append("p&l_found")
    if "budget estimate" in text or "expenditure report" in text:
        raw["Finance"] += 1.5
        reasons["Finance"].append("budget_terms_found")

    #Regulatory
    if "eia" in text or "environmental impact" in text or "environmental clearance" in text:
        raw["Regulatory"] += 3.0
        reasons["Regulatory"].append("environmental_found")
    if "safety directive" in text or "safety norms" in text:
        raw["Regulatory"] += 1.5
        reasons["Regulatory"].append("safety_directive_found")
    if "compliance order" in text or "regulatory directive" in text:
        raw["Regulatory"] += 2.0
        reasons["Regulatory"].append("regulatory_directive_found")

    #Engineering
    if "rolling stock" in text or "maximo" in text:
        raw["Engineering"] += 3.0
        reasons["Engineering"].append("rolling_stock_or_maximo")
    if "technical specification" in text or "engineering report" in text:
        raw["Engineering"] += 1.5
        reasons["Engineering"].append("technical_terms_found")

    #Dominance or Suppression Logic
    if raw["Procurement"] >= 3.0:
        raw["Procurement"] += 3.0
        reasons["Procurement"].append("procurement_strong_flag")
        for dept in ["Legal", "Finance", "Regulatory", "Engineering", "HR"]:
            if raw[dept] < 3.0:
                raw[dept] *= 0.35
                reasons[dept].append("suppressed_by_procurement")

    if raw["Finance"] >= 3.0:
        raw["Finance"] += 3.0
        reasons["Finance"].append("finance_strong_flag")
        for dept in ["Legal", "Procurement", "Regulatory", "Engineering", "HR"]:
            if raw[dept] < 3.0:
                raw[dept] *= 0.35
                reasons[dept].append("suppressed_by_finance")

    if raw["Legal"] >= 3.0:
        raw["Legal"] += 3.0
        reasons["Legal"].append("legal_strong_flag")
        for dept in ["Finance", "Procurement", "Regulatory", "Engineering", "HR"]:
            if raw[dept] < 3.0:
                raw[dept] *= 0.35
                reasons[dept].append("suppressed_by_legal")

    max_raw = max(raw.values()) if raw else 1.0
    normalized = {dept: round(val / max_raw, 2) for dept, val in raw.items()}

    predicted_departments = [dept for dept, score in normalized.items() if score >= 0.5]

    if debug:
        return normalized, dict(reasons), predicted_departments
    return normalized, predicted_departments

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def process_pdf_improved(pdf_path, debug=False):
    full_text = extract_text_from_pdf(pdf_path)
    metadata = extract_metadata(full_text)
    if debug:
        scores, reasons, depts = classify_department_improved(metadata, full_text=full_text, debug=True)
        return {"file": pdf_path, "metadata": metadata, "scores": scores, "reasons": reasons, "predicted_departments": depts}
    else:
        scores, depts = classify_department_improved(metadata, full_text=full_text, debug=False)
        return {"file": pdf_path, "metadata": metadata, "scores": scores, "predicted_departments": depts}

if __name__ == "__main__":
    pdf_file = "Kochi_Metro_Rail_Ltd_vs_Union_Of_India.PDF"
    result = process_pdf_improved(pdf_file, debug=True)
    print("Scores:")
    for dept, s in result["scores"].items():
        print(f"  {dept}: {s}")
    print("\nTop reasons (debug):")
    for dept, r in result["reasons"].items():
        print(f"  {dept}: {r}")
    print("\nPredicted Departments:", result["predicted_departments"])
