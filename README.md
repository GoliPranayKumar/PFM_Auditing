# 🕵️ Audit Agent API

AI-powered audit agent for detecting fraud, waste, and abuse in public expenditure using FastAPI and LangChain.

## 📋 Features

- **AI-Powered Analysis**: Uses OpenAI GPT-3.5-turbo via LangChain for intelligent fraud detection
- **Multiple Input Methods**:
  - **Transaction-Level**: Analyze individual transactions for fraud indicators
  - **Document-Level**: Comprehensive analysis of full financial documents
  - **File Upload**: **🆕** Direct upload of PDF, DOCX, and TXT files
- **Advanced Fraud Detection**:
  - Duplicate payments
  - Inflated costs
  - Missing approvals
  - Suspicious vendor behavior
  - Policy violations
  - Temporal anomalies
- **Document Processing**: LangChain-powered text extraction from multiple formats
- **RESTful API**: Clean FastAPI backend with automatic OpenAPI documentation
- **Modular Architecture**: Well-organized code structure for maintainability
- **Risk Assessment**: Provides risk scores, indicators, and actionable recommendations
- **Structured Output**: JSON-formatted results with evidence and confidence scores
- **Free-Tier Compatible**: Works with OpenAI's free tier limits

## 🏗️ Project Structure

```
audit-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   └── routes/
│   │       ├── health.py          # Health check endpoints
│   │       ├── audit.py           # Transaction audit endpoints
│   │       └── document.py        # Document analysis endpoints
│   ├── core/
│   │   └── config.py              # Application configuration
│   ├── models/
│   │   └── schemas.py             # Pydantic data models
│   ├── services/
│   │   ├── langchain_service.py   # LangChain AI integration
│   │   └── audit_service.py       # Business logic orchestration
│   └── utils/
│       └── helpers.py             # Utility functions
├── backend/
│   └── agent/
│       └── fraud_agent.py         # 🎯 Advanced fraud detection agent
├── examples/
│   └── demo_fraud_agent.py        # Demo script
├── .env.example                   # Environment variables template
├── .gitignore
├── requirements.txt               # Python dependencies
├── README.md
└── FRAUD_AGENT_DOCS.md           # 📖 Detailed fraud agent documentation
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.9 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd audit-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   ```bash
   # Copy the example file
   copy .env.example .env
   
   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

### Running the Application

1. **Start the development server**
   ```bash
   # Option 1: Using uvicorn directly
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Option 2: Using the main.py script
   python -m app.main
   ```

2. **Access the application**
   - API Root: http://localhost:8000
   - Interactive API Docs: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## 📖 API Usage

### 1. Transaction-Level Analysis

Analyze individual transactions for fraud indicators.

**Endpoint:** `POST /api/v1/audit/analyze`

**Request Body:**
```json
{
  "transaction_description": "Payment to ABC Consulting for office supplies",
  "amount": 9999.99,
  "vendor": "ABC Consulting LLC",
  "category": "Office Supplies",
  "additional_context": "Purchase made on Sunday"
}
```

**Response:**
```json
{
  "risk_score": 65.5,
  "risk_level": "high",
  "fraud_indicators": [
    {
      "type": "Suspicious Amount",
      "severity": "medium",
      "description": "Amount just below $10,000 threshold",
      "confidence": 0.75
    }
  ],
  "summary": "Transaction shows multiple fraud indicators...",
  "recommendations": [
    "Verify vendor legitimacy",
    "Review approval documentation"
  ],
  "timestamp": "2025-12-21T02:16:02Z"
}
```

### 2. Document-Level Analysis (🆕 Advanced)

Analyze complete financial documents for comprehensive fraud detection.

**Endpoint:** `POST /api/v1/document/analyze`

**Request Body:**
```json
{
  "document_text": "EXPENDITURE REPORT - Q4 2024\n\nTransaction 1:\nDate: 2024-12-15\nVendor: ABC Consulting LLC\nAmount: $9,995.00\nDescription: IT consulting services\nApproved by: John Smith\n\nTransaction 2:\nDate: 2024-12-15\nVendor: ABC Consulting LLC\nAmount: $9,995.00\nDescription: IT consulting services\nApproved by: John Smith",
  "document_name": "Q4_2024_Report",
  "document_type": "expense_report"
}
```

**Response:**
```json
{
  "risk_level": "High",
  "summary": "Document contains duplicate payments and potential fraud indicators...",
  "list_of_flags": [
    {
      "category": "duplicate_payment",
      "severity": "high",
      "description": "Identical transaction detected",
      "evidence": "Same vendor, amount, and date appearing twice",
      "confidence": 0.95,
      "amount_involved": 9995.00
    },
    {
      "category": "missing_approval",
      "severity": "medium",
      "description": "Potential self-approval detected",
      "evidence": "John Smith appears as both requester and approver",
      "confidence": 0.75,
      "amount_involved": 19990.00
    }
  ],
  "recommendations": [
    "Investigate duplicate payment immediately",
    "Review approval chain for conflicts of interest",
    "Verify vendor legitimacy and services rendered"
  ],
  "total_flagged_amount": 19990.00,
  "document_metadata": {
    "document_length": 245,
    "flags_count": 2,
    "high_severity_count": 1,
    "document_name": "Q4_2024_Report"
  },
  "timestamp": "2025-12-21T02:16:02Z"
}
```

### Example cURL Request

```bash
curl -X POST "http://localhost:8000/api/v1/audit/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "transaction_description": "Emergency IT consulting services",
       "amount": 25000.00,
       "vendor": "Tech Solutions Inc",
       "category": "IT Services"
     }'
```

## 🔒 Security Best Practices

- **Never commit `.env` file** - It's in `.gitignore` by default
- **Use environment variables** for all sensitive data
- **Rotate API keys** regularly
- **Monitor API usage** to stay within free tier limits
- **Validate all inputs** - Pydantic handles this automatically

## 🧪 Testing

Test the health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "app_name": "Audit Agent API",
  "version": "1.0.0",
  "environment": "development"
}
```

## 📊 OpenAI Free Tier Limits

- GPT-3.5-turbo: 3 requests per minute
- Monthly token limits apply
- Monitor usage at: https://platform.openai.com/usage

## 🎯 Fraud Detection Agent

### Quick Demo

Test the advanced fraud detection agent with sample documents:

```bash
cd audit-agent
python examples/demo_fraud_agent.py
```

This will analyze two sample documents (high-risk and low-risk) and show comprehensive fraud analysis reports.

### Direct Usage

```python
from backend.agent.fraud_agent import FraudDetectionAgent

# Initialize agent
agent = FraudDetectionAgent()

# Analyze a document
document = """
EXPENDITURE REPORT - Q4 2024

Transaction 1:
Date: 2024-12-15
Vendor: ABC Consulting LLC
Amount: $9,995.00
...
"""

result = agent.analyze_document(document)

# View results
print(f"Risk Level: {result.risk_level}")
print(f"Flags: {len(result.list_of_flags)}")
print(f"Total Flagged: ${result.total_flagged_amount:,.2f}")

# Generate report
print(agent.get_summary_report(result))
```

### 📚 Detailed Documentation

For comprehensive documentation on the fraud detection agent, see **[FRAUD_AGENT_DOCS.md](FRAUD_AGENT_DOCS.md)**

Topics covered:
- Complete API reference
- Detection capabilities and patterns
- Risk level determination
- Batch processing
- Advanced features
- Best practices
- Troubleshooting

## 🛠️ Development

### Adding New Features

1. **New endpoint**: Add route in `app/api/routes/`
2. **Business logic**: Add service in `app/services/`
3. **Data models**: Define schemas in `app/models/schemas.py`
4. **Configuration**: Update `app/core/config.py`

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add docstrings to functions
- Keep functions focused and modular

## 🐛 Troubleshooting

### "OpenAI API key not configured"
- Ensure `.env` file exists with valid `OPENAI_API_KEY`
- Check that .env is in the `audit-agent` directory

### "Module not found" errors
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### Port already in use
- Change port in `.env`: `API_PORT=8001`
- Or specify when running: `uvicorn app.main:app --port 8001`

## 📝 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📧 Support

For questions or issues, please check the interactive API documentation at `/docs` endpoint.

---

**Built with:** FastAPI | LangChain | OpenAI | Python 3.9+
