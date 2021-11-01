import re
import discord
from discord.ext import tasks, commands
from datetime import datetime

class AutoMessageCog(commands.Cog):
    guild = None
    messages = []

    channel_msg_auto = None

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if guild.name.startswith('Hacking Industry Camp'):
                self.guild = guild

        self.channel_msg_auto = discord.utils.find(lambda c: c.name == 'msg_auto', guild.channels)
        
        await self.loadMessagesAuto()
        self.send_msg_auto.start()

    def stripList(self, l):
        return list(map(lambda s : s.strip(), l))
    
    def checkNumber(self, text):
        try:
            val = int(text)
            
            if val >= 0:
                return val
            
            return None
        except ValueError:
            return None

    async def loadMessagesAuto(self):
        self.messages = []

        async for message in self.channel_msg_auto.history(limit=None):
            if len(message.reactions) > 0:
                continue

            content = message.content

            if '\n-----\n' not in content:
                print('Auto Message: Error 1')
                await message.add_reaction('👎')
                continue

            headers_body = self.stripList(content.split('\n-----\n', 1))

            if len(headers_body) != 2:
                print('Auto Message: Error 2')
                await message.add_reaction('👎')
                continue
            
            raw_headers, body = self.stripList(headers_body)

            if len(body) < 1:
                print('Auto Message: Error 3')
                await message.add_reaction('👎')
                continue

            obj = dict({
                'id' : message.id,
                'couleur': 2013674,
                'body': body
            })

            for raw_header in raw_headers.split('\n'):
                if ':' not in raw_header:
                    continue
                
                key, value = self.stripList(raw_header.split(':', 1))

                if key == '' or value == '':
                    continue

                if key == 'Date':
                    obj['date'] = datetime.strptime(value, '%d/%m/%Y %H:%M')
                elif key == 'Salons':
                    if ' ' in value:
                        obj['salons'] = list(map(lambda s : int(s[2:-1].strip()), value.split(' ')))
                    else:
                        obj[key.lower()] = [int(value[2:-1])]
                elif key == 'Couleur':
                    if re.search('^[0-9A-Fa-f]{6}$', value):
                        obj['couleur'] = int(f"0x{value}", 0)
                    else:
                        val = self.checkNumber(value)

                        if val is None:
                            print('Auto Message: Error 4')
                            await message.add_reaction('👎')
                            continue

                        obj['couleur'] = val
                else:
                    obj[key.lower()] = value

            if 'date' not in obj or 'salons' not in obj:
                print('Auto Message: Error 5')
                await message.add_reaction('👎')
                continue

            if obj['date'] <= datetime.now():
                await message.add_reaction('⏲')
                continue

            self.messages.append(obj)
    
    @tasks.loop(seconds=30.0)
    async def send_msg_auto(self):
        now = datetime.now().replace(second=0)
        print(now)

        print(self.messages)

        for index in range(len(self.messages)):
            message = self.messages[index]

            if message['date'] > now:
                continue

            embed = discord.Embed(
                colour=message['couleur'],
                description=message['body']
            )

            if 'titre' in message:
                embed.title = message['titre']

            for salon_id in message['salons']:
                salon = discord.utils.find(lambda c: c.id == salon_id, self.guild.channels)

                if salon is None:
                    continue

                await salon.send(embed=embed)

            await self.channel_msg_auto.get_partial_message(message['id']).add_reaction('👍')
            del self.messages[index]

        print(self.messages)

    @commands.Cog.listener()
    async def on_message(self, message):
        channel = message.channel

        if channel == self.channel_msg_auto:
            await self.loadMessagesAuto()

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        channel_id = payload.channel_id

        if channel_id == self.channel_msg_auto.id:
            await self.loadMessagesAuto()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        channel_id = payload.channel_id

        if channel_id == self.channel_msg_auto.id:
            await self.loadMessagesAuto()

def setup(bot):
    bot.add_cog(AutoMessageCog(bot))