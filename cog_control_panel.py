import discord
from discord.ext import commands
from datetime import datetime
import platform
import sys
import database as db
from bot_embeds import success_embed, error_embed, build_dashboard_embed
from bot_helpers import has_admin_perms, has_mod_perms
from config import BOT_VERSION


class ControlPanelView(discord.ui.View):
    def __init__(self, bot, guild, settings, author_id):
        super().__init__(timeout=300)
        self.bot = bot
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

    @discord.ui.button(label="🎵 ระบบเพลง", style=discord.ButtonStyle.primary, row=0)
    async def music_toggle(self, button, interaction):
        await self._toggle(interaction, 'music_enabled', 'ระบบเพลง', '🎵')

    @discord.ui.button(label="🛡️ ความปลอดภัย", style=discord.ButtonStyle.danger, row=0)
    async def security_toggle(self, button, interaction):
        await self._toggle(interaction, 'security_enabled', 'ระบบความปลอดภัย', '🛡️')

    @discord.ui.button(label="👋 ต้อนรับ", style=discord.ButtonStyle.success, row=0)
    async def welcome_toggle(self, button, interaction):
        await self._toggle(interaction, 'welcome_enabled', 'ระบบต้อนรับ', '👋')

    @discord.ui.button(label="📢 ประกาศ", style=discord.ButtonStyle.secondary, row=0)
    async def announce_toggle(self, button, interaction):
        await self._toggle(interaction, 'announce_enabled', 'ระบบประกาศ', '📢')

    @discord.ui.button(label="🧾 ล็อก", style=discord.ButtonStyle.secondary, row=1)
    async def log_toggle(self, button, interaction):
        await self._toggle(interaction, 'log_enabled', 'ระบบล็อก', '🧾')

    @discord.ui.button(label="✅ ยืนยันตัวตน", style=discord.ButtonStyle.success, row=1)
    async def verify_toggle(self, button, interaction):
        await self._toggle(interaction, 'verify_enabled', 'ระบบยืนยัน', '✅')

    @discord.ui.button(label="🎁 รับยศ", style=discord.ButtonStyle.primary, row=1)
    async def roles_toggle(self, button, interaction):
        await self._toggle(interaction, 'selfrole_enabled', 'ระบบรับยศ', '🎁')

    @discord.ui.button(label="⚡ ระบบเลเวล", style=discord.ButtonStyle.primary, row=1)
    async def levels_toggle(self, button, interaction):
        await self._toggle(interaction, 'levels_enabled', 'ระบบเลเวล XP', '⚡')

    @discord.ui.button(label="🛡️ กันสแปม", style=discord.ButtonStyle.danger, row=2)
    async def antispam_toggle(self, button, interaction):
        await self._toggle(interaction, 'antispam_enabled', 'ระบบกันสแปม', '🛡️')

    @discord.ui.button(label="🤬 กรองคำหยาบ", style=discord.ButtonStyle.danger, row=2)
    async def antiswear_toggle(self, button, interaction):
        await self._toggle(interaction, 'antiswear_enabled', 'ระบบกรองคำหยาบ', '🤬')

    @discord.ui.button(label="🔗 กันลิงก์", style=discord.ButtonStyle.danger, row=2)
    async def antilink_toggle(self, button, interaction):
        await self._toggle(interaction, 'antilink_enabled', 'ระบบกันลิงก์', '🔗')

    @discord.ui.button(label="🚨 กัน Raid", style=discord.ButtonStyle.danger, row=2)
    async def antiraid_toggle(self, button, interaction):
        await self._toggle(interaction, 'antiraid_enabled', 'ระบบกัน Raid', '🚨')

    @discord.ui.button(label="🔄 รีเฟรช Dashboard", style=discord.ButtonStyle.success, row=3)
    async def refresh_dashboard(self, button, interaction):
        settings = await db.get_guild_settings(self.guild.id)
        self.settings = settings
        from cog_dashboard import DashboardView
        embed = build_dashboard_embed(self.guild, self.bot, settings)
        view = DashboardView(self.bot, self.guild, settings, interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="💊 สุขภาพระบบ", style=discord.ButtonStyle.secondary, row=3)
    async def system_health(self, button, interaction):
        latency = round(self.bot.latency * 1000)
        lat_label = "🟢 ดีมาก" if latency < 100 else ("🟡 หน่วงนิด" if latency < 300 else "🔴 หน่วงมาก")
        uptime = datetime.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
        uptime_str = str(uptime).split('.')[0] if uptime else "กำลังเริ่ม..."

        embed = discord.Embed(
            title="💊 สุขภาพระบบบอท",
            description="ตรวจสอบสถานะระบบและประสิทธิภาพน้าา 🩺",
            color=0x66BB6A,
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="📶 ดีเลย์", value=f"{lat_label}\n`{latency}ms`", inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="🐍 Python", value=f"`{sys.version.split()[0]}`", inline=True)
        embed.add_field(name="💻 ระบบ", value=f"`{platform.system()} {platform.release()}`", inline=True)
        embed.add_field(name="🤖 เซิร์ฟเวอร์ที่ดูแล", value=f"`{len(self.bot.guilds)}` แห่ง", inline=True)
        embed.add_field(name="📦 เวอร์ชัน", value=f"`v{BOT_VERSION}`", inline=True)

        cogs_status = []
        for cog_name in ["Music", "Welcome", "Verification", "Security", "Moderation",
                         "Announcements", "Channels", "ActivityLog", "ControlPanel", "Levels"]:
            loaded = self.bot.get_cog(cog_name) is not None
            cogs_status.append(f"{'✅' if loaded else '❌'} {cog_name}")
        embed.add_field(name="🧩 Cog Status", value="\n".join(cogs_status[:6]), inline=True)
        embed.add_field(name="\u200b", value="\n".join(cogs_status[6:]), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)


class ControlPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="ควบคุม", description="เปิด Dashboard ควบคุมทุกระบบ")
    async def control_panel(self, ctx):
        if not has_mod_perms(ctx.author):
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์ Mod ขึ้นไปถึงจะเข้าได้ 💡"),
                ephemeral=True,
            )
            return
        settings = await db.get_guild_settings(ctx.guild.id)
        view = ControlPanelView(self.bot, ctx.guild, settings, ctx.author.id)
        systems = [
            ("🎵", "เพลง", settings.get('music_enabled', False)),
            ("🛡️", "ความปลอดภัย", settings.get('security_enabled', False)),
            ("👋", "ต้อนรับ", settings.get('welcome_enabled', False)),
            ("📢", "ประกาศ", settings.get('announce_enabled', False)),
            ("🧾", "ล็อก", settings.get('log_enabled', False)),
            ("✅", "ยืนยัน", settings.get('verify_enabled', False)),
            ("🎁", "รับยศ", settings.get('selfrole_enabled', False)),
            ("⚡", "เลเวล", settings.get('levels_enabled', False)),
            ("🛡️", "กันสแปม", settings.get('antispam_enabled', False)),
            ("🤬", "กรองคำหยาบ", settings.get('antiswear_enabled', False)),
            ("🔗", "กันลิงก์", settings.get('antilink_enabled', False)),
            ("🚨", "กัน Raid", settings.get('antiraid_enabled', False)),
        ]
        embed = discord.Embed(
            title="🎛️ Control Panel — ควบคุมทุกระบบ",
            description="กดปุ่มด้านล่างเพื่อเปิด/ปิดแต่ละระบบได้เลยน้าา 👇✨",
            color=0x5865F2,
        )
        for emoji, name, status in systems:
            embed.add_field(
                name=f"{emoji} {name}",
                value="🟢 เปิด" if status else "🔴 ปิด",
                inline=True,
            )
        embed.set_footer(text=f"v{BOT_VERSION} • กดปุ่มเพื่อเปลี่ยนสถานะได้เลยยย ✅")
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @commands.slash_command(name="ตั้งค่าระบบ", description="เปิดหน้าตั้งค่าระบบทั้งหมด")
    async def settings_cmd(self, ctx):
        await self.control_panel(ctx)


def setup(bot):
    bot.add_cog(ControlPanel(bot))
