"""
Advanced LangChain-based fraud detection agent for public financial auditing.

This agent analyzes extracted document text to detect fraud, waste, and abuse
patterns in public expenditure with comprehensive compliance checking.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
import json


class FraudFlag(BaseModel):
    """Individual fraud indicator or compliance issue."""
    
    category: str = Field(
        description="Category of the flag: 'duplicate_payment', 'inflated_cost', "
                    "'missing_approval', 'suspicious_vendor', 'policy_violation', or 'other'"
    )
    severity: str = Field(
        description="Severity level: 'low', 'medium', or 'high'"
    )
    description: str = Field(
        description="Detailed description of the identified issue"
    )
    evidence: str = Field(
        description="Specific evidence from the document supporting this flag"
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0",
        ge=0.0,
        le=1.0
    )
    amount_involved: Optional[float] = Field(
        None,
        description="Dollar amount involved in this issue, if applicable"
    )


class FraudAnalysisResult(BaseModel):
    """Structured output for complete fraud analysis."""
    
    risk_level: str = Field(
        description="Overall risk assessment: 'Low', 'Medium', or 'High'"
    )
    summary: str = Field(
        description="Executive summary of the audit findings (2-3 sentences)"
    )
    list_of_flags: List[FraudFlag] = Field(
        description="Detailed list of all identified fraud indicators and compliance issues"
    )
    recommendations: List[str] = Field(
        description="Prioritized list of recommended actions to address issues"
    )
    total_flagged_amount: float = Field(
        description="Total dollar amount of flagged transactions"
    )
    document_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the analysis"
    )


class FraudDetectionAgent:
    """
    Advanced AI agent for detecting fraud, waste, and abuse in public financial documents.
    
    This agent uses LangChain with OpenAI to perform comprehensive auditing of financial
    documents, identifying patterns of fraud, waste, abuse, and compliance violations.
    """
    
    SYSTEM_PROMPT = """You are a highly experienced public financial auditor and forensic accountant with over 20 years of experience in detecting fraud, waste, and abuse in government and public sector expenditures.

Your expertise includes:
- Government Accountability Office (GAO) auditing standards
- Federal and state procurement regulations
- Anti-fraud controls and risk assessment
- Forensic accounting and pattern recognition
- Public sector compliance and ethics

Your mission is to analyze financial documents with extreme scrutiny to protect public funds and ensure accountability.

CRITICAL FRAUD INDICATORS TO DETECT:

1. DUPLICATE PAYMENTS:
   - Same vendor, amount, and description appearing multiple times
   - Invoice numbers that repeat
   - Identical payment dates to the same vendor
   - Round-robin duplicate payments with slight variations
   - Split payments that when combined match previous payments

2. INFLATED COSTS:
   - Prices significantly above market rates
   - Sudden price increases without justification
   - Non-competitive pricing
   - Prices just below competitive bidding thresholds
   - Excessive unit costs
   - Unusual bulk discounts (negative discounts)

3. MISSING APPROVALS:
   - Transactions without proper authorization signatures
   - Payments exceeding authorized limits
   - Missing purchase orders or requisitions
   - Bypassed approval workflows
   - Retroactive approvals
   - Self-approvals by requesters

4. SUSPICIOUS VENDOR BEHAVIOR:
   - Vendors with PO boxes instead of physical addresses
   - Multiple vendors with same address or phone number
   - Vendors with similar names (shell companies)
   - New vendors without proper vetting
   - Sole-source awards without justification
   - Vendors with conflicts of interest
   - Unusual payment patterns (e.g., payments on weekends/holidays)

5. POLICY VIOLATIONS:
   - Exceeding single-transaction limits
   - Split purchases to avoid approval thresholds
   - Missing competitive bids
   - Inappropriate use of emergency procurement
   - Personal purchases masked as official expenses
   - Violation of spending policies
   - Lack of supporting documentation

6. TEMPORAL ANOMALIES:
   - Rush payments without justification
   - Payments during non-business hours
   - Year-end spending spikes
   - Suspicious timing patterns

7. DOCUMENTATION RED FLAGS:
   - Altered or modified documents
   - Missing invoices or receipts
   - Vague or generic descriptions
   - Incomplete vendor information
   - Photocopied signatures

RISK LEVEL DETERMINATION:

- HIGH RISK: 
  * Multiple fraud indicators present
  * Large dollar amounts involved (>$10,000)
  * Evidence of intentional deception
  * Pattern of recurring issues
  * Senior official involvement
  
- MEDIUM RISK:
  * 1-2 fraud indicators
  * Moderate amounts ($1,000-$10,000)
  * Possible procedural violations
  * Requires investigation
  
- LOW RISK:
  * Minor procedural issues
  * Small amounts (<$1,000)
  * Likely administrative errors
  * Correctable through training

ANALYSIS APPROACH:
1. Read the document thoroughly
2. Identify all transactions and their details
3. Look for patterns across multiple transactions
4. Cross-reference vendor information
5. Check for policy compliance
6. Assess timing and authorization
7. Calculate total exposure
8. Provide specific, actionable recommendations

Be thorough, objective, and evidence-based. Assume the document may contain fraud - your job is to find it."""

    USER_PROMPT_TEMPLATE = """Analyze the following financial document for fraud, waste, and abuse:

DOCUMENT TEXT:
{document_text}

ANALYSIS INSTRUCTIONS:
1. Carefully review all transactions, vendors, amounts, and dates
2. Identify ALL fraud indicators based on the categories provided
3. For each flag, provide specific evidence from the document
4. Assess overall risk level (Low/Medium/High)
5. Provide actionable recommendations prioritized by impact

{format_instructions}

Perform a comprehensive audit analysis now."""

    def __init__(
        self,
        model_name: str = "llama-3.3-70b-versatile",
        temperature: float = 0.1,
        api_key: Optional[str] = None
    ):
        """
        Initialize the fraud detection agent with Groq.
        
        Args:
            model_name: Groq model to use (default: llama-3.3-70b-versatile - fast and accurate)
            temperature: Model temperature for consistency (low = more consistent)
            api_key: Groq API key (if not provided, uses centralized config)
            
        Raises:
            RuntimeError: If Groq API key is not configured
        """
        # Use centralized configuration (NEVER use os.getenv directly)
        from app.core.config import get_groq_api_key
        
        self.api_key = api_key or get_groq_api_key()
        if not self.api_key:
            raise RuntimeError(
                "Groq API key not configured. "
                "AI fraud analysis is disabled. "
                "Please set GROQ_API_KEY in your .env file to enable this feature."
            )
        
        # Initialize the LLM with Groq (much faster than OpenAI!)
        self.llm = ChatGroq(
            model=model_name,
            temperature=temperature,
            groq_api_key=self.api_key,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        # Set up output parser for structured results
        self.output_parser = PydanticOutputParser(pydantic_object=FraudAnalysisResult)
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("user", self.USER_PROMPT_TEMPLATE)
        ])
        
        # Build the analysis chain
        self.chain = (
            {
                "document_text": RunnablePassthrough(),
                "format_instructions": lambda _: self.output_parser.get_format_instructions()
            }
            | self.prompt
            | self.llm
            | self.output_parser
        )
    
    def analyze_document(
        self,
        document_text: str,
        max_retries: int = 3
    ) -> FraudAnalysisResult:
        """
        Analyze a financial document for fraud, waste, and abuse.
        
        Args:
            document_text: Extracted text from the financial document
            max_retries: Number of retries if analysis fails
            
        Returns:
            FraudAnalysisResult containing risk level, flags, and recommendations
            
        Raises:
            ValueError: If document_text is empty or invalid
            Exception: If analysis fails after retries
        """
        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty")
        
        if len(document_text) < 50:
            raise ValueError(
                "Document text too short. Provide complete financial document content."
            )
        
        # Attempt analysis with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                result = self.chain.invoke(document_text)
                
                # Validate result
                if not result.list_of_flags and result.risk_level != "Low":
                    # If high/medium risk but no flags, something's wrong
                    result.risk_level = "Low"
                    result.summary = "Document reviewed - no significant issues detected."
                
                # Add metadata
                result.document_metadata = {
                    "document_length": len(document_text),
                    "flags_count": len(result.list_of_flags),
                    "analysis_model": self.llm.model_name,
                    "high_severity_count": sum(
                        1 for flag in result.list_of_flags if flag.severity == "high"
                    )
                }
                
                return result
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    continue
        
        raise Exception(f"Analysis failed after {max_retries} attempts: {last_error}")
    
    async def analyze_document_async(
        self,
        document_text: str,
        max_retries: int = 3
    ) -> FraudAnalysisResult:
        """
        Asynchronously analyze a financial document.
        
        Args:
            document_text: Extracted text from the financial document
            max_retries: Number of retries if analysis fails
            
        Returns:
            FraudAnalysisResult containing risk level, flags, and recommendations
        """
        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty")
        
        last_error = None
        for attempt in range(max_retries):
            try:
                result = await self.chain.ainvoke(document_text)
                
                # Add metadata
                result.document_metadata = {
                    "document_length": len(document_text),
                    "flags_count": len(result.list_of_flags),
                    "analysis_model": self.llm.model_name,
                    "high_severity_count": sum(
                        1 for flag in result.list_of_flags if flag.severity == "high"
                    )
                }
                
                return result
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    continue
        
        raise Exception(f"Async analysis failed after {max_retries} attempts: {last_error}")
    
    def batch_analyze(
        self,
        documents: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple documents in batch.
        
        Args:
            documents: List of dicts with 'id' and 'text' keys
            
        Returns:
            List of analysis results with document IDs
        """
        results = []
        
        for doc in documents:
            doc_id = doc.get("id", "unknown")
            doc_text = doc.get("text", "")
            
            try:
                analysis = self.analyze_document(doc_text)
                results.append({
                    "document_id": doc_id,
                    "success": True,
                    "analysis": analysis.model_dump()
                })
            except Exception as e:
                results.append({
                    "document_id": doc_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def export_results_to_json(
        self,
        result: FraudAnalysisResult,
        filepath: str
    ) -> None:
        """
        Export analysis results to JSON file.
        
        Args:
            result: FraudAnalysisResult object
            filepath: Path to save JSON file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
    
    def get_summary_report(self, result: FraudAnalysisResult) -> str:
        """
        Generate a human-readable summary report.
        
        Args:
            result: FraudAnalysisResult object
            
        Returns:
            Formatted text report
        """
        report = f"""
{'='*80}
FRAUD DETECTION AUDIT REPORT
{'='*80}

RISK LEVEL: {result.risk_level.upper()}
Total Flagged Amount: ${result.total_flagged_amount:,.2f}
Number of Issues: {len(result.list_of_flags)}

EXECUTIVE SUMMARY:
{result.summary}

DETAILED FINDINGS:
"""
        for i, flag in enumerate(result.list_of_flags, 1):
            report += f"""
{i}. {flag.category.upper().replace('_', ' ')} - {flag.severity.upper()} SEVERITY
   Description: {flag.description}
   Evidence: {flag.evidence}
   Confidence: {flag.confidence * 100:.1f}%
   Amount: ${flag.amount_involved:,.2f if flag.amount_involved else 0}
"""
        
        report += f"""
RECOMMENDATIONS:
"""
        for i, rec in enumerate(result.recommendations, 1):
            report += f"{i}. {rec}\n"
        
        report += f"""
{'='*80}
Analysis completed using {result.document_metadata.get('analysis_model', 'N/A')}
Document length: {result.document_metadata.get('document_length', 0):,} characters
High severity issues: {result.document_metadata.get('high_severity_count', 0)}
{'='*80}
"""
        return report


# Convenience function for quick analysis
def analyze_document_for_fraud(
    document_text: str,
    api_key: Optional[str] = None
) -> FraudAnalysisResult:
    """
    Convenience function to quickly analyze a document.
    
    Args:
        document_text: The financial document text to analyze
        api_key: Optional OpenAI API key
        
    Returns:
        FraudAnalysisResult with complete analysis
    """
    agent = FraudDetectionAgent(api_key=api_key)
    return agent.analyze_document(document_text)


if __name__ == "__main__":
    # Example usage
    sample_document = """
    EXPENDITURE REPORT - Q4 2024
    
    Transaction 1:
    Date: 2024-12-15
    Vendor: ABC Consulting LLC
    Amount: $9,995.00
    Description: IT consulting services
    Approved by: John Smith
    
    Transaction 2:
    Date: 2024-12-15
    Vendor: ABC Consulting LLC
    Amount: $9,995.00
    Description: IT consulting services
    Approved by: John Smith
    
    Transaction 3:
    Date: 2024-12-20
    Vendor: XYZ Supplies Inc
    Amount: $45,000.00
    Description: Office supplies
    Approved by: [PENDING]
    
    Transaction 4:
    Date: 2024-12-25
    Vendor: Quick Services Ltd
    PO Box: 12345
    Amount: $15,000.00
    Description: Emergency maintenance
    Approved by: Self-approved
    """
    
    print("Running fraud detection analysis...")
    print("="*80)
    
    try:
        agent = FraudDetectionAgent()
        result = agent.analyze_document(sample_document)
        
        print(agent.get_summary_report(result))
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure OPENAI_API_KEY is set in your environment variables.")
