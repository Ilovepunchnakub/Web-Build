import discord
from discord.ext import commands
from datetime import datetime
import database as db
from bot_embeds import build_log_embed, success_embed, error_embed
from bot_helpers import has_admin_perms, has_mod_perms


EVENT_COLORS = {
    "message_delete": 0xEF5350,
    "message_edit": 0xFFA726,
    "member_join": 0x66BB6A,
    "member_leave": 0x78909C,
    "ban": 0xB71C1C,
    "kick": 0xEF5350,
    "timeout": 0xFF7043,
    "role_add": 0x42A5F5,
    "role_remove": 0xFFA726,
    "channel_create": 0x66BB6A,
    "channel_delete": 0xEF5350,
    "voice_join": 0x26C6DA,
    "voice_leave": 0x78909C,
    "voice_move": 0x42A5F5,
    "verify_success": 0x66BB6A,
}

EVENT_ICONS = {
    "message_delete": "🗑️",
    "message_edit": "✏️",
    "member_join": "✅",
    "member_leave": "🚪",
    "ban": "🔨",
    "kick": "👟",
    "timeout": "⏰",
    "role_add": "➕",
    "role_remove": "➖",
    "channel_create": "🏗️",
    "channel_delete": "🗑️",
    "voice_join": "🎙️",
    "voice_leave": "🔇",
    "voice_move": "🔀",
    "verify_success": "✅",
}

EVENT_LABELS = {
    "message_delete": "ข้อความถูกลบ",
    "message_edit": "ข้อความถูกแก้",
    "member_join": "สมาชิกเข้าร่วม",
    "member_leave": "สมาชิกออก",
    "ban": "แบนสมาชิก",
    "kick": "เตะสมาชิก",
    "timeout": "มิวท์สมาชิก",
    "role_add": "เพิ่มยศ",
    "role_remove": "ลบยศ",
    "channel_create": "สร้างห้อง",
    "channel_delete": "ลบห้อง",
    "voice_join": "เข้าห้องเสียง",
    "voice_leave": "ออกห้องเสียง",
    "voice_move": "ย้ายห้องเสียง",
    "verify_success": "ยืนยันตัวตน",
}


class LogSettingsView(discord.ui.View):
    def __init__(self, guild, settings, author_id):
        super().__init__(timeout=300)
        self.guild = guild
        self.settings = settings
        self.author_id = author_id

    async def interaction_check(self, interaction):
        return interaction.user.id == self.author_id or has_mod_perms(interaction.user)

    async def _toggle(self, interaction, key, label, emoji):
        current = self.settings.get(key, False)
        new_val = not current
        self.settings[key] = new_val
        await db.update_guild_settings(self.guild.id, key, new_val)
        status = "เปิดแล้วน้าา 🟢✨" if new_val else "ปิดแล้วน้าา 🔴"
        await interaction.response.send_message(
            embed=success_embed(f"{emoji} {label} {status}", "เปลี่ยนสถานะเรียบร้อยยย ✅"),
            ephemeral=True,
        )

    @discord.ui.button(label="✅ เปิด/ปิดระบบล็อก", style=discord.ButtonStyle.success, row=0)
    async def toggle_log(self, button, interaction):
        await self._toggle(interaction, "log_enabled", "ระบบล็อก", "🧾")

    @discord.ui.button(label="📍 ตั้งห้องบันทึก", style=discord.ButtonStyle.primary, row=0)
    async def set_log_channel(self, button, interaction):
        from cog_welcome import ChannelSelectView
        view = ChannelSelectView(self.guild, self.settings, self.author_id, "log_channel", "บันทึกเหตุการณ์")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="📍 เลือกห้องบันทึกล็อก",
                description="เลือกห้องที่จะส่งข้อความบันทึกเหตุการณ์ทั้งหมด 👇",
                color=0x42A5F5,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="⚙️ หมวดที่บันทึก", style=discord.ButtonStyle.secondary, row=0)
    async def log_categories(self, button, interaction):
        view = LogCategoryView(self.guild, self.settings, interaction.user.id)
        embed = discord.Embed(
            title="⚙️ เลือกหมวดที่ต้องการบันทึก",
            description="กดเปิด/ปิดแต่ละหมวดได้เลยน้าา 👇\nเปิดแค่ที่ต้องการเพื่อประหยัดพื้นที่ ✨",
            color=0x42A5F5,
        )
        cats = [
            ("💬 ข้อความ", "log_messages", self.settings.get("log_messages", False)),
            ("👤 สมาชิก", "log_members", self.settings.get("log_members", False)),
            ("🏗️ ห้อง", "log_channels", self.settings.get("log_channels", False)),
            ("🧩 ยศ", "log_roles", self.settings.get("log_roles", False)),
            ("🔨 ลงโทษ", "log_mod", self.settings.get("log_mod", False)),
            ("🎙️ เสียง", "log_voice", self.settings.get("log_voice", False)),
        ]
        for name, key, val in cats:
            embed.add_field(name=name, value="🟢 เปิด" if val else "🔴 ปิด", inline=True)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🔍 โหมดละเอียด", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_detailed(self, button, interaction):
        await self._toggle(interaction, "log_detailed", "โหมดละเอียด", "🔍")

    @discord.ui.button(label="📊 ดูล็อกล่าสุด", style=discord.ButtonStyle.primary, row=1)
    async def view_recent_logs(self, button, interaction):
        logs = await db.get_recent_logs(self.guild.id, limit=8)
        embed = discord.Embed(
            title="📊 เหตุการณ์ล่าสุด",
            description="8 เหตุการณ์ล่าสุดในเซิร์ฟเวอร์น้าา 🔍",
            color=0x42A5F5,
        )
        if not logs:
            embed.description = "ยังไม่มีบันทึกล็อกน้าา~\nเปิดระบบล็อกก่อนแล้วมาดูใหม่ 💡"
        else:
            lines = []
            for event_type, user_id, desc, created_at in logs[:8]:
                icon = EVENT_ICONS.get(event_type, "📋")
                label = EVENT_LABELS.get(event_type, event_type)
                member = self.guild.get_member(user_id)
                name = member.display_name if member else f"ID:{user_id}"
                lines.append(f"{icon} **{label}** — {name}")
            embed.description = "\n".join(lines)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="♻️ รีเซ็ต", style=discord.ButtonStyle.danger, row=1)
    async def reset_log(self, button, interaction):
        for key in ["log_enabled", "log_channel", "log_messages", "log_members",
                    "log_channels", "log_roles", "log_mod", "log_voice", "log_detailed"]:
            self.settings.pop(key, None)
        await db.set_guild_settings(self.guild.id, self.settings)
        await interaction.response.send_message(
            embed=success_embed("รีเซ็ตแล้วน้าา ✨", "ค่าระบบล็อกถูกรีเซ็ตเรียบร้อยยย"),
            ephemeral=True,
        )


class LogCategoryView(discord.ui.View):
    def __init__(self, guild, settings, author_id):
        super().__init__(timeout=120)
        self.guild = guild
        self.settings = settings
        self.author_id = author_id

    async def _toggle(self, interaction, key, label):
        current = self.settings.get(key, False)
        new_val = not current
        self.settings[key] = new_val
        await db.update_guild_settings(self.guild.id, key, new_val)
        status = "เปิดแล้วน้าา 🟢✨" if new_val else "ปิดแล้วน้าา 🔴"
        await interaction.response.send_message(
            embed=success_embed(f"ล็อก{label} {status}", ""),
            ephemeral=True,
        )

    @discord.ui.button(label="💬 ข้อความ", style=discord.ButtonStyle.secondary, row=0)
    async def tog_msg(self, b, i): await self._toggle(i, "log_messages", "ข้อความ")

    @discord.ui.button(label="👤 สมาชิก", style=discord.ButtonStyle.secondary, row=0)
    async def tog_mem(self, b, i): await self._toggle(i, "log_members", "สมาชิก")

    @discord.ui.button(label="🏗️ ห้อง", style=discord.ButtonStyle.secondary, row=0)
    async def tog_ch(self, b, i): await self._toggle(i, "log_channels", "ห้อง")

    @discord.ui.button(label="🧩 ยศ", style=discord.ButtonStyle.secondary, row=1)
    async def tog_roles(self, b, i): await self._toggle(i, "log_roles", "ยศ")

    @discord.ui.button(label="🔨 ลงโทษ", style=discord.ButtonStyle.secondary, row=1)
    async def tog_mod(self, b, i): await self._toggle(i, "log_mod", "ลงโทษ")

    @discord.ui.button(label="🎙️ เสียง", style=discord.ButtonStyle.secondary, row=1)
    async def tog_voice(self, b, i): await self._toggle(i, "log_voice", "เสียง")


class ActivityLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, guild: discord.Guild, event_type: str, embed: discord.Embed):
        settings = await db.get_guild_settings(guild.id)
        if not settings.get("log_enabled"):
            return
        log_ch_id = settings.get("log_channel")
        if not log_ch_id:
            return
        channel = guild.get_channel(log_ch_id)
        if not channel:
            return
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    def make_log_embed(self, event_type: str, title: str, description: str = "", **fields) -> discord.Embed:
        icon = EVENT_ICONS.get(event_type, "📋")
        color = EVENT_COLORS.get(event_type, 0x42A5F5)
        embed = discord.Embed(
            title=f"{icon} {title}",
            description=description,
            color=color,
            timestamp=datetime.utcnow(),
        )
        for name, value in fields.items():
            embed.add_field(name=name, value=str(value)[:1024], inline=True)
        embed.set_footer(text="📋 ระบบบันทึกกิจกรรม")
        return embed

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        settings = await db.get_guild_settings(message.guild.id)
        if not settings.get("log_enabled") or not settings.get("log_messages"):
            return
        embed = self.make_log_embed(
            "message_delete",
            "ข้อความถูกลบน้าา",
            f"ข้อความในห้อง {message.channel.mention} ถูกลบแล้ว",
        )
        embed.add_field(name="👤 ผู้ส่ง", value=message.author.mention, inline=True)
        embed.add_field(name="📍 ห้อง", value=message.channel.mention, inline=True)
        content = message.content[:800] if message.content else "*ไม่มีข้อความ (อาจเป็นรูป/ไฟล์)*"
        embed.add_field(name="📝 ข้อความ", value=f"```{content}```", inline=False)
        if message.author.display_avatar:
            embed.set_thumbnail(url=message.author.display_avatar.url)
        await self.send_log(message.guild, "message_delete", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or before.author.bot or before.content == after.content:
            return
        settings = await db.get_guild_settings(before.guild.id)
        if not settings.get("log_enabled") or not settings.get("log_messages"):
            return
        embed = self.make_log_embed(
            "message_edit",
            "ข้อความถูกแก้ไข",
            f"ข้อความในห้อง {before.channel.mention} ถูกแก้ไข",
        )
        embed.add_field(name="👤 ผู้ส่ง", value=before.author.mention, inline=True)
        embed.add_field(name="📍 ห้อง", value=before.channel.mention, inline=True)
        embed.add_field(name="🔗 ดูข้อความ", value=f"[คลิกที่นี่]({after.jump_url})", inline=True)
        embed.add_field(name="📝 ก่อนแก้", value=f"```{before.content[:400]}```", inline=False)
        embed.add_field(name="📝 หลังแก้", value=f"```{after.content[:400]}```", inline=False)
        if before.author.display_avatar:
            embed.set_thumbnail(url=before.author.display_avatar.url)
        await self.send_log(before.guild, "message_edit", embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = await db.get_guild_settings(member.guild.id)
        if not settings.get("log_enabled") or not settings.get("log_members"):
            return
        account_age = (datetime.utcnow() - member.created_at.replace(tzinfo=None)).days
        new_account_warning = "⚠️ **บัญชีใหม่มาก!**\n" if account_age < 7 else ""
        embed = self.make_log_embed(
            "member_join",
            f"สมาชิกใหม่เข้าร่วมน้าา",
            f"{new_account_warning}{member.mention} เข้าร่วมเซิร์ฟเวอร์แล้วยย",
        )
        embed.add_field(name="👤 สมาชิก", value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="📅 อายุบัญชี", value=f"{account_age} วัน", inline=True)
        embed.add_field(name="👥 สมาชิกลำดับที่", value=f"#{member.guild.member_count}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(member.guild, "member_join", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        settings = await db.get_guild_settings(member.guild.id)
        if not settings.get("log_enabled") or not settings.get("log_members"):
            return
        roles = [r.mention for r in member.roles if r.name != "@everyone"][:5]
        embed = self.make_log_embed(
            "member_leave",
            f"สมาชิกออกจากเซิร์ฟเวอร์",
            f"{member} ออกไปแล้วน้าา",
        )
        embed.add_field(name="👤 สมาชิก", value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="🧩 ยศที่มี", value=", ".join(roles) if roles else "ไม่มียศ", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(member.guild, "member_leave", embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        settings = await db.get_guild_settings(guild.id)
        if not settings.get("log_enabled") or not settings.get("log_mod"):
            return
        embed = self.make_log_embed(
            "ban",
            f"แบนสมาชิก 🔨",
            f"{user.mention} ถูกแบนออกจากเซิร์ฟเวอร์",
        )
        embed.add_field(name="👤 สมาชิก", value=f"{user} ({user.id})", inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        await self.send_log(guild, "ban", embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        settings = await db.get_guild_settings(member.guild.id)
        if not settings.get("log_enabled") or not settings.get("log_voice"):
            return
        if before.channel is None and after.channel is not None:
            embed = self.make_log_embed(
                "voice_join",
                "เข้าห้องเสียงน้าา 🎙️",
                f"{member.mention} เข้าห้อง **{after.channel.name}**",
            )
            embed.add_field(name="👤 สมาชิก", value=member.mention, inline=True)
            embed.add_field(name="🎙️ ห้อง", value=after.channel.name, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_log(member.guild, "voice_join", embed)
        elif before.channel is not None and after.channel is None:
            embed = self.make_log_embed(
                "voice_leave",
                "ออกห้องเสียงแล้ว 🔇",
                f"{member.mention} ออกจากห้อง **{before.channel.name}**",
            )
            embed.add_field(name="👤 สมาชิก", value=member.mention, inline=True)
            embed.add_field(name="🔇 ห้องที่ออก", value=before.channel.name, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_log(member.guild, "voice_leave", embed)
        elif before.channel != after.channel and before.channel and after.channel:
            embed = self.make_log_embed(
                "voice_move",
                "ย้ายห้องเสียงน้าา 🔀",
                f"{member.mention} ย้ายจาก **{before.channel.name}** ไป **{after.channel.name}**",
            )
            embed.add_field(name="👤 สมาชิก", value=member.mention, inline=True)
            embed.add_field(name="⬅️ ห้องเดิม", value=before.channel.name, inline=True)
            embed.add_field(name="➡️ ห้องใหม่", value=after.channel.name, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_log(member.guild, "voice_move", embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        settings = await db.get_guild_settings(channel.guild.id)
        if not settings.get("log_enabled") or not settings.get("log_channels"):
            return
        embed = self.make_log_embed(
            "channel_create",
            "สร้างห้องใหม่น้าา 🏗️",
            f"ห้อง {channel.mention} ถูกสร้างขึ้นแล้วยย",
        )
        embed.add_field(name="📋 ชื่อ", value=channel.name, inline=True)
        embed.add_field(name="📦 ประเภท", value=str(channel.type).split(".")[1], inline=True)
        await self.send_log(channel.guild, "channel_create", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        settings = await db.get_guild_settings(channel.guild.id)
        if not settings.get("log_enabled") or not settings.get("log_channels"):
            return
        embed = self.make_log_embed(
            "channel_delete",
            "ลบห้องแล้วน้าา 🗑️",
            f"ห้อง **#{channel.name}** ถูกลบออกไปแล้ว",
        )
        embed.add_field(name="📋 ชื่อ", value=channel.name, inline=True)
        embed.add_field(name="📍 ประเภท", value=str(channel.type).split(".")[1], inline=True)
        await self.send_log(channel.guild, "channel_delete", embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        settings = await db.get_guild_settings(before.guild.id)
        if not settings.get("log_enabled") or not settings.get("log_roles"):
            return
        added = [r for r in after.roles if r not in before.roles]
        removed = [r for r in before.roles if r not in after.roles]
        if added:
            embed = self.make_log_embed(
                "role_add",
                "เพิ่มยศ ➕",
                f"{after.mention} ได้รับยศใหม่น้าา",
            )
            embed.add_field(name="👤 สมาชิก", value=after.mention, inline=True)
            embed.add_field(name="🧩 ยศที่ได้", value=", ".join(r.mention for r in added), inline=True)
            embed.set_thumbnail(url=after.display_avatar.url)
            await self.send_log(before.guild, "role_add", embed)
        if removed:
            embed = self.make_log_embed(
                "role_remove",
                "ถอดยศ ➖",
                f"{after.mention} ถูกถอดยศออกน้าา",
            )
            embed.add_field(name="👤 สมาชิก", value=after.mention, inline=True)
            embed.add_field(name="🧩 ยศที่ถูกถอด", value=", ".join(r.mention for r in removed), inline=True)
            embed.set_thumbnail(url=after.display_avatar.url)
            await self.send_log(before.guild, "role_remove", embed)

    @commands.slash_command(name="ล็อก", description="เปิดศูนย์ตั้งค่าระบบบันทึกกิจกรรม")
    async def log_panel(self, ctx):
        if not has_mod_perms(ctx.author):
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์ Mod ขึ้นไปถึงจะตั้งค่าได้ 💡"),
                ephemeral=True,
            )
            return
        settings = await db.get_guild_settings(ctx.guild.id)
        embed = build_log_embed(settings)
        view = LogSettingsView(ctx.guild, settings, ctx.author.id)
        await ctx.respond(embed=embed, view=view)


def setup(bot):
    bot.add_cog(ActivityLog(bot))
