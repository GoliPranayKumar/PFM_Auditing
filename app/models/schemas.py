"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AuditRequest(BaseModel):
    """Request model for audit analysis."""
    
    transaction_description: str = Field(
        ...,
        description="Description of the financial transaction or expenditure",
        min_length=10,
        max_length=5000
    )
    amount: float = Field(
        ...,
        description="Transaction amount",
        gt=0
    )
    vendor: Optional[str] = Field(
        None,
        description="Vendor or recipient name"
    )
    category: Optional[str] = Field(
        None,
        description="Expenditure category"
    )
    additional_context: Optional[str] = Field(
        None,
        description="Any additional context or notes"
    )


class FraudIndicator(BaseModel):
    """Individual fraud indicator."""
    
    type: str = Field(..., description="Type of fraud indicator")
    severity: str = Field(..., description="Severity level: low, medium, high")
    description: str = Field(..., description="Description of the indicator")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class AuditResponse(BaseModel):
    """Response model for audit analysis."""
    
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall risk score (0-100)"
    )
    risk_level: str = Field(
        ...,
        description="Risk classification: low, medium, high, critical"
    )
    fraud_indicators: List[FraudIndicator] = Field(
        default_factory=list,
        description="List of detected fraud indicators"
    )
    summary: str = Field(
        ...,
        description="Summary of the audit findings"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommended actions"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analysis timestamp"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    app_name: str
    version: str
    environment: str


# Document-based fraud analysis schemas
class DocumentAuditRequest(BaseModel):
    """Request model for document-based fraud analysis."""
    
    document_text: str = Field(
        ...,
        description="Extracted text from the financial document to analyze",
        min_length=50,
        max_length=100000
    )
    document_name: Optional[str] = Field(
        None,
        description="Name or identifier of the document"
    )
    document_type: Optional[str] = Field(
        None,
        description="Type of document (e.g., expense report, invoice, procurement)"
    )
    recipient_email: Optional[str] = Field(
        None,
        description="Optional email address to send analysis report"
    )


class DocumentFraudFlag(BaseModel):
    """Individual fraud flag from document analysis."""
    
    category: str = Field(..., description="Category of fraud indicator")
    severity: str = Field(..., description="Severity: low, medium, high")
    description: str = Field(..., description="Description of the issue")
    evidence: str = Field(..., description="Evidence from document")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    amount_involved: Optional[float] = Field(None, description="Dollar amount if applicable")


class DocumentAuditResponse(BaseModel):
    """Response model for document-based fraud analysis."""
    
    risk_level: str = Field(
        ...,
        description="Overall risk level: Low, Medium, or High"
    )
    summary: str = Field(
        ...,
        description="Executive summary of audit findings"
    )
    list_of_flags: List[DocumentFraudFlag] = Field(
        default_factory=list,
        description="List of all detected fraud indicators"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommended actions"
    )
    total_flagged_amount: float = Field(
        default=0.0,
        description="Total dollar amount flagged"
    )
    document_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Analysis metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analysis timestamp"
    )
    visualizations: Optional[Dict[str, str]] = Field(
        None,
        description="Paths to generated visualization charts"
    )
    email_sent: Optional[Dict[str, Any]] = Field(
        None,
        description="Email delivery status if recipient was provided"
    )


# File upload schemas
class FileUploadResponse(BaseModel):
    """Response model for file upload and analysis."""
    
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (.pdf, .docx, .txt)")
    file_size_bytes: int = Field(..., description="File size in bytes")
    extracted_text_length: int = Field(..., description="Length of extracted text")
    analysis: DocumentAuditResponse = Field(..., description="Fraud analysis results")
