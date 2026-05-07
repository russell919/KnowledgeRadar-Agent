/**
 * Knowledge Radar — Lightweight Event Graph (轻量事件图)
 *
 * Tracks high-value events around projects, problems, documents, and tasks.
 * Unlike a full timeline knowledge graph, this focuses on event-centric relationships:
 * - An event is triggered by a message, document change, meeting, or task update
 * - Events are connected via shared entities (people, projects, documents)
 * - Only high-value events are stored (decisions, task assignments, risks, document changes)
 *
 * This enables "what's the context around this project/decision/person?" queries
 * without building a full temporal knowledge graph.
 */

// ── Event Types ──────────────────────────────────────────────────────────

const HIGH_VALUE_EVENT_TYPES = [
  'decision_made',
  'task_assigned',
  'task_completed',
  'risk_identified',
  'risk_resolved',
  'document_updated',
  'meeting_held',
  'question_asked',
  'question_answered',
  'project_started',
  'milestone_reached',
];

// ── Event Graph ──────────────────────────────────────────────────────────

export class EventGraph {
  constructor() {
    this.events = new Map();       // eventId -> Event
    this.entityEvents = new Map(); // entityName -> Set<eventId>
    this.eventChains = new Map();  // chainId -> { events: [], entities: [] }
  }

  /**
   * Add a high-value event to the graph.
   * @param {Object} event
   * @param {string} event.id - Unique event ID
   * @param {string} event.type - Event type (from HIGH_VALUE_EVENT_TYPES)
   * @param {string} event.summary - Short event description
   * @param {string[]} event.entities - Related entity names (people, projects, docs)
   * @param {string} event.sourceId - Original message/document ID
   * @param {string} event.sourceType - 'message' | 'document' | 'calendar' | 'task'
   * @param {string} event.createdAt - ISO datetime
   * @param {string} event.chainId - Optional chain ID for grouping related events
   */
  addEvent(event) {
    const id = event.id || `evg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    
    const evt = {
      id,
      type: event.type,
      summary: event.summary || '',
      entities: event.entities || [],
      sourceId: event.sourceId || '',
      sourceType: event.sourceType || 'message',
      createdAt: event.createdAt || new Date().toISOString(),
      chainId: event.chainId || '',
      resolved: false,
    };

    this.events.set(id, evt);

    // Index by entity
    for (const entity of evt.entities) {
      if (!this.entityEvents.has(entity)) {
        this.entityEvents.set(entity, new Set());
      }
      this.entityEvents.get(entity).add(id);
    }

    // Add to chain
    if (evt.chainId) {
      if (!this.eventChains.has(evt.chainId)) {
        this.eventChains.set(evt.chainId, { events: [], entities: new Set() });
      }
      const chain = this.eventChains.get(evt.chainId);
      chain.events.push(id);
      for (const e of evt.entities) chain.entities.add(e);
    }

    return evt;
  }

  /**
   * Mark an event as resolved (e.g., risk resolved, task completed).
   */
  resolveEvent(eventId) {
    const evt = this.events.get(eventId);
    if (evt) {
      evt.resolved = true;
    }
  }

  /**
   * Get all events related to a specific entity.
   * @param {string} entityName - Person, project, or document name
   * @param {Object} options
   * @param {number} options.limit - Max events
   * @param {boolean} options.includeResolved - Include resolved events
   * @returns {Array} Sorted by recency (newest first)
   */
  getEventsForEntity(entityName, options = {}) {
    const limit = options.limit || 20;
    const includeResolved = options.includeResolved || false;
    
    const eventIds = this.entityEvents.get(entityName);
    if (!eventIds) return [];
    
    let events = Array.from(eventIds)
      .map(id => this.events.get(id))
      .filter(e => e && (includeResolved || !e.resolved))
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
      .slice(0, limit);
    
    return events;
  }

  /**
   * Get the event chain (context thread) for a given chain ID.
   */
  getEventChain(chainId) {
    const chain = this.eventChains.get(chainId);
    if (!chain) return null;
    
    return {
      chainId,
      events: Array.from(chain.events).map(id => this.events.get(id)).filter(Boolean),
      entities: Array.from(chain.entities),
    };
  }

  /**
   * Build context summary for a set of entities (used by scene executors).
   * @param {string[]} entityNames - Names of entities to get context for
   * @returns {string} Formatted context summary
   */
  buildContextSummary(entityNames, options = {}) {
    const maxEvents = options.maxEvents || 10;
    const sections = [];

    for (const name of entityNames) {
      const events = this.getEventsForEntity(name, { limit: 5 });
      if (events.length === 0) continue;

      const activeEvents = events.filter(e => !e.resolved);
      const resolvedEvents = events.filter(e => e.resolved);

      const lines = [];
      if (activeEvents.length > 0) {
        lines.push(`  ⏳ **未闭环**:`);
        for (const e of activeEvents) {
          lines.push(`    • [${e.type}] ${e.summary}`);
        }
      }
      if (resolvedEvents.length > 0) {
        lines.push(`  ✅ **已闭环**:`);
        for (const e of resolvedEvents.slice(0, 3)) {
          lines.push(`    • [${e.type}] ${e.summary}`);
        }
      }

      if (lines.length > 0) {
        sections.push(`**${name}**\n${lines.join('\n')}`);
      }
    }

    return sections.join('\n\n');
  }

  /**
   * Get unresolved risks and tasks (for weekly digest and meeting briefing).
   */
  getOpenItems(limit = 10) {
    const items = [];
    for (const [, evt] of this.events) {
      if (evt.resolved) continue;
      if (evt.type === 'risk_identified' || 
          evt.type === 'task_assigned' ||
          evt.type === 'question_asked') {
        items.push(evt);
      }
    }
    return items.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, limit);
  }

  /**
   * Get recent high-value events.
   */
  getRecentEvents(days = 7, limit = 20) {
    const since = new Date(Date.now() - days * 86400000);
    const events = Array.from(this.events.values())
      .filter(e => new Date(e.createdAt) >= since)
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
      .slice(0, limit);
    return events;
  }

  /**
   * Serialize the graph to a plain object for persistence.
   */
  toJSON() {
    return {
      events: Array.from(this.events.values()),
      entityEvents: Array.from(this.entityEvents.entries()).map(([k, v]) => [k, Array.from(v)]),
      eventChains: Array.from(this.eventChains.entries()).map(([k, v]) => [k, { events: v.events, entities: Array.from(v.entities) }]),
    };
  }

  /**
   * Deserialize from plain object.
   */
  static fromJSON(data) {
    const graph = new EventGraph();
    for (const evt of (data.events || [])) {
      graph.events.set(evt.id, evt);
      for (const entity of evt.entities) {
        if (!graph.entityEvents.has(entity)) graph.entityEvents.set(entity, new Set());
        graph.entityEvents.get(entity).add(evt.id);
      }
      if (evt.chainId) {
        if (!graph.eventChains.has(evt.chainId)) graph.eventChains.set(evt.chainId, { events: [], entities: new Set() });
        const chain = graph.eventChains.get(evt.chainId);
        chain.events.push(evt.id);
        for (const e of evt.entities) chain.entities.add(e);
      }
    }
    return graph;
  }
}

// ── Event Extraction from Messages ────────────────────────────────────────

/**
 * Extract high-value events from a processed message.
 * Called by the ingestion pipeline after entity extraction.
 */
export function extractEventsFromEntities(message, entities, relations, knowledgeItems) {
  const events = [];
  const chainId = `chain_${message.chat_id || 'default'}_${message.message_id?.split('_')[0] || Date.now()}`;

  // Extract decisions
  for (const ki of (knowledgeItems || [])) {
    if (ki.knowledge_type === 'decision') {
      events.push({
        type: 'decision_made',
        summary: ki.title,
        entities: entities.map(e => e.name).filter(Boolean),
        sourceId: message.message_id,
        sourceType: 'message',
        createdAt: message.created_at,
        chainId,
      });
    }
    if (ki.knowledge_type === 'action_item') {
      events.push({
        type: 'task_assigned',
        summary: `${ki.title}: ${ki.summary || ''}`,
        entities: entities.map(e => e.name).filter(Boolean),
        sourceId: message.message_id,
        sourceType: 'message',
        createdAt: message.created_at,
        chainId,
      });
    }
    if (ki.knowledge_type === 'risk') {
      events.push({
        type: 'risk_identified',
        summary: ki.title,
        entities: entities.map(e => e.name).filter(Boolean),
        sourceId: message.message_id,
        sourceType: 'message',
        createdAt: message.created_at,
        chainId,
      });
    }
  }

  // Extract task assignments from relations
  for (const rel of (relations || [])) {
    if (rel.relation_type === 'responsibility' || rel.relation_type === 'assignee') {
      events.push({
        type: 'task_assigned',
        summary: `${rel.source_entity_name || ''} 负责 ${rel.target_entity_name || ''}`,
        entities: [rel.source_entity_name, rel.target_entity_name].filter(Boolean),
        sourceId: message.message_id,
        sourceType: 'message',
        createdAt: message.created_at,
        chainId,
      });
    }
  }

  return events;
}

export default { EventGraph, extractEventsFromEntities };
