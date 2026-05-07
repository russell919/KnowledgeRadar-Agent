/**
 * Knowledge Radar — FAQ Miner
 *
 * 高频问题自动聚类 + FAQ 候选生成
 *
 * 工作流程：
 * 1. 从消息历史中提取用户提问（含"?"）和带追问的对话
 * 2. 聚类相似问题（字符级 Jaccard + Embedding 相似度）
 * 3. 聚类内取最佳答案（选置信度最高的，或由 LLM 生成）
 * 4. 存入 faq_candidates 表，状态为 'candidate'
 * 5. 人工确认后改为 'published'
 */

import * as DB from './database.js';

// ── 配置 ──────────────────────────────────────────────────────────────────

const SIMILARITY_THRESHOLD = 0.6;  // 聚类相似度阈值
const MAX_CANDIDATES = 50;         // 最多保留的候选数
const MIN_FREQUENCY = 2;           // 最少出现次数才视为高频

// ── FAQ Mining ────────────────────────────────────────────────────────────

/**
 * 从消息历史中挖掘 FAQ 候选
 *
 * @param {Object} db - SQLite 数据库实例
 * @param {Object} options
 * @param {number} options.days - 回溯天数（默认30）
 * @param {number} options.minFreq - 最小频次（默认2）
 * @param {Object} llm - LLM 客户端（可选，提供时用于生成答案摘要）
 * @returns {Array<Object>} 新发现的 FAQ 候选列表
 */
export function mineFaqs(db, options = {}, llm = null) {
  const days = options.days || 30;
  const minFreq = options.minFreq || MIN_FREQUENCY;
  const threshold = options.threshold || SIMILARITY_THRESHOLD;

  // 1. 获取消息历史
  const since = new Date(Date.now() - days * 24 * 3600 * 1000).toISOString();
  const messages = DB.query(db,
    `SELECT * FROM messages WHERE content IS NOT NULL AND created_at >= ? ORDER BY created_at ASC LIMIT 500`,
    [since]
  );

  if (messages.length === 0) return [];

  // 2. 提取问题类消息（含"?"/如何/怎么/为什么/啥是/什么是）
  const questions = messages.filter(m => {
    const c = m.content || '';
    return /[?？]|如何|怎么|为什么|啥是|什么是|怎样|是否|能不能|有没有|可否|请教|请问/.test(c);
  });

  if (questions.length < 2) return [];

  // 3. 聚类相似问题（使用文本嵌入的 Jaccard 近似）
  const clusters = clusterQuestions(questions, threshold);

  // 4. 为每个聚类生成 FAQ 候选
  const candidates = [];
  for (const cluster of clusters) {
    if (cluster.length < minFreq) continue;

    // 取最完整的提问作为问题
    const bestQuestion = cluster.sort((a, b) => (b.content || '').length - (a.content || '').length)[0];
    const question = bestQuestion.content.slice(0, 200).trim();

    // 寻找可能包含答案的后续消息
    const answers = findAnswers(db, cluster, messages);

    // 生成答案
    let answer = '';
    if (answers.length > 0) {
      answer = answers.sort((a, b) => (b.content || '').length - (a.content || '').length)[0].content.slice(0, 500);
    } else if (llm && llm.available) {
      // 如果有 LLM，尝试生成答案
      try {
        answer = '(待生成)';
      } catch {}
    }

    // 计算置信度 = 频次占比 * 答案完整度
    const frequency = cluster.length;
    const confidence = Math.min(0.95, 0.3 + (frequency / Math.max(clusters.length, 1)) * 0.5 + (answer.length > 50 ? 0.2 : 0));

    // 提取来源 ID
    const sourceIds = cluster.map(m => m.message_id || m.id).filter(Boolean);

    // 提取项目/话题标签
    const tags = extractTags(cluster);

    candidates.push({
      question,
      answer: answer || '',
      source_ids: JSON.stringify(sourceIds),
      confidence: Math.round(confidence * 100) / 100,
      frequency,
      tags: JSON.stringify(tags),
      status: 'candidate',
      project: tags[0] || '',
    });
  }

  // 5. 存入 DB（去重）
  let savedCount = 0;
  for (const c of candidates) {
    // 检查是否已存在相似问题
    const existing = DB.query(db,
      `SELECT id, question FROM faq_candidates WHERE question LIKE ? AND status != 'rejected' LIMIT 1`,
      [`%${c.question.slice(0, 30)}%`]
    );
    if (existing.length === 0) {
      DB.exec(db,
        `INSERT INTO faq_candidates (question, answer, source_ids_json, confidence, frequency, tags_json, status, project)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [c.question, c.answer, c.source_ids, c.confidence, c.frequency, c.tags, c.status, c.project]
      );
      savedCount++;
    } else {
      // 更新已有 FAQ 的频次
      DB.exec(db,
        `UPDATE faq_candidates SET frequency = frequency + 1, updated_at = datetime('now') WHERE id = ?`,
        [existing[0].id]
      );
    }
  }

  // 限制候选数量
  const allCandidates = DB.query(db,
    `SELECT * FROM faq_candidates WHERE status = 'candidate' ORDER BY frequency DESC`
  );
  if (allCandidates.length > MAX_CANDIDATES) {
    const toDelete = allCandidates.slice(MAX_CANDIDATES).map(c => c.id);
    for (const id of toDelete) {
      DB.exec(db, `DELETE FROM faq_candidates WHERE id = ?`, [id]);
    }
  }

  DB.persistDatabase(db);
  return candidates.slice(0, savedCount > 0 ? undefined : 0);
}

/**
 * 按项目获取已发布的 FAQ
 */
export function getFaqsForProject(db, projectName, limit = 20) {
  if (projectName) {
    return DB.query(db,
      `SELECT * FROM faq_candidates WHERE status = 'published' AND project LIKE ? ORDER BY frequency DESC LIMIT ?`,
      [`%${projectName}%`, limit]
    );
  }
  return DB.query(db,
    `SELECT * FROM faq_candidates WHERE status = 'published' ORDER BY frequency DESC LIMIT ?`,
    [limit]
  );
}

/**
 * 审核 FAQ：接受/拒绝
 */
export function reviewFaq(db, faqId, action, answer) {
  if (action === 'publish') {
    const updates = answer ? `answer = ?, ` : '';
    DB.exec(db,
      `UPDATE faq_candidates SET status = 'published', ${updates}updated_at = datetime('now') WHERE id = ?`,
      answer ? [answer, faqId] : [faqId]
    );
    return { success: true, status: 'published' };
  }
  if (action === 'reject') {
    DB.exec(db, `UPDATE faq_candidates SET status = 'rejected', updated_at = datetime('now') WHERE id = ?`, [faqId]);
    return { success: true, status: 'rejected' };
  }
  return { success: false, error: `Unknown action: ${action}` };
}

// ── 内部方法 ────────────────────────────────────────────────────────────

/**
 * 聚类相似问题（贪心聚类）
 */
function clusterQuestions(questions, threshold) {
  const clusters = [];
  const assigned = new Set();

  for (let i = 0; i < questions.length; i++) {
    if (assigned.has(i)) continue;
    const cluster = [questions[i]];
    assigned.add(i);

    for (let j = i + 1; j < questions.length; j++) {
      if (assigned.has(j)) continue;
      const sim = textSimilarity(questions[i].content || '', questions[j].content || '');
      if (sim >= threshold) {
        cluster.push(questions[j]);
        assigned.add(j);
      }
    }

    clusters.push(cluster);
  }

  return clusters;
}

/**
 * 文本相似度（字符级 Jaccard + 长度归一化）
 */
function textSimilarity(a, b) {
  if (!a || !b) return 0;
  if (a === b) return 1;

  // 短文本用字符级 Jaccard
  const setA = new Set(a);
  const setB = new Set(b);
  const intersect = new Set([...setA].filter(x => setB.has(x)));
  const union = new Set([...setA, ...setB]);
  const jaccard = union.size > 0 ? intersect.size / union.size : 0;

  // 长度惩罚（差异太大则降低相似度）
  const lenRatio = Math.min(a.length, b.length) / Math.max(a.length, b.length);
  return jaccard * Math.min(1, lenRatio * 1.5);
}

/**
 * 在问题后面的消息中寻找答案
 */
function findAnswers(db, cluster, allMessages) {
  const answers = [];
  const lastQuestion = cluster[cluster.length - 1];
  const lastIdx = allMessages.indexOf(lastQuestion);

  // 取问题后面的 5 条消息作为候选答案
  for (let i = lastIdx + 1; i < Math.min(lastIdx + 6, allMessages.length); i++) {
    const msg = allMessages[i];
    const c = msg.content || '';
    // 跳过新的问题
    if (/[?？]$/.test(c.trim())) break;
    // 答案通常比问题长
    if (c.length > 10) {
      answers.push(msg);
    }
  }

  return answers;
}

/**
 * 从聚类中提取标签
 */
function extractTags(cluster) {
  const tagSet = new Set();
  for (const m of cluster) {
    const c = m.content || '';
    // 提取项目名（含"项目"的词汇）
    const projectMatch = c.match(/([^\s，。,\.]+项目)/);
    if (projectMatch) tagSet.add(projectMatch[1]);
    // 提取系统名
    const sysMatch = c.match(/([^\s，。]{2,8}(系统|平台|模块|方案))/);
    if (sysMatch) tagSet.add(sysMatch[0]);
    // 提取主题标签
    const topicMatch = c.match(/(如何|怎么)([^\s，。]{2,20})/);
    if (topicMatch) tagSet.add(topicMatch[0].slice(2));
  }
  return [...tagSet].slice(0, 5);
}

export default {
  mineFaqs,
  getFaqsForProject,
  reviewFaq,
};
