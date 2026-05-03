# TaskFlow — Full-Stack Task Tracker

A beautiful, fast task tracker with real authentication built on **Next.js 14 + MongoDB**.

## Features

- 🔐 Real authentication (Signup / Login) — bcrypt-hashed passwords + JWT
- ✅ Full task CRUD — create, edit, delete, mark complete
- 🏷️ Priority levels (Low / Medium / High) and due dates
- 📊 Dashboard stats — total / active / done / overdue
- 🎨 Modern UI with shadcn/ui + TailwindCSS
- 👥 User-scoped data (each user sees only their own tasks)
- 🗄️ MongoDB persistence

## Tech Stack

- **Frontend + Backend:** Next.js 14 (App Router, API Routes)
- **Database:** MongoDB
- **Auth:** JWT (jsonwebtoken) + bcryptjs
- **UI:** TailwindCSS, shadcn/ui, lucide-react
- **Notifications:** sonner

## Getting Started

### 1. Prerequisites

- Node.js 18+
- Yarn
- A running MongoDB instance (local or Atlas)

### 2. Install

```bash
yarn install
```

### 3. Environment variables

Copy `.env.example` to `.env` and fill in values:

```bash
cp .env.example .env
```

```
MONGO_URL=mongodb://localhost:27017
DB_NAME=task_tracker_db
NEXT_PUBLIC_BASE_URL=http://localhost:3000
JWT_SECRET=replace-with-a-long-random-string
```

### 4. Run dev server

```bash
yarn dev
```

Open http://localhost:3000

### 5. Build for production

```bash
yarn build && yarn start
```

## API Endpoints

All routes are under `/api`.

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET    | `/api/health`        | No  | Health check |
| POST   | `/api/auth/signup`   | No  | `{ email, password, name }` → `{ token, user }` |
| POST   | `/api/auth/login`    | No  | `{ email, password }` → `{ token, user }` |
| GET    | `/api/auth/me`       | Yes | Returns current user |
| GET    | `/api/tasks`         | Yes | List current user's tasks |
| POST   | `/api/tasks`         | Yes | Create `{ title, description?, priority?, dueDate? }` |
| PUT    | `/api/tasks/:id`     | Yes | Update any task field |
| DELETE | `/api/tasks/:id`     | Yes | Delete task |

Auth header: `Authorization: Bearer <JWT>`

## Project Structure

```
app/
├── api/[[...path]]/route.js   # All backend API routes
├── layout.js
├── page.js                    # Auth + Dashboard UI
└── globals.css
components/ui/                 # shadcn components
lib/                           # utils
```

## License

MIT
