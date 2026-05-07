/**
 * Knowledge Radar — GraphRAG (轻量知识图谱增强检索)
 *
 * 基于实体关系图的上下文增强引擎。核心能力：
 *
 * 1. 关系加权遍历：给定实体，沿关系边遍历关联实体
 * 2. 上下文聚合：为遍历到的实体收集决策/任务/风险/知识
 * 3. 影响分析：给定文档/变更，找出影响的项目、人员、待办
 * 4. 项目脉络生成：从项目实体出发，构建项目-人员-决策全景图
 *
 * 相比 EventGraph（事件链追踪），GraphRAG 关注实体间的关系网络和知识关联。
 */

import * as DB from './database.js';

// ── 遍历深度配置 ──────────────────────────────────────────────────────────

const MAX_TRAVERSAL = 200; // 最多遍历的节点数
const DEFAULT_DEPTH = 2;   // 默认遍历深度

// ── 实体类型权重 ──────────────────────────────────────────────────────────

const ENTITY_WEIGHTS = {
  person: 1.0,
  project: 1.0,
  decision: 1.0,
  risk: 0.9,
  task: 0.8,
  document: 0.7,
  meeting: 0.6,
  system: 0.5,
  concept: 0.3,
};

/**
 * GraphRAG 引擎
 */
export class GraphRAG {
  constructor(db) {
    this.db = db;
  }

  /**
   * 关系加权遍历：从种子实体出发，沿关系边遍历关联实体网络
   *
   * @param {string} seedName - 种子实体名称
   * @param {Object} options
   * @param {number} options.maxDepth - 遍历深度（默认2）
   * @param {number} options.maxNodes - 最多节点数（默认200）
   * @param {string[]} options.targetTypes - 目标实体类型过滤
   * @returns {Array<{entity: Object, depth: number, path: string[], relevance: number}>}
   */
  traverse(seedName, options = {}) {
    const maxDepth = options.maxDepth || DEFAULT_DEPTH;
    const maxNodes = options.maxNodes || MAX_TRAVERSAL;
    const targetTypes = options.targetTypes || null;

    // 1. 查找种子实体
    const seeds = DB.searchEntities(this.db, seedName, null, 5);
    if (seeds.length === 0) return [];

    const visited = new Set();
    const result = [];

    // BFS 遍历
    const queue = seeds.map(s => ({
      entity: s,
      depth: 0,
      path: [s.name],
      relevance: 1.0,
    }));

    while (queue.length > 0 && result.length < maxNodes) {
      const current = queue.shift();

      // 跳过已访问
      const visitKey = `${current.entity.entity_type}:${current.entity.entity_id}`;
      if (visited.has(visitKey)) continue;
      visited.add(visitKey);

      // 记录节点
      result.push(current);

      // 达到最大深度，不再展开
      if (current.depth >= maxDepth) continue;

      // 2. 查找该实体的所有关系
      const relations = DB.getRelationsForEntity(this.db, current.entity.entity_id, 50);

      // 按关系权重排序，取高权重的优先展开
      relations.sort((a, b) => (b.weight || 1) - (a.weight || 1));

      for (const rel of relations) {
        // 找出不在当前节点上的另一端
        const isSource = rel.source_entity_id === current.entity.entity_id;
        const neighborId = isSource ? rel.target_entity_id : rel.source_entity_id;
        const neighborName = isSource ? rel.target_name : rel.source_name;
        const neighborType = isSource ? rel.target_type : rel.source_type;
        const neighborKey = `${neighborType}:${neighborId}`;

        // 跳过已访问
        if (visited.has(neighborKey)) continue;

        // 如果有目标类型过滤，跳过不符合的
        if (targetTypes && !targetTypes.includes(neighborType)) {
          // 但依然将目标类型的邻居加入队列（如果 seed 本身就是目标类型）
          // 这样做是为了"途经"其他类型找到目标
        }

        // 计算关联度 = 父节点关联度 × 关系权重 × 实体类型权重
        const entityWeight = ENTITY_WEIGHTS[neighborType] || 0.3;
        const relevance = current.relevance * (rel.weight || 1) * entityWeight;

        const neighborEntity = {
          entity_id: neighborId,
          entity_type: neighborType,
          name: neighborName,
        };

        queue.push({
          entity: neighborEntity,
          depth: current.depth + 1,
          path: [...current.path, neighborName],
          relevance,
        });
      }

      // 按关联度排序队列，保证高关联度的优先展开
      queue.sort((a, b) => b.relevance - a.relevance);
    }

    return result;
  }

  /**
   * 生成实体的上下文摘要（用于场景执行器）
   *
   * 给定一组实体名称，收集它们的：
   * - 关联知识项（决策/任务/风险）
   * - 未闭环节点
   * - 项目-人员关系
   *
   * @param {string[]} entityNames - 实体名称列表
   * @param {Object} options
   * @returns {Object} 结构化上下文
   */
  buildContext(entityNames, options = {}) {
    const maxDepth = options.maxDepth || 1;
    const context = {
      entities: new Map(),  // name -> { type, decisions, tasks, risks, relatedPeople, relatedProjects }
      relatedDecisions: [],
      relatedTasks: [],
      relatedRisks: [],
      relatedPeople: [],
      relatedProjects: [],
      unresolvedItems: [],
      impactSummary: '',
    };

    // 遍历每个种子实体
    const allNodes = new Map(); // entityKey -> traversal result

    for (const name of entityNames) {
      const nodes = this.traverse(name, { maxDepth, maxNodes: 50 });
      for (const node of nodes) {
        const key = `${node.entity.entity_type}:${node.entity.entity_id}`;
        if (!allNodes.has(key)) {
          allNodes.set(key, node);
        }
      }
    }

    // 为每个遍历到的节点收集关联知识
    for (const [, node] of allNodes) {
      const ent = node.entity;
      const entityKey = ent.name;

      if (!context.entities.has(entityKey)) {
        context.entities.set(entityKey, {
          type: ent.entity_type,
          decisions: [],
          tasks: [],
          risks: [],
          relatedPeople: [],
          relatedProjects: [],
          depth: node.depth,
          relevance: node.relevance,
          path: node.path,
        });
      }

      // 查找该实体的关联知识
      const knowledgeItems = DB.query(this.db,
        `SELECT ki.*
         FROM knowledge_items ki
         WHERE ki.status = 'active'
         AND (ki.title LIKE ? OR ki.summary LIKE ?)
         ORDER BY ki.confidence DESC LIMIT 20`,
        [`%${ent.name}%`, `%${ent.name}%`]
      );

      for (const ki of knowledgeItems) {
        const item = { title: ki.title, summary: ki.summary, confidence: ki.confidence };
        if (ki.knowledge_type === 'decision') context.relatedDecisions.push(item);
        else if (ki.knowledge_type === 'action_item') context.relatedTasks.push(item);
        else if (ki.knowledge_type === 'risk') context.relatedRisks.push(item);
      }

      // 收集关联人员
      if (ent.entity_type === 'person') {
        context.relatedPeople.push(ent.name);
      }

      // 收集关联项目
      if (ent.entity_type === 'project') {
        context.relatedProjects.push({
          name: ent.name,
          relevance: node.relevance,
        });
      }
    }

    // 去重
    context.relatedDecisions = this._dedupByTitle(context.relatedDecisions);
    context.relatedTasks = this._dedupByTitle(context.relatedTasks);
    context.relatedRisks = this._dedupByTitle(context.relatedRisks);
    context.relatedPeople = [...new Set(context.relatedPeople)];
    context.relatedProjects.sort((a, b) => b.relevance - a.relevance);

    // 生成影响摘要
    context.impactSummary = this._generateImpactSummary(context, entityNames);

    return context;
  }

  /**
   * 文档变更影响分析
   *
   * 给定文档名称，分析：
   * - 影响了哪些项目
   * - 影响了哪些人的待办
   * - 关联了哪些决策
   *
   * @param {string} documentName - 文档名称
   * @returns {Object} 影响分析结果
   */
  analyzeImpact(documentName) {
    const context = this.buildContext([documentName], { maxDepth: 2 });

    // 查找关联文档的知识项
    const affectedKnowledge = DB.query(this.db,
      `SELECT ki.* FROM knowledge_items ki
       WHERE ki.status = 'active'
       AND ki.source_refs_json LIKE ?
       ORDER BY ki.updated_at DESC LIMIT 20`,
      [`%${documentName}%`]
    );

    // 查找受影响的待办
    const assignedTasks = context.relatedTasks.map(t => ({
      ...t,
      owner: context.relatedPeople.slice(0, 3),
    }));

    return {
      documentName,
      affectedProjects: context.relatedProjects.map(p => p.name),
      affectedPeople: context.relatedPeople,
      affectedDecisions: context.relatedDecisions,
      affectedTasks: assignedTasks,
      affectedKnowledge: affectedKnowledge.map(k => ({
        type: k.knowledge_type,
        title: k.title,
        summary: k.summary,
      })),
      summary: context.impactSummary,
    };
  }

  /**
   * 项目脉络生成（用于新人入职）
   *
   * 给定项目名称，生成项目-人员-决策全景图
   *
   * @param {string} projectName - 项目名称
   * @returns {Object} 项目全景图
   */
  buildProjectOverview(projectName) {
    const nodes = this.traverse(projectName, {
      maxDepth: 2,
      maxNodes: 100,
    });

    // 按类型分组节点
    const people = [];
    const decisions = [];
    const docs = [];
    const tasks = [];
    const risks = [];

    for (const node of nodes) {
      const type = node.entity.entity_type;
      const name = node.entity.name;
      const item = { name, relevance: node.relevance, path: node.path };

      if (type === 'person') people.push(item);
      else if (type === 'decision') decisions.push(item);
      else if (type === 'document') docs.push(item);
      else if (type === 'task') tasks.push(item);
      else if (type === 'risk') risks.push(item);
    }

    // 按关联度排序
    const sortByRelevance = arr => arr.sort((a, b) => b.relevance - a.relevance);
    sortByRelevance(people);
    sortByRelevance(decisions);
    sortByRelevance(docs);
    sortByRelevance(tasks);
    sortByRelevance(risks);

    // 收集关联知识
    const context = this.buildContext([projectName], { maxDepth: 1 });

    return {
      projectName,
      overview: {
        totalNodes: nodes.length,
        peopleCount: people.length,
        decisionCount: decisions.length,
        docCount: docs.length,
        taskCount: tasks.length,
        riskCount: risks.length,
      },
      people: people.slice(0, 15),
      decisions: context.relatedDecisions.slice(0, 10),
      docs: docs.slice(0, 10),
      tasks: context.relatedTasks.slice(0, 10),
      risks: context.relatedRisks.slice(0, 10),
      contextSummary: context.impactSummary,
    };
  }

  // ── 内部方法 ──────────────────────────────────────────────────────────

  /**
   * 按标题去重（文本相似度）
   */
  _dedupByTitle(items) {
    const seen = new Set();
    const result = [];
    for (const item of items) {
      const key = item.title ? item.title.slice(0, 30) : '';
      if (key && !seen.has(key)) {
        seen.add(key);
        result.push(item);
      }
    }
    return result;
  }

  /**
   * 生成影响摘要文本
   */
  _generateImpactSummary(context, seedNames) {
    const parts = [];

    if (context.relatedDecisions.length > 0) {
      parts.push(`关联 ${context.relatedDecisions.length} 项决策`);
    }
    if (context.relatedTasks.length > 0) {
      parts.push(`${context.relatedTasks.length} 个待办事项`);
    }
    if (context.relatedRisks.length > 0) {
      parts.push(`${context.relatedRisks.length} 项风险`);
    }
    if (context.relatedPeople.length > 0) {
      parts.push(`涉及 ${context.relatedPeople.length} 人`);
    }
    if (context.relatedProjects.length > 0) {
      parts.push(`影响 ${context.relatedProjects.length} 个项目`);
    }

    return parts.length > 0
      ? `「${seedNames.join('、')}」${parts.join('，')}。`
      : `「${seedNames.join('、')}」暂无关联数据。`;
  }
}

export default { GraphRAG };
