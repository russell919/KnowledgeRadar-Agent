/**
 * Knowledge Radar — Document Semantic Chunker
 *
 * 文档语义切分 + 独立索引。
 *
 * 分块策略：
 * 1. 按段落（\n\n）为基本分割单位
 * 2. 合并小段落直到达到目标分块大小（~500字）
 * 3. 大段落按句号/分号切分
 * 4. 每个 chunk 独立索引到 Hybrid Search
 */

import * as DB from './database.js';

// ── 配置 ──────────────────────────────────────────────────────────────────

const TARGET_CHUNK_SIZE = 500;   // 目标分块大小（字符数）
const MIN_CHUNK_SIZE = 200;      // 最小分块大小
const MAX_CHUNK_SIZE = 1000;     // 最大分块大小
const OVERLAP_CHARS = 50;        // 块间重叠字符数

// ── 文档切分 ────────────────────────────────────────────────────────────

/**
 * 对文档进行语义切分
 *
 * @param {Object} doc - { doc_id, doc_title, content, metadata }
 * @returns {Array<{chunk_index, content, summary}>}
 */
export function chunkDocument(doc) {
  const content = doc.content || '';
  if (!content || content.length < MIN_CHUNK_SIZE) {
    // 短文档：直接作为一个 chunk
    return [{
      chunk_index: 0,
      content: content,
      summary: content.slice(0, 100),
    }];
  }

  // 1. 按段落分割（连续两个换行）
  const paragraphs = content
    .split(/\n\n+|(?:\r\n){2,}/)
    .map(p => p.trim())
    .filter(p => p.length > 0);

  if (paragraphs.length <= 1) {
    // 没有明显段落分割，按句号切分
    return chunkBySentences(content);
  }

  // 2. 智能合并段落
  const chunks = [];
  let current = '';

  for (const para of paragraphs) {
    const wouldBe = current ? current + '\n\n' + para : para;

    if (wouldBe.length <= MAX_CHUNK_SIZE) {
      current = wouldBe;
    } else {
      // 当前块已满，保存
      if (current.length >= MIN_CHUNK_SIZE) {
        chunks.push(current);
        // 重叠：保留尾部的 OVERLAP_CHARS 个字符
        current = current.slice(-OVERLAP_CHARS) + '\n\n' + para;
      } else {
        chunks.push(wouldBe);
        current = '';
      }
    }
  }

  // 最后的块
  if (current.length >= MIN_CHUNK_SIZE) {
    chunks.push(current);
  } else if (current.length > 0 && chunks.length > 0) {
    // 合并到最后一块
    chunks[chunks.length - 1] += '\n\n' + current;
  }

  // 如果合并后超长，对大块进行二次切分
  const finalChunks = [];
  for (const chunk of chunks) {
    if (chunk.length > MAX_CHUNK_SIZE * 1.5) {
      finalChunks.push(...chunkBySentences(chunk));
    } else {
      finalChunks.push(chunk);
    }
  }

  // 格式化输出
  return finalChunks.map((c, i) => ({
    chunk_index: i,
    content: c,
    summary: extractSummary(c, doc.doc_title || ''),
  }));
}

/**
 * 按句号切分（当没有段落标记时）
 */
function chunkBySentences(text) {
  // 按句号、问号、感叹号、分号切分
  const sentences = text
    .split(/(?<=[。！？；\n])\s*/)
    .map(s => s.trim())
    .filter(s => s.length > 0);

  if (sentences.length <= 1) {
    return [{ chunk_index: 0, content: text, summary: extractSummary(text, '') }];
  }

  const chunks = [];
  let current = '';

  for (const sent of sentences) {
    const wouldBe = current ? current + sent : sent;

    if (wouldBe.length <= TARGET_CHUNK_SIZE || current.length < MIN_CHUNK_SIZE) {
      current = wouldBe;
    } else {
      if (current.length >= MIN_CHUNK_SIZE) {
        chunks.push(current);
        current = sent.slice(-OVERLAP_CHARS) + sent;
      } else {
        current = wouldBe;
      }
    }
  }

  if (current.length >= MIN_CHUNK_SIZE) {
    chunks.push(current);
  } else if (chunks.length > 0) {
    chunks[chunks.length - 1] += current;
  }

  return chunks.map((c, i) => ({
    chunk_index: i,
    content: c,
    summary: extractSummary(c, ''),
  }));
}

/**
 * 提取摘要（取开头 + 关键句）
 */
function extractSummary(content, docTitle) {
  const clean = content.replace(/[#*_~`]/g, '').trim();
  if (clean.length <= 150) return clean;

  // 取前 100 字
  const firstPart = clean.slice(0, 100).replace(/\n.*$/, '');
  // 如果有 docTitle，附加
  return docTitle ? `${docTitle}: ${firstPart}...` : firstPart + '...';
}

// ── 索引到 Hybrid Search ─────────────────────────────────────────────────

/**
 * 切分文档并索引到 Hybrid Search
 *
 * @param {Object} db - SQLite 实例
 * @param {Object} doc - { doc_id, doc_title, content, metadata }
 * @param {Object} hybridSearch - Hybrid Search 实例
 * @returns {number} 生成的 chunk 数量
 */
export function indexDocumentChunks(db, doc, hybridSearch) {
  const chunks = chunkDocument(doc);
  const metadata = doc.metadata || {};

  // 删除旧 chunk（重新索引）
  DB.exec(db, `DELETE FROM document_chunks WHERE doc_id = ?`, [doc.doc_id]);

  for (const chunk of chunks) {
    // 存入 document_chunks 表
    DB.exec(db,
      `INSERT INTO document_chunks (doc_id, doc_title, chunk_index, content, summary, metadata_json, created_at)
       VALUES (?, ?, ?, ?, ?, ?, datetime('now'))`,
      [doc.doc_id, doc.doc_title, chunk.chunk_index, chunk.content, chunk.summary,
       JSON.stringify({ ...metadata, type: 'doc_chunk', docTitle: doc.doc_title })]
    );

    // 索引到 Hybrid Search
    if (hybridSearch) {
      const chunkId = `${doc.doc_id}_chunk_${chunk.chunk_index}`;
      hybridSearch.indexDocument(
        chunkId,
        `${doc.doc_title} - 第${chunk.chunk_index + 1}段: ${chunk.content}`,
        { type: 'doc_chunk', docId: doc.doc_id, chunkIndex: chunk.chunk_index, sourceType: 'doc' },
        new Date().toISOString()
      );
    }
  }

  DB.persistDatabase(db);
  return chunks.length;
}

// ── 查询 Chunk ──────────────────────────────────────────────────────────

/**
 * 按文档 ID 获取所有 chunk
 */
export function getDocumentChunks(db, docId) {
  return DB.query(db,
    `SELECT * FROM document_chunks WHERE doc_id = ? ORDER BY chunk_index ASC`,
    [docId]
  );
}

export default {
  chunkDocument,
  indexDocumentChunks,
  getDocumentChunks,
};
