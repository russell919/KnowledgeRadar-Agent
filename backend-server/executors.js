/**
 * Knowledge Radar — Scene Executors v2.1
 * 
 * Uses Hybrid Search + Event Graph + GraphRAG for knowledge retrieval.
 * Factory receives all dependencies from server.js.
 */

export function createExecutors({ db, feishu, llm, hybridSearch, eventGraph, pushScore, behaviorTracker, graphRAG, uuid, DB }) {

  // ── Helper: Hybrid Search with fallback ─────────────────────────────────

  function searchRelevant(query, filter = {}, topK = 10) {
    if (!hybridSearch || hybridSearch.size() === 0) return [];
    try { return hybridSearch.search(query, { topK, filter }); }
    catch (e) { console.warn(`[Search] Hybrid search failed: ${e.message}`); return []; }
  }

  function getKnowledgeForScene(sceneQuery, topK = 15) {
    const results = searchRelevant(sceneQuery, {}, topK);
    const decisions = [];
    const tasks = [];
    const risks = [];
    const updates = [];
    
    for (const r of results) {
      const type = r.metadata?.type || '';
      const text = r.text || '';
      if (type === 'decision') decisions.push({ title: text.split(':')[0], summary: text });
      else if (type === 'action_item') tasks.push({ text: text, title: text.split(':')[0] });
      else if (type === 'risk') risks.push({ title: text });
      else if (type === 'update') updates.push({ title: text });
    }
    
    // Fallback to DB if empty
    if (decisions.length === 0) {
      for (const d of DB.getKnowledgeByType(db, 'decision', 5))
        decisions.push({ title: d.title, summary: d.summary });
    }
    if (tasks.length === 0) {
      for (const t of DB.getKnowledgeByType(db, 'action_item', 5))
        tasks.push({ text: t.title, title: t.title });
    }
    if (risks.length === 0) {
      for (const r of DB.getKnowledgeByType(db, 'risk', 5))
        risks.push({ title: r.title, summary: r.summary });
    }
    
    return { results, decisions, tasks, risks, updates };
  }

  function getEventContext(entityNames) {
    if (!eventGraph) return '';
    try { return eventGraph.buildContextSummary(entityNames); } catch (e) { return ''; }
  }

  function getOpenItems() {
    if (!eventGraph) return [];
    try { return eventGraph.getOpenItems(10); } catch (e) { return []; }
  }

  function getUpcomingMeetings() {
    const now = new Date();
    const twoHoursLater = new Date(now.getTime() + 2 * 60 * 60 * 1000);
    const sourceMeetings = DB.getSourceObjectsByType(db, 'calendar_event', 50);
    const meetings = [];
    for (const m of sourceMeetings) {
      try {
        const meta = JSON.parse(m.metadata_json || '{}');
        const startTime = new Date(meta.start_time || m.created_at);
        if (startTime > now && startTime <= twoHoursLater) {
          meetings.push({ id: m.source_id, title: m.title, startTime: startTime.toISOString(), description: m.content, participants: meta.participants || [] });
        }
      } catch {}
    }
    return meetings;
  }

  // ── 1. Meeting Briefing ─────────────────────────────────────────────

  async function executeMeetingBriefingScene(triggerId, params) {
    const runId = `exec_${uuid().slice(0, 12)}`;
    DB.createAgentRun(db, { run_id: runId, scene_type: 'meeting_briefing' });
    const startTs = params?.startTs || (Math.floor(Date.now() / 1000) - 24 * 3600);
    const endTs = params?.endTs || Math.floor(Date.now() / 1000);

    const upcomingMeetings = triggerId
      ? [{ id: triggerId, title: params?.title || 'Meeting', startTime: new Date().toISOString() }]
      : getUpcomingMeetings();

    // Fetch Feishu calendar
    if (feishu) {
      try {
        const cal = await feishu.getPrimaryCalendar();
        if (cal) {
          const feishuMeetings = await feishu.getCalendarEvents(cal.calendar_id, startTs, endTs);
          for (const m of feishuMeetings) {
            const meta = { start_time: m.start_time?.timestamp, end_time: m.end_time?.timestamp, timezone: m.start_time?.timezone, organizer: m.event_organizer?.display_name, participants: [] };
            DB.upsertSourceObject(db, { source_id: m.event_id, source_type: 'calendar_event', title: m.summary || m.title || 'Untitled Event', content: m.description || '', metadata: meta, url: m.app_link || '' });
            try { const attendees = await feishu.getEventAttendees(cal.calendar_id, m.event_id); meta.participants = attendees.map(a => ({ id: a.user_id, name: a.display_name })); } catch {}
          }
        }
      } catch (e) { console.warn(`[MeetingBriefing] Feishu error: ${e.message}`); }
    }

    const meetingInfo = {
      title: upcomingMeetings[0]?.title || params?.title || 'Upcoming Meeting',
      startTime: upcomingMeetings[0]?.startTime || new Date().toISOString(),
      description: params?.description || '',
      participants: params?.participants || [],
    };

    // Hybrid Search by meeting title + participants
    const searchQuery = `${meetingInfo.title} ${(meetingInfo.participants || []).map(p => p.name || p).join(' ')}`;
    const knowledge = getKnowledgeForScene(searchQuery, 20);
    const openItems = getOpenItems();
    const entityNames = [meetingInfo.title, ...(meetingInfo.participants || []).map(p => p.name || p)];
    const eventContext = getEventContext(entityNames);
    const recentEntities = DB.getAllEntities(db, null, 20);
    const relatedEntityNames = recentEntities.map(e => e.name);

    let briefing = null;
    const prevDecisions = knowledge.decisions.map(d => `${d.title}: ${d.summary}`);
    const pendingItems = knowledge.tasks.map(t => ({ text: t.text || t.title || '', owner: '', status: 'pending' }));
    const risks = knowledge.risks.map(r => r.title);

    // GraphRAG: traverse entity relationships to find unresolved tasks and risks
    let graphRAGContext = null;
    if (graphRAG && entityNames.length > 0) {
      try {
        const ctx = graphRAG.buildContext(entityNames, { maxDepth: 2 });
        if (ctx.relatedDecisions.length > 0 || ctx.relatedRisks.length > 0) {
          graphRAGContext = ctx;
          // Supplement decisions/risks from GraphRAG
          for (const d of ctx.relatedDecisions) {
            const label = `${d.title}: ${(d.summary || '').slice(0, 100)}`;
            if (!prevDecisions.includes(label)) prevDecisions.push(label);
          }
          for (const r of ctx.relatedRisks) {
            if (!risks.includes(r.title)) risks.push(r.title);
          }
        }
      } catch (e) { console.warn('[MeetingBriefing] GraphRAG error:', e.message); }
    }

    if (llm.available) {
      try { briefing = await llm.generateMeetingBriefing(meetingInfo, { decisions: prevDecisions, actionItems: pendingItems }, []); } catch {}
    }

    let summary;
    if (briefing) {
      summary = `# Meeting Briefing - ${meetingInfo.title}\n\n${briefing.summary}`;
    } else {
      summary = [
        `**Meeting Briefing - ${meetingInfo.title}**`,
        `Time: ${new Date(meetingInfo.startTime).toLocaleString('zh-CN')}`, '', '---', '',
        prevDecisions.length > 0 ? `**Key Decisions (Hybrid Search)**\n${prevDecisions.map(d => `- ${d}`).join('\n')}` : '',
        pendingItems.length > 0 ? `**Action Items (Event Graph)**\n${pendingItems.map(t => `- ${t.text}`).join('\n')}` : '',
        risks.length > 0 ? `**Risks**\n${risks.map(r => `- ${r}`).join('\n')}` : '',
        openItems.length > 0 ? `**Open Items**\n${openItems.map(o => `- [${o.type}] ${o.summary}`).join('\n')}` : '',
        graphRAGContext ? `**GraphRAG Context**\n${graphRAGContext.impactSummary}` : '',
        eventContext ? `**Event Context**\n${eventContext}` : '',
      ].filter(Boolean).join('\n');
    }

    const briefingKnowledge = { title: meetingInfo.title, summary: searchQuery, entities: entityNames, createdAt: new Date().toISOString() };
    const briefingContext = { sceneType: 'meeting_briefing', participants: params?.participants || [] };
    const psUsers = getPushScoreUsers(briefingKnowledge, briefingContext, params?.participants || ['user_current']);
    const receivers = psUsers.length > 0 ? psUsers : (params?.participants || ['user_current']);
    DB.completeAgentRun(db, runId, { status: 'completed', summary: { title: meetingInfo.title, decisionCount: prevDecisions.length, riskCount: risks.length }, total_receivers: receivers.length, push_count: receivers.length, duration_ms: 0 });
    return {
      success: true, execution_id: runId, summary, scene_type: 'meeting_briefing',
      source_refs: [...knowledge.decisions.map(d => ({ type: 'decision', title: d.title })), ...knowledge.tasks.map(t => ({ type: 'task', title: t.text || t.title }))],
      preview: { title: `Meeting Briefing - ${meetingInfo.title}`, summary: `Generated for ${receivers.length} participants (Hybrid Search + Event Graph + GraphRAG)`, receivers, push_channels: ['feishu_im'] },
      stats: { total_receivers: receivers.length, success_count: 0, failed_count: 0 },
    };
  }

  // ── 2. Weekly Digest ────────────────────────────────────────────────

  async function executeWeeklyDigestScene(params) {
    const runId = `exec_${uuid().slice(0, 12)}`;
    DB.createAgentRun(db, { run_id: runId, scene_type: 'weekly_digest' });
    
    const recentKnowledge = DB.getRecentKnowledge(db, 30);
    const recentMessages = DB.getMessagesSince(db, new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString(), 50);
    const activeEntities = DB.getAllEntities(db, null, 30);
    const knowledge = getKnowledgeForScene('weekly work', 30);
    const openItems = getOpenItems();
    const recentEvents = eventGraph ? eventGraph.getRecentEvents(7, 20) : [];

    // Group events by type for trend detection
    const eventClusters = {};
    for (const evt of recentEvents) {
      const type = evt.type || 'other';
      if (!eventClusters[type]) eventClusters[type] = [];
      eventClusters[type].push(evt.summary);
    }

    // GraphRAG: aggregate context from the most active entities
    let graphRAGSummary = '';
    if (graphRAG && activeEntities.length > 0) {
      try {
        const topEntities = activeEntities.slice(0, 5).map(e => e.name);
        const ctx = graphRAG.buildContext(topEntities, { maxDepth: 1 });
        graphRAGSummary = ctx.impactSummary;
      } catch (e) { console.warn('[WeeklyDigest] GraphRAG error:', e.message); }
    }

    let digest = null;
    if (llm.available) {
      try { digest = await llm.generateWeeklyDigest(recentKnowledge, activeEntities); } catch {}
    }

    const decisionCount = knowledge.decisions.length;
    const riskCount = knowledge.risks.length;
    const msgCount = recentMessages.length;

    let summary;
    if (digest) {
      summary = `# Weekly Knowledge Report\n\n${digest.summary}\n\n---\n${(digest.sections || []).map(s => `## ${s.heading}\n${s.items.map(i => `- ${i}`).join('\n')}`).join('\n\n')}`;
    } else {
      summary = [
        `# Weekly Knowledge Report`, '',
        `**Knowledge Items** (${recentKnowledge.length})`,
        ...recentKnowledge.slice(0, 10).map(k => `- [${k.knowledge_type}] ${k.title}`), '',
        `**Decisions** (${decisionCount})`,
        ...knowledge.decisions.slice(0, 10).map(d => `- ${d.title}: ${(d.summary || '').slice(0, 100)}`), '',
        `**Risks** (${riskCount})`,
        ...knowledge.risks.slice(0, 8).map(r => `- ${r.title}: ${(r.summary || '').slice(0, 100)}`), '',
        ...Object.entries(eventClusters).map(([type, items]) => 
          `**Event Trend - ${type}** (${items.length})\n${items.slice(0, 5).map(i => `- ${i}`).join('\n')}`
        ), '',
        graphRAGSummary ? `**GraphRAG Context**\n${graphRAGSummary}` : '',
        `**Open Items** (${openItems.length})`,
        ...openItems.slice(0, 8).map(o => `- [${o.type}] ${o.summary.slice(0, 100)}`), '',
        `**Messages** (${msgCount} this week)`,
        `**Active Entities** (${activeEntities.length})`,
        ...activeEntities.slice(0, 15).map(e => `- ${e.name} (${e.entity_type}, ${e.mention_count} mentions)`),
      ].filter(Boolean).join('\n');
    }

    const users = DB.getAllEntities(db, 'person', 10);
    const digestKnowledge = { title: 'Weekly Knowledge Report', summary: (knowledge.results || []).map(r => r.text || '').join(' '), entities: [], createdAt: new Date().toISOString() };
    const digestContext = { sceneType: 'weekly_digest' };
    const psUsers = getPushScoreUsers(digestKnowledge, digestContext, users.map(u => u.entity_id));
    const receivers = psUsers.length > 0 ? psUsers : users.map(u => u.entity_id);
    DB.completeAgentRun(db, runId, { status: 'completed', summary: { knowledgeCount: recentKnowledge.length, decisionCount, riskCount, msgCount }, total_receivers: receivers.length, push_count: receivers.length, duration_ms: 0 });
    return {
      success: true, execution_id: runId, summary, scene_type: 'weekly_digest',
      source_refs: recentKnowledge.map(k => ({ type: 'knowledge', id: k.knowledge_id, title: k.title })),
      preview: { title: 'Weekly Knowledge Report', summary: `${recentKnowledge.length} knowledge items, ${decisionCount} decisions, ${riskCount} risks, ${openItems.length} open items`, receivers, push_channels: ['feishu_im'] },
      stats: { total_receivers: receivers.length, success_count: 0, failed_count: 0 },
    };
  }

  // ── 3. Doc Change ──────────────────────────────────────────────────

  async function executeDocChangeScene(triggerId, params) {
    const runId = `exec_${uuid().slice(0, 12)}`;
    DB.createAgentRun(db, { run_id: runId, scene_type: 'doc_change' });

    let docs = [];
    if (feishu) {
      try {
        const results = await feishu.searchWiki(params?.query || '');
        docs = results.map(r => ({
          source_id: r.obj?.doc_token || r.url, source_type: 'doc',
          title: r.title || r.obj?.title || 'Untitled',
          content: r.content || r.summary || '', author: r.obj?.owner_name || '', url: r.url || '',
        }));
        for (const d of docs) {
          DB.upsertSourceObject(db, d);
          if (hybridSearch) hybridSearch.indexDocument(d.source_id, `${d.title}: ${d.content}`, { type: 'doc_update', sourceType: 'doc', author: d.author }, new Date().toISOString());
        }
      } catch {}
    }

    const recentDocs = DB.getSourceObjectsByType(db, 'doc', 10);
    const allDocs = docs.length > 0 ? docs : recentDocs;

    // GraphRAG: impact analysis for each changed document
    let impactAnalysis = null;
    let graphRAGEdge = '';
    if (graphRAG && allDocs.length > 0) {
      try {
        const docTitles = allDocs.slice(0, 3).map(d => d.title);
        impactAnalysis = graphRAG.analyzeImpact(docTitles.join(' '));
        if (impactAnalysis) {
          const parts = [];
          if (impactAnalysis.affectedProjects.length > 0) parts.push(`Projects: ${impactAnalysis.affectedProjects.join(', ')}`);
          if (impactAnalysis.affectedPeople.length > 0) parts.push(`People: ${impactAnalysis.affectedPeople.join(', ')}`);
          if (impactAnalysis.affectedDecisions.length > 0) parts.push(`Decisions: ${impactAnalysis.affectedDecisions.length}`);
          if (impactAnalysis.affectedTasks.length > 0) parts.push(`Tasks: ${impactAnalysis.affectedTasks.length}`);
          graphRAGEdge = parts.length > 0 ? `**GraphRAG Impact**\n${parts.join('\n')}` : '';
        }
      } catch (e) { console.warn('[DocChange] GraphRAG error:', e.message); }
    }

    let impactedKnowledge = [];
    if (allDocs.length > 0) {
      const docTitles = allDocs.map(d => d.title).join(' ');
      impactedKnowledge = searchRelevant(docTitles, {}, 10);
    }
    const eventContext = allDocs.length > 0 ? getEventContext(allDocs.map(d => d.title)) : '';
    const recentUpdates = DB.getKnowledgeByType(db, 'update', 10);

    let summary;
    if (allDocs.length > 0) {
      summary = [
        `# Document Change Alert`,
        `Recent changes: ${allDocs.length} document(s)`, '',
        ...allDocs.slice(0, 5).map(d => [
          `**${d.title}**`,
          d.author ? `  Author: ${d.author}` : '',
          `  Updated: ${new Date(d.updated_at || Date.now()).toLocaleString('zh-CN')}`,
          d.content ? `  Summary: ${d.content.slice(0, 200)}` : '',
        ].filter(Boolean).join('\n')),
        graphRAGEdge || '',
        impactedKnowledge.length > 0 ? `**Affected Knowledge (Hybrid Search)**\n${impactedKnowledge.slice(0, 8).map(r => `- ${r.text ? r.text.split(':')[0] : r.id}`).join('\n')}` : '',
        eventContext ? `**Event Context**\n${eventContext}` : '',
        recentUpdates.length > 0 ? `**Related Updates**\n${recentUpdates.map(u => `- ${u.title}`).join('\n')}` : '',
      ].filter(Boolean).join('\n');
    } else {
      summary = '# Document Change Alert\n\nNo recent document changes found.';
    }

    const receivers = ['user_all'];
    DB.completeAgentRun(db, runId, { status: 'completed', summary: { docCount: allDocs.length, updateCount: recentUpdates.length }, total_receivers: receivers.length, push_count: receivers.length, duration_ms: 0 });
    return {
      success: true, execution_id: runId, summary, scene_type: 'doc_change',
      source_refs: allDocs.map(d => ({ type: 'document', id: d.source_id, title: d.title })),
      preview: { title: 'Document Change Alert', summary: `Detected ${allDocs.length} document change(s)`, receivers, push_channels: ['feishu_im'] },
      stats: { total_receivers: receivers.length, success_count: 0, failed_count: 0 },
    };
  }

  // ── 4. Onboarding ──────────────────────────────────────────────────

  async function executeOnboardingScene(params) {
    const runId = `exec_${uuid().slice(0, 12)}`;
    DB.createAgentRun(db, { run_id: runId, scene_type: 'onboarding' });
    const newUserId = params?.userId || params?.newUserId || 'new_user';
    const roleTags = params?.roleTags || ['new_join'];
    const projectName = params?.projectName || '';

    const searchQuery = `${projectName} ${(roleTags || []).join(' ')}`.trim() || 'project overview';
    const knowledge = getKnowledgeForScene(searchQuery, 25);
    const eventContext = projectName ? getEventContext([projectName]) : '';
    const openItems = getOpenItems();
    const recentDocs = DB.getSourceObjectsByType(db, 'doc', 5);
    const allEntities = DB.getAllEntities(db, null, 20);
    const people = DB.getAllEntities(db, 'person', 10);
    const projects = DB.getAllEntities(db, 'project', 10);

    DB.upsertUserProfile(db, { user_id: newUserId, user_name: params?.userName || 'New Member', role_tags: roleTags });

    // GraphRAG: generate project overview (people + decisions + documents)
    let graphRAGPeople = [];
    let graphRAGDecisions = [];
    let graphRAGSection = '';
    if (graphRAG && projects.length > 0) {
      try {
        const overview = graphRAG.buildProjectOverview(projects[0].name);
        if (overview && overview.overview.totalNodes > 0) {
          graphRAGPeople = overview.people;
          graphRAGDecisions = overview.decisions;
          graphRAGSection = `## Project Graph (GraphRAG)\n\n` +
            `Nodes: ${overview.overview.totalNodes} | ` +
            `People: ${overview.overview.peopleCount} | ` +
            `Decisions: ${overview.overview.decisionCount} | ` +
            `Docs: ${overview.overview.docCount} | ` +
            `Tasks: ${overview.overview.taskCount} | ` +
            `Risks: ${overview.overview.riskCount}\n\n`;
        }
      } catch (e) { console.warn('[Onboarding] GraphRAG error:', e.message); }
    }

    const summary = [
      `**Welcome to the team!**`, '',
      `## Project Overview`,
      projects.length > 0 ? `Current projects: ${projects.map(p => p.name).join(', ')}` : 'No project info yet', '',
      graphRAGSection || '',
      `## Required Reading`,
      ...recentDocs.slice(0, 5).map(d => `- ${d.title}${d.url ? ` (${d.url})` : ''}`), '',
      knowledge.decisions.length > 0 ? `## Key Decisions (Hybrid Search)\n${knowledge.decisions.slice(0, 8).map(d => `- ${d.title}: ${(d.summary || '').slice(0, 150)}`).join('\n')}` : '', '',
      graphRAGDecisions.length > 0 ? `## Related Decisions (GraphRAG)\n${graphRAGDecisions.slice(0, 5).map(d => `- ${d.title}: ${(d.summary || '').slice(0, 120)}`).join('\n')}` : '', '',
      knowledge.risks.length > 0 ? `## Current Risks\n${knowledge.risks.slice(0, 5).map(r => `- ${r.title}: ${(r.summary || '').slice(0, 120)}`).join('\n')}` : '', '',
      knowledge.tasks.length > 0 ? `## Open Tasks\n${knowledge.tasks.slice(0, 5).map(t => `- ${t.text || t.title}`).join('\n')}` : '', '',
      eventContext ? `## Event Context\n${eventContext}` : '', '',
      openItems.length > 0 ? `## Open Items\n${openItems.slice(0, 5).map(o => `- [${o.type}] ${o.summary.slice(0, 80)}`).join('\n')}` : '', '',
      `## Key Contacts`,
      ...(graphRAGPeople.length > 0
        ? graphRAGPeople.slice(0, 8).map(p => `- ${p.name} (GraphRAG relevance: ${p.relevance.toFixed(2)})`)
        : people.slice(0, 10).map(p => `- ${p.name}${p.properties_json ? ` (${JSON.parse(p.properties_json).role || ''})` : ''}`)
      ), '',
      `## Knowledge Graph Overview`,
      `${allEntities.length} entities total`, '', `---`,
      `For questions, ask in the group or contact the tech lead.`,
    ].filter(Boolean).join('\n');

    const receivers = [newUserId];
    DB.completeAgentRun(db, runId, { status: 'completed', summary: { userId: newUserId, knowledgeCount: knowledge.results.length, decisionCount: knowledge.decisions.length }, total_receivers: receivers.length, push_count: receivers.length, duration_ms: 0 });
    return {
      success: true, execution_id: runId, summary, scene_type: 'onboarding',
      source_refs: [...knowledge.decisions.slice(0, 5).map(d => ({ type: 'decision', title: d.title })), ...recentDocs.slice(0, 3).map(d => ({ type: 'document', id: d.source_id, title: d.title }))],
      preview: { title: 'Welcome Onboarding Package', summary: `Generated for ${newUserId}: ${knowledge.results.length} knowledge items, ${knowledge.decisions.length} decisions (Hybrid Search + Event Graph + GraphRAG)`, receivers, push_channels: ['feishu_im'] },
      stats: { total_receivers: receivers.length, success_count: 0, failed_count: 0 },
    };
  }

  // ── PushScore helper ──────────────────────────────────────────────

  function getPushScoreUsers(knowledge, context, candidateUsers) {
    if (!pushScore || !candidateUsers || candidateUsers.length === 0) {
      return candidateUsers || [];
    }

    // Build user objects from entity/user profiles in DB
    const users = candidateUsers.map(cu => {
      let id;
      if (typeof cu === 'object') {
        if (cu.userId) id = cu.userId;
        else if (cu.id) id = cu.id;
        else if (cu.user_id) id = cu.user_id;
        else id = JSON.stringify(cu);
      } else {
        id = cu;
      }
      const profile = DB.getUserProfile(db, id) || {};
      let roleTags;
      try { roleTags = profile.role_tags ? JSON.parse(profile.role_tags) : []; } catch { roleTags = Array.isArray(profile.role_tags) ? profile.role_tags : []; }
      return {
        userId: id,
        role_tags: roleTags,
        topics: profile.topics || [],
        muted_topics: profile.muted_topics_json ? JSON.parse(profile.muted_topics_json) : [],
      };
    });

    // Filter using PushScore batch scoring
    const scored = pushScore.filterByThreshold(users, knowledge, context, 0.3);
    return scored.map(u => u.userId || u.user_id);
  }

  return {
    executeMeetingBriefingScene,
    executeWeeklyDigestScene,
    executeDocChangeScene,
    executeOnboardingScene,
    getUpcomingMeetings,
  };
}
