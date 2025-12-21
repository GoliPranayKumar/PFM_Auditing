"""Visualization service for fraud analysis results."""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import numpy as np
from collections import Counter

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


class VisualizationService:
    """Service for generating fraud analysis visualizations."""
    
    # Visualization output directory
    OUTPUT_DIR = Path("visualizations")
    
    # Color schemes
    RISK_COLORS = {
        "Low": "#2ecc71",     # Green
        "Medium": "#f39c12",  # Orange
        "High": "#e74c3c"     # Red
    }
    
    SEVERITY_COLORS = {
        "low": "#3498db",     # Blue
        "medium": "#f39c12",  # Orange
        "high": "#e74c3c"     # Red
    }
    
    def __init__(self):
        """Initialize visualization service."""
        # Create output directory
        self.OUTPUT_DIR.mkdir(exist_ok=True)
    
    def generate_unique_filename(self, prefix: str = "fraud_analysis") -> str:
        """
        Generate unique filename with timestamp.
        
        Args:
            prefix: Filename prefix
            
        Returns:
            Unique filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{prefix}_{timestamp}.png"
    
    def create_fraud_flags_chart(
        self,
        flags: List[Dict],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Create bar chart showing number of fraud flags by category.
        
        Args:
            flags: List of fraud flag dictionaries
            output_path: Optional custom output path
            
        Returns:
            Path to saved chart
        """
        if not flags:
            return self._create_no_flags_chart(output_path)
        
        # Count flags by category
        categories = [flag.get('category', 'unknown') for flag in flags]
        category_counts = Counter(categories)
        
        # Sort by count
        sorted_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        categories_list = [cat.replace('_', ' ').title() for cat, _ in sorted_categories]
        counts = [count for _, count in sorted_categories]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Create bars
        bars = ax.barh(categories_list, counts, color='#e74c3c', alpha=0.7)
        
        # Add value labels on bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(
                count + 0.1,
                i,
                str(count),
                va='center',
                fontweight='bold'
            )
        
        # Styling
        ax.set_xlabel('Number of Flags', fontsize=12, fontweight='bold')
        ax.set_title('Fraud Indicators by Category', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        
        # Save
        if output_path is None:
            output_path = self.OUTPUT_DIR / self.generate_unique_filename("flags_by_category")
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def create_severity_distribution_chart(
        self,
        flags: List[Dict],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Create pie chart showing distribution of severity levels.
        
        Args:
            flags: List of fraud flag dictionaries
            output_path: Optional custom output path
            
        Returns:
            Path to saved chart
        """
        if not flags:
            return self._create_no_flags_chart(output_path)
        
        # Count by severity
        severities = [flag.get('severity', 'unknown') for flag in flags]
        severity_counts = Counter(severities)
        
        # Order: high, medium, low
        severity_order = ['high', 'medium', 'low']
        labels = []
        sizes = []
        colors = []
        
        for sev in severity_order:
            if sev in severity_counts:
                labels.append(f"{sev.title()} ({severity_counts[sev]})")
                sizes.append(severity_counts[sev])
                colors.append(self.SEVERITY_COLORS[sev])
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 11}
        )
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Fraud Flags by Severity Level', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # Save
        if output_path is None:
            output_path = self.OUTPUT_DIR / self.generate_unique_filename("severity_distribution")
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def create_risk_summary_chart(
        self,
        risk_level: str,
        total_flagged_amount: float,
        flags_count: int,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Create summary dashboard showing key metrics.
        
        Args:
            risk_level: Overall risk level (Low/Medium/High)
            total_flagged_amount: Total amount flagged
            flags_count: Number of flags
            output_path: Optional custom output path
            
        Returns:
            Path to saved chart
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # 1. Risk Level Gauge
        ax = axes[0]
        risk_color = self.RISK_COLORS.get(risk_level, '#95a5a6')
        
        ax.text(
            0.5, 0.6,
            risk_level.upper(),
            ha='center',
            va='center',
            fontsize=32,
            fontweight='bold',
            color=risk_color
        )
        ax.text(
            0.5, 0.3,
            'RISK LEVEL',
            ha='center',
            va='center',
            fontsize=14,
            color='#7f8c8d'
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Add colored border
        rect = plt.Rectangle(
            (0.05, 0.05), 0.9, 0.9,
            fill=False,
            edgecolor=risk_color,
            linewidth=4
        )
        ax.add_patch(rect)
        
        # 2. Total Flagged Amount
        ax = axes[1]
        amount_text = f"${total_flagged_amount:,.2f}"
        
        ax.text(
            0.5, 0.6,
            amount_text,
            ha='center',
            va='center',
            fontsize=24,
            fontweight='bold',
            color='#e74c3c'
        )
        ax.text(
            0.5, 0.3,
            'TOTAL FLAGGED',
            ha='center',
            va='center',
            fontsize=14,
            color='#7f8c8d'
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        rect = plt.Rectangle(
            (0.05, 0.05), 0.9, 0.9,
            fill=False,
            edgecolor='#e74c3c',
            linewidth=4
        )
        ax.add_patch(rect)
        
        # 3. Flags Count
        ax = axes[2]
        
        ax.text(
            0.5, 0.6,
            str(flags_count),
            ha='center',
            va='center',
            fontsize=32,
            fontweight='bold',
            color='#3498db'
        )
        ax.text(
            0.5, 0.3,
            'FLAGS DETECTED',
            ha='center',
            va='center',
            fontsize=14,
            color='#7f8c8d'
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        rect = plt.Rectangle(
            (0.05, 0.05), 0.9, 0.9,
            fill=False,
            edgecolor='#3498db',
            linewidth=4
        )
        ax.add_patch(rect)
        
        plt.suptitle('Fraud Analysis Summary', fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        # Save
        if output_path is None:
            output_path = self.OUTPUT_DIR / self.generate_unique_filename("risk_summary")
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def create_confidence_distribution_chart(
        self,
        flags: List[Dict],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Create histogram showing distribution of confidence scores.
        
        Args:
            flags: List of fraud flag dictionaries
            output_path: Optional custom output path
            
        Returns:
            Path to saved chart
        """
        if not flags:
            return self._create_no_flags_chart(output_path)
        
        # Extract confidence scores
        confidences = [flag.get('confidence', 0.0) for flag in flags]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create histogram
        n, bins, patches = ax.hist(
            confidences,
            bins=10,
            range=(0, 1),
            color='#3498db',
            alpha=0.7,
            edgecolor='black'
        )
        
        # Color bars by confidence level
        for i, patch in enumerate(patches):
            confidence_val = (bins[i] + bins[i+1]) / 2
            if confidence_val >= 0.8:
                patch.set_facecolor('#2ecc71')  # Green for high confidence
            elif confidence_val >= 0.5:
                patch.set_facecolor('#f39c12')  # Orange for medium
            else:
                patch.set_facecolor('#e74c3c')  # Red for low confidence
        
        # Styling
        ax.set_xlabel('Confidence Score', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Flags', fontsize=12, fontweight='bold')
        ax.set_title('Confidence Score Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3)
        
        # Add average line
        avg_confidence = np.mean(confidences)
        ax.axvline(
            avg_confidence,
            color='red',
            linestyle='--',
            linewidth=2,
            label=f'Average: {avg_confidence:.2f}'
        )
        ax.legend()
        
        plt.tight_layout()
        
        # Save
        if output_path is None:
            output_path = self.OUTPUT_DIR / self.generate_unique_filename("confidence_distribution")
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def create_comprehensive_dashboard(
        self,
        risk_level: str,
        total_flagged_amount: float,
        flags: List[Dict],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Create comprehensive dashboard with multiple visualizations.
        
        Args:
            risk_level: Overall risk level
            total_flagged_amount: Total amount flagged
            flags: List of fraud flags
            output_path: Optional custom output path
            
        Returns:
            Path to saved dashboard
        """
        if not flags:
            return self._create_no_flags_chart(output_path)
        
        # Create 2x2 grid
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # 1. Summary metrics (top, spanning both columns)
        ax_summary = fig.add_subplot(gs[0, :])
        self._add_summary_metrics(
            ax_summary,
            risk_level,
            total_flagged_amount,
            len(flags)
        )
        
        # 2. Flags by category (bottom left)
        ax_categories = fig.add_subplot(gs[1, 0])
        self._add_category_bars(ax_categories, flags)
        
        # 3. Severity distribution (bottom right)
        ax_severity = fig.add_subplot(gs[1, 1])
        self._add_severity_pie(ax_severity, flags)
        
        # 4. Confidence distribution (bottom left)
        ax_confidence = fig.add_subplot(gs[2, 0])
        self._add_confidence_hist(ax_confidence, flags)
        
        # 5. Amount by category (bottom right)
        ax_amounts = fig.add_subplot(gs[2, 1])
        self._add_amount_by_category(ax_amounts, flags)
        
        plt.suptitle(
            'Fraud Analysis Dashboard',
            fontsize=18,
            fontweight='bold',
            y=0.995
        )
        
        # Save
        if output_path is None:
            output_path = self.OUTPUT_DIR / self.generate_unique_filename("comprehensive_dashboard")
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def _create_no_flags_chart(self, output_path: Optional[Path] = None) -> Path:
        """Create a chart indicating no flags were found."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.text(
            0.5, 0.5,
            '✓ No Fraud Indicators Detected',
            ha='center',
            va='center',
            fontsize=24,
            fontweight='bold',
            color='#2ecc71'
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        if output_path is None:
            output_path = self.OUTPUT_DIR / self.generate_unique_filename("no_flags")
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def _add_summary_metrics(self, ax, risk_level, total_amount, flags_count):
        """Add summary metrics to subplot."""
        risk_color = self.RISK_COLORS.get(risk_level, '#95a5a6')
        
        # Create three boxes
        metrics = [
            (risk_level.upper(), 'RISK LEVEL', risk_color),
            (f"${total_amount:,.0f}", 'TOTAL FLAGGED', '#e74c3c'),
            (str(flags_count), 'FLAGS DETECTED', '#3498db')
        ]
        
        for i, (value, label, color) in enumerate(metrics):
            x_pos = 0.15 + (i * 0.35)
            
            # Box
            rect = plt.Rectangle(
                (x_pos - 0.12, 0.2), 0.24, 0.6,
                fill=False,
                edgecolor=color,
                linewidth=3,
                transform=ax.transAxes
            )
            ax.add_patch(rect)
            
            # Value
            ax.text(
                x_pos, 0.6,
                value,
                ha='center',
                va='center',
                fontsize=20,
                fontweight='bold',
                color=color,
                transform=ax.transAxes
            )
            
            # Label
            ax.text(
                x_pos, 0.35,
                label,
                ha='center',
                va='center',
                fontsize=10,
                color='#7f8c8d',
                transform=ax.transAxes
            )
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    
    def _add_category_bars(self, ax, flags):
        """Add category bar chart to subplot."""
        categories = [flag.get('category', 'unknown') for flag in flags]
        category_counts = Counter(categories)
        
        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        cats = [cat.replace('_', ' ').title() for cat, _ in sorted_cats]
        counts = [count for _, count in sorted_cats]
        
        bars = ax.barh(cats, counts, color='#e74c3c', alpha=0.7)
        
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count + 0.05, i, str(count), va='center', fontweight='bold', fontsize=9)
        
        ax.set_xlabel('Count', fontsize=10)
        ax.set_title('Flags by Category', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
    
    def _add_severity_pie(self, ax, flags):
        """Add severity pie chart to subplot."""
        severities = [flag.get('severity', 'unknown') for flag in flags]
        severity_counts = Counter(severities)
        
        labels = []
        sizes = []
        colors = []
        
        for sev in ['high', 'medium', 'low']:
            if sev in severity_counts:
                labels.append(f"{sev.title()}")
                sizes.append(severity_counts[sev])
                colors.append(self.SEVERITY_COLORS[sev])
        
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.0f%%',
            startangle=90
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
        
        ax.set_title('Severity Distribution', fontsize=12, fontweight='bold')
    
    def _add_confidence_hist(self, ax, flags):
        """Add confidence histogram to subplot."""
        confidences = [flag.get('confidence', 0.0) for flag in flags]
        
        n, bins, patches = ax.hist(confidences, bins=10, range=(0, 1), color='#3498db', alpha=0.7, edgecolor='black')
        
        for i, patch in enumerate(patches):
            conf = (bins[i] + bins[i+1]) / 2
            if conf >= 0.8:
                patch.set_facecolor('#2ecc71')
            elif conf >= 0.5:
                patch.set_facecolor('#f39c12')
            else:
                patch.set_facecolor('#e74c3c')
        
        ax.set_xlabel('Confidence', fontsize=10)
        ax.set_ylabel('Count', fontsize=10)
        ax.set_title('Confidence Distribution', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    def _add_amount_by_category(self, ax, flags):
        """Add amount by category chart to subplot."""
        category_amounts = {}
        
        for flag in flags:
            cat = flag.get('category', 'unknown')
            amount = flag.get('amount_involved', 0) or 0
            category_amounts[cat] = category_amounts.get(cat, 0) + amount
        
        if not category_amounts or all(v == 0 for v in category_amounts.values()):
            ax.text(0.5, 0.5, 'No amount data', ha='center', va='center', transform=ax.transAxes)
            ax.axis('off')
            return
        
        sorted_cats = sorted(category_amounts.items(), key=lambda x: x[1], reverse=True)
        cats = [cat.replace('_', ' ').title() for cat, _ in sorted_cats]
        amounts = [amt for _, amt in sorted_cats]
        
        bars = ax.barh(cats, amounts, color='#9b59b6', alpha=0.7)
        
        for i, (bar, amt) in enumerate(zip(bars, amounts)):
            ax.text(amt + max(amounts) * 0.02, i, f'${amt:,.0f}', va='center', fontweight='bold', fontsize=9)
        
        ax.set_xlabel('Amount ($)', fontsize=10)
        ax.set_title('Flagged Amount by Category', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
    
    def cleanup_old_visualizations(self, max_age_hours: int = 24) -> int:
        """
        Clean up old visualization files.
        
        Args:
            max_age_hours: Maximum age of files to keep
            
        Returns:
            Number of files deleted
        """
        if not self.OUTPUT_DIR.exists():
            return 0
        
        deleted = 0
        current_time = datetime.now().timestamp()
        max_age_seconds = max_age_hours * 3600
        
        for filepath in self.OUTPUT_DIR.iterdir():
            if filepath.is_file() and filepath.suffix == '.png':
                file_age = current_time - filepath.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        filepath.unlink()
                        deleted += 1
                    except Exception:
                        pass
        
        return deleted


# Global service instance
visualization_service = VisualizationService()
