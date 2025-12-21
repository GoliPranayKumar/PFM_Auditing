"""
Test the file upload and analysis endpoint.

This script demonstrates how to upload PDF, DOCX, and TXT files for fraud analysis.
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"


def create_sample_txt_file():
    """Create a sample TXT file for testing."""
    content = """
QUARTERLY EXPENDITURE REPORT - Q4 2024
Department of Finance

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
    
    filepath = Path("test_document.txt")
    filepath.write_text(content, encoding='utf-8')
    return filepath


def test_file_upload_api(filepath: Path):
    """
    Test file upload and analysis endpoint.
    
    Args:
        filepath: Path to file to upload
    """
    print(f"\n{'='*80}")
    print(f"Testing File Upload: {filepath.name}")
    print(f"{'='*80}\n")
    
    # Open and upload file
    with open(filepath, 'rb') as f:
        files = {'file': (filepath.name, f, 'multipart/form-data')}
        
        print(f"Uploading {filepath.name}...")
        print("Extracting text and analyzing for fraud...")
        print("(This may take 10-15 seconds)")
        print()
        
        response = requests.post(
            f"{BASE_URL}/api/v1/upload/analyze",
            files=files
        )
    
    if response.status_code == 200:
        print("✅ File upload and analysis successful!\n")
        result = response.json()
        
        # Display results
        print(f"📄 File Information:")
        print(f"   Filename: {result['filename']}")
        print(f"   File Type: {result['file_type']}")
        print(f"   File Size: {result['file_size_bytes']:,} bytes")
        print(f"   Extracted Text: {result['extracted_text_length']:,} characters")
        print()
        
        analysis = result['analysis']
        print(f"🔍 Fraud Analysis Results:")
        print(f"   Risk Level: {analysis['risk_level']}")
        print(f"   Total Flagged Amount: ${analysis['total_flagged_amount']:,.2f}")
        print(f"   Flags Found: {len(analysis['list_of_flags'])}")
        print()
        
        print(f"📋 Executive Summary:")
        print(f"   {analysis['summary']}")
        print()
        
        if analysis['list_of_flags']:
            print(f"🚨 Fraud Indicators:")
            for i, flag in enumerate(analysis['list_of_flags'], 1):
                print(f"\n   {i}. {flag['category'].upper().replace('_', ' ')} - {flag['severity'].upper()}")
                print(f"      Description: {flag['description']}")
                print(f"      Evidence: {flag['evidence'][:100]}...")
                print(f"      Confidence: {flag['confidence']*100:.1f}%")
                if flag['amount_involved']:
                    print(f"      Amount: ${flag['amount_involved']:,.2f}")
        
        print()
        if analysis['recommendations']:
            print(f"💡 Recommendations:")
            for i, rec in enumerate(analysis['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print()
        print(f"{'='*80}")
        print("Full JSON Response:")
        print(json.dumps(result, indent=2))
        print(f"{'='*80}\n")
        
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"Error: {response.text}\n")


def test_upload_info():
    """Test the upload info endpoint."""
    print(f"\n{'='*80}")
    print("Upload API Information")
    print(f"{'='*80}\n")
    
    response = requests.get(f"{BASE_URL}/api/v1/upload/")
    
    if response.status_code == 200:
        info = response.json()
        print("✅ Upload API is available\n")
        print(json.dumps(info, indent=2))
        print()
    else:
        print(f"❌ Failed to get upload info: {response.status_code}\n")


def test_cleanup():
    """Test the cleanup endpoint."""
    print(f"\n{'='*80}")
    print("Testing Cleanup Endpoint")
    print(f"{'='*80}\n")
    
    response = requests.post(f"{BASE_URL}/api/v1/upload/cleanup?max_age_hours=1")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Cleanup successful")
        print(f"   Files deleted: {result['files_deleted']}")
        print(f"   Max age: {result['max_age_hours']} hours\n")
    else:
        print(f"❌ Cleanup failed: {response.status_code}\n")


def main():
    """Run all upload API tests."""
    print("\n" + "="*80)
    print("FILE UPLOAD & ANALYSIS API - TESTS")
    print("="*80)
    print("\nMake sure the API server is running:")
    print("  uvicorn app.main:app --reload")
    print("\n" + "="*80)
    
    try:
        # Test 1: Get upload API info
        test_upload_info()
        
        # Test 2: Create and upload sample file
        print("\nCreating sample test file...")
        sample_file = create_sample_txt_file()
        print(f"✅ Created: {sample_file}")
        
        test_file_upload_api(sample_file)
        
        # Test 3: Cleanup old files
        test_cleanup()
        
        # Cleanup test file
        if sample_file.exists():
            sample_file.unlink()
            print(f"🧹 Cleaned up test file: {sample_file.name}")
        
        print("\n" + "="*80)
        print("✅ All file upload tests completed!")
        print("="*80 + "\n")
        
        print("💡 Try uploading your own files:")
        print("   • PDF documents")
        print("   • DOCX documents")
        print("   • TXT files")
        print("\nUse the interactive API docs: http://localhost:8000/docs")
        print("Look for the 'File Upload' section\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API server.")
        print("Make sure the server is running on http://localhost:8000\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")


if __name__ == "__main__":
    main()
