/**
 * Knowledge Radar — User Behavior Tracker & Dynamic Profile
 *
 * Tracks user interactions and auto-updates user profiles:
 * - Click / read / follow-up / collect / negative feedback
 * - Dynamic role_tags and topic_interest updates
 * - Read history for PushScore dedup
 */

import * as DB from './database.js';

// ── Behavior Types ───────────────────────────────────────────────────────

const BEHAVIOR_TYPES = {
  CLICK: 'click',
  READ: 'read',
  FOLLOW_UP: 'follow_up',
  COLLECT: 'collect',
  NEGATIVE: 'negative_feedback',
  DISMISS: 'dismiss',
  REPLY: 'reply',
  SEARCH: 'search',
};

// ── Topic Extraction ─────────────────────────────────────────────────────

function extractTopicsFromText(text) {
  if (!text) return [];
  const topics = new Set();
  
  // Common enterprise topic patterns
  const patterns = [
    /[\u4e00-\u9fff]{2,10}(?:方案|系统|项目|模块|架构|设计|平台|服务|平台|框架)/g,
    /[\u4e00-\u9fff]{2,6}(?:技术|产品|需求|测试|部署|发布)/g,
  ];

  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      topics.add(match[0]);
    }
  }

  return Array.from(topics).slice(0, 10);
}

// ── Dynamic Profile Updater ──────────────────────────────────────────────

export class UserBehaviorTracker {
  constructor(db) {
    this.db = db;
    this.recentBehaviors = new Map(); // userId -> { behaviors: [], lastUpdate: timestamp }
  }

  /**
   * Record a user behavior event.
   * @param {Object} event
   * @param {string} event.userId - User ID
   * @param {string} event.type - Behavior type (from BEHAVIOR_TYPES)
   * @param {string} event.knowledgeId - Related knowledge ID
   * @param {string} event.knowledgeType - Knowledge type
   * @param {string} event.content - User's input (for follow_up/reply)
   * @param {number} event.timestamp - Event time
   */
  recordBehavior(event) {
    const userId = event.userId || 'unknown';
    const timestamp = event.timestamp || Date.now();
    
    if (!this.recentBehaviors.has(userId)) {
      this.recentBehaviors.set(userId, { behaviors: [], lastUpdate: 0 });
    }
    
    const userData = this.recentBehaviors.get(userId);
    userData.behaviors.push(event);
    userData.lastUpdate = timestamp;

    // Update profile periodically (every 5 behaviors or 1 hour)
    if (userData.behaviors.length >= 5 || (timestamp - userData.lastUpdate) > 3600000) {
      this._updateProfile(userId);
    }
  }

  /**
   * Get read history for a user (for PushScore dedup).
   */
  getReadHistory(userId) {
    const userData = this.recentBehaviors.get(userId);
    if (!userData) return [];
    
    return userData.behaviors
      .filter(b => b.type === BEHAVIOR_TYPES.READ || b.type === BEHAVIOR_TYPES.CLICK)
      .map(b => b.knowledgeId)
      .filter(Boolean);
  }

  /**
   * Get user's recent topics of interest.
   */
  getRecentTopics(userId, maxTopics = 10) {
    const userData = this.recentBehaviors.get(userId);
    if (!userData) return [];

    const topicScores = {};
    
    for (const behavior of userData.behaviors) {
      const weight = this._behaviorWeight(behavior.type);
      const topics = extractTopicsFromText(behavior.content || behavior.knowledgeId || '');
      
      for (const topic of topics) {
        topicScores[topic] = (topicScores[topic] || 0) + weight;
      }
    }

    return Object.entries(topicScores)
      .sort((a, b) => b[1] - a[1])
      .slice(0, maxTopics)
      .map(([topic]) => topic);
  }

  /**
   * Get users who are currently active (behavior in last N minutes).
   */
  getActiveUsers(minutes = 30) {
    const cutoff = Date.now() - minutes * 60000;
    const active = [];
    
    for (const [userId, data] of this.recentBehaviors) {
      const recent = data.behaviors.filter(b => (b.timestamp || 0) >= cutoff);
      if (recent.length > 0) {
        active.push({ userId, behaviorCount: recent.length, lastTime: recent[recent.length - 1].timestamp });
      }
    }

    return active.sort((a, b) => b.lastTime - a.lastTime);
  }

  // ── Internal ─────────────────────────────────────────────────────────

  _updateProfile(userId) {
    const userData = this.recentBehaviors.get(userId);
    if (!userData) return;

    // Extract topics from all behaviors
    const topicScores = {};
    let totalWeight = 0;

    for (const behavior of userData.behaviors) {
      const weight = this._behaviorWeight(behavior.type);
      totalWeight += weight;
      
      const content = behavior.content || behavior.knowledgeId || '';
      const topics = extractTopicsFromText(content);
      
      for (const topic of topics) {
        topicScores[topic] = (topicScores[topic] || 0) + weight;
      }
    }

    // Get top topics
    const topTopics = Object.entries(topicScores)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([topic]) => topic);

    // Update DB profile
    try {
      const existing = DB.getUserProfile(this.db, userId);
      if (existing) {
        const currentInterests = JSON.parse(existing.topic_interest_json || '[]');
        const merged = [...new Set([...topTopics, ...currentInterests])].slice(0, 10);
        
        DB.upsertUserProfile(this.db, {
          user_id: userId,
          topic_interest: merged,
          metadata: { lastBehaviorUpdate: new Date().toISOString(), behaviorCount: userData.behaviors.length },
        });
      }
    } catch (e) {
      console.warn(`[BehaviorTracker] Profile update failed for ${userId}: ${e.message}`);
    }
  }

  _behaviorWeight(type) {
    switch (type) {
      case BEHAVIOR_TYPES.COLLECT: return 5;   // Strong signal
      case BEHAVIOR_TYPES.REPLY: return 4;      // Engaged
      case BEHAVIOR_TYPES.FOLLOW_UP: return 3;   // Interested
      case BEHAVIOR_TYPES.CLICK: return 2;       // Mild interest
      case BEHAVIOR_TYPES.READ: return 1;        // Passive
      case BEHAVIOR_TYPES.SEARCH: return 2;      // Intent
      case BEHAVIOR_TYPES.NEGATIVE: return -3;   // Disinterest
      case BEHAVIOR_TYPES.DISMISS: return -1;    // Skipped
      default: return 1;
    }
  }

  /**
   * Serialize for persistence.
   */
  toJSON() {
    const data = {};
    for (const [userId, userData] of this.recentBehaviors) {
      data[userId] = {
        behaviors: userData.behaviors,
        lastUpdate: userData.lastUpdate,
      };
    }
    return data;
  }

  static fromJSON(db, data) {
    const tracker = new UserBehaviorTracker(db);
    for (const [userId, userData] of Object.entries(data || {})) {
      tracker.recentBehaviors.set(userId, {
        behaviors: userData.behaviors || [],
        lastUpdate: userData.lastUpdate || 0,
      });
    }
    return tracker;
  }
}

export { BEHAVIOR_TYPES };
export default { UserBehaviorTracker, BEHAVIOR_TYPES };
