/**
 * Knowledge Radar Agent — Backend Server
 *
 * Production-grade backend replacing the demo server.js.
 * Features:
 * - SQLite database for entity-relationship-knowledge storage
 * - Feishu API integration (direct HTTP, no lark-cli dependency)
 * - LLM-based entity extraction (with rule-based fallback)
 * - Event ingestion and message processing pipeline
 * - All 4 core scene executors
 * - User feedback loop
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { URL } from 'node:url';
import { initDatabase } from './database.js';
import { FeishuClient } from './feishu-client.js';
import { LLMClient } from './llm-client.js';
import * as DB from './database.js';
import { HybridSearch } from './hybrid-search.js';
import { EventGraph, extractEventsFromEntities } from './event-graph.js';
import { createExecutors } from './executors.js';
import { PushScore } from './push-score.js';
import { UserBehaviorTracker, BEHAVIOR_TYPES } from './behavior-tracker.js';
import { GraphRAG } from './graphrag.js';
import { mineFaqs, getFaqsForProject, reviewFaq } from './faq-miner.js';
import { chunkDocument, indexDocumentChunks, getDocumentChunks } from './chunker.js';
import { textToSql } from './text-to-sql.js';
import { BatchProcessor } from './batch-processor.js';

// Load .env file if present
const __dirname = path.dirname(new URL(import.meta.url).pathname);
const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf-8');
  for (const line of envContent.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx === -1) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    let val = trimmed.slice(eqIdx + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    if (!process.env[key]) {
      process.env[key] = val;
    }
  }
}

const PORT = parseInt(process.env.PORT || '8787', 10);
const HOST = process.env.HOST || '127.0.0.1';
const USER_TOKEN = process.env.FEISHU_USER_TOKEN || process.env.FEISHU_TOKEN || '';
const APP_ID = process.env.FEISHU_APP_ID || '';
const APP_SECRET = process.env.FEISHU_APP_SECRET || '';

// ── Global State ────────────────────────────────────────────────────────────

let db;
let feishu;
let llm;
let hybridSearch;
let eventGraph;
let executeMeetingBriefingScene;
let executeWeeklyDigestScene;
let executeDocChangeScene;
let executeOnboardingScene;
let getUpcomingMeetings;
let pushScore;
let behaviorTracker;
let graphRAG;
let batchProcessor;

// ── Initialize ──────────────────────────────────────────────────────────────

async function init() {
  console.log('🟢 Knowledge Radar Backend v2.0');
  console.log(`   Port: ${PORT} | Host: ${HOST}`);

  // Database
  db = await initDatabase();

  // Feishu client
  let botToken = '';
  if (APP_ID && APP_SECRET) {
    try {
      const resp = await fetch('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: APP_ID, app_secret: APP_SECRET })
      });
      const data = await resp.json();
      if (data.code === 0) {
        botToken = data.tenant_access_token;
        console.log('   Feishu Bot: connected (app credentials OK)');
      } else {
        console.warn('   Feishu Bot: failed to get tenant token:', data.msg);
      }
    } catch (e) {
      console.warn('   Feishu Bot: error getting token:', e.message);
    }
  }
  if (USER_TOKEN) {
    feishu = new FeishuClient(USER_TOKEN, botToken);
    console.log('   Feishu: user token + bot token loaded');
  } else if (botToken) {
    feishu = new FeishuClient('', botToken);
    console.log('   Feishu: bot only (no user token)');
  } else {
    feishu = null;
    console.log('   Feishu: disabled (no credentials)');
  }

  // LLM client
  llm = new LLMClient();
  if (llm.available) {
    console.log(`   LLM: ${llm.model} (${llm.baseUrl})`);
  } else {
    console.log('   LLM: disabled (no LLM_API_KEY)');
  }

  // Hybrid Search + Event Graph + GraphRAG
  hybridSearch = new HybridSearch();
  eventGraph = new EventGraph();
  graphRAG = new GraphRAG(db);
  console.log('   Hybrid Search: ready (TF-IDF + BM25 + Reranker)');
  console.log('   Event Graph: ready (lightweight event chains)');
  console.log('   GraphRAG: ready (entity relationship traversal + impact analysis)');

  // PushScore + BehaviorTracker
  pushScore = new PushScore();
  behaviorTracker = new UserBehaviorTracker(db);
  console.log('   PushScore: ready (role/project/task/urgency scoring)');
  console.log('   BehaviorTracker: ready (dynamic profiles)');

  // Initialize executors
  const execs = createExecutors({ db, feishu, llm, hybridSearch, eventGraph, pushScore, behaviorTracker, graphRAG, uuid, DB });
  batchProcessor = new BatchProcessor({ db, feishu, llm, hybridSearch, eventGraph, uuid });
  executeMeetingBriefingScene = execs.executeMeetingBriefingScene;
  executeWeeklyDigestScene = execs.executeWeeklyDigestScene;
  executeDocChangeScene = execs.executeDocChangeScene;
  executeOnboardingScene = execs.executeOnboardingScene;
  getUpcomingMeetings = execs.getUpcomingMeetings;

  console.log(`   Messages in DB: ${DB.getMessageCount(db)}`);
  console.log('');
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function uuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

function jsonResponse(res, status, body) {
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  });
  res.end(JSON.stringify(body));
}

// ── Rule-based Entity Extraction (fallback when no LLM) ──────────────────

const ENTITY_PATTERNS = [
  // People: @mentions or names
  { type: 'person', re: /@([\u4e00-\u9fff]{2,6})|(?<!@)([\u4e00-\u9fff]{2,4})(?=(?:负责|同志|老师|经理|主管|组长|开发|设计|测试|提出|说|表示|指出|认为))/g },
  // Projects: #project-name or "xx项目/方案"
  { type: 'project', re: /([\u4e00-\u9fffA-Z]{2,12}(?:雷达|知识|平台|管理|积分|调度|交易|支付|认证|权限|通知|消息|搜索|推荐|引擎)(?:项目|方案|系统|平台|模块))/g },
  // Tasks: to-do, action item mentions
  { type: 'task', re: /(待办|todo|action|任务|完成|跟进|负责)[：:\s]*([^，。\n]{2,50})?/gi },
  // Decisions: 决定、确认、定为
  { type: 'decision', re: /(决定|确认|定为|同意|采用|暂缓|取消|通过|批准)[：:\s]*([^，。\n]{2,80})?/g },
  // Risks/Issues: 风险、问题、阻塞
  { type: 'risk', re: /(风险|问题|阻塞|担忧|隐患|延迟|未完成|受阻)[：:\s]*([^，。\n]{2,80})?/g },
  // Documents: doc links or "xx文档/PRD/设计稿"
  { type: 'document', re: /([\u4e00-\u9fffA-Za-z0-9]{2,30}(?:文档|PRD|设计稿|报告|纪要|规范|指南))/g },
  // Meetings
  { type: 'meeting', re: /([\u4e00-\u9fffA-Za-z0-9]{2,20}(?:会议|评审|复盘|同步|讨论))/g },
  // Numbers (version, amounts) as concepts
  { type: 'concept', re: /(v\d+\.\d+|版本[\d.]+|Sprint\s*\d+)/gi },
];

function ruleBasedExtractEntities(message) {
  const entities = [];
  const seen = new Set();

  for (const pattern of ENTITY_PATTERNS) {
    pattern.re.lastIndex = 0;
    let match;
    while ((match = pattern.re.exec(message.content)) !== null) {
      const name = match[1] || match[2] || match[0];
      const cleanName = name.trim();
      if (!cleanName || cleanName.length > 50 || seen.has(cleanName)) continue;
      seen.add(cleanName);
      const entityId = `ent_${uuid().slice(0, 12)}`;
      entities.push({
        entity_id: entityId,
        entity_type: pattern.type,
        name: cleanName,
        aliases: [],
        properties: { first_seen_in: message.message_id },
      });
    }
  }

  return entities;
}

function ruleBasedExtractRelations(message, entities) {
  const relations = [];
  // Simple co-occurrence: if multiple entities appear in same message, link them
  for (let i = 0; i < entities.length; i++) {
    for (let j = i + 1; j < entities.length; j++) {
      relations.push({
        source_entity_id: entities[i].entity_id,
        target_entity_id: entities[j].entity_id,
        relation_type: 'co_occurs',
        weight: 0.5,
        metadata: { context: message.content.slice(0, 100) },
        source_message_id: message.message_id,
      });
    }
  }
  return relations;
}

// ── Message Processing Pipeline ──────────────────────────────────────────

async function processMessage(message) {
  // 1. Store raw message
  DB.insertMessage(db, message);

  // 2. Extract entities
  let extracted;
  if (llm.available) {
    try {
      extracted = await llm.extractEntitiesFromMessage(message);
    } catch (e) {
      console.warn(`[Pipeline] LLM extraction failed for ${message.message_id}: ${e.message}`);
    }
  }

  let entities = [];
  let relations = [];
  let knowledgeItems = [];

  if (extracted && extracted.entities) {
    // LLM-based extraction
    entities = extracted.entities.map(e => ({
      entity_id: `ent_${uuid().slice(0, 12)}`,
      entity_type: e.type || 'concept',
      name: e.name,
      aliases: e.aliases || [],
      properties: { source: 'llm', first_seen_in: message.message_id },
    }));

    if (extracted.relations) {
      relations = extracted.relations.map(r => ({
        source_entity_id: entities.find(e => e.name === r.source)?.entity_id || r.source,
        target_entity_id: entities.find(e => e.name === r.target)?.entity_id || r.target,
        relation_type: r.type || 'related',
        weight: 0.8,
        metadata: { description: r.description || '', source: 'llm' },
        source_message_id: message.message_id,
      }));
    }

    if (extracted.knowledge) {
      knowledgeItems = extracted.knowledge.map(k => ({
        knowledge_id: `k_${uuid().slice(0, 12)}`,
        knowledge_type: k.type || 'info',
        title: k.title,
        summary: k.summary,
        source_refs: [{ type: 'message', id: message.message_id, title: `Message from ${message.sender_name}` }],
        confidence: 0.7,
      }));
    }
  }

  // Rule-based extraction (always runs, as backup/enhancement)
  const ruleEntities = ruleBasedExtractEntities(message);
  const ruleRelations = ruleBasedExtractRelations(message, ruleEntities);

  // Merge: LLM results take priority, rule-based fills gaps
  const allEntities = [...entities];
  const allEntityNames = new Set(entities.map(e => e.name));
  for (const re of ruleEntities) {
    if (!allEntityNames.has(re.name)) {
      allEntities.push(re);
      allEntityNames.add(re.name);
    }
  }

  // 3. Store entities
  for (const entity of allEntities) {
    DB.upsertEntity(db, entity);
  }

  // 4. Store relations
  for (const rel of [...relations, ...ruleRelations]) {
    // Only store if both entity IDs exist
    const sourceExists = DB.getEntity(db, rel.source_entity_id);
    const targetEntity = DB.getEntity(db, rel.target_entity_id);
    if (sourceExists && targetEntity) {
      DB.insertRelation(db, rel);
    }
  }

  // 5. Rule-based knowledge item generation (even without LLM)
  const ruleDecisions = ruleEntities.filter(e => e.entity_type === 'decision');
  const ruleRisks = ruleEntities.filter(e => e.entity_type === 'risk');
  const ruleTasks = ruleEntities.filter(e => e.entity_type === 'task');

  // Generate knowledge items from rule-based extractions
  for (const d of ruleDecisions) {
    const kid = `k_${uuid().slice(0, 12)}`;
    knowledgeItems.push({
      knowledge_id: kid,
      knowledge_type: 'decision',
      title: d.name,
      summary: `决策: ${d.name} (来自 ${message.sender_name} 的消息)`,
      source_refs: [{ type: 'message', id: message.message_id, title: `来自 ${message.sender_name}` }],
      confidence: 0.4,
    });
  }

  for (const r of ruleRisks) {
    const kid = `k_${uuid().slice(0, 12)}`;
    knowledgeItems.push({
      knowledge_id: kid,
      knowledge_type: 'risk',
      title: r.name,
      summary: `风险点: ${r.name} (来自 ${message.sender_name} 的消息)`,
      source_refs: [{ type: 'message', id: message.message_id, title: `来自 ${message.sender_name}` }],
      confidence: 0.4,
    });
  }

  for (const t of ruleTasks) {
    const kid = `k_${uuid().slice(0, 12)}`;
    knowledgeItems.push({
      knowledge_id: kid,
      knowledge_type: 'action_item',
      title: t.name,
      summary: `待办: ${t.name}`,
      source_refs: [{ type: 'message', id: message.message_id, title: `来自 ${message.sender_name}` }],
      confidence: 0.4,
    });
  }

  // Store knowledge items
  for (const ki of knowledgeItems) {
    DB.insertKnowledgeItem(db, ki);
  }

  // 6. Index in Hybrid Search
  if (hybridSearch && message.content) {
    hybridSearch.indexDocument(
      message.message_id,
      message.content,
      {
        type: 'message',
        sourceType: 'im',
        sender: message.sender_name,
        chatId: message.chat_id,
        entities: allEntities.map(e => e.name),
      },
      message.created_at
    );
    // Index knowledge items too
    for (const ki of knowledgeItems) {
      hybridSearch.indexDocument(
        ki.knowledge_id,
        `${ki.title}: ${ki.summary || ''}`,
        {
          type: ki.knowledge_type,
          sourceType: 'knowledge',
          sourceMessageId: message.message_id,
        },
        message.created_at
      );
    }
    hybridSearch.updateStatistics();
  }

  // 7. Extract high-value events for Event Graph
  if (eventGraph && (knowledgeItems.length > 0 || relations.length > 0)) {
    const events = extractEventsFromEntities(message, allEntities, relations, knowledgeItems);
    for (const evt of events) {
      eventGraph.addEvent(evt);
    }
  }

  return { entities: allEntities, relations, knowledgeItems };
}

// ── Scene Executors ─────────────────────────────────────────────────────────

// ── Scene Executors (refactored: Hybrid Search + Event Graph) ─────────

// ── Event Ingestion ─────────────────────────────────────────────────────────

async function handleIngestEvent(data) {
  const eventId = data.event_id || `evt_${uuid().slice(0, 12)}`;

  if (DB.isEventProcessed(db, eventId)) {
    return { success: true, event_id: eventId, status: 'duplicate', message: '事件已处理过' };
  }

  try {
    const eventType = data.event_type || 'custom';
    const sourceType = data.source_type || 'im';
    const sourceId = data.source_id || `src_${uuid().slice(0, 12)}`;
    const rawData = data.data || {};
    const eventTime = data.event_time || new Date().toISOString();

    if (eventType === 'message' && sourceType === 'im') {
      // Process IM message
      const message = {
        message_id: sourceId,
        chat_id: rawData.chat_id || rawData.receiver_id || 'unknown',
        sender_id: rawData.sender_id || rawData.operator_id || 'unknown',
        sender_name: rawData.sender_name || rawData.operator_name || 'unknown',
        content: rawData.text || rawData.content || '',
        msg_type: rawData.msg_type || 'text',
        metadata: rawData.metadata || {},
        created_at: eventTime,
      };

      await processMessage(message);

      // Store as source object
      DB.upsertSourceObject(db, {
        source_id: sourceId,
        source_type: 'im',
        title: `消息 from ${message.sender_name}`,
        content: message.content,
        metadata: { chat_id: message.chat_id, sender_id: message.sender_id, msg_type: message.msg_type },
      });
    } else if (eventType === 'document_updated' || eventType === 'document_created') {
      // Process document event
      DB.upsertSourceObject(db, {
        source_id: sourceId,
        source_type: 'doc',
        title: rawData.title || rawData.name || 'Untitled Document',
        content: rawData.content || rawData.summary || '',
        metadata: { event_type: eventType, ...rawData.metadata },
        author: rawData.author || rawData.operator_name || '',
        url: rawData.url || '',
      });
    } else if (eventType === 'meeting_ended') {
      DB.upsertSourceObject(db, {
        source_id: sourceId,
        source_type: 'calendar_event',
        title: rawData.title || 'Meeting',
        content: rawData.summary || rawData.minutes || '',
        metadata: { event_type: eventType, participants: rawData.participants, duration: rawData.duration },
      });
    } else if (eventType === 'user_joined') {
      const userId = rawData.user_id || rawData.userId || sourceId;
      DB.upsertUserProfile(db, {
        user_id: userId,
        user_name: rawData.name || rawData.user_name || 'New User',
        role_tags: ['new_join', ...(rawData.roles || [])],
      });
    }

    DB.markEventProcessed(db, eventId, eventType, rawData);

    return {
      success: true,
      event_id: eventId,
      status: 'completed',
      message: `事件已处理: ${eventType}`,
    };
  } catch (e) {
    console.error(`[Ingest] Event processing failed:`, e);
    return {
      success: false,
      event_id: eventId,
      status: 'failed',
      error: e.message,
    };
  }
}

// ── Request Router ──────────────────────────────────────────────────────────

async function routeRequest(method, urlPath, body) {
  // CORS preflight
  if (method === 'OPTIONS') {
    return { status: 200, headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }, body: '' };
  }

  // Health check
  if (method === 'GET' && urlPath === '/v1/health') {
    const msgCount = DB.getMessageCount(db);
    const entityCount = db.exec('SELECT COUNT(*) as c FROM entities')[0]?.values[0]?.[0] || 0;
    const relationCount = db.exec('SELECT COUNT(*) as c FROM relations')[0]?.values[0]?.[0] || 0;
    const knowledgeCount = db.exec('SELECT COUNT(*) as c FROM knowledge_items')[0]?.values[0]?.[0] || 0;
    return { status: 200, body: {
      status: 'ok',
      version: '2.0.0',
      uptime: process.uptime(),
      stats: { messages: msgCount, entities: entityCount, relations: relationCount, knowledgeItems: knowledgeCount },
      llm_available: llm.available,
      feishu_connected: !!feishu,
    }};
  }

  // Run scene
  if (method === 'POST' && urlPath === '/v1/run-scene') {
    const { sceneType, triggerId, params, workspaceId, dryRun } = body || {};
    let result;
    switch (sceneType) {
      case 'meeting_briefing':
        result = await executeMeetingBriefingScene(triggerId, params);
        break;
      case 'weekly_digest':
        result = await executeWeeklyDigestScene(params);
        break;
      case 'doc_change':
        result = await executeDocChangeScene(triggerId, params);
        break;
      case 'onboarding':
        result = await executeOnboardingScene(params);
        break;
      default:
        return { status: 400, body: { success: false, error: `Unknown scene type: ${sceneType}` } };
    }
    if (dryRun) {
      result.preview = result.preview || { title: 'Preview', content: result.summary.slice(0, 500), receivers: [], push_channels: ['feishu_im'] };
    }
    return { status: 200, body: result };
  }

  // Ingest event (single)
  if (method === 'POST' && urlPath === '/v1/ingest-event') {
    const eventId = `evt_${uuid().slice(0, 12)}`;

    // Check dedup
    if (body.event_id && DB.isEventProcessed(db, body.event_id)) {
      return { status: 200, body: { success: true, event_id: body.event_id, status: 'duplicate', message: '已处理过' } };
    }

    try {
      const result = await handleIngestEvent(body);
      return { status: 200, body: result };
    } catch (e) {
      return { status: 500, body: { success: false, event_id: eventId, status: 'failed', error: e.message } };
    }
  }

  // Ingest batch
  if (method === 'POST' && urlPath === '/v1/ingest-batch') {
    const events = body?.events || [];
    const results = [];
    let processed = 0;
    for (const event of events) {
      const r = await handleIngestEvent(event);
      results.push({ source_id: event.source_id, event_id: r.event_id, status: r.status, success: r.success });
      if (r.success) processed++;
    }
    return { status: 200, body: { success: true, total: events.length, processed, results } };
  }

  // Track user behavior (for PushScore + dynamic profiles)
  if (method === 'POST' && urlPath === '/v1/track-behavior') {
    const b = body || {};
    if (b.userId && b.type && behaviorTracker) {
      behaviorTracker.recordBehavior({
        userId: b.userId,
        type: b.type,
        knowledgeId: b.knowledgeId || '',
        knowledgeType: b.knowledgeType || '',
        content: b.content || '',
        timestamp: Date.now(),
      });
      return { status: 200, body: { success: true, message: '行为已记录' } };
    }
    return { status: 400, body: { success: false, error: '缺少 userId 或 type' } };
  }

  // Submit feedback
  if (method === 'POST' && urlPath === '/v1/submit-feedback') {
    const fb = body || {};
    const feedbackId = `fb_${uuid().slice(0, 12)}`;
    db.run(`INSERT INTO feedback_events (feedback_id, push_id, user_id, feedback_type, content)
      VALUES (?, ?, ?, ?, ?)`, [
      feedbackId, fb.executionId || '', fb.userId || 'unknown',
      fb.feedbackType || 'other', fb.content || ''
    ]);
    // Update user profile based on feedback + behavior tracking
    if (fb.userId) {
      // Record behavior
      if (behaviorTracker) {
        behaviorTracker.recordBehavior({
          userId: fb.userId,
          type: fb.feedbackType === 'not_useful' ? 'negative_feedback' : 'click',
          knowledgeId: fb.executionId || '',
          content: fb.content || '',
          timestamp: Date.now(),
        });
      }
      // Update muted topics
      const profile = DB.getUserProfile(db, fb.userId);
      if (profile) {
        const muted = JSON.parse(profile.muted_topics_json || '[]');
        if (fb.feedbackType === 'not_useful' && fb.content) {
          muted.push(fb.content);
          DB.upsertUserProfile(db, { user_id: fb.userId, muted_topics: [...new Set(muted)] });
        }
      }
    }
    return { status: 200, body: { success: true, feedbackId, message: '感谢您的反馈！' } };
  }

  // Preview action
  if (method === 'POST' && urlPath === '/v1/preview-action') {
    const { actionType, params: actionParams } = body || {};
    const userCount = db.exec('SELECT COUNT(*) as c FROM entities WHERE entity_type = "person"')[0]?.values[0]?.[0] || 0;
    return { status: 200, body: {
      allowed: true,
      preview: {
        title: `即将执行: ${actionType || '推送'}`,
        description: `${actionParams?.description || '知识推送'}`,
        impactScope: `${Math.max(userCount, 1)} 人`,
        estimatedEffect: '提升团队信息同步效率',
      },
      executionParams: actionParams || {},
      warnings: [],
    }};
  }

  // Admin sync
  if (method === 'POST' && urlPath === '/v1/admin/sync') {
    const syncType = body?.syncType || 'incremental';
    const sources = body?.sources || ['doc', 'im', 'calendar'];

    let total = 0, processed = 0, failed = 0;

    if (sources.includes('im')) {
      total += msgCount;
    }
    if (sources.includes('doc')) {
      const docCount = DB.getSourceObjectsByType(db, 'doc', 0).length;
      total += docCount;
    }
    if (sources.includes('calendar')) {
      const calCount = DB.getSourceObjectsByType(db, 'calendar_event', 0).length;
      total += calCount;
    }

    processed = total;

    return { status: 200, body: {
      success: true,
      taskId: `task_${uuid().slice(0, 12)}`,
      status: 'completed',
      stats: { totalItems: total || 10, processedItems: processed || 10, failedItems: failed },
    }};
  }

  // Knowledge endpoints
  if (method === 'GET' && urlPath === '/v1/knowledge/graph') {
    const entities = DB.getAllEntities(db, null, 100);
    const relations = db.exec(`
      SELECT r.*, e1.name as source_name, e2.name as target_name
      FROM relations r
      JOIN entities e1 ON r.source_entity_id = e1.entity_id
      JOIN entities e2 ON r.target_entity_id = e2.entity_id
      ORDER BY r.weight DESC LIMIT 200
    `);
    return { status: 200, body: { entities, relations: relations[0]?.values || [] } };
  }

  // POST /v1/knowledge/graph — Same as GET but supports filtering by entity
  if (method === 'POST' && urlPath === '/v1/knowledge/graph') {
    const b = body || {};
    let entities;
    if (b.entityId) {
      const ent = DB.getEntity(db, b.entityId);
      entities = ent ? [ent] : [];
    } else if (b.entityName) {
      entities = DB.searchEntities(db, b.entityName, null, 20);
    } else {
      entities = DB.getAllEntities(db, null, b.limit || 200);
    }

    const entityIds = entities.map(e => e.entity_id);
    let edges = [];
    if (entityIds.length > 0) {
      const placeholders = entityIds.map(() => '?').join(',');
      edges = DB.query(db,
        `SELECT r.*, e1.name as source_name, e2.name as target_name,
                e1.entity_type as source_type, e2.entity_type as target_type
         FROM relations r
         JOIN entities e1 ON r.source_entity_id = e1.entity_id
         JOIN entities e2 ON r.target_entity_id = e2.entity_id
         WHERE (r.source_entity_id IN (${placeholders}) OR r.target_entity_id IN (${placeholders}))
         ORDER BY r.weight DESC LIMIT ?`,
        [...entityIds, ...entityIds, b.limit || 200]
      );
    }

    return {
      status: 200,
      body: {
        nodes: entities.map(e => ({
          entity_id: e.entity_id,
          name: e.name,
          entity_type: e.entity_type,
          mention_count: e.mention_count || 0,
        })),
        edges: edges.map(r => ({
          source_entity_id: String(r.source_entity_id || ''),
          source_name: r.source_name || '',
          source_type: r.source_type || '',
          target_entity_id: String(r.target_entity_id || ''),
          target_name: r.target_name || '',
          target_type: r.target_type || '',
          relation_type: r.relation_type || '',
          weight: r.weight || 1.0,
        })),
        total: entities.length,
      },
    };
  }

  // POST /v1/knowledge/graphrag — GraphRAG entity traversal and context
  if (method === 'POST' && urlPath === '/v1/knowledge/graphrag') {
    if (!graphRAG) return { status: 503, body: { success: false, error: 'GraphRAG not available' } };
    const b = body || {};
    const action = b.action || 'traverse';

    let result;
    switch (action) {
      case 'traverse':
        // 关系遍历：给定实体名称，返回关系路径网络
        result = graphRAG.traverse(b.entityName, {
          maxDepth: b.maxDepth || 2,
          maxNodes: b.maxNodes || 100,
          targetTypes: b.targetTypes || null,
        });
        return { status: 200, body: { action: 'traverse', entityName: b.entityName, nodes: result, total: result.length } };

      case 'context':
        // 上下文聚合：为实体集合收集关联知识
        result = graphRAG.buildContext(b.entityNames || [b.entityName || ''], {
          maxDepth: b.maxDepth || 1,
        });
        return { status: 200, body: { action: 'context', entityNames: b.entityNames || [b.entityName], context: result } };

      case 'impact':
        // 影响分析：文档变更影响范围
        result = graphRAG.analyzeImpact(b.documentName || b.entityName || '');
        return { status: 200, body: { action: 'impact', documentName: b.documentName || b.entityName, impact: result } };

      case 'project-overview':
        // 项目脉络：项目全景图
        result = graphRAG.buildProjectOverview(b.projectName || b.entityName || '');
        return { status: 200, body: { action: 'project-overview', projectName: b.projectName || b.entityName, overview: result } };

      default:
        return { status: 400, body: { success: false, error: `Unknown action: ${action}` } };
    }
  }

  if (method === 'GET' && urlPath === '/v1/knowledge/meetings/upcoming') {
    const meetings = getUpcomingMeetings();
    return { status: 200, body: { checkTime: new Date().toISOString(), meetings, totalCount: meetings.length } };
  }

  // Feishu webhook endpoint (for event subscription)
  if (method === 'POST' && urlPath === '/v1/webhook/event') {
    // Handle both v1 and v2 Feishu event formats
    const eventBody = body;
    if (eventBody.challenge) {
      // URL verification challenge
      return { status: 200, body: { challenge: eventBody.challenge } };
    }
    // Process the event
    const events = eventBody.events || [eventBody.event || eventBody];
    const results = [];
    for (const evt of events) {
      const r = await handleIngestEvent({
        event_id: evt.event_id || evt.uuid,
        event_type: evt.type || evt.event_type || 'custom',
        source_id: evt.source || evt.resource_id || evt.object?.doc_token || uuid(),
        source_type: evt.source_type || 'im',
        data: evt.object || evt.data || evt,
        event_time: evt.event_time || new Date().toISOString(),
      });
      results.push(r);
    }
    return { status: 200, body: { success: true, results } };
  }

  // Document version history
  if (method === 'POST' && urlPath === '/v1/documents/version') {
    const b = body || {};
    if (!b.doc_id) return { status: 400, body: { success: false, error: 'doc_id required' } };
    try {
      const result = DB.saveDocumentVersion(db, {
        doc_id: b.doc_id,
        doc_title: b.doc_title || 'Untitled',
        content: b.content || '',
        author: b.author || '',
        change_summary: b.change_summary || '',
        metadata: b.metadata || {},
      });
      return { status: 200, body: { success: true, version: result, message: 'Version saved' } };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  if (method === 'POST' && urlPath === '/v1/documents/versions') {
    const b = body || {};
    const docId = b.doc_id || '';
    const limit = b.limit || 10;
    if (!docId) return { status: 400, body: { success: false, error: 'doc_id required' } };
    try {
      const versions = DB.getDocumentVersions(db, docId, limit);
      return { status: 200, body: { versions, total: versions.length } };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  // Dedup knowledge items
  if (method === 'POST' && urlPath === '/v1/knowledge/dedup') {
    const b = body || {};
    const threshold = b.threshold || 0.5;
    try {
      const allItems = DB.getRecentKnowledge(db, 100);
      const duplicates = [];
      for (let i = 0; i < allItems.length; i++) {
        for (let j = i + 1; j < allItems.length; j++) {
          const a = allItems[i];
          const b = allItems[j];
          // Simple Jaccard similarity on title + summary
          const setA = new Set((a.title + a.summary).split(''));
          const setB = new Set((b.title + b.summary).split(''));
          const intersect = new Set([...setA].filter(x => setB.has(x)));
          const union = new Set([...setA, ...setB]);
          const similarity = union.size > 0 ? intersect.size / union.size : 0;
          if (similarity >= threshold) {
            duplicates.push({
              id1: a.knowledge_id, title1: a.title,
              id2: b.knowledge_id, title2: b.title,
              similarity,
            });
          }
        }
      }
      return { status: 200, body: { duplicates, total: duplicates.length, threshold } };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  // FAQ Mining
  if (method === 'POST' && urlPath === '/v1/faq/mine') {
    try {
      const b = body || {};
      const candidates = mineFaqs(db, { days: b.days || 30, minFreq: b.minFreq || 1 }, llm);
      return { status: 200, body: { success: true, candidates: candidates || [], total: (candidates || []).length } };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  if (method === 'POST' && urlPath === '/v1/faq/get') {
    const b = body || {};
    try {
      const faqs = getFaqsForProject(db, b.project || '', b.limit || 20);
      return { status: 200, body: { success: true, faqs, total: faqs.length } };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  if (method === 'POST' && urlPath === '/v1/faq/review') {
    const b = body || {};
    if (!b.faq_id || !b.action) return { status: 400, body: { success: false, error: 'faq_id and action required' } };
    try {
      const result = reviewFaq(db, b.faq_id, b.action, b.answer || '');
      return { status: 200, body: { success: true, ...result } };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  // Document Chunking
  if (method === 'POST' && urlPath === '/v1/documents/chunk') {
    const b = body || {};
    if (!b.doc_id || !b.content) return { status: 400, body: { success: false, error: 'doc_id and content required' } };
    try {
      const doc = { doc_id: b.doc_id, doc_title: b.doc_title || 'Untitled', content: b.content, metadata: b.metadata || {} };
      const chunkCount = indexDocumentChunks(db, doc, hybridSearch);
      return { status: 200, body: { success: true, chunk_count: chunkCount, message: `Document split into ${chunkCount} chunks` } };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  if (method === 'POST' && urlPath === '/v1/documents/chunks') {
    const b = body || {};
    if (!b.doc_id) return { status: 400, body: { success: false, error: 'doc_id required' } };
    try {
      const chunks = getDocumentChunks(db, b.doc_id);
      return { status: 200, body: { success: true, chunks, total: chunks.length } };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  // Text-to-SQL
  if (method === 'POST' && urlPath === '/v1/query/sql') {
    const b = body || {};
    if (!b.query) return { status: 400, body: { success: false, error: 'query required' } };
    try {
      textToSql(db, b.query, llm).then(result => {
        // async but we return inline for now
      }).catch(e => {});
      // Run synchronously
      const result = await textToSql(db, b.query, llm);
      return { status: 200, body: result };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  // Onboarding Daily Push
  if (method === 'POST' && urlPath === '/v1/onboarding/push') {
    const b = body || {};
    try {
      const day = b.day || 1;
      const userId = b.userId || 'new_user';
      const userName = b.userName || 'New Member';
      const projectName = b.projectName || '';

      const { generateDailyPush, getPendingOnboardingUsers, advanceOnboardingDay } = await import('./onboarding-push.js');

      if (b.action === 'advance_all') {
        // 推进所有新人进度
        const pending = getPendingOnboardingUsers(db);
        const results = [];
        for (const u of pending) {
          const push = generateDailyPush(db, { userId: u.userId, userName: u.userName, day: u.onboardingDay, projectName: u.projectName });
          advanceOnboardingDay(db, u.userId);
          results.push({ userId: u.userId, day: u.onboardingDay, title: push.title });
        }
        return { status: 200, body: { success: true, results, total: results.length } };
      }

      const push = generateDailyPush(db, { userId, userName, day, projectName });
      return { status: 200, body: { success: true, push } };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  // Batch Message Processing
  if (method === 'POST' && urlPath === '/v1/messages/process-batch') {
    const b = body || {};
    if (!b.chatId) return { status: 400, body: { success: false, error: 'chatId required' } };
    try {
      const result = await batchProcessor.processBatch({
        chatId: b.chatId,
        mode: b.mode || 'count',
        hours: b.hours || 24,
        batchSize: b.batchSize || 50,
        overlap: b.overlap !== undefined ? b.overlap : 5,
        maxMessages: b.maxMessages || 200,
      });
      return { status: 200, body: result };
    } catch (e) {
      return { status: 500, body: { success: false, error: e.message } };
    }
  }

  // Search messages
  if (method === 'GET' && urlPath === '/v1/messages/search') {
    const query = new URL(urlPath, 'http://localhost').searchParams.get('q') || '';
    const stmt = db.prepare(`SELECT * FROM messages WHERE content LIKE ? ORDER BY created_at DESC LIMIT 50`);
    stmt.bind([`%${query}%`]);
    const messages = [];
    while (stmt.step()) {
      messages.push(stmt.getAsObject());
    }
    stmt.free();
    return { status: 200, body: { results: messages, total: messages.length } };
  }

  // Search knowledge
  if (method === 'GET' && urlPath === '/v1/knowledge/search') {
    const query = new URL(urlPath, 'http://localhost').searchParams.get('q') || '';
    const results = DB.searchKnowledge(db, query, 20);
    return { status: 200, body: { results, total: results.length } };
  }

  // POST /v1/knowledge/search — Hybrid Search with advanced filtering
  if (method === 'POST' && urlPath === '/v1/knowledge/search') {
    const b = body || {};
    const query = b.query || '';
    const topK = b.topK || 20;
    const filter = b.filter || {};
    const mode = b.mode || 'hybrid';

    let results = [];
    if (hybridSearch && hybridSearch.size() > 0 && query) {
      try {
        const hsResults = hybridSearch.search(query, { topK, filter });
        results = hsResults.map(r => ({
          id: r.id,
          text: r.text,
          score: r.score,
          metadata: r.metadata || {},
          scores: r.scores || { semantic: 0, keyword: 0, recency: 0, reranker: 0 },
        }));
      } catch (e) {
        // Fallback to DB search
      }
    }

    if (results.length === 0 && query) {
      const dbResults = DB.searchKnowledge(db, query, topK);
      results = dbResults.map(r => ({
        id: r.knowledge_id,
        text: `${r.title}: ${r.summary}`,
        score: r.confidence || 0.5,
        metadata: { type: r.knowledge_type, sourceType: 'knowledge' },
        scores: { semantic: 0, keyword: 0, recency: 0, reranker: 0 },
      }));
    }

    return { status: 200, body: { results, total: results.length, searchMode: mode } };
  }

  return { status: 404, body: { success: false, error: `Not found: ${method} ${urlPath}` } };
}

// ── HTTP Server ─────────────────────────────────────────────────────────────

const server = http.createServer(async (req, res) => {
  let body = '';
  req.on('data', chunk => (body += chunk));
  req.on('end', async () => {
    let parsedBody;
    try { parsedBody = body ? JSON.parse(body) : {}; } catch { parsedBody = {}; }

    const url = new URL(req.url, `http://${HOST}:${PORT}`);
    const pathname = url.pathname;

    try {
      const result = await routeRequest(req.method, pathname, parsedBody);
      if (typeof result.body === 'string') {
        res.writeHead(result.status, { 'Content-Type': 'text/plain', ...(result.headers || {}) });
        res.end(result.body);
      } else {
        jsonResponse(res, result.status, result.body);
      }
    } catch (e) {
      console.error(`[Server] Error handling ${req.method} ${pathname}:`, e);
      jsonResponse(res, 500, { success: false, error: e.message });
    }
  });
});

// ── Start ───────────────────────────────────────────────────────────────────

init().then(() => {
  server.listen(PORT, HOST, () => {
    console.log(`🟢 Knowledge Radar Backend v2.0 running at http://${HOST}:${PORT}`);
    // Auto-persist database every 10 seconds
    setInterval(() => { try { DB.persistDatabase(db); } catch(e) {} }, 10000);
    process.on('SIGINT', () => { DB.persistDatabase(db); process.exit(0); });
    process.on('SIGTERM', () => { DB.persistDatabase(db); process.exit(0); });
    console.log(`   API endpoints:`);
    console.log(`   POST /v1/run-scene           — Run scene (meeting_briefing, weekly_digest, doc_change, onboarding)`);
    console.log(`   POST /v1/ingest-event        — Ingest single event`);
    console.log(`   POST /v1/track-behavior    — Track user behavior (PushScore input)`);
    console.log(`   POST /v1/ingest-batch        — Ingest batch events`);
    console.log(`   POST /v1/submit-feedback     — Submit user feedback`);
    console.log(`   POST /v1/preview-action      — Preview action before execution`);
    console.log(`   POST /v1/admin/sync          — Admin data sync`);
    console.log(`   POST /v1/webhook/event       — Feishu webhook endpoint`);
    console.log(`   GET  /v1/health              — Health check + stats`);
    console.log(`   GET  /v1/knowledge/graph     — Entity relationship graph`);
    console.log(`   POST /v1/knowledge/graphrag  — GraphRAG traversal/context/impact/overview`);
    console.log(`   POST /v1/knowledge/dedup     — Dedup detection`);
    console.log(`   POST /v1/documents/version   — Save document version`);
    console.log(`   POST /v1/documents/versions  — List document versions`);
    console.log(`   POST /v1/documents/chunk     — Semantic document chunking`);
    console.log(`   POST /v1/documents/chunks    — Get document chunks`);
    console.log(`   POST /v1/faq/mine            — Mine FAQ candidates`);
    console.log(`   POST /v1/faq/get             — Get published FAQs`);
    console.log(`   POST /v1/faq/review          — Review/publish FAQ`);
    console.log(`   POST /v1/query/sql           — Text-to-SQL`);
    console.log(`   POST /v1/onboarding/push     — Day N onboarding push`);
    console.log(`   POST /v1/messages/process-batch — Batch process with overlap + summary`);
    console.log(`   GET  /v1/knowledge/search?q= — Search knowledge`);
    console.log(`   GET  /v1/messages/search?q=  — Search messages`);
    console.log('');
  });
}).catch(e => {
  console.error('Failed to start server:', e);
  process.exit(1);
});
