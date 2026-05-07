/**
 * Knowledge Radar — PushScore Distribution Strategy
 *
 * Scores each potential recipient for a knowledge push based on:
 * - Role relevance: how relevant is this knowledge to the user's role
 * - Project participation: is the user involved in the related project
 * - Task responsibility: is the user responsible for related tasks
 * - Time urgency: is there a deadline approaching
 * - Information freshness: how new is this information
 * - Read status: has the user already seen related content
 * - Interruption cost: is now a good time to push
 *
 * Score range: 0.0 (don't push) to 1.0 (must push immediately)
 */

// ── Weights ──────────────────────────────────────────────────────────────

const DEFAULT_WEIGHTS = {
  roleRelevance: 0.20,
  projectParticipation: 0.20,
  taskResponsibility: 0.20,
  timeUrgency: 0.15,
  freshness: 0.10,
  readStatus: 0.10,
  interruptionCost: 0.05,
};

// ── PushScore Engine ─────────────────────────────────────────────────────

export class PushScore {
  constructor(weights = {}) {
    this.weights = { ...DEFAULT_WEIGHTS, ...weights };
  }

  /**
   * Calculate PushScore for a user receiving a knowledge item.
   * @param {Object} params
   * @param {Object} params.user - User profile { userId, roleTags, topics, recentTopics, pushPreference }
   * @param {Object} params.knowledge - Knowledge item { type, title, summary, entities, sourceType, createdAt }
   * @param {Object} params.context - Scene context { sceneType, projectName, participants, deadlines }
   * @returns {{ score: number, signals: Object, decision: string }}
   */
  calculate(params) {
    const { user = {}, knowledge = {}, context = {} } = params;
    
    // Calculate each signal
    const roleRelevance = this._scoreRoleRelevance(user, knowledge, context);
    const projectParticipation = this._scoreProjectParticipation(user, knowledge, context);
    const taskResponsibility = this._scoreTaskResponsibility(user, knowledge, context);
    const timeUrgency = this._scoreTimeUrgency(knowledge, context);
    const freshness = this._scoreFreshness(knowledge);
    const readStatus = this._scoreReadStatus(user, knowledge);
    const interruptionCost = this._scoreInterruptionCost(user, context);

    // Combined score
    const { roleRelevance: w1, projectParticipation: w2, taskResponsibility: w3,
            timeUrgency: w4, freshness: w5, readStatus: w6, interruptionCost: w7 } = this.weights;

    const rawScore = 
      w1 * roleRelevance +
      w2 * projectParticipation +
      w3 * taskResponsibility +
      w4 * timeUrgency +
      w5 * freshness +
      w6 * readStatus +
      w7 * (1 - interruptionCost); // Lower interruption cost = higher score

    // Normalize to 0-1
    const score = Math.max(0, Math.min(1, rawScore));

    // Decision
    let decision;
    if (score >= 0.8) decision = 'push_now';       // Immediate push (IM card)
    else if (score >= 0.5) decision = 'push_digest'; // Add to next digest
    else if (score >= 0.2) decision = 'archive';    // Store for search only
    else decision = 'filter';                        // Don't push

    return {
      score,
      decision,
      signals: { roleRelevance, projectParticipation, taskResponsibility, timeUrgency, freshness, readStatus, interruptionCost },
    };
  }

  /**
   * Batch calculate PushScores for multiple users.
   * @param {Array} users - Array of user objects
   * @param {Object} knowledge - Knowledge item
   * @param {Object} context - Scene context
   * @returns {Array} Users sorted by score, with score/decision attached
   */
  batchCalculate(users, knowledge, context) {
    const scored = users.map(user => {
      const result = this.calculate({ user, knowledge, context });
      return { ...user, pushScore: result.score, pushDecision: result.decision, pushSignals: result.signals };
    });

    scored.sort((a, b) => b.pushScore - a.pushScore);
    return scored;
  }

  /**
   * Filter users by minimum score threshold.
   */
  filterByThreshold(users, knowledge, context, minScore = 0.5) {
    return this.batchCalculate(users, knowledge, context)
      .filter(u => u.pushScore >= minScore);
  }

  // ── Signal Scoring Functions ─────────────────────────────────────────

  _scoreRoleRelevance(user, knowledge, context) {
    const roleTags = user.roleTags || user.role_tags || [];
    const topics = user.topics || [];
    const knowledgeText = `${knowledge.title || ''} ${knowledge.summary || ''}`.toLowerCase();
    
    // Role match
    let roleScore = 0;
    const roleKeywords = {
      'developer': ['开发', '代码', 'bug', 'API', '架构', '工程', '实现'],
      'manager': ['决策', '进度', '资源', '评审', '报告', '排期'],
      'designer': ['设计', 'UI', 'UX', '界面', '体验'],
      'tester': ['测试', '质量', '用例', '回归', 'bug'],
      'operator': ['运维', '部署', '发布', '监控', '告警'],
      'pm': ['需求', '项目', '规划', '迭代', '优先级'],
      'new_join': ['概览', '文档', '流程', '环境', '配置'],
    };

    for (const role of roleTags) {
      const keywords = roleKeywords[role] || [];
      const matchCount = keywords.filter(kw => knowledgeText.includes(kw)).length;
      if (matchCount > 0) {
        roleScore = Math.max(roleScore, matchCount / keywords.length);
      }
    }

    // Topic match
    let topicScore = 0;
    if (topics.length > 0) {
      for (const topic of topics) {
        if (knowledgeText.includes(topic.toLowerCase())) {
          topicScore = Math.max(topicScore, 0.8);
        }
      }
    }

    return Math.max(roleScore, topicScore);
  }

  _scoreProjectParticipation(user, knowledge, context) {
    const userProjects = user.projects || user.recentProjects || [];
    const relatedEntities = knowledge.entities || [];
    
    for (const project of userProjects) {
      for (const entity of relatedEntities) {
        if (typeof entity === 'string' && project.toLowerCase().includes(entity.toLowerCase())) {
          return 1.0;
        }
        if (typeof entity === 'string' && entity.toLowerCase().includes(project.toLowerCase())) {
          return 1.0;
        }
      }
    }

    // Scene context
    if (context.sceneType === 'meeting_briefing' && 
        (context.participants || []).includes(user.userId || user.user_id)) {
      return 0.9;
    }

    if (context.sceneType === 'onboarding' && user.userId === context.userId) {
      return 1.0;
    }

    return 0;
  }

  _scoreTaskResponsibility(user, knowledge, context) {
    const userTasks = user.tasks || user.assignedTasks || [];
    const knowledgeText = `${knowledge.title || ''} ${knowledge.summary || ''}`.toLowerCase();
    
    for (const task of userTasks) {
      const taskName = typeof task === 'string' ? task : (task.title || task.name || '');
      if (taskName && knowledgeText.includes(taskName.toLowerCase())) {
        return 1.0;
      }
    }

    return 0;
  }

  _scoreTimeUrgency(knowledge, context) {
    const deadlines = context.deadlines || [];
    if (deadlines.length === 0) return 0.5; // Neutral

    const now = Date.now();
    let maxUrgency = 0;

    for (const dl of deadlines) {
      const deadlineTime = typeof dl === 'string' ? new Date(dl).getTime() : (dl.time || dl);
      const msRemaining = deadlineTime - now;
      const daysRemaining = msRemaining / (1000 * 60 * 60 * 24);

      if (daysRemaining <= 0) maxUrgency = Math.max(maxUrgency, 1.0);      // Overdue
      else if (daysRemaining <= 1) maxUrgency = Math.max(maxUrgency, 0.9);  // Today
      else if (daysRemaining <= 3) maxUrgency = Math.max(maxUrgency, 0.7);  // This week
      else if (daysRemaining <= 7) maxUrgency = Math.max(maxUrgency, 0.5);  // Next week
      else maxUrgency = Math.max(maxUrgency, 0.2);                          // Later
    }

    return maxUrgency;
  }

  _scoreFreshness(knowledge) {
    if (!knowledge.createdAt && !knowledge.created_at) return 0.5;

    const createdAt = new Date(knowledge.createdAt || knowledge.created_at).getTime();
    const ageHours = (Date.now() - createdAt) / (1000 * 60 * 60);

    if (ageHours <= 1) return 1.0;        // Within the hour
    if (ageHours <= 24) return 0.8;        // Today
    if (ageHours <= 72) return 0.6;        // Within 3 days
    if (ageHours <= 168) return 0.4;       // Within a week
    if (ageHours <= 720) return 0.2;       // Within a month
    return 0.1;                             // Older
  }

  _scoreReadStatus(user, knowledge) {
    const readItems = user.readItems || user.readHistory || [];
    const knowledgeId = knowledge.id || knowledge.knowledge_id || '';

    if (readItems.includes(knowledgeId)) {
      return 0.0; // Already read, skip
    }

    // Check similar items
    const similarIds = knowledge.similarIds || [];
    const hasReadSimilar = similarIds.some(id => readItems.includes(id));
    if (hasReadSimilar) return 0.3; // May have seen similar content

    return 0.8; // Not seen, likely relevant
  }

  _scoreInterruptionCost(user, context) {
    const pushPreference = user.pushPreference || user.push_preference || {};
    const quietHours = pushPreference.quietHours || { start: 22, end: 8 }; // 10PM - 8AM
    
    const now = new Date();
    const hour = now.getHours();
    
    // Check quiet hours
    if (hour >= quietHours.start || hour < quietHours.end) {
      return 0.9; // High interruption cost during quiet hours
    }

    // Check user's recent activity (if we have it)
    const lastActive = user.lastActive ? new Date(user.lastActive).getTime() : 0;
    const minutesSinceActive = (Date.now() - lastActive) / (1000 * 60);
    
    if (minutesSinceActive < 5) return 0.3;  // Just active, low cost
    if (minutesSinceActive < 30) return 0.5; // Recently active
    if (minutesSinceActive > 120) return 0.7; // Away for a while, moderate cost

    return 0.4; // Default
  }

  toJSON() {
    return { weights: { ...this.weights } };
  }

  static fromJSON(data) {
    return new PushScore(data.weights);
  }
}

export default { PushScore };
