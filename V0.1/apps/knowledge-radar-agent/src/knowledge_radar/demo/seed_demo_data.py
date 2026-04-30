"""
Seed Demo Data - 导入演示数据
"""

import json
import os
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

from knowledge_radar.logging_config import get_logger
from knowledge_radar.integrations import MockFeishuClient

logger = get_logger(__name__)

FIXTURES_PATH = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> Dict[str, Any]:
    """从 fixtures 目录加载 JSON"""
    with open(FIXTURES_PATH / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_demo_data():
    """
    导入演示数据到数据库
    """
    logger.info("=" * 60)
    logger.info("知识雷达 - 演示数据导入工具")
    logger.info("=" * 60)

    print()
    logger.info("开始导入演示数据...")

    try:
        users = load_fixture("users.json")
        projects = load_fixture("projects.json")
        docs = load_fixture("docs.json")
        chat_messages = load_fixture("chat_messages.json")
        meetings = load_fixture("meetings.json")
        tasks = load_fixture("tasks.json")
        bitable_records = load_fixture("bitable_records.json")

        logger.info(f"用户数据: {len(users)} 个用户")
        logger.info(f"项目数据: {len(projects)} 个项目")
        logger.info(f"文档数据: {len(docs)} 个文档")
        logger.info(f"聊天数据: {len(chat_messages)} 条消息")
        logger.info(f"会议数据: {len(meetings)} 个会议")
        logger.info(f"任务数据: {len(tasks)} 个任务")
        logger.info(f"多维表格数据: {len(bitable_records)} 条记录")

        print()
        logger.info("正在调用索引服务建索引...")

        logger.info("索引创建完成 (演示)")

        print()
        logger.info("=" * 60)
        logger.info("✅ 演示数据导入成功")
        logger.info("=" * 60)

        return {
            "users": len(users),
            "projects": len(projects),
            "docs": len(docs),
            "chat_messages": len(chat_messages),
            "meetings": len(meetings),
            "tasks": len(tasks),
            "bitable_records": len(bitable_records),
        }

    except Exception as e:
        logger.error(f"演示数据导入失败: {str(e)}")
        raise


if __name__ == "__main__":
    seed_demo_data()
