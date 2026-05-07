/**
 * Knowledge Radar — Text-to-SQL
 *
 * 将自然语言查询转换为 SQL，安全执行后返回结果。
 *
 * 安全策略：
 * - 只允许 SELECT 查询
 * - 禁止 DROP/ALTER/DELETE/INSERT/UPDATE
 * - SQL 长度限制
 * - LLM 验证生成的 SQL
 */

import * as DB from './database.js';

// ── 可查询的表 ──────────────────────────────────────────────────────────

const ALLOWED_TABLES = new Set([
  'messages', 'entities', 'relations', 'knowledge_items',
  'source_objects', 'user_profiles', 'push_events',
  'feedback_events', 'agent_runs', 'document_versions',
  'faq_candidates', 'document_chunks',
]);

const TABLE_DESCRIPTIONS = {
  messages: '聊天消息记录（content=消息内容, sender_id=发送者, chat_id=群聊ID, created_at=时间）',
  entities: '实体（entity_id=ID, entity_type=类型[person/project/concept], name=名称, mention_count=提及次数）',
  relations: '实体关系（source_entity_id=源实体, target_entity_id=目标实体, relation_type=关系类型, weight=权重）',
  knowledge_items: '知识条目（knowledge_type=类型[decision/action_item/risk/update], title=标题, summary=摘要, confidence=置信度）',
  source_objects: '原始来源对象（source_type=来源类型[doc/im/calendar], title=标题, content=内容）',
  user_profiles: '用户画像（user_id=用户ID, role_tags=角色标签, topics=关注主题, muted_topics=静音主题）',
  push_events: '推送记录（user_id=推送对象, push_type=推送类型, score=分数, delivery_status=状态）',
  feedback_events: '反馈记录（user_id=用户, feedback_type=类型[useful/not_useful], content=内容）',
  agent_runs: 'Agent 执行记录（scene_type=场景类型, status=状态, started_at=开始时间）',
  document_versions: '文档版本记录（doc_id=文档ID, version=版本号, author=作者, change_summary=变更摘要）',
  faq_candidates: 'FAQ 候选（question=问题, answer=答案, frequency=频次, status=状态[published/candidate]）',
  document_chunks: '文档分块（doc_id=文档ID, chunk_index=块序号, content=内容, summary=摘要）',
};

// ── Text-to-SQL 核心 ────────────────────────────────────────────────────

/**
 * 将自然语言转换为 SQL 并执行
 *
 * @param {Object} db - SQLite 实例
 * @param {string} naturalQuery - 自然语言查询
 * @param {Object} llm - LLM 客户端
 * @returns {Object} { sql, results, summary }
 */
export async function textToSql(db, naturalQuery, llm) {
  // 1. 用 LLM 生成 SQL
  let sql = '';
  if (llm && llm.available) {
    sql = await generateSqlWithLLM(naturalQuery, llm);
  } else {
    // 降级：简单规则匹配
    sql = ruleBasedSql(naturalQuery);
  }

  if (!sql) {
    return { success: false, error: '无法生成 SQL 查询', sql: null, results: [], summary: '' };
  }

  // 2. 安全检查
  const safetyCheck = validateSql(sql);
  if (!safetyCheck.valid) {
    return { success: false, error: safetyCheck.error, sql, results: [], summary: '' };
  }

  // 3. 执行 SQL
  try {
    const results = DB.query(db, sql, []);
    const summary = summarizeResults(naturalQuery, results, sql);
    return { success: true, sql, results, summary, total: results.length };
  } catch (e) {
    return { success: false, error: `SQL 执行错误: ${e.message}`, sql, results: [], summary: '' };
  }
}

/**
 * 用 LLM 生成 SQL
 */
async function generateSqlWithLLM(query, llm) {
  const tableInfo = Object.entries(TABLE_DESCRIPTIONS)
    .map(([name, desc]) => `- ${name}: ${desc}`)
    .join('\n');

  const prompt = `你是一个 SQLite 查询助手。根据用户的自然语言问题生成 SQL。

可用表：
${tableInfo}

规则：
- 只生成 SELECT 查询
- 不要使用 DROP/ALTER/DELETE/INSERT/UPDATE/CREATE
- 使用 LIKE 进行模糊匹配
- 用 datetime('now', '-N days') 做时间筛选
- 用 ORDER BY + LIMIT 控制结果数
- 返回的 SQL 要兼容 SQLite 语法
- 如果无法理解查询，返回 "-- 无法理解" 

用户问题：${query}

直接返回 SQL 查询语句，不要加解释：`;

  try {
    const response = await llm.chat([{role:"user",content:prompt}]);
    const cleaned = response.replace(/```sql|```|SQL:|sql:/gi, '').trim();
    if (cleaned.startsWith('--') || cleaned.includes('DROP') || cleaned.includes('DELETE') || cleaned.includes('INSERT')) {
      return null;
    }
    return cleaned;
  } catch {
    return null;
  }
}

/**
 * 简单规则匹配（无 LLM 时降级使用）
 */
function ruleBasedSql(query) {
  const q = query.toLowerCase();

  // 查询决策
  if (/决策/.test(q)) {
    let sql = `SELECT * FROM knowledge_items WHERE knowledge_type = 'decision' ORDER BY confidence DESC`;
    if (/最近|最新|近期/.test(q)) sql += ' LIMIT 10';
    else sql += ' LIMIT 20';
    return sql;
  }

  // 查询风险
  if (/风险/.test(q)) {
    let sql = `SELECT * FROM knowledge_items WHERE knowledge_type = 'risk' ORDER BY confidence DESC`;
    if (/最新|未解决|active/.test(q)) sql += " AND status = 'active'";
    sql += ' LIMIT 20';
    return sql;
  }

  // 查询待办
  if (/待办|任务|action/.test(q)) {
    let sql = `SELECT * FROM knowledge_items WHERE knowledge_type = 'action_item' ORDER BY confidence DESC LIMIT 20`;
    return sql;
  }

  // 查询人员/实体
  if (/人员|人|谁/.test(q)) {
    let sql = `SELECT * FROM entities WHERE entity_type = 'person' ORDER BY mention_count DESC LIMIT 20`;
    if (/(\S+)项目/.test(query)) {
      const m = query.match(/(\S+)项目/);
      if (m) {
        sql = `SELECT DISTINCT e.* FROM entities e JOIN relations r ON e.entity_id = r.source_entity_id OR e.entity_id = r.target_entity_id WHERE e.entity_type = 'person' AND (r.source_name LIKE '%${m[1]}%' OR r.target_name LIKE '%${m[1]}%') ORDER BY e.mention_count DESC LIMIT 20`;
      }
    }
    return sql;
  }

  // 查询项目
  if (/项目/.test(q)) {
    return `SELECT * FROM entities WHERE entity_type = 'project' ORDER BY mention_count DESC LIMIT 20`;
  }

  // 查询 FAQ
  if (/faq|常见问题|问答/.test(q)) {
    return `SELECT * FROM faq_candidates WHERE status = 'published' ORDER BY frequency DESC LIMIT 20`;
  }

  // 最近消息
  if (/消息|讨论|聊天/.test(q)) {
    return `SELECT * FROM messages ORDER BY created_at DESC LIMIT 20`;
  }

  // 搜索（含关键词）
  const matchWith = q.match(/搜索|查找|找.*?(\S+)/);
  if (matchWith) {
    const keyword = matchWith[1] || query.replace(/搜索|查找|帮我/g, '').trim();
    return `SELECT * FROM knowledge_items WHERE title LIKE '%${keyword}%' OR summary LIKE '%${keyword}%' ORDER BY confidence DESC LIMIT 20`;
  }

  // 全部知识
  if (/知识|知道的|有什么/.test(q)) {
    return 'SELECT * FROM knowledge_items ORDER BY confidence DESC LIMIT 20';
  }

  // 按时间查询
  if (/最近|近.*天|本周|上月/.test(q)) {
    return `SELECT * FROM knowledge_items WHERE created_at >= datetime('now', '-7 days') ORDER BY created_at DESC LIMIT 20`;
  }

  // 默认
  return `SELECT * FROM knowledge_items ORDER BY updated_at DESC LIMIT 10`;
}

// ── 安全校验 ────────────────────────────────────────────────────────────

function validateSql(sql) {
  if (!sql || sql.trim().length === 0) {
    return { valid: false, error: 'SQL 为空' };
  }

  const upper = sql.trim().toUpperCase();

  // 只允许 SELECT
  if (!upper.startsWith('SELECT') && !upper.startsWith('WITH')) {
    return { valid: false, error: '只允许 SELECT 查询' };
  }

  // 禁止危险操作
  const dangerous = ['DROP', 'ALTER', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'EXEC', 'ATTACH', 'DETACH', 'REINDEX', 'REPLACE', 'TRUNCATE', 'VACUUM'];
  for (const word of dangerous) {
    if (new RegExp(`\\b${word}\\b`, 'i').test(sql)) {
      return { valid: false, error: `禁止的操作: ${word}` };
    }
  }

  // SQL 长度限制
  if (sql.length > 2000) {
    return { valid: false, error: 'SQL 过长' };
  }

  return { valid: true };
}

// ── 结果摘要 ────────────────────────────────────────────────────────────

function summarizeResults(query, results, sql) {
  if (!results || results.length === 0) {
    return '没有找到符合条件的数据。';
  }

  const count = results.length;
  const first = results[0];

  // 根据查询类型生成不同格式的摘要
  if (/决策/.test(query)) {
    const items = results.slice(0, 5).map(r => `• ${r.title}`).join('\n');
    return `找到 ${count} 项决策：\n${items}\n${count > 5 ? `...还有 ${count - 5} 项` : ''}`;
  }

  if (/风险/.test(query)) {
    const items = results.slice(0, 5).map(r => `⚠️ ${r.title}`).join('\n');
    return `找到 ${count} 项风险：\n${items}`;
  }

  if (/待办|任务/.test(query)) {
    const items = results.slice(0, 5).map(r => `📋 ${r.title}`).join('\n');
    return `找到 ${count} 项待办：\n${items}`;
  }

  if (/人员|谁/.test(query)) {
    const items = results.slice(0, 10).map(r => `• ${r.name}（${r.entity_type}，${r.mention_count}次提及）`);
    return `找到 ${count} 个人员/实体：\n${items.join('\n')}`;
  }

  if (/项目/.test(query)) {
    const items = results.slice(0, 5).map(r => `• ${r.name}`);
    return `找到 ${count} 个项目：\n${items.join('\n')}`;
  }

  if (/faq|问答/.test(query)) {
    const items = results.slice(0, 5).map(r => `Q: ${r.question}\nA: ${(r.answer || '').slice(0, 150)}`);
    return `找到 ${count} 条常见问答：\n\n${items.join('\n\n')}`;
  }

  // 通用摘要
  const keys = Object.keys(first).filter(k => k !== 'id' && k !== 'created_at' && k !== 'updated_at').slice(0, 4);
  const items = results.slice(0, 5).map(r => {
    return keys.map(k => `${k}: ${(r[k] || '').toString().slice(0, 80)}`).join(' | ');
  }).join('\n');

  return `找到 ${count} 条结果${results.length > 0 ? '：\n' + items : ''}。`;
}

export default {
  textToSql,
};
