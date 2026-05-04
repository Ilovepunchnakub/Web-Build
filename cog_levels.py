import discord
from discord.ext import commands
import database as db
import math
import random
from datetime import datetime
from bot_embeds import success_embed, error_embed
from bot_helpers import has_admin_perms, has_mod_perms


LEVEL_COLOR = 0xFFD700
XP_COOLDOWN = 60
XP_MIN = 5
XP_MAX = 15


def calc_level(xp: int) -> int:
    if xp <= 0:
        return 0
    return int(0.1 * math.sqrt(xp))


def xp_for_level(level: int) -> int:
    return int((level / 0.1) ** 2)


def level_progress(xp: int) -> tuple[int, int, int]:
    level = calc_level(xp)
    current_level_xp = xp_for_level(level)
    next_level_xp = xp_for_level(level + 1)
    progress_xp = xp - current_level_xp
    needed_xp = next_level_xp - current_level_xp
    return level, progress_xp, needed_xp


def xp_bar(current: int, total: int, length: int = 12) -> str:
    if total <= 0:
        return "▱" * length
    pct = min(current / total, 1.0)
    filled = int(pct * length)
    bar = "█" * filled + "░" * (length - filled)
    return bar


def level_emoji(level: int) -> str:
    if level >= 50:
        return "👑"
    elif level >= 30:
        return "💎"
    elif level >= 20:
        return "🏆"
    elif level >= 10:
        return "⭐"
    elif level >= 5:
        return "🌟"
    else:
        return "⚡"


class LeaderboardView(discord.ui.View):
    def __init__(self, bot, guild, all_rows, author_id, page=0):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild = guild
        self.all_rows = all_rows
        self.author_id = author_id
        self.page = page
        self.per_page = 10

    def get_page_embed(self) -> discord.Embed:
        total = len(self.all_rows)
        total_pages = max(1, -(-total // self.per_page))
        start = self.page * self.per_page
        end = start + self.per_page
        rows = self.all_rows[start:end]

        embed = discord.Embed(
            title=f"🏆 Leaderboard — {self.guild.name}",
            description="อันดับ XP สูงสุดในเซิร์ฟเวอร์น้าา 💪✨",
            color=LEVEL_COLOR,
        )

        if self.guild.icon:
            embed.set_thumbnail(url=self.guild.icon.url)

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, (user_id, user_xp, lvl, msgs) in enumerate(rows, start + 1):
            member = self.guild.get_member(user_id)
            name = member.display_name if member else f"User {user_id}"
            rank_icon = medals.get(i, f"`{i:>3}.`")
            emoji = level_emoji(lvl)
            progress = level_progress(user_xp)
            bar = xp_bar(progress[1], progress[2], 8)
            lines.append(
                f"{rank_icon} **{name}**\n"
                f"     {emoji} Lv.**{lvl}** • ✨ {user_xp:,} XP • 💬 {msgs:,} msg\n"
                f"     `{bar}` {progress[1]}/{progress[2]} XP"
            )

        embed.description = "\n".join(lines) if lines else "ยังไม่มีข้อมูลน้าา~\nแชทก่อนแล้วมาดูใหม่นะา 💡"
        embed.set_footer(text=f"หน้า {self.page + 1}/{total_pages} • {total} สมาชิกทั้งหมด • แชทเยอะ XP เยอะน้าา ✅")
        embed.timestamp = datetime.utcnow()
        return embed

    @discord.ui.button(label="⬅️ ก่อนหน้า", style=discord.ButtonStyle.secondary)
    async def prev_page(self, button, interaction):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)

    @discord.ui.button(label="➡️ ถัดไป", style=discord.ButtonStyle.secondary)
    async def next_page(self, button, interaction):
        total_pages = max(1, -(-len(self.all_rows) // self.per_page))
        if self.page < total_pages - 1:
            self.page += 1
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)

    @discord.ui.button(label="🔄 รีเฟรช", style=discord.ButtonStyle.success)
    async def refresh(self, button, interaction):
        rows = await db.get_levels_leaderboard(self.guild.id)
        self.all_rows = rows
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)

    @discord.ui.button(label="👤 โปรไฟล์ฉัน", style=discord.ButtonStyle.primary)
    async def my_profile(self, button, interaction):
        levels_cog = interaction.client.get_cog("Levels")
        if levels_cog:
            embed = await levels_cog.build_profile_embed(interaction.user, self.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                embed=error_embed("โหลดระบบไม่ได้น้าา 😅", "ลองใหม่อีกทีน้าา 💡"),
                ephemeral=True,
            )


class LevelSettingsView(discord.ui.View):
    def __init__(self, guild, settings, author_id):
        super().__init__(timeout=300)
        self.guild = guild
        self.settings = settings
        self.author_id = author_id

    async def interaction_check(self, interaction):
        return interaction.user.id == self.author_id or has_mod_perms(interaction.user)

    @discord.ui.button(label="✅ เปิด/ปิดระบบเลเวล", style=discord.ButtonStyle.success, row=0)
    async def toggle_levels(self, button, interaction):
        current = self.settings.get("levels_enabled", False)
        new_val = not current
        await db.update_guild_settings(self.guild.id, "levels_enabled", new_val)
        self.settings["levels_enabled"] = new_val
        status = "เปิดแล้วน้าา 🟢✨" if new_val else "ปิดแล้วน้าา 🔴"
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"⚡ ระบบเลเวล {status}",
                description="เปลี่ยนสถานะเรียบร้อยยย ✅",
                color=0x66BB6A if new_val else 0xEF5350,
            ),
            ephemeral=True,
        )

    @discord.ui.button(label="🔔 ห้องแจ้งเตือน Level Up", style=discord.ButtonStyle.primary, row=0)
    async def set_levelup_channel(self, button, interaction):
        modal = LevelChannelModal(self.guild, self.settings)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🏅 ตั้งรางวัลยศตามเลเวล", style=discord.ButtonStyle.secondary, row=0)
    async def set_level_roles(self, button, interaction):
        modal = LevelRoleModal(self.guild, self.settings)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="⚡ ปรับค่า XP", style=discord.ButtonStyle.secondary, row=1)
    async def set_xp_rate(self, button, interaction):
        modal = XPRateModal(self.guild, self.settings)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📢 เปิด/ปิดประกาศ Level Up", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_levelup_announce(self, button, interaction):
        current = self.settings.get("levelup_announce", True)
        new_val = not current
        await db.update_guild_settings(self.guild.id, "levelup_announce", new_val)
        self.settings["levelup_announce"] = new_val
        status = "เปิดแล้วน้าา 🟢✨" if new_val else "ปิดแล้วน้าา 🔴"
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"📢 ประกาศ Level Up: {status}",
                color=0x66BB6A if new_val else 0xEF5350,
            ),
            ephemeral=True,
        )

    @discord.ui.button(label="🧹 รีเซ็ต XP ทั้งเซิร์ฟเวอร์", style=discord.ButtonStyle.danger, row=1)
    async def reset_all_xp(self, button, interaction):
        if not has_admin_perms(interaction.user):
            await interaction.response.send_message(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์แอดมิน 💡"),
                ephemeral=True,
            )
            return
        view = ConfirmResetView(self.guild, interaction.user.id)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="⚠️ ยืนยันการรีเซ็ต XP ทั้งเซิร์ฟเวอร์?",
                description=(
                    "คุณกำลังจะรีเซ็ต XP ของสมาชิกทุกคนน้าา\n"
                    "ทำแล้วกู้คืนไม่ได้เลยนะา 🥺\n\n"
                    "**ยืนยันต่อไหม?**"
                ),
                color=0xFF5722,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="📊 ดูรางวัลยศที่ตั้งค่า", style=discord.ButtonStyle.secondary, row=2)
    async def view_level_roles(self, button, interaction):
        level_roles = self.settings.get("level_roles", {})
        embed = discord.Embed(
            title="🏅 รางวัลยศตามเลเวล",
            description="ตั้งค่าไว้ว่าเลเวลไหนได้ยศอะไรน้าา 🎁",
            color=LEVEL_COLOR,
        )
        if not level_roles:
            embed.description = "ยังไม่มีรางวัลยศน้าา~\nกด **🏅 ตั้งรางวัลยศ** เพื่อเพิ่มได้เลยยย 💡"
        else:
            for lvl, role_id in sorted(level_roles.items(), key=lambda x: int(x[0])):
                role = self.guild.get_role(role_id)
                emoji = level_emoji(int(lvl))
                embed.add_field(
                    name=f"{emoji} เลเวล {lvl}",
                    value=role.mention if role else f"ยศไอดี {role_id} (ไม่พบ)",
                    inline=True,
                )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ConfirmResetView(discord.ui.View):
    def __init__(self, guild, author_id):
        super().__init__(timeout=30)
        self.guild = guild
        self.author_id = author_id

    @discord.ui.button(label="✅ ยืนยัน รีเซ็ตเลย!", style=discord.ButtonStyle.danger)
    async def confirm(self, button, interaction):
        if interaction.user.id != self.author_id:
            return
        await db.reset_all_xp(self.guild.id)
        await interaction.response.send_message(
            embed=success_embed("รีเซ็ตแล้วน้าา ✨", "XP ทั้งเซิร์ฟเวอร์ถูกรีเซ็ตเรียบร้อยยย"),
            ephemeral=True,
        )
        self.stop()

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.secondary)
    async def cancel(self, button, interaction):
        await interaction.response.send_message(
            embed=success_embed("ยกเลิกแล้วน้าา ✅", "ไม่มีอะไรเปลี่ยนแปลง สบายใจได้ 💖"),
            ephemeral=True,
        )
        self.stop()


class LevelChannelModal(discord.ui.Modal):
    def __init__(self, guild, settings):
        super().__init__(title="🔔 ตั้งห้องแจ้งเตือน Level Up")
        self.guild = guild
        self.settings = settings
        self.add_item(discord.ui.InputText(
            label="ไอดีหรือชื่อห้อง",
            placeholder="เช่น 123456789 หรือ general",
            required=True,
        ))

    async def callback(self, interaction: discord.Interaction):
        val = self.children[0].value.strip().lstrip("#").lstrip("<#").rstrip(">")
        channel = None
        try:
            channel = self.guild.get_channel(int(val))
        except ValueError:
            channel = discord.utils.get(self.guild.channels, name=val)
        if not channel:
            await interaction.response.send_message(
                embed=error_embed("หาห้องไม่เจอน้าา 🔍", "ลองเช็คชื่อหรือไอดีอีกทีนะา 💡"),
                ephemeral=True,
            )
            return
        await db.update_guild_settings(self.guild.id, "levelup_channel", channel.id)
        await interaction.response.send_message(
            embed=success_embed("บันทึกแล้วน้าา ✨", f"ตั้งห้องแจ้งเตือน Level Up เป็น {channel.mention} เรียบร้อยยย"),
            ephemeral=True,
        )


class LevelRoleModal(discord.ui.Modal):
    def __init__(self, guild, settings):
        super().__init__(title="🏅 ตั้งรางวัลยศตามเลเวล")
        self.guild = guild
        self.settings = settings
        self.add_item(discord.ui.InputText(
            label="เลเวล",
            placeholder="เช่น 5, 10, 20",
            required=True,
        ))
        self.add_item(discord.ui.InputText(
            label="ไอดียศ (Role ID)",
            placeholder="คัดลอก Role ID มาใส่ได้เลยน้าา",
            required=True,
        ))

    async def callback(self, interaction: discord.Interaction):
        try:
            level = int(self.children[0].value.strip())
            role_id = int(self.children[1].value.strip())
        except ValueError:
            await interaction.response.send_message(
                embed=error_embed("ตัวเลขผิดน้าา 🥺", "ใส่แค่ตัวเลขนะา 💡"),
                ephemeral=True,
            )
            return
        role = self.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message(
                embed=error_embed("หายศไม่เจอน้าา 🔍", "เช็ค Role ID อีกทีนะา 💡"),
                ephemeral=True,
            )
            return
        level_roles = self.settings.get("level_roles", {})
        level_roles[str(level)] = role_id
        await db.update_guild_settings(self.guild.id, "level_roles", level_roles)
        await interaction.response.send_message(
            embed=success_embed(
                "ตั้งรางวัลแล้วน้าา ✨",
                f"เลเวล **{level}** → ยศ {role.mention} เรียบร้อยยย 🏅",
            ),
            ephemeral=True,
        )


class XPRateModal(discord.ui.Modal):
    def __init__(self, guild, settings):
        super().__init__(title="⚡ ปรับค่า XP")
        self.guild = guild
        self.settings = settings
        self.add_item(discord.ui.InputText(
            label="XP ขั้นต่ำต่อข้อความ",
            value=str(settings.get("xp_min", XP_MIN)),
            placeholder="เช่น 5",
            required=True,
        ))
        self.add_item(discord.ui.InputText(
            label="XP สูงสุดต่อข้อความ",
            value=str(settings.get("xp_max", XP_MAX)),
            placeholder="เช่น 15",
            required=True,
        ))
        self.add_item(discord.ui.InputText(
            label="ระยะ Cooldown (วินาที)",
            value=str(settings.get("xp_cooldown", XP_COOLDOWN)),
            placeholder="เช่น 60 (วินาที)",
            required=True,
        ))

    async def callback(self, interaction: discord.Interaction):
        try:
            xp_min = max(1, int(self.children[0].value.strip()))
            xp_max = max(xp_min, int(self.children[1].value.strip()))
            cooldown = max(10, int(self.children[2].value.strip()))
        except ValueError:
            await interaction.response.send_message(
                embed=error_embed("ตัวเลขผิดน้าา 🥺", "ใส่แค่ตัวเลขนะา 💡"),
                ephemeral=True,
            )
            return
        await db.update_guild_settings(self.guild.id, "xp_min", xp_min)
        await db.update_guild_settings(self.guild.id, "xp_max", xp_max)
        await db.update_guild_settings(self.guild.id, "xp_cooldown", cooldown)
        await interaction.response.send_message(
            embed=success_embed(
                "ตั้งค่า XP แล้วน้าา ✨",
                f"XP ต่อข้อความ: **{xp_min}–{xp_max}** XP\nCooldown: **{cooldown}** วินาที",
            ),
            ephemeral=True,
        )


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldowns: dict[tuple, float] = {}

    def is_on_cooldown(self, guild_id: int, user_id: int, cooldown: int) -> bool:
        import time
        key = (guild_id, user_id)
        now = time.time()
        last = self.xp_cooldowns.get(key, 0)
        if now - last >= cooldown:
            self.xp_cooldowns[key] = now
            return False
        return True

    async def build_profile_embed(self, member: discord.Member, guild: discord.Guild) -> discord.Embed:
        data = await db.get_user_level(guild.id, member.id)
        xp = data.get("xp", 0) if data else 0
        messages = data.get("messages", 0) if data else 0
        level, cur_xp, need_xp = level_progress(xp)
        bar = xp_bar(cur_xp, need_xp, 14)
        pct = round((cur_xp / need_xp * 100) if need_xp > 0 else 100, 1)
        emoji = level_emoji(level)

        all_rows = await db.get_levels_leaderboard(guild.id)
        rank = next((i + 1 for i, (uid, *_) in enumerate(all_rows) if uid == member.id), None)

        embed = discord.Embed(
            title=f"{emoji} โปรไฟล์ {member.display_name}",
            color=member.color if member.color != discord.Color.default() else LEVEL_COLOR,
            timestamp=datetime.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🎯 เลเวล", value=f"**{level}**", inline=True)
        embed.add_field(name="✨ XP รวม", value=f"**{xp:,}**", inline=True)
        embed.add_field(name="🏆 อันดับ", value=f"**#{rank}**" if rank else "ยังไม่มีอันดับ", inline=True)
        embed.add_field(name="💬 ข้อความ", value=f"**{messages:,}**", inline=True)
        embed.add_field(name="⬆️ XP ถึงเลเวลถัดไป", value=f"**{need_xp - cur_xp:,} XP**", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(
            name="📊 ความก้าวหน้า",
            value=f"`{bar}` **{pct}%**\n{cur_xp:,}/{need_xp:,} XP → เลเวล {level + 1}",
            inline=False,
        )
        embed.set_footer(text=f"แชทเยอะๆ เดี๋ยวเลเวลขึ้นเองน้าา ✨")
        return embed

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not message.content:
            return
        settings = await db.get_guild_settings(message.guild.id)
        if not settings.get("levels_enabled"):
            return

        cooldown = settings.get("xp_cooldown", XP_COOLDOWN)
        if self.is_on_cooldown(message.guild.id, message.author.id, cooldown):
            return

        xp_min = settings.get("xp_min", XP_MIN)
        xp_max = settings.get("xp_max", XP_MAX)
        xp_gained = random.randint(xp_min, xp_max)

        data_before = await db.get_user_level(message.guild.id, message.author.id)
        old_xp = data_before.get("xp", 0) if data_before else 0
        old_level = calc_level(old_xp)

        await db.add_xp(message.guild.id, message.author.id, xp_gained)

        data_after = await db.get_user_level(message.guild.id, message.author.id)
        new_xp = data_after.get("xp", 0) if data_after else old_xp + xp_gained
        new_level = calc_level(new_xp)

        if new_level > old_level:
            emoji = level_emoji(new_level)
            level_roles = settings.get("level_roles", {})
            role_id = level_roles.get(str(new_level))
            role_mention = ""
            if role_id:
                role = message.guild.get_role(role_id)
                if role and role not in message.author.roles:
                    try:
                        await message.author.add_roles(role, reason=f"Level Up เลเวล {new_level}")
                        role_mention = f"\n🎁 ได้รับยศ {role.mention} แล้วน้าา!"
                    except discord.Forbidden:
                        pass

            if settings.get("levelup_announce", True):
                levelup_ch_id = settings.get("levelup_channel")
                target_ch = message.guild.get_channel(levelup_ch_id) if levelup_ch_id else message.channel

                embed = discord.Embed(
                    title=f"{emoji} Level Up! เลเวลขึ้นแล้วน้าา! ✨",
                    description=(
                        f"🎉 ยินดีด้วยน้าา {message.author.mention}!\n"
                        f"เลเวล **{old_level}** → **{new_level}** เย่เล่ยยย! 🥳{role_mention}"
                    ),
                    color=LEVEL_COLOR,
                    timestamp=datetime.utcnow(),
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                level_xp = xp_for_level(new_level)
                next_xp = xp_for_level(new_level + 1)
                bar = xp_bar(0, next_xp - level_xp, 12)
                embed.add_field(
                    name="📊 เลเวลถัดไป",
                    value=f"`{bar}` 0/{next_xp - level_xp:,} XP → เลเวล {new_level + 1}",
                    inline=False,
                )
                embed.set_footer(text="แชทต่อไปนะา เดี๋ยวเลเวลขึ้นอีกแน่ๆ 💪✨")

                if target_ch:
                    try:
                        await target_ch.send(embed=embed)
                    except discord.Forbidden:
                        pass

    @commands.slash_command(name="rank", description="ดูอันดับและ XP ของตัวเอง")
    async def rank_cmd(
        self, ctx,
        สมาชิก: discord.Option(discord.Member, "สมาชิกที่ต้องการดู", required=False),
    ):
        target = สมาชิก or ctx.author
        embed = await self.build_profile_embed(target, ctx.guild)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="leaderboard", description="ดู Leaderboard อันดับ XP")
    async def leaderboard_cmd(self, ctx):
        await ctx.defer()
        rows = await db.get_levels_leaderboard(ctx.guild.id)
        if not rows:
            await ctx.respond(
                embed=discord.Embed(
                    title="📊 ยังไม่มีข้อมูล XP น้าา",
                    description="แชทกันก่อนแล้วมาดูอันดับกันนะา 💬✨",
                    color=LEVEL_COLOR,
                )
            )
            return
        view = LeaderboardView(self.bot, ctx.guild, rows, ctx.author.id)
        await ctx.respond(embed=view.get_page_embed(), view=view)

    @commands.slash_command(name="ระบบเลเวล", description="เปิดศูนย์ตั้งค่าระบบเลเวล XP")
    async def levels_panel(self, ctx):
        if not has_mod_perms(ctx.author):
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์ Mod ขึ้นไป 💡"),
                ephemeral=True,
            )
            return
        settings = await db.get_guild_settings(ctx.guild.id)
        data = await db.get_user_level(ctx.guild.id, ctx.author.id)
        xp = data.get("xp", 0) if data else 0
        level, cur_xp, need_xp = level_progress(xp)
        bar = xp_bar(cur_xp, need_xp, 12)
        total_members = len([r for r in (await db.get_levels_leaderboard(ctx.guild.id))])

        embed = discord.Embed(
            title="⚡ ศูนย์ระบบเลเวลและ XP",
            description=(
                "ยิ่งแชทเยอะ ยิ่งได้ XP เยอะ ยิ่งเลเวลสูง ✨\n"
                "ตั้งค่าระบบ XP รางวัลยศ และ Leaderboard ได้จากที่นี่น้าา 💖"
            ),
            color=LEVEL_COLOR,
        )
        embed.add_field(
            name="⚙️ สถานะระบบ",
            value=(
                f"✅ ระบบเลเวล: {'🟢 เปิด' if settings.get('levels_enabled') else '🔴 ปิด'}\n"
                f"📢 ประกาศ Level Up: {'🟢 เปิด' if settings.get('levelup_announce', True) else '🔴 ปิด'}\n"
                f"⚡ XP ต่อข้อความ: {settings.get('xp_min', XP_MIN)}–{settings.get('xp_max', XP_MAX)} XP\n"
                f"⏰ Cooldown: {settings.get('xp_cooldown', XP_COOLDOWN)} วินาที\n"
                f"👥 สมาชิกที่มีข้อมูล XP: {total_members} คน"
            ),
            inline=True,
        )
        embed.add_field(
            name="👤 ข้อมูลของคุณ",
            value=(
                f"🎯 เลเวล: **{level}**\n"
                f"✨ XP: **{xp:,}**\n"
                f"`{bar}`\n"
                f"{cur_xp}/{need_xp} XP → เลเวล {level + 1}"
            ),
            inline=True,
        )
        level_roles = settings.get("level_roles", {})
        if level_roles:
            roles_text = "\n".join([
                f"Lv.**{lvl}** → <@&{rid}>"
                for lvl, rid in sorted(level_roles.items(), key=lambda x: int(x[0]))[:5]
            ])
            embed.add_field(name="🏅 รางวัลยศ", value=roles_text, inline=False)

        embed.set_footer(text="แชทเยอะๆ เดี๋ยวเลเวลขึ้นเองน้าา ✨")
        embed.timestamp = datetime.utcnow()
        view = LevelSettingsView(ctx.guild, settings, ctx.author.id)
        await ctx.respond(embed=embed, view=view)

    @commands.slash_command(name="ให้xp", description="ให้ XP แก่สมาชิก (แอดมินเท่านั้น)")
    async def give_xp_cmd(
        self, ctx,
        สมาชิก: discord.Option(discord.Member, "สมาชิกที่ต้องการให้ XP"),
        จำนวน: discord.Option(int, "จำนวน XP", min_value=1, max_value=10000),
    ):
        if not has_admin_perms(ctx.author):
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์แอดมิน 💡"),
                ephemeral=True,
            )
            return
        await db.add_xp(ctx.guild.id, สมาชิก.id, จำนวน)
        data = await db.get_user_level(ctx.guild.id, สมาชิก.id)
        new_xp = data.get("xp", 0) if data else จำนวน
        new_level = calc_level(new_xp)
        await ctx.respond(
            embed=success_embed(
                "ให้ XP แล้วน้าา ✨",
                f"ให้ {สมาชิก.mention} **+{จำนวน:,} XP** แล้วยย!\n✨ XP รวม: {new_xp:,} • เลเวล: {new_level}",
            ),
            ephemeral=True,
        )


def setup(bot):
    bot.add_cog(Levels(bot))
