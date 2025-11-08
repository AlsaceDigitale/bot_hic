from functools import cached_property
from typing import Optional
import asyncio

import discord
import requests
import structlog
from discord.errors import Forbidden
from discord.ext import tasks, commands

from extensions.base_cog import BaseCog, progress_message
from extensions.perms import is_support_user

log = structlog.get_logger()


class WelcomeCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    @cached_property
    def channel_welcome(self) -> discord.TextChannel:
        return self.settings.get_channel('WELCOME')

    async def cog_load(self):
        await super().cog_load()

        # Only start the automatic check task if WELCOME_MODE is 'open'
        if self.settings.WELCOME_MODE == 'open':
            log.info('starting check_attendees_task (WELCOME_MODE=open)')
            self.check_attendees_task.start()
        else:
            log.info('check_attendees_task disabled (WELCOME_MODE=close)')

    def _get_attendees_data(self):
        response = requests.get(f"{self.settings.URL_API}/api/attendees/", timeout=10)
        response.raise_for_status()
        
        # Handle empty response
        if not response.text.strip():
            log.error('attendees_api_empty_response')
            return []
        
        return response.json()
    
    async def _assign_discord_role(self, member: discord.Member, role_name: str, context: str = 'operation'):
        """
        Assigns a Discord role to a member.
        
        Returns:
            bool: True if role was assigned or already present, False otherwise
        """
        discord_role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), self.guild.roles)
        
        if not discord_role:
            log.warning(f'{context}_role_not_found', member=member.name, role_name=role_name)
            return False
        
        if discord_role in member.roles:
            log.info(f'{context}_role_already_assigned', member=member.name, role=discord_role.name)
            return True
        
        try:
            await member.add_roles(discord_role)
            log.info(f'{context}_role_assigned', member=member.name, role=discord_role.name)
            return True
        except Forbidden:
            log.warning(f'{context}_role_permission_denied', member=member.name, role_name=role_name)
            return False
    
    async def _finalize_member_link(self, ctx, member: discord.Member, attendee_id: int, email: str, role_name: str, context: str = 'operation'):
        """
        Finalizes member linking by assigning role, renaming, and sending welcome message.
        
        Returns:
            bool: True if role was assigned successfully
        """
        # Assign the Discord role
        role_assigned = await self._assign_discord_role(member, role_name, context)
        
        if not role_assigned:
            discord_role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), self.guild.roles)
            if not discord_role:
                await ctx.send(f"⚠️ Warning: Role `{role_name}` not found on Discord server.")
            else:
                await ctx.send(f"⚠️ Warning: Bot lacks permission to assign role `{role_name}`.")
        
        # Refresh attendee data and rename the member
        try:
            attendees = self._get_attendees_data()
            # Prioritize attendee_id lookup, fall back to email only if no ID
            if attendee_id:
                found_attendee_updated = next((att for att in attendees if att.get('id') == attendee_id), None)
            else:
                found_attendee_updated = next((att for att in attendees if att.get('email_address') == email), None)
            
            if found_attendee_updated:
                await self._rename_member(found_attendee_updated, member, pedantic=True)
            else:
                log.warning(f'{context}_attendee_not_found_for_rename', attendee_id=attendee_id, email=email)
        except Exception as e:
            # Don't fail the entire operation if rename fails
            log.error(f'{context}_rename_failed', member=member.name, exc_info=e)
        
        # Send welcome message to channel
        await self.channel_welcome.send(
            f"Bienvenue à {member.mention} sur le Discord du {self.settings.EVENT_NAME} !"
        )
        
        return role_assigned
    
    def _get_discord_username(self, member: discord.Member):
        """Returns the Discord username, handling the discriminator properly."""
        return f"{member.name}#{member.discriminator}" if member.discriminator != "0" else member.name

    async def welcome_member_helper(self, ctx, member: discord.Member, attendees_data=None, pedantic=True):
        if pedantic:
            log.info('welcome member', member=member.name, member_id=member.id)
        attendees = attendees_data or self._get_attendees_data()

        found_attendee = next((attendee for attendee in attendees if attendee["discord_unique_id"] == member.id), None)

        if found_attendee is None:
            if pedantic:
                log.warning('member not found in attendees list', member_id=member.id, member_name=member.name)
            return

        role: Optional[discord.Role] = None

        if found_attendee.get('role'):
            role = discord.utils.find(lambda r: r.name.lower() == found_attendee['role'].lower(),
                                      self.guild.roles)

        if role is None:
            if pedantic:
                log.warning('no role defined or found for member', member_name=member.name,
                            member_id=member.id)

        await self._rename_member(found_attendee, member, pedantic)

        if role and role not in member.roles:
            log.info('adding role to member', role=role.name, member=member.name)
            await member.add_roles(role)
            await self.channel_welcome.send(
                f"Bienvenue à {member.mention} sur le Discord du {self.settings.EVENT_NAME} !")

    async def _rename_member(self, found_attendee, member, pedantic=True):
        new_nick = f"{found_attendee['first_name'].title()} {found_attendee['last_name'][0].upper()}"
        
        # Discord nicknames must be 32 characters or fewer
        if len(new_nick) > 32:
            # Truncate the first name if needed, keeping at least the last name initial
            max_first_name_length = 30  # 32 - 1 (space) - 1 (last name initial)
            truncated_first_name = found_attendee['first_name'].title()[:max_first_name_length]
            new_nick = f"{truncated_first_name} {found_attendee['last_name'][0].upper()}"
            
        if member.nick != new_nick:
            try:
                if pedantic:
                    log.info('renaming member', first_name=found_attendee['first_name'],
                             last_name=found_attendee['last_name'],
                             new_nick=new_nick, nick_length=len(new_nick))
                await member.edit(nick=new_nick)
            except Forbidden:
                pass

    @commands.command(name='welcome_member')
    @commands.check(is_support_user)
    async def welcome_member(self, ctx, member: discord.Member):
        async with progress_message(ctx, f'welcome_member {member.mention}'):
            await self.welcome_member_helper(ctx, member)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.welcome_member_helper(None, member)

    @tasks.loop(minutes=5.0)
    async def check_attendees_task(self):
        await self.check_attendees()

    async def check_attendees(self):
        log.info('check_attendees')
        attendees = self._get_attendees_data()

        async for member in self.guild.fetch_members(limit=None):
            await self.welcome_member_helper(None, member, attendees, pedantic=False)

    @commands.command(name='check_attendees')
    @commands.check(is_support_user)
    async def check_attendees_command(self, ctx):
        async with progress_message(ctx, 'check attendees'):
            await self.check_attendees()

    @commands.command(name='change_nicks')
    @commands.check(is_support_user)
    async def change_nicks(self, ctx):
        async with progress_message(ctx, 'changing nicks'):
            attendees = self._get_attendees_data()

            async for member in self.guild.fetch_members(limit=None):
                found_attendee = next(
                    (attendee for attendee in attendees if attendee["discord_unique_id"] == member.id),
                    None)

                if found_attendee is None:
                    continue

                await self._rename_member(found_attendee, member)

    @commands.command(name='link_member')
    @commands.check(is_support_user)
    async def link_member(self, ctx, member: discord.Member, email: str, role_name: str = None):
        """
        Command: !link_member @user email@example.com [role_name]
        
        Manually links a Discord member to a backend attendee by email address.
        This updates the backend with the Discord user's information, assigns
        the specified role (or Participant by default), and renames them.
        
        Arguments:
        - @user: Discord member to link
        - email: Email address of the attendee in the backend
        - role_name: (Optional) Role to assign. Defaults to "Participant" (BOT_PARTICIPANT_ROLE setting)
        
        Use this when:
        - User was manually added to backend without OAuth
        - User joined Discord before completing registration
        - OAuth flow failed but user is on Discord
        
        Requires Support role.
        """
        async with progress_message(ctx, f'linking {member.mention} to {email}'):
            try:
                # Get all attendees
                attendees = self._get_attendees_data()
                
                # Find attendee by email
                found_attendee = next((att for att in attendees if att.get('email_address') == email), None)
                
                if found_attendee is None:
                    await ctx.send(f"❌ No attendee found with email `{email}` in the backend.")
                    return
                
                # Determine role to assign - use parameter, or default to Participant
                target_role_name = role_name or self.settings.PARTICIPANT_ROLE
                
                # Check if attendee is already linked to this Discord user
                if found_attendee.get('discord_unique_id') == member.id:
                    # Already linked to the same user - check if role would change
                    current_role = found_attendee.get('role', '')
                    
                    if current_role and current_role != target_role_name:
                        await ctx.send(
                            f"❌ Error: {member.mention} is already linked to `{email}` with role `{current_role}`. "
                            f"Cannot change to role `{target_role_name}`."
                        )
                        return
                    else:
                        await ctx.send(f"ℹ️ {member.mention} is already linked to `{email}`. No changes needed.")
                        return
                
                # Check if attendee is already linked to a DIFFERENT Discord user
                if found_attendee.get('discord_unique_id') and found_attendee['discord_unique_id'] != member.id:
                    existing_discord_username = found_attendee.get('discord_username', 'unknown')
                    await ctx.send(
                        f"⚠️ Warning: Attendee `{email}` is already linked to Discord user `{existing_discord_username}` "
                        f"(ID: {found_attendee['discord_unique_id']}). Proceeding will overwrite this link."
                    )
                
                # Update backend via API
                attendee_id = found_attendee['id']
                update_data = {
                    'discord_unique_id': member.id,
                    'discord_username': self._get_discord_username(member),
                    'status': 'JOINED',
                    'role': target_role_name,
                }
                
                response = requests.patch(
                    f"{self.settings.URL_API}/api/attendees/{attendee_id}/",
                    json=update_data,
                    timeout=10
                )
                
                if response.status_code not in [200, 204]:
                    await ctx.send(f"❌ Failed to update backend: {response.status_code} - {response.text}")
                    log.error('link_member_api_failed', status=response.status_code, response=response.text)
                    return
                
                log.info('link_member_success', member=member.name, member_id=member.id, email=email, attendee_id=attendee_id, role=target_role_name)
                
                # Finalize: assign role, rename, and welcome
                role_assigned = await self._finalize_member_link(ctx, member, attendee_id, email, target_role_name, 'link_member')
                
                # Build success message
                success_msg = f"✅ Successfully linked {member.mention} to attendee `{email}`\n"
                success_msg += "- Backend updated with Discord ID, username, and role\n"
                if role_assigned:
                    success_msg += f"- Discord role assigned: `{target_role_name}`"
                else:
                    success_msg += "- Discord role NOT assigned (see warning above)"
                
                await ctx.send(success_msg)
                
            except requests.exceptions.RequestException as e:
                await ctx.send(f"❌ Failed to connect to API: {str(e)}")
                log.error('link_member_api_error', exc_info=e)
            except Exception as e:
                await ctx.send(f"❌ Unexpected error: {str(e)}")
                log.error('link_member_error', exc_info=e)

    @link_member.error
    async def link_member_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('❌ Usage: `!link_member @member email@example.com [role_name]`')
        elif isinstance(error, commands.CheckFailure):
            await ctx.send('❌ You need the Support role to use this command.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('❌ Invalid arguments. Usage: `!link_member @member email@example.com [role_name]`')

    @commands.command(name='create_member')
    @commands.check(is_support_user)
    async def create_member(self, ctx, member: discord.Member, first_name: str, last_name: str, email: str, *, role_name: str = None):
        """
        Command: !create_member @user FirstName LastName email@example.com [role_name]
        
        Creates or updates a backend attendee and links them to a Discord member.
        
        Arguments:
        - @user: Discord member to link
        - first_name: First name of the attendee (no spaces allowed)
        - last_name: Last name of the attendee (no spaces allowed)
        - email: Email address (will be used to find/create attendee)
        - role_name: (Optional) Role to assign. Can contain spaces. Defaults to "Participant" (BOT_PARTICIPANT_ROLE setting)
        
        Success conditions:
        - Attendee doesn't exist in backend → Creates new attendee
        - Attendee exists but NOT linked to Discord → Updates and links
        
        Failure condition:
        - Attendee exists and is already linked to a DIFFERENT Discord user → Command fails
        
        Requires Support role.
        
        Note: For names with spaces, use quotes: !create_member @user "Jean-Pierre" "De La Fontaine" email@example.com
        """
        async with progress_message(ctx, f'creating/linking {member.mention}'):
            try:
                # Get all attendees
                attendees = self._get_attendees_data()
                
                # Find attendee by email
                found_attendee = next((att for att in attendees if att.get('email_address') == email), None)
                
                # Determine role to assign
                target_role_name = role_name or self.settings.PARTICIPANT_ROLE
                
                # Check if attendee exists and is linked to another Discord user
                if found_attendee:
                    existing_discord_id = found_attendee.get('discord_unique_id')
                    
                    # Case 1: Already linked to the SAME Discord user - prevent role change
                    if existing_discord_id == member.id:
                        current_role = found_attendee.get('role', '')
                        
                        if current_role and current_role != target_role_name:
                            await ctx.send(
                                f"❌ Error: {member.mention} is already linked to `{email}` with role `{current_role}`. "
                                f"Cannot change to role `{target_role_name}`."
                            )
                            return
                        else:
                            # Allow name updates if role stays the same
                            log.info('create_member_updating_existing', member=member.name, email=email)
                            # Continue to UPDATE section below
                    
                    # Case 2: Linked to a DIFFERENT Discord user - fail
                    elif existing_discord_id:
                        existing_discord_username = found_attendee.get('discord_username', 'unknown')
                        await ctx.send(
                            f"❌ **Command Failed**: Attendee with email `{email}` is already linked to Discord user `{existing_discord_username}` "
                            f"(ID: {existing_discord_id}).\n"
                            f"Cannot link to {member.mention} because the attendee is already associated with another Discord account."
                        )
                        log.warning('create_member_already_linked', 
                                   email=email, 
                                   existing_discord_id=existing_discord_id,
                                   existing_discord_username=existing_discord_username,
                                   attempted_member=member.name)
                        return
                    
                    # Attendee exists but not linked - UPDATE
                    attendee_id = found_attendee['id']
                    update_data = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'discord_unique_id': member.id,
                        'discord_username': self._get_discord_username(member),
                        'status': 'JOINED',
                        'role': target_role_name,
                    }
                    
                    response = requests.patch(
                        f"{self.settings.URL_API}/api/attendees/{attendee_id}/",
                        json=update_data,
                        timeout=10
                    )
                    
                    if response.status_code not in [200, 204]:
                        await ctx.send(f"❌ Failed to update backend: {response.status_code} - {response.text}")
                        log.error('create_member_update_failed', status=response.status_code, response=response.text)
                        return
                    
                    log.info('create_member_updated', member=member.name, member_id=member.id, email=email, attendee_id=attendee_id)
                    action_taken = "updated and linked"
                    
                else:
                    # Attendee doesn't exist - CREATE
                    create_data = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'email_address': email,
                        'discord_unique_id': member.id,
                        'discord_username': self._get_discord_username(member),
                        'status': 'JOINED',
                        'role': target_role_name,
                    }
                    
                    response = requests.post(
                        f"{self.settings.URL_API}/api/attendees/",
                        json=create_data,
                        timeout=10
                    )
                    
                    if response.status_code not in [200, 201]:
                        await ctx.send(f"❌ Failed to create attendee in backend: {response.status_code} - {response.text}")
                        log.error('create_member_create_failed', status=response.status_code, response=response.text)
                        return
                    
                    response_data = response.json()
                    attendee_id = response_data.get('id')
                    
                    if not attendee_id:
                        await ctx.send(f"⚠️ Warning: Attendee created but no ID returned. Will use email for lookup. Response: {response_data}")
                        log.warning('create_member_no_id', response=response_data)
                        attendee_id = None  # Explicitly set to None for clarity
                    
                    log.info('create_member_created', member=member.name, member_id=member.id, email=email, attendee_id=attendee_id)
                    action_taken = "created and linked"
                
                # Finalize: assign role, rename, and welcome
                role_assigned = await self._finalize_member_link(ctx, member, attendee_id, email, target_role_name, 'create_member')
                
                # Build success message
                success_msg = f"✅ Successfully {action_taken} {member.mention}\n"
                success_msg += f"- Name: {first_name} {last_name}\n"
                success_msg += f"- Email: {email}\n"
                success_msg += "- Backend status: JOINED\n"
                if role_assigned:
                    success_msg += f"- Discord role assigned: `{target_role_name}`"
                else:
                    success_msg += "- Discord role NOT assigned (see warning above)"
                
                await ctx.send(success_msg)
                
            except requests.exceptions.RequestException as e:
                await ctx.send(f"❌ Failed to connect to API: {str(e)}")
                log.error('create_member_api_error', exc_info=e)
            except Exception as e:
                await ctx.send(f"❌ Unexpected error: {str(e)}")
                log.error('create_member_error', exc_info=e)

    @create_member.error
    async def create_member_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('❌ Usage: `!create_member @member FirstName LastName email@example.com [role_name]`')
        elif isinstance(error, commands.CheckFailure):
            await ctx.send('❌ You need the Support role to use this command.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('❌ Invalid arguments. Usage: `!create_member @member FirstName LastName email@example.com [role_name]`')

    def _create_nudge_embed(self, member: discord.Member) -> discord.Embed:
        """
        Creates the nudge message embed for unidentified users.
        
        Args:
            member: The Discord member to create the message for
            
        Returns:
            discord.Embed: The formatted nudge message
        """
        embed = discord.Embed(
            title=f"🔔 Action requise - {self.settings.EVENT_NAME}",
            description=(
                f"Bonjour **{member.display_name}**,\n\n"
                f"Nous avons remarqué que vous avez rejoint le serveur Discord du **{self.settings.EVENT_NAME}**, "
                f"mais votre compte Discord n'est pas encore lié à votre inscription.\n\n"
                f"**Pour profiter pleinement de l'événement, merci de :**\n"
                f"1️⃣ Vérifier vos emails (y compris les spams/promotions)\n"
                f"2️⃣ Chercher l'email d'invitation du {self.settings.EVENT_NAME}\n"
                f"3️⃣ Cliquer sur le lien personnel dans cet email\n"
                f"4️⃣ Autoriser l'application Discord pour finaliser votre inscription\n\n"
                f"**Pourquoi c'est important ?**\n"
                f"✅ Recevoir votre rôle de participant automatiquement\n"
                f"✅ Être renommé(e) avec votre vrai nom\n"
                f"✅ Être pris(e) en compte pour le check-in\n"
                f"✅ Accéder à toutes les fonctionnalités de l'événement\n\n"
                f"Si vous n'avez pas reçu d'email ou si vous rencontrez des difficultés, "
                f"contactez l'équipe **{self.settings.ADMIN_ROLE}** sur le serveur."
            ),
            color=0xFFA500  # Orange color for attention
        )
        embed.set_footer(text=f"Message automatique du bot {self.settings.EVENT_NAME}")
        return embed

    @commands.command(name='nudge_unidentified_users')
    @commands.check(is_support_user)
    async def nudge_unidentified_users(self, ctx):
        """
        Command: !nudge_unidentified_users
        
        Sends a DM to all ONLINE Discord server members who have not been identified
        in the backend system (no discord_unique_id match).
        
        Offline users are skipped to avoid spamming inactive members.
        
        This reminds them to check their email and complete the OAuth flow
        to link their Discord account with their registration.
        
        Requires Support role.
        """
        async with progress_message(ctx, 'nudging unidentified users'):
            attendees = self._get_attendees_data()
            # Build set of identified Discord IDs, filtering out None values explicitly
            identified_discord_ids = {
                att['discord_unique_id'] 
                for att in attendees 
                if att.get('discord_unique_id') is not None
            }
            
            success_count = 0
            failed_count = 0
            skipped_bots = 0
            skipped_offline = 0
            notified_users = []  # Track successfully notified users
            
            async for member in self.guild.fetch_members(limit=None):
                # Skip bots
                if member.bot:
                    skipped_bots += 1
                    continue
                
                # Skip offline users
                if member.status == discord.Status.offline:
                    skipped_offline += 1
                    continue
                
                # Check if member is identified in the backend
                if member.id in identified_discord_ids:
                    continue
                
                # This member is not identified - send them a DM
                try:
                    dm_channel = member.dm_channel
                    if dm_channel is None:
                        dm_channel = await member.create_dm()
                    
                    embed = self._create_nudge_embed(member)
                    await dm_channel.send(embed=embed)
                    success_count += 1
                    notified_users.append(member)  # Add to list of notified users
                    log.info('nudge_dm_sent', member=member.name, member_id=member.id)
                    
                    # Rate limiting: wait 0.5 seconds between DMs to avoid hitting Discord limits
                    await asyncio.sleep(0.5)
                    
                except Forbidden:
                    # User has DMs disabled
                    failed_count += 1
                    log.warning('nudge_dm_failed_forbidden', member=member.name, member_id=member.id)
                except Exception as e:
                    failed_count += 1
                    log.error('nudge_dm_failed', member=member.name, member_id=member.id, exc_info=e)
            
            # Create a nice embed with summary
            result_embed = discord.Embed(
                title="📊 Nudge Report",
                description="Summary of unidentified users notification",
                color=0x00FF00 if success_count > 0 else 0xFF9900
            )
            
            result_embed.add_field(
                name="📈 Statistics",
                value=(
                    f"✅ DMs sent: **{success_count}**\n"
                    f"❌ Failed: **{failed_count}**\n"
                    f"💤 Offline (skipped): **{skipped_offline}**\n"
                    f"🤖 Bots (skipped): **{skipped_bots}**\n"
                    f"📝 Total unidentified online: **{success_count + failed_count}**"
                ),
                inline=False
            )
            
            result_embed.set_footer(text=f"Completed at {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            await ctx.send(embed=result_embed)
            
            # Create detailed user list embeds (without mentions to avoid pinging them)
            if notified_users:
                # Discord embed field has a 1024 character limit, embed description has 4096 limit
                # We'll use multiple embeds if needed, showing ~40 users per embed
                users_per_embed = 40
                total_embeds = (len(notified_users) + users_per_embed - 1) // users_per_embed
                
                for embed_index in range(total_embeds):
                    start_idx = embed_index * users_per_embed
                    end_idx = min(start_idx + users_per_embed, len(notified_users))
                    users_batch = notified_users[start_idx:end_idx]
                    
                    # Format usernames - use display name or username, NOT mentions
                    user_list = "\n".join([
                        f"• `{member.display_name}` (@{member.name})"
                        for member in users_batch
                    ])
                    
                    user_embed = discord.Embed(
                        title=f"✉️ Notified Users ({len(notified_users)} total)" if embed_index == 0 else f"✉️ Notified Users (continued)",
                        description=user_list,
                        color=0x5865F2  # Discord blurple
                    )
                    
                    user_embed.set_footer(text=f"Page {embed_index + 1}/{total_embeds}")
                    await ctx.send(embed=user_embed)
            
            log.info('nudge_complete', success=success_count, failed=failed_count, offline=skipped_offline, bots=skipped_bots)

    @commands.command(name='nudge_test')
    @commands.check(is_support_user)
    async def nudge_test(self, ctx):
        """
        Command: !nudge_test
        
        Sends the nudge message to the user invoking the command for testing purposes.
        This allows support users to preview the exact message that unidentified users will receive.
        
        Requires Support role.
        """
        author = ctx.author
        log.info('nudge_test', user=author.name, user_id=author.id)
        
        try:
            dm_channel = author.dm_channel
            if dm_channel is None:
                dm_channel = await author.create_dm()
            
            embed = self._create_nudge_embed(author)
            await dm_channel.send(embed=embed)
            await ctx.send(f"✅ Message de test envoyé en DM à {author.mention}")
            log.info('nudge_test_sent', user=author.name, user_id=author.id)
            
        except Forbidden:
            await ctx.send(f"❌ Impossible d'envoyer le DM - vérifiez que vos messages privés sont activés")
            log.warning('nudge_test_failed_forbidden', user=author.name, user_id=author.id)
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de l'envoi du message de test")
            log.error('nudge_test_failed', user=author.name, user_id=author.id, exc_info=e)


async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
