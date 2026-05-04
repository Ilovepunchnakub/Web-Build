import discord
from discord.ext import commands
from datetime import datetime
import database as db
from bot_embeds import success_embed, error_embed, build_announce_embed, announce_embed
from bot_helpers import has_admin_perms, has_mod_perms


ANNOUNCEMENT_TEMPLATES = {
    "ประกาศทั่วไป": {
        "color": 0x42A5F5,
        "emoji": "📢",
        "title": "📢 ประกาศสำคัญ",
    },
    "อัปเดต/แพตช์": {
        "color": 0x66BB6A,
        "emoji": "🔄",
        "title": "🔄 อัปเดตใหม่",
    },
    "กติกาและนโยบาย": {
        "color": 0xFFA726,
        "emoji": "📜",
        "title": "📜 กติกาเซิร์ฟเวอร์",
    },
    "อีเวนต์/กิจกรรม": {
        "color": 0xEC407A,
        "emoji": "🎉",
        "title": "🎉 อีเวนต์พิเศษ!",
    },
    "แจ้งเตือนเร่งด่วน": {
        "color": 0xEF5350,
        "emoji": "🚨",
        "title": "🚨 แจ้งเตือนเร่งด่วน",
    },
    "ขอบคุณ/เฉลิมฉลอง": {
        "color": 0xFFD700,
        "emoji": "🥳",
        "title": "🥳 เฉลิมฉลองน้าา!",
    },
}


class AnnouncementView(discord.ui.View):
    def __init__(self, guild, settings, author_id):
        super().__init__(timeout=300)
        self.guild = guild
        self.settings = settings
        self.author_id = author_id

    async def interaction_check(self, interaction):
        return interaction.user.id == self.author_id or has_mod_perms(interaction.user)

    @discord.ui.button(label="✅ เปิด/ปิดระบบ", style=discord.ButtonStyle.success, row=0)
    async def toggle_announce(self, button, interaction):
        current = self.settings.get("announce_enabled", False)
        new_val = not current
        self.settings["announce_enabled"] = new_val
        await db.update_guild_settings(self.guild.id, "announce_enabled", new_val)
        status = "เปิดแล้วน้าา 🟢✨" if new_val else "ปิดแล้วน้าา 🔴"
        await interaction.response.send_message(
            embed=success_embed(f"ระบบประกาศ {status}", "เปลี่ยนสถานะเรียบร้อยยย ✅"),
            ephemeral=True,
        )

    @discord.ui.button(label="📍 ตั้งห้องประกาศ", style=discord.ButtonStyle.primary, row=0)
    async def set_channel(self, button, interaction):
        from cog_welcome import ChannelSelectView
        view = ChannelSelectView(self.guild, self.settings, self.author_id, "announce_channel", "ประกาศ")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="📍 เลือกห้องประกาศ",
                description="เลือกห้องที่จะส่งประกาศหลัก 👇",
                color=0x26C6DA,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="✍️ สร้างประกาศใหม่", style=discord.ButtonStyle.success, row=0)
    async def create_announce(self, button, interaction):
        modal = CreateAnnouncementModal(self.guild, self.settings)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🎨 เลือกเทมเพลต", style=discord.ButtonStyle.primary, row=0)
    async def use_template(self, button, interaction):
        view = TemplateSelectView(self.guild, self.settings, interaction.user.id)
        embed = discord.Embed(
            title="🎨 เลือกเทมเพลตประกาศ",
            description="เลือกสไตล์ประกาศที่ต้องการ แล้วกรอกเนื้อหาได้เลยน้าา 👇",
            color=0x26C6DA,
        )
        for name, tmpl in ANNOUNCEMENT_TEMPLATES.items():
            embed.add_field(
                name=f"{tmpl['emoji']} {name}",
                value=f"สีธีม: `#{hex(tmpl['color'])[2:].upper()}`",
                inline=True,
            )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="📌 เปิด/ปิดปักหมุดอัตโนมัติ", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_pin(self, button, interaction):
        current = self.settings.get("announce_pin", False)
        new_val = not current
        self.settings["announce_pin"] = new_val
        await db.update_guild_settings(self.guild.id, "announce_pin", new_val)
        status = "เปิดแล้วน้าา 🟢✨" if new_val else "ปิดแล้วน้าา 🔴"
        await interaction.response.send_message(
            embed=success_embed(f"ปักหมุดอัตโนมัติ {status}", "ประกาศใหม่จะถูกปักหมุดทุกครั้งเลยยย ✅"),
            ephemeral=True,
        )

    @discord.ui.button(label="🔔 ตั้งห้องแจ้งเตือน", style=discord.ButtonStyle.secondary, row=1)
    async def set_notify_channel(self, button, interaction):
        from cog_welcome import ChannelSelectView
        view = ChannelSelectView(self.guild, self.settings, self.author_id, "notify_channel", "แจ้งเตือน")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔔 เลือกห้องแจ้งเตือน",
                description="เลือกห้องที่จะส่งการแจ้งเตือนอัตโนมัติต่างๆ 👇",
                color=0xFFA726,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="📜 ประวัติประกาศ", style=discord.ButtonStyle.secondary, row=1)
    async def history(self, button, interaction):
        announcements = await db.get_recent_announcements(self.guild.id, limit=5)
        embed = discord.Embed(
            title="📜 ประวัติประกาศล่าสุด",
            description="5 ประกาศล่าสุดในเซิร์ฟเวอร์น้าา 📋",
            color=0x26C6DA,
        )
        if not announcements:
            embed.description = "ยังไม่มีประวัติประกาศน้าา~\nสร้างประกาศแรกได้เลยยย 📢"
        else:
            for i, (title, channel_id, user_id, created_at) in enumerate(announcements, 1):
                ch = self.guild.get_channel(channel_id) if channel_id else None
                member = self.guild.get_member(user_id) if user_id else None
                embed.add_field(
                    name=f"`{i}.` {title[:50]}",
                    value=(
                        f"📍 {ch.mention if ch else 'ไม่ทราบห้อง'} • "
                        f"👤 {member.display_name if member else 'ไม่ทราบ'}"
                    ),
                    inline=False,
                )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class TemplateSelectView(discord.ui.View):
    def __init__(self, guild, settings, author_id):
        super().__init__(timeout=60)
        self.guild = guild
        self.settings = settings
        self.author_id = author_id

        options = [
            discord.SelectOption(
                label=name,
                value=name,
                description=f"{tmpl['emoji']} {tmpl['title']}",
                emoji=tmpl["emoji"],
            )
            for name, tmpl in ANNOUNCEMENT_TEMPLATES.items()
        ]
        select = discord.ui.Select(
            placeholder="🎨 เลือกเทมเพลตประกาศได้เลยน้าา...",
            options=options,
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        tmpl_name = interaction.data["values"][0]
        tmpl = ANNOUNCEMENT_TEMPLATES.get(tmpl_name, {})
        modal = CreateAnnouncementModal(self.guild, self.settings, template=tmpl, template_name=tmpl_name)
        await interaction.response.send_modal(modal)


class CreateAnnouncementModal(discord.ui.Modal):
    def __init__(self, guild, settings, template=None, template_name=""):
        title_text = f"✍️ ประกาศ: {template_name}" if template_name else "✍️ สร้างประกาศใหม่"
        super().__init__(title=title_text[:45])
        self.guild = guild
        self.settings = settings
        self.template = template or {}

        default_title = self.template.get("title", "📢 ประกาศสำคัญ")
        self.add_item(discord.ui.InputText(
            label="หัวข้อประกาศ",
            placeholder="ระบุหัวข้อประกาศ...",
            value=default_title,
            required=True,
        ))
        self.add_item(discord.ui.InputText(
            label="เนื้อหาประกาศ",
            placeholder="พิมพ์เนื้อหาประกาศได้เลยน้าา...",
            style=discord.InputTextStyle.long,
            required=True,
        ))
        self.add_item(discord.ui.InputText(
            label="URL รูปภาพ (ไม่บังคับ)",
            placeholder="https://example.com/image.png",
            required=False,
        ))
        self.add_item(discord.ui.InputText(
            label="แท็ก Role ไอดี (ไม่บังคับ)",
            placeholder="ไอดี Role ที่จะ ping เช่น 123456789",
            required=False,
        ))

    async def callback(self, interaction: discord.Interaction):
        title = self.children[0].value.strip()
        content = self.children[1].value.strip()
        image_url = self.children[2].value.strip() if self.children[2].value else None
        role_id_raw = self.children[3].value.strip() if self.children[3].value else None

        announce_ch_id = self.settings.get("announce_channel")
        if not announce_ch_id:
            await interaction.response.send_message(
                embed=error_embed(
                    "ยังไม่ตั้งห้องประกาศน้าา 🥺",
                    "ไปตั้งค่าห้องประกาศก่อนแล้วค่อยส่งนะา 💡",
                ),
                ephemeral=True,
            )
            return

        channel = self.guild.get_channel(announce_ch_id)
        if not channel:
            await interaction.response.send_message(
                embed=error_embed("หาห้องไม่เจอน้าา 🔍", "ห้องประกาศอาจถูกลบไปแล้ว 💡"),
                ephemeral=True,
            )
            return

        color = self.template.get("color", 0x26C6DA)
        embed = discord.Embed(title=title, description=content, color=color, timestamp=datetime.utcnow())
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"📢 {self.guild.name} • ประกาศโดยทีมงาน")

        if image_url:
            try:
                embed.set_image(url=image_url)
            except Exception:
                pass

        ping_content = ""
        if role_id_raw:
            try:
                role_id = int(role_id_raw)
                role = self.guild.get_role(role_id)
                if role:
                    ping_content = role.mention
            except ValueError:
                pass

        try:
            msg = await channel.send(content=ping_content if ping_content else None, embed=embed)
            if self.settings.get("announce_pin"):
                try:
                    await msg.pin()
                except discord.Forbidden:
                    pass
            await db.add_announcement(self.guild.id, title, announce_ch_id, interaction.user.id)
            await interaction.response.send_message(
                embed=success_embed(
                    "ส่งประกาศแล้วน้าา ✨",
                    f"ส่งประกาศ **{title[:50]}** ไปที่ {channel.mention} เรียบร้อยยย 📢",
                ),
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed(
                    "ส่งไม่ได้น้าา 😅",
                    "บอทไม่มีสิทธิ์ส่งข้อความในห้องนั้น ตรวจสอบสิทธิ์บอทด้วยนะา 💡",
                ),
                ephemeral=True,
            )


class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="ประกาศ", description="เปิดศูนย์ประกาศและส่งประกาศ")
    async def announce_panel(self, ctx):
        if not has_mod_perms(ctx.author):
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์ Mod ขึ้นไปถึงจะประกาศได้ 💡"),
                ephemeral=True,
            )
            return
        settings = await db.get_guild_settings(ctx.guild.id)
        embed = build_announce_embed(settings)
        view = AnnouncementView(ctx.guild, settings, ctx.author.id)
        await ctx.respond(embed=embed, view=view)

    @commands.slash_command(name="ประกาศด่วน", description="ส่งประกาศด่วนทันที")
    async def quick_announce(self, ctx, ข้อความ: discord.Option(str, "ข้อความประกาศ")):
        if not has_mod_perms(ctx.author):
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์ Mod ขึ้นไป 💡"),
                ephemeral=True,
            )
            return
        settings = await db.get_guild_settings(ctx.guild.id)
        announce_ch_id = settings.get("announce_channel")

        if not announce_ch_id:
            await ctx.respond(
                embed=error_embed("ยังไม่ตั้งห้องประกาศน้าา 🥺", "ใช้ `/ประกาศ` เพื่อตั้งค่าก่อน 💡"),
                ephemeral=True,
            )
            return

        channel = ctx.guild.get_channel(announce_ch_id)
        if not channel:
            await ctx.respond(
                embed=error_embed("หาห้องไม่เจอน้าา 🔍", "ห้องประกาศอาจถูกลบไปแล้ว 💡"),
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🚨 ประกาศด่วนน้าา!",
            description=ข้อความ,
            color=0xEF5350,
            timestamp=datetime.utcnow(),
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"📢 {ctx.guild.name} • ประกาศด่วนโดยทีมงาน")

        try:
            await channel.send(embed=embed)
            await ctx.respond(
                embed=success_embed("ส่งประกาศด่วนแล้วน้าา ✨", f"ส่งไปที่ {channel.mention} เรียบร้อยยย"),
                ephemeral=True,
            )
        except discord.Forbidden:
            await ctx.respond(
                embed=error_embed("ส่งไม่ได้น้าา 😅", "บอทไม่มีสิทธิ์ส่งข้อความในห้องนั้น 💡"),
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(Announcements(bot))
