"""
Oracle ERP Tax Code Master Data
"""

from typing import Dict, Tuple

# Union Territory state codes (same as SAP)
UNION_TERRITORIES = {'04', '07', '25', '26', '31', '34', '35', '38'}

# Oracle Tax Code Mapping
# TODO: Implement Oracle-specific tax code nomenclature
# Oracle may use different naming conventions than SAP
ORACLE_TAX_CODE_MASTER: Dict[Tuple[str, str, str, str, str], str] = {
    # Example structure - to be populated based on Oracle configuration
    # ("5", "INTRA", "REGULAR", "CREDIT", "STATE"): "IN_CGST_SGST_5",
    # ("5", "INTER", "REGULAR", "CREDIT", "STATE"): "IN_IGST_5",
    
    # Placeholder - using similar structure to SAP
    ("5", "INTRA", "REGULAR", "CREDIT", "STATE"): "ORA_CGST_SGST_5",
    ("12", "INTRA", "REGULAR", "CREDIT", "STATE"): "ORA_CGST_SGST_12",
    ("18", "INTRA", "REGULAR", "CREDIT", "STATE"): "ORA_CGST_SGST_18",
    ("28", "INTRA", "REGULAR", "CREDIT", "STATE"): "ORA_CGST_SGST_28",
    
    ("5", "INTER", "REGULAR", "CREDIT", "STATE"): "ORA_IGST_5",
    ("12", "INTER", "REGULAR", "CREDIT", "STATE"): "ORA_IGST_12",
    ("18", "INTER", "REGULAR", "CREDIT", "STATE"): "ORA_IGST_18",
    ("28", "INTER", "REGULAR", "CREDIT", "STATE"): "ORA_IGST_28",
}

ORACLE_TAX_CODE_DESCRIPTIONS: Dict[str, str] = {
    "ORA_CGST_SGST_5": "Oracle CGST-SGST 5% Input",
    "ORA_CGST_SGST_12": "Oracle CGST-SGST 12% Input",
    "ORA_CGST_SGST_18": "Oracle CGST-SGST 18% Input",
    "ORA_CGST_SGST_28": "Oracle CGST-SGST 28% Input",
    "ORA_IGST_5": "Oracle IGST 5% Input",
    "ORA_IGST_12": "Oracle IGST 12% Input",
    "ORA_IGST_18": "Oracle IGST 18% Input",
    "ORA_IGST_28": "Oracle IGST 28% Input",
}
