import database
import discord
from discord.ext import commands


class Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_name = '歡迎大廳'
        print("Program start")
    """
    When the program is executed, slashes command will be added to discord
    """

    @commands.Cog.listener()
    async def on_ready(self):
        # 同步 Slash 指令到 Discord
        await self.bot.tree.sync()

    """
    new member join
    """

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # 獲取歡迎頻道
        channel = discord.utils.get(member.guild.channels, name=self.welcome_name)
        if channel:
            # 創建嵌入消息
            embed = discord.Embed(
                title="➤加入通知",
                description=f"""
                歡迎 {member.display_name} 來到資管伺服器,
                請至驗證資訊頻道以獲得檢閱其他頻道權限的資訊。
                """,
                color=discord.Color.blue(),
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

        guest_role = discord.utils.get(member.guild.roles, name='訪客')
        if guest_role:
            await member.add_roles(guest_role)

    """
    member exit
    """

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = discord.utils.get(member.guild.channels, name=self.welcome_name)
        if channel:
            embed = discord.Embed(
                title="➤離開通知",
                description=f"""
                再見,{member.display_name},我們會想念你的。
                """,
                color=discord.Color.red(),
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)
        else:
            print("未找到指定的离开消息频道")

    """
    verify command instruction
    -- if verification is successful:
    1. Grant the member access.
    2. Force the member to change their nickname.
    3. Revoke the member's guest privileges.
    """

    @discord.app_commands.command(description="認證指令")
    @discord.app_commands.describe(name="請輸入本名")
    @discord.app_commands.checks.has_role('訪客')
    async def verify(self, interaction: discord.Interaction, name: str):

        # 發送私密消息
        if database.is_member(name) and interaction.guild:
            await interaction.response.send_message("驗證成功！", ephemeral=True)
            database.update_member_val(name)
            role = discord.utils.get(interaction.guild.roles, name="資管新生")
            if role:
                await interaction.user.edit(nick=f'113成員-{name}')
                await interaction.user.add_roles(role)
                await interaction.user.remove_roles(discord.utils.get(interaction.guild.roles, name='訪客'))
        else:
            await interaction.response.send_message(
                "驗證失敗，你不在新生名單上，請檢查是否有錯別字。若有疑慮請私訊會長", ephemeral=True)

    """
    add new member
    """

    @discord.app_commands.command(description="增加新成員指令")
    @discord.app_commands.checks.has_role('會長')
    async def add_new_member(self, interaction: discord.Interaction, name: str):
        if database.is_member(name):
            await interaction.response.send_message("此名稱已經存在", ephemeral=True)
        else:
            database.add_newMember(name)
            database.delete_member(name)
            await interaction.response.send_message("新增成功!", ephemeral=True)

    """
    get all the member data from database
    """

    @discord.app_commands.command(description="獲取資料庫所有成員")
    @discord.app_commands.checks.has_role('會長')
    async def get_all_member(self, interaction: discord.Interaction):
        members = database.get_all_members()
        await interaction.response.send_message(members, ephemeral=True)

    @discord.app_commands.command(description="清除所有成員")
    @discord.app_commands.checks.has_role('會長')
    async def remove_all_member(self, interaction: discord.Interaction):
        database.remove_all_member()
        await interaction.response.send_message("清除成功!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Cog(bot))
