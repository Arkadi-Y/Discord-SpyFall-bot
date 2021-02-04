import asyncio
import random
import discord
import json
from player_class import Player
from discord.ext import commands
from disToken import tok

client = commands.Bot(command_prefix='.')

global game


@client.event
async def on_ready():
    print('SpyFall ready')


class SpyFall:
    def __init__(self, ctx):
        super(SpyFall, self).__init__()
        self.ctx = ctx
        self.bot = commands.Bot(command_prefix='!')
        self.roundtime = 10 * 60
        self.location = getLocation()
        self.spy = ''
        self.players = []
        self.time = ''

    async def endRound(self, user):
        if user == 'time-out':
            await self.ctx.send("Game over - the spy wasn't caught" + self.spy.name + " wins")
        elif user == self.spy:
            await self.ctx.send(user.display_name + " was the spy")
        else:
            await self.ctx.send(str(self.spy.name) + " was the spy")
        self.roundtime = 0
        await self.nextRound()

    async def assignRoles(self):
        await self.checkForNewPlayers()
        if len(self.location['roles']) < len(self.players):
            self.location = getLocation()
            await self.assignRoles()
        else:
            self.spy = random.choice(self.players)
            await DM(self.spy.name, 'you are the spy')
            try:
                self.players.remove(self.spy)
            except ValueError:
                print("no spy in player list")
            for player in self.players:
                job = random.choice(self.location['roles'])
                try:
                    self.location['roles'].remove(job)
                except ValueError:
                    print('no ' + job)
                finally:
                    player.setRole(job)
                    message = 'the location is -' + self.location['title'] + '\n and you are the ' + job
                    await DM(player.name, message)

    async def checkForNewPlayers(self):
        playerList = await getVoiceUsers(self.ctx)
        for player in self.players:
            try:
                exists = playerList.index(player.name)
                playerList.remove(exists)
            except ValueError:
                self.players.remove(player)
        for user in playerList:
            self.players.append(Player(user))

    async def nextRound(self):
        await self.ctx.send("new round in 10 seconds")
        await asyncio.sleep(10)
        self.location = getLocation()
        self.players.append(self.spy)
        self.spy = ''
        self.roundtime = 10 * 60
        await self.assignRoles()

    async def timer(self):
        message = await self.ctx.send("Timer: {self.roundtime}")
        while True:
            self.roundtime -= 1
            if self.roundtime == 0:
                await message.edit(content="Ended!")
                await self.endRound('time-out')
                break
            await message.edit(content=f"Timer: {int(self.roundtime / 60) + 1}")
            await asyncio.sleep(1)
        await self.ctx.send("the round has ended!")

    async def voted(self, player, count):
        if count is None:
            count = 0
        if count >= len(self.players):
            await self.ctx.send(player.display_name + ' indicted as a spy')
            await self.endRound(player)
        else:
            await self.ctx.send('not enough votes. keep playing')


def getLocation():
    with open('./Locations.json') as data:
        Locations = json.load(data)
        location = random.choice(list(Locations['locations']))
    return location


@client.command()
async def locations(ctx):
    titles = []
    with open('./Locations.json') as data:
        Locations = json.load(data)
    Locations = list(Locations['locations'])
    for location in Locations:
        titles.append(str(location['title']))
    await ctx.send('\n'.join(titles))


@client.command()
async def endGame(ctx):
    global game
    game = ''


@client.command()
async def startGame(ctx):
    global game
    game = SpyFall(ctx)
    game.ctx = ctx
    await game.assignRoles()
    await game.timer()


async def getVoiceUsers(ctx):
    users = []
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel
    else:
        await ctx.send("You are not connected to a voice channel")
        return None
    for user in channel.members:
        users.append(user)
    return users


async def DM(user, message=None):
    message = message or "This Message is sent via DM"
    await user.send(message)


@client.command()
async def vote(ctx, member: discord.Member):
    global game
    try:
        if game == '':
            await ctx.send('no game started')
        await ctx.send(member.display_name + ' is up for vote')
        await ctx.message.add_reaction(emoji='👍')

        async def reactionFunction():
            try:
                reaction, user = await client.wait_for('reaction_add',
                                                       check=lambda reaction, user: str(reaction.emoji) == '👍',
                                                       timeout=30.0)
                if reaction.count >= len(game.players):
                    return reaction.count
            except asyncio.exceptions.TimeoutError:
                print('timed out')
                return reaction.count
        count = await reactionFunction()
        await game.voted(member, count)
    except NameError:
        await ctx.send('no game started')



@client.command()
async def rules(ctx):
    Rules = 'One player is always a spy who doesn\'t know where they are. The spy\'s mission is to listen carefully, ' \
            'identify the location, and keep from blowing his cover. Each non-spy must give an oblique hint to the ' \
            'other non-spies suggesting that he knows the location\'s identity, thus proving he\'s not the spy. '
    Objective = 'The spy: try to guess the round\'s location. Infer from others\' questions and answers.\nOther ' \
                'players: figure out who the spy is. '
    GameFlow = 'Round length: 6-10 minutes. Shorter for smaller groups, longer for larger.\nThe location: round ' \
               'starts, each player is given a location card. The location is the same for all players (e.g., ' \
               'the bank) except for one player, who is randomly given the "spy" card. The spy does not know the ' \
               'round\'s location.\nQuestioning: the game leader (person who started the game) begins by questioning ' \
               'another player about the location. Example: ("is this a place where children are ' \
               'welcome?").\nAnswering: the questioned player must answer. No follow up questions allowed. After they ' \
               'answer, it\'s then their turn to ask someone else a question. This continues until round is over.\nNo ' \
               'retaliation questions: if someone asked you a question for their turn, you cannot then immediately ' \
               'ask them a question back for your turn. You must choose someone else. '
    GuessingTheSpy = 'Putting up for vote: at any time, a player can try to indict a suspected spy by putting that ' \
                     'suspect up for vote. They must type .vote @player-name in chat.Then go one by one react to the ' \
                     'vote message if they\'re in agreement to ' \
                     'indict.\nVote must be unanimous to indict: if ' \
                     'any player votes no, the round continues as it was. Each person can only put a suspect up for ' \
                     'vote once per round. Use it wisely!\nSpy is indicted: if a player is indicted, they must reveal ' \
                     'whether or not they are the spy and the round ends. '
    SpyGuesses = 'at any time, the spy can reveal that they are the spy and make a guess at what the location is. The ' \
                 'round immediately ends. '
    RoundEnds = 'Indictment: group successfully indicts a player after voting OR \nSpy guesses: spy stops the round ' \
                'to make a guess about the location OR\nNo time left: clock runs out '
    Scoring = 'Spy Victory - The spy earns 2 points if no one is successfully indicted of being the spy\nThe spy ' \
              'earns 4 points if ' \
              'a non-spy player is successfully indicted of being a spy\nThe spy earns 4 points if the spy stops the ' \
              'game and successfully guesses the location ' \
              'Non-Spy Victory - Each non-spy player earns 1 point\nThe player who initiated the successful ' \
              'indictment of the spy earns 2 points instead '
    embed = discord.Embed(title="Rules", description=Rules, color=discord.Color.dark_red())
    await ctx.send(embed=embed)
    embed = discord.Embed(title="Objective", description=Objective, color=discord.Color.dark_red())
    await ctx.send(embed=embed)
    embed = discord.Embed(title="GameFlow", description=GameFlow, color=discord.Color.dark_red())
    await ctx.send(embed=embed)
    embed = discord.Embed(title="GuessingTheSpy", description=GuessingTheSpy, color=discord.Color.dark_red())
    await ctx.send(embed=embed)
    embed = discord.Embed(title="SpyGuesses", description=SpyGuesses, color=discord.Color.dark_red())
    await ctx.send(embed=embed)
    embed = discord.Embed(title="RoundEnds", description=RoundEnds, color=discord.Color.dark_red())
    await ctx.send(embed=embed)
    embed = discord.Embed(title="Scoring", description=Scoring, color=discord.Color.dark_red())
    await ctx.send(embed=embed)


client.run(tok)