package com.knowledgeradar.utils;

import com.google.gson.Gson;
import lombok.extern.slf4j.Slf4j;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
public class HttpUtils {
    private static final Gson gson = new Gson();
    // 全局复用 HttpClient 是最佳实践
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    /**
     * 发送飞书API GET请求的工具函数
     *
     * @param url    基础URL（不包含查询参数）
     * @param token  认证token
     * @param params 请求参数Map
     * @return API响应字符串
     * @throws IOException          网络或HTTP错误
     * @throws InterruptedException 线程中断异常
     */
    public static String sendHttpGet(String url, String token, Map<String, String> params) throws IOException, InterruptedException {
        String fullUrl = buildUrlWithParams(url, params);

        // 替换为 log.info("Sending GET request to: {}", fullUrl);
        System.out.println("Sending GET request to: " + fullUrl);

        // 创建GET请求（去除了多余的 Content-Type）
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(fullUrl))
                .timeout(Duration.ofSeconds(15))
                .header("Authorization", "Bearer " + token)
                .GET()
                .build();

        // 发送请求
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        // 检查HTTP状态码 (2xx 代表成功)
        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            String errorMsg = String.format("HTTP request failed, status code: %d, response: %s",
                    response.statusCode(), response.body());
            // 统一调用错误日志方法
            log.error(errorMsg);
            // 将详细错误抛出，方便上层捕获处理
            throw new IOException(errorMsg);
        }

        // 替换为 log.debug("GET request successful...");
        System.out.println("GET request successful, response received");
        return response.body();
    }

    /**
     * 发送飞书API POST请求的工具函数（接收 Map 参数）
     * @param url 完整URL
     * @param token 认证token
     * @param params 请求参数Map，将在内部被转换为JSON格式
     * @return API响应字符串
     * @throws IOException 网络或HTTP错误
     * @throws InterruptedException 线程中断异常
     */
    public static String sendHttpPost(String url, String token, Map<String, String> params) throws IOException, InterruptedException {
        System.out.println("Sending POST request to: " + url);

        // 使用 Gson 将 Map 转换为 JSON 字符串。如果 params 为空，则发送空 JSON 对象 "{}"
        String jsonBody = (params == null || params.isEmpty()) ? "{}" : gson.toJson(params);

        System.out.println("Request JSON Body: " + jsonBody);

        // 创建POST请求
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(15))
                // 添加认证头
                .header("Authorization", "Bearer " + token)
                // 严格设置内容类型为 json 及 utf-8 编码
                .header("Content-Type", "application/json; charset=utf-8")
                // 绑定 JSON 字符串作为请求体
                .POST(HttpRequest.BodyPublishers.ofString(jsonBody, StandardCharsets.UTF_8))
                .build();

        // 发送请求
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        // 检查HTTP状态码 (2xx 代表成功)
        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            String errorMsg = String.format("HTTP POST request failed, status code: %d, response: %s",
                    response.statusCode(), response.body());
            log.error(errorMsg);
            throw new IOException(errorMsg);
        }

        System.out.println("POST request successful, response received");
        return response.body();
    }

    /**
     * 辅助方法：优雅地构建带参数的 URL
     */
    private static String buildUrlWithParams(String baseUrl, Map<String, String> params) {
        if (params == null || params.isEmpty()) {
            return baseUrl;
        }

        String queryString = params.entrySet().stream()
                .map(entry -> {
                    String key = URLEncoder.encode(entry.getKey(), StandardCharsets.UTF_8);
                    String value = entry.getValue() != null ? URLEncoder.encode(entry.getValue(), StandardCharsets.UTF_8) : "";
                    return key + "=" + value;
                })
                .collect(Collectors.joining("&"));

        return baseUrl + "?" + queryString;
    }
}
