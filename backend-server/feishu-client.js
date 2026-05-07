/**
 * Knowledge Radar — Feishu/Lark API Client
 *
 * Direct HTTP-based client using user_access_token.
 * This replaces both MockFeishuClient and FeishuCLIClient (lark-cli).
 */

import fetch from 'node-fetch';

const BASE = 'https://open.feishu.cn/open-apis';

export class FeishuClient {
  constructor(token, botToken) {
    this.token = token;
    this.botToken = botToken || '';
    this._headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
    if (botToken) {
      this._botHeaders = {
        'Authorization': `Bearer ${botToken}`,
        'Content-Type': 'application/json',
      };
    }
  }

  async _get(path) {
    const res = await fetch(`${BASE}${path}`, { headers: this._headers });
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      throw new Error(`Feishu API GET ${path}: ${res.status} ${body.slice(0, 200)}`);
    }
    return res.json();
  }

  async _post(path, body = {}) {
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: this._headers,
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Feishu API POST ${path}: ${res.status} ${text.slice(0, 200)}`);
    }
    return res.json();
  }

  // ── User Info ───────────────────────────────────────────────────────────

  async getCurrentUser() {
    try {
      const data = await this._get('/contact/v3/users/me');
      return data.data?.user || {};
    } catch (e) {
      // Maybe contact scope not granted; return basic info
      return {};
    }
  }

  // ── Calendar ────────────────────────────────────────────────────────────

  async getPrimaryCalendar() {
    const data = await this._get('/calendar/v4/calendars?page_size=50');
    const calendars = data.data?.calendar_list || [];
    return calendars.find(c => c.type === 'primary') || calendars[0];
  }

  async getCalendarEvents(calendarId, startTs, endTs) {
    const encId = encodeURIComponent(calendarId);
    const data = await this._get(
      `/calendar/v4/calendars/${encId}/events?page_size=50&start_time=${startTs}&end_time=${endTs}`
    );
    return data.data?.items || [];
  }

  async getEventAttendees(calendarId, eventId) {
    const encCal = encodeURIComponent(calendarId);
    const data = await this._get(
      `/calendar/v4/calendars/${encCal}/events/${encodeURIComponent(eventId)}/attendees?page_size=50`
    );
    return data.data?.items || [];
  }

  // ── Documents ───────────────────────────────────────────────────────────

  async readDocument(docToken) {
    const data = await this._get(`/docx/v1/documents/${docToken}/raw_content`);
    return data.data || {};
  }

  async downloadFile(fileToken) {
    const res = await fetch(`${BASE}/drive/v1/medias/${fileToken}/download`, {
      headers: { 'Authorization': `Bearer ${this.token}` },
    });
    if (!res.ok) return null;
    return res.text();
  }

  // ── Chat / Messages ─────────────────────────────────────────────────────

  async listMessages(chatId, pageSize = 50, pageToken = null) {
    let path = `/im/v1/messages?container_id_type=chat&container_id=${encodeURIComponent(chatId)}&page_size=${pageSize}&sort_type=ByCreateTimeDesc`;
    if (pageToken) path += `&page_token=${pageToken}`;
    const data = await this._get(path);
    return data.data || { items: [] };
  }

  async _postWithToken(path, body, token) {
    const headers = token ? {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    } : this._headers;
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Feishu API POST ${path}: ${res.status} ${text.slice(0, 200)}`);
    }
    return res.json();
  }

  async sendMessage(chatId, msgType, content) {
    const data = await this._post('/im/v1/messages', {
      receive_id: chatId,
      msg_type: msgType,
      content: typeof content === 'string' ? content : JSON.stringify(content),
    });
    return data.data || {};
  }

  async sendText(chatId, text) {
    return this.sendMessage(chatId, 'text', JSON.stringify({ text }));
  }

  async sendCard(chatId, card) {
    return this.sendMessage(chatId, 'interactive', JSON.stringify(card));
  }

  // Bot-specific send methods (uses tenant token instead of user token)
  async sendBotMessage(openId, msgType, content) {
    const data = await this._postWithToken('/im/v1/messages?receive_id_type=open_id', {
      receive_id: openId,
      msg_type: msgType,
      content: typeof content === 'string' ? content : JSON.stringify(content),
    }, this.botToken);
    return data.data || {};
  }

  async sendBotText(openId, text) {
    return this.sendBotMessage(openId, 'text', JSON.stringify({ text }));
  }

  async sendBotCard(openId, card) {
    return this.sendBotMessage(openId, 'interactive', JSON.stringify(card));
  }

  // ── Group Info ──────────────────────────────────────────────────────────

  async getChatInfo(chatId) {
    const data = await this._get(`/im/v1/chats/${encodeURIComponent(chatId)}`);
    return data.data || {};
  }

  async listChatMembers(chatId) {
    const data = await this._get(`/im/v1/chats/${encodeURIComponent(chatId)}/members?page_size=50`);
    return data.data?.items || [];
  }

  // ── Meetings ────────────────────────────────────────────────────────────

  async getMeetingsByTime(startTs, endTs) {
    const data = await this._get(
      `/vc/v1/meetings?start_time=${startTs}&end_time=${endTs}&status=1`
    );
    return data.data || {};
  }

  // ── Tasks ────────────────────────────────────────────────────────────────

  async listTasks(pageSize = 50) {
    const data = await this._get(`/task/v1/tasks?page_size=${pageSize}`);
    return data.data?.items || [];
  }

  // ── Wiki / Knowledge Base ───────────────────────────────────────────────

  async searchWiki(query) {
    const data = await this._post('/wiki/v2/search', { query, page_size: 10 });
    return data.data?.items || [];
  }

  // ── Multi-dimensional Tables (Bitable) ──────────────────────────────────

  async listBitableRecords(appToken, tableId, pageSize = 20) {
    const data = await this._get(
      `/bitable/v1/apps/${appToken}/tables/${tableId}/records?page_size=${pageSize}`
    );
    return data.data?.items || [];
  }

  // ── Utilities ────────────────────────────────────────────────────────────

  async resolveUserId(identifier) {
    // Try open_id first, then user_id
    try {
      const data = await this._get(`/contact/v3/users/${encodeURIComponent(identifier)}`);
      return data.data?.user?.user_id || identifier;
    } catch {
      return identifier;
    }
  }
}
