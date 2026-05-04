import discord
from datetime import datetime
from config import (DEFAULT_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR,
                    INFO_COLOR, MUSIC_COLOR, SECURITY_COLOR, MOD_COLOR,
                    ANNOUNCE_COLOR, WELCOME_COLOR, BOT_VERSION, BOT_UPDATE_DATE)


def base_embed(title: str, description: str = "", color: int = DEFAULT_COLOR) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.timestamp = datetime.utcnow()
    embed.set_footer(text=f"✨ บอทระบบ v{BOT_VERSION} • พร้อมใช้งานเต็มที่น้าา")
    return embed


def success_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"✅ {title}", description, SUCCESS_COLOR)


def error_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"❌ {title}", description, ERROR_COLOR)


def warning_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"⚠️ {title}", description, WARNING_COLOR)


def info_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"ℹ️ {title}", description, INFO_COLOR)


def music_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"🎵 {title}", description, MUSIC_COLOR)


def security_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"🛡️ {title}", description, SECURITY_COLOR)


def mod_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"👮 {title}", description, MOD_COLOR)


def announce_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"📢 {title}", description, ANNOUNCE_COLOR)


def welcome_embed(title: str, description: str = "") -> discord.Embed:
    return base_embed(f"👋 {title}", description, WELCOME_COLOR)


def status_indicator(enabled: bool) -> str:
    return "🟢 เปิดอยู่" if enabled else "🔴 ปิดอยู่"


def build_dashboard_embed(guild: discord.Guild, bot: discord.Bot, settings: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🏠 ศูนย์ควบคุมหลัก",
        description=(
            f"สวัสดีน้าา! 👋✨ ยินดีต้อนรับสู่แผงควบคุมหลักของ **{guild.name}**\n"
            f"จัดการทุกระบบได้จากที่นี่เลยยย — เพลง ความปลอดภัย สมาชิก และอื่นๆ อีกเพียบ 💖"
        ),
        color=DEFAULT_COLOR
    )

    online_count = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
    voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
    locked_channels = len([c for c in guild.channels if
                           isinstance(c, (discord.TextChannel, discord.VoiceChannel)) and
                           not c.permissions_for(guild.default_role).view_channel])
    boost_level = guild.premium_tier
    boost_count = guild.premium_subscription_count or 0

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(
        name="📌 ข้อมูลเซิร์ฟเวอร์",
        value=(
            f"🏷️ **ชื่อ:** {guild.name}\n"
            f"👑 **เจ้าของ:** {guild.owner.mention if guild.owner else 'ไม่ทราบ'}\n"
            f"📅 **สร้างเมื่อ:** {guild.created_at.strftime('%d/%m/%Y')}\n"
            f"💎 **Boost:** Lv.{boost_level} ({boost_count} บูสต์)"
        ),
        inline=True
    )

    embed.add_field(
        name="👥 สถานะสมาชิก",
        value=(
            f"👥 **ทั้งหมด:** {guild.member_count:,} คน\n"
            f"🟢 **ออนไลน์:** {online_count:,} คน\n"
            f"🤖 **บอท:** {sum(1 for m in guild.members if m.bot)} ตัว\n"
            f"🧩 **ยศ:** {len(guild.roles)} ยศ"
        ),
        inline=True
    )

    embed.add_field(
        name="📊 ห้องในเซิร์ฟเวอร์",
        value=(
            f"💬 **ข้อความ:** {text_channels} ห้อง\n"
            f"🎙️ **เสียง:** {voice_channels} ห้อง\n"
            f"🔒 **ซ่อน:** {locked_channels} ห้อง\n"
            f"📦 **ทั้งหมด:** {len(guild.channels)} ห้อง"
        ),
        inline=True
    )

    systems = [
        ("👋", "ต้อนรับ", settings.get('welcome_enabled', False)),
        ("✅", "ยืนยัน", settings.get('verify_enabled', False)),
        ("🎁", "รับยศ", settings.get('roles_enabled', False)),
        ("🧾", "ล็อก", settings.get('log_enabled', False)),
        ("🛡️", "กันสแปม", settings.get('antispam_enabled', False)),
        ("🎵", "เพลง", settings.get('music_enabled', False)),
        ("📢", "ประกาศ", settings.get('announce_enabled', False)),
        ("⚡", "เลเวล", settings.get('levels_enabled', False)),
    ]
    sys_text = " • ".join(
        f"{'🟢' if on else '🔴'} {name}" for _, name, on in systems
    )
    embed.add_field(name="⚙️ สถานะระบบทั้งหมด", value=sys_text, inline=False)

    uptime = datetime.utcnow() - bot.start_time if hasattr(bot, 'start_time') else None
    uptime_str = str(uptime).split('.')[0] if uptime else "กำลังเริ่ม..."
    latency = round(bot.latency * 1000)
    latency_icon = "🟢" if latency < 100 else ("🟡" if latency < 300 else "🔴")

    embed.add_field(
        name="🤖 ข้อมูลบอท",
        value=(
            f"🤖 **ชื่อ:** {bot.user.name}\n"
            f"⏱️ **ทำงานมาแล้ว:** {uptime_str}\n"
            f"{latency_icon} **ดีเลย์:** {latency}ms\n"
            f"📦 **เวอร์ชัน:** v{BOT_VERSION}"
        ),
        inline=True
    )

    embed.timestamp = datetime.utcnow()
    embed.set_footer(text=f"🤖 {bot.user.name} • อัปเดต {BOT_UPDATE_DATE} • พร้อมใช้งาน ✅")
    return embed


def build_music_embed(guild: discord.Guild, settings: dict, current_track=None) -> discord.Embed:
    embed = discord.Embed(
        title="🎵 ศูนย์ควบคุมเพลง",
        description=(
            "🎶 จัดการเพลง คิว เสียง โหมด EQ ได้ทั้งหมดจากที่นี่เลยน้าา 💖\n"
            "กดปุ่มด้านล่างเพื่อเริ่มได้เลยยย ✨"
        ),
        color=MUSIC_COLOR
    )
    music_ch = settings.get('music_command_channel')
    control_ch = settings.get('music_control_channel')

    embed.add_field(
        name="⚙️ สถานะระบบ",
        value=(
            f"🎵 ระบบเพลง: {status_indicator(settings.get('music_enabled', False))}\n"
            f"📍 ห้องคำสั่ง: {'<#' + str(music_ch) + '>' if music_ch else '⚙️ ยังไม่ตั้งค่า'}\n"
            f"🎛️ ห้องควบคุม: {'<#' + str(control_ch) + '>' if control_ch else '⚙️ ยังไม่ตั้งค่า'}\n"
            f"🔊 เสียง: {settings.get('volume', 70)}%\n"
            f"🔁 วนซ้ำ: {status_indicator(settings.get('loop', False))}\n"
            f"🔀 สุ่ม: {status_indicator(settings.get('shuffle', False))}"
        ),
        inline=True
    )

    if current_track:
        embed.add_field(
            name="🎶 กำลังเล่นอยู่ตอนนี้",
            value=(
                f"🎵 **{current_track.get('title', 'ไม่ทราบ')[:45]}**\n"
                f"👤 ขอโดย: {current_track.get('requester', '?')}\n"
                f"⏱️ ความยาว: {current_track.get('duration', '00:00')}\n"
                f"📋 คิวถัดไป: {current_track.get('queue_length', 0)} เพลง"
            ),
            inline=True
        )
    else:
        embed.add_field(
            name="🎶 สถานะเพลง",
            value="⏸️ ยังไม่มีเพลงเล่นอยู่น้าา\nกด **🎵 เพิ่มเพลง** เพื่อเริ่มต้นเลยยย 👇",
            inline=True
        )

    embed.set_footer(text="🎵 กดปุ่มด้านล่างเพื่อควบคุม • ใช้ /เล่นเพลง เพื่อเพิ่มเพลงน้าา")
    embed.timestamp = datetime.utcnow()
    return embed


def build_welcome_embed(settings: dict) -> discord.Embed:
    embed = discord.Embed(
        title="👋 ระบบต้อนรับสมาชิกใหม่",
        description="ตั้งค่าข้อความต้อนรับ รูปต้อนรับ ห้อง และยศอัตโนมัติได้จากหน้านี้เลยน้าา 💖",
        color=WELCOME_COLOR
    )
    welcome_ch = settings.get('welcome_channel')
    farewell_ch = settings.get('farewell_channel')
    auto_role = settings.get('auto_role')

    embed.add_field(
        name="✅ สถานะต้อนรับ",
        value=(
            f"👋 ระบบต้อนรับ: {status_indicator(settings.get('welcome_enabled', False))}\n"
            f"📍 ห้องต้อนรับ: {'<#' + str(welcome_ch) + '>' if welcome_ch else '⚙️ ยังไม่ตั้งค่า'}\n"
            f"🎁 ยศอัตโนมัติ: {'<@&' + str(auto_role) + '>' if auto_role else '⚙️ ยังไม่ตั้งค่า'}\n"
            f"🖼️ รูปต้อนรับ: {status_indicator(settings.get('welcome_image', False))}\n"
            f"💌 DM ต้อนรับ: {status_indicator(settings.get('dm_welcome', False))}"
        ),
        inline=True
    )

    embed.add_field(
        name="🚪 สถานะอำลา",
        value=(
            f"✅ ระบบอำลา: {status_indicator(settings.get('farewell_enabled', False))}\n"
            f"📍 ห้องอำลา: {'<#' + str(farewell_ch) + '>' if farewell_ch else '⚙️ ยังไม่ตั้งค่า'}\n"
            f"🖼️ รูปอำลา: {status_indicator(settings.get('farewell_image', False))}\n"
            f"✍️ ข้อความอำลา: {'ตั้งค่าแล้ว ✅' if settings.get('farewell_message') else '⚙️ ยังไม่ตั้งค่า'}"
        ),
        inline=True
    )

    embed.timestamp = datetime.utcnow()
    return embed


def build_security_embed(settings: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🛡️ ศูนย์ความปลอดภัย",
        description=(
            "ป้องกันสแปม คำหยาบ ลิงก์อันตราย และการโจมตีได้จากที่นี่เลยน้าา 💪\n"
            "ตั้งค่าให้ตรงกับเซิร์ฟเวอร์ของคุณได้เลยยย ✨"
        ),
        color=SECURITY_COLOR
    )
    level = settings.get('security_level', 'กลาง')
    level_map = {"ต่ำ": "🔻 ต่ำ", "กลาง": "🔸 กลาง", "สูง": "🔺 สูง", "โหด": "☠️ โหดสุดๆ"}
    level_display = level_map.get(level, "🔸 กลาง")

    embed.add_field(
        name="📊 ภาพรวมระบบ",
        value=(
            f"🛡️ ระบบความปลอดภัย: {status_indicator(settings.get('security_enabled', False))}\n"
            f"🚨 แจ้งเตือนภัย: {status_indicator(settings.get('security_alerts', False))}\n"
            f"⚡ ระดับความเข้ม: {level_display}\n"
            f"🚨 โหมดฉุกเฉิน: {status_indicator(settings.get('emergency_mode', False))}"
        ),
        inline=True
    )

    embed.add_field(
        name="🔰 ระบบป้องกัน",
        value=(
            f"💬 กันสแปม: {status_indicator(settings.get('antispam_enabled', False))}\n"
            f"🤬 กรองคำหยาบ: {status_indicator(settings.get('antiswear_enabled', False))}\n"
            f"🔗 กันลิงก์เสี่ยง: {status_indicator(settings.get('antilink_enabled', False))}\n"
            f"🤖 กัน Raid: {status_indicator(settings.get('antiraid_enabled', False))}"
        ),
        inline=True
    )

    embed.timestamp = datetime.utcnow()
    return embed


def build_verify_embed(settings: dict) -> discord.Embed:
    verify_ch = settings.get('verify_channel')
    verify_role = settings.get('verify_role')
    mode = settings.get('verify_mode', 'ปุ่มกด')

    embed = discord.Embed(
        title="✅ ระบบยืนยันตัวตน",
        description=(
            "🔐 ยืนยันตัวตนเพื่อปลดล็อกห้องและเริ่มใช้งานเซิร์ฟเวอร์ได้เต็มที่น้าา 💖\n"
            "กดปุ่มด้านล่างเพื่อตั้งค่าได้เลยยย ✨"
        ),
        color=SUCCESS_COLOR
    )

    embed.add_field(
        name="📋 สถานะระบบ",
        value=(
            f"✅ ระบบยืนยัน: {status_indicator(settings.get('verify_enabled', False))}\n"
            f"📍 ห้องยืนยัน: {'<#' + str(verify_ch) + '>' if verify_ch else '⚙️ ยังไม่ตั้งค่า'}\n"
            f"🎁 ยศหลังยืนยัน: {'<@&' + str(verify_role) + '>' if verify_role else '⚙️ ยังไม่ตั้งค่า'}\n"
            f"🛡️ กันบอท: {status_indicator(settings.get('verify_antibot', True))}\n"
            f"🎯 โหมด: {mode}"
        ),
        inline=False
    )

    embed.timestamp = datetime.utcnow()
    return embed


def build_mod_embed(member: discord.Member = None) -> discord.Embed:
    embed = discord.Embed(
        title="👮 ระบบจัดการสมาชิก",
        description="ดูข้อมูล เตะ แบน มิวท์ เตือน และดูประวัติสมาชิกได้จากหน้านี้น้าา 💖",
        color=MOD_COLOR
    )

    if member:
        roles = [r.mention for r in member.roles if r.name != "@everyone"][:5]
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="👤 ข้อมูลสมาชิก",
            value=(
                f"**ชื่อ:** {member.display_name}\n"
                f"**แท็ก:** {member}\n"
                f"**ไอดี:** `{member.id}`\n"
                f"**เข้าร่วม:** {member.joined_at.strftime('%d/%m/%Y') if member.joined_at else 'ไม่ทราบ'}\n"
                f"**สมัคร Discord:** {member.created_at.strftime('%d/%m/%Y')}\n"
                f"**ยศ:** {', '.join(roles) if roles else 'ไม่มียศ'}"
            ),
            inline=False
        )
    else:
        embed.add_field(
            name="📋 คำแนะนำ",
            value="ใช้ `/จัดการสมาชิก @ชื่อสมาชิก` เพื่อดูข้อมูลและจัดการสมาชิกได้เลยน้าา 💡",
            inline=False
        )

    embed.timestamp = datetime.utcnow()
    return embed


def build_log_embed(settings: dict) -> discord.Embed:
    log_ch = settings.get('log_channel')
    embed = discord.Embed(
        title="🧾 ระบบบันทึกกิจกรรม",
        description=(
            "บันทึกเหตุการณ์สำคัญทั้งหมดไว้ที่ห้องล็อก\n"
            "ตรวจย้อนหลัง ดูรายละเอียด และค้นหาได้ทุกเวลาน้าา 🔍"
        ),
        color=INFO_COLOR
    )

    categories = [
        ("💬 ข้อความ", settings.get('log_messages', False)),
        ("👤 สมาชิก", settings.get('log_members', False)),
        ("🏗️ ห้อง", settings.get('log_channels', False)),
        ("🧩 ยศ", settings.get('log_roles', False)),
        ("🔨 ลงโทษ", settings.get('log_mod', False)),
        ("🎙️ เสียง", settings.get('log_voice', False)),
    ]

    cats_text = "\n".join([f"{name}: {status_indicator(enabled)}" for name, enabled in categories])

    embed.add_field(
        name="📊 สถานะ",
        value=(
            f"🧾 ระบบล็อก: {status_indicator(settings.get('log_enabled', False))}\n"
            f"📍 ห้องล็อก: {'<#' + str(log_ch) + '>' if log_ch else '⚙️ ยังไม่ตั้งค่า'}\n"
            f"🔍 โหมดละเอียด: {status_indicator(settings.get('log_detailed', False))}"
        ),
        inline=True
    )

    embed.add_field(name="📋 หมวดที่เปิด", value=cats_text, inline=True)

    embed.timestamp = datetime.utcnow()
    return embed


def build_announce_embed(settings: dict) -> discord.Embed:
    announce_ch = settings.get('announce_channel')
    embed = discord.Embed(
        title="📢 ศูนย์ประกาศ",
        description=(
            "สร้างประกาศสวยๆ ส่งทันทีหรือกำหนดเวลาล่วงหน้าได้น้าา 📣✨\n"
            "มีเทมเพลตให้เลือกเพียบเลยยย 💖"
        ),
        color=ANNOUNCE_COLOR
    )

    embed.add_field(
        name="📊 สถานะ",
        value=(
            f"✅ ระบบประกาศ: {status_indicator(settings.get('announce_enabled', False))}\n"
            f"📍 ห้องประกาศ: {'<#' + str(announce_ch) + '>' if announce_ch else '⚙️ ยังไม่ตั้งค่า'}\n"
            f"⏰ ตั้งเวลา: {status_indicator(True)}\n"
            f"🖼️ ใส่รูปได้: {status_indicator(True)}\n"
            f"📌 ปักหมุดอัตโนมัติ: {status_indicator(settings.get('announce_pin', False))}"
        ),
        inline=False
    )

    embed.timestamp = datetime.utcnow()
    return embed


def build_channel_embed(guild: discord.Guild, settings: dict) -> discord.Embed:
    text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
    voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
    locked = len([c for c in guild.channels if
                  isinstance(c, (discord.TextChannel, discord.VoiceChannel)) and
                  not c.permissions_for(guild.default_role).send_messages])
    hidden = len([c for c in guild.channels if
                  isinstance(c, (discord.TextChannel, discord.VoiceChannel)) and
                  not c.permissions_for(guild.default_role).view_channel])

    embed = discord.Embed(
        title="🏗️ ศูนย์จัดการห้อง",
        description="สร้าง ลบ ล็อก ซ่อน และตั้งสิทธิ์ห้องได้จากที่นี่น้าา 💖",
        color=0x78909C
    )

    embed.add_field(
        name="📊 ข้อมูลห้อง",
        value=(
            f"📦 ทั้งหมด: {len(guild.channels)} ห้อง\n"
            f"💬 ข้อความ: {text_channels} ห้อง\n"
            f"🎙️ เสียง: {voice_channels} ห้อง\n"
            f"🔒 ล็อก: {locked} ห้อง\n"
            f"👁️ ซ่อน: {hidden} ห้อง\n"
            f"🤖 Auto Room: {status_indicator(settings.get('autoroom_enabled', False))}"
        ),
        inline=False
    )

    embed.timestamp = datetime.utcnow()
    return embed


def build_roles_embed(guild: discord.Guild, settings: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🎁 ระบบรับยศ",
        description="เลือกยศที่ตรงกับความสนใจของคุณ กดครั้งเดียวก็รับได้ทันทีเลยน้าา 💖✨",
        color=0xFFD700
    )

    role_categories = settings.get('role_categories', {})
    cat_count = len(role_categories)
    role_count = sum(len(v.get('roles', [])) for v in role_categories.values())

    embed.add_field(
        name="📊 ข้อมูลระบบยศ",
        value=(
            f"📁 หมวดยศ: {cat_count} หมวด\n"
            f"🧩 ยศทั้งหมด: {role_count} ยศ\n"
            f"✅ รับได้เอง: {status_indicator(settings.get('selfrole_enabled', True))}"
        ),
        inline=False
    )

    if role_categories:
        emojis = ["🎮", "🎨", "🔔", "💎", "🌟"]
        cats_text = "\n".join([f"{emojis[i % len(emojis)]} {name}"
                               for i, name in enumerate(list(role_categories.keys())[:5])])
        embed.add_field(name="📋 หมวดยศที่มี", value=cats_text or "ยังไม่มีหมวดยศน้าา", inline=False)

    embed.timestamp = datetime.utcnow()
    return embed


def format_duration(seconds: int) -> str:
    if seconds is None:
        return "ไม่ทราบ"
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def progress_bar(current: int, total: int, length: int = 10) -> str:
    if total == 0:
        return "▱" * length
    filled = int((current / total) * length)
    return "█" * filled + "░" * (length - filled)
