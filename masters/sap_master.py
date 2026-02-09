"""
SAP ECC Tax Code Master Data
"""

from typing import Dict, Tuple

# Union Territory state codes
UNION_TERRITORIES = {'04', '07', '25', '26', '31', '34', '35', '38'}

# SAP ECC Tax Code Mapping
# Key: (tax_rate, transaction_type, charge_type, credit_type, state_type)
# Value: SAP tax code
SAP_TAX_CODE_MASTER: Dict[Tuple[str, str, str, str, str], str] = {
    # Standard GST - Intrastate CGST-SGST (Regular States)
    ("0.25", "INTRA", "REGULAR", "CREDIT", "STATE"): "3A",
    ("3", "INTRA", "REGULAR", "CREDIT", "STATE"): "3B",
    ("5", "INTRA", "REGULAR", "CREDIT", "STATE"): "3C",
    ("12", "INTRA", "REGULAR", "CREDIT", "STATE"): "3X",
    ("18", "INTRA", "REGULAR", "CREDIT", "STATE"): "3Z",
    ("28", "INTRA", "REGULAR", "CREDIT", "STATE"): "3Y",
    
    # Standard GST - Intrastate CGST-UGST (Union Territories)
    ("0.25", "INTRA", "REGULAR", "CREDIT", "UT"): "3A_UT",
    ("3", "INTRA", "REGULAR", "CREDIT", "UT"): "3B_UT",
    ("5", "INTRA", "REGULAR", "CREDIT", "UT"): "3C_UT",
    ("12", "INTRA", "REGULAR", "CREDIT", "UT"): "3X_UT",
    ("18", "INTRA", "REGULAR", "CREDIT", "UT"): "3Z_UT",
    ("28", "INTRA", "REGULAR", "CREDIT", "UT"): "3Y_UT",
    
    # Standard GST - Interstate IGST
    ("0.25", "INTER", "REGULAR", "CREDIT", "STATE"): "1A",
    ("0.25", "INTER", "REGULAR", "CREDIT", "UT"): "1A",  # Same for UT
    ("3", "INTER", "REGULAR", "CREDIT", "STATE"): "1B",
    ("3", "INTER", "REGULAR", "CREDIT", "UT"): "1B",
    ("5", "INTER", "REGULAR", "CREDIT", "STATE"): "1C",
    ("5", "INTER", "REGULAR", "CREDIT", "UT"): "1C",
    ("12", "INTER", "REGULAR", "CREDIT", "STATE"): "1X",
    ("12", "INTER", "REGULAR", "CREDIT", "UT"): "1X",
    ("18", "INTER", "REGULAR", "CREDIT", "STATE"): "1Z",
    ("18", "INTER", "REGULAR", "CREDIT", "UT"): "1Z",
    ("28", "INTER", "REGULAR", "CREDIT", "STATE"): "1Y",
    ("28", "INTER", "REGULAR", "CREDIT", "UT"): "1Y",
    
    # Non-Credit scenarios - Intrastate
    ("5", "INTRA", "REGULAR", "NON_CREDIT", "STATE"): "3C_NC",
    ("5", "INTRA", "REGULAR", "NON_CREDIT", "UT"): "3C_UT_NC",
    ("12", "INTRA", "REGULAR", "NON_CREDIT", "STATE"): "3X_NC",
    ("12", "INTRA", "REGULAR", "NON_CREDIT", "UT"): "3X_UT_NC",
    ("18", "INTRA", "REGULAR", "NON_CREDIT", "STATE"): "3Z_NC",
    ("18", "INTRA", "REGULAR", "NON_CREDIT", "UT"): "3Z_UT_NC",
    ("28", "INTRA", "REGULAR", "NON_CREDIT", "STATE"): "3Y_NC",
    ("28", "INTRA", "REGULAR", "NON_CREDIT", "UT"): "3Y_UT_NC",
    
    # Non-Credit scenarios - Interstate
    ("5", "INTER", "REGULAR", "NON_CREDIT", "STATE"): "1C_NC",
    ("5", "INTER", "REGULAR", "NON_CREDIT", "UT"): "1C_NC",
    ("12", "INTER", "REGULAR", "NON_CREDIT", "STATE"): "1X_NC",
    ("12", "INTER", "REGULAR", "NON_CREDIT", "UT"): "1X_NC",
    ("18", "INTER", "REGULAR", "NON_CREDIT", "STATE"): "1Z_NC",
    ("18", "INTER", "REGULAR", "NON_CREDIT", "UT"): "1Z_NC",
    ("28", "INTER", "REGULAR", "NON_CREDIT", "STATE"): "1Y_NC",
    ("28", "INTER", "REGULAR", "NON_CREDIT", "UT"): "1Y_NC",
    
    # RCM scenarios - Intrastate
    ("5", "INTRA", "RCM", "CREDIT", "STATE"): "R3",
    ("5", "INTRA", "RCM", "CREDIT", "UT"): "R3_UT",
    ("12", "INTRA", "RCM", "CREDIT", "STATE"): "R6",
    ("12", "INTRA", "RCM", "CREDIT", "UT"): "R6_UT",
    ("18", "INTRA", "RCM", "CREDIT", "STATE"): "R9",
    ("18", "INTRA", "RCM", "CREDIT", "UT"): "R9_UT",
    ("28", "INTRA", "RCM", "CREDIT", "STATE"): "R12",
    ("28", "INTRA", "RCM", "CREDIT", "UT"): "R12_UT",
    
    # RCM scenarios - Interstate
    ("5", "INTER", "RCM", "CREDIT", "STATE"): "R1",
    ("5", "INTER", "RCM", "CREDIT", "UT"): "R1",
    ("12", "INTER", "RCM", "CREDIT", "STATE"): "R4",
    ("12", "INTER", "RCM", "CREDIT", "UT"): "R4",
    ("18", "INTER", "RCM", "CREDIT", "STATE"): "R7",
    ("18", "INTER", "RCM", "CREDIT", "UT"): "R7",
    ("28", "INTER", "RCM", "CREDIT", "STATE"): "R10",
    ("28", "INTER", "RCM", "CREDIT", "UT"): "R10",
    
    # RCM Non-Credit - Intrastate
    ("5", "INTRA", "RCM", "NON_CREDIT", "STATE"): "R3_NC",
    ("5", "INTRA", "RCM", "NON_CREDIT", "UT"): "R3_UT_NC",
    ("12", "INTRA", "RCM", "NON_CREDIT", "STATE"): "R6_NC",
    ("12", "INTRA", "RCM", "NON_CREDIT", "UT"): "R6_UT_NC",
    ("18", "INTRA", "RCM", "NON_CREDIT", "STATE"): "R9_NC",
    ("18", "INTRA", "RCM", "NON_CREDIT", "UT"): "R9_UT_NC",
    ("28", "INTRA", "RCM", "NON_CREDIT", "STATE"): "R12_NC",
    ("28", "INTRA", "RCM", "NON_CREDIT", "UT"): "R12_UT_NC",
    
    # RCM Non-Credit - Interstate
    ("5", "INTER", "RCM", "NON_CREDIT", "STATE"): "R1_NC",
    ("5", "INTER", "RCM", "NON_CREDIT", "UT"): "R1_NC",
    ("12", "INTER", "RCM", "NON_CREDIT", "STATE"): "R4_NC",
    ("12", "INTER", "RCM", "NON_CREDIT", "UT"): "R4_NC",
    ("18", "INTER", "RCM", "NON_CREDIT", "STATE"): "R7_NC",
    ("18", "INTER", "RCM", "NON_CREDIT", "UT"): "R7_NC",
    ("28", "INTER", "RCM", "NON_CREDIT", "STATE"): "R10_NC",
    ("28", "INTER", "RCM", "NON_CREDIT", "UT"): "R10_NC",
    
    # Zero rated / Exempt
    ("0", "INTRA", "REGULAR", "CREDIT", "STATE"): "Z0",
    ("0", "INTRA", "REGULAR", "CREDIT", "UT"): "Z0",
    ("0", "INTER", "REGULAR", "CREDIT", "STATE"): "Z0",
    ("0", "INTER", "REGULAR", "CREDIT", "UT"): "Z0",
}


# Tax code descriptions for better reporting
SAP_TAX_CODE_DESCRIPTIONS: Dict[str, str] = {
    "3A": "CGST-SGST 0.25% Input",
    "3B": "CGST-SGST 3% Input",
    "3C": "CGST-SGST 5% Input",
    "3X": "CGST-SGST 12% Input",
    "3Z": "CGST-SGST 18% Input",
    "3Y": "CGST-SGST 28% Input",
    
    "3A_UT": "CGST-UGST 0.25% Input",
    "3B_UT": "CGST-UGST 3% Input",
    "3C_UT": "CGST-UGST 5% Input",
    "3X_UT": "CGST-UGST 12% Input",
    "3Z_UT": "CGST-UGST 18% Input",
    "3Y_UT": "CGST-UGST 28% Input",
    
    "1A": "IGST 0.25% Input",
    "1B": "IGST 3% Input",
    "1C": "IGST 5% Input",
    "1X": "IGST 12% Input",
    "1Z": "IGST 18% Input",
    "1Y": "IGST 28% Input",
    
    "3C_NC": "CGST-SGST 5% Non-Credit",
    "3X_NC": "CGST-SGST 12% Non-Credit",
    "3Z_NC": "CGST-SGST 18% Non-Credit",
    "3Y_NC": "CGST-SGST 28% Non-Credit",
    
    "R3": "RCM CGST-SGST 5% Input",
    "R6": "RCM CGST-SGST 12% Input",
    "R9": "RCM CGST-SGST 18% Input",
    "R12": "RCM CGST-SGST 28% Input",
    
    "R1": "RCM IGST 5% Input",
    "R4": "RCM IGST 12% Input",
    "R7": "RCM IGST 18% Input",
    "R10": "RCM IGST 28% Input",
    
    "Z0": "Input Tax Exempt / Zero Rated",
}
