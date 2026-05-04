import discord
import re
from datetime import timedelta
from typing import Optional


def parse_time(time_str: str) -> Optional[int]:
    patterns = {
        r'(\d+)d': 86400,
        r'(\d+)h': 3600,
        r'(\d+)m': 60,
        r'(\d+)s': 1,
    }
    total = 0
    found = False
    for pattern, multiplier in patterns.items():
        match = re.search(pattern, time_str.lower())
        if match:
            total += int(match.group(1)) * multiplier
            found = True
    return total if found else None


def format_timedelta(seconds: int) -> str:
    td = timedelta(seconds=seconds)
    parts = []
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if days:
        parts.append(f"{days} วัน")
    if hours:
        parts.append(f"{hours} ชม.")
    if minutes:
        parts.append(f"{minutes} นาที")
    if secs:
        parts.append(f"{secs} วิ")
    return " ".join(parts) if parts else "0 วิ"


def has_admin_perms(member: discord.Member) -> bool:
    return (member.guild_permissions.administrator or
            member.guild_permissions.manage_guild)


def has_mod_perms(member: discord.Member) -> bool:
    return (member.guild_permissions.kick_members or
            member.guild_permissions.ban_members or
            member.guild_permissions.manage_messages or
            member.guild_permissions.administrator)


def is_url(text: str) -> bool:
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|'
        r'(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return bool(url_pattern.search(text))


def extract_urls(text: str) -> list:
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|'
        r'(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return url_pattern.findall(text)


def truncate(text: str, max_length: int = 1024) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def chunk_list(lst: list, size: int) -> list:
    return [lst[i:i + size] for i in range(0, len(lst), size)]


async def safe_send(channel, **kwargs) -> Optional[discord.Message]:
    try:
        return await channel.send(**kwargs)
    except (discord.Forbidden, discord.HTTPException):
        return None


async def safe_delete(message: discord.Message) -> bool:
    try:
        await message.delete()
        return True
    except (discord.Forbidden, discord.NotFound):
        return False


def get_member_status(member: discord.Member) -> str:
    statuses = {
        discord.Status.online: "🟢 ออนไลน์",
        discord.Status.idle: "🟡 เงียบ",
        discord.Status.dnd: "🔴 ห้ามรบกวน",
        discord.Status.offline: "⚫ ออฟไลน์",
    }
    return statuses.get(member.status, "⚫ ออฟไลน์")


def permission_check(ctx, required_perm: str = "administrator"):
    perms = ctx.author.guild_permissions
    perm_map = {
        "administrator": perms.administrator,
        "manage_guild": perms.manage_guild,
        "manage_channels": perms.manage_channels,
        "manage_roles": perms.manage_roles,
        "kick_members": perms.kick_members,
        "ban_members": perms.ban_members,
        "manage_messages": perms.manage_messages,
        "mute_members": perms.mute_members,
        "mod": (perms.kick_members or perms.ban_members or
                perms.manage_messages or perms.administrator),
        "admin": perms.administrator or perms.manage_guild,
    }
    return perm_map.get(required_perm, False)


def replace_variables(text: str, member: discord.Member = None,
                      guild: discord.Guild = None) -> str:
    if not text:
        return text
    replacements = {}
    if member:
        replacements.update({
            "{ชื่อผู้ใช้}": member.name,
            "{ชื่อเล่น}": member.display_name,
            "{ไอดีผู้ใช้}": str(member.id),
            "{แท็ก}": str(member),
            "{วันที่เข้า}": member.joined_at.strftime("%d/%m/%Y") if member.joined_at else "",
            "{mention}": member.mention,
        })
    if guild:
        replacements.update({
            "{ชื่อเซิร์ฟเวอร์}": guild.name,
            "{จำนวนสมาชิก}": str(guild.member_count),
            "{ไอดีเซิร์ฟเวอร์}": str(guild.id),
        })
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


class Paginator:
    def __init__(self, pages: list, timeout: float = 60):
        self.pages = pages
        self.current = 0
        self.timeout = timeout

    def current_page(self):
        return self.pages[self.current]

    def next(self) -> bool:
        if self.current < len(self.pages) - 1:
            self.current += 1
            return True
        return False

    def prev(self) -> bool:
        if self.current > 0:
            self.current -= 1
            return True
        return False

    def is_first(self) -> bool:
        return self.current == 0

    def is_last(self) -> bool:
        return self.current == len(self.pages) - 1
