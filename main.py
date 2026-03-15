from contextlib import asynccontextmanager

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.star.filter.platform_adapter_type import PlatformAdapterType


class GroupLog(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context, config)
        self.log_enabled: bool = bool(config.get("log", True))
        self.log_event: list = list(config.get("event_types", []))


    async def log(self, type: str, string: str):
        """日志"""
        if self.log_enabled:
            if type in self.log_event:
                logger.info(string)

    @filter.platform_adapter_type(PlatformAdapterType.AIOCQHTTP, priority=5)
    async def handle_group(self, event: AiocqhttpMessageEvent):
        """处理群事件"""
        raw = getattr(event.message_obj, "raw_message", None)
        if not isinstance(raw, dict):
            return

        post_type = raw.get("post_type")
        user_id = str(raw.get("user_id"))
        group_id = str(raw.get("group_id"))

        if post_type == "request" and raw.get("request_type") == "group":
            sub_type = raw.get("sub_type")
            comment = raw.get("comment", "")
            flag = raw.get("flag", "")
            question,answer,verify_type = ""
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

            if sub_type == "add":
                # 加群
                await self.log("加群申请",
                    f"收到用户 {user_id} 的加群申请 | "
                    f"问题: {question} | "
                    f"回答: {answer} | "
                    f"验证方式: {verify_type} | "
                    f"请求标识: {flag}"
                )

        elif post_type == "notice":
            notice_type = raw.get("notice_type")

            # 增加
            if notice_type == "group_increase":
                sub_type = raw.get("sub_type")
                operator_id = raw.get("operator_id")
                if sub_type == "approve":
                    await self.log("进群事件",f"用户 {user_id} 被管理员 {operator_id} 同意加入群 {group_id}")
                    
                elif sub_type == "invite":
                    await self.log("进群事件",f"用户 {user_id} 被 {operator_id} 邀请加入群 {group_id}")
            # 减少
            elif notice_type == "group_decrease":
                sub_type = raw.get("sub_type")
                operator_id = raw.get("operator_id")
                if sub_type == "leave":
                    await self.log("退群/踢出",f"用户 {user_id} 主动退出群 {group_id}")
                elif sub_type == "kick":
                    await self.log("退群/踢出",f"用户 {user_id} 被管理员 {operator_id} 踢出群 {group_id}")

            # 管理变动
            elif notice_type == "group_admin":
                sub_type = raw.get("sub_type")
                if sub_type == "set":
                    await self.log("管理员变动",f"用户 {user_id} 被设置为管理员")
                elif sub_type == "unset":
                    await self.log("管理员变动",f"用户 {user_id} 被取消管理员身份")
            
            # 禁言
            elif notice_type == "group_ban":
                sub_type = raw.get("sub_type")
                operator_id = raw.get("operator_id")
                duration = raw.get("duration")
                if sub_type == "ban":
                    if user_id == "0":
                        await self.log("禁言/解禁",f"管理员 {operator_id} 开启全体禁言")
                    else:
                        await self.log("禁言/解禁",f"用户 {user_id} 被管理员 {operator_id} 禁言 {duration} 秒")
                elif sub_type == "lift_ban":
                    if user_id == "0":
                        await self.log("禁言/解禁",f"管理员 {operator_id} 解除全体禁言")
                    else:
                        await self.log("禁言/解禁",f"用户 {user_id} 的禁言被管理员 {operator_id} 解除")

            elif notice_type == "notify":
                sub_type = raw.get("sub_type")

                if sub_type == "group_name":
                    name_new = raw.get("name_new")
                    await self.log("其他通知",f"用户 {user_id} 将群 {group_id} 的名称修改为 {name_new}")
                elif sub_type == "poke":
                    target_id = raw.get("target_id")
                    txt = raw.get("raw_info", [])
                    await self.log("其他通知",f"用户 {user_id} {txt[2].get('txt')} {target_id}")

            # 撤回
            elif notice_type == "group_recall":
                operator_id = raw.get("operator_id")
                message_id = raw.get("message_id")
                if str(operator_id) == str(user_id):
                    await self.log("消息撤回",f"用户 {user_id} 撤回 {message_id} 消息")
                else:
                    await self.log("消息撤回",f"用户 {user_id} 的消息 {message_id} 被 {operator_id} 撤回")

            # 精华
            elif notice_type == "essence":
                sub_type = raw.get("sub_type")
                operator_id = raw.get("operator_id")
                message_id = raw.get("message_id")
                sender_id = raw.get("sender_id")
                if user_id == "0":
                    sender_id = "自己"  
                if sub_type == "add":
                    await self.log("精华消息",f"管理员 {operator_id} 将 {sender_id} 的消息 {message_id} 添加为精华")
                elif sub_type == "delete":
                    # 好像收不到这个消息
                    await self.log("精华消息",f"管理员 {operator_id} 将 {sender_id} 的消息 {message_id} 移除精华")
            else:
                await logger.warning(f"收到未处理的 notice_type: {notice_type} | raw: {raw}")
        elif post_type == "message":
            pass
        else:
            await logger.warning(f"收到未处理的 post_type: {post_type} | raw: {raw}")
