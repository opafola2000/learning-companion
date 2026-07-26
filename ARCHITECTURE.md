# Learning Companion Agent -- Architecture & Build Plan

## 1. Project Overview

The Learning Companion Agent is a full-stack AI-powered application that helps users prepare for professional certification exams (e.g., AWS Certified AI Practitioner). It builds personalized curricula, discovers learning resources, generates practice quizzes, and adapts the learning path based on mastery tracking.

### Tech Stack

| Layer        | Technology                                         |
| ------------ | -------------------------------------------------- |
| Frontend     | React 18+, Vite, TailwindCSS, React Router, Axios  |
| Backend      | Python 3.12, FastAPI, Uvicorn, SQLAlchemy, Pydantic |
| AI           | AWS Bedrock -- Claude Sonnet 5 (complex tasks), Claude Haiku 4.5 (simple tasks) |
| Web Search   | Tavily Python SDK (`tavily-python`)                |
| Auth         | JWT (passlib + python-jose), bcrypt password hashing |
| Database     | SQLite (local dev), portable to RDS for production |
| Deployment   | Docker, Docker Compose (local), AWS App Runner (production) |

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Frontend                               │
│                                                                     │
│  ┌──────────┐ ┌───────────┐ ┌────────┐ ┌──────────┐ ┌───────────┐ │
│  │  Auth     │ │ Dashboard │ │  Quiz  │ │Curriculum│ │ Progress  │ │
│  │  Pages    │ │           │ │   UI   │ │  View    │ │  Tracker  │ │
│  └──────────┘ └───────────┘ └────────┘ └──────────┘ └───────────┘ │
│                          │ REST API (JSON) │                        │
└──────────────────────────┼─────────────────┼────────────────────────┘
                           │                 │
┌──────────────────────────┼─────────────────┼────────────────────────┐
│                     FastAPI Backend                                  │
│                                                                     │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────────┐│
│  │ Auth Service  │  │Curriculum Eng. │  │  Resource Finder         ││
│  │ (JWT tokens)  │  │                │  │                          ││
│  └──────────────┘  └───────┬────────┘  └────────┬─────────────────┘│
│                            │                     │                  │
│  ┌──────────────┐  ┌──────┴────────┐  ┌─────────┴────────────────┐│
│  │Quiz Engine   │  │Mastery Tracker│  │  Adaptive Path Engine    ││
│  │              │  │               │  │                          ││
│  └──────┬───────┘  └──────┬────────┘  └──────────────────────────┘│
│         │                 │                                        │
└─────────┼─────────────────┼────────────────────────────────────────┘
          │                 │
    ┌─────┴─────┐    ┌──────┴──────┐    ┌──────────────┐
    │  AWS       │    │  SQLite     │    │   Tavily     │
    │  Bedrock   │    │  Database   │    │   Search API │
    │  (Claude)  │    │             │    │              │
    └───────────┘    └─────────────┘    └──────────────┘
```

### Data Flow

1. **User enters a skill** (e.g., "AWS Certified AI Practitioner") via the React frontend.
2. **Backend receives the request** and orchestrates:
   - Tavily searches for the official exam guide/blueprint.
   - Bedrock Claude Sonnet generates a structured curriculum grounded in the exam objectives.
   - The curriculum (modules, topics, difficulty levels) is stored in SQLite.
3. **For each topic**, the user can:
   - **Discover resources** -- Tavily searches, Bedrock summarizes and ranks.
   - **Take quizzes** -- Bedrock generates exam-format questions, Haiku grades answers.
   - **Track progress** -- mastery scores update, adaptive engine adjusts the path.

---

## 3. Project Structure

```
learning-companion/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point, CORS, lifespan
│   │   ├── config.py               # Pydantic Settings (env vars, API keys)
│   │   ├── database.py             # SQLAlchemy engine, session, Base
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User table
│   │   │   ├── curriculum.py       # Curriculum, Module, Topic tables
│   │   │   ├── resource.py         # Resource table
│   │   │   ├── quiz.py             # Quiz, Question, AnswerOption tables
│   │   │   └── progress.py         # QuizAttempt, UserAnswer, TopicMastery
│   │   ├── routers/                # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # POST /register, /login, /refresh
│   │   │   ├── curriculum.py       # POST /generate, GET /, GET /{id}
│   │   │   ├── resources.py        # POST /search/{topic_id}, GET /{topic_id}
│   │   │   ├── quiz.py             # POST /generate/{topic_id}, GET /{id}, POST /submit
│   │   │   └── progress.py         # GET /{curriculum_id}, GET /recommendations
│   │   ├── services/               # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── bedrock_client.py   # AWS Bedrock wrapper (Sonnet + Haiku)
│   │   │   ├── tavily_client.py    # Tavily search wrapper
│   │   │   ├── curriculum_service.py  # Curriculum generation logic
│   │   │   ├── resource_service.py    # Resource discovery + summarization
│   │   │   ├── quiz_service.py        # Quiz generation + grading
│   │   │   └── mastery_service.py     # Mastery scoring + adaptive path
│   │   └── schemas/                # Pydantic request/response schemas
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── curriculum.py
│   │       ├── quiz.py
│   │       └── progress.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.tsx                # React DOM entry point
│   │   ├── App.tsx                 # Root component with routing
│   │   ├── api/                    # Axios client + endpoint functions
│   │   │   ├── client.ts           # Axios instance with auth interceptor
│   │   │   ├── auth.ts
│   │   │   ├── curriculum.ts
│   │   │   ├── quiz.ts
│   │   │   └── progress.ts
│   │   ├── components/             # Reusable UI components
│   │   │   ├── Navbar.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   ├── TopicCard.tsx
│   │   │   ├── QuestionCard.tsx
│   │   │   ├── MasteryBadge.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   ├── pages/                  # Route-level page components
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── CurriculumBuilder.tsx
│   │   │   ├── CurriculumView.tsx
│   │   │   ├── Quiz.tsx
│   │   │   └── Progress.tsx
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx      # Auth state + token management
│   │   └── hooks/
│   │       └── useApi.ts            # Data fetching hook
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── docker-compose.yml              # Local dev: frontend + backend
├── Dockerfile                      # Production: combined build
├── apprunner.yaml                  # AWS App Runner configuration
├── ARCHITECTURE.md                 # This file
└── README.md
```

---

## 4. Database Schema

### Tables and Relationships

```
User (1) ───── (*) Curriculum
                     │
                     ├── (1) ───── (*) Module
                     │                   │
                     │                   └── (1) ───── (*) Topic
                     │                                    │
                     │                          ┌─────────┼─────────┐
                     │                          │         │         │
                     │                     (*) Resource  (*) Quiz  (*) TopicMastery
                     │                                    │              ▲
                     │                          (*) Question             │
                     │                                    │         User (1) ── (*)
                     │                          (*) AnswerOption
                     │
User (1) ───── (*) QuizAttempt
                     │
                (*) UserAnswer
```

### Table Definitions

**User**
| Column          | Type     | Constraints      |
| --------------- | -------- | ---------------- |
| id              | INTEGER  | PK, auto         |
| email           | VARCHAR  | UNIQUE, NOT NULL |
| hashed_password | VARCHAR  | NOT NULL         |
| name            | VARCHAR  | NOT NULL         |
| created_at      | DATETIME | default=now      |

**Curriculum**
| Column             | Type     | Constraints      |
| ------------------ | -------- | ---------------- |
| id                 | INTEGER  | PK, auto         |
| user_id            | INTEGER  | FK -> User.id    |
| skill_name         | VARCHAR  | NOT NULL         |
| description        | TEXT     |                  |
| overall_structure   | JSON    |                  |
| created_at         | DATETIME | default=now      |

**Module**
| Column        | Type     | Constraints          |
| ------------- | -------- | -------------------- |
| id            | INTEGER  | PK, auto             |
| curriculum_id | INTEGER  | FK -> Curriculum.id  |
| title         | VARCHAR  | NOT NULL             |
| description   | TEXT     |                      |
| order_index   | INTEGER  | NOT NULL             |
| status        | VARCHAR  | default="not_started"|

**Topic**
| Column      | Type     | Constraints        |
| ----------- | -------- | ------------------ |
| id          | INTEGER  | PK, auto           |
| module_id   | INTEGER  | FK -> Module.id    |
| title       | VARCHAR  | NOT NULL           |
| description | TEXT     |                    |
| order_index | INTEGER  | NOT NULL           |
| difficulty  | VARCHAR  | beginner/intermediate/advanced |
| status      | VARCHAR  | default="not_started"|

**Resource**
| Column   | Type    | Constraints       |
| -------- | ------- | ----------------- |
| id       | INTEGER | PK, auto          |
| topic_id | INTEGER | FK -> Topic.id    |
| title    | VARCHAR | NOT NULL          |
| url      | VARCHAR | NOT NULL          |
| type     | VARCHAR | article/video/doc/lab |
| summary  | TEXT    |                   |

**Quiz**
| Column        | Type     | Constraints       |
| ------------- | -------- | ----------------- |
| id            | INTEGER  | PK, auto          |
| topic_id      | INTEGER  | FK -> Topic.id    |
| quiz_type     | VARCHAR  | practice/assessment |
| num_questions | INTEGER  | NOT NULL          |
| created_at    | DATETIME | default=now       |

**Question**
| Column        | Type    | Constraints      |
| ------------- | ------- | ---------------- |
| id            | INTEGER | PK, auto         |
| quiz_id       | INTEGER | FK -> Quiz.id    |
| question_text | TEXT    | NOT NULL         |
| explanation   | TEXT    |                  |
| difficulty    | VARCHAR | beginner/intermediate/advanced |

**AnswerOption**
| Column      | Type    | Constraints         |
| ----------- | ------- | ------------------- |
| id          | INTEGER | PK, auto            |
| question_id | INTEGER | FK -> Question.id   |
| option_text | TEXT    | NOT NULL            |
| is_correct  | BOOLEAN | NOT NULL            |

**QuizAttempt**
| Column   | Type     | Constraints      |
| -------- | -------- | ---------------- |
| id       | INTEGER  | PK, auto         |
| user_id  | INTEGER  | FK -> User.id    |
| quiz_id  | INTEGER  | FK -> Quiz.id    |
| score    | FLOAT    | NOT NULL         |
| taken_at | DATETIME | default=now      |

**UserAnswer**
| Column             | Type    | Constraints              |
| ------------------ | ------- | ------------------------ |
| id                 | INTEGER | PK, auto                 |
| attempt_id         | INTEGER | FK -> QuizAttempt.id     |
| question_id        | INTEGER | FK -> Question.id        |
| selected_option_id | INTEGER | FK -> AnswerOption.id    |
| is_correct         | BOOLEAN | NOT NULL                 |

**TopicMastery**
| Column         | Type     | Constraints       |
| -------------- | -------- | ----------------- |
| id             | INTEGER  | PK, auto          |
| user_id        | INTEGER  | FK -> User.id     |
| topic_id       | INTEGER  | FK -> Topic.id    |
| mastery_score  | FLOAT    | default=0.0       |
| attempts_count | INTEGER  | default=0         |
| last_assessed  | DATETIME |                   |

---

## 5. API Endpoints

### Authentication

| Method | Endpoint              | Description                    | Auth Required |
| ------ | --------------------- | ------------------------------ | ------------- |
| POST   | `/api/auth/register`  | Register a new user            | No            |
| POST   | `/api/auth/login`     | Login, returns JWT tokens      | No            |
| POST   | `/api/auth/refresh`   | Refresh an expired access token| No (refresh token) |

### Curriculum

| Method | Endpoint                       | Description                           | Auth Required |
| ------ | ------------------------------ | ------------------------------------- | ------------- |
| GET    | `/api/curriculum`              | List all curricula for current user   | Yes           |
| POST   | `/api/curriculum/generate`     | Generate a new curriculum for a skill | Yes           |
| GET    | `/api/curriculum/{id}`         | Get full curriculum with modules/topics | Yes         |

### Resources

| Method | Endpoint                            | Description                              | Auth Required |
| ------ | ----------------------------------- | ---------------------------------------- | ------------- |
| POST   | `/api/resources/search/{topic_id}`  | Search and save resources for a topic    | Yes           |
| GET    | `/api/resources/{topic_id}`         | Get saved resources for a topic          | Yes           |

### Quizzes

| Method | Endpoint                          | Description                            | Auth Required |
| ------ | --------------------------------- | -------------------------------------- | ------------- |
| POST   | `/api/quiz/generate/{topic_id}`   | Generate a new quiz for a topic        | Yes           |
| GET    | `/api/quiz/{quiz_id}`             | Get quiz with questions and options    | Yes           |
| POST   | `/api/quiz/{quiz_id}/submit`      | Submit answers, returns score + feedback | Yes         |

### Progress

| Method | Endpoint                              | Description                              | Auth Required |
| ------ | ------------------------------------- | ---------------------------------------- | ------------- |
| GET    | `/api/progress/{curriculum_id}`       | Get mastery scores for all topics        | Yes           |
| GET    | `/api/progress/recommendations`       | Get adaptive learning recommendations    | Yes           |

---

## 6. Core Feature Design

### 6.1 Curriculum Generation

**Flow:**
1. User submits a skill name (e.g., "AWS Certified AI Practitioner").
2. Tavily searches for the official exam guide and key learning objectives.
3. Bedrock Claude Sonnet receives:
   - The skill name
   - The exam guide content from Tavily
   - A structured prompt requesting modules, topics, difficulty tagging, and ordering
4. Claude returns a JSON curriculum structure.
5. Backend parses and persists the curriculum, modules, and topics to the database.

**Prompt strategy:** The system prompt instructs Claude to act as an expert curriculum designer. It must output a JSON object with a defined schema to ensure reliable parsing.

### 6.2 Resource Discovery

**Flow:**
1. User clicks "Find Resources" on a topic.
2. Backend constructs targeted search queries from the topic title and context.
3. Tavily executes the search (max 10 results per query).
4. Bedrock Claude Haiku summarizes each resource and assigns a relevance score.
5. Results are saved to the Resource table and returned to the frontend.

**Resource types tracked:** article, video, official documentation, hands-on lab, practice exam.

### 6.3 Quiz Engine

**Flow:**
1. User requests a quiz for a topic.
2. Bedrock Claude Sonnet generates questions in JSON format:
   - 5-10 multiple-choice questions per quiz
   - 4 answer options each, one correct
   - Difficulty matched to user's current mastery level
   - Explanations for each correct answer
3. Questions are stored in the database.
4. User takes the quiz in the frontend.
5. On submission, backend scores the attempt and Bedrock Claude Haiku generates personalized feedback.
6. Mastery scores are updated.

**Question types:**
- Standard multiple choice (single correct answer)
- True/False
- Scenario-based (a paragraph of context followed by a question)

### 6.4 Mastery Tracking and Adaptive Learning

**Mastery score algorithm:**
- Each quiz attempt contributes to the topic's mastery score.
- Formula: weighted average with recency bias -- recent attempts count more.
- Score range: 0% to 100%.

**Mastery thresholds:**
| Score Range | Status       | Action                                    |
| ----------- | ------------ | ----------------------------------------- |
| 0-30%       | Needs Study  | Flag for immediate attention, easy quizzes |
| 31-59%      | In Progress  | Standard quizzes, additional resources     |
| 60-79%      | Proficient   | Harder quizzes, less resource pushing      |
| 80-100%     | Mastered     | Deprioritize, schedule spaced review       |

**Adaptive path logic (via Bedrock Claude):**
- Analyzes the user's mastery scores across all topics.
- Identifies weak areas and suggests a study order.
- Generates harder questions for topics approaching mastery.
- Schedules review quizzes for mastered topics using spaced repetition intervals (1 day, 3 days, 7 days, 14 days, 30 days).

---

## 7. Authentication Design

**Mechanism:** JWT-based stateless authentication.

**Token structure:**
- **Access token:** Short-lived (30 minutes), used for API requests.
- **Refresh token:** Long-lived (7 days), used to obtain new access tokens.

**Password handling:**
- Hashed with bcrypt via `passlib`.
- Never stored or transmitted in plaintext.

**Protected routes:**
- FastAPI dependency injection (`get_current_user`) extracts and validates the JWT from the `Authorization: Bearer <token>` header.
- All endpoints except `/auth/register`, `/auth/login`, and `/auth/refresh` require a valid access token.

---

## 8. AI Integration Details

### AWS Bedrock Configuration

**Models used:**

| Model              | Model ID (Bedrock)                  | Use Cases                                    | Cost (per 1M tokens) |
| ------------------ | ----------------------------------- | -------------------------------------------- | -------------------- |
| Claude Sonnet 5    | `anthropic.claude-sonnet-5-v1`      | Curriculum generation, quiz creation, adaptive analysis | $2/$10 (promo) |
| Claude Haiku 4.5   | `anthropic.claude-haiku-4-5-v1`     | Quiz grading, resource summarization, quick feedback    | $1/$5            |

**Bedrock client pattern:**
- Uses `boto3` with the `bedrock-runtime` client.
- Calls `invoke_model` with the Anthropic messages API format.
- All prompts enforce JSON output via system prompts for reliable parsing.
- Timeout and retry logic for resilience.

### Tavily Integration

**Search strategy:**
- `search_depth="advanced"` for curriculum generation (higher relevance).
- `search_depth="basic"` for resource discovery (faster, cheaper).
- `max_results=10` for resource searches, `max_results=5` for exam guide lookups.
- Domain filtering where applicable (e.g., `include_domains=["aws.amazon.com"]` for AWS exams).

---

## 9. Deployment

### Local Development

```yaml
# docker-compose.yml runs:
# - backend: FastAPI on port 8000
# - frontend: Vite dev server on port 3000 (proxies API to backend)
```

**Requirements:**
- Docker and Docker Compose installed.
- `.env` file with API keys (AWS credentials, Tavily key, JWT secret).
- Run: `docker-compose up --build`

### Production (AWS App Runner)

**Strategy:** Single container that serves both the React static build and the FastAPI backend.

**Build process:**
1. Frontend: `npm run build` produces static files in `frontend/dist/`.
2. Backend: FastAPI serves the static files via `StaticFiles` mount and handles API routes.
3. Single Dockerfile combines both steps.

**App Runner configuration:**
- Source: ECR container image (pushed via CI/CD or manual `docker push`).
- Port: **8080** (App Runner default).
- CPU: 1 vCPU, Memory: 2 GB (sufficient for this workload).
- IAM instance role: must have `bedrock:InvokeModel` permission.
- Environment variables: `TAVILY_API_KEY`, `JWT_SECRET_KEY`, `AWS_REGION` set in App Runner console.

**Scaling:**
- Min instances: 1 (keeps the app warm).
- Max instances: 5 (handles traffic spikes).
- Auto-scaling based on concurrent requests.

---

## 10. Environment Variables

| Variable               | Required | Description                                | Default                           |
| ---------------------- | -------- | ------------------------------------------ | --------------------------------- |
| `AWS_REGION`           | Yes      | AWS region for Bedrock API                 | `us-east-1`                       |
| `AWS_ACCESS_KEY_ID`    | Local    | AWS access key (use IAM role on App Runner)| --                                |
| `AWS_SECRET_ACCESS_KEY`| Local    | AWS secret key (use IAM role on App Runner)| --                                |
| `TAVILY_API_KEY`       | Yes      | Tavily API key for web search              | --                                |
| `JWT_SECRET_KEY`       | Yes      | Secret for signing JWT tokens              | --                                |
| `DATABASE_URL`         | No       | Database connection string                 | `sqlite:///./learning_companion.db` |
| `CORS_ORIGINS`         | No       | Allowed CORS origins                       | `http://localhost:3000`           |
| `BEDROCK_SONNET_MODEL` | No       | Bedrock model ID for complex tasks         | `anthropic.claude-sonnet-5-v1`    |
| `BEDROCK_HAIKU_MODEL`  | No       | Bedrock model ID for simple tasks          | `anthropic.claude-haiku-4-5-v1`   |

---

## 11. Estimated Costs

### LLM Usage (AWS Bedrock)

Assuming ~20 interactions per study session, ~30 sessions/month:

| Strategy                         | Monthly Cost  |
| -------------------------------- | ------------- |
| Haiku 4.5 only                   | ~$0.06-0.12   |
| Sonnet 5 only (promo rate)       | ~$0.12-0.30   |
| Mixed Sonnet + Haiku (recommended)| ~$0.08-0.20  |

### Tavily Search

Free tier: 1,000 searches/month. Paid plans start at $20/month for higher volume.

### AWS App Runner Hosting

- Minimum: ~$5-7/month (1 vCPU, 2 GB, 1 instance).
- Scales with traffic.

### Total Estimated Monthly Cost (MVP)

**$6-10/month** for a single active learner (dominated by App Runner hosting).

---

## 12. Build Order

The implementation follows this sequence, where each step builds on the previous:

| Step | Component                           | Dependencies         |
| ---- | ----------------------------------- | -------------------- |
| 1    | Backend scaffold + config + database | None                |
| 2    | Auth system (user model, JWT, routes)| Step 1              |
| 3    | Bedrock client wrapper               | Step 1              |
| 4    | Tavily client wrapper                | Step 1              |
| 5    | Curriculum service + routes          | Steps 2, 3, 4      |
| 6    | Resource service + routes            | Steps 3, 4         |
| 7    | Quiz service + routes                | Steps 2, 3         |
| 8    | Mastery tracking + adaptive engine   | Steps 2, 3, 7      |
| 9    | Frontend scaffold + auth pages       | Step 2              |
| 10   | Frontend dashboard + curriculum UI   | Steps 5, 9         |
| 11   | Frontend quiz UI                     | Steps 7, 9         |
| 12   | Frontend progress UI                 | Steps 8, 9         |
| 13   | Docker + local deployment            | Steps 1-12         |
| 14   | App Runner deployment                | Step 13            |
