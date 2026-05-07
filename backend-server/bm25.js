/**
 * Knowledge Radar — BM25 Ranking
 *
 * Pure JavaScript BM25 implementation for Chinese text.
 * Uses character-level unigrams and bigrams as terms.
 */

// ── BM25 Parameters ──────────────────────────────────────────────────────

const K1 = 1.5;   // Term frequency saturation
const B = 0.75;   // Length normalization
const K3 = 0;     // Query term frequency (not used for short queries)

// ── Tokenization ─────────────────────────────────────────────────────────

/**
 * Tokenize Chinese text into searchable tokens.
 * Uses both unigrams (single chars) and bigrams (character pairs).
 */
function tokenize(text) {
  if (!text || typeof text !== 'string') return [];
  const chars = text.replace(/\s+/g, '');
  const tokens = new Set();
  
  // Unigrams (single Chinese characters)
  for (const ch of chars) {
    if (/[\u4e00-\u9fff]/.test(ch)) {
      tokens.add(ch);
    }
  }
  
  // Bigrams (character pairs)
  for (let i = 0; i < chars.length - 1; i++) {
    const bigram = chars.slice(i, i + 2);
    if (/[\u4e00-\u9fff]/.test(bigram[0]) || /[\u4e00-\u9fff]/.test(bigram[1])) {
      tokens.add(bigram);
    }
  }

  // Also include the original text as a single "phrase" for exact matching
  if (chars.length > 0 && chars.length <= 50) {
    tokens.add(chars);
  }

  return Array.from(tokens);
}

// ── BM25 Index ───────────────────────────────────────────────────────────

export class BM25Index {
  constructor() {
    this.documents = [];
    this.docCount = 0;
    this.avgDocLength = 0;
    this.docLengths = [];
    this.invertedIndex = {};  // token -> { docId: termFreq, ... }
    this.docTokenCache = {};  // docId -> tokens[]
  }

  /**
   * Add a document to the index.
   * @param {string} docId - Unique document identifier
   * @param {string} text - Document text content
   */
  addDocument(docId, text) {
    const tokens = tokenize(text);
    this.docTokenCache[docId] = tokens;
    
    const termFreq = {};
    for (const token of tokens) {
      termFreq[token] = (termFreq[token] || 0) + 1;
    }

    for (const [token, freq] of Object.entries(termFreq)) {
      if (!this.invertedIndex[token]) {
        this.invertedIndex[token] = {};
      }
      this.invertedIndex[token][docId] = freq;
    }

    this.documents.push({ id: docId, text, length: tokens.length });
    this.docLengths.push(tokens.length);
    this.docCount++;
    this.avgDocLength = this.docLengths.reduce((a, b) => a + b, 0) / this.docCount;
  }

  /**
   * Remove a document from the index.
   */
  removeDocument(docId) {
    this.documents = this.documents.filter(d => d.id !== docId);
    const idx = this.documents.findIndex(d => d.id === docId);
    if (idx >= 0) {
      this.docLengths.splice(idx, 1);
      this.docCount--;
      this.avgDocLength = this.docCount > 0 
        ? this.docLengths.reduce((a, b) => a + b, 0) / this.docCount 
        : 0;
    }
    
    const tokens = this.docTokenCache[docId] || [];
    delete this.docTokenCache[docId];
    
    for (const token of tokens) {
      if (this.invertedIndex[token]) {
        delete this.invertedIndex[token][docId];
        if (Object.keys(this.invertedIndex[token]).length === 0) {
          delete this.invertedIndex[token];
        }
      }
    }
  }

  /**
   * Search the index and return ranked results.
   * @param {string} query - Search query
   * @param {number} topK - Number of results to return
   * @returns {Array<{id: string, score: number, text: string}>}
   */
  search(query, topK = 10) {
    const queryTokens = tokenize(query);
    if (queryTokens.length === 0) return [];

    // Calculate BM25 score for each document
    const scores = {};

    for (const qt of queryTokens) {
      const posting = this.invertedIndex[qt];
      if (!posting) continue;

      const qf = 1; // Query term frequency (assume 1 for non-repeating query)
      const df = Object.keys(posting).length;
      const idf = Math.log((this.docCount - df + 0.5) / (df + 0.5) + 1);

      for (const [docId, tf] of Object.entries(posting)) {
        const doc = this.documents.find(d => d.id === docId);
        if (!doc) continue;
        const docLen = doc.length;
        const score = idf * ((tf * (K1 + 1)) / (tf + K1 * (1 - B + B * (docLen / this.avgDocLength))));
        scores[docId] = (scores[docId] || 0) + score;
      }
    }

    // Sort by score descending
    const results = Object.entries(scores)
      .map(([id, score]) => {
        const doc = this.documents.find(d => d.id === id);
        return { id, score, text: doc ? doc.text : '' };
      })
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);

    return results;
  }

  /**
   * Get the number of documents in the index.
   */
  size() {
    return this.docCount;
  }

  /**
   * Serialize the index to JSON.
   */
  toJSON() {
    return {
      documents: this.documents,
      docCount: this.docCount,
      avgDocLength: this.avgDocLength,
      docLengths: this.docLengths,
      invertedIndex: this.invertedIndex,
      docTokenCache: this.docTokenCache,
    };
  }

  /**
   * Deserialize from JSON.
   */
  static fromJSON(data) {
    const index = new BM25Index();
    index.documents = data.documents || [];
    index.docCount = data.docCount || 0;
    index.avgDocLength = data.avgDocLength || 0;
    index.docLengths = data.docLengths || [];
    index.invertedIndex = data.invertedIndex || {};
    index.docTokenCache = data.docTokenCache || {};
    return index;
  }
}

export function tokenizeText(text) {
  return tokenize(text);
}

export default { BM25Index, tokenizeText };
