"""Audit analysis endpoints."""

from fastapi import APIRouter, HTTPException, status
from app.models.schemas import AuditRequest, AuditResponse
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])


@router.post("/analyze", response_model=AuditResponse, status_code=status.HTTP_200_OK)
async def analyze_transaction(request: AuditRequest) -> AuditResponse:
    """
    Analyze a financial transaction for fraud, waste, and abuse indicators.
    
    This endpoint uses AI to analyze transaction details and identify potential
    fraud indicators, providing a risk score and recommendations.
    
    Args:
        request: AuditRequest containing transaction details
        
    Returns:
        AuditResponse with fraud analysis results
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        result = await audit_service.perform_audit(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing transaction: {str(e)}"
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def audit_info():
    """
    Get information about the audit API.
    
    Returns:
        API information and available endpoints
    """
    return {
        "message": "Audit Agent API - Fraud, Waste, and Abuse Detection",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/v1/audit/analyze": "Analyze a transaction for fraud indicators"
        },
        "documentation": "/docs"
    }
