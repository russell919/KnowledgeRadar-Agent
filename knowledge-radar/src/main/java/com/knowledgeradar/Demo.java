package com.knowledgeradar;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.lark.oapi.core.utils.Jsons;
import com.lark.oapi.event.EventDispatcher;
import com.lark.oapi.service.calendar.CalendarService;
import com.lark.oapi.service.calendar.v4.model.*;
import com.lark.oapi.service.im.v1.model.CreateMessageReq;
import com.lark.oapi.service.im.v1.model.CreateMessageReqBody;
import com.lark.oapi.service.im.v1.model.CreateMessageResp;
import com.lark.oapi.ws.Client;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import io.github.cdimascio.dotenv.Dotenv;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.concurrent.*;

@Slf4j
public class Demo {
    // 初始化 Dotenv 实例，只会在类加载时执行一次
    private static final Dotenv dotenv = Dotenv.load();

    private static final String APP_ID = dotenv.get("APP_ID");
    private static final String APP_SECRET = dotenv.get("APP_SECRET");
    private static final String OPEN_ID = dotenv.get("OPEN_ID");
    private static final String USER_ACCESS_TOKEN=dotenv.get("USER_ACCESS_TOKEN");
    private static final long REMINDER_MINUTES = 30;

    private static com.lark.oapi.Client apiClient;
    private static final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(4);
    private static final ConcurrentHashMap<String, ScheduledFuture<?>> scheduledReminders = new ConcurrentHashMap<>();
    private static final Gson gson = new Gson();
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    private static void logError(String errorMessage, String responseBody) {
        System.err.println("Error message: " + errorMessage);
        if (responseBody != null && !responseBody.isEmpty()) {
            System.err.println("Response content: " + responseBody);
        }
    }

    public static void main(String[] args) throws Exception {
        apiClient = com.lark.oapi.Client.newBuilder(APP_ID, APP_SECRET).build();

        EventDispatcher eventHandler = EventDispatcher.newBuilder("", "")
                .onP2CalendarEventChangedV4(new CalendarService.P2CalendarEventChangedV4Handler() {
                    @Override
                    public void handle(P2CalendarEventChangedV4 event) throws Exception {
                        // 处理日历事件变更
                        System.out.println("Calendar event changed: " + event.getEvent());
                    }
                })
                .build();
//        PrimaryCalendarReq req = PrimaryCalendarReq.newBuilder()
//                .userIdType("open_id")
//                .build();
//        PrimaryCalendarResp resp = apiClient.calendar().v4().calendar().primary(req);
        // 创建请求对象
        PrimarysCalendarReq req = PrimarysCalendarReq.newBuilder()
                .userIdType("open_id")
                .primarysCalendarReqBody(PrimarysCalendarReqBody.newBuilder()
                        .userIds(new String[]{OPEN_ID})
                        .build())
                .build();

        // 发起请求
        PrimarysCalendarResp resp = apiClient.calendar().v4().calendar().primarys(req);

        // 处理服务端错误
        if (!resp.success()) {
            System.out.println(String.format("code:%s,msg:%s,reqId:%s, resp:%s",
                    resp.getCode(), resp.getMsg(), resp.getRequestId(), Jsons.createGSON(true, false).toJson(JsonParser.parseString(new String(resp.getRawResponse().getBody(), StandardCharsets.UTF_8)))));
            return;
        }
        String calendarId = resp.getData().getCalendars()[0].getCalendar().getCalendarId();

        String json = Jsons.DEFAULT.toJson(resp.getData());
        // 业务数据处理
        System.out.println(json);

//        GetCalendarReq test = GetCalendarReq.newBuilder()
//                .calendarId(calendarId)
//                .build();
//        // 创建请求对象
//        SubscriptionCalendarEventReq subscriptionCalendarEventReq = SubscriptionCalendarEventReq.newBuilder()
//                .calendarId(calendarId)
//                .build();
//        RequestOptions options = RequestOptions.newBuilder()
//                .userAccessToken("u-cKEFMlLqd4FbyPcVt4SxWz0l4m2MklUPWEyy2QgyyICp")
//                .build();
        // 发起请求
//        GetCalendarResp testp = apiClient.calendar().v4().calendar().get(test,options);

        subscribeCalendarEvent(USER_ACCESS_TOKEN, calendarId);


        // 发起请求
//        SubscriptionCalendarEventResp eventResp = apiClient.calendar().v4().calendarEvent().subscription(subscriptionCalendarEventReq, options);
//        if (!eventResp.success()) {
//            System.out.println(String.format("code:%s,msg:%s,reqId:%s, resp:%s",
//                    resp.getCode(), resp.getMsg(), resp.getRequestId(), Jsons.createGSON(true, false).toJson(JsonParser.parseString(new String(resp.getRawResponse().getBody(), StandardCharsets.UTF_8)))));
//            return;
//
//        }

        // 业务数据处理
//        System.out.println(Jsons.DEFAULT.toJson(eventResp));

        Client cli = new Client.Builder(APP_ID, APP_SECRET)
                .eventHandler(eventHandler)
                .build();

        log.info("知识雷达启动，监听日程变更事件...");
        cli.start();
    }

    /**
     * 处理日程变更事件：解析 event 中的 calendar_id 和 event_id，调用日程列表接口定位日程详情。
     */
    private static void handleCalendarChangeEvent(String rawJson) {
        try {
            JsonObject root = JsonParser.parseString(rawJson).getAsJsonObject();
            JsonObject event = root.getAsJsonObject("event");

            String calendarId = event.get("calendar_id").getAsString();
            String eventId = event.get("event_id").getAsString();

            log.info("日程变更 - calendarId: {}, eventId: {}", calendarId, eventId);

            // 调用获取日程列表接口，定位变更日程
            fetchAndProcessEvent(calendarId, eventId);
        } catch (Exception e) {
            log.error("处理日程变更事件失败", e);
        }
    }

    /**
     * 调用日程列表接口，根据 eventId 定位日程，判断是否为即将开始的会议。
     */
    private static void fetchAndProcessEvent(String calendarId, String eventId) {
        try {
            long nowSeconds = Instant.now().getEpochSecond();
            long windowEnd = nowSeconds + (REMINDER_MINUTES + 5) * 60;

            ListCalendarEventReq req = ListCalendarEventReq.newBuilder()
                    .calendarId(calendarId)
                    .startTime(String.valueOf(nowSeconds))
                    .endTime(String.valueOf(windowEnd))
                    .build();

            ListCalendarEventResp resp = apiClient.calendar().calendarEvent().list(req);

            if (!resp.success()) {
                log.error("查询日程列表失败, code: {}, msg: {}", resp.getCode(), resp.getMsg());
                return;
            }

            ListCalendarEventRespBody data = resp.getData();
            if (data == null || data.getItems() == null) {
                log.info("日程列表为空");
                return;
            }

            boolean found = false;
            for (CalendarEvent evt : data.getItems()) {
                String evtId = evt.getEventId();

                // 通过 eventId 匹配变更的日程
                if (eventId.equals(evtId)) {
                    found = true;
                    processMeetingEvent(evt);
                    break;
                }
            }

            if (!found) {
                log.info("变更日程 {} 在列表中未找到（可能不在未来30分钟窗口内）", eventId);
            }
        } catch (Exception e) {
            log.error("调用日程列表接口异常", e);
        }
    }

    /**
     * 判断日程是否为会议，计算距开始时间，在开始前30分钟调度提醒。
     */
    private static void processMeetingEvent(CalendarEvent evt) {
        String summary = evt.getSummary() != null ? evt.getSummary() : "未知会议";

        // 解析开始时间
        TimeInfo startTimeInfo = evt.getStartTime();
        if (startTimeInfo == null || startTimeInfo.getTimestamp() == null) {
            log.info("日程 [{}] 没有时间戳，跳过", summary);
            return;
        }

        long startTimestamp;
        try {
            startTimestamp = Long.parseLong(startTimeInfo.getTimestamp());
        } catch (NumberFormatException e) {
            log.info("日程 [{}] 时间戳格式不正确: {}", summary, startTimeInfo.getTimestamp());
            return;
        }

        // 判断是否为会议（有视频会议链接、有多人参会、或日程标题含"会议"关键词）
        boolean isMeeting = false;

        // 有视频会议信息
        Vchat vchat = evt.getVchat();
        if (vchat != null && vchat.getMeetingUrl() != null && !vchat.getMeetingUrl().isEmpty()) {
            isMeeting = true;
        }

        // 有多个参会人（日程组织者 + 其他人）
        if (evt.getAttendees() != null && evt.getAttendees().length > 1) {
            isMeeting = true;
        }

        // 日程标题包含会议关键词
        if (summary.contains("会议") || summary.toLowerCase().contains("meeting")
                || summary.toLowerCase().contains("sync") || summary.toLowerCase().contains("review")) {
            isMeeting = true;
        }

        if (!isMeeting) {
            log.info("日程 [{}] 不是会议类型，跳过提醒", summary);
            return;
        }

        // 计算距开始的时间差
        long nowSeconds = Instant.now().getEpochSecond();
        long secondsUntilStart = startTimestamp - nowSeconds;
        long minutesUntilStart = secondsUntilStart / 60;

        LocalDateTime meetingTime = LocalDateTime.ofInstant(
                Instant.ofEpochSecond(startTimestamp), ZoneId.systemDefault());
        String timeStr = meetingTime.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"));

        String eventKey = evt.getEventId() != null ? evt.getEventId() : summary;

        if (minutesUntilStart > REMINDER_MINUTES) {
            // 距开始超过30分钟，调度在30分钟时提醒
            long delaySeconds = secondsUntilStart - REMINDER_MINUTES * 60;
            scheduleReminder(eventKey, summary, timeStr, delaySeconds);
        } else if (minutesUntilStart > 0 && minutesUntilStart <= REMINDER_MINUTES) {
            // 已在30分钟窗口内，立即提醒一次
            scheduleReminder(eventKey, summary, timeStr, 0);
        } else {
            log.info("会议 [{}] 已开始或已过期，跳过", summary);
        }
    }

    /**
     * 调度提醒任务，在指定延迟后发送消息。
     */
    private static void scheduleReminder(String eventKey, String summary, String meetingTime, long delaySeconds) {
        // 取消已有的同类提醒（日程变更后重新调度）
        ScheduledFuture<?> existing = scheduledReminders.remove(eventKey);
        if (existing != null && !existing.isDone()) {
            existing.cancel(false);
            log.info("已取消旧的提醒任务: {}", eventKey);
        }

        ScheduledFuture<?> future = scheduler.schedule(() -> {
            try {
                sendMeetingReminder(summary, meetingTime);
                scheduledReminders.remove(eventKey);
            } catch (Exception e) {
                log.error("发送会议提醒失败: {}", summary, e);
            }
        }, delaySeconds, TimeUnit.SECONDS);

        scheduledReminders.put(eventKey, future);

        if (delaySeconds > 0) {
            log.info("已安排提醒: [{}] 将在 {} 秒后提醒", summary, delaySeconds);
        } else {
            log.info("即将立即提醒: [{}]", summary);
        }
    }

    /**
     * 通过 IM 接口给当前应用的机器人发送提醒消息。
     * 需要填入接收人的 open_id 才能实际发送消息。
     */
    private static void sendMeetingReminder(String summary, String meetingTime) {
        String content = String.format(
                "会议提醒：[%s] 将在 %d 分钟后开始（%s），请做好准备。",
                summary, REMINDER_MINUTES, meetingTime
        );

        log.info(">>> 发送会议提醒: {}", content);

        // 构造 text 消息的 JSON content
        JsonObject textJson = new JsonObject();
        textJson.addProperty("text", content);

        try {
            CreateMessageReq req = CreateMessageReq.newBuilder()
                    .receiveIdType("open_id")
                    .createMessageReqBody(CreateMessageReqBody.newBuilder()
                            .receiveId(OPEN_ID)  // 填入接收人的 open_id
                            .msgType("text")
                            .content(textJson.toString())
                            .build())
                    .build();

            CreateMessageResp resp = apiClient.im().message().create(req);

            if (resp.success()) {
                log.info("会议提醒发送成功: {}", summary);
            } else {
                log.error("会议提醒发送失败, code: {}, msg: {}", resp.getCode(), resp.getMsg());
            }
        } catch (Exception e) {
            log.error("发送会议提醒异常", e);
        }
    }

    // 订阅日程变更事件
    public static void subscribeCalendarEvent(String userAccessToken, String calendarId) throws IOException, InterruptedException {
        String url = "https://open.feishu.cn/open-apis/calendar/v4/calendars/" + URLEncoder.encode(calendarId, StandardCharsets.UTF_8) + "/events/subscription";

        System.out.println("Subscribing to calendar event changes, request URL: " + url);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(15))
                .header("Authorization", "Bearer " + userAccessToken)
                .header("Content-Type", "application/json; charset=utf-8")
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            logError("HTTP request failed, status code: " + response.statusCode(), response.body());
            throw new IOException("HTTP request failed, status code: " + response.statusCode());
        }

        Map<String, Object> result = gson.fromJson(response.body(), new TypeToken<Map<String, Object>>() {
        }.getType());
        Double code = (Double) result.get("code");
        if (code == null || code.intValue() != 0) {
            String errorMsg = "Failed to subscribe calendar event: " + result.get("msg");
            logError(errorMsg, response.body());
            throw new IOException(errorMsg);
        }

        System.out.println("Successfully subscribed to calendar event changes for calendar: " + calendarId);
    }
}