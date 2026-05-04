import discord
from discord.ext import commands
from discord import SlashCommandGroup
import database as db
from bot_embeds import build_dashboard_embed, success_embed, error_embed
from bot_helpers import has_admin_perms, has_mod_perms
from datetime import datetime
import math


class DashboardView(discord.ui.View):
    def __init__(self, bot, guild, settings, author_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild = guild
        self.settings = settings
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id or has_mod_perms(interaction.user)

    @discord.ui.button(label="⚙️ ตั้งค่าระบบ", style=discord.ButtonStyle.primary, row=0)
    async def settings_btn(self, button, interaction):
        from cog_control_panel import ControlPanelView
        view = ControlPanelView(self.bot, self.guild, self.settings, interaction.user.id)
        systems = [
            ("👋", "ต้อนรับ", "welcome_enabled"),
            ("✅", "ยืนยันตัวตน", "verify_enabled"),
            ("🎁", "รับยศ", "selfrole_enabled"),
            ("🧾", "ล็อกกิจกรรม", "log_enabled"),
            ("📢", "ประกาศ", "announce_enabled"),
            ("🎵", "เพลง", "music_enabled"),
            ("🛡️", "กันสแปม", "antispam_enabled"),
            ("⚡", "เลเวล XP", "levels_enabled"),
        ]
        embed = discord.Embed(
            title="⚙️ ปรับแต่งระบบทั้งหมด",
            description="กดปุ่มด้านล่างเพื่อเปิด/ปิดแต่ละระบบได้เลยน้าา 👇",
            color=0x5865F2,
        )
        for emoji, name, key in systems:
            status = "🟢 เปิด" if self.settings.get(key, False) else "🔴 ปิด"
            embed.add_field(name=f"{emoji} {name}", value=status, inline=True)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🛡️ ความปลอดภัย", style=discord.ButtonStyle.danger, row=0)
    async def security_btn(self, button, interaction):
        from cog_security import SecurityView
        from bot_embeds import build_security_embed
        view = SecurityView(self.guild, self.settings, interaction.user.id)
        embed = build_security_embed(self.settings)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="👮 จัดการสมาชิก", style=discord.ButtonStyle.secondary, row=0)
    async def moderation_btn(self, button, interaction):
        from bot_embeds import build_mod_embed
        embed = build_mod_embed()
        embed.add_field(
            name="⚡ คำสั่งที่ใช้ได้เลย",
            value=(
                "• `/เตะ @สมาชิก` — เตะออก 👢\n"
                "• `/แบน @สมาชิก` — แบนถาวร ⛔\n"
                "• `/มิวท์ @สมาชิก` — เงียบชั่วคราว 🔇\n"
                "• `/เตือน @สมาชิก` — ส่งคำเตือน ⚠️\n"
                "• `/ดูประวัติ @สมาชิก` — ดูประวัติ 📋\n"
                "• `/จัดการสมาชิก @สมาชิก` — หน้าจัดการ 🎛️\n"
                "• `/ล้างแชท [จำนวน]` — ล้างข้อความ 🧹"
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🎵 ระบบเพลง", style=discord.ButtonStyle.success, row=0)
    async def music_btn(self, button, interaction):
        from cog_music import MusicControlView
        from bot_embeds import build_music_embed
        music_cog = self.bot.get_cog("Music")
        guild_player = music_cog.players.get(self.guild.id) if music_cog else None
        current = guild_player.current_track if guild_player else None
        embed = build_music_embed(self.guild, self.settings, current.to_dict() if current else None)
        view = MusicControlView(self.bot, self.guild, self.settings, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="⚡ เลเวลและ XP", style=discord.ButtonStyle.primary, row=1)
    async def levels_btn(self, button, interaction):
        rows = await db.get_levels_leaderboard(self.guild.id, limit=3)
        data = await db.get_user_level(self.guild.id, interaction.user.id)
        xp = data.get('xp', 0) if data else 0
        from cog_levels import calc_level, level_progress, xp_bar

        level, cur_xp, need_xp = level_progress(xp)
        bar = xp_bar(cur_xp, need_xp, 10)

        embed = discord.Embed(
            title="⚡ ระบบเลเวลและ XP",
            description=(
                "ยิ่งแชทเยอะ ยิ่งได้ XP เยอะ ยิ่งเลเวลสูง ✨\n"
                "แข่งกันในอันดับ Leaderboard ได้เลยน้าา 💪"
            ),
            color=0xFFD700,
        )
        embed.add_field(
            name="👤 สถานะของคุณ",
            value=(
                f"⚡ **เลเวล:** {level}\n"
                f"✨ **XP:** {xp:,} XP\n"
                f"`{bar}` {cur_xp}/{need_xp} XP"
            ),
            inline=True,
        )
        embed.add_field(
            name="⚙️ สถานะระบบ",
            value=(
                f"✅ ระบบเลเวล: {'🟢 เปิด' if self.settings.get('levels_enabled') else '🔴 ปิด'}\n"
                f"📢 แจ้ง Level Up: {'🟢 เปิด' if self.settings.get('levelup_announce', True) else '🔴 ปิด'}"
            ),
            inline=True,
        )
        if rows:
            top_lines = []
            medals = ["🥇", "🥈", "🥉"]
            for i, (uid, user_xp, lvl, msgs) in enumerate(rows[:3]):
                m = self.guild.get_member(uid)
                name = m.display_name if m else f"User {uid}"
                top_lines.append(f"{medals[i]} **{name}** — {user_xp:,} XP")
            embed.add_field(name="🏆 Top 3 อันดับ", value="\n".join(top_lines), inline=False)

        embed.set_footer(text="ใช้ /rank เพื่อดูอันดับตัวเอง • /leaderboard เพื่อดูทั้งหมด ✅")
        view = LevelDashView(self.guild, self.settings, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="📢 ประกาศ", style=discord.ButtonStyle.primary, row=1)
    async def announce_btn(self, button, interaction):
        from cog_announcements import AnnouncementView
        from bot_embeds import build_announce_embed
        embed = build_announce_embed(self.settings)
        view = AnnouncementView(self.guild, self.settings, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="✅ ยืนยันตัวตน", style=discord.ButtonStyle.success, row=1)
    async def verify_btn(self, button, interaction):
        from cog_verification import VerifySetupView
        from bot_embeds import build_verify_embed
        embed = build_verify_embed(self.settings)
        view = VerifySetupView(self.guild, self.settings, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🎁 รับยศ", style=discord.ButtonStyle.secondary, row=1)
    async def roles_btn(self, button, interaction):
        from cog_verification import RoleMenuView
        from bot_embeds import build_roles_embed
        embed = build_roles_embed(self.guild, self.settings)
        view = RoleMenuView(self.guild, self.settings, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🧾 ล็อกกิจกรรม", style=discord.ButtonStyle.secondary, row=1)
    async def log_btn(self, button, interaction):
        from cog_activity_log import LogSettingsView
        from bot_embeds import build_log_embed
        embed = build_log_embed(self.settings)
        view = LogSettingsView(self.guild, self.settings, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="📊 สถิติเซิร์ฟเวอร์", style=discord.ButtonStyle.secondary, row=2)
    async def stats_btn(self, button, interaction):
        guild = self.guild
        online = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
        bots_count = sum(1 for m in guild.members if m.bot)
        text_chs = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_chs = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])

        latency = round(self.bot.latency * 1000)
        lat_label = "🟢 ดีมาก" if latency < 100 else ("🟡 หน่วงนิดนึง" if latency < 300 else "🔴 หน่วงมาก")
        uptime = datetime.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
        uptime_str = str(uptime).split('.')[0] if uptime else "กำลังเริ่ม..."
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count or 0

        embed = discord.Embed(
            title="📊 สถิติเซิร์ฟเวอร์แบบ Real-time",
            description="ข้อมูลอัปเดตทุกครั้งที่กด รีเฟรช น้าา ✅",
            color=0x42A5F5,
        )
        embed.add_field(name="👥 สมาชิกทั้งหมด", value=f"{guild.member_count:,} คน", inline=True)
        embed.add_field(name="🟢 ออนไลน์", value=f"{online:,} คน", inline=True)
        embed.add_field(name="🤖 บอท", value=f"{bots_count} ตัว", inline=True)
        embed.add_field(name="💬 ห้องข้อความ", value=f"{text_chs} ห้อง", inline=True)
        embed.add_field(name="🎙️ ห้องเสียง", value=f"{voice_chs} ห้อง", inline=True)
        embed.add_field(name="🧩 ยศ", value=f"{len(guild.roles)} ยศ", inline=True)
        embed.add_field(name="📶 สัญญาณบอท", value=f"{lat_label} ({latency}ms)", inline=True)
        embed.add_field(name="⏱️ ทำงานมาแล้ว", value=uptime_str, inline=True)
        embed.add_field(name="💎 Server Boost", value=f"Lv.{boost_level} ({boost_count} บูสต์)", inline=True)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.timestamp = datetime.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="💾 สำรองข้อมูล", style=discord.ButtonStyle.secondary, row=2)
    async def backup_btn(self, button, interaction):
        embed = discord.Embed(
            title="💾 ระบบสำรองข้อมูล",
            description="ข้อมูลของคุณปลอดภัยน้าา 🔐 ทุกอย่างเก็บในฐานข้อมูลอัตโนมัติ ✨",
            color=0x78909C,
        )
        embed.add_field(
            name="✅ สิ่งที่สำรองอัตโนมัติ",
            value=(
                "• ✅ การตั้งค่าทุกระบบ\n"
                "• ✅ ยศและสิทธิ์อัตโนมัติ\n"
                "• ✅ คำห้ามและโดเมนที่บล็อก\n"
                "• ✅ ประกาศที่บันทึกไว้\n"
                "• ✅ ข้อมูล XP และเลเวล\n"
                "• ✅ ประวัติการจัดการสมาชิก"
            ),
            inline=True,
        )
        embed.add_field(
            name="💡 วิธีกู้คืน",
            value=(
                "ข้อมูลทั้งหมดเก็บใน SQLite อัตโนมัติ\n"
                "หากต้องการ Export — ติดต่อแอดมินระบบได้เลยน้าา 💪"
            ),
            inline=True,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔄 รีเฟรช", style=discord.ButtonStyle.success, row=2)
    async def refresh_btn(self, button, interaction):
        settings = await db.get_guild_settings(interaction.guild.id)
        self.settings = settings
        embed = build_dashboard_embed(interaction.guild, self.bot, settings)
        view = DashboardView(self.bot, interaction.guild, settings, interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🛠️ โหมดแอดมิน", style=discord.ButtonStyle.danger, row=2)
    async def admin_btn(self, button, interaction):
        if not has_admin_perms(interaction.user):
            await interaction.response.send_message(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์แอดมินถึงจะเข้าได้ 💡"),
                ephemeral=True,
            )
            return
        embed = discord.Embed(
            title="🛠️ โหมดแอดมิน",
            description="เครื่องมือพิเศษสำหรับแอดมินเท่านั้น 🔐\nใช้ด้วยความรอบคอบนะา 🥺",
            color=0xEF5350,
        )
        embed.add_field(
            name="⚡ คำสั่งด่วน",
            value=(
                "• `/ล็อกเซิร์ฟเวอร์` — ล็อกทุกห้อง 🔒\n"
                "• `/ปลดล็อกเซิร์ฟเวอร์` — เปิดทุกห้อง 🔓\n"
                "• `/โหมดฉุกเฉิน` — เปิดโหมดฉุกเฉิน 🚨\n"
                "• `/ประกาศด่วน` — ส่งประกาศทันที 📢\n"
                "• `/ล้างแชท [จำนวน]` — ล้างข้อความ 🧹\n"
                "• `/รีเซ็ตxp @สมาชิก` — รีเซ็ต XP ⚡"
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class LevelDashView(discord.ui.View):
    def __init__(self, guild, settings, author_id):
        super().__init__(timeout=120)
        self.guild = guild
        self.settings = settings
        self.author_id = author_id

    @discord.ui.button(label="🏆 ดู Leaderboard", style=discord.ButtonStyle.primary)
    async def leaderboard_btn(self, button, interaction):
        from cog_levels import LeaderboardView
        rows = await db.get_levels_leaderboard(self.guild.id)
        if not rows:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="📊 ยังไม่มีข้อมูลน้าา",
                    description="แชทก่อนแล้วมาดูใหม่นะา 💬✨",
                    color=0xFFD700,
                ),
                ephemeral=True,
            )
            return
        view = LeaderboardView(interaction.client, self.guild, rows, author_id=interaction.user.id)
        await interaction.response.send_message(embed=view.get_page_embed(), view=view, ephemeral=True)

    @discord.ui.button(label="👤 อันดับฉัน", style=discord.ButtonStyle.secondary)
    async def my_rank(self, button, interaction):
        from cog_levels import calc_level, level_progress, xp_bar
        data = await db.get_user_level(self.guild.id, interaction.user.id)
        xp = data.get('xp', 0) if data else 0
        messages = data.get('messages', 0) if data else 0
        level, cur_xp, need_xp = level_progress(xp)
        bar = xp_bar(cur_xp, need_xp, 12)
        embed = discord.Embed(
            title=f"⚡ อันดับของ {interaction.user.display_name}",
            color=0xFFD700,
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="🎯 เลเวล", value=f"**{level}**", inline=True)
        embed.add_field(name="✨ XP รวม", value=f"**{xp:,}**", inline=True)
        embed.add_field(name="💬 ข้อความ", value=f"**{messages:,}**", inline=True)
        embed.add_field(name="📊 ความก้าวหน้า", value=f"`{bar}`\n{cur_xp}/{need_xp} XP", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="หน้าแรก", description="เปิดแผงควบคุมหลักของเซิร์ฟเวอร์")
    async def dashboard(self, ctx):
        settings = await db.get_guild_settings(ctx.guild.id)
        embed = build_dashboard_embed(ctx.guild, self.bot, settings)
        view = DashboardView(self.bot, ctx.guild, settings, ctx.author.id)
        await ctx.respond(embed=embed, view=view)

    @commands.slash_command(name="สถิติ", description="ดูสถิติเซิร์ฟเวอร์แบบละเอียด")
    async def server_stats(self, ctx):
        guild = ctx.guild
        online = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
        latency = round(self.bot.latency * 1000)
        lat_label = "🟢" if latency < 100 else ("🟡" if latency < 300 else "🔴")
        uptime = datetime.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
        uptime_str = str(uptime).split('.')[0] if uptime else "กำลังเริ่ม..."

        embed = discord.Embed(
            title=f"📊 สถิติ {guild.name}",
            color=0x42A5F5,
            timestamp=datetime.utcnow(),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="👥 สมาชิกทั้งหมด", value=f"{guild.member_count:,}", inline=True)
        embed.add_field(name="🟢 ออนไลน์", value=f"{online:,}", inline=True)
        embed.add_field(name="🤖 บอท", value=f"{sum(1 for m in guild.members if m.bot)}", inline=True)
        embed.add_field(name="💬 ห้องข้อความ", value=f"{len([c for c in guild.channels if isinstance(c, discord.TextChannel)])}", inline=True)
        embed.add_field(name="🎙️ ห้องเสียง", value=f"{len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])}", inline=True)
        embed.add_field(name="🧩 ยศ", value=f"{len(guild.roles)}", inline=True)
        embed.add_field(name=f"{lat_label} ดีเลย์", value=f"{latency}ms", inline=True)
        embed.add_field(name="⏱️ Uptime", value=uptime_str, inline=True)
        embed.add_field(name="💎 Boost", value=f"Lv.{guild.premium_tier} ({guild.premium_subscription_count or 0} บูสต์)", inline=True)
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Dashboard(bot))
