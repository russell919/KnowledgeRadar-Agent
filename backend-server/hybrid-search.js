/**
 * Knowledge Radar — Hybrid Search Engine
 *
 * Combines:
 * 1. Semantic retrieval (TF-IDF char n-gram embedding + cosine similarity)
 * 2. Keyword retrieval (BM25)
 * 3. Metadata filtering
 * 4. Reranker scoring
 *
 * Produces a unified ranked result set.
 */

import { textToEmbedding, cosineSimilarity, updateIDF } from './embedding.js';
import { BM25Index } from './bm25.js';
import { Reranker } from './reranker.js';

// ── Hybrid Search Config ──────────────────────────────────────────────────

const DEFAULT_CONFIG = {
  semanticWeight: 0.4,    // Weight for semantic similarity score
  keywordWeight: 0.4,     // Weight for BM25 keyword score
  recencyWeight: 0.1,     // Weight for recency boost
  authorityWeight: 0.1,   // Weight for source authority
  topK: 20,               // Max results to return
};

// ── Hybrid Search Engine ─────────────────────────────────────────────────

export class HybridSearch {
  constructor(config = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.bm25 = new BM25Index();
    this.reranker = new Reranker();
    this.documents = new Map(); // id -> { id, text, metadata, embedding, createdAt }
    this.embeddingCache = new Map(); // id -> Float64Array
  }

  /**
   * Index a document for hybrid search.
   * @param {string} id - Unique document identifier
   * @param {string} text - Document text content
   * @param {Object} metadata - Document metadata (type, source, author, etc.)
   * @param {string} createdAt - ISO datetime string
   */
  indexDocument(id, text, metadata = {}, createdAt = null) {
    const doc = { id, text, metadata: { ...metadata }, createdAt };
    this.documents.set(id, doc);
    
    // Add to BM25 index
    this.bm25.addDocument(id, text);
    
    // Compute embedding
    const emb = textToEmbedding(text);
    this.embeddingCache.set(id, emb);
    
    return doc;
  }

  /**
   * Remove a document from the index.
   */
  removeDocument(id) {
    this.documents.delete(id);
    this.bm25.removeDocument(id);
    this.embeddingCache.delete(id);
  }

  /**
   * Update IDF statistics from all indexed documents.
   */
  updateStatistics() {
    const docs = Array.from(this.documents.values());
    updateIDF(docs.map(d => ({ text: d.text })));
    
    // Recompute all embeddings with updated IDF
    for (const [id, doc] of this.documents) {
      this.embeddingCache.set(id, textToEmbedding(doc.text));
    }
  }

  /**
   * Search across indexed documents.
   * @param {string} query - Search query
   * @param {Object} options
   * @param {number} options.topK - Max results
   * @param {Object} options.filter - Metadata filters
   * @param {string} options.filter.type - Filter by document type
   * @param {string} options.filter.sourceType - Filter by source type
   * @param {number} options.filter.sinceDays - Only include documents from last N days
   * @param {string} options.userId - User ID for permission filtering
   * @returns {Array<{id, text, metadata, score, scores: {semantic, keyword, recency, authority, reranker}}>}
   */
  search(query, options = {}) {
    const topK = options.topK || this.config.topK;
    const filter = options.filter || {};

    // 1. Semantic retrieval — compute query embedding
    const queryEmb = textToEmbedding(query);

    // 2. BM25 keyword retrieval
    const bm25Results = this.bm25.search(query, this.documents.size);

    // 3. Score each document
    const candidates = new Map();

    for (const [id, doc] of this.documents) {
      // Apply metadata filters
      if (filter.type && doc.metadata.type !== filter.type) continue;
      if (filter.sourceType && doc.metadata.sourceType !== filter.sourceType) continue;
      if (filter.sinceDays && doc.createdAt) {
        const since = new Date(Date.now() - filter.sinceDays * 86400000);
        if (new Date(doc.createdAt) < since) continue;
      }
      // Permission filter: skip if private and not allowed
      if (filter.allowedUserIds && doc.metadata.permission === 'private' 
          && !(filter.allowedUserIds || []).includes('*')) {
        if (!doc.metadata.allowedUsers || !doc.metadata.allowedUsers.some(u => 
          (filter.allowedUserIds || []).includes(u))) {
          continue;
        }
      }

      // Semantic score
      const emb = this.embeddingCache.get(id);
      const semanticScore = emb ? cosineSimilarity(queryEmb.values, emb.values) : 0;

      // BM25 score
      const bm25Result = bm25Results.find(r => r.id === id);
      const keywordScore = bm25Result ? bm25Result.score / (bm25Results[0]?.score || 1) : 0;

      // Recency score (newer is better, decay over 30 days)
      let recencyScore = 0;
      if (doc.createdAt) {
        const ageDays = (Date.now() - new Date(doc.createdAt).getTime()) / 86400000;
        recencyScore = Math.max(0, 1 - ageDays / 30);
      }

      // Authority score (based on source type)
      const authorityScore = getAuthorityScore(doc.metadata);

      candidates.set(id, {
        id: doc.id,
        text: doc.text,
        metadata: doc.metadata,
        scores: {
          semantic: semanticScore,
          keyword: keywordScore,
          recency: recencyScore,
          authority: authorityScore,
        },
      });
    }

    // 4. Compute combined score
    const { semanticWeight, keywordWeight, recencyWeight, authorityWeight } = this.config;
    const results = Array.from(candidates.values()).map(c => {
      c.score = 
        semanticWeight * c.scores.semantic +
        keywordWeight * c.scores.keyword +
        recencyWeight * c.scores.recency +
        authorityWeight * c.scores.authority;
      return c;
    });

    // 5. Sort and truncate
    results.sort((a, b) => b.score - a.score);
    const topResults = results.slice(0, topK);

    // 6. Apply reranker on top results
    if (topResults.length > 0) {
      const reranked = this.reranker.rerank(query, topResults);
      return reranked.map((r, i) => ({
        ...r,
        rank: i + 1,
        scores: { ...r.scores, reranker: r.scores.reranker || 0 },
      }));
    }

    return topResults;
  }

  /**
   * Get total indexed document count.
   */
  size() {
    return this.documents.size;
  }

  /**
   * Serialize index to JSON.
   */
  toJSON() {
    const docs = Array.from(this.documents.entries()).map(([id, doc]) => ({
      id, text: doc.text, metadata: doc.metadata, createdAt: doc.createdAt,
      embedding: Array.from(this.embeddingCache.get(id)?.values || []),
    }));
    return {
      config: this.config,
      documents: docs,
      bm25: this.bm25.toJSON(),
      reranker: this.reranker.toJSON(),
    };
  }

  /**
   * Deserialize from JSON.
   */
  static fromJSON(data) {
    const engine = new HybridSearch(data.config);
    engine.reranker = Reranker.fromJSON(data.reranker || {});
    engine.bm25 = BM25Index.fromJSON(data.bm25 || {});
    
    for (const docData of (data.documents || [])) {
      engine.documents.set(docData.id, {
        id: docData.id,
        text: docData.text,
        metadata: docData.metadata || {},
        createdAt: docData.createdAt,
      });
      const emb = { indices: [], values: docData.embedding || [], dim: docData.embedding?.length || 0 };
      engine.embeddingCache.set(docData.id, emb);
    }
    
    return engine;
  }
}

// ── Authority Score ───────────────────────────────────────────────────────

function getAuthorityScore(metadata) {
  const sourceType = metadata?.sourceType || metadata?.source_type || '';
  const type = metadata?.type || '';
  
  // Authority ranking by source type
  const authorityMap = {
    'meeting': 1.0,        // Meeting notes / decisions
    'decision': 1.0,       // Explicit decisions
    'document': 0.8,       // Formal documents
    'doc': 0.8,
    'wiki': 0.8,
    'calendar_event': 0.7, // Calendar events
    'task': 0.7,           // Tasks
    'action_item': 0.7,
    'im': 0.5,             // IM messages
    'message': 0.5,
    'bitable': 0.6,        // Multi-dimensional tables
  };
  
  return authorityMap[sourceType] || authorityMap[type] || 0.5;
}

export default { HybridSearch };
