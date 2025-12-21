"""Audit service orchestrating business logic."""

from typing import List
from app.models.schemas import AuditRequest, AuditResponse, FraudIndicator
from app.services.langchain_service import langchain_service


class AuditService:
    """Service for orchestrating audit operations."""
    
    async def perform_audit(self, request: AuditRequest) -> AuditResponse:
        """
        Perform comprehensive audit analysis on a transaction.
        
        Args:
            request: AuditRequest containing transaction details
            
        Returns:
            AuditResponse with fraud analysis results
        """
        
        # Call LangChain service for AI analysis
        analysis = await langchain_service.analyze_transaction(
            transaction_description=request.transaction_description,
            amount=request.amount,
            vendor=request.vendor,
            category=request.category,
            additional_context=request.additional_context
        )
        
        # Convert to response format
        fraud_indicators = [
            FraudIndicator(
                type=indicator.get("type", "Unknown"),
                severity=indicator.get("severity", "low"),
                description=indicator.get("description", ""),
                confidence=indicator.get("confidence", 0.5)
            )
            for indicator in analysis.fraud_indicators
        ]
        
        response = AuditResponse(
            risk_score=analysis.risk_score,
            risk_level=analysis.risk_level,
            fraud_indicators=fraud_indicators,
            summary=analysis.summary,
            recommendations=analysis.recommendations
        )
        
        return response


# Global service instance
audit_service = AuditService()
