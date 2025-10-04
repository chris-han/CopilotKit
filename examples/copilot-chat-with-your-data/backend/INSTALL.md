# Installation Guide

## Quick Start

### 1. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install --no-cache-dir -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file with your API keys:
```env
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
TAVILY_API_KEY=your_tavily_key  # Optional for web search
```

### 4. Run the Application
```bash
# Full-featured server (requires Azure OpenAI)
python main.py

# OR simplified server (no external dependencies)
python main_simple.py
```

### 5. Test the Installation
```bash
curl http://localhost:8004/health
```

## System Features

- **Context-Aware Chart Suggestions**: AI-powered visualization recommendations
- **FOCUS v1.2 Compliance**: FinOps Open Cost & Usage Specification datasets
- **User Preference Learning**: Remembers and improves chart suggestions
- **Dynamic ECharts Generation**: Real-time chart configuration via FastMCP
- **Multi-Dataset Support**: 3 sample FinOps datasets (500-2000 records each)

## API Endpoints

- `GET /health` - System health check
- `GET /finops-web/datasets` - Available FOCUS datasets
- `POST /lida/visualize` - Generate chart suggestions
- `POST /lida/select-chart` - Record user preferences

## Dependencies Overview

The requirements.txt includes 82+ packages organized into:
- **Core FastAPI**: Web framework and server
- **AI/ML**: OpenAI, Pydantic AI for intelligent suggestions
- **Data Processing**: LIDA, Pandas, Plotly for visualization
- **FastMCP**: Dynamic chart generation runtime
- **Security**: Authentication and encryption libraries

## Troubleshooting

**Import Errors**: Ensure you're using the correct Python version (3.8+) and virtual environment
**API Key Issues**: Verify your Azure OpenAI credentials in `.env`
**Port Conflicts**: Check if port 8004 is available: `lsof -i :8004`

For issues, check the logs or use the simplified server (`main_simple.py`) which doesn't require external APIs.