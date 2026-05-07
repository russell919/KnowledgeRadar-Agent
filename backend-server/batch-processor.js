/**
 * Knowledge Radar — Batch Message Processor
 *
 * 批量消息处理引擎。支持两种模式：
 *
 * 时间模式 (time)：按时间段拉取消息，消息少则一次处理完
 * 计数模式 (count)：固定条数分批处理，带重叠窗口保持上下文
 *
 * 每次批次处理：
 * 1. 逐条存储消息（走完整流水线：入库 → LLM抽取 → 实体/关系/知识 → 索引）
 * 2. LLM 对整批消息生成批次摘要（主题、决策、风险、待办）
 * 3. 批次摘要存入 message_batch_summaries 表
 *
 * 上下文连续性：批次间重叠 overlap 条消息，避免因切分丢失上下文。
 */

import * as DB from './database.js';

// ── 默认配置 ──────────────────────────────────────────────────────────────

const DEFAULT_BATCH_SIZE = 50;
const DEFAULT_OVERLAP = 5;
const DEFAULT_HOURS = 24;
const MAX_FETCH_PAGES = 10;  // 最多拉取页数

export class BatchProcessor {
  constructor({ db, feishu, llm, hybridSearch, eventGraph, uuid }) {
    this.db = db;
    this.feishu = feishu;
    this.llm = llm;
    this.hybridSearch = hybridSearch;
    this.eventGraph = eventGraph;
    this.uuid = uuid;
  }

  /**
   * 主入口：批量处理消息
   *
   * @param {Object} options
   * @param {string} options.chatId - 群聊 ID（必填）
   * @param {string} options.mode - 'time' | 'count'（默认 'count'）
   * @param {number} options.hours - 时间模式下回溯小时数（默认 24）
   * @param {number} options.batchSize - 每批消息数（默认 50）
   * @param {number} options.overlap - 批次间重叠消息数（默认 5）
   * @param {number} options.maxMessages - 最大总处理消息数（默认 0=不限制）
   * @returns {Object} 处理结果
   */
  async processBatch(options = {}) {
    const chatId = options.chatId;
    if (!chatId) return { success: false, error: 'chatId is required' };

    const mode = options.mode || 'count';
    const hours = options.hours || DEFAULT_HOURS;
    const batchSize = options.batchSize || DEFAULT_BATCH_SIZE;
    const overlap = options.overlap !== undefined ? options.overlap : DEFAULT_OVERLAP;
    const maxMessages = options.maxMessages || 0;

    // 1. 从飞书拉取消息（支持翻页）
    const allMessages = await this._fetchFeishuMessages(chatId, mode, hours, batchSize, maxMessages);
    if (!allMessages || allMessages.length === 0) {
      return { success: true, chatId, processed: 0, batches: [], message: '没有新消息' };
    }

    // 2. 按时间正序排列（飞书 API 返回倒序）
    allMessages.sort((a, b) => new Date(a.create_time || 0) - new Date(b.create_time || 0));

    // 3. 分批处理（带重叠）
    const totalMessages = allMessages.length;
    const batches = [];

    if (totalMessages <= batchSize) {
      // 策略 A：消息少，一次处理完
      const batchResult = await this._processSingleBatch(chatId, allMessages, 0, totalMessages);
      batches.push(batchResult);
    } else {
      // 策略 B：分批带重叠
      let startIdx = 0;
      let batchIndex = 0;
      while (startIdx < totalMessages) {
        const endIdx = Math.min(startIdx + batchSize, totalMessages);
        const batchMessages = allMessages.slice(Math.max(0, startIdx - (batchIndex > 0 ? overlap : 0)), endIdx);

        const batchResult = await this._processSingleBatch(
          chatId, batchMessages, startIdx, batchMessages.length
        );
        batches.push(batchResult);

        startIdx += batchSize - (batchIndex > 0 ? overlap : 0);
        batchIndex++;
      }
    }

    const processed = batches.reduce((sum, b) => sum + b.processed, 0);
    return {
      success: true,
      chatId,
      mode,
      batchSize,
      overlap,
      totalFetched: totalMessages,
      processed,
      batchCount: batches.length,
      batches,
    };
  }

  // ── 内部方法 ──────────────────────────────────────────────────────────

  /**
   * 从飞书拉取消息
   */
  async _fetchFeishuMessages(chatId, mode, hours, batchSize, maxMessages) {
    if (!this.feishu) return [];

    const allMessages = [];
    let pageToken = null;
    const pageSize = Math.min(batchSize * 2, 100); // 一次拉取尽量多
    let pages = 0;

    while (pages < MAX_FETCH_PAGES) {
      let result;
      try {
        result = await this.feishu.listMessages(chatId, pageSize, pageToken);
      } catch (e) {
        console.warn(`[BatchProcessor] Feishu fetch error: ${e.message}`);
        break;
      }

      if (!result || !result.items) break;

      for (const item of result.items) {
        const msg = this._normalizeFeishuMessage(item);
        if (msg && msg.content) {
          // 时间过滤
          if (mode === 'time') {
            const since = Date.now() - hours * 3600 * 1000;
            if (msg.timestamp < since) continue; // 跳过超时的
          }
          // 去重（查数据库是否已存在）
          if (!DB.query(this.db, 'SELECT 1 FROM messages WHERE message_id = ?', [msg.message_id]).length > 0) {
            allMessages.push(msg);
          }
        }
      }

      pageToken = result.page_token || null;
      pages++;

      if (!pageToken) break;
      if (maxMessages > 0 && allMessages.length >= maxMessages) break;
    }

    return allMessages;
  }

  /**
   * 规范化飞书消息格式
   */
  _normalizeFeishuMessage(item) {
    try {
      const msgType = item.msg_type || 'text';
      let content = '';
      try {
        const parsed = JSON.parse(item.body?.content || item.content || '{}');
        content = parsed.text || parsed.content || item.body?.content || item.content || '';
      } catch {
        content = item.body?.content || item.content || '';
      }

      if (!content) return null;

      return {
        message_id: item.message_id || item.open_message_id,
        chat_id: item.chat_id || item.container_id || 'unknown',
        sender_id: item.sender?.id || item.sender_id || 'unknown',
        sender_name: item.sender?.id?.name || item.sender?.name || item.sender_name || 'unknown',
        content,
        msg_type: msgType,
        metadata: { source: 'feishu_batch', message_type: msgType },
        created_at: item.create_time ? new Date(parseInt(item.create_time)).toISOString() : new Date().toISOString(),
        timestamp: item.create_time ? parseInt(item.create_time) : Date.now(),
      };
    } catch {
      return null;
    }
  }

  /**
   * 处理单个批次
   */
  async _processSingleBatch(chatId, messages, startIdx, batchSize) {
    const batchId = `batch_${this.uuid().slice(0, 12)}`;
    let processed = 0;

    // 1. 逐条处理消息（调用 processMessage 逻辑）
    for (const msg of messages) {
      try {
        await this._processMessage(msg);
        processed++;
      } catch (e) {
        console.warn(`[BatchProcessor] Message ${msg.message_id} failed: ${e.message}`);
      }
    }

    // 2. 生成批次摘要（LLM）
    const summary = await this._generateBatchSummary(messages, batchId);

    // 3. 存入批次摘要表
    DB.exec(this.db,
      `INSERT INTO message_batch_summaries
       (chat_id, batch_id, start_message_id, end_message_id, message_count,
        summary, topics_json, decisions_json, risks_json, action_items_json, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`,
      [
        chatId, batchId,
        messages[0]?.message_id || '',
        messages[messages.length - 1]?.message_id || '',
        messages.length,
        summary?.summary || '',
        JSON.stringify(summary?.topics || []),
        JSON.stringify(summary?.decisions || []),
        JSON.stringify(summary?.risks || []),
        JSON.stringify(summary?.actionItems || []),
      ]
    );

    // 4. 如果批次摘要中提取了决策/风险，也存入 knowledge_items
    if (summary) {
      for (const dec of (summary.decisions || [])) {
        const kid = `k_${this.uuid().slice(0, 12)}`;
        DB.insertKnowledgeItem(this.db, {
          knowledge_id: kid,
          knowledge_type: 'decision',
          title: dec.length > 50 ? dec.slice(0, 50) : dec,
          summary: `[批次摘要] ${dec}`,
          source_refs: [{ type: 'batch', id: batchId, title: `批量处理 ${messages.length} 条消息` }],
          confidence: 0.7,
        });
      }
      for (const risk of (summary.risks || [])) {
        const kid = `k_${this.uuid().slice(0, 12)}`;
        DB.insertKnowledgeItem(this.db, {
          knowledge_id: kid,
          knowledge_type: 'risk',
          title: risk.length > 50 ? risk.slice(0, 50) : risk,
          summary: `[批次摘要] ${risk}`,
          source_refs: [{ type: 'batch', id: batchId, title: `批量处理 ${messages.length} 条消息` }],
          confidence: 0.7,
        });
      }
      for (const action of (summary.actionItems || [])) {
        const kid = `k_${this.uuid().slice(0, 12)}`;
        DB.insertKnowledgeItem(this.db, {
          knowledge_id: kid,
          knowledge_type: 'action_item',
          title: action.length > 50 ? action.slice(0, 50) : action,
          summary: `[批次摘要] ${action}`,
          source_refs: [{ type: 'batch', id: batchId, title: `批量处理 ${messages.length} 条消息` }],
          confidence: 0.7,
        });
      }
    }

    // 5. 标记 EventGraph（整批作为一个事件）
    if (this.eventGraph) {
      try {
        this.eventGraph.addEvent({
          event_id: batchId,
          type: 'batch_summary',
          summary: summary?.summary || `批处理 ${messages.length} 条消息`,
          metadata: { chatId, messageCount: messages.length },
        });
      } catch (e) {}
    }

    DB.persistDatabase(this.db);

    return {
      batchId,
      startIdx,
      total: messages.length,
      processed,
      summary: summary?.summary?.slice(0, 200) || '',
    };
  }

  /**
   * 处理单条消息（复用现有流水线逻辑但改为方法）
   */
  async _processMessage(msg) {
    // 1. 检查去重
    if (DB.isEventProcessed(this.db, msg.message_id)) return;

    // 2. 存原始消息
    DB.insertMessage(this.db, msg);

    // 3. LLM 抽取 + 规则抽取
    let extracted = null;
    if (this.llm && this.llm.available && msg.content) {
      try {
        extracted = await this.llm.extractEntitiesFromMessage(msg);
      } catch (e) {
        console.warn(`[BatchProcessor] LLM extract failed for ${msg.message_id}: ${e.message}`);
      }
    }

    // 4. LLM 抽取结果处理
    const entities = [];
    const relations = [];
    const knowledgeItems = [];

    if (extracted && extracted.entities) {
      for (const e of extracted.entities) {
        entities.push({
          entity_id: `ent_${this.uuid().slice(0, 12)}`,
          entity_type: e.type || 'concept',
          name: e.name,
          aliases: e.aliases || [],
          properties: { source: 'llm', first_seen_in: msg.message_id },
        });
      }

      if (extracted.relations) {
        for (const r of extracted.relations) {
          relations.push({
            source_entity_id: entities.find(e => e.name === r.source)?.entity_id || r.source,
            target_entity_id: entities.find(e => e.name === r.target)?.entity_id || r.target,
            relation_type: r.type || 'related',
            weight: 0.8,
            metadata: { description: r.description || '', source: 'llm' },
            source_message_id: msg.message_id,
          });
        }
      }

      if (extracted.knowledge) {
        for (const k of extracted.knowledge) {
          knowledgeItems.push({
            knowledge_id: `k_${this.uuid().slice(0, 12)}`,
            knowledge_type: k.type || 'info',
            title: k.title,
            summary: k.summary,
            source_refs: [{ type: 'message', id: msg.message_id, title: `来自 ${msg.sender_name}` }],
            confidence: 0.7,
          });
        }
      }
    }

    // 5. 规则抽取（通用规则）
    const ruleEntities = this._ruleBasedEntities(msg);
    for (const re of ruleEntities) {
      if (!entities.some(e => e.name === re.name)) {
        entities.push(re);
      }
    }

    // 6. 存入实体/关系/知识
    for (const entity of entities) {
      DB.upsertEntity(this.db, entity);
    }
    for (const rel of relations) {
      const srcExists = DB.getEntity(this.db, rel.source_entity_id);
      const tgtExists = DB.getEntity(this.db, rel.target_entity_id);
      if (srcExists && tgtExists) {
        DB.insertRelation(this.db, rel);
      }
    }
    for (const ki of knowledgeItems) {
      DB.insertKnowledgeItem(this.db, ki);
    }

    // 7. 规则生成知识项（即使 LLM 失败了也有保底）
    if (knowledgeItems.length === 0 && msg.content) {
      const rules = this._ruleBasedKnowledge(msg);
      for (const ki of rules) {
        DB.insertKnowledgeItem(this.db, ki);
      }
    }

    // 8. 索引到 Hybrid Search
    if (this.hybridSearch && msg.content) {
      try {
        this.hybridSearch.indexDocument(
          msg.message_id,
          `${msg.sender_name}: ${msg.content}`,
          { type: 'message', sourceType: 'im', chatId: msg.chat_id, sender: msg.sender_name },
          msg.created_at
        );
      } catch (e) {}
    }

    // 9. 标记已处理
    DB.markEventProcessed(this.db, msg.message_id, 'message', { chatId: msg.chat_id, content: msg.content?.slice(0, 100) });
  }

  /**
   * 规则实体抽取（保底）
   */
  _ruleBasedEntities(msg) {
    const content = msg.content || '';
    const entities = [];

    // 项目名
    const projectMatch = content.match(/([^\s，。、！？]{2,10}(?:项目|方案|系统|平台|模块|架构))/);
    if (projectMatch) {
      entities.push({
        entity_id: `ent_${this.uuid().slice(0, 12)}`,
        entity_type: 'project',
        name: projectMatch[1],
        aliases: [],
        properties: { source: 'rule', first_seen_in: msg.message_id },
      });
    }

    // 人员（@ 提及）
    const atMatch = content.match(/@([^\s，。、！？]{2,10})/g);
    if (atMatch) {
      for (const at of atMatch) {
        const name = at.replace('@', '');
        entities.push({
          entity_id: `ent_${this.uuid().slice(0, 12)}`,
          entity_type: 'person',
          name,
          aliases: [],
          properties: { source: 'rule', first_seen_in: msg.message_id },
        });
      }
    }

    // 决策关键词
    if (/决定|确认|确定|通过|采用/.test(content)) {
      entities.push({
        entity_id: `ent_${this.uuid().slice(0, 12)}`,
        entity_type: 'decision',
        name: content.slice(0, 30).replace(/[，。！？].*$/, ''),
        aliases: [],
        properties: { source: 'rule', first_seen_in: msg.message_id },
      });
    }

    // 风险关键词
    if (/风险|问题|阻塞|延期|异常/.test(content)) {
      entities.push({
        entity_id: `ent_${this.uuid().slice(0, 12)}`,
        entity_type: 'risk',
        name: content.slice(0, 30).replace(/[，。！？].*$/, ''),
        aliases: [],
        properties: { source: 'rule', first_seen_in: msg.message_id },
      });
    }

    return entities;
  }

  /**
   * 规则知识生成
   */
  _ruleBasedKnowledge(msg) {
    const content = msg.content || '';
    const items = [];

    // 决策
    if (/决定|确认|确定|通过|采用/.test(content)) {
      items.push({
        knowledge_id: `k_${this.uuid().slice(0, 12)}`,
        knowledge_type: 'decision',
        title: content.slice(0, 40),
        summary: `决策: ${content.slice(0, 100)}`,
        source_refs: [{ type: 'message', id: msg.message_id, title: `来自 ${msg.sender_name}` }],
        confidence: 0.4,
      });
    }

    // 风险
    if (/风险|问题|阻塞|延期|异常/.test(content)) {
      items.push({
        knowledge_id: `k_${this.uuid().slice(0, 12)}`,
        knowledge_type: 'risk',
        title: content.slice(0, 40),
        summary: `风险: ${content.slice(0, 100)}`,
        source_refs: [{ type: 'message', id: msg.message_id, title: `来自 ${msg.sender_name}` }],
        confidence: 0.4,
      });
    }

    // 待办
    if (/负责|跟进|完成|需要|assign|下周|下月/.test(content)) {
      items.push({
        knowledge_id: `k_${this.uuid().slice(0, 12)}`,
        knowledge_type: 'action_item',
        title: content.slice(0, 40),
        summary: `待办: ${content.slice(0, 100)}`,
        source_refs: [{ type: 'message', id: msg.message_id, title: `来自 ${msg.sender_name}` }],
        confidence: 0.4,
      });
    }

    return items;
  }

  /**
   * LLM 批次摘要生成
   */
  async _generateBatchSummary(messages, batchId) {
    if (!this.llm || !this.llm.available || messages.length === 0) {
      return { summary: `批处理 ${messages.length} 条消息（无 LLM 摘要）`, topics: [], decisions: [], risks: [], actionItems: [] };
    }

    // 构建批次的聊天文本
    const chatLog = messages.map(m =>
      `[${m.sender_name}] ${m.content}`
    ).join('\n');

    const prompt = `你是一次群聊消息批处理的摘要引擎。分析以下群聊消息批次，提取关键信息。

消息批次（共 ${messages.length} 条）：
${chatLog.slice(0, 4000)}

请分析并返回 JSON（只返回 JSON，不要其他文字）：
{
  "summary": "这个批次的总体摘要（50-150字，概括主要讨论内容）",
  "topics": ["话题1", "话题2", ...]（3-8个话题标签，每个2-10字）,
  "decisions": ["决策1: ...", "决策2: ..."]（讨论中确认的决策）,
  "risks": ["风险1: ...", "风险2: ..."]（提到的风险或问题）,
  "actionItems": ["待办1: ...", "待办2: ..."]（明确的待办事项）
}`;

    try {
      const result = await this.llm.chat([
        { role: 'system', content: '你是群聊消息分析师。输出纯 JSON，不要额外文字。' },
        { role: 'user', content: prompt },
      ], { jsonMode: true });

      if (!result) throw new Error('Empty LLM response');
      return JSON.parse(result);
    } catch (e) {
      console.warn(`[BatchProcessor] Summary generation failed: ${e.message}`);
      // 降级：简单统计
      const topics = [];
      const keywords = ['项目', '架构', '方案', '部署', '需求', 'bug', '测试', '上线'];
      for (const kw of keywords) {
        if (messages.some(m => (m.content || '').includes(kw))) {
          topics.push(kw);
        }
      }
      return {
        summary: `共 ${messages.length} 条消息，涉及 ${topics.length} 个话题。`,
        topics,
        decisions: [],
        risks: [],
        actionItems: [],
      };
    }
  }
}

export default { BatchProcessor };
