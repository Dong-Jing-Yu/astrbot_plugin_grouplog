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

    async def log(self, string: str):
        if self.log_enabled:
            logger.info(string)

    @filter.platform_adapter_type(PlatformAdapterType.AIOCQHTTP, priority=5)
    async def handle_group(self, event: AiocqhttpMessageEvent):
        """处理加群和退群事件"""
        raw = getattr(event.message_obj, "raw_message", None)
        if not isinstance(raw, dict): return

        post_type = raw.get("post_type")
        user_id = str(raw.get("user_id"))
        group_id = str(raw.get("group_id"))

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
                await self.log(f"收到用户 {user_id} 的加群申请\
                               问题: {question}\
                               回答: {answer}\
                               验证方式: {verify_type}\
                               请求标识: {flag}")

        elif post_type == "notice":
            notice_type = raw.get("notice_type")

            # 增加
            if notice_type == "group_increase":
                sub_type = raw.get("sub_type")
                operator_id = raw.get("operator_id")
                if sub_type == "approve":
                    await self.log(f"用户 {user_id} 被管理员 {operator_id} 同意加入群 {group_id}")
                    
                elif sub_type == "invite":
                    await self.log(f"用户 {user_id} 被 {operator_id} 邀请加入群 {group_id}")
            # 减少
            elif notice_type == "group_decrease":
                sub_type = raw.get("sub_type")
                operator_id = raw.get("operator_id")
                if sub_type == "leave":
                    await self.log(f"用户 {user_id} 主动退出群 {group_id}")
                elif sub_type == "kick":
                    await self.log(f"用户 {user_id} 被管理员 {operator_id} 踢出群 {group_id}")

            # 管理变动
            elif notice_type == "group_admin":
                sub_type = raw.get("sub_type")
                if sub_type == "set":
                    await self.log(f"用户 {user_id} 被设置为管理员")
                elif sub_type == "unset":
                    await self.log(f"用户 {user_id} 被取消管理员身份")
            
            # 禁言
            elif notice_type == "group_ban":
                sub_type = raw.get("sub_type")
                operator_id = raw.get("operator_id")
                duration = raw.get("duration")
                if sub_type == "ban":
                    await self.log(f"用户 {user_id} 被管理员 {operator_id} 禁言 {duration} 秒")
                elif sub_type == "lift_ban":
                    await self.log(f"用户 {user_id} 的禁言被管理员 {operator_id} 解除")

            elif notice_type == "notify":
                sub_type = raw.get("sub_type")

                if sub_type == "group_name":
                    name_new = raw.get("name_new")
                    await self.log(f"用户 {user_id} 将群 {group_id} 的名称修改为 {name_new}")
                elif sub_type == "poke":
                    target_id = raw.get("target_id")
                    txt = raw.get("raw_info")
                    await self.log(f"用户 {user_id} {txt[2].get('txt')} {target_id}")

            # 撤回
            elif notice_type == "group_recall":
                operator_id = raw.get("operator_id")
                message_id = raw.get("message_id")
                await self.log(f"测试: operator_id类型={type(operator_id)}, user_id类型={type(user_id)}")
                if operator_id == user_id:
                    await self.log(f"用户 {user_id} 撤回 {message_id} 消息")
                else:
                    await self.log(f"用户 {user_id} 的消息 {message_id} 被 {operator_id} 撤回")

            # 精华
            elif notice_type == "essence":
                sub_type = raw.get("sub_type")
                operator_id = raw.get("operator_id")
                message_id = raw.get("message_id")
                sender_id = raw.get("sender_id")
                if user_id == "0":
                    sender_id = "自己"  
                if sub_type == "add":
                    await self.log(f"管理员 {operator_id} 将 {sender_id} 的消息 {message_id} 添加为精华")
                elif sub_type == "delete":
                    # 确实收不到这个消息
                    await self.log(f"管理员 {operator_id} 将 {sender_id} 的消息 {message_id} 移除精华")
            else:
                await self.log(f"未处理的 notice_type: {notice_type}")
        else:
            await self.log(f"未处理的 post_type: {post_type}")
