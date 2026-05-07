/**
 * Knowledge Radar — Reranker
 *
 * Lightweight cross-encoder style reranker using overlap-based scoring.
 * In production, this would be replaced with a BGE-Reranker model.
 *
 * Current approach uses a multi-signal scoring function:
 * - Query-document token overlap (TF-IDF weighted)
 * - Entity overlap (matching named entities)
 * - Term proximity (how close query terms appear in the document)
 */

// ── Simple Token Overlap Scoring ──────────────────────────────────────────

function extractKeywords(text) {
  if (!text) return [];
  const chars = text.replace(/\s+/g, '');
  const keywords = new Set();
  
  // Extract all bigrams and trigrams
  for (let n = 2; n <= 3; n++) {
    for (let i = 0; i <= chars.length - n; i++) {
      keywords.add(chars.slice(i, i + n));
    }
  }
  // Add single characters too
  for (const ch of chars) {
    if (/[\u4e00-\u9fff]/.test(ch)) keywords.add(ch);
  }
  
  return Array.from(keywords);
}

function computeOverlap(queryKeywords, docKeywords) {
  if (queryKeywords.length === 0 || docKeywords.length === 0) return 0;
  
  const docSet = new Set(docKeywords);
  let matches = 0;
  
  for (const kw of queryKeywords) {
    if (docSet.has(kw)) matches++;
  }
  
  return matches / queryKeywords.length;
}

function computeTfIdfOverlap(query, docText) {
  // Compute TF-IDF weighted overlap score
  const queryTokens = extractKeywords(query);
  const docTokens = extractKeywords(docText);
  const docFreq = {};
  
  for (const token of docTokens) {
    docFreq[token] = (docFreq[token] || 0) + 1;
  }
  
  let score = 0;
  const docLen = docTokens.length || 1;
  const queryLen = queryTokens.length || 1;
  
  for (const qt of queryTokens) {
    const tf = (docFreq[qt] || 0) / (docLen + 1);
    score += tf;
  }
  
  return score / queryLen;
}

// ── Entity Matching ───────────────────────────────────────────────────────

function extractEntities(text) {
  // Simple entity detection: look for known patterns
  const entities = new Set();
  
  // Chinese person names (2-3 characters)
  const namePattern = /[\u4e00-\u9fff]{2,3}(?=负责|参与|提出|建议|决定|说|表示|认为|指出)/g;
  let match;
  while ((match = namePattern.exec(text)) !== null) {
    entities.add(match[0]);
  }
  
  // Project/concept mentions (at least 4 chars)
  const conceptPattern = /[\u4e00-\u9fff\u0020]{4,20}(?=方案|系统|项目|模块|架构|设计|平台)/g;
  while ((match = conceptPattern.exec(text)) !== null) {
    entities.add(match[0].trim());
  }
  
  return Array.from(entities);
}

function computeEntityOverlap(query, docText) {
  const queryEntities = extractEntities(query);
  const docEntities = extractEntities(docText);
  
  if (queryEntities.length === 0) return 0.5; // Neutral if no entities in query
  
  const docSet = new Set(docEntities);
  let matches = 0;
  for (const e of queryEntities) {
    if (docSet.has(e)) matches++;
    // Also check if entity name appears in doc text
    else if (docText.includes(e)) matches += 0.5;
  }
  
  return matches / queryEntities.length;
}

// ── Term Proximity ────────────────────────────────────────────────────────

function computeTermProximity(query, docText) {
  const queryChars = query.replace(/\s+/g, '');
  if (queryChars.length < 2) return 0;
  
  const positions = [];
  for (const ch of queryChars) {
    const pos = docText.indexOf(ch);
    if (pos >= 0) positions.push(pos);
  }
  
  if (positions.length < 2) return 0;
  
  // Calculate average distance between consecutive query character positions
  let totalDist = 0;
  for (let i = 1; i < positions.length; i++) {
    totalDist += Math.abs(positions[i] - positions[i - 1]);
  }
  const avgDist = totalDist / (positions.length - 1);
  
  // Convert to score: closer = better
  return Math.max(0, 1 - avgDist / Math.max(docText.length, 1));
}

// ── Reranker Class ────────────────────────────────────────────────────────

export class Reranker {
  constructor() {
    // Weights for each scoring signal
    this.weights = {
      tokenOverlap: 0.3,
      tfidfOverlap: 0.25,
      entityOverlap: 0.25,
      termProximity: 0.2,
    };
  }

  /**
   * Rerank a list of search results based on query-document relevance.
   * @param {string} query - Original search query
   * @param {Array} results - Search results with {id, text, scores}
   * @returns {Array} Reranked results with updated scores
   */
  rerank(query, results) {
    if (!results || results.length === 0) return results;
    
    const queryKeywords = extractKeywords(query);
    
    const scored = results.map(doc => {
      const docText = doc.text || '';
      const docKeywords = extractKeywords(docText);
      
      // Compute individual signals
      const tokenOverlap = computeOverlap(queryKeywords, docKeywords);
      const tfidfOverlap = computeTfIdfOverlap(query, docText);
      const entityOverlap = computeEntityOverlap(query, docText);
      const termProximity = computeTermProximity(query, docText);
      
      // Combined reranker score
      const rerankerScore = 
        this.weights.tokenOverlap * tokenOverlap +
        this.weights.tfidfOverlap * tfidfOverlap +
        this.weights.entityOverlap * entityOverlap +
        this.weights.termProximity * termProximity;
      
      // Final score: blend original with reranker
      const originalScore = doc.score || 0;
      const combinedScore = 0.7 * originalScore + 0.3 * rerankerScore;
      
      return {
        ...doc,
        score: combinedScore,
        scores: {
          ...doc.scores,
          reranker: rerankerScore,
          reranker_signals: {
            tokenOverlap,
            tfidfOverlap,
            entityOverlap,
            termProximity,
          },
        },
      };
    });
    
    // Sort by new score
    scored.sort((a, b) => b.score - a.score);
    return scored;
  }

  toJSON() {
    return { weights: { ...this.weights } };
  }

  static fromJSON(data) {
    const r = new Reranker();
    if (data.weights) r.weights = { ...data.weights };
    return r;
  }
}

export default { Reranker };
