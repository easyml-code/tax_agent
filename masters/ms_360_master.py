"""
Microsoft Dynamics 365 Tax Code Master Data
"""

from typing import Dict, Tuple

# Union Territory state codes (same as SAP)
UNION_TERRITORIES = {'04', '07', '25', '26', '31', '34', '35', '38'}

# MS 365 Tax Code Mapping
# TODO: Implement MS Dynamics 365-specific tax code nomenclature
MS360_TAX_CODE_MASTER: Dict[Tuple[str, str, str, str, str], str] = {
    # Example structure - to be populated based on MS 365 configuration
    # Placeholder - using similar structure to SAP
    ("5", "INTRA", "REGULAR", "CREDIT", "STATE"): "MS_IN_CGST_SGST_5",
    ("12", "INTRA", "REGULAR", "CREDIT", "STATE"): "MS_IN_CGST_SGST_12",
    ("18", "INTRA", "REGULAR", "CREDIT", "STATE"): "MS_IN_CGST_SGST_18",
    ("28", "INTRA", "REGULAR", "CREDIT", "STATE"): "MS_IN_CGST_SGST_28",
    
    ("5", "INTER", "REGULAR", "CREDIT", "STATE"): "MS_IN_IGST_5",
    ("12", "INTER", "REGULAR", "CREDIT", "STATE"): "MS_IN_IGST_12",
    ("18", "INTER", "REGULAR", "CREDIT", "STATE"): "MS_IN_IGST_18",
    ("28", "INTER", "REGULAR", "CREDIT", "STATE"): "MS_IN_IGST_28",
}

MS360_TAX_CODE_DESCRIPTIONS: Dict[str, str] = {
    "MS_IN_CGST_SGST_5": "MS 365 CGST-SGST 5% Input",
    "MS_IN_CGST_SGST_12": "MS 365 CGST-SGST 12% Input",
    "MS_IN_CGST_SGST_18": "MS 365 CGST-SGST 18% Input",
    "MS_IN_CGST_SGST_28": "MS 365 CGST-SGST 28% Input",
    "MS_IN_IGST_5": "MS 365 IGST 5% Input",
    "MS_IN_IGST_12": "MS 365 IGST 12% Input",
    "MS_IN_IGST_18": "MS 365 IGST 18% Input",
    "MS_IN_IGST_28": "MS 365 IGST 28% Input",
}
