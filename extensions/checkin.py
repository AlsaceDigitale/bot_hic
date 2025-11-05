import discord
import requests
from discord.ext import commands

from extensions.base_cog import BaseCog


class CheckinCog(BaseCog):
    """Cog for checking in attendees at the physical event"""

    def __init__(self, bot):
        super().__init__(bot)
        self.api_url = None

    async def cog_load(self):
        await super().cog_load()
        self.api_url = self.settings.URL_API

    @commands.command(name='checkin')
    @commands.check(lambda ctx: BaseCog.is_support_user(ctx))
    async def checkin(self, ctx, member: discord.Member):
        """
        Commande: !checkin
        Argument: @member
        
        Check in an attendee at the physical event.
        Requires Support role.
        """
        
        # Get the Discord username in the format used by the API
        discord_username = f"{member.name}#{member.discriminator}" if member.discriminator != "0" else member.name
        
        # Prepare the API request
        payload = {
            'discord_username': discord_username,
            'discord_unique_id': member.id,
            'checked_in_by': f"{ctx.author.name}#{ctx.author.discriminator}" if ctx.author.discriminator != "0" else ctx.author.name
        }
        
        try:
            # Call the check-in API
            response = requests.post(
                f"{self.api_url}/api/attendees/checkin/",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'already_checked_in':
                    await ctx.send(
                        f"✅ {member.mention} was already checked in at {data['checked_in_at']} "
                        f"by {data['checked_in_by']}"
                    )
                else:
                    await ctx.send(
                        f"✅ Successfully checked in {member.mention} ({data['attendee']['name']}) "
                        f"at {data['attendee']['checked_in_at']}"
                    )
                    
            elif response.status_code == 404:
                await ctx.send(
                    f"❌ {member.mention} not found in the attendee database. "
                    f"Make sure they have joined through the invitation system."
                )
            else:
                await ctx.send(
                    f"⚠️ Error checking in {member.mention}: {response.json().get('error', 'Unknown error')}"
                )
                
        except requests.exceptions.RequestException as e:
            await ctx.send(f"❌ Failed to connect to the API: {str(e)}")
            self.logger.error(f"Check-in API error: {e}")

    @commands.command(name='checkin_status')
    async def checkin_status(self, ctx, member: discord.Member = None):
        """
        Commande: !checkin_status
        Argument: [@member] (optional)
        
        Check the check-in status of a member (or yourself if no member specified).
        """
        
        target = member or ctx.author
        discord_username = f"{target.name}#{target.discriminator}" if target.discriminator != "0" else target.name
        
        try:
            # Query the API for attendee info
            response = requests.get(
                f"{self.api_url}/api/attendees/",
                params={'discord_unique_id': target.id},
                timeout=10
            )
            
            if response.status_code == 200:
                attendees = response.json()
                if attendees and len(attendees) > 0:
                    attendee = attendees[0]
                    
                    embed = discord.Embed(
                        title=f"Check-in Status for {target.display_name}",
                        color=discord.Color.green() if attendee.get('checked_in_at') else discord.Color.orange()
                    )
                    
                    embed.add_field(name="Name", value=f"{attendee.get('first_name')} {attendee.get('last_name')}", inline=True)
                    embed.add_field(name="Role", value=attendee.get('role', 'N/A'), inline=True)
                    
                    if attendee.get('checked_in_at'):
                        embed.add_field(name="✅ Checked In", value=attendee['checked_in_at'], inline=False)
                        if attendee.get('checked_in_by'):
                            embed.add_field(name="Checked In By", value=attendee['checked_in_by'], inline=True)
                    else:
                        embed.add_field(name="Status", value="❌ Not checked in yet", inline=False)
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"{target.mention} not found in the attendee database.")
            else:
                await ctx.send(f"⚠️ Error fetching check-in status")
                
        except requests.exceptions.RequestException as e:
            await ctx.send(f"❌ Failed to connect to the API: {str(e)}")
            self.logger.error(f"Check-in status API error: {e}")

    @checkin.error
    async def checkin_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Usage: !checkin @member')
        elif isinstance(error, commands.CheckFailure):
            await ctx.send('❌ You need the Support role to use this command.')


async def setup(bot):
    await bot.add_cog(CheckinCog(bot))
