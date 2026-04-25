package com.knowledgeradar;


import com.google.gson.JsonParser;
import com.lark.oapi.Client;
import com.lark.oapi.core.utils.Jsons;
import com.lark.oapi.service.event.v1.model.*;
import java.util.HashMap;
import com.lark.oapi.core.request.RequestOptions;

// SDK 使用文档：https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/server-side-sdk/java-sdk-guide/preparations
// 复制该 Demo 后, 需要将 "YOUR_APP_ID", "YOUR_APP_SECRET" 替换为自己应用的 APP_ID, APP_SECRET.
// 以下示例代码默认根据文档示例值填充，如果存在代码问题，请在 API 调试台填上相关必要参数后再复制代码使用
public class ListOutboundIpSample {

	public static void main(String arg[]) throws Exception {
		// 构建client
		Client client = Client.newBuilder("cli_a961f3962e389cd5", "BfrA7wcWDbQ4iDDGukbRKcDaiBHCwwZI").build();

		// 创建请求对象
		ListOutboundIpReq req = ListOutboundIpReq.newBuilder()
			.pageSize(10)
			.build();

		// 发起请求
		ListOutboundIpResp resp = client.event().v1().outboundIp().list(req);

		// 处理服务端错误
		if(!resp.success()) {
			System.out.println(String.format("code:%s,msg:%s,reqId:%s, resp:%s",
				resp.getCode(), resp.getMsg(), resp.getRequestId(), Jsons.createGSON(true, false).toJson(JsonParser.parseString(new String(resp.getRawResponse().getBody(), "UTF-8")))));
			return;
		}

		// 业务数据处理
		System.out.println(Jsons.DEFAULT.toJson(resp.getData()));
	}
}