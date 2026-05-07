/**
 * Knowledge Radar — Onboarding Daily Push
 *
 * 新人入职 7 天线性推送系统。
 *
 * 排期：
 *   Day 1: 项目概览 + 团队架构
 *   Day 2: 关键决策
 *   Day 3: 待办事项 + 近期任务
 *   Day 4: 风险 + 已知问题
 *   Day 5: 关键联系人 + 协作方式
 *   Day 6: FAQ + SOP 候选
 *   Day 7: 入组总结 + 下一步指引
 */

import * as DB from './database.js';

// ── Day 计划 ────────────────────────────────────────────────────────────

const DAY_PLANS = [
  {
    day: 1,
    title: '项目概览与团队架构',
    template: (data) => `📅 **Day 1：项目概览与团队架构**

📌 **${data.projectName || '项目'}概览**
${data.overview || '暂无项目信息'}

👥 **团队架构**
${(data.people || []).map(p => `• ${p.name} — ${p.role || '成员'}`).join('\n') || '暂无团队信息'}

📄 **核心文档**
${(data.docs || []).slice(0, 5).map(d => `• ${d.title}`).join('\n') || '暂无文档'}

---
📬 明天 Day 2 将推送关键决策和背景知识。`,
  },
  {
    day: 2,
    title: '关键决策与背景知识',
    template: (data) => `📅 **Day 2：关键决策与背景知识**

📌 **关键决策回顾**
${(data.decisions || []).slice(0, 8).map(d => `• ${d.title}: ${(d.summary || '').slice(0, 150)}`).join('\n') || '暂无决策记录'}

💡 **背景知识**
${(data.knowledge || []).slice(0, 5).map(k => `• ${k.title || k}`).join('\n') || '暂无相关知识'}

---
📬 明天 Day 3 将推送待办事项和近期任务。`,
  },
  {
    day: 3,
    title: '待办事项与近期任务',
    template: (data) => `📅 **Day 3：待办事项与近期任务**

📋 **待办事项**
${(data.tasks || []).slice(0, 8).map(t => `• ${t.text || t.title}${t.owner ? ` (负责人: ${t.owner})` : ''}`).join('\n') || '暂无待办'}

⏳ **未闭环事件**
${(data.openItems || []).slice(0, 5).map(o => `• [${o.type}] ${o.summary.slice(0, 100)}`).join('\n') || '暂无未闭环事件'}

---
📬 明天 Day 4 将推送风险信息。`,
  },
  {
    day: 4,
    title: '风险与已知问题',
    template: (data) => `📅 **Day 4：风险与已知问题**

⚠️ **当前风险**
${(data.risks || []).slice(0, 8).map(r => `• ${r.title}: ${(r.summary || '').slice(0, 120)}`).join('\n') || '暂无风险记录'}

🔍 **已知问题**
${(data.issues || []).slice(0, 5).map(i => `• ${i}`).join('\n') || '暂无已知问题'}

---
📬 明天 Day 5 将推送关键联系人和协作方式。`,
  },
  {
    day: 5,
    title: '关键联系人',
    template: (data) => `📅 **Day 5：关键联系人与协作方式**

👥 **关键联系人**
${(data.people || []).slice(0, 10).map(p => `• ${p.name}${p.role ? ` — ${p.role}` : ''}${p.relevance ? ` (关联度: ${p.relevance.toFixed(2)})` : ''}`).join('\n') || '暂无联系人信息'}

🔗 **协作方式**
• 日常沟通：飞书群聊
• 文档评审：飞书文档评论
• 任务追踪：看板
• 代码审查：GitLab MR

---
📬 明天 Day 6 将推送 FAQ 和 SOP。`,
  },
  {
    day: 6,
    title: 'FAQ 与 SOP',
    template: (data) => `📅 **Day 6：FAQ 与 SOP**

💡 **常见问题**
${(data.faqs || []).slice(0, 8).map(f => `Q: ${f.question}\nA: ${(f.answer || '').slice(0, 150)}`).join('\n\n') || '暂无 FAQ 数据'}

📖 **SOP 文档**
${(data.sops || []).slice(0, 5).map(s => `• ${s}`).join('\n') || '暂无 SOP 文档'}

---
📬 明天 Day 7 将推送入组总结和下一步指引。`,
  },
  {
    day: 7,
    title: '入组总结与下一步',
    template: (data) => `📅 **Day 7：入组总结与下一步**

🎉 **恭喜完成入组引导！**

📊 **本周回顾**
• 项目概览 ✅
• 关键决策 ✅
• 待办事项 ✅
• 风险信息 ✅
• 关键联系人 ✅
• FAQ 与 SOP ✅

🔜 **下一步建议**
1. 阅读核心文档（参见 Day 1 必读材料）
2. 参与本周后续会议
3. 分配开发任务
4. 提出你对项目的问题

❓ 如有任何问题，随时在群内提出或 @技术负责人。`,
  },
];

// ── 推送生成 ────────────────────────────────────────────────────────────

/**
 * 为新人生成 Day N 的推送内容
 *
 * @param {Object} db - SQLite 实例
 * @param {Object} options
 * @param {string} options.userId - 用户 ID
 * @param {string} options.userName - 用户姓名
 * @param {number} options.day - 第几天（1-7）
 * @param {string} options.projectName - 项目名称
 * @returns {Object} { title, content, day, totalDays }
 */
export function generateDailyPush(db, options = {}) {
  const day = Math.max(1, Math.min(7, options.day || 1));
  const plan = DAY_PLANS[day - 1];

  // 获取数据
  const data = gatherPushData(db, options);

  const content = plan.template(data);

  return {
    day,
    totalDays: 7,
    title: `Day ${day}: ${plan.title}`,
    content,
    receivers: [options.userId || 'new_user'],
    userId: options.userId || '',
  };
}

/**
 * 获取某一天所有需要推送的新人列表
 * 根据用户 profile 中的 onboarding_day 判断
 */
export function getPendingOnboardingUsers(db) {
  const users = DB.query(db,
    `SELECT * FROM user_profiles WHERE role_tags LIKE '%new_join%' OR onboarding_day IS NOT NULL`
  );

  const pending = [];
  for (const u of users) {
    let tags;
    try { tags = u.role_tags ? JSON.parse(u.role_tags) : []; } catch { tags = []; }
    const day = u.onboarding_day || tags.indexOf('new_join') >= 0 ? 1 : 0;

    if (day > 0 && day <= 7) {
      pending.push({
        userId: u.user_id,
        userName: u.user_name || 'New Member',
        onboardingDay: u.onboarding_day || 1,
        projectName: u.project_name || '',
        tags,
      });
    }
  }

  return pending;
}

/**
 * 推进新人的 onboarding_day（每天调用一次）
 */
export function advanceOnboardingDay(db, userId) {
  const user = DB.queryOne(db,
    `SELECT onboarding_day, role_tags FROM user_profiles WHERE user_id = ?`,
    [userId]
  );
  if (!user) return null;

  const day = (user.onboarding_day || 0) + 1;
  if (day > 7) {
    // 完成 onboarding
    let tags;
    try { tags = JSON.parse(user.role_tags || '[]'); } catch { tags = []; }
    tags = tags.filter(t => t !== 'new_join');
    DB.exec(db,
      `UPDATE user_profiles SET onboarding_day = 7, role_tags = ?, project_name = '' WHERE user_id = ?`,
      [JSON.stringify(tags), userId]
    );
    return { status: 'completed', day: 7 };
  }

  DB.exec(db,
    `UPDATE user_profiles SET onboarding_day = ? WHERE user_id = ?`,
    [day, userId]
  );
  return { status: 'active', day };
}

// ── 内部方法 ──────────────────────────────────────────────────────────

function gatherPushData(db, options) {
  const projectName = options.projectName || '';
  const searchQuery = projectName || '';

  const people = DB.getAllEntities(db, 'person', 15);
  const projects = DB.getAllEntities(db, 'project', 5);
  const docs = DB.getSourceObjectsByType(db, 'doc', 10);
  const decisions = DB.getKnowledgeByType(db, 'decision', 10);
  const tasks = DB.getKnowledgeByType(db, 'action_item', 10);
  const risks = DB.getKnowledgeByType(db, 'risk', 10);
  const updates = DB.getKnowledgeByType(db, 'update', 10);
  const faqs = DB.query(db,
    `SELECT * FROM faq_candidates WHERE status = 'published' ORDER BY frequency DESC LIMIT 10`
  );

  // 用知识库拿未闭环事件
  const unresolved = DB.query(db,
    `SELECT * FROM knowledge_items WHERE knowledge_type = 'action_item' AND status != 'resolved' AND status != 'done' LIMIT 10`
  );
  const openItems = unresolved.map(t => ({ type: 'task', summary: t.title }));

  // 项目概述
  const overview = projects.map(p => p.name).join(', ');

  // 人带角色信息
  const peopleWithRole = people.map(p => ({
    name: p.name,
    role: p.properties_json ? (() => { try { return JSON.parse(p.properties_json).role; } catch { return ''; } })() : '',
    relevance: p.mention_count || 0,
  }));

  // 处理 tasks 的格式
  const taskItems = tasks.map(t => ({
    text: t.title || t.summary,
    title: t.title,
    owner: t.author || '',
  }));

  return {
    projectName,
    overview,
    people: peopleWithRole,
    docs,
    decisions,
    knowledge: updates,
    tasks: taskItems,
    risks,
    openItems,
    faqs,
    issues: risks.filter(r => r.status === 'critical').map(r => r.title),
    sops: docs.slice(0, 3).map(d => d.title),
  };
}

export default {
  generateDailyPush,
  getPendingOnboardingUsers,
  advanceOnboardingDay,
  DAY_PLANS,
};
