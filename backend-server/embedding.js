/**
 * Knowledge Radar — Embedding Service
 *
 * Pure JavaScript embedding using character-level n-grams (TF-IDF weighted).
 * Falls back gracefully if external embedding API is unavailable.
 *
 * Chinese text works well with char n-grams because:
 * - Characters carry semantic meaning
 * - Bigrams capture compound words naturally
 * - No tokenizer needed
 * - Fast computation
 */

// ── Character-level N-gram Extraction ────────────────────────────────────

function extractCharNGrams(text, n = 2) {
  const chars = text.replace(/\s+/g, '');
  const grams = {};
  for (let i = 0; i <= chars.length - n; i++) {
    const gram = chars.slice(i, i + n);
    grams[gram] = (grams[gram] || 0) + 1;
  }
  return grams;
}

// ── Global IDF Cache ──────────────────────────────────────────────────────

let globalDocCount = 0;
let globalDocFreq = {};  // { gram: docCount }

export function updateIDF(documents) {
  // documents: array of { text: string }
  const df = {};
  for (const doc of documents) {
    const grams = extractCharNGrams(doc.text || '', 2);
    const seen = new Set();
    for (const gram of Object.keys(grams)) {
      if (!seen.has(gram)) {
        df[gram] = (df[gram] || 0) + 1;
        seen.add(gram);
      }
    }
  }
  globalDocCount += documents.length;
  for (const [gram, count] of Object.entries(df)) {
    globalDocFreq[gram] = (globalDocFreq[gram] || 0) + count;
  }
}

export function setGlobalIDF(docCount, docFreq) {
  globalDocCount = docCount;
  globalDocFreq = { ...docFreq };
}

export function getGlobalIDF() {
  return { docCount: globalDocCount, docFreq: { ...globalDocFreq } };
}

function idf(gram) {
  if (globalDocCount === 0) return 1.0;
  const df = globalDocFreq[gram] || 0;
  return Math.log((globalDocCount + 1) / (df + 1)) + 1;
}

// ── Embedding Generation ──────────────────────────────────────────────────

const NGRAM_SIZES = [2, 3];  // Bi-gram and tri-gram

/**
 * Generate a sparse embedding vector from text.
 * Returns { indices: number[], values: number[], dim: number }
 * where indices are hash positions in a fixed-size vector space.
 */
export function textToEmbedding(text) {
  if (!text || typeof text !== 'string') {
    return { indices: [], values: [], dim: 4096 };
  }

  // Combine character n-grams of different sizes
  const allGrams = {};
  for (const n of NGRAM_SIZES) {
    const grams = extractCharNGrams(text, n);
    for (const [gram, count] of Object.entries(grams)) {
      allGrams[gram] = (allGrams[gram] || 0) + count;
    }
  }

  // Normalize by text length
  const totalGrams = Object.values(allGrams).reduce((a, b) => a + b, 0);
  if (totalGrams === 0) return { indices: [], values: [], dim: 4096 };

  // Hash grams into a fixed-size vector space (4096 dimensions)
  const VECTOR_DIM = 4096;
  const vector = new Float64Array(VECTOR_DIM);

  for (const [gram, count] of Object.entries(allGrams)) {
    // Use multiple hash positions for each gram (locality-sensitive hashing style)
    const tf = count / totalGrams;
    const weight = tf * idf(gram);
    const hash = hashString(gram);
    const pos1 = hash % VECTOR_DIM;
    const pos2 = (hash * 31 + 7) % VECTOR_DIM;
    const pos3 = (hash * 17 + 13) % VECTOR_DIM;
    vector[pos1] += weight * 0.5;
    vector[pos2] += weight * 0.3;
    vector[pos3] += weight * 0.2;
  }

  // L2 normalize
  let norm = 0;
  for (let i = 0; i < VECTOR_DIM; i++) norm += vector[i] * vector[i];
  norm = Math.sqrt(norm);
  if (norm > 0) {
    for (let i = 0; i < VECTOR_DIM; i++) vector[i] /= norm;
  }

  return { indices: [...Array(VECTOR_DIM).keys()], values: Array.from(vector), dim: VECTOR_DIM };
}

/**
 * Generate dense embedding for external API use (future: replace with real model).
 * Returns an array of floats.
 */
export async function embedding(text) {
  const result = textToEmbedding(text);
  return result.values;
}

// ── Cosine Similarity ─────────────────────────────────────────────────────

export function cosineSimilarity(a, b) {
  if (!a || !b || a.length !== b.length) return 0;
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  return denom === 0 ? 0 : dot / denom;
}

export function cosineSimilaritySparse(a, b) {
  return cosineSimilarity(a.values, b.values);
}

// ── Utility ───────────────────────────────────────────────────────────────

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const chr = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + chr;
    hash |= 0; // Convert to 32bit integer
  }
  return Math.abs(hash);
}

/**
 * Pre-compute embeddings for a batch of texts and store in a Map.
 */
export function computeEmbeddingMap(items) {
  const map = new Map();
  for (const item of items) {
    if (item.id && item.text) {
      map.set(item.id, textToEmbedding(item.text));
    }
  }
  return map;
}

export default {
  textToEmbedding,
  cosineSimilarity,
  cosineSimilaritySparse,
  computeEmbeddingMap,
  embedding,
  updateIDF,
  setGlobalIDF,
  getGlobalIDF,
};
