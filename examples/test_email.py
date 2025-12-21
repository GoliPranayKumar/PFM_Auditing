"""
Test email delivery functionality.

This script demonstrates how to send fraud analysis reports via email.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.email_service import email_service


# Sample fraud analysis data
SAMPLE_DATA = {
    "risk_level": "High",
    "summary": "Document contains multiple high-severity fraud indicators including duplicate payments, missing approvals, and suspicious vendor behavior. Total flagged amount of $143,490 warrants immediate investigation.",
    "total_flagged_amount": 143490.00,
    "flags": [
        {
            "category": "duplicate_payment",
            "severity": "high",
            "description": "Identical invoice detected",
            "evidence": "Invoice INV-2024-001 to ABC Consulting LLC for $9,995 appears twice on same date (2024-10-15)",
            "confidence": 0.95,
            "amount_involved": 9995.00
        },
        {
            "category": "duplicate_payment",
            "severity": "high",
            "description": "Duplicate transaction confirmation",
            "evidence": "Same vendor, same amount, same description, same date - confirmed duplicate",
            "confidence": 0.92,
            "amount_involved": 9995.00
        },
        {
            "category": "missing_approval",
            "severity": "high",
            "description": "Self-approval detected",
            "evidence": "Transaction for $45,000 shows 'Self-approved' by initiator John Smith",
            "confidence": 0.88,
            "amount_involved": 45000.00
        },
        {
            "category": "policy_violation",
            "severity": "high",
            "description": "Emergency procurement abuse",
            "evidence": "Emergency Services Ltd - no competitive bidding documentation, no approver listed",
            "confidence": 0.82,
            "amount_involved": 45000.00
        },
        {
            "category": "inflated_cost",
            "severity": "medium",
            "description": "Price significantly above market rate",
            "evidence": "Office supplies purchased for $8,500 when market rate estimated at $3,200 (166% markup)",
            "confidence": 0.70,
            "amount_involved": 8500.00
        },
        {
            "category": "suspicious_vendor",
            "severity": "medium",
            "description": "Vendor using PO Box address",
            "evidence": "ABC Consulting LLC lists 'PO Box 5432' instead of physical business address",
            "confidence": 0.65,
            "amount_involved": 25000.00
        }
    ],
    "recommendations": [
        "Immediately investigate duplicate payment to ABC Consulting LLC (INV-2024-001)",
        "Review approval workflow - self-approvals should be automatically rejected",
        "Verify legitimacy of Emergency Services Ltd and review emergency procurement policies",
        "Implement competitive bidding requirements for purchases over $10,000",
        "Conduct market rate analysis for office supplies vendor",
        "Verify physical business address for ABC Consulting LLC",
        "Implement automated duplicate detection system",
        "Review all transactions approved by John Smith in Q4 2024"
    ],
    "document_name": "Q4_2024_Expenditure_Report"
}


def check_configuration():
    """Check if email service is configured."""
    print("="*80)
    print("EMAIL CONFIGURATION CHECK")
    print("="*80)
    print()
    
    if email_service.is_configured:
        print("✅ Email service is configured")
        print(f"   Gmail User: {email_service.gmail_user}")
        print(f"   SMTP Server: {email_service.smtp_server}:{email_service.smtp_port}")
        print()
        return True
    else:
        print("❌ Email service NOT configured")
        print()
        print("To enable email reports:")
        print("1. Get a Gmail App Password:")
        print("   • Go to https://myaccount.google.com/apppasswords")
        print("   • Sign in with your Gmail account")
        print("   • Create new app password for 'Mail'")
        print()
        print("2. Set environment variables in .env file:")
        print("   GMAIL_USER=your_email@gmail.com")
        print("   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx")
        print()
        print("3. Restart the script")
        print()
        return False


def test_send_email():
    """Test sending an email report."""
    print("="*80)
    print("TESTING EMAIL SEND")
    print("="*80)
    print()
    
    # Get recipient email
    recipient = input("Enter recipient email address: ").strip()
    
    if not recipient or '@' not in recipient:
        print("❌ Invalid email address")
        return
    
    print()
    print(f"Sending fraud analysis report to: {recipient}")
    print("(This may take a few seconds...)")
    print()
    
    # Generate sample visualizations (if available)
    visualizations = None
    try:
        from backend.services.visualization import visualization_service
        
        print("Generating visualizations...")
        dashboard_path = visualization_service.create_comprehensive_dashboard(
            risk_level=SAMPLE_DATA["risk_level"],
            total_flagged_amount=SAMPLE_DATA["total_flagged_amount"],
            flags=SAMPLE_DATA["flags"]
        )
        
        visualizations = {
            "dashboard": str(dashboard_path)
        }
        print(f"✅ Dashboard created: {dashboard_path}")
        print()
        
    except Exception as e:
        print(f"⚠️  Skipping visualizations: {e}")
        print()
    
    # Send email
    result = email_service.send_analysis_report(
        recipient_email=recipient,
        risk_level=SAMPLE_DATA["risk_level"],
        summary=SAMPLE_DATA["summary"],
        total_flagged_amount=SAMPLE_DATA["total_flagged_amount"],
        flags=SAMPLE_DATA["flags"],
        recommendations=SAMPLE_DATA["recommendations"],
        visualizations=visualizations,
        document_name=SAMPLE_DATA["document_name"]
    )
    
    # Display result
    print("="*80)
    print("EMAIL SEND RESULT")
    print("="*80)
    print()
    
    if result["success"]:
        print("✅ Email sent successfully!")
        print()
        print(f"   Recipient: {result['recipient']}")
        print(f"   Timestamp: {result['timestamp']}")
        if result.get('attachments'):
            print(f"   Attachments: {', '.join(result['attachments'])}")
        print()
        print("Check your inbox (and spam folder) for the report.")
    else:
        print("❌ Failed to send email")
        print()
        print(f"   Error: {result['message']}")
        if result.get('error'):
            print(f"   Details: {result['error']}")
        print()
        
        if "authentication" in result['message'].lower():
            print("💡 Authentication failed. Make sure you're using:")
            print("   • A Gmail App Password (not your regular password)")
            print("   • The correct Gmail address")
            print()
    
    print("="*80)


def test_via_api():
    """Show how to use email via API."""
    print("="*80)
    print("USING EMAIL VIA API")
    print("="*80)
    print()
    
    print("To send analysis reports via email through the API:")
    print()
    print("1. Add 'recipient_email' to your request:")
    print()
    print("   Python example:")
    print("   ```python")
    print("   import requests")
    print()
    print("   response = requests.post(")
    print("       'http://localhost:8000/api/v1/document/analyze',")
    print("       json={")
    print("           'document_text': 'Your financial document...',")
    print("           'document_name': 'Q4_Report',")
    print("           'recipient_email': 'auditor@company.com'  # Add this!")
    print("       }")
    print("   )")
    print()
    print("   result = response.json()")
    print("   if result['email_sent']['success']:")
    print("       print('Email sent!')")
    print("   ```")
    print()
    print("2. Check the 'email_sent' field in the response:")
    print()
    print("   ```json")
    print("   {")
    print("     \"risk_level\": \"High\",")
    print("     \"email_sent\": {")
    print("       \"success\": true,")
    print("       \"message\": \"Email sent successfully\",")
    print("       \"recipient\": \"auditor@company.com\"")
    print("     }")
    print("   }")
    print("   ```")
    print()
    print("="*80)


def main():
    """Run email tests."""
    print("\n" + "="*80)
    print("EMAIL SERVICE - TEST SUITE")
    print("="*80)
    print()
    
    # Check configuration
    if not check_configuration():
        print("\n" + "="*80)
        print("⚠️  Email service not configured - skipping tests")
        print("="*80)
        print()
        test_via_api()
        return
    
    print("Email service is ready!")
    print()
    print("Options:")
    print("  1. Send test email")
    print("  2. View API usage example")
    print("  3. Exit")
    print()
    
    choice = input("Select option (1-3): ").strip()
    
    if choice == "1":
        test_send_email()
    elif choice == "2":
        test_via_api()
    else:
        print("Exiting...")
    
    print("\n" + "="*80)
    print("✅ Email test completed")
    print("="*80)
    print()
    print("Next steps:")
    print("  • Configure Gmail credentials in .env if not done")
    print("  • Use 'recipient_email' field in API requests")
    print("  • Check email_sent status in responses")
    print()


if __name__ == "__main__":
    main()
