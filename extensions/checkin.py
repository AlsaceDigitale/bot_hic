import discord
import requests
import structlog
import time
from discord.ext import commands

from extensions.base_cog import BaseCog
from extensions.perms import is_support_user

log = structlog.get_logger()


class CheckinCog(BaseCog):
    """Cog for checking in attendees at the physical event"""

    def __init__(self, bot):
        super().__init__(bot)
        self.api_url = None
        self.auto_checkin_enabled = False
        # Cache to track check-in status and avoid hammering the API
        self._checkin_cache = {}  # {member_id: 'pending' | 'checked' | timestamp}
        self._checkin_cooldown = 300  # 5 minutes cooldown between failed attempts
        self._event_dates_cache = None  # Cache event dates to avoid repeated API calls
        self._event_dates_last_check = 0  # Timestamp of last event dates check

    async def cog_load(self):
        await super().cog_load()
        self.api_url = self.settings.URL_API
        # Enable auto check-in if configured
        self.auto_checkin_enabled = getattr(self.settings, 'AUTO_CHECKIN_ENABLED', False)
        if self.auto_checkin_enabled:
            log.info('auto_checkin_enabled', mode='message_activity', cooldown=self._checkin_cooldown)
        else:
            log.info('auto_checkin_disabled')

    def _is_event_active(self) -> bool:
        """
        Check if the event is currently active based on start_date and end_date.
        
        Returns:
            bool: True if event is active or if no dates are configured (allow check-in anytime)
        
        Note:
            Currently returns True by default since the event API endpoint with start_date/end_date
            is not yet implemented. When available, this method will check actual event dates.
            Behavior: If no dates are set, auto check-in is allowed (permissive default).
        """
        current_time = time.time()
        
        # Refresh event dates cache every 5 minutes
        if current_time - self._event_dates_last_check > 300:
            try:
                # Fetch event info from API
                # Note: Currently no direct event endpoint with start_date/end_date exists
                # When implemented, add proper date checking here
                response = requests.get(
                    f"{self.api_url}/api/project-teams/",
                    timeout=5
                )
                
                if response.status_code == 200:
                    teams = response.json()
                    if teams and len(teams) > 0:
                        # Get event code from first team
                        event_code = teams[0].get('event')
                        if event_code:
                            # Assume event is always active for now
                            # This is safe - dates will be enforced when the endpoint is available
                            self._event_dates_cache = {'active': True}
                            self._event_dates_last_check = current_time
                            return True
            except (requests.exceptions.RequestException, ValueError, KeyError) as e:
                log.warning('event_dates_check_failed', error=str(e))
        
        # If we have cached dates, check them
        if self._event_dates_cache:
            return self._event_dates_cache.get('active', True)
        
        # No dates configured or cached - allow check-in anytime (safer default)
        log.debug('event_dates_not_configured', behavior='allow_checkin_anytime')
        return True

    async def _perform_checkin(self, member: discord.Member, checked_in_by: str) -> dict:
        """
        Internal method to perform check-in via API.
        
        Returns:
            dict with keys: success (bool), message (str), data (dict or None)
        """
        discord_username = f"{member.name}#{member.discriminator}" if member.discriminator != "0" else member.name
        
        payload = {
            'discord_username': discord_username,
            'discord_unique_id': member.id,
            'checked_in_by': checked_in_by
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/api/attendees/checkin/",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'already_checked_in':
                    return {
                        'success': True,
                        'already_checked': True,
                        'message': f"Already checked in at {data['checked_in_at']} by {data['checked_in_by']}",
                        'data': data
                    }
                else:
                    return {
                        'success': True,
                        'already_checked': False,
                        'message': f"Successfully checked in at {data['attendee']['checked_in_at']}",
                        'data': data
                    }
                    
            elif response.status_code == 404:
                return {
                    'success': False,
                    'message': 'Not found in attendee database',
                    'data': None
                }
            else:
                error_msg = response.json().get('error', 'Unknown error')
                return {
                    'success': False,
                    'message': f'API error: {error_msg}',
                    'data': None
                }
                
        except requests.exceptions.RequestException as e:
            log.error('checkin_api_error', error=str(e), member=member.name)
            return {
                'success': False,
                'message': f'Failed to connect to API: {str(e)}',
                'data': None
            }

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Automatically check in users when they send messages during the event.
        
        This listener monitors all messages and performs automatic check-in for users who:
        1. Are not bots
        2. Are members of the guild (not DMs)
        3. Have auto check-in enabled
        4. Event is currently active (or no dates configured)
        5. Haven't been checked in yet (cached as 'checked')
        6. Aren't in cooldown period after a failed check-in attempt
        """
        # Skip if auto check-in is disabled
        if not self.auto_checkin_enabled:
            return
        
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Only process guild messages (not DMs)
        if not message.guild:
            return
        
        # Check if event is currently active
        if not self._is_event_active():
            log.debug('auto_checkin_skipped_event_inactive', user=str(message.author))
            return
        
        member = message.author
        member_id = member.id
        
        # Check if already checked in (permanent state)
        cache_status = self._checkin_cache.get(member_id)
        if cache_status == 'checked':
            return  # Already checked in, no need to do anything
        
        # Check if in cooldown period after a failed attempt
        if isinstance(cache_status, (int, float)):
            if time.time() - cache_status < self._checkin_cooldown:
                return  # Still in cooldown
        
        # Check if already pending (avoid race conditions)
        if cache_status == 'pending':
            return  # Already processing this user
        
        # Mark as pending to avoid duplicate requests
        self._checkin_cache[member_id] = 'pending'
        
        try:
            # Perform the check-in (silent - no DM notification)
            result = await self._perform_checkin(member, 'Auto (Message Activity)')
            
            if result['success']:
                # Successfully checked in - cache permanently
                self._checkin_cache[member_id] = 'checked'
                log.info('auto_checkin_success', user=str(member), discord_id=member_id)
            else:
                # Failed - set cooldown timestamp
                self._checkin_cache[member_id] = time.time()
                log.debug('auto_checkin_failed', user=str(member), reason=result['message'])
        except Exception as e:
            # Error occurred - set cooldown timestamp
            self._checkin_cache[member_id] = time.time()
            log.error('auto_checkin_error', user=str(member), error=str(e))
        
        # Clean up old cooldown entries (keep only failures from last hour)
        current_time = time.time()
        self._checkin_cache = {
            k: v for k, v in self._checkin_cache.items()
            if v == 'checked' or v == 'pending' or 
            (isinstance(v, (int, float)) and current_time - v < 3600)
        }

    @commands.command(name='checkin')
    @commands.check(is_support_user)
    async def checkin(self, ctx, member: discord.Member):
        """
        Commande: !checkin
        Argument: @member
        
        Check in an attendee at the physical event.
        Requires Support role.
        """
        
        checked_in_by = f"{ctx.author.name}#{ctx.author.discriminator}" if ctx.author.discriminator != "0" else ctx.author.name
        result = await self._perform_checkin(member, checked_in_by)
        
        if result['success']:
            data = result['data']
            if result.get('already_checked'):
                await ctx.send(
                    f"✅ {member.mention} was already checked in at {data['checked_in_at']} "
                    f"by {data['checked_in_by']}"
                )
            else:
                await ctx.send(
                    f"✅ Successfully checked in {member.mention} ({data['attendee']['name']}) "
                    f"at {data['attendee']['checked_in_at']}"
                )
        else:
            if 'Not found' in result['message']:
                await ctx.send(
                    f"❌ {member.mention} not found in the attendee database. "
                    f"Make sure they have joined through the invitation system."
                )
            else:
                await ctx.send(f"⚠️ Error checking in {member.mention}: {result['message']}")

    @commands.command(name='checkin_status')
    @commands.check(is_support_user)
    async def checkin_status(self, ctx, member: discord.Member = None):
        """
        Commande: !checkin_status
        Argument: [@member] (optional)
        
        Check the check-in status of a member (or yourself if no member specified).
        Requires Support role.
        """
        
        target = member or ctx.author
        
        try:
            # Query the API with discord_unique_id filter
            response = requests.get(
                f"{self.api_url}/api/attendees/",
                params={'discord_unique_id': target.id},
                timeout=10
            )
            
            if response.status_code == 200:
                attendees = response.json()
                
                # API now supports filtering, but verify we got a result
                if attendees and len(attendees) > 0:
                    attendee = attendees[0]
                    
                    # Double-check we got the right person (in case of API issues)
                    if attendee.get('discord_unique_id') != target.id:
                        await ctx.send(f"⚠️ API returned unexpected data for {target.mention}")
                        log.error('checkin_status_mismatch', expected_id=target.id, got_id=attendee.get('discord_unique_id'))
                        return
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
                    await ctx.send(f"❌ {target.mention} not found in the attendee database.")
            else:
                await ctx.send("⚠️ Error fetching check-in status from API")
                
        except requests.exceptions.RequestException as e:
            await ctx.send(f"❌ Failed to connect to the API: {str(e)}")
            log.error('checkin_status_api_error', error=str(e), target=target.name)

    @checkin.error
    async def checkin_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Usage: !checkin @member')
        elif isinstance(error, commands.CheckFailure):
            await ctx.send('❌ You need the Support role to use this command.')

    @checkin_status.error
    async def checkin_status_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('❌ You need the Support role to use this command.')


async def setup(bot):
    await bot.add_cog(CheckinCog(bot))
