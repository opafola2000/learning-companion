# Learning Companion Agent

AI-powered learning companion that helps you prepare for professional certification exams. Built with React, FastAPI, AWS Bedrock (Claude), and Tavily search.

## Features

- **Personalized Curriculum Generation** -- enter a certification (e.g., "AWS Certified AI Practitioner") and get a structured learning path with modules and topics
- **Resource Discovery** -- automatically searches the web for tutorials, docs, videos, and practice materials for each topic
- **Practice Quizzes** -- AI-generated exam-style questions with explanations, adapting difficulty to your current level
- **Mastery Tracking** -- tracks your progress across all topics with scores and visual progress indicators
- **Adaptive Learning** -- recommends what to study next based on your weak areas

## Tech Stack

- **Frontend:** React 18, Vite, TailwindCSS, React Router
- **Backend:** Python 3.12, FastAPI, SQLAlchemy, Pydantic
- **AI:** AWS Bedrock (Claude Sonnet for complex tasks, Haiku for simple tasks)
- **Search:** Tavily API
- **Database:** SQLite
- **Deployment:** Docker, AWS App Runner

## Prerequisites

- Python 3.12+
- Node.js 20+
- AWS account with Bedrock access (Claude models enabled)
- Tavily API key ([sign up at tavily.com](https://tavily.com))

## Quick Start (Local Development)

### 1. Clone and set up environment

```bash
cd learning-companion

# Backend setup
cd backend
cp .env.example .env
# Edit .env with your API keys
pip install -r requirements.txt
cd ..

# Frontend setup
cd frontend
npm install
cd ..
```

### 2. Configure your `.env` file

Edit `backend/.env` with your actual keys:

```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
TAVILY_API_KEY=tvly-your-key
JWT_SECRET_KEY=generate-a-random-secret
```

### 3. Run the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Run the frontend

```bash
cd frontend
npm run dev
```

Open http://localhost:3000 in your browser.

## Docker Development

```bash
# Copy and configure .env first
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Run both services
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Deploy to AWS App Runner

### Option A: Container Image (Recommended)

1. Build the production image:
```bash
docker build -t learning-companion .
```

2. Push to ECR:
```bash
aws ecr create-repository --repository-name learning-companion
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker tag learning-companion:latest <account>.dkr.ecr.<region>.amazonaws.com/learning-companion:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/learning-companion:latest
```

3. Create App Runner service:
   - Source: ECR container image
   - Port: 8080
   - CPU: 1 vCPU, Memory: 2 GB
   - Set environment variables: `TAVILY_API_KEY`, `JWT_SECRET_KEY`, `AWS_REGION`
   - Attach IAM instance role with `bedrock:InvokeModel` permission

### Option B: Source Code

1. Push to GitHub
2. Connect repository in App Runner console
3. Use the `apprunner.yaml` configuration
4. Set environment variables in App Runner console

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for the interactive Swagger UI.

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | Create account |
| `POST /api/auth/login` | Login |
| `POST /api/curriculum/generate` | Generate curriculum for a skill |
| `GET /api/curriculum/{id}` | View curriculum details |
| `POST /api/quiz/generate/{topic_id}` | Generate practice quiz |
| `POST /api/quiz/{id}/submit` | Submit quiz answers |
| `GET /api/progress/{curriculum_id}` | View mastery progress |
| `GET /api/progress/recommendations` | Get study recommendations |

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full architecture document.
