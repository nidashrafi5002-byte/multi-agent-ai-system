# MAIA - Multi-Agent Intelligence System

A sophisticated multi-agent AI orchestration system built with LangGraph, featuring 7 specialized agents for various tasks including research, stock analysis, code review, job search, flight tracking, image generation, and general Q&A.

## 🌐 Live Demo

**Frontend**: https://maia-frontend.vercel.app

**Backend**: https://multi-agent-ai-system-nr1g.onrender.com

The application is deployed and ready to use. Visit the frontend URL to interact with all 7 AI agents.

## 🚀 Features

### Core Capabilities
- **7 Specialized Agents**: Research, Stock, Code, Job, Flight, Image, and General agents
- **Multi-Agent Orchestration**: LangGraph-based workflow coordination
- **Vector Database**: ChromaDB for context-aware retrieval
- **Web Search Integration**: Real-time information via SerpAPI
- **Quality Scoring**: Automated evaluation of research reports
- **File Upload Analysis**: Support for PDF, DOCX, TXT, and image files
- **User Authentication**: Secure login/signup with JWT tokens

### Agent Capabilities

#### 🔬 Research Agent
- Conducts deep research with live web sources
- Generates comprehensive reports with citations
- Quality scoring (0-100) for report evaluation
- Source verification and synthesis

#### 📈 Stock Analysis Agent
- Real-time stock market analysis
- Interactive charts with Plotly
- Portfolio insights and market signals
- Support for major stocks (AAPL, GOOG, MSFT, TSLA, NVDA, META, AMZN)

#### 💻 Code Review Agent
- Security-focused code analysis
- Bug detection and patch suggestions
- Best practices recommendations
- Code quality assessment

#### 💼 Job Search Agent
- Job listing aggregation
- Resume matching
- Career guidance
- Skill recommendations

#### ✈️ Flight Tracker Agent
- Real-time flight status
- Route visualization with interactive maps
- Airport information
- Flight delay predictions

#### 🎨 Image Generation Agent
- AI-powered image generation
- Prompt enhancement
- Creative visual content creation

#### 💬 General Q&A Agent
- Conversational AI assistance
- Knowledge base queries
- General problem solving

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance API framework
- **LangGraph**: Multi-agent orchestration
- **LangChain**: LLM integration
- **ChromaDB**: Vector database for memory
- **SQLite**: User authentication database
- **JWT**: Secure authentication tokens
- **bcrypt**: Password hashing
- **Groq**: LLM provider

### Frontend
- **React**: UI framework
- **TypeScript**: Type-safe development
- **TailwindCSS**: Styling (via custom CSS)
- **Lucide Icons**: Icon library
- **Axios**: HTTP client

### Data Processing
- **pypdf**: PDF text extraction
- **python-docx**: DOCX text extraction
- **Pillow**: Image processing
- **Pandas**: Data analysis
- **Plotly**: Interactive charts
- **Folium**: Map visualization

## 📋 Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/nidashrafi5002-byte/multi-agent-ai-system.git
cd multi-agent-ai-system
```

### 2. Backend Setup

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```env
GROQ_API_KEY=your_groq_api_key
SERPAPI_KEY=your_serpapi_key
JWT_SECRET_KEY=your_jwt_secret_key
```

### 3. Frontend Setup

Navigate to frontend directory:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

## 🚀 Running the Application

### Start Backend
```bash
# From project root
python backend/main.py
```

Backend will run on `http://localhost:8000`

### Start Frontend
```bash
# From frontend directory
npm start
```

Frontend will run on `http://localhost:3000`

### Using Streamlit (Alternative)
```bash
# From project root
streamlit run app.py
```

## 🔐 Authentication

The application requires user authentication:

1. Navigate to `http://localhost:3000`
2. Click "Sign up" to create an account
3. Enter your email, username, and password (min 6 characters)
4. Login with your credentials
5. Access all features after authentication

## 📁 Project Structure

```
multi-agent-ai-system/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── chat.py              # Chat API endpoints
│   └── routes/
│       ├── auth.py          # Authentication endpoints
│       └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── chatService.ts
│   │   │   └── authService.ts
│   │   ├── pages/
│   │   │   ├── ChatPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── SignupPage.tsx
│   │   │   └── ...
│   │   ├── components/
│   │   └── App.tsx
│   └── package.json
├── agents/                  # Agent implementations
├── pipelines/               # Pipeline orchestration
├── workflows/               # Workflow definitions
├── memory/                  # ChromaDB and auth database
├── app.py                   # Streamlit application
├── requirements.txt         # Python dependencies
└── README.md
```

## 🎯 Usage Examples

### Research Agent
```
Query: "Write executive summary on quantum computing"
Output: Comprehensive research report with quality score
```

### Stock Analysis
```
Query: "Analyze Apple stock performance"
Output: Analysis with interactive stock chart
```

### Code Review
```
Query: "Review this code for security issues"
Output: Security analysis with recommendations
```

### File Upload
```
Upload: PDF, DOCX, TXT, or image file
Output: Extracted content with analysis options
```

## 🔑 API Keys Required

- **Groq API Key**: For LLM operations
  - Get from: https://console.groq.com/
- **SerpAPI Key**: For web search
  - Get from: https://serpapi.com/
- **JWT Secret Key**: For authentication (generate your own)

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Chat
- `POST /api/chat` - Send chat message
- `POST /api/analyze-file` - Analyze uploaded file

### Health
- `GET /api/health` - Health check

## 🧪 Testing

Run backend tests:
```bash
pytest tests/
```

Run frontend tests:
```bash
npm test
```

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |
| `SERPAPI_KEY` | SerpAPI key for web search | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Yes |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature-name`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

**Nida Fatima Ashrafi**
- GitHub: [@nidashrafi5002-byte](https://github.com/nidashrafi5002-byte)
- LinkedIn: [linkedin.com/in/nida-ashrafi](https://linkedin.com/in/nida-ashrafi)

## 🙏 Acknowledgments

- LangChain team for the excellent framework
- Groq for fast LLM inference
- SerpAPI for web search capabilities
- The open-source community

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Contact: nidashrafi5002@gmail.com

---

**Built with ❤️ using LangGraph, FastAPI, and React**
