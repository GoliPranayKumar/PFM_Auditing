"""
Example usage of the Fraud Detection Agent.

This script demonstrates how to use the FraudDetectionAgent to analyze
financial documents for fraud, waste, and abuse.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agent.fraud_agent import FraudDetectionAgent


# Sample financial documents for testing
SAMPLE_DOCUMENT_HIGH_RISK = """
QUARTERLY EXPENDITURE REPORT - Q4 2024
Department of Public Works

Transaction Log:

1. Date: 2024-10-15
   Vendor: ABC Consulting LLC, PO Box 5432, Anytown
   Amount: $9,985.00
   Description: IT consulting services
   Invoice: INV-2024-001
   Approved by: John Smith

2. Date: 2024-10-15
   Vendor: ABC Consulting LLC, PO Box 5432, Anytown
   Amount: $9,985.00
   Description: IT consulting services
   Invoice: INV-2024-001
   Approved by: John Smith

3. Date: 2024-11-20
   Vendor: Global Office Supplies Inc
   Amount: $150,000.00
   Description: Office furniture and supplies
   Approved by: [PENDING APPROVAL]
   Notes: Emergency procurement, competitive bidding waived

4. Date: 2024-12-01
   Vendor: Quick Fix Maintenance Ltd, PO Box 5433, Anytown
   Amount: $25,000.00
   Description: Building maintenance
   Approved by: John Smith (self-approved)
   Notes: Sole source award

5. Date: 2024-12-25 (Christmas Day)
   Vendor: Tech Solutions Pro
   Amount: $45,000.00
   Description: Emergency IT infrastructure upgrade
   Invoice: None available
   Approved by: Jane Doe

6. Date: 2024-12-28
   Vendor: ABC Consulting LLC
   Amount: $9,985.00
   Description: Additional consulting
   Invoice: INV-2024-002
   Approved by: John Smith

7. Date: 2024-12-30
   Vendor: Premium Supplies Co
   Amount: $8,500.00
   Description: Year-end office supplies
   Market rate: $3,200 (estimated)
   Approved by: John Smith

Notes:
- Total spending: $267,435.00
- Multiple vendors share similar PO Box addresses
- Several approvals by same individual
- Year-end spending significantly higher than previous quarters
"""

SAMPLE_DOCUMENT_LOW_RISK = """
MONTHLY EXPENDITURE REPORT - November 2024
Finance Department

Transaction 1:
Date: 2024-11-05
Vendor: Staples Inc., 123 Main Street, Boston MA
Amount: $425.50
Description: Office supplies (paper, pens, folders)
Invoice: 89234-A
Purchase Order: PO-2024-1156
Approved by: Sarah Johnson (Department Head)
Reviewed by: Mike Chen (Finance Director)

Transaction 2:
Date: 2024-11-12
Vendor: Dell Technologies
Amount: $1,850.00
Description: Laptop replacement (Model: XPS 15)
Invoice: DELL-92834
Purchase Order: PO-2024-1189
Approved by: Sarah Johnson
Budget code: IT-Equipment-2024
Competitive quotes obtained: Yes (3 vendors)

Transaction 3:
Date: 2024-11-18
Vendor: Metro Cleaning Services, 456 Oak Ave, Boston MA
Amount: $320.00
Description: Monthly office cleaning service
Invoice: MCS-NOV-2024
Contract: Annual service agreement #2024-CS-01
Approved by: Facilities Manager
Auto-approved under contract

Total monthly spending: $2,595.50
All transactions within approved budget
All proper documentation attached
No exceptions or variances noted
"""


def main():
    """Run fraud detection examples."""
    
    print("="*80)
    print("FRAUD DETECTION AGENT - DEMONSTRATION")
    print("="*80)
    print()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set!")
        print()
        print("Please set your OpenAI API key:")
        print("  Windows: set OPENAI_API_KEY=sk-your-key-here")
        print("  Linux/Mac: export OPENAI_API_KEY=sk-your-key-here")
        print()
        return
    
    try:
        # Initialize the agent
        print("Initializing Fraud Detection Agent...")
        agent = FraudDetectionAgent(temperature=0.1)
        print("✅ Agent initialized successfully")
        print()
        
        # Example 1: High-risk document
        print("="*80)
        print("EXAMPLE 1: Analyzing HIGH-RISK Document")
        print("="*80)
        print()
        print("Document Preview:")
        print("-"*80)
        print(SAMPLE_DOCUMENT_HIGH_RISK[:300] + "...")
        print("-"*80)
        print()
        print("Running fraud analysis... (this may take 10-15 seconds)")
        print()
        
        result1 = agent.analyze_document(SAMPLE_DOCUMENT_HIGH_RISK)
        
        # Print formatted report
        print(agent.get_summary_report(result1))
        
        # Example 2: Low-risk document
        print("\n\n")
        print("="*80)
        print("EXAMPLE 2: Analyzing LOW-RISK Document")
        print("="*80)
        print()
        print("Document Preview:")
        print("-"*80)
        print(SAMPLE_DOCUMENT_LOW_RISK[:300] + "...")
        print("-"*80)
        print()
        print("Running fraud analysis...")
        print()
        
        result2 = agent.analyze_document(SAMPLE_DOCUMENT_LOW_RISK)
        
        print(agent.get_summary_report(result2))
        
        # Summary comparison
        print("\n\n")
        print("="*80)
        print("COMPARISON SUMMARY")
        print("="*80)
        print()
        print(f"Document 1 (High-Risk Sample):")
        print(f"  Risk Level: {result1.risk_level}")
        print(f"  Flags Found: {len(result1.list_of_flags)}")
        print(f"  Total Flagged: ${result1.total_flagged_amount:,.2f}")
        print()
        print(f"Document 2 (Low-Risk Sample):")
        print(f"  Risk Level: {result2.risk_level}")
        print(f"  Flags Found: {len(result2.list_of_flags)}")
        print(f"  Total Flagged: ${result2.total_flagged_amount:,.2f}")
        print()
        print("="*80)
        print()
        print("✅ Demonstration completed successfully!")
        print()
        print("Next steps:")
        print("  1. Try analyzing your own financial documents")
        print("  2. Integrate with the FastAPI endpoints")
        print("  3. Export results using export_results_to_json()")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
