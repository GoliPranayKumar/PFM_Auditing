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

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form, BackgroundTasks
from typing import Optional, Dict, Any
import uuid
import datetime
import traceback
import asyncio
import functools

from app.models.schemas import FileUploadResponse, DocumentFraudFlag, DocumentAuditResponse
from app.services.document_loader import document_loader_service
from app.utils.logger import get_logger
from backend.agent.fraud_agent import FraudDetectionAgent

# Initialize router
router = APIRouter(prefix="/api/v1/upload", tags=["File Upload"])

# Initialize services
fraud_agent = FraudDetectionAgent()
logger = get_logger(__name__)

# In-memory result store (simple dict for MVP)
# Structure: { request_id: { "status": "processing"|"completed"|"failed", "result": ..., "error": ... } }
RESULTS_STORE: Dict[str, Dict[str, Any]] = {}

async def process_document_task(
    request_id: str,
    filename: str,
    file_content: bytes,
    recipient_email: Optional[str]
):
    """
    Background task to process document, analyze fraud, generate visualization, and send email.
    """
    logger.info(f"[Request {request_id}] 🟢 Starting background processing task")
    
    try:
        # Update status
        RESULTS_STORE[request_id] = {
            "status": "processing", 
            "stage": "extracting_text",
            "timestamp": datetime.datetime.now().isoformat()
        }

        # ========================================
        # STEP 1: Process & Extract Text
        # ========================================
        # ========================================
        # STEP 1: Process & Extract Text
        # ========================================
        logger.debug(f"[Request {request_id}] Extracting text from {filename}...")
        
        # Run blocking document loading in thread pool
        loop = asyncio.get_running_loop()
        extracted_text, metadata = await loop.run_in_executor(
            None,
            functools.partial(
                document_loader_service.process_uploaded_file,
                file_content=file_content,
                filename=filename,
                cleanup_after=True
            )
        )
        
        if len(extracted_text) < 50:
            raise ValueError(f"Insufficient text extracted ({len(extracted_text)} chars). Minimum 50 required.")

        # ========================================
        # STEP 2: Fraud Analysis
        # ========================================
        RESULTS_STORE[request_id]["stage"] = "analyzing_fraud"
        logger.info(f"[Request {request_id}] 🤖 Running AI Fraud Analysis...")
        
        analysis_result = await fraud_agent.analyze_document_async(extracted_text)
        
        logger.info(
            f"[Request {request_id}] Analysis complete: Risk={analysis_result.risk_level}, "
            f"Flags={len(analysis_result.list_of_flags)}"
        )

        # ========================================
        # STEP 3: Generate Visualizations
        # ========================================
        RESULTS_STORE[request_id]["stage"] = "generating_visualizations"
        visualizations = None
        
        try:
            # Lazy import to handle missing dependencies gracefully
            from backend.services.visualization import visualization_service
            
            # Run blocking visualization generation in thread pool
            dashboard_path = await loop.run_in_executor(
                None,
                functools.partial(
                    visualization_service.create_comprehensive_dashboard,
                    risk_level=analysis_result.risk_level,
                    total_flagged_amount=analysis_result.total_flagged_amount,
                    flags=[flag.model_dump() for flag in analysis_result.list_of_flags]
                )
            )
            visualizations = {"dashboard": str(dashboard_path)}
            logger.info(f"[Request {request_id}] 📊 Visualizations generated successfully")
            
        except ImportError:
            logger.warning(f"[Request {request_id}] Visualizations skipped: matplotlib/seaborn not installed")
        except Exception as e:
            logger.warning(f"[Request {request_id}] Visualization error (non-fatal): {e}")

        # ========================================
        # STEP 4: Send Email (Critical)
        # ========================================
        email_status = None
        if recipient_email:
            RESULTS_STORE[request_id]["stage"] = "sending_email"
            try:
                logger.info(f"[Request {request_id}] 📧 Preparing email for {recipient_email}...")
                
                from backend.services.email_service import email_service
                
                # Verify email service is configured
                # Verify email service is configured
                if not email_service.is_configured:
                     logger.warning(f"[Request {request_id}] Email service not configured (GMAIL_USER missing)")
                     email_status = {"success": False, "error": "Email service not configured"}
                else:
                    # Run blocking email sending in thread pool
                    # Note: We use the sync `send_analysis_report` method here
                    email_report = await loop.run_in_executor(
                        None,
                        functools.partial(
                            email_service.send_analysis_report,
                            recipient_email=recipient_email,
                            risk_level=analysis_result.risk_level,
                            summary=analysis_result.summary,
                            total_flagged_amount=analysis_result.total_flagged_amount,
                            flags=[flag.model_dump() for flag in analysis_result.list_of_flags],
                            recommendations=analysis_result.recommendations,
                            visualizations=visualizations,
                            document_name=metadata["original_filename"]
                        )
                    )
                    
                    if email_report.get("success"):
                        logger.info(f"[Request {request_id}] ✅ Email sent successfully!")
                        email_status = {"success": True, "message": "Email sent"}
                    else:
                        logger.error(f"[Request {request_id}] ❌ Email failed: {email_report.get('error')}")
                        email_status = {"success": False, "error": email_report.get("error")}
                        
            except Exception as e:
                logger.error(f"[Request {request_id}] Unexpected email error: {e}")
                email_status = {"success": False, "error": str(e)}

        # ========================================
        # STEP 5: Finalize Result
        # ========================================
        RESULTS_STORE[request_id]["stage"] = "completed"
        
        # Format for API response
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

        analysis_metadata = analysis_result.document_metadata.copy()
        analysis_metadata.update({
            "original_filename": metadata["original_filename"],
            "file_type": metadata["file_type"],
            "file_size_bytes": metadata["file_size_bytes"],
            "extraction_timestamp": metadata["extraction_timestamp"]
        })

        audit_response = DocumentAuditResponse(
            risk_level=analysis_result.risk_level,
            summary=analysis_result.summary,
            list_of_flags=fraud_flags,
            recommendations=analysis_result.recommendations,
            total_flagged_amount=analysis_result.total_flagged_amount,
            document_metadata=analysis_metadata,
            visualizations=visualizations,
            email_sent=email_status
        )
        
        RESULTS_STORE[request_id]["status"] = "completed"
        RESULTS_STORE[request_id]["result"] = FileUploadResponse(
            filename=metadata["original_filename"],
            file_type=metadata["file_type"],
            file_size_bytes=metadata["file_size_bytes"],
            extracted_text_length=metadata["extracted_length"],
            analysis=audit_response
        ).model_dump()
        
        logger.info(f"[Request {request_id}] 🏁 Processing task completed successfully")

    except Exception as e:
        logger.error(f"[Request {request_id}] 💥 Task failed: {e}")
        logger.error(traceback.format_exc())
        RESULTS_STORE[request_id]["status"] = "failed"
        RESULTS_STORE[request_id]["error"] = str(e)


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_uploaded_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    recipient_email: Optional[str] = Form(None)
):
    """
    Upload a document for background analysis.
    Returns a request_id for polling status.
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Received upload request. Assigned ID: {request_id}")
    
    try:
        # Read file content immediately (file is closed after request context)
        file_content = await file.read()
        filename = file.filename or "unknown_file"
        
        # Initialize status
        RESULTS_STORE[request_id] = {
            "status": "queued",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Dispatch background task
        background_tasks.add_task(
            process_document_task,
            request_id,
            filename,
            file_content,
            recipient_email
        )
        
        return {
            "status": "processing",
            "request_id": request_id,
            "message": "File uploaded successfully. Processing started in background."
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate upload processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{request_id}")
async def get_analysis_status(request_id: str):
    """
    Check the status of a document analysis request.
    """
    if request_id not in RESULTS_STORE:
        raise HTTPException(status_code=404, detail="Request ID not found")
        
    return RESULTS_STORE[request_id]


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
