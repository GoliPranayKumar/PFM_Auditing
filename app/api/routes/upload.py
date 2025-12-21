"""
File upload and analysis endpoints.

API Flow:
1. User uploads document (PDF, DOCX, or TXT)
2. Validate file type and size
3. Extract text using LangChain loaders
4. Analyze for fraud using AI agent
5. Generate visualization charts
6. Send email if recipient provided
7. Return structured JSON response
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form
from typing import Optional
from starlette.concurrency import run_in_threadpool

from app.models.schemas import FileUploadResponse, DocumentFraudFlag, DocumentAuditResponse
from app.services.document_loader import document_loader_service
from app.utils.logger import get_logger
from backend.agent.fraud_agent import FraudDetectionAgent

# Initialize router
router = APIRouter(prefix="/api/v1/upload", tags=["File Upload"])

# Initialize services
fraud_agent = FraudDetectionAgent()
logger = get_logger(__name__)


@router.post("/analyze", response_model=FileUploadResponse)
async def analyze_uploaded_document(
    file: UploadFile = File(...),
    recipient_email: Optional[str] = Form(None)
):
    """Upload and analyze a financial document with optional email report."""
    
    request_id = id(file)  # Simple request tracking
    logger.info(f"[Request {request_id}] Starting file upload analysis")
    logger.info(f"[Request {request_id}] Filename: {file.filename}, Content-Type: {file.content_type}")
    if recipient_email:
        logger.info(f"[Request {request_id}] Email report will be sent to: {recipient_email}")
    
    # ========================================
    # STEP 1: Read File Content
    # ========================================
    try:
        logger.debug(f"[Request {request_id}] Reading uploaded file content...")
        file_content = await file.read()
        file_size = len(file_content)
        logger.info(f"[Request {request_id}] File read successfully: {file_size:,} bytes")
        
    except Exception as e:
        logger.error(f"[Request {request_id}] Failed to read file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )
    
    # ========================================
    # STEP 2: Validate and Extract Text
    # ========================================
    try:
        logger.debug(f"[Request {request_id}] Validating file and extracting text...")
        
        # Run blocking file processing in threadpool
        extracted_text, metadata = await run_in_threadpool(
            document_loader_service.process_uploaded_file,
            file_content=file_content,
            filename=file.filename or "unknown.txt",
            cleanup_after=True  # Auto-delete temporary file
        )
        
        logger.info(
            f"[Request {request_id}] Text extracted successfully: "
            f"{metadata['extracted_length']:,} characters from {metadata['file_type']} file"
        )
        
    except ValueError as e:
        # Validation error (invalid file type or size)
        logger.warning(f"[Request {request_id}] File validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Extraction error
        logger.error(f"[Request {request_id}] Text extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from document: {str(e)}"
        )
    
    # Verify sufficient text was extracted
    if len(extracted_text) < 50:
        logger.warning(
            f"[Request {request_id}] Insufficient text extracted: "
            f"{len(extracted_text)} chars (minimum: 50)"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient text extracted ({len(extracted_text)} chars). Minimum 50 characters required."
        )
    
    # ========================================
    # STEP 3: Perform Fraud Analysis
    # ========================================
    try:
        logger.info(f"[Request {request_id}] Starting fraud analysis with AI agent...")
        
        # Truncate text if too long to prevent timeouts/OOM
        MAX_CHARS = 100000
        if len(extracted_text) > MAX_CHARS:
            logger.warning(f"[Request {request_id}] Truncating text from {len(extracted_text)} to {MAX_CHARS} chars")
            extracted_text = extracted_text[:MAX_CHARS] + "... [TRUNCATED]"

        analysis_result = await fraud_agent.analyze_document_async(extracted_text)
        
        logger.info(
            f"[Request {request_id}] Analysis complete: "
            f"Risk={analysis_result.risk_level}, "
            f"Flags={len(analysis_result.list_of_flags)}, "
            f"Amount=${analysis_result.total_flagged_amount:,.2f}"
        )
        
    except Exception as e:
        logger.error(f"[Request {request_id}] Fraud analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fraud analysis failed: {str(e)}"
        )
    
    # ========================================
    # STEP 4: Generate Visualizations
    # ========================================
    visualizations = None
    try:
        logger.debug(f"[Request {request_id}] Generating visualization charts...")
        
        from backend.services.visualization import visualization_service
        
        # Run blocking visualization in threadpool
        dashboard_path = await run_in_threadpool(
            visualization_service.create_comprehensive_dashboard,
            risk_level=analysis_result.risk_level,
            total_flagged_amount=analysis_result.total_flagged_amount,
            flags=[flag.model_dump() for flag in analysis_result.list_of_flags]
        )
        
        visualizations = {
            "dashboard": str(dashboard_path),
        }
        
        logger.info(f"[Request {request_id}] Visualizations generated: {len(visualizations)} chart(s)")
        
    except Exception as viz_error:
        # Visualization errors are non-critical - log but continue
        logger.warning(f"[Request {request_id}] Failed to generate visualizations: {viz_error}")
    
    # ========================================
    # STEP 5: Send Email Report (Optional)
    # ========================================
    email_status = None
    if recipient_email:
        try:
            logger.info(f"[Request {request_id}] Sending email report to: {recipient_email}")
            
            from backend.services.email_service import email_service
            
            # Send email with visualizations
            email_result = await email_service.send_analysis_report_async(
                recipient_email=recipient_email,
                risk_level=analysis_result.risk_level,
                summary=analysis_result.summary,
                total_flagged_amount=analysis_result.total_flagged_amount,
                flags=[flag.model_dump() for flag in analysis_result.list_of_flags],
                recommendations=analysis_result.recommendations,
                visualizations=visualizations,
                document_name=metadata["original_filename"]
            )
            
            email_status = {
                "success": email_result["success"],
                "recipient": recipient_email,
                "message": email_result.get("message", "Email sent successfully")
            }
            
            if email_result["success"]:
                logger.info(f"[Request {request_id}] ✅ Email sent successfully to {recipient_email}")
            else:
                logger.warning(f"[Request {request_id}] ⚠️ Email sending failed: {email_result.get('error')}")
                email_status["error"] = email_result.get("error")
                
        except Exception as email_error:
            logger.warning(f"[Request {request_id}] Failed to send email: {email_error}")
            email_status = {
                "success": False,
                "recipient": recipient_email,
                "error": str(email_error)
            }
    
    # ========================================
    # STEP 6: Build Response
    # ========================================
    try:
        logger.debug(f"[Request {request_id}] Building API response...")
        
        # Convert fraud flags to response format
        fraud_flags = [
            DocumentFraudFlag(
                category=flag.category,
                severity=flag.severity,
                description=flag.description,
                evidence=flag.evidence,
                confidence=flag.confidence,
                amount_involved=flag.amount_involved
            )
            for flag in analysis_result.list_of_flags
        ]
        
        # Build final response
        response = FileUploadResponse(
            filename=metadata["original_filename"],
            file_type=metadata["file_type"],
            file_size_bytes=file_size,
            extracted_text_length=len(extracted_text),
            analysis=DocumentAuditResponse(
                risk_level=analysis_result.risk_level,
                summary=analysis_result.summary,
                total_flagged_amount=analysis_result.total_flagged_amount,
                list_of_flags=fraud_flags,
                recommendations=analysis_result.recommendations,
                visualizations=visualizations,
                email_sent=email_status
            )
        )
        
        logger.info(f"[Request {request_id}] Analysis completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"[Request {request_id}] Failed to build response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build response: {str(e)}"
        )
