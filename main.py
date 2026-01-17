from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.star.filter.platform_adapter_type import PlatformAdapterType


class JoinLog(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.platform_adapter_type(PlatformAdapterType.AIOCQHTTP)
    async def handle_group_add(self, event: AiocqhttpMessageEvent):
        """处理加群和退群事件"""
        raw = getattr(event.message_obj, "raw_message", None)
        if not isinstance(raw, dict): return

        post_type = raw.get("post_type")
        user_id = str(raw.get("user_id"))
        group_id = str(raw.get("group_id"))

        # logger.info(f"测试: {raw}")

        if post_type == "request" and raw.get("request_type") == "group":
            sub_type = raw.get("sub_type")
            comment = raw.get("comment", "")
            verify_type = ""
            if '\n' in comment:
                verify_type = "验证消息"
                comment = comment.split('\n')
                if len(comment) >= 2:
                    question = comment[0][3:]
                    answer = comment[1][3:]
                else:
                    verify_type = "管理审核"
                    question = ""
                    answer = comment

                flag = raw.get("flag")

            if sub_type == "add":
                # 加群
                logger.info(f"收到用户 {user_id} 的加群申请")
                logger.info(f"问题: {question}")
                logger.info(f"回答: {answer}")
                logger.info(f"验证方式: {verify_type}")
                logger.info(f"请求标识: {flag}")

        elif post_type == "notice":
            notice_type = raw.get("notice_type")

            # 增加
            if notice_type == "group_increase":
                sub_type = raw.get("sub_type")
                operator_id = raw.get("operator_id")
                if sub_type == "approve":
                    logger.info(f"用户 {user_id} 被管理员 {operator_id} 同意加入群 {group_id}")
                elif sub_type == "invite":
                    logger.info(f"用户 {user_id} 被 {operator_id} 邀请加入群 {group_id}")
            # 减少
            elif notice_type == "group_decrease":
                sub_type = raw.get("sub_type")
                operator_id = raw.get("operator_id")
                if sub_type == "leave":
                    logger.info(f"用户 {user_id} 主动退出群 {group_id}")
                elif sub_type == "kick":
                    logger.info(f"用户 {user_id} 被管理员 {operator_id} 踢出群 {group_id}")