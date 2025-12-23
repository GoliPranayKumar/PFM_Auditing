"""Email service for sending fraud analysis reports via Gmail."""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


class EmailService:
    """Service for sending fraud analysis reports via email."""
    
    def __init__(
        self,
        gmail_user: Optional[str] = None,
        gmail_password: Optional[str] = None,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 465
    ):
        """
        Initialize email service.
        
        Args:
            gmail_user: Gmail email address (from config if not provided)
            gmail_password: Gmail app password (from config if not provided)
            smtp_server: SMTP server address
            smtp_port: SMTP server port
        """
        # Use centralized configuration (NEVER use os.getenv directly)
        from app.core.config import get_gmail_credentials
        
        # Try to get from parameters first, then from config
        if gmail_user and gmail_password:
            self.gmail_user = gmail_user
            self.gmail_password = gmail_password
        else:
            credentials = get_gmail_credentials()
            if credentials:
                self.gmail_user, self.gmail_password = credentials
            else:
                self.gmail_user = None
                self.gmail_password = None
        
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
        # Check if credentials are configured
        self.is_configured = bool(self.gmail_user and self.gmail_password)
    
    def _create_html_report(
        self,
        risk_level: str,
        summary: str,
        total_flagged_amount: float,
        flags: List[Dict[str, Any]],
        recommendations: List[str],
        document_name: Optional[str] = None
    ) -> str:
        """
        Create HTML email body with analysis results.
        
        Args:
            risk_level: Risk level (Low/Medium/High)
            summary: Executive summary
            total_flagged_amount: Total flagged amount
            flags: List of fraud flags
            recommendations: List of recommendations
            document_name: Optional document name
            
        Returns:
            HTML string
        """
        # Risk level color
        risk_colors = {
            "Low": "#2ecc71",
            "Medium": "#f39c12",
            "High": "#e74c3c"
        }
        risk_color = risk_colors.get(risk_level, "#95a5a6")
        
        # Build flags HTML
        flags_html = ""
        for i, flag in enumerate(flags, 1):
            severity_color = {
                "low": "#3498db",
                "medium": "#f39c12",
                "high": "#e74c3c"
            }.get(flag.get('severity', 'low'), '#7f8c8d')
            
            flags_html += f"""
            <div style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid {severity_color}; border-radius: 4px;">
                <h3 style="margin: 0 0 10px 0; color: {severity_color};">
                    {i}. {flag.get('category', 'Unknown').replace('_', ' ').title()} 
                    <span style="font-size: 0.8em;">({flag.get('severity', 'unknown').upper()})</span>
                </h3>
                <p style="margin: 5px 0;"><strong>Description:</strong> {flag.get('description', 'N/A')}</p>
                <p style="margin: 5px 0;"><strong>Evidence:</strong> {flag.get('evidence', 'N/A')}</p>
                <p style="margin: 5px 0;">
                    <strong>Confidence:</strong> {flag.get('confidence', 0) * 100:.1f}%
                    {f" | <strong>Amount:</strong> ${flag.get('amount_involved', 0):,.2f}" if flag.get('amount_involved') else ""}
                </p>
            </div>
            """
        
        # Build recommendations HTML
        recommendations_html = ""
        for i, rec in enumerate(recommendations, 1):
            recommendations_html += f"""
            <li style="margin-bottom: 10px; color: #2c3e50;">{rec}</li>
            """
        
        # Complete HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
                <h1 style="margin: 0; font-size: 28px;">🕵️ Fraud Analysis Report</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{document_name or 'Financial Document Analysis'}</p>
                <p style="margin: 5px 0 0 0; opacity: 0.8; font-size: 14px;">Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <!-- Risk Summary -->
            <div style="background-color: #f8f9fa; padding: 25px; border-radius: 10px; margin-bottom: 30px;">
                <div style="display: flex; justify-content: space-around; text-align: center;">
                    <div style="flex: 1; padding: 15px;">
                        <div style="font-size: 36px; font-weight: bold; color: {risk_color}; margin-bottom: 5px;">{risk_level.upper()}</div>
                        <div style="color: #7f8c8d; font-size: 14px;">RISK LEVEL</div>
                    </div>
                    <div style="flex: 1; padding: 15px; border-left: 2px solid #dee2e6; border-right: 2px solid #dee2e6;">
                        <div style="font-size: 28px; font-weight: bold; color: #e74c3c; margin-bottom: 5px;">${total_flagged_amount:,.2f}</div>
                        <div style="color: #7f8c8d; font-size: 14px;">TOTAL FLAGGED</div>
                    </div>
                    <div style="flex: 1; padding: 15px;">
                        <div style="font-size: 36px; font-weight: bold; color: #3498db; margin-bottom: 5px;">{len(flags)}</div>
                        <div style="color: #7f8c8d; font-size: 14px;">FLAGS DETECTED</div>
                    </div>
                </div>
            </div>
            
            <!-- Executive Summary -->
            <div style="margin-bottom: 30px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 10px;">📋 Executive Summary</h2>
                <p style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #667eea; border-radius: 4px; margin: 15px 0;">
                    {summary}
                </p>
            </div>
            
            <!-- Fraud Indicators -->
            <div style="margin-bottom: 30px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">🚨 Fraud Indicators ({len(flags)})</h2>
                {flags_html if flags else '<p style="color: #2ecc71; font-weight: bold;">✓ No fraud indicators detected</p>'}
            </div>
            
            <!-- Recommendations -->
            {f'''
            <div style="margin-bottom: 30px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #f39c12; padding-bottom: 10px;">💡 Recommendations</h2>
                <ul style="background-color: #fff3cd; padding: 20px 20px 20px 40px; border-left: 4px solid #f39c12; border-radius: 4px; margin: 15px 0;">
                    {recommendations_html}
                </ul>
            </div>
            ''' if recommendations else ''}
            
            <!-- Visualizations Note -->
            <div style="background-color: #e3f2fd; padding: 15px; border-left: 4px solid #2196f3; border-radius: 4px; margin-bottom: 30px;">
                <p style="margin: 0; color: #1976d2;">
                    <strong>📊 Visualizations:</strong> Detailed charts and graphs are attached to this email for your review.
                </p>
            </div>
            
            <!-- Footer -->
            <div style="border-top: 2px solid #dee2e6; padding-top: 20px; margin-top: 40px; text-align: center; color: #7f8c8d; font-size: 12px;">
                <p>This report was generated automatically by the AI-Powered Audit Agent</p>
                <p style="margin: 5px 0;">For questions or concerns, please review the detailed analysis.</p>
                <p style="margin: 5px 0;">⚠️ This email and attachments may contain confidential information.</p>
            </div>
            
        </body>
        </html>
        """
        
        return html
    
    def send_analysis_report(
        self,
        recipient_email: str,
        risk_level: str,
        summary: str,
        total_flagged_amount: float,
        flags: List[Dict[str, Any]],
        recommendations: List[str],
        visualizations: Optional[Dict[str, str]] = None,
        document_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send fraud analysis report via email.
        
        Args:
            recipient_email: Recipient email address
            risk_level: Risk level (Low/Medium/High)
            summary: Executive summary
            total_flagged_amount: Total flagged amount
            flags: List of fraud flags
            recommendations: List of recommendations
            visualizations: Optional dict of visualization file paths
            document_name: Optional document name
            
        Returns:
            Dict with success status and message
            
        Raises:
            Exception: If email sending fails (caller should handle)
        """
        # Check if service is configured
        if not self.is_configured:
            return {
                "success": False,
                "message": "Email service not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD in environment variables.",
                "sent": False
            }
        
        try:
            # Create message
            msg = MIMEMultipart('related')
            msg['From'] = self.gmail_user
            msg['To'] = recipient_email
            msg['Subject'] = f"🚨 Fraud Analysis Report - {risk_level} Risk{f' - {document_name}' if document_name else ''}"
            
            # Create HTML body
            html_body = self._create_html_report(
                risk_level=risk_level,
                summary=summary,
                total_flagged_amount=total_flagged_amount,
                flags=flags,
                recommendations=recommendations,
                document_name=document_name
            )
            
            # Attach HTML
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach visualizations if provided
            attached_files = []
            if visualizations:
                for viz_name, viz_path in visualizations.items():
                    try:
                        path = Path(viz_path)
                        if path.exists():
                            with open(path, 'rb') as f:
                                img = MIMEImage(f.read())
                                img.add_header(
                                    'Content-Disposition',
                                    'attachment',
                                    filename=f"{viz_name}_{datetime.now().strftime('%Y%m%d')}.png"
                                )
                                msg.attach(img)
                                attached_files.append(viz_name)
                    except Exception as e:
                        print(f"Warning: Failed to attach {viz_name}: {e}")
            
            # Send email
            print(f"[Email] Connecting to {self.smtp_server}:{self.smtp_port}...")
            timestamp_start = datetime.now()
            
            # Choose connection method based on port
            # Port 465: Implicit SSL (smtplib.SMTP_SSL) - Recommended for cloud hosting
            # Port 587: Explicit SSL/STARTTLS (smtplib.SMTP + starttls)
            
            if self.smtp_port == 465:
                # Use implicit SSL (Port 465)
                try:
                    server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30)
                    print(f"[Email] Connected (SSL). Logging in as {self.gmail_user}...")
                    server.login(self.gmail_user, self.gmail_password)
                    
                    print(f"[Email] Sending message ({len(msg.as_string())/1024:.1f} KB)...")
                    server.send_message(msg)
                    server.quit()
                except Exception as e:
                     raise e
            else:
                # Use explicit SSL/STARTTLS (Port 587 or others)
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                    print(f"[Email] Connected. Starting TLS...")
                    server.starttls()  # Secure connection
                    
                    print(f"[Email] Logging in as {self.gmail_user}...")
                    server.login(self.gmail_user, self.gmail_password)
                    
                    print(f"[Email] Sending message ({len(msg.as_string())/1024:.1f} KB)...")
                    server.send_message(msg)
                
            duration = (datetime.now() - timestamp_start).total_seconds()
            print(f"[Email] Sent successfully in {duration:.2f}s")
            
            return {
                "success": True,
                "message": f"Email sent successfully to {recipient_email}",
                "sent": True,
                "recipient": recipient_email,
                "attachments": attached_files,
                "timestamp": datetime.now().isoformat()
            }
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"[Email] Authentication Error: {e}")
            return {
                "success": False,
                "message": "Gmail authentication failed. Check GMAIL_USER and GMAIL_APP_PASSWORD.",
                "error": str(e),
                "sent": False
            }
        except smtplib.SMTPConnectError as e:
            print(f"[Email] Connection Error: {e}")
            return {
                "success": False,
                "message": f"Could not connect to SMTP server: {e}",
                "error": str(e),
                "sent": False
            }
        except smtplib.SMTPException as e:
            print(f"[Email] SMTP Error: {e}")
            return {
                "success": False,
                "message": f"SMTP error: {str(e)}",
                "error": str(e),
                "sent": False
            }
        except Exception as e:
            print(f"[Email] General Error: {e}")
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                "error": str(e),
                "sent": False
            }
    
    async def send_analysis_report_async(
        self,
        recipient_email: str,
        risk_level: str,
        summary: str,
        total_flagged_amount: float,
        flags: List[Dict[str, Any]],
        recommendations: List[str],
        visualizations: Optional[Dict[str, str]] = None,
        document_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Async version of send_analysis_report.
        
        Note: Actually synchronous but provides async interface for compatibility.
        For true async, consider using aiosmtplib.
        """
        return self.send_analysis_report(
            recipient_email=recipient_email,
            risk_level=risk_level,
            summary=summary,
            total_flagged_amount=total_flagged_amount,
            flags=flags,
            recommendations=recommendations,
            visualizations=visualizations,
            document_name=document_name
        )


# Global service instance
email_service = EmailService()
