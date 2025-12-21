"""
Test visualization generation functionality.

This script demonstrates the visualization service capabilities.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.visualization import visualization_service


# Sample fraud flags data
SAMPLE_FLAGS = [
    {
        "category": "duplicate_payment",
        "severity": "high",
        "description": "Duplicate invoice detected",
        "evidence": "Invoice INV-2024-001 appears twice",
        "confidence": 0.95,
        "amount_involved": 9995.00
    },
    {
        "category": "duplicate_payment",
        "severity": "high",
        "description": "Another duplicate payment",
        "evidence": "Same vendor and amount on same date",
        "confidence": 0.92,
        "amount_involved": 9995.00
    },
    {
        "category": "missing_approval",
        "severity": "medium",
        "description": "Self-approval detected",
        "evidence": "John Smith approved own transaction",
        "confidence": 0.75,
        "amount_involved": 45000.00
    },
    {
        "category": "suspicious_vendor",
        "severity": "medium",
        "description": "PO Box address",
        "evidence": "Vendor uses PO Box instead of physical address",
        "confidence": 0.65,
        "amount_involved": 25000.00
    },
    {
        "category": "policy_violation",
        "severity": "high",
        "description": "Emergency procurement abuse",
        "evidence": "No competitive bidding documentation",
        "confidence": 0.88,
        "amount_involved": 45000.00
    },
    {
        "category": "inflated_cost",
        "severity": "medium",
        "description": "Above market pricing",
        "evidence": "Price $8,500 vs market $3,200",
        "confidence": 0.70,
        "amount_involved": 8500.00
    }
]


def test_individual_charts():
    """Test individual chart generation."""
    print("="*80)
    print("TESTING INDIVIDUAL CHARTS")
    print("="*80)
    print()
    
    # 1. Fraud Flags by Category
    print("1. Generating flags by category chart...")
    flags_path = visualization_service.create_fraud_flags_chart(SAMPLE_FLAGS)
    print(f"   ✅ Saved to: {flags_path}")
    print(f"   Size: {flags_path.stat().st_size:,} bytes")
    print()
    
    # 2. Severity Distribution
    print("2. Generating severity distribution chart...")
    severity_path = visualization_service.create_severity_distribution_chart(SAMPLE_FLAGS)
    print(f"   ✅ Saved to: {severity_path}")
    print(f"   Size: {severity_path.stat().st_size:,} bytes")
    print()
    
    # 3. Risk Summary
    print("3. Generating risk summary dashboard...")
    risk_path = visualization_service.create_risk_summary_chart(
        risk_level="High",
        total_flagged_amount=143490.00,
        flags_count=len(SAMPLE_FLAGS)
    )
    print(f"   ✅ Saved to: {risk_path}")
    print(f"   Size: {risk_path.stat().st_size:,} bytes")
    print()
    
    # 4. Confidence Distribution
    print("4. Generating confidence distribution chart...")
    confidence_path = visualization_service.create_confidence_distribution_chart(SAMPLE_FLAGS)
    print(f"   ✅ Saved to: {confidence_path}")
    print(f"   Size: {confidence_path.stat().st_size:,} bytes")
    print()


def test_comprehensive_dashboard():
    """Test comprehensive dashboard generation."""
    print("="*80)
    print("TESTING COMPREHENSIVE DASHBOARD")
    print("="*80)
    print()
    
    print("Generating comprehensive dashboard with all charts...")
    dashboard_path = visualization_service.create_comprehensive_dashboard(
        risk_level="High",
        total_flagged_amount=143490.00,
        flags=SAMPLE_FLAGS
    )
    
    print(f"✅ Dashboard saved to: {dashboard_path}")
    print(f"   Size: {dashboard_path.stat().st_size:,} bytes")
    print()


def test_no_flags():
    """Test visualization with no flags."""
    print("="*80)
    print("TESTING NO FLAGS SCENARIO")
    print("="*80)
    print()
    
    print("Generating chart for document with no flags...")
    no_flags_path = visualization_service.create_fraud_flags_chart([])
    print(f"✅ Saved to: {no_flags_path}")
    print()


def display_summary():
    """Display summary of generated files."""
    print("="*80)
    print("VISUALIZATION FILES SUMMARY")
    print("="*80)
    print()
    
    viz_dir = Path("visualizations")
    if not viz_dir.exists():
        print("No visualizations directory found.")
        return
    
    files = list(viz_dir.glob("*.png"))
    if not files:
        print("No visualization files found.")
        return
    
    print(f"Total files: {len(files)}")
    print()
    
    total_size = 0
    for file in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
        size = file.stat().st_size
        total_size += size
        print(f"  📊 {file.name}")
        print(f"     Size: {size:,} bytes")
        print()
    
    print(f"Total size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print()
    print(f"View files in: {viz_dir.absolute()}")
    print()


def main():
    """Run all visualization tests."""
    print("\n" + "="*80)
    print("VISUALIZATION SERVICE - TEST SUITE")
    print("="*80)
    print()
    
    try:
        # Test individual charts
        test_individual_charts()
        
        # Test comprehensive dashboard
        test_comprehensive_dashboard()
        
        # Test no flags scenario
        test_no_flags()
        
        # Display summary
        display_summary()
        
        print("="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print()
        print("Charts generated:")
        print("  • Flags by category (bar chart)")
        print("  • Severity distribution (pie chart)")
        print("  • Risk summary dashboard (metrics)")
        print("  • Confidence distribution (histogram)")
        print("  • Comprehensive dashboard (all-in-one)")
        print()
        print("Next steps:")
        print("  1. Open the visualizations/ folder")
        print("  2. View the generated PNG files")
        print("  3. Try uploading documents via the API to see automatic generation")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
