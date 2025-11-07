from functools import cached_property
from typing import Optional

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
        return requests.get(f"{self.settings.URL_API}/api/attendees/").json()

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
    async def check_attendees_command(self, ctx):
        async with progress_message(ctx, 'check attendees'):
            await self.check_attendees()

    @commands.command(name='change_nicks')
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
                
                # Check if attendee is already linked to another Discord user
                if found_attendee.get('discord_unique_id') and found_attendee['discord_unique_id'] != member.id:
                    existing_discord_username = found_attendee.get('discord_username', 'unknown')
                    await ctx.send(
                        f"⚠️ Warning: Attendee `{email}` is already linked to Discord user `{existing_discord_username}` "
                        f"(ID: {found_attendee['discord_unique_id']}). Proceeding will overwrite this link."
                    )
                
                # Determine role to assign - use parameter, or default to Participant
                target_role_name = role_name or self.settings.PARTICIPANT_ROLE
                
                # Update backend via API
                attendee_id = found_attendee['id']
                update_data = {
                    'discord_unique_id': member.id,
                    'discord_username': f"{member.name}#{member.discriminator}" if member.discriminator != "0" else member.name,
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
                
                # Assign the Discord role
                discord_role = discord.utils.find(lambda r: r.name.lower() == target_role_name.lower(), self.guild.roles)
                role_assigned = False
                
                if discord_role:
                    if discord_role not in member.roles:
                        try:
                            await member.add_roles(discord_role)
                            role_assigned = True
                            log.info('link_member_role_assigned', member=member.name, role=discord_role.name)
                        except Forbidden:
                            await ctx.send(f"⚠️ Warning: Bot lacks permission to assign role `{target_role_name}`. User linked but role not assigned.")
                            log.warning('link_member_role_permission_denied', member=member.name, role_name=target_role_name)
                    else:
                        role_assigned = True  # Already has the role
                        log.info('link_member_role_already_assigned', member=member.name, role=discord_role.name)
                else:
                    await ctx.send(f"⚠️ Warning: Role `{target_role_name}` not found on Discord server. User linked but role not assigned.")
                    log.warning('link_member_role_not_found', member=member.name, role_name=target_role_name)
                
                # Refresh attendee data and rename the member
                attendees = self._get_attendees_data()
                found_attendee_updated = next((att for att in attendees if att['id'] == attendee_id), None)
                
                if found_attendee_updated:
                    await self._rename_member(found_attendee_updated, member, pedantic=True)
                
                # Send welcome message to channel
                await self.channel_welcome.send(
                    f"Bienvenue à {member.mention} sur le Discord du {self.settings.EVENT_NAME} !"
                )
                
                # Build success message
                success_msg = f"✅ Successfully linked {member.mention} to attendee `{email}`\n"
                success_msg += f"- Backend updated with Discord ID, username, and role\n"
                if role_assigned:
                    success_msg += f"- Discord role assigned: `{target_role_name}`"
                else:
                    success_msg += f"- Discord role NOT assigned (see warning above)"
                
                await ctx.send(success_msg)
                
            except requests.exceptions.RequestException as e:
                await ctx.send(f"❌ Failed to connect to API: {str(e)}")
                log.error('link_member_api_error', exc_info=e)
            except Exception as e:
                await ctx.send(f"❌ Unexpected error: {str(e)}")
                log.error('link_member_error', exc_info=e)

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
                    if found_attendee.get('discord_unique_id') and found_attendee['discord_unique_id'] != member.id:
                        existing_discord_username = found_attendee.get('discord_username', 'unknown')
                        await ctx.send(
                            f"❌ **Command Failed**: Attendee with email `{email}` is already linked to Discord user `{existing_discord_username}` "
                            f"(ID: {found_attendee['discord_unique_id']}).\n"
                            f"Cannot link to {member.mention} because the attendee is already associated with another Discord account."
                        )
                        log.warning('create_member_already_linked', 
                                   email=email, 
                                   existing_discord_id=found_attendee['discord_unique_id'],
                                   existing_discord_username=existing_discord_username,
                                   attempted_member=member.name)
                        return
                    
                    # Attendee exists but not linked - UPDATE
                    attendee_id = found_attendee['id']
                    update_data = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'discord_unique_id': member.id,
                        'discord_username': f"{member.name}#{member.discriminator}" if member.discriminator != "0" else member.name,
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
                        'discord_username': f"{member.name}#{member.discriminator}" if member.discriminator != "0" else member.name,
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
                        await ctx.send(f"⚠️ Warning: Attendee created but no ID returned. Response: {response_data}")
                        log.warning('create_member_no_id', response=response_data)
                    
                    log.info('create_member_created', member=member.name, member_id=member.id, email=email, attendee_id=attendee_id)
                    action_taken = "created and linked"
                
                # Assign the Discord role
                discord_role = discord.utils.find(lambda r: r.name.lower() == target_role_name.lower(), self.guild.roles)
                role_assigned = False
                
                if discord_role:
                    if discord_role not in member.roles:
                        try:
                            await member.add_roles(discord_role)
                            role_assigned = True
                            log.info('create_member_role_assigned', member=member.name, role=discord_role.name)
                        except Forbidden:
                            await ctx.send(f"⚠️ Warning: Bot lacks permission to assign role `{target_role_name}`.")
                            log.warning('create_member_role_permission_denied', member=member.name, role_name=target_role_name)
                    else:
                        role_assigned = True
                        log.info('create_member_role_already_assigned', member=member.name, role=discord_role.name)
                else:
                    await ctx.send(f"⚠️ Warning: Role `{target_role_name}` not found on Discord server.")
                    log.warning('create_member_role_not_found', member=member.name, role_name=target_role_name)
                
                # Refresh attendee data and rename the member
                attendees = self._get_attendees_data()
                found_attendee_updated = next((att for att in attendees if att.get('email_address') == email), None)
                
                if found_attendee_updated:
                    await self._rename_member(found_attendee_updated, member, pedantic=True)
                
                # Send welcome message to channel
                await self.channel_welcome.send(
                    f"Bienvenue à {member.mention} sur le Discord du {self.settings.EVENT_NAME} !"
                )
                
                # Build success message
                success_msg = f"✅ Successfully {action_taken} {member.mention}\n"
                success_msg += f"- Name: {first_name} {last_name}\n"
                success_msg += f"- Email: {email}\n"
                success_msg += f"- Backend status: JOINED\n"
                if role_assigned:
                    success_msg += f"- Discord role assigned: `{target_role_name}`"
                else:
                    success_msg += f"- Discord role NOT assigned (see warning above)"
                
                await ctx.send(success_msg)
                
            except requests.exceptions.RequestException as e:
                await ctx.send(f"❌ Failed to connect to API: {str(e)}")
                log.error('create_member_api_error', exc_info=e)
            except Exception as e:
                await ctx.send(f"❌ Unexpected error: {str(e)}")
                log.error('create_member_error', exc_info=e)

    @commands.command(name='nudge_unidentified_users')
    @commands.check(is_support_user)
    async def nudge_unidentified_users(self, ctx):
        """
        Command: !nudge_unidentified_users
        
        Sends a DM to all Discord server members who have not been identified
        in the backend system (no discord_unique_id match).
        
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
            
            async for member in self.guild.fetch_members(limit=None):
                # Skip bots
                if member.bot:
                    skipped_bots += 1
                    continue
                
                # Check if member is identified in the backend
                if member.id in identified_discord_ids:
                    continue
                
                # This member is not identified - send them a DM
                try:
                    dm_channel = member.dm_channel
                    if dm_channel is None:
                        dm_channel = await member.create_dm()
                    
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
                    
                    await dm_channel.send(embed=embed)
                    success_count += 1
                    log.info('nudge_dm_sent', member=member.name, member_id=member.id)
                    
                except Forbidden:
                    # User has DMs disabled
                    failed_count += 1
                    log.warning('nudge_dm_failed_forbidden', member=member.name, member_id=member.id)
                except Exception as e:
                    failed_count += 1
                    log.error('nudge_dm_failed', member=member.name, member_id=member.id, exc_info=e)
            
            # Send summary to the channel
            summary = (
                f"📊 **Nudge Summary:**\n"
                f"✅ DMs sent: {success_count}\n"
                f"❌ Failed (DMs disabled or error): {failed_count}\n"
                f"🤖 Bots skipped: {skipped_bots}\n"
                f"📝 Total unidentified: {success_count + failed_count}"
            )
            await ctx.send(summary)
            log.info('nudge_complete', success=success_count, failed=failed_count, bots=skipped_bots)


async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
