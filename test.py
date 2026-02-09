"""
Example usage of tax agent
"""

import asyncio
from tax_agent.tax_agent import get_tax_agent, TaggingRequest, TaggingRequestLineItem


async def main():
    # Create sample request
    request = TaggingRequest(
        lines=[
            TaggingRequestLineItem(
                item_description="Professional consulting services",
                hsn=998314,
                supplier_name="ABC Consultants Pvt Ltd",
                po_number="PO-2024-001",
                quantity=1,
                unit_price=100000.0,
                total=118000.0,
                supplier_gstin="27AABCU9603R1ZM",  # Maharashtra
                supplier_country="IN",
                buyer_gstin="27AADCB2501D1ZF",  # Maharashtra
                buyer_country="IN",
                tax=[('CGST', '9%'), ('SGST', '9%')]
            ),
            TaggingRequestLineItem(
                item_description="Software license",
                hsn=997331,
                supplier_name="XYZ Tech Solutions",
                po_number="PO-2024-002",
                quantity=10,
                unit_price=50000.0,
                total=590000.0,
                supplier_gstin="29AABCX1234F1Z5",  # Karnataka
                supplier_country="IN",
                buyer_gstin="27AADCB2501D1ZF",  # Maharashtra
                buyer_country="IN",
                tax=[('IGST', '18%')]
            ),
            TaggingRequestLineItem(
                item_description="Legal services from unregistered vendor",
                hsn=998212,
                supplier_name="Advocate Services",
                po_number="PO-2024-003",
                quantity=1,
                unit_price=25000.0,
                total=29500.0,
                supplier_gstin="UNREGISTERED",
                supplier_country="IN",
                buyer_gstin="27AADCB2501D1ZF",  # Maharashtra
                buyer_country="IN",
                tax=[('CGST', '9%'), ('SGST', '9%')]  # Will be RCM
            )
        ],
        erp_type="SAP_ECC"
    )
    
    # Get tax agent
    agent = get_tax_agent()
    
    # Process request
    response = await agent.process_tagging_request(request)
    
    # Print results
    print("\n" + "="*80)
    print("TAX TAGGING RESULTS")
    print("="*80)
    
    for result in response.results:
        print(f"\nLine {result.line_index + 1}: {result.item_description}")
        print(f"Tax Code: {result.tax_code}")
        print(f"Description: {result.tax_description}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Tokens - Prompt: {result.total_prompt_tokens}, "
              f"Completion: {result.total_completion_tokens}, "
              f"Reasoning: {result.total_reasoning_tokens}, "
              f"Total: {result.total_tokens}")
        if result.errors:
            print(f"Errors: {', '.join(result.errors)}")
        print("-" * 80)
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print("="*80)
    print(f"Total Lines: {response.summary['total_lines']}")
    print(f"Successful: {response.summary['successful']}")
    print(f"Manual Review: {response.summary['manual_review']}")
    print(f"Errors: {response.summary['errors']}")
    print(f"Average Confidence: {response.summary['average_confidence']:.3f}")
    print(f"\nToken Usage:")
    print(f"  Prompt Tokens: {response.summary['total_prompt_tokens']}")
    print(f"  Completion Tokens: {response.summary['total_completion_tokens']}")
    print(f"  Reasoning Tokens: {response.summary['total_reasoning_tokens']}")
    print(f"  Total Tokens: {response.summary['total_tokens']}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
