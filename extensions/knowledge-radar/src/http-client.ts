import fetch, { Response } from 'node-fetch';
import type { KnowledgeRadarConfig } from './config';

/**
 * HTTP请求错误
 */
export class HttpClientError extends Error {
  constructor(
    message: string,
    public readonly path: string,
    public readonly status: number,
    public readonly responseBody?: string,
  ) {
    super(message);
    this.name = 'HttpClientError';
  }
}

/**
 * HTTP客户端，封装对知识雷达后端的请求
 */
export class HttpClient {
  private readonly baseUrl: string;
  private readonly apiKey?: string;

  constructor(config: KnowledgeRadarConfig) {
    this.baseUrl = config.backendBaseUrl.replace(/\/$/, '');
    this.apiKey = config.apiKey;
  }

  /**
   * 发送POST请求到后端
   * @param path 请求路径（以/开头）
   * @param body 请求体
   * @returns 响应数据
   * @throws HttpClientError 请求失败时抛出
   */
  async post<T = any>(path: string, body: any): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      });
    } catch (error) {
      throw new HttpClientError(
        `网络请求失败: ${(error as Error).message}`,
        path,
        0,
      );
    }

    if (!response.ok) {
      let responseBody: string | undefined;
      try {
        responseBody = await response.text();
      } catch {
        // 忽略响应体读取错误
      }

      throw new HttpClientError(
        `请求失败，状态码: ${response.status}`,
        path,
        response.status,
        responseBody,
      );
    }

    try {
      return await response.json() as T;
    } catch (error) {
      throw new HttpClientError(
        `解析响应JSON失败: ${(error as Error).message}`,
        path,
        response.status,
      );
    }
  }
}
