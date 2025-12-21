"""LangChain service for AI-powered audit analysis."""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

from app.core.config import settings


class FraudAnalysis(BaseModel):
    """Structured output for fraud analysis."""
    
    risk_score: float = Field(description="Risk score from 0 to 100")
    risk_level: str = Field(description="Risk level: low, medium, high, or critical")
    fraud_indicators: List[dict] = Field(description="List of fraud indicators")
    summary: str = Field(description="Summary of findings")
    recommendations: List[str] = Field(description="List of recommendations")


class LangChainService:
    """Service for AI-powered fraud detection using Groq."""
    
    def __init__(self):
        """Initialize LangChain service with Groq model."""
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",  # Fast and accurate
            temperature=0.2,
            groq_api_key=settings.groq_api_key
        )
        self.parser = PydanticOutputParser(pydantic_object=FraudAnalysis)
        
    def _create_audit_prompt(self) -> ChatPromptTemplate:
        """Create the audit analysis prompt template."""
        
        template = """You are an expert auditor specializing in detecting fraud, waste, and abuse in public expenditure.

Analyze the following financial transaction for potential fraud indicators:

Transaction Details:
- Description: {transaction_description}
- Amount: ${amount}
- Vendor: {vendor}
- Category: {category}
- Additional Context: {additional_context}

Your task:
1. Identify potential fraud, waste, or abuse indicators
2. Assign a risk score (0-100) where:
   - 0-25: Low risk
   - 26-50: Medium risk
   - 51-75: High risk
   - 76-100: Critical risk
3. Classify the risk level as: low, medium, high, or critical
4. Provide specific fraud indicators with type, severity (low/medium/high), description, and confidence (0-1)
5. Summarize your findings
6. Recommend specific actions

Consider these fraud indicators:
- Unusual amounts (round numbers, amounts just below approval thresholds)
- Suspicious vendor patterns (duplicate vendors, unknown vendors)
- Mismatched categories
- Vague or unclear descriptions
- Split transactions to avoid oversight
- Weekend/holiday transactions
- Non-competitive procurement

{format_instructions}

Provide your analysis in the specified JSON format."""

        return ChatPromptTemplate.from_template(template)
    
    async def analyze_transaction(
        self,
        transaction_description: str,
        amount: float,
        vendor: str = "Unknown",
        category: str = "Unspecified",
        additional_context: str = ""
    ) -> FraudAnalysis:
        """
        Analyze a financial transaction for fraud indicators.
        
        Args:
            transaction_description: Description of the transaction
            amount: Transaction amount
            vendor: Vendor name
            category: Expenditure category
            additional_context: Additional context
            
        Returns:
            FraudAnalysis object with risk assessment
        """
        
        prompt = self._create_audit_prompt()
        
        chain = prompt | self.llm | self.parser
        
        result = await chain.ainvoke({
            "transaction_description": transaction_description,
            "amount": amount,
            "vendor": vendor or "Unknown",
            "category": category or "Unspecified",
            "additional_context": additional_context or "None provided",
            "format_instructions": self.parser.get_format_instructions()
        })
        
        return result


# Global service instance
langchain_service = LangChainService()
