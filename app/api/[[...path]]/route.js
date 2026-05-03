import { NextResponse } from 'next/server';
import { MongoClient } from 'mongodb';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';

const MONGO_URL = process.env.MONGO_URL;
const DB_NAME = process.env.DB_NAME || 'task_tracker_db';
const JWT_SECRET = process.env.JWT_SECRET || 'fallback-secret';

let cachedClient = null;
async function getDb() {
  if (!cachedClient) {
    cachedClient = new MongoClient(MONGO_URL);
    await cachedClient.connect();
  }
  return cachedClient.db(DB_NAME);
}

function json(data, status = 200) {
  return NextResponse.json(data, { status });
}

function getTokenFromRequest(request) {
  const auth = request.headers.get('authorization');
  if (auth && auth.startsWith('Bearer ')) return auth.slice(7);
  const cookie = request.headers.get('cookie') || '';
  const m = cookie.match(/(?:^|;\s*)token=([^;]+)/);
  return m ? m[1] : null;
}

async function getUserFromRequest(request) {
  const token = getTokenFromRequest(request);
  if (!token) return null;
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    const db = await getDb();
    const user = await db.collection('users').findOne({ id: decoded.userId });
    return user || null;
  } catch {
    return null;
  }
}

function sanitizeUser(u) {
  if (!u) return null;
  const { password, _id, ...rest } = u;
  return rest;
}

async function handler(request, { params }) {
  const pathArr = params?.path || [];
  const route = '/' + pathArr.join('/');
  const method = request.method;

  try {
    // Health
    if (route === '/' || route === '/health') {
      return json({ status: 'ok', service: 'task-tracker' });
    }

    // ===== AUTH =====
    if (route === '/auth/signup' && method === 'POST') {
      const body = await request.json();
      const { email, password, name } = body || {};
      if (!email || !password || !name) return json({ error: 'email, password, name required' }, 400);
      if (password.length < 6) return json({ error: 'Password must be at least 6 characters' }, 400);
      const db = await getDb();
      const existing = await db.collection('users').findOne({ email: email.toLowerCase() });
      if (existing) return json({ error: 'Email already registered' }, 409);
      const hashed = await bcrypt.hash(password, 10);
      const user = {
        id: uuidv4(),
        email: email.toLowerCase(),
        name,
        password: hashed,
        createdAt: new Date().toISOString(),
      };
      await db.collection('users').insertOne(user);
      const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '7d' });
      return json({ token, user: sanitizeUser(user) });
    }

    if (route === '/auth/login' && method === 'POST') {
      const body = await request.json();
      const { email, password } = body || {};
      if (!email || !password) return json({ error: 'email and password required' }, 400);
      const db = await getDb();
      const user = await db.collection('users').findOne({ email: email.toLowerCase() });
      if (!user) return json({ error: 'Invalid credentials' }, 401);
      const ok = await bcrypt.compare(password, user.password);
      if (!ok) return json({ error: 'Invalid credentials' }, 401);
      const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '7d' });
      return json({ token, user: sanitizeUser(user) });
    }

    if (route === '/auth/me' && method === 'GET') {
      const user = await getUserFromRequest(request);
      if (!user) return json({ error: 'Unauthorized' }, 401);
      return json({ user: sanitizeUser(user) });
    }

    // ===== TASKS =====
    if (route === '/tasks' && method === 'GET') {
      const user = await getUserFromRequest(request);
      if (!user) return json({ error: 'Unauthorized' }, 401);
      const db = await getDb();
      const tasks = await db
        .collection('tasks')
        .find({ userId: user.id })
        .sort({ createdAt: -1 })
        .toArray();
      return json({ tasks: tasks.map(({ _id, ...t }) => t) });
    }

    if (route === '/tasks' && method === 'POST') {
      const user = await getUserFromRequest(request);
      if (!user) return json({ error: 'Unauthorized' }, 401);
      const body = await request.json();
      const { title, description = '', priority = 'medium', dueDate = null } = body || {};
      if (!title) return json({ error: 'title required' }, 400);
      const task = {
        id: uuidv4(),
        userId: user.id,
        title,
        description,
        priority,
        dueDate,
        status: 'todo',
        completed: false,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      const db = await getDb();
      await db.collection('tasks').insertOne(task);
      const { _id, ...rest } = task;
      return json({ task: rest });
    }

    // /tasks/:id
    if (pathArr[0] === 'tasks' && pathArr[1]) {
      const user = await getUserFromRequest(request);
      if (!user) return json({ error: 'Unauthorized' }, 401);
      const id = pathArr[1];
      const db = await getDb();

      if (method === 'PUT' || method === 'PATCH') {
        const body = await request.json();
        const allowed = ['title', 'description', 'priority', 'dueDate', 'status', 'completed'];
        const update = { updatedAt: new Date().toISOString() };
        for (const k of allowed) {
          if (k in body) update[k] = body[k];
        }
        if ('completed' in update) {
          update.status = update.completed ? 'done' : 'todo';
        } else if ('status' in update) {
          update.completed = update.status === 'done';
        }
        const res = await db
          .collection('tasks')
          .findOneAndUpdate(
            { id, userId: user.id },
            { $set: update },
            { returnDocument: 'after' }
          );
        const doc = res.value || res; // driver compat
        if (!doc) return json({ error: 'Not found' }, 404);
        const { _id, ...rest } = doc;
        return json({ task: rest });
      }

      if (method === 'DELETE') {
        const r = await db.collection('tasks').deleteOne({ id, userId: user.id });
        if (r.deletedCount === 0) return json({ error: 'Not found' }, 404);
        return json({ success: true });
      }
    }

    return json({ error: 'Not found', route, method }, 404);
  } catch (err) {
    console.error('API error:', err);
    return json({ error: 'Server error', detail: String(err?.message || err) }, 500);
  }
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
