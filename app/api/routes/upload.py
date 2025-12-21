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
        
        extracted_text, metadata = document_loader_service.process_uploaded_file(
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
        
        # Create comprehensive dashboard
        dashboard_path = visualization_service.create_comprehensive_dashboard(
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
        
        # Merge metadata
        analysis_metadata = analysis_result.document_metadata.copy()
        analysis_metadata.update({
            "original_filename": metadata["original_filename"],
            "file_type": metadata["file_type"],
            "file_size_bytes": metadata["file_size_bytes"],
            "extraction_timestamp": metadata["extraction_timestamp"]
        })
        
        # Build audit response
        audit_response = DocumentAuditResponse(
            risk_level=analysis_result.risk_level,
            summary=analysis_result.summary,
            list_of_flags=fraud_flags,
            recommendations=analysis_result.recommendations,
            total_flagged_amount=analysis_result.total_flagged_amount,
            document_metadata=analysis_metadata,
            visualizations=visualizations,
            email_sent=email_status  # Include email status if email was sent
        )
        
        # Build final response
        response = FileUploadResponse(
            filename=metadata["original_filename"],
            file_type=metadata["file_type"],
            file_size_bytes=metadata["file_size_bytes"],
            extracted_text_length=metadata["extracted_length"],
            analysis=audit_response
        )
        
        logger.info(
            f"[Request {request_id}] Request completed successfully! "
            f"Risk={audit_response.risk_level}, "
            f"Response size: ~{len(str(response.model_dump())):,} bytes"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"[Request {request_id}] Failed to format response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to format response: {str(e)}"
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def upload_info():
    """
    Get information about the file upload API.
    
    Returns comprehensive API documentation including supported formats,
    file size limits, processing workflow, and usage examples.
    
    Returns:
        Dict with API information and capabilities
    """
    logger.debug("File upload info endpoint called")
    
    return {
        "message": "File Upload & Analysis API",
        "version": "1.0.0",
        "description": "Upload financial documents for automated fraud detection",
        "supported_formats": [
            {
                "extension": ".pdf",
                "description": "Adobe PDF documents",
                "loader": "PyPDF2 / LangChain PyPDFLoader",
                "mime_types": ["application/pdf"]
            },
            {
                "extension": ".docx",
                "description": "Microsoft Word documents",
                "loader": "python-docx / LangChain Docx2txtLoader",
                "mime_types": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
            },
            {
                "extension": ".txt",
                "description": "Plain text files",
                "loader": "Direct read / LangChain TextLoader",
                "mime_types": ["text/plain"]
            }
        ],
        "limits": {
            "max_file_size_mb": 10,
            "max_file_size_bytes": 10 * 1024 * 1024,
            "min_text_length": 50,
            "max_text_length": 100000
        },
        "workflow": [
            "1. Upload file (PDF, DOCX, or TXT)",
            "2. Validate file type and size",
            "3. Extract text using LangChain loaders",
            "4. Analyze for fraud with AI agent",
            "5. Generate visualization charts",
            "6. Return structured JSON results"
        ],
        "endpoints": {
            "POST /api/v1/upload/analyze": "Upload and analyze a document",
            "GET /api/v1/upload/": "Get API information",
            "POST /api/v1/upload/cleanup": "Clean up old files"
        },
        "documentation": "/docs",
        "example_usage": {
            "python": "requests.post('http://localhost:8000/api/v1/upload/analyze', files={'file': open('report.pdf', 'rb')})",
            "curl": "curl -X POST http://localhost:8000/api/v1/upload/analyze -F 'file=@report.pdf'"
        }
    }


@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_old_files(max_age_hours: int = 24):
    """
    Clean up old uploaded files from temporary storage.
    
    This maintenance endpoint removes temporary files older than the specified age.
    Useful for periodic cleanup to prevent disk space issues.
    
    Args:
        max_age_hours: Maximum age of files to keep (default: 24 hours)
        
    Returns:
        Dict with cleanup results
        
    Example:
        ```
        POST /api/v1/upload/cleanup?max_age_hours=1
        ```
    """
    logger.info(f"Starting cleanup of files older than {max_age_hours} hours...")
    
    try:
        deleted_count = document_loader_service.cleanup_old_files(max_age_hours)
        
        logger.info(f"Cleanup completed: {deleted_count} file(s) deleted")
        
        return {
            "success": True,
            "message": f"Cleanup completed successfully",
            "files_deleted": deleted_count,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )
