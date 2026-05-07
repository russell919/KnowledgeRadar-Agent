/**
 * Knowledge Radar — SQLite Database Layer
 *
 * Stores messages, entities, relations, knowledge items, and more.
 * Uses sql.js (pure JavaScript SQLite) for zero native dependencies.
 */

import initSqlJs from 'sql.js';
import fs from 'fs';
import os from 'os';
import path from 'path';

// ── Schema ──────────────────────────────────────────────────────────────────

const CREATE_TABLES = `
CREATE TABLE IF NOT EXISTS messages (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id    TEXT UNIQUE NOT NULL,
  chat_id       TEXT NOT NULL,
  sender_id     TEXT NOT NULL,
  sender_name   TEXT DEFAULT '',
  content       TEXT NOT NULL,
  msg_type      TEXT DEFAULT 'text',
  metadata_json TEXT DEFAULT '{}',
  created_at    TEXT NOT NULL,
  ingested_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS entities (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id       TEXT UNIQUE NOT NULL,
  entity_type     TEXT NOT NULL,
  name            TEXT NOT NULL,
  aliases_json    TEXT DEFAULT '[]',
  properties_json TEXT DEFAULT '{}',
  first_seen_at   TEXT,
  last_seen_at    TEXT,
  mention_count   INTEGER DEFAULT 1,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS relations (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  source_entity_id TEXT NOT NULL,
  target_entity_id TEXT NOT NULL,
  relation_type    TEXT NOT NULL,
  weight           REAL DEFAULT 1.0,
  metadata_json    TEXT DEFAULT '{}',
  source_message_id TEXT,
  created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS knowledge_items (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  knowledge_id    TEXT UNIQUE NOT NULL,
  knowledge_type  TEXT NOT NULL,
  title           TEXT NOT NULL,
  summary         TEXT NOT NULL,
  content         TEXT DEFAULT '',
  key_points_json TEXT DEFAULT '[]',
  source_refs_json TEXT DEFAULT '[]',
  confidence      REAL DEFAULT 0.5,
  status          TEXT DEFAULT 'active',
  workspace_id    TEXT DEFAULT 'default',
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS source_objects (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id     TEXT UNIQUE NOT NULL,
  source_type   TEXT NOT NULL,
  title         TEXT NOT NULL,
  content       TEXT DEFAULT '',
  metadata_json TEXT DEFAULT '{}',
  author        TEXT DEFAULT '',
  url           TEXT DEFAULT '',
  workspace_id  TEXT DEFAULT 'default',
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_profiles (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id             TEXT UNIQUE NOT NULL,
  user_name           TEXT DEFAULT '',
  role_tags_json      TEXT DEFAULT '[]',
  topic_interest_json TEXT DEFAULT '[]',
  muted_topics_json   TEXT DEFAULT '[]',
  push_preference_json TEXT DEFAULT '{}',
  push_enabled        INTEGER DEFAULT 1,
  metadata_json       TEXT DEFAULT '{}',
  updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS push_events (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  push_id           TEXT UNIQUE NOT NULL,
  execution_id      TEXT NOT NULL,
  scene_type        TEXT NOT NULL,
  user_id           TEXT NOT NULL,
  content_title     TEXT NOT NULL,
  content_summary   TEXT NOT NULL,
  knowledge_ids_json TEXT DEFAULT '[]',
  status            TEXT DEFAULT 'pending',
  push_channel      TEXT DEFAULT 'feishu_im',
  workspace_id      TEXT DEFAULT 'default',
  dry_run           INTEGER DEFAULT 0,
  created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS feedback_events (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  feedback_id   TEXT UNIQUE NOT NULL,
  push_id       TEXT,
  user_id       TEXT NOT NULL,
  feedback_type TEXT NOT NULL,
  content       TEXT DEFAULT '',
  metadata_json TEXT DEFAULT '{}',
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id          TEXT UNIQUE NOT NULL,
  scene_type      TEXT NOT NULL,
  trigger_type    TEXT DEFAULT 'manual',
  status          TEXT DEFAULT 'running',
  input_summary   TEXT DEFAULT '{}',
  output_summary  TEXT DEFAULT '{}',
  total_receivers INTEGER DEFAULT 0,
  push_count      INTEGER DEFAULT 0,
  error           TEXT,
  duration_ms     INTEGER,
  workspace_id    TEXT DEFAULT 'default',
  started_at      TEXT NOT NULL DEFAULT (datetime('now')),
  completed_at    TEXT
);

CREATE TABLE IF NOT EXISTS processed_events (
  event_id      TEXT PRIMARY KEY,
  event_type    TEXT NOT NULL,
  processed_at  TEXT NOT NULL DEFAULT (datetime('now')),
  event_data    TEXT
);

CREATE TABLE IF NOT EXISTS document_versions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  doc_id        TEXT NOT NULL,
  doc_title     TEXT NOT NULL,
  version       INTEGER NOT NULL,
  content       TEXT DEFAULT '',
  content_hash  TEXT DEFAULT '',
  author        TEXT DEFAULT '',
  change_summary TEXT DEFAULT '',
  metadata_json TEXT DEFAULT '{}',
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS faq_candidates (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  question        TEXT NOT NULL,
  answer          TEXT DEFAULT '',
  source_ids_json TEXT DEFAULT '[]',
  confidence      REAL DEFAULT 0.5,
  frequency       INTEGER DEFAULT 1,
  tags_json       TEXT DEFAULT '[]',
  status          TEXT DEFAULT 'candidate',
  project         TEXT DEFAULT '',
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS document_chunks (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  doc_id          TEXT NOT NULL,
  doc_title       TEXT DEFAULT '',
  chunk_index     INTEGER NOT NULL,
  content         TEXT DEFAULT '',
  summary         TEXT DEFAULT '',
  embedding       TEXT DEFAULT '',
  metadata_json   TEXT DEFAULT '{}',
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS message_batch_summaries (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id           TEXT NOT NULL,
  batch_id          TEXT NOT NULL,
  start_message_id  TEXT DEFAULT '',
  end_message_id    TEXT DEFAULT '',
  message_count     INTEGER DEFAULT 0,
  summary           TEXT DEFAULT '',
  topics_json       TEXT DEFAULT '[]',
  decisions_json    TEXT DEFAULT '[]',
  risks_json        TEXT DEFAULT '[]',
  action_items_json TEXT DEFAULT '[]',
  metadata_json     TEXT DEFAULT '{}',
  created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_items(knowledge_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_status ON knowledge_items(status);
CREATE INDEX IF NOT EXISTS idx_push_user ON push_events(user_id);
CREATE INDEX IF NOT EXISTS idx_push_scene ON push_events(scene_type);
CREATE INDEX IF NOT EXISTS idx_source_type ON source_objects(source_type);
`;

// ── Database Class ──────────────────────────────────────────────────────────

let SQL = null;

const DB_PATH = process.env.KR_DB_PATH || path.join(os.homedir(), '.openclaw', 'workspace', 'knowledge-radar', 'backend-server', 'knowledge.db');

function persistDb(db) {
  try {
    const dir = path.dirname(DB_PATH);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    const data = db.export();
    fs.writeFileSync(DB_PATH, Buffer.from(data));
  } catch (e) {
    console.error('[DB] Persist error:', e.message);
  }
}

export async function initDatabase() {
  SQL = await initSqlJs();
  let db;
  if (fs.existsSync(DB_PATH)) {
    const data = fs.readFileSync(DB_PATH);
    db = new SQL.Database(data);
    console.log('[DB] Loaded database from', DB_PATH);
  } else {
    db = new SQL.Database();
    console.log('[DB] Created new database at', DB_PATH);
  }
  db.run('PRAGMA journal_mode=WAL');
  db.run('PRAGMA foreign_keys=ON');
  for (const stmt of CREATE_TABLES.split(';').filter(s => s.trim())) {
    db.run(stmt + ';');
  }
  console.log('[DB] Database initialized with all tables');
  return db;
}

export function persistDatabase(db) {
  persistDb(db);
}

// ── Utilities ───────────────────────────────────────────────────────────────

function uuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

function escape(val) {
  if (typeof val === 'number') return String(val);
  if (val === null || val === undefined) return 'NULL';
  return `'${String(val).replace(/'/g, "''")}'`;
}

export function exec(db, sql, params = []) {
  // sql.js's db.exec doesn't support parameterized queries directly
  // So we prepare, bind, then use db.run with ? params
  if (params.length > 0) {
    db.run(sql, params);
    return;
  }
  db.run(sql);
}

export function query(db, sql, params = []) {
  // Use prepare to get rows back
  const stmt = db.prepare(sql);
  if (params.length > 0) stmt.bind(params);
  
  const rows = [];
  while (stmt.step()) {
    rows.push(stmt.getAsObject());
  }
  stmt.free();
  return rows;
}

function queryOne(db, sql, params = []) {
  const rows = query(db, sql, params);
  return rows.length > 0 ? rows[0] : null;
}

function lastId(db) {
  const r = db.exec("SELECT last_insert_rowid() as id");
  return r.length > 0 ? r[0].values[0][0] : null;
}

function count(db, table, condition = '') {
  const r = db.exec(`SELECT COUNT(*) as c FROM ${table} ${condition}`);
  return r.length > 0 ? r[0].values[0][0] : 0;
}

// ── Message Operations ──────────────────────────────────────────────────────

export function insertMessage(db, msg) {
  const existing = queryOne(db, 'SELECT id FROM messages WHERE message_id = ?', [msg.message_id]);
  if (existing) return existing.id;
  
  exec(db,
    `INSERT OR IGNORE INTO messages (message_id, chat_id, sender_id, sender_name, content, msg_type, metadata_json, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    [msg.message_id, msg.chat_id, msg.sender_id, msg.sender_name || '',
     msg.content, msg.msg_type || 'text',
     JSON.stringify(msg.metadata || {}),
     msg.created_at || new Date().toISOString()]
  );
  persistDb(db);
  return lastId(db);
}

export function getMessagesByChat(db, chatId, limit = 50, offset = 0) {
  return query(db, 'SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
    [chatId, limit, offset]);
}

export function getMessagesSince(db, sinceISO, limit = 200) {
  return query(db, 'SELECT * FROM messages WHERE created_at >= ? ORDER BY created_at ASC LIMIT ?',
    [sinceISO, limit]);
}

export function getMessageCount(db) {
  return count(db, 'messages');
}

// ── Entity Operations ───────────────────────────────────────────────────────

export function upsertEntity(db, entity) {
  const existing = queryOne(db, 'SELECT id, mention_count FROM entities WHERE entity_id = ?', [entity.entity_id]);
  if (existing) {
    exec(db,
      `UPDATE entities SET last_seen_at = datetime('now'), mention_count = mention_count + 1,
       aliases_json = ?, properties_json = ? WHERE entity_id = ?`,
      [JSON.stringify(entity.aliases || []), JSON.stringify(entity.properties || {}), entity.entity_id]
    );
    return existing.id;
  }
  exec(db,
    `INSERT INTO entities (entity_id, entity_type, name, aliases_json, properties_json, first_seen_at, last_seen_at)
     VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))`,
    [entity.entity_id, entity.entity_type, entity.name,
     JSON.stringify(entity.aliases || []), JSON.stringify(entity.properties || {})]
  );
  return lastId(db);
}

export function getEntity(db, entityId) {
  return queryOne(db, 'SELECT * FROM entities WHERE entity_id = ?', [entityId]);
}

export function searchEntities(db, queryText, type = null, limit = 20) {
  let sql = 'SELECT * FROM entities WHERE name LIKE ?';
  const params = [`%${queryText}%`];
  if (type) { sql += ' AND entity_type = ?'; params.push(type); }
  sql += ' ORDER BY mention_count DESC LIMIT ?';
  params.push(limit);
  return query(db, sql, params);
}

export function getAllEntities(db, type = null, limit = 100) {
  let sql = 'SELECT * FROM entities';
  const params = [];
  if (type) { sql += ' WHERE entity_type = ?'; params.push(type); }
  sql += ' ORDER BY mention_count DESC LIMIT ?';
  params.push(limit);
  return query(db, sql, params);
}

// ── Relation Operations ─────────────────────────────────────────────────────

export function insertRelation(db, rel) {
  exec(db,
    `INSERT INTO relations (source_entity_id, target_entity_id, relation_type, weight, metadata_json, source_message_id)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [rel.source_entity_id, rel.target_entity_id, rel.relation_type,
     rel.weight || 1.0, JSON.stringify(rel.metadata || {}), rel.source_message_id || null]
  );
  persistDb(db);
}

export function getRelationsForEntity(db, entityId, limit = 50) {
  return query(db,
    `SELECT r.*, e1.name as source_name, e2.name as target_name,
            e1.entity_type as source_type, e2.entity_type as target_type
     FROM relations r
     JOIN entities e1 ON r.source_entity_id = e1.entity_id
     JOIN entities e2 ON r.target_entity_id = e2.entity_id
     WHERE r.source_entity_id = ? OR r.target_entity_id = ?
     ORDER BY r.weight DESC LIMIT ?`,
    [entityId, entityId, limit]
  );
}

export function getEntityGraph(db, limit = 200) {
  return query(db,
    `SELECT r.*, e1.name as source_name, e2.name as target_name,
            e1.entity_type as source_type, e2.entity_type as target_type
     FROM relations r
     JOIN entities e1 ON r.source_entity_id = e1.entity_id
     JOIN entities e2 ON r.target_entity_id = e2.entity_id
     ORDER BY r.weight DESC LIMIT ?`,
    [limit]
  );
}

// ── Knowledge Item Operations ───────────────────────────────────────────────

export function insertKnowledgeItem(db, item) {
  const kid = item.knowledge_id || `k_${uuid().slice(0, 12)}`;
  exec(db,
    `INSERT OR IGNORE INTO knowledge_items (knowledge_id, knowledge_type, title, summary, content, key_points_json, source_refs_json, confidence, status, workspace_id)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [kid, item.knowledge_type, item.title, item.summary, item.content || '',
     JSON.stringify(item.key_points || []), JSON.stringify(item.source_refs || []),
     item.confidence || 0.5, item.status || 'active', item.workspace_id || 'default']
  );
  persistDb(db);
  return kid;
}

export function getKnowledgeByType(db, type, limit = 50) {
  return query(db,
    `SELECT * FROM knowledge_items WHERE knowledge_type = ? AND status = 'active' ORDER BY updated_at DESC LIMIT ?`,
    [type, limit]
  );
}

export function getRecentKnowledge(db, limit = 50) {
  return query(db,
    `SELECT * FROM knowledge_items WHERE status = 'active' ORDER BY updated_at DESC LIMIT ?`,
    [limit]
  );
}

export function searchKnowledge(db, queryText, limit = 20) {
  return query(db,
    `SELECT * FROM knowledge_items WHERE (title LIKE ? OR summary LIKE ? OR content LIKE ?) AND status = 'active' ORDER BY confidence DESC LIMIT ?`,
    [`%${queryText}%`, `%${queryText}%`, `%${queryText}%`, limit]
  );
}

// ── Source Object Operations ────────────────────────────────────────────────

export function upsertSourceObject(db, obj) {
  exec(db,
    `INSERT OR REPLACE INTO source_objects (source_id, source_type, title, content, metadata_json, author, url, workspace_id, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`,
    [obj.source_id, obj.source_type, obj.title, obj.content || '',
     JSON.stringify(obj.metadata || {}), obj.author || '',
     obj.url || '', obj.workspace_id || 'default']
  );
  persistDb(db);
}

export function getSourceObjectsByType(db, type, limit = 50) {
  return query(db,
    `SELECT * FROM source_objects WHERE source_type = ? ORDER BY updated_at DESC LIMIT ?`,
    [type, limit]
  );
}

// ── User Profile Operations ─────────────────────────────────────────────────

export function upsertUserProfile(db, profile) {
  exec(db,
    `INSERT OR REPLACE INTO user_profiles (user_id, user_name, role_tags_json, topic_interest_json, muted_topics_json, push_preference_json, push_enabled, metadata_json, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`,
    [profile.user_id, profile.user_name || '',
     JSON.stringify(profile.role_tags || []),
     JSON.stringify(profile.topic_interest || []),
     JSON.stringify(profile.muted_topics || []),
     JSON.stringify(profile.push_preference || {}),
     profile.push_enabled !== undefined ? (profile.push_enabled ? 1 : 0) : 1,
     JSON.stringify(profile.metadata || {})]
  );
  persistDb(db);
}

export function getUserProfile(db, userId) {
  return queryOne(db, 'SELECT * FROM user_profiles WHERE user_id = ?', [userId]);
}

// ── Push Event Operations ───────────────────────────────────────────────────

export function insertPushEvent(db, push) {
  const pid = push.push_id || `push_${uuid().slice(0, 12)}`;
  exec(db,
    `INSERT INTO push_events (push_id, execution_id, scene_type, user_id, content_title, content_summary, knowledge_ids_json, status, push_channel, workspace_id, dry_run)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [pid, push.execution_id, push.scene_type, push.user_id,
     push.content_title, push.content_summary,
     JSON.stringify(push.knowledge_ids || []),
     push.status || 'pending', push.push_channel || 'feishu_im',
     push.workspace_id || 'default', push.dry_run ? 1 : 0]
  );
  return pid;
}

export function getPushHistory(db, userId = null, limit = 20) {
  let sql = 'SELECT * FROM push_events';
  const params = [];
  if (userId) { sql += ' WHERE user_id = ?'; params.push(userId); }
  sql += ' ORDER BY created_at DESC LIMIT ?';
  params.push(limit);
  return query(db, sql, params);
}

// ── Event Dedup ─────────────────────────────────────────────────────────────

export function isEventProcessed(db, eventId) {
  const r = queryOne(db, 'SELECT 1 as c FROM processed_events WHERE event_id = ?', [eventId]);
  return !!r;
}

export function markEventProcessed(db, eventId, eventType, eventData = {}) {
  exec(db, 'INSERT OR IGNORE INTO processed_events (event_id, event_type, event_data) VALUES (?, ?, ?)',
    [eventId, eventType, JSON.stringify(eventData)]);
  persistDb(db);
}

// ── Agent Run Operations ────────────────────────────────────────────────────

export function createAgentRun(db, run) {
  const rid = run.run_id || `exec_${uuid().slice(0, 12)}`;
  exec(db,
    `INSERT INTO agent_runs (run_id, scene_type, trigger_type, status, input_summary, workspace_id)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [rid, run.scene_type, run.trigger_type || 'manual', 'running',
     JSON.stringify(run.input_summary || {}), run.workspace_id || 'default']
  );
  persistDb(db);
  return rid;
}

export function completeAgentRun(db, runId, output) {
  exec(db,
    `UPDATE agent_runs SET status = ?, output_summary = ?, total_receivers = ?, push_count = ?,
     completed_at = datetime('now'), duration_ms = ? WHERE run_id = ?`,
    [output.status || 'completed', JSON.stringify(output.summary || {}),
     output.total_receivers || 0, output.push_count || 0,
     output.duration_ms || null, runId]
  );
  persistDb(db);
}

export function failAgentRun(db, runId, error) {
  exec(db, `UPDATE agent_runs SET status = 'failed', error = ?, completed_at = datetime('now') WHERE run_id = ?`,
    [error, runId]);
  persistDb(db);
}

// ── Document Version Operations ────────────────────────────────────────────

export function saveDocumentVersion(db, doc) {
  // Find the latest version number for this doc
  const latest = queryOne(db, 'SELECT MAX(version) as maxv FROM document_versions WHERE doc_id = ?', [doc.doc_id]);
  const version = (latest?.maxv || 0) + 1;
  const contentHash = doc.content ? hashContent(doc.content) : '';
  
  exec(db,
    `INSERT INTO document_versions (doc_id, doc_title, version, content, content_hash, author, change_summary, metadata_json)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    [doc.doc_id, doc.doc_title, version, doc.content || '', contentHash,
     doc.author || '', doc.change_summary || '', JSON.stringify(doc.metadata || {})]
  );
  persistDb(db);
  return { doc_id: doc.doc_id, version, content_hash: contentHash };
}

export function getDocumentVersions(db, docId, limit = 10) {
  return query(db,
    `SELECT * FROM document_versions WHERE doc_id = ? ORDER BY version DESC LIMIT ?`,
    [docId, limit]
  );
}

export function getDocumentVersion(db, docId, version) {
  return queryOne(db,
    `SELECT * FROM document_versions WHERE doc_id = ? AND version = ?`,
    [docId, version]
  );
}

function hashContent(content) {
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    const chr = content.charCodeAt(i);
    hash = ((hash << 5) - hash) + chr;
    hash |= 0;
  }
  return Math.abs(hash).toString(16);
}
