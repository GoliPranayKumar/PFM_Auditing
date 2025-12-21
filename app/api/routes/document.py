"""
Document-based fraud analysis endpoints.

API Flow:
1. User submits document text
2. Agent analyzes for fraud/waste/abuse
3. Visualizations are generated
4. Optional email is sent
5. JSON response returned
"""

from fastapi import APIRouter, HTTPException, status
from app.models.schemas import DocumentAuditRequest, DocumentAuditResponse, DocumentFraudFlag
from app.utils.logger import get_logger
from backend.agent.fraud_agent import FraudDetectionAgent

# Initialize router
router = APIRouter(prefix="/api/v1/document", tags=["Document Analysis"])

# Initialize services
fraud_agent = FraudDetectionAgent()
logger = get_logger(__name__)


@router.post("/analyze", response_model=DocumentAuditResponse, status_code=status.HTTP_200_OK)
async def analyze_document(request: DocumentAuditRequest) -> DocumentAuditResponse:
    """
    Analyze a complete financial document for fraud, waste, and abuse.
    
    **Complete Analysis Flow:**
    
    1. **Text Validation** - Verify document text meets requirements
    2. **Fraud Analysis** - AI agent detects fraud patterns using LangChain
    3. **Visualization Generation** - Create charts (dashboard, flags, severity)
    4. **Email Delivery** - Send report if recipient_email provided
    5. **Structured Response** - Return complete JSON analysis
    
    **Detection Capabilities:**
    - Duplicate payments
    - Inflated costs
    - Missing approvals
    - Suspicious vendor behavior
    - Policy violations
    - Temporal anomalies
    
    **Automatically Generated:**
    - Risk assessment (Low/Medium/High)
    - Executive summary
    - Detailed fraud flags with evidence
    - Actionable recommendations
    - Visualization charts
    - Optional email report
    
    Args:
        request: DocumentAuditRequest with document text and optional metadata
        
    Returns:
        DocumentAuditResponse with comprehensive fraud analysis
        
    Raises:
        HTTPException 400: Invalid document (too short/long)
        HTTPException 500: Analysis or processing error
    
    Example:
        ```python
        import requests
        
        response = requests.post(
            "http://localhost:8000/api/v1/document/analyze",
            json={
                "document_text": "EXPENDITURE REPORT...",
                "document_name": "Q4_2024",
                "recipient_email": "auditor@company.com"  # Optional
            }
        )
        
        result = response.json()
        print(f"Risk: {result['risk_level']}")
        print(f"Flags: {len(result['list_of_flags'])}")
        print(f"Email sent: {result['email_sent']['success']}")
        ```
    """
    
    request_id = id(request)  # Simple request tracking
    logger.info(f"[Request {request_id}] Starting document analysis")
    logger.info(
        f"[Request {request_id}] Document: name='{request.document_name or 'N/A'}', "
        f"type='{request.document_type or 'N/A'}', length={len(request.document_text):,} chars"
    )
    if request.recipient_email:
        logger.info(f"[Request {request_id}] Email recipient: {request.recipient_email}")
    
    # ========================================
    # STEP 1: Validate Document Text
    # ========================================
    text_length = len(request.document_text)
    if text_length < 50:
        logger.warning(f"[Request {request_id}] Document too short: {text_length} chars")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document text too short ({text_length} chars). Minimum 50 characters required."
        )
    
    if text_length > 100000:
        logger.warning(f"[Request {request_id}] Document too long: {text_length} chars")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document text too long ({text_length} chars). Maximum 100,000 characters allowed."
        )
    
    logger.debug(f"[Request {request_id}] Document validation passed")
    
    # ========================================
    # STEP 2: Perform Fraud Analysis
    # ========================================
    try:
        logger.info(f"[Request {request_id}] Starting AI fraud analysis...")
        
        # Check if Groq is enabled
        from app.core.config import settings
        if not settings.is_groq_enabled():
            logger.error(f"[Request {request_id}] Groq AI integration disabled - cannot perform analysis")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI fraud analysis is currently unavailable. Groq API key is not configured. "
                       "Please contact the administrator to enable this feature."
            )
        
        result = await fraud_agent.analyze_document_async(request.document_text)
        
        logger.info(
            f"[Request {request_id}] Analysis complete: "
            f"Risk={result.risk_level}, "
            f"Flags={len(result.list_of_flags)}, "
            f"Flagged Amount=${result.total_flagged_amount:,.2f}"
        )
        
        # Log high-risk detections
        if result.risk_level == "High":
            logger.warning(
                f"[Request {request_id}] ⚠️ HIGH RISK DETECTED! "
                f"{len(result.list_of_flags)} fraud indicators found"
            )
        
    except ValueError as e:
        logger.error(f"[Request {request_id}] Invalid document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[Request {request_id}] Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing document: {str(e)}"
        )
    
    # ========================================
    # STEP 3: Convert to API Response Format
    # ========================================
    try:
        logger.debug(f"[Request {request_id}] Converting analysis results to API format...")
        
        # Convert fraud flags
        fraud_flags = [
            DocumentFraudFlag(
                category=flag.category,
                severity=flag.severity,
                description=flag.description,
                evidence=flag.evidence,
                confidence=flag.confidence,
                amount_involved=flag.amount_involved
            )
            for flag in result.list_of_flags
        ]
        
        # Build metadata
        metadata = result.document_metadata.copy()
        if request.document_name:
            metadata["document_name"] = request.document_name
        if request.document_type:
            metadata["document_type"] = request.document_type
        
    except Exception as e:
        logger.error(f"[Request {request_id}] Failed to convert results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process analysis results: {str(e)}"
        )
    
    # ========================================
    # STEP 4: Generate Visualizations
    # ========================================
    visualizations = None
    try:
        logger.debug(f"[Request {request_id}] Generating visualization charts...")
        
        from backend.services.visualization import visualization_service
        
        # Create comprehensive dashboard
        dashboard_path = visualization_service.create_comprehensive_dashboard(
            risk_level=result.risk_level,
            total_flagged_amount=result.total_flagged_amount,
            flags=[flag.model_dump() for flag in result.list_of_flags]
        )
        
        # Create individual charts
        flags_chart_path = visualization_service.create_fraud_flags_chart(
            [flag.model_dump() for flag in result.list_of_flags]
        )
        
        severity_chart_path = visualization_service.create_severity_distribution_chart(
            [flag.model_dump() for flag in result.list_of_flags]
        )
        
        risk_summary_path = visualization_service.create_risk_summary_chart(
            risk_level=result.risk_level,
            total_flagged_amount=result.total_flagged_amount,
            flags_count=len(result.list_of_flags)
        )
        
        visualizations = {
            "dashboard": str(dashboard_path),
            "flags_by_category": str(flags_chart_path),
            "severity_distribution": str(severity_chart_path),
            "risk_summary": str(risk_summary_path)
        }
        
        logger.info(f"[Request {request_id}] Visualizations generated: {len(visualizations)} chart(s)")
        
    except Exception as viz_error:
        # Visualization errors are non-critical - log warning but continue
        logger.warning(f"[Request {request_id}] Failed to generate visualizations: {viz_error}")
        visualizations = None
    
    # ========================================
    # STEP 5: Send Email (if recipient provided)
    # ========================================
    email_status = None
    if request.recipient_email:
        try:
            logger.info(
                f"[Request {request_id}] Sending email report to: {request.recipient_email}"
            )
            
            from backend.services.email_service import email_service
            
            email_status = await email_service.send_analysis_report_async(
                recipient_email=request.recipient_email,
                risk_level=result.risk_level,
                summary=result.summary,
                total_flagged_amount=result.total_flagged_amount,
                flags=[flag.model_dump() for flag in result.list_of_flags],
                recommendations=result.recommendations,
                visualizations=visualizations,
                document_name=request.document_name or "Financial Document"
            )
            
            if email_status.get('success'):
                logger.info(
                    f"[Request {request_id}] ✅ Email sent successfully to {request.recipient_email}"
                )
            else:
                logger.warning(
                    f"[Request {request_id}] ❌ Email failed: {email_status.get('message')}"
                )
            
        except Exception as email_error:
            # Email errors are non-critical - log warning but continue
            logger.warning(f"[Request {request_id}] Email sending error: {email_error}")
            email_status = {
                "success": False,
                "message": f"Failed to send email: {str(email_error)}",
                "sent": False
            }
    else:
        logger.debug(f"[Request {request_id}] No email recipient provided - skipping email")
    
    # ========================================
    # STEP 6: Build Final Response
    # ========================================
    try:
        logger.debug(f"[Request {request_id}] Building final API response...")
        
        response = DocumentAuditResponse(
            risk_level=result.risk_level,
            summary=result.summary,
            list_of_flags=fraud_flags,
            recommendations=result.recommendations,
            total_flagged_amount=result.total_flagged_amount,
            document_metadata=metadata,
            visualizations=visualizations,
            email_sent=email_status
        )
        
        logger.info(
            f"[Request {request_id}] ✅ Request completed successfully! "
            f"Risk={response.risk_level}, Flags={len(response.list_of_flags)}, "
            f"Amount=${response.total_flagged_amount:,.2f}, "
            f"Email={'✓' if email_status and email_status.get('success') else '✗'}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"[Request {request_id}] Failed to build response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build response: {str(e)}"
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def document_analysis_info():
    """
    Get information about the document analysis API.
    
    Returns comprehensive documentation about capabilities,
    supported fraud detection types, and usage examples.
    
    Returns:
        Dict with API information and capabilities
    """
    logger.debug("Document analysis info endpoint called")
    
    return {
        "message": "Document-Based Fraud Analysis API",
        "version": "1.0.0",
        "description": "AI-powered fraud detection for financial documents using LangChain and OpenAI",
        "capabilities": {
            "fraud_detection": [
                "Duplicate payments",
                "Inflated costs",
                "Missing approvals",
                "Suspicious vendor behavior",
                "Policy violations",
                "Temporal anomalies"
            ],
            "risk_levels": ["Low", "Medium", "High"],
            "output_types": [
                "Structured JSON analysis",
                "Visualization charts",
                "Email reports (optional)"
            ]
        },
        "limits": {
            "min_document_size": "50 characters",
            "max_document_size": "100,000 characters"
        },
        "workflow": [
            "1. Submit document text",
            "2. AI analyzes for fraud patterns",
            "3. Generate visualization charts",
            "4. Send email if recipient provided",
            "5. Return structured JSON results"
        ],
        "endpoints": {
            "POST /api/v1/document/analyze": "Analyze a full financial document",
            "GET /api/v1/document/": "Get API information",
            "POST /api/v1/document/batch": "Batch analyze multiple documents"
        },
        "documentation": "/docs",
        "example_usage": {
            "python": "requests.post('http://localhost:8000/api/v1/document/analyze', json={'document_text': '...', 'recipient_email': 'auditor@company.com'})"
        }
    }


@router.post("/batch", status_code=status.HTTP_200_OK)
async def batch_analyze_documents(documents: list[DocumentAuditRequest]):
    """
    Analyze multiple documents in batch.
    
    Processes up to 10 documents sequentially, returning results for each.
    Failed documents don't stop processing; errors are included in results.
    
    Args:
        documents: List of DocumentAuditRequest objects (max 10)
        
    Returns:
        Dict with batch results and statistics
        
    Raises:
        HTTPException 400: More than 10 documents provided
    
    Example:
        ```python
        documents = [
            {"document_text": "Document 1..."},
            {"document_text": "Document 2..."}
        ]
        
        response = requests.post(
            "http://localhost:8000/api/v1/document/batch",
            json=documents
        )
        
        results = response.json()
        print(f"Processed: {results['successful']}/{results['total_documents']}")
        ```
    """
    batch_id = id(documents)
    logger.info(f"[Batch {batch_id}] Starting batch analysis of {len(documents)} document(s)")
    
    # Validate batch size
    if len(documents) > 10:
        logger.warning(f"[Batch {batch_id}] Too many documents: {len(documents)} (max: 10)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 documents per batch request"
        )
    
    results = []
    
    # Process each document
    for i, doc in enumerate(documents):
        doc_name = doc.document_name or f"Document {i+1}"
        logger.info(f"[Batch {batch_id}] Processing document {i+1}/{len(documents)}: {doc_name}")
        
        try:
            # Analyze document
            result = await analyze_document(doc)
            
            results.append({
                "document_index": i,
                "document_name": doc_name,
                "success": True,
                "analysis": result
            })
            
            logger.info(
                f"[Batch {batch_id}] Document {i+1} completed: "
                f"Risk={result.risk_level}, Flags={len(result.list_of_flags)}"
            )
            
        except HTTPException as e:
            logger.warning(f"[Batch {batch_id}] Document {i+1} failed: {e.detail}")
            results.append({
                "document_index": i,
                "document_name": doc_name,
                "success": False,
                "error": e.detail,
                "error_code": e.status_code
            })
    
    # Build batch summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    logger.info(
        f"[Batch {batch_id}] Batch completed: "
        f"{successful} successful, {failed} failed"
    )
    
    return {
        "batch_id": batch_id,
        "total_documents": len(documents),
        "successful": successful,
        "failed": failed,
        "results": results
    }
