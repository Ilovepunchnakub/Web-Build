import discord
from discord.ext import commands
import database as db
from bot_embeds import success_embed, error_embed, build_channel_embed
from bot_helpers import has_admin_perms, has_mod_perms


class ChannelManageView(discord.ui.View):
    def __init__(self, guild, settings, author_id):
        super().__init__(timeout=300)
        self.guild = guild
        self.settings = settings
        self.author_id = author_id

    async def interaction_check(self, interaction):
        return interaction.user.id == self.author_id or has_mod_perms(interaction.user)

    @discord.ui.button(label="➕ สร้างห้อง", style=discord.ButtonStyle.success, row=0)
    async def create_channel(self, button, interaction):
        modal = CreateChannelModal(self.guild)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🗑️ ลบห้อง", style=discord.ButtonStyle.danger, row=0)
    async def delete_channel(self, button, interaction):
        if not has_admin_perms(interaction.user):
            await interaction.response.send_message(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์แอดมินถึงจะลบห้องได้ 💡"),
                ephemeral=True,
            )
            return
        view = ChannelActionSelectView(self.guild, self.author_id, "delete")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🗑️ เลือกห้องที่จะลบ",
                description="⚠️ **ระวัง!** ลบแล้วกู้คืนไม่ได้น้าา ข้อความทั้งหมดจะหายถาวร 🥺",
                color=0xEF5350,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="✏️ แก้ชื่อห้อง", style=discord.ButtonStyle.primary, row=0)
    async def rename_channel(self, button, interaction):
        view = ChannelActionSelectView(self.guild, self.author_id, "rename")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✏️ เลือกห้องที่จะแก้ชื่อ",
                description="เลือกห้องที่ต้องการเปลี่ยนชื่อได้เลยน้าา 👇",
                color=0x5865F2,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="📋 ดูรายการห้อง", style=discord.ButtonStyle.secondary, row=0)
    async def list_channels(self, button, interaction):
        embed = discord.Embed(title="📋 รายการห้องทั้งหมดน้าา", color=0x78909C)
        text_chs = [c for c in self.guild.channels if isinstance(c, discord.TextChannel)][:10]
        voice_chs = [c for c in self.guild.channels if isinstance(c, discord.VoiceChannel)][:8]

        text_list = "\n".join([f"💬 {c.mention}" for c in text_chs])
        voice_list = "\n".join([f"🎙️ **{c.name}** ({len(c.members)} คน)" for c in voice_chs])

        if text_list:
            embed.add_field(name=f"💬 ห้องข้อความ ({len(text_chs)})", value=text_list, inline=True)
        if voice_list:
            embed.add_field(name=f"🎙️ ห้องเสียง ({len(voice_chs)})", value=voice_list, inline=True)
        embed.set_footer(text=f"📦 รวม {len(self.guild.channels)} ห้องทั้งหมด")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔒 ล็อกห้อง", style=discord.ButtonStyle.danger, row=1)
    async def lock_channel(self, button, interaction):
        view = ChannelActionSelectView(self.guild, self.author_id, "lock")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔒 เลือกห้องที่จะล็อก",
                description="สมาชิกทั่วไปจะส่งข้อความไม่ได้หลังล็อกน้าา 🔐",
                color=0xEF5350,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="🔓 ปลดล็อก", style=discord.ButtonStyle.success, row=1)
    async def unlock_channel(self, button, interaction):
        view = ChannelActionSelectView(self.guild, self.author_id, "unlock")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔓 เลือกห้องที่จะปลดล็อก",
                description="เปิดให้สมาชิกส่งข้อความได้อีกครั้งน้าา 🔓✨",
                color=0x66BB6A,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="👁️ ซ่อนห้อง", style=discord.ButtonStyle.secondary, row=1)
    async def hide_channel(self, button, interaction):
        view = ChannelActionSelectView(self.guild, self.author_id, "hide")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="👁️ เลือกห้องที่จะซ่อน",
                description="สมาชิกทั่วไปจะมองไม่เห็นห้องหลังซ่อนน้าา 👁️",
                color=0x78909C,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="👁️‍🗨️ แสดงห้อง", style=discord.ButtonStyle.success, row=1)
    async def show_channel(self, button, interaction):
        view = ChannelActionSelectView(self.guild, self.author_id, "show")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="👁️‍🗨️ เลือกห้องที่จะแสดง",
                description="เปิดให้ทุกคนมองเห็นได้อีกครั้งน้าา 👁️‍🗨️✨",
                color=0x66BB6A,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="🧹 ล้างข้อความ", style=discord.ButtonStyle.danger, row=1)
    async def clear_messages(self, button, interaction):
        view = ChannelActionSelectView(self.guild, self.author_id, "clear")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🧹 เลือกห้องที่จะล้างข้อความ",
                description="⚠️ ข้อความที่ลบแล้วกู้คืนไม่ได้น้าา ระวังด้วยนะา 🥺",
                color=0xEF5350,
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="🤖 ตั้ง Auto Room", style=discord.ButtonStyle.primary, row=2)
    async def setup_autoroom(self, button, interaction):
        modal = AutoRoomModal(self.guild, self.settings)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🧩 ตั้งสิทธิ์ยศ", style=discord.ButtonStyle.secondary, row=2)
    async def set_role_perms(self, button, interaction):
        embed = discord.Embed(
            title="🧩 ตั้งค่าสิทธิ์ยศในห้อง",
            description="ใช้คำสั่งด้านล่างเพื่อตั้งค่าสิทธิ์ได้เลยน้าา 💡",
            color=0x78909C,
        )
        embed.add_field(
            name="⚡ คำสั่งที่ใช้ได้",
            value=(
                "• `/ล็อกห้อง #ห้อง` — ล็อกห้อง 🔒\n"
                "• `/ปลดล็อกห้อง #ห้อง` — ปลดล็อก 🔓\n"
                "• `/ซ่อนห้อง #ห้อง` — ซ่อนห้อง 👁️\n"
                "• `/ตั้งสิทธิ์ #ห้อง @ยศ` — ตั้งค่าสิทธิ์ 🧩"
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔄 รีเฟรช", style=discord.ButtonStyle.success, row=2)
    async def refresh(self, button, interaction):
        settings = await db.get_guild_settings(self.guild.id)
        self.settings = settings
        embed = build_channel_embed(self.guild, settings)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="🔒 ล็อกเซิร์ฟเวอร์", style=discord.ButtonStyle.danger, row=2)
    async def lock_server(self, button, interaction):
        if not has_admin_perms(interaction.user):
            await interaction.response.send_message(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์แอดมิน 💡"),
                ephemeral=True,
            )
            return
        view = ConfirmServerLockView(self.guild, interaction.user.id, lock=True)
        embed = discord.Embed(
            title="⚠️ ยืนยันการล็อกเซิร์ฟเวอร์?",
            description="ทุกห้องจะถูกล็อกและสมาชิกทั่วไปจะส่งข้อความไม่ได้\nกดยืนยันเพื่อดำเนินการต่อน้าา",
            color=0xEF5350,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ChannelActionSelectView(discord.ui.View):
    def __init__(self, guild, author_id, action):
        super().__init__(timeout=60)
        self.guild = guild
        self.action = action
        self.author_id = author_id

        channels = [c for c in guild.channels
                    if isinstance(c, (discord.TextChannel, discord.VoiceChannel))][:25]
        options = [
            discord.SelectOption(
                label=f"#{c.name}"[:100],
                value=str(c.id),
                emoji="💬" if isinstance(c, discord.TextChannel) else "🎙️",
                description=f"{'ข้อความ' if isinstance(c, discord.TextChannel) else 'เสียง'}",
            )
            for c in channels
        ]
        if options:
            select = discord.ui.Select(placeholder="📍 เลือกห้องได้เลยน้าา...", options=options)
            select.callback = self.channel_callback
            self.add_item(select)

    async def channel_callback(self, interaction: discord.Interaction):
        ch_id = int(interaction.data["values"][0])
        channel = self.guild.get_channel(ch_id)
        if not channel:
            await interaction.response.send_message(
                embed=error_embed("หาห้องไม่เจอน้าา 🔍", "ห้องนี้อาจถูกลบไปแล้ว 💡"),
                ephemeral=True,
            )
            return

        try:
            if self.action == "delete":
                view = ConfirmDeleteView(channel)
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="⚠️ ยืนยันการลบ?",
                        description=f"กำลังจะลบห้อง **#{channel.name}**\n⚠️ ข้อความทั้งหมดจะหายถาวรเลยน้าา 🥺",
                        color=0xEF5350,
                    ),
                    view=view,
                    ephemeral=True,
                )
            elif self.action == "rename":
                modal = RenameChannelModal(channel)
                await interaction.response.send_modal(modal)
            elif self.action == "lock":
                overwrite = channel.overwrites_for(self.guild.default_role)
                overwrite.send_messages = False
                await channel.set_permissions(self.guild.default_role, overwrite=overwrite)
                await interaction.response.send_message(
                    embed=success_embed(
                        "ล็อกแล้วน้าา 🔒✨",
                        f"ล็อกห้อง {channel.mention} แล้วยย\nสมาชิกทั่วไปส่งข้อความไม่ได้แล้ว",
                    ),
                    ephemeral=True,
                )
            elif self.action == "unlock":
                overwrite = channel.overwrites_for(self.guild.default_role)
                overwrite.send_messages = None
                await channel.set_permissions(self.guild.default_role, overwrite=overwrite)
                await interaction.response.send_message(
                    embed=success_embed(
                        "ปลดล็อกแล้วน้าา 🔓✨",
                        f"ปลดล็อกห้อง {channel.mention} แล้วยย สมาชิกส่งข้อความได้แล้ว",
                    ),
                    ephemeral=True,
                )
            elif self.action == "hide":
                overwrite = channel.overwrites_for(self.guild.default_role)
                overwrite.view_channel = False
                await channel.set_permissions(self.guild.default_role, overwrite=overwrite)
                await interaction.response.send_message(
                    embed=success_embed(
                        "ซ่อนแล้วน้าา 👁️✨",
                        f"ซ่อนห้อง **#{channel.name}** แล้วยย สมาชิกทั่วไปมองไม่เห็น",
                    ),
                    ephemeral=True,
                )
            elif self.action == "show":
                overwrite = channel.overwrites_for(self.guild.default_role)
                overwrite.view_channel = None
                await channel.set_permissions(self.guild.default_role, overwrite=overwrite)
                await interaction.response.send_message(
                    embed=success_embed(
                        "แสดงแล้วน้าา 👁️‍🗨️✨",
                        f"แสดงห้อง {channel.mention} แล้วยย ทุกคนมองเห็นแล้ว",
                    ),
                    ephemeral=True,
                )
            elif self.action == "clear":
                if isinstance(channel, discord.TextChannel):
                    modal = ClearChannelModal(channel)
                    await interaction.response.send_modal(modal)
                else:
                    await interaction.response.send_message(
                        embed=error_embed("ล้างไม่ได้น้าา 🥺", "ล้างข้อความได้เฉพาะห้องข้อความเท่านั้น 💡"),
                        ephemeral=True,
                    )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed("ไม่มีสิทธิ์น้าา 😅", "บอทไม่มีสิทธิ์ดำเนินการนี้ ตรวจสอบสิทธิ์บอทด้วยนะา 💡"),
                ephemeral=True,
            )


class ConfirmDeleteView(discord.ui.View):
    def __init__(self, channel):
        super().__init__(timeout=30)
        self.channel = channel

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.secondary)
    async def cancel(self, button, interaction):
        await interaction.response.send_message(
            embed=success_embed("ยกเลิกแล้วน้าา ✅", "ไม่มีอะไรถูกลบ สบายใจได้ 💖"),
            ephemeral=True,
        )
        self.stop()

    @discord.ui.button(label="🗑️ ยืนยันลบเลย", style=discord.ButtonStyle.danger)
    async def confirm(self, button, interaction):
        try:
            name = self.channel.name
            await self.channel.delete(reason=f"ลบโดย {interaction.user}")
            await interaction.response.send_message(
                embed=success_embed("ลบแล้วน้าา 🗑️✨", f"ลบห้อง **#{name}** เรียบร้อยยย"),
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed("ไม่มีสิทธิ์น้าา 😅", "บอทไม่มีสิทธิ์ลบห้องนี้ 💡"),
                ephemeral=True,
            )
        self.stop()


class ConfirmServerLockView(discord.ui.View):
    def __init__(self, guild, author_id, lock=True):
        super().__init__(timeout=30)
        self.guild = guild
        self.author_id = author_id
        self.lock = lock

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.secondary)
    async def cancel(self, button, interaction):
        await interaction.response.send_message(
            embed=success_embed("ยกเลิกแล้วน้าา ✅", "ไม่มีอะไรเปลี่ยนแปลง 💖"),
            ephemeral=True,
        )
        self.stop()

    @discord.ui.button(label="🔒 ยืนยันล็อกทั้งหมด", style=discord.ButtonStyle.danger)
    async def confirm(self, button, interaction):
        if interaction.user.id != self.author_id:
            return
        await interaction.response.defer(ephemeral=True)
        locked = 0
        for channel in self.guild.channels:
            if isinstance(channel, discord.TextChannel):
                try:
                    overwrite = channel.overwrites_for(self.guild.default_role)
                    overwrite.send_messages = False if self.lock else None
                    await channel.set_permissions(self.guild.default_role, overwrite=overwrite)
                    locked += 1
                except discord.Forbidden:
                    pass
        action = "ล็อก" if self.lock else "ปลดล็อก"
        await interaction.followup.send(
            embed=success_embed(
                f"{action}เซิร์ฟเวอร์แล้วน้าา ✨",
                f"{action} {locked} ห้องข้อความเรียบร้อยยย",
            ),
            ephemeral=True,
        )
        self.stop()


class CreateChannelModal(discord.ui.Modal):
    def __init__(self, guild):
        super().__init__(title="➕ สร้างห้องใหม่")
        self.guild = guild
        self.add_item(discord.ui.InputText(
            label="ชื่อห้อง",
            placeholder="ชื่อห้องใหม่ (ภาษาอังกฤษหรือไทยได้น้าา)",
            required=True,
        ))
        self.add_item(discord.ui.InputText(
            label="ประเภท (text / voice)",
            value="text",
            placeholder="text = ห้องข้อความ, voice = ห้องเสียง",
        ))
        self.add_item(discord.ui.InputText(
            label="คำอธิบายห้อง (ไม่บังคับ)",
            required=False,
            placeholder="คำอธิบายสั้นๆ เกี่ยวกับห้องนี้",
        ))

    async def callback(self, interaction: discord.Interaction):
        name = self.children[0].value.strip().replace(" ", "-")
        ch_type = self.children[1].value.strip().lower()
        description = self.children[2].value.strip() if self.children[2].value else None

        try:
            if ch_type == "voice":
                channel = await self.guild.create_voice_channel(
                    name=name,
                    reason=f"สร้างโดย {interaction.user}",
                )
                type_label = "🎙️ ห้องเสียง"
            else:
                channel = await self.guild.create_text_channel(
                    name=name,
                    topic=description,
                    reason=f"สร้างโดย {interaction.user}",
                )
                type_label = "💬 ห้องข้อความ"

            await interaction.response.send_message(
                embed=success_embed(
                    "สร้างห้องแล้วน้าา ✨",
                    f"{type_label} {channel.mention} ถูกสร้างเรียบร้อยยย 🎉",
                ),
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed("ไม่มีสิทธิ์น้าา 😅", "บอทไม่มีสิทธิ์สร้างห้อง ตรวจสอบสิทธิ์บอทด้วยนะา 💡"),
                ephemeral=True,
            )


class RenameChannelModal(discord.ui.Modal):
    def __init__(self, channel):
        super().__init__(title=f"✏️ แก้ชื่อ #{channel.name}")
        self.channel = channel
        self.add_item(discord.ui.InputText(
            label="ชื่อใหม่",
            value=channel.name,
            required=True,
        ))

    async def callback(self, interaction: discord.Interaction):
        old_name = self.channel.name
        new_name = self.children[0].value.strip()
        try:
            await self.channel.edit(name=new_name, reason=f"แก้ชื่อโดย {interaction.user}")
            await interaction.response.send_message(
                embed=success_embed(
                    "แก้ชื่อแล้วน้าา ✏️✨",
                    f"เปลี่ยน **#{old_name}** → **#{new_name}** เรียบร้อยยย",
                ),
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed("ไม่มีสิทธิ์น้าา 😅", "บอทไม่มีสิทธิ์แก้ชื่อห้อง 💡"),
                ephemeral=True,
            )


class ClearChannelModal(discord.ui.Modal):
    def __init__(self, channel):
        super().__init__(title=f"🧹 ล้างข้อความ #{channel.name}")
        self.channel = channel
        self.add_item(discord.ui.InputText(
            label="จำนวนข้อความที่จะลบ (สูงสุด 100)",
            placeholder="เช่น 50",
            required=True,
        ))

    async def callback(self, interaction: discord.Interaction):
        try:
            count = min(100, max(1, int(self.children[0].value.strip())))
        except ValueError:
            await interaction.response.send_message(
                embed=error_embed("ตัวเลขผิดน้าา 🥺", "ใส่แค่ตัวเลขนะา 💡"),
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        try:
            deleted = await self.channel.purge(limit=count)
            await interaction.followup.send(
                embed=success_embed(
                    "ล้างแล้วน้าา 🧹✨",
                    f"ลบ **{len(deleted)}** ข้อความในห้อง {self.channel.mention} เรียบร้อยยย",
                ),
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                embed=error_embed("ไม่มีสิทธิ์น้าา 😅", "บอทไม่มีสิทธิ์ลบข้อความ 💡"),
                ephemeral=True,
            )


class AutoRoomModal(discord.ui.Modal):
    def __init__(self, guild, settings):
        super().__init__(title="🤖 ตั้งค่า Auto Room")
        self.guild = guild
        self.settings = settings
        self.add_item(discord.ui.InputText(
            label="ไอดีหรือชื่อห้องเสียงต้นแบบ",
            placeholder="เข้าห้องนี้แล้วบอทจะสร้างห้องใหม่ให้อัตโนมัติน้าา",
            required=True,
        ))
        self.add_item(discord.ui.InputText(
            label="ชื่อห้องที่สร้าง (ใช้ {ชื่อผู้ใช้} ได้น้าา)",
            value="🎙️ ห้องของ {ชื่อผู้ใช้}",
            required=True,
        ))

    async def callback(self, interaction: discord.Interaction):
        value = self.children[0].value.strip().lstrip("#").lstrip("<#").rstrip(">")
        channel = None
        try:
            channel = self.guild.get_channel(int(value))
        except ValueError:
            channel = discord.utils.get(self.guild.voice_channels, name=value)

        if not channel:
            await interaction.response.send_message(
                embed=error_embed("หาห้องไม่เจอน้าา 🔍", "ตรวจสอบชื่อหรือไอดีอีกทีนะา 💡"),
                ephemeral=True,
            )
            return

        name_template = self.children[1].value.strip()
        await db.update_guild_settings(self.guild.id, "autoroom_channel", channel.id)
        await db.update_guild_settings(self.guild.id, "autoroom_name", name_template)
        await db.update_guild_settings(self.guild.id, "autoroom_enabled", True)
        await interaction.response.send_message(
            embed=success_embed(
                "ตั้ง Auto Room แล้วน้าา 🤖✨",
                f"ห้องต้นแบบ: **{channel.name}**\nชื่อห้องใหม่: `{name_template}`\nเข้าห้องนี้แล้วบอทจะสร้างห้องให้อัตโนมัติเลยยย ✅",
            ),
            ephemeral=True,
        )


class Channels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_rooms: dict[int, int] = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.guild:
            return
        settings = await db.get_guild_settings(member.guild.id)
        if not settings.get("autoroom_enabled"):
            return
        autoroom_ch = settings.get("autoroom_channel")
        if not autoroom_ch:
            return

        if after.channel and after.channel.id == autoroom_ch:
            name_template = settings.get("autoroom_name", "🎙️ ห้องของ {ชื่อผู้ใช้}")
            name = name_template.replace("{ชื่อผู้ใช้}", member.display_name)
            try:
                category = after.channel.category
                new_channel = await member.guild.create_voice_channel(
                    name=name,
                    category=category,
                    reason=f"Auto Room สำหรับ {member}",
                )
                self.auto_rooms[new_channel.id] = member.id
                await member.move_to(new_channel)
            except discord.Forbidden:
                pass

        if before.channel and before.channel.id in self.auto_rooms:
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete(reason="Auto Room ว่างแล้ว — ลบอัตโนมัติ")
                    self.auto_rooms.pop(before.channel.id, None)
                except (discord.Forbidden, discord.NotFound):
                    pass

    @commands.slash_command(name="จัดการห้อง", description="เปิดศูนย์จัดการห้องทั้งหมด")
    async def channels_panel(self, ctx):
        if not has_mod_perms(ctx.author):
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์ Mod ขึ้นไป 💡"),
                ephemeral=True,
            )
            return
        settings = await db.get_guild_settings(ctx.guild.id)
        embed = build_channel_embed(ctx.guild, settings)
        view = ChannelManageView(ctx.guild, settings, ctx.author.id)
        await ctx.respond(embed=embed, view=view)

    @commands.slash_command(name="ล้างแชท", description="ล้างข้อความในห้องนี้")
    async def purge_cmd(
        self, ctx,
        จำนวน: discord.Option(int, "จำนวนข้อความที่จะลบ (สูงสุด 100)", min_value=1, max_value=100),
    ):
        if not has_mod_perms(ctx.author):
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์ Mod ขึ้นไป 💡"),
                ephemeral=True,
            )
            return
        await ctx.defer(ephemeral=True)
        try:
            deleted = await ctx.channel.purge(limit=จำนวน)
            await ctx.respond(
                embed=success_embed(
                    "ล้างแล้วน้าา 🧹✨",
                    f"ลบ **{len(deleted)}** ข้อความในห้องนี้เรียบร้อยยย",
                ),
                ephemeral=True,
            )
        except discord.Forbidden:
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 😅", "บอทไม่มีสิทธิ์ลบข้อความ 💡"),
                ephemeral=True,
            )

    @commands.slash_command(name="ล็อกเซิร์ฟเวอร์", description="ล็อกทุกห้องในเซิร์ฟเวอร์")
    async def lockdown_cmd(self, ctx):
        if not has_admin_perms(ctx.author):
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์แอดมิน 💡"),
                ephemeral=True,
            )
            return
        view = ConfirmServerLockView(ctx.guild, ctx.author.id, lock=True)
        await ctx.respond(
            embed=discord.Embed(
                title="⚠️ ยืนยันการล็อกเซิร์ฟเวอร์?",
                description="ทุกห้องข้อความจะถูกล็อก\nกดยืนยันเพื่อดำเนินการต่อน้าา",
                color=0xEF5350,
            ),
            view=view,
            ephemeral=True,
        )

    @commands.slash_command(name="ปลดล็อกเซิร์ฟเวอร์", description="ปลดล็อกทุกห้องในเซิร์ฟเวอร์")
    async def unlockdown_cmd(self, ctx):
        if not has_admin_perms(ctx.author):
            await ctx.respond(
                embed=error_embed("ไม่มีสิทธิ์น้าา 🥺", "ต้องการสิทธิ์แอดมิน 💡"),
                ephemeral=True,
            )
            return
        view = ConfirmServerLockView(ctx.guild, ctx.author.id, lock=False)
        await ctx.respond(
            embed=discord.Embed(
                title="⚠️ ยืนยันการปลดล็อกเซิร์ฟเวอร์?",
                description="ทุกห้องข้อความจะถูกปลดล็อก\nกดยืนยันเพื่อดำเนินการต่อน้าา",
                color=0x66BB6A,
            ),
            view=view,
            ephemeral=True,
        )


def setup(bot):
    bot.add_cog(Channels(bot))
