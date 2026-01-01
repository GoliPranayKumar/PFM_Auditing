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
    """
    Service for sending fraud analysis reports via Email.
    Supports:
    1. Resend API (Preferred - HTTP based, works everywhere)
    2. Gmail SMTP (Legacy - Port blocking issues on cloud)
    """
    
    def __init__(self):
        """Initialize email service with configuration."""
        # Use centralized configuration
        from app.core.config import get_gmail_credentials, get_resend_api_key
        import resend
        
        # 1. Try Resend (Priority)
        self.resend_api_key = get_resend_api_key()
        if self.resend_api_key:
            resend.api_key = self.resend_api_key
            self.provider = "resend"
            self.is_configured = True
            print(f"[Email] Service configured using Resend API (Trusted)")
            
        # 2. Fallback to Gmail
        else:
            credentials = get_gmail_credentials()
            if credentials:
                self.gmail_user, self.gmail_password = credentials
                self.provider = "gmail"
                self.is_configured = True
                self.smtp_server = "smtp.gmail.com"
                self.smtp_port = 587
                print(f"[Email] Service configured using Gmail SMTP (Legacy)")
            else:
                self.provider = None
                self.is_configured = False
                print(f"[Email] Service NOT configured (No Resend Key or Gmail Credentials)")

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
        (Same HTML generation logic as before)
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
        Send fraud analysis report via configure provider (Resend or Gmail).
        """
        if not self.is_configured:
            return {
                "success": False,
                "message": "No email service configured (Set RESEND_API_KEY or Gmail creds)",
                "sent": False
            }
            
        # Generate content
        html_body = self._create_html_report(
            risk_level=risk_level,
            summary=summary,
            total_flagged_amount=total_flagged_amount,
            flags=flags,
            recommendations=recommendations,
            document_name=document_name
        )
        
        subject = f"🚨 Fraud Analysis Report - {risk_level} Risk{f' - {document_name}' if document_name else ''}"
        
        # ----------------------------------------
        # WAY 1: Use Resend (Preferred)
        # ----------------------------------------
        if self.provider == "resend":
            try:
                import resend
                print(f"[Email] Sending via Resend API to {recipient_email}...")
                
                # Prepare attachments for Resend (list of dicts with content as int list)
                attachments = []
                if visualizations:
                    for viz_name, viz_path in visualizations.items():
                        path = Path(viz_path)
                        if path.exists():
                            with open(path, 'rb') as f:
                                file_content = list(f.read()) # Convert bytes to list of ints
                                attachments.append({
                                    "filename": f"{viz_name}_{datetime.now().strftime('%Y%m%d')}.png",
                                    "content": file_content
                                })
                
                params = {
                    "from": "PFM Analyzer <onboarding@resend.dev>", # Neutral sender name
                    "to": [recipient_email],
                    "subject": f"Financial Analysis Report - {document_name or 'Document'}", # Neutral subject
                    "html": html_body,
                    "attachments": attachments
                }
                
                # NOTE: In Resend free tier, you can only send to the email you signed up with!
                # Unless you verify a domain.
                
                r = resend.Emails.send(params)
                print(f"[Email] Resend API Response: {r}")
                
                return {
                    "success": True,
                    "message": "Email sent via Resend API",
                    "sent": True,
                    "provider": "resend",
                    "response": r
                }
                
            except Exception as e:
                print(f"[Email] ❌ Resend API Error: {e}")
                return {
                    "success": False, 
                    "message": f"Resend API failed: {str(e)}", 
                    "error": str(e)
                }

        # ----------------------------------------
        # WAY 2: Use Gmail SMTP (Legacy)
        # ----------------------------------------
        elif self.provider == "gmail":
            return self._send_via_gmail(recipient_email, subject, html_body, visualizations)
            
        return {"success": False, "message": "Unknown provider", "sent": False}

    def _send_via_gmail(self, recipient_email, subject, html_body, visualizations):
        """Internal method to send via Gmail SMTP."""
        try:
            print(f"[Email] Sending via Gmail SMTP to {recipient_email}...")
            # Create message
            msg = MIMEMultipart('related')
            msg['From'] = self.gmail_user
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach visualizations
            if visualizations:
                for viz_name, viz_path in visualizations.items():
                    try:
                        path = Path(viz_path)
                        if path.exists():
                            with open(path, 'rb') as f:
                                img = MIMEImage(f.read())
                                img.add_header('Content-Disposition', 'attachment', 
                                             filename=f"{viz_name}.png")
                                msg.attach(img)
                    except Exception as e:
                        print(f"Attachment error: {e}")
            
            # Connect
            import socket
            smtp_host_ip = self.smtp_server
            try:
                addr_info = socket.getaddrinfo(self.smtp_server, self.smtp_port, family=socket.AF_INET)
                if addr_info: smtp_host_ip = addr_info[0][4][0]
            except: pass
            
            with smtplib.SMTP(host=smtp_host_ip, port=self.smtp_port, timeout=120) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)
                
            print(f"[Email] Sent via Gmail successfully")
            return {"success": True, "message": "Sent via Gmail", "sent": True, "provider": "gmail"}
            
        except Exception as e:
            print(f"[Email] ❌ Gmail SMTP Error: {e}")
            return {"success": False, "message": f"Gmail failed: {e}", "error": str(e)}

    async def send_analysis_report_async(self, *args, **kwargs):
        """Async compatibility wrapper."""
        return self.send_analysis_report(*args, **kwargs)

email_service = EmailService()
