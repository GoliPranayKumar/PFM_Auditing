"""
Test the Audit Agent API endpoints using Python requests.

This script demonstrates how to interact with the FastAPI endpoints.
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        print("✅ Health check passed!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Health check failed: {response.status_code}")
    print()


def test_transaction_analysis():
    """Test transaction-level fraud analysis."""
    print("Testing transaction analysis endpoint...")
    
    payload = {
        "transaction_description": "Payment to ABC Consulting for IT services",
        "amount": 9995.00,
        "vendor": "ABC Consulting LLC",
        "category": "IT Services",
        "additional_context": "Emergency procurement on December 25th"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/audit/analyze",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print("✅ Transaction analysis successful!")
        result = response.json()
        print(f"Risk Level: {result['risk_level']}")
        print(f"Risk Score: {result['risk_score']}")
        print(f"Indicators Found: {len(result['fraud_indicators'])}")
        print("\nFull Response:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Transaction analysis failed: {response.status_code}")
        print(response.text)
    print()


def test_document_analysis():
    """Test document-level fraud analysis."""
    print("Testing document analysis endpoint...")
    
    document_text = """
QUARTERLY EXPENDITURE REPORT - Q4 2024
Department: Finance

Transaction 1:
Date: 2024-10-15
Vendor: ABC Consulting LLC, PO Box 5432
Amount: $9,985.00
Description: IT consulting services
Invoice: INV-2024-001
Approved by: John Smith

Transaction 2:
Date: 2024-10-15
Vendor: ABC Consulting LLC, PO Box 5432
Amount: $9,985.00
Description: IT consulting services
Invoice: INV-2024-001
Approved by: John Smith

Transaction 3:
Date: 2024-12-25 (Christmas Day)
Vendor: Emergency Services Ltd
Amount: $45,000.00
Description: Emergency IT infrastructure
Approved by: Self-approved
Documentation: None available

Transaction 4:
Date: 2024-12-30
Vendor: Office Supplies Pro
Amount: $8,500.00
Description: Year-end office supplies
Market Rate: Estimated $3,200
Approved by: John Smith

Total Spending: $73,470.00
"""
    
    payload = {
        "document_text": document_text,
        "document_name": "Q4_2024_Finance_Report",
        "document_type": "expense_report"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/document/analyze",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print("✅ Document analysis successful!")
        result = response.json()
        print(f"Risk Level: {result['risk_level']}")
        print(f"Flags Found: {len(result['list_of_flags'])}")
        print(f"Total Flagged Amount: ${result['total_flagged_amount']:,.2f}")
        print("\nDetected Issues:")
        for i, flag in enumerate(result['list_of_flags'], 1):
            print(f"\n{i}. {flag['category'].upper()} - {flag['severity'].upper()}")
            print(f"   Description: {flag['description']}")
            print(f"   Confidence: {flag['confidence'] * 100:.1f}%")
        
        print("\nRecommendations:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"{i}. {rec}")
        
        print("\n\nFull Response:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Document analysis failed: {response.status_code}")
        print(response.text)
    print()


def main():
    """Run all API tests."""
    print("="*80)
    print("AUDIT AGENT API - ENDPOINT TESTS")
    print("="*80)
    print()
    print("Make sure the API server is running:")
    print("  uvicorn app.main:app --reload")
    print()
    print("="*80)
    print()
    
    try:
        # Test 1: Health Check
        test_health_check()
        
        # Test 2: Transaction Analysis
        test_transaction_analysis()
        
        # Test 3: Document Analysis (requires OpenAI API key)
        print("⚠️  Document analysis requires OpenAI API key and may take 10-15 seconds")
        test_document_analysis()
        
        print("="*80)
        print("✅ All API tests completed!")
        print("="*80)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
