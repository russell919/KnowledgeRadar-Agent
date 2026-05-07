/**
 * Knowledge Radar — LLM Client
 *
 * Entity extraction, knowledge summarization, and relationship inference.
 * Supports OpenAI-compatible APIs (OpenAI, DeepSeek, Ark, etc.).
 */

import fetch from 'node-fetch';

export class LLMClient {
  constructor(config = {}) {
    this.baseUrl = config.baseUrl || process.env.LLM_BASE_URL || 'https://api.openai.com/v1';
    this.apiKey = config.apiKey || process.env.LLM_API_KEY || '';
    this.model = config.model || process.env.LLM_MODEL || 'gpt-4o-mini';
    this._available = !!this.apiKey;
  }

  get available() { return this._available; }

  async chat(messages, options = {}) {
    if (!this._available) return null;
    
    const body = {
      model: this.model,
      messages,
      temperature: options.temperature ?? 0.1,
      max_tokens: options.maxTokens ?? 4096,
      response_format: options.jsonMode ? { type: 'json_object' } : undefined,
    };

    try {
      const res = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const text = await res.text().catch(() => '');
        console.warn(`[LLM] API error (${res.status}): ${text.slice(0, 200)}`);
        return null;
      }
      const data = await res.json();
      return data.choices?.[0]?.message?.content || null;
    } catch (e) {
      console.warn(`[LLM] Request failed:`, e.message);
      return null;
    }
  }

  // ── Entity Extraction from Message ──────────────────────────────────────

  async extractEntitiesFromMessage(message) {
    const prompt = `Extract all entities and their relationships from this IM message.

Message: "${message.content}"

Entity types to look for: person, project, task, concept, decision, document, meeting, risk, system

Respond with JSON only:
{
  "entities": [{ "name": "...", "type": "...", "aliases": ["..."] }],
  "relations": [{ "source": "...", "target": "...", "type": "...", "description": "..." }],
  "knowledge": [{ "type": "decision|action_item|risk|update|faq|info", "title": "...", "summary": "..." }]
}`;

    const result = await this.chat([
      { role: 'system', content: 'You are a knowledge extraction engine. Output only valid JSON.' },
      { role: 'user', content: prompt },
    ], { jsonMode: true });

    if (!result) return null;
    try {
      return JSON.parse(result);
    } catch {
      console.warn('[LLM] Failed to parse entity extraction result');
      return null;
    }
  }

  // ── Knowledge Summarization ─────────────────────────────────────────────

  async summarizeKnowledge(items, context) {
    const prompt = `Summarize the following knowledge items into a coherent briefing.

Context: ${context}

Items:
${items.map((i, idx) => `${idx + 1}. [${i.type}] ${i.title}: ${i.summary}`).join('\n')}

Respond with JSON:
{
  "summary": "brief summary paragraph",
  "keyPoints": ["point 1", "point 2"],
  "suggestedActions": ["action 1"]
}`;

    const result = await this.chat([
      { role: 'system', content: 'You are a knowledge management assistant. Output only valid JSON.' },
      { role: 'user', content: prompt },
    ], { jsonMode: true });

    if (!result) return null;
    try {
      return JSON.parse(result);
    } catch {
      return null;
    }
  }

  // ── Meeting Briefing Generation ─────────────────────────────────────────

  async generateMeetingBriefing(meeting, previousMeeting, recentKnowledge) {
    const prompt = `Generate a pre-meeting briefing based on the following data.

Current meeting: ${meeting.title} at ${meeting.startTime}
Description: ${meeting.description || ''}
Participants: ${(meeting.participants || []).map(p => p.name || p).join(', ')}

${previousMeeting ? `Previous meeting decisions:\n${previousMeeting.decisions?.map(d => `- ${d}`).join('\n') || 'None'}\n\nPrevious action items:\n${previousMeeting.actionItems?.map(a => `- ${a.text} (${a.owner}, ${a.status})`).join('\n') || 'None'}` : 'No previous meeting data.'}

${recentKnowledge.length ? `Recent related knowledge:\n${recentKnowledge.map(k => `- [${k.knowledge_type}] ${k.title}: ${k.summary}`).join('\n')}` : ''}

Respond with JSON:
{
  "summary": "Briefing summary in markdown",
  "lastMeetingDecisions": ["decision 1"],
  "pendingActionItems": [{"text": "...", "owner": "..."}],
  "relatedUpdates": [{"title": "...", "detail": "..."}],
  "suggestedTopics": ["discussion topic"]
}`;

    const result = await this.chat([
      { role: 'system', content: 'You are a meeting preparation assistant. Output only valid JSON.' },
      { role: 'user', content: prompt },
    ], { jsonMode: true });

    if (!result) return null;
    try {
      return JSON.parse(result);
    } catch {
      return null;
    }
  }

  // ── Weekly Digest Generation ────────────────────────────────────────────

  async generateWeeklyDigest(knowledgeItems, entities) {
    const prompt = `Generate a weekly knowledge digest from the following data.

Knowledge items this week:
${knowledgeItems.map((k, i) => `${i + 1}. [${k.knowledge_type}] ${k.title}: ${k.summary}`).join('\n')}

Active entities:
${entities.map(e => `- ${e.name} (${e.entity_type})`).join('\n')}

Respond with JSON:
{
  "title": "Weekly Knowledge Digest",
  "sections": [
    {"heading": "...", "items": ["item1", "item2"]}
  ],
  "summary": "overall summary"
}`;

    const result = await this.chat([
      { role: 'system', content: 'You are a knowledge management assistant. Output only valid JSON.' },
      { role: 'user', content: prompt },
    ], { jsonMode: true });

    if (!result) return null;
    try {
      return JSON.parse(result);
    } catch {
      return null;
    }
  }
}
