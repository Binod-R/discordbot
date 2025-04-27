import discord
from discord.ext import commands
from discord.ui import View, Select, Modal, TextInput, Button
import os


# Intents setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

# Staff role names (who can see tickets)
staff_roles_names = ["Staff", "Trial Staff", "High Command Staff", "Admin"]

# Ticket Modal (Form)
class TicketModal(Modal):
    def __init__(self, ticket_type):
        super().__init__(title=f"{ticket_type} Ticket")
        self.ticket_type = ticket_type

        # Label text depending on ticket type
        if ticket_type == "Redeem a Code":
            label_text = "Enter the code you want to redeem"
        elif ticket_type == "Claim a Reward":
            label_text = "Enter the service you want to claim"
        elif ticket_type == "Support":
            label_text = "Explain your issue"
        elif ticket_type == "Event Ticket":
            label_text = "Provide details about the event"
        else:
            label_text = "Provide details"

        self.add_item(TextInput(
            label=label_text,
            placeholder="Type here...",
            required=True,
            max_length=500
        ))

    async def on_submit(self, interaction: discord.Interaction):
       

        # Choose category name based on ticket type
        if self.ticket_type == "Redeem a Code":
            category_name = "Code"
        elif self.ticket_type == "Claim a Reward":
            category_name = "Reward"
        elif self.ticket_type == "Event Ticket":
            category_name = "Event"
        elif self.ticket_type == "Support":
            category_name = "Support"
        else:
            category_name = "🎟️ Other Tickets"

        # Find or create the category
        category = discord.utils.get(interaction.guild.categories, name=category_name)
        if category is None:
            print(f"❗ Category '{category_name}' not found, creating...")
            category = await interaction.guild.create_category(category_name)

        # Permissions
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        # Allow staff roles to see
        for role in interaction.guild.roles:
            if role.name in staff_roles_names:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # Create the ticket channel
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}".replace(" ", "-").lower(),
            category=category,
            overwrites=overwrites
        )

        # Embed message
        embed = discord.Embed(
            title=f"New Ticket - {self.ticket_type}",
            color=discord.Color.blue()
        )
        embed.add_field(name="User", value=interaction.user.mention, inline=False)
        embed.add_field(name="Details", value=self.children[0].value, inline=False)

        # Ticket View with Delete Button
        class TicketView(View):
            def __init__(self, channel):
                super().__init__()
                self.channel = channel

            @discord.ui.button(label="Delete Ticket", style=discord.ButtonStyle.danger)
            async def delete_ticket(self, interaction: discord.Interaction, button: Button):
                await self.channel.delete()
                try:
                    await interaction.response.send_message("✅ Ticket deleted!", ephemeral=True)
                except discord.NotFound:
                    pass  # Channel already deleted

        view = TicketView(channel)
        await channel.send(embed=embed, view=view)

        # Acknowledge user
        await interaction.response.send_message(f"🎟️ Your ticket has been created: {channel.mention}", ephemeral=True)

# Ticket Type Selection (Dropdown)
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Redeem a Code", description="Redeem your code!", emoji="🖊️"),
            discord.SelectOption(label="Claim a Reward", description="Claim your reward!", emoji="🎁"),
            discord.SelectOption(label="Event Ticket", description="Get your event reward!", emoji="🎟️"),
            discord.SelectOption(label="Support", description="Need help from staff?", emoji="❓"),
        ]
        super().__init__(placeholder="Choose a Ticket Type", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal(self.values[0]))

# View for Dropdown
class TicketDropdownView(View):
    def __init__(self):
        super().__init__()
        self.add_item(TicketSelect())

# Bot command to open ticket panel
@bot.command()
async def ticket(ctx):
    embed = discord.Embed(
        title="🎟️ Open a Ticket",
        description="Select the type of ticket you want to create!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=TicketDropdownView())

# Start the bot
bot.run(os.environ["DISCORD_TOKEN"])

