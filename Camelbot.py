#!/usr/bin/env python

import discord, asyncio, random, re, os, urllib.request, json, knuckleheads

pattern = re.compile("[^\s\"']+|\"([^\"]*)\"|'([^']*)'")

def changeSettings(toChange=None, value=None):
	settings[toChange] = value
	json.dump(settings, open("config.json", "w"))

settings = {}
try:
	settings = json.load(open("config.json"))
except Exception as e:
	settings = {}
	changeSettings()
	raise Exception (str(e) + ": please initialise the bot's settings in 'config.json' before using it")

commands = {}
adminCommands = {}

try:
	Token = settings['token']
except Exception as e:
	raise Exception (str(e) + ": please set the 'token' value in config.json!")

directions = [u"\u2196", u"\u2B06", u"\u2197", u"\u2B05", u"\u23FA", u"\u27A1", u"\u2199", u"\u2B07", u"\u2198"]

numbers = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣"]

class doNothing():
	
	async def __new__(cls, *a, **kw):
		instance = super().__new__(cls)
		await instance.__init__(*a, **kw)
		return instance

	async def __init__(self, message, gameIndex):
		self.reactionMessages = []	
		self.message = message
		self.gameIndex = gameIndex
		self.forwards = {message.author: self.gameIndex}
		
	async def handleEmojis(self, reaction, user):
		pass
		
	async def endGame(self):
		client.games[self.gameIndex] = None		

class connect():

	async def __new__(cls, *a, **kw):
		instance = super().__new__(cls)
		await instance.__init__(*a, **kw)
		return instance

	async def __init__(self, message, gameIndex):
		self.reactionMessages = []	
		self.message = message
		self.gameIndex = gameIndex
		self.players = []
		self.last_player = None
		self.gameData = [[":white_large_square:"] * 7 for i in range(6)]
		self.playersMsg = await client.send_message(self.message.channel, ":red_circle:: Waiting...\n:large_blue_circle:: Waiting...")
		self.nextMsg = await client.send_message(self.message.channel, "Next: Waiting...")
		self.gameMessage = await client.send_message(self.message.channel, "{}\n{}\n{}\n{}\n{}\n{}\n{}".format(*["".join(i) for i in self.gameData], "".join(numbers)))
		self.reactionMessages.extend([self.gameMessage.id])
		for i in numbers:
			await client.add_reaction(self.gameMessage, i)
	
	async def checkDirection(self, toCheck, data, initialPos, add):
		total = 0
		x, y = initialPos
		dx, dy = add
		while x in range(7) and y in range(6) and toCheck[y][x] == data:
			x -= dx
			y -= dy
		x += dx
		y += dy
		while x in range(7) and y in range(6) and toCheck[y][x] == data:
			total += 1
			x += dx 
			y += dy
		return total
	
	async def findConnected(self, toCheck, data, initialPos):
		counts = [await self.checkDirection(toCheck, data, initialPos, (1, 0)), await self.checkDirection(toCheck, data, initialPos, (0, 1)), await self.checkDirection(toCheck, data, initialPos, (1, 1)), await self.checkDirection(toCheck, data, initialPos, (-1, 1))]
		return counts
	
	async def newCounter(self, column, data, user):
		for i, j in enumerate(self.gameData[::-1]):
			if j[column - 1] == ":white_large_square:":
				if self.last_player:
					await client.edit_message(self.nextMsg, new_content = "Next: {}".format(self.playersMsg.server.get_member(self.last_player).display_name))
				self.last_player = user.id				
				x, y = (column - 1, len(self.gameData) - 1 - i)
				self.gameData[y][x] = data
				await client.edit_message(self.gameMessage, new_content = "{}\n{}\n{}\n{}\n{}\n{}\n{}".format(*["".join(i) for i in self.gameData], "".join(numbers)))
				tiles = []
				for i, j in enumerate(self.gameData):
					for k, l in enumerate(j):
						if l == data:
							tiles.append(await self.findConnected(self.gameData, data, (x, y)))
				for i in tiles:
					for j in i:
						if j >= 4:
							self.winner = user
							break
				try:
					if self.winner:
						await client.send_message(self.gameMessage.channel, "Game won by {}!".format(self.winner.display_name))
						await client.edit_message(self.nextMsg, new_content = "Winner: {}".format(self.winner.display_name))
						await self.endGame()
				except:
					pass
				draw = True
				for i in self.gameData:
					for j in i:
						if j == ":white_large_square:":
							draw = False
				if draw:
					await client.send_message(self.gameMessage.channel, "Draw!")
					await client.edit_message(self.nextMsg, new_content = "Draw!")
					await self.endGame()					
				break
			else:
				continue
		
	async def handleEmoji(self, reaction, user):
		try:
			move = int(reaction.emoji[0])
		except:
			return
		if move is not None:
			if len(self.players) < 2:
				self.players.append(user.id)
				await client.edit_message(self.playersMsg, new_content = ":red_circle:: {}\n:large_blue_circle:: {}".format(self.playersMsg.server.get_member(self.players[0]).display_name, self.playersMsg.server.get_member(self.players[1]).display_name if len(self.players) > 1 else "Waiting..."))
			if user.id in self.players and self.last_player != user.id:
				await self.newCounter(move, [":red_circle:", ":large_blue_circle:"][self.players.index(user.id)], user)

	async def endGame(self):
		client.games[self.gameIndex] = None		

class noughtsandcrosses():
	
	async def __new__(cls, *a, **kw):
		instance = super().__new__(cls)
		await instance.__init__(*a, **kw)
		return instance
	
	async def __init__(self, message, gameIndex):
		self.reactionMessages = []
		self.message = message
		self.gameIndex = gameIndex
		self.players = []
		self.playersMsg = ":o:: Waiting...\n:x:: Waiting..."
		self.nextMsg = "Next: Waiting..."		
		self.metaMsg = await client.send_message(self.message.channel, await self.getMeta())
		self.game = [":white_large_square:"] * 9
		self.last_player = None
		self.gameData = "{}{}{}\n{}{}{}\n{}{}{}".format(*self.game[:3], *self.game[3:6], *self.game[6:])
		self.msg = await client.send_message(self.message.channel, self.gameData)
		self.reactionMessages.extend([self.msg.id])
		for i in directions:
			await client.add_reaction(self.msg, "{}".format(i))	
			
	async def getMeta(self):
		self.metaData = "\n".join([self.playersMsg, self.nextMsg])
		return self.metaData
		
	async def refreshGameboard(self, message):
		self.gameData = "{}{}{}\n{}{}{}\n{}{}{}".format(*self.game[:3], *self.game[3:6], *self.game[6:])
		await client.edit_message(message, new_content = self.gameData)
		self.sections = [self.game[:3], self.game[3:6], self.game[6:], [self.game[0], self.game[3], self.game[6]], [self.game[1], self.game[4], self.game[7]], [self.game[2], self.game[5], self.game[8]], [self.game[0], self.game[4], self.game[8]], [self.game[2], self.game[4], self.game[6]]]
		for i in self.sections:
			if i[0] == i[1] and i[1] == i[2]:
				try:
					self.winner = message.server.get_member(self.players[[":o:", ":x:"].index(i[0])])
					await client.send_message(message.channel, "{} won!".format(self.winner.display_name))
					self.nextMsg = "Winner: {}".format(self.winner.display_name)
					await client.edit_message(self.metaMsg, new_content = await self.getMeta())					
					await self.endGame()
					return None
				except:
					continue
		if ":white_large_square:" not in self.game:
			await client.send_message(message.channel, "Draw!")
			await self.endGame()
			
	async def handleEmoji(self, reaction, user):
		move = directions.index(str(reaction.emoji))
		if move is not None:
			if len(self.players) < 2:
				self.players.append(user.id)
				self.playersMsg = ":o:: {}\n:x:: {}".format(self.msg.server.get_member(self.players[0]).display_name, self.metaMsg.server.get_member(self.players[1]).display_name if len(self.players) > 1 else "Waiting...")
				await client.edit_message(self.metaMsg, new_content = await self.getMeta())									
			if user.id in self.players and self.game[move] == ":white_large_square:" and self.last_player != user.id:
				if self.last_player:
					self.nextMsg = "Next: {}".format(self.metaMsg.server.get_member(self.last_player).display_name)
				self.last_player = user.id
				self.game[move] = [":o:", ":x:"][self.players.index(user.id)]
				await client.edit_message(self.metaMsg, new_content = await self.getMeta())					
				await self.refreshGameboard(reaction.message)		
			
	async def endGame(self):
		client.games[self.gameIndex] = None

class pixelword():
	
	async def __new__(cls, *a, **kw):
		instance = super().__new__(cls)
		await instance.__init__(*a, **kw)
		return instance

	async def __init__(self, message, gameIndex):
		self.reactionMessages = []
		self.message = message
		self.gameIndex = gameIndex
		self.remaining = settings[self.message.server.id]['totalLives']
		await client.send_message(self.message.author, "Which word would you like to play?")
		self.forwards = {message.author: self.gameIndex}
	
	async def newHangman(self, message):
		self.word = "".join([i for i in list(message.content.lower().split()[0]) if ord(i) in range(97, 123)])
		if self.word != message.content.lower():
			print(message.content)
		if not self.word or len(self.word) > 20:
			await client.send_message(message.author, "Invalid word!")
			return
		await client.send_message(self.message.channel, "Author: {}".format(message.author.display_name))
		self.remainingMessage = await client.send_message(self.message.channel, "Remaining: {}".format("".join([":heart:"] * self.remaining + [":black_heart:"] * (settings[self.message.server.id]['totalLives'] - self.remaining))))
		self.gameData = ["\_"] * len(self.word)
		self.gameWord = await client.send_message(self.message.channel, "**{}**".format(" ".join(self.gameData)))
		self.reactionMessages.extend([self.remainingMessage.id, self.gameWord.id])
		for i in range(127462, 127475):
			await client.add_reaction(self.remainingMessage, "{}".format(chr(i)))
		for i in range(127475, 127488):
			await client.add_reaction(self.gameWord, "{}".format(chr(i)))
			
	async def handleEmoji(self, reaction, user):
		try:
			if ord(reaction.emoji) in range(127462, 127488):
				letter = chr(ord(reaction.emoji) - 127365)
				author = user
				if letter in self.gameData or author == self.message.author:
					return
				letterLocations = [i for i in range(len(self.word)) if self.word.startswith(letter, i)]
				if letterLocations == []:
					await client.remove_reaction(reaction.message, reaction.emoji, client.user)
					self.remaining -= 1
					await client.edit_message(self.remainingMessage, new_content = "Remaining: {}".format("".join([":heart:"] * self.remaining + [":black_heart:"] * (settings[self.message.server.id]['totalLives'] - self.remaining))))
					if self.remaining <= 0:
						await client.send_message(self.remainingMessage.channel, "All {} lives lost - the word was '{}'!".format(settings[self.message.server.id]['totalLives'], self.word))
						await self.endGame()
					return
				for i in letterLocations:
					self.gameData[i] = letter
				await client.edit_message(self.gameWord, new_content = "**{}**".format(" ".join(self.gameData)))
				if "".join(self.gameData) == self.word:
					await client.send_message(self.gameWord.channel, "Game complete! The winner was {}!".format(author.display_name))
					await self.endGame()
		except Exception as e:
			print(e)	
			return		

	async def endGame(self):
		client.games[self.gameIndex] = None
	
class camel(discord.Client): 
	# Command setup stuff

	global commands
	commands = {}
	command = lambda f: commands.setdefault(f.__name__, f)
	
	global adminCommands
	adminCommands = {}
	adminCommand = lambda g: adminCommands.setdefault(g.__name__, g)

	# Commands:

	@command
	async def help(self, message, *args): 
		"""provides this help text"""
		await client.send_message(message.author, "All commands: ```{}```".format("\n".join(["• " + i + " - " + commands[i].__doc__ for i in commands if i not in settings[message.server.id]['disallowedCmds']])))

	@command
	async def apple(self, message, *args):
		"""sends an apple to make sure your local BY is properly fed"""
		await client.send_message(message.channel, ":{}:".format(random.choice(["apple", "green_apple"])))

	# Games:

	@command
	async def newword(self, message, *args):
		"""starts a new game of hangman"""
		self.games.append(await pixelword(message, len(self.games)))

	@command
	async def newgame(self, message, *args):
		"""starts a new game of noughts-and-crosses/tic-tac-toe/whatever"""
		self.games.append(await noughtsandcrosses(message, len(self.games)))

	@command
	async def new4(self, message, *args):
		"""starts a new game of connect 4"""
		self.games.append(await connect(message, len(self.games)))

	# Bot stuff and admin commands
	
	@adminCommand
	async def help(self, message, *args): 
		"""provides this help text"""
		await client.send_message(message.author, "Admin commands: ```{}```".format("\n".join([*["• " + i + " - " + commands[i].__doc__ for i in commands], *["• " + i + " - " + adminCommands[i].__doc__ for i in adminCommands]])))	

	@adminCommand
	async def test(self, message, *args):
		"""allows admins to test the command error handler"""
		await client.send_message(message.channel, "Raising exception...")
		raise Exception ("Testing exception handler...")

	@adminCommand
	async def shutdown(self, message, *args):
		"""allows admins to shut down the bot"""
		await client.send_message(message.channel, "Goodbye all!")
		await client.logout()

	@adminCommand
	async def reloadconfig(self, message, *args):
		"""allows admins to reload the bot's config file"""
		global settings
		try:
			settings = json.load(open("config.json"))
			await client.send_message(message.channel, "Config reloaded!")
		except Exception as e:
			settings = {}
			changeSettings()
			raise Exception (str(e) + ": please initialise the bot's settings in 'config.json' before using this command")
		
	async def on_ready(self):
		print("------")
		print(client.user.name)
		print(client.user.id)
		print(", ".join([i.name for i in client.servers]))
		print("------")
		self.games = []

	async def checkMessages(self, message):
		if str(self.user) in [str(i) for i in message.mentions]:
			await self.send_message(message.channel, "***ＮＯ ＰＩＮＧ ＰＬＳ***")		

	async def on_message(self, message): # Handles pretty much everything
		
		if type(message.channel) == discord.channel.PrivateChannel:
			message.server = knuckleheads.jsDict({"id": "DM"})

		if message.author == self.user or message.author.id in settings[message.server.id]['banned']: 
			return

		raw = message.content

		data = [i.group(0) for i in re.finditer(pattern, raw) if any([raw.startswith(i) for i in settings[message.server.id]["prefixes"]])]

		if not data or len(message.content) < 2:
			try:
				await client.checkMessages(message)

			except discord.errors.Forbidden:
				await client.send_file(message.author, "data/Quality Twingo Memes/" + random.choice(os.listdir("data/Quality Twingo Memes")), content = "I don't have permission to post in #{} - please contact the server owner! In the meantime, here's a random Twingo meme:".format(message.channel.name))

			except Exception as e:
				print(e)
				await client.send_message(message.channel, "Something went wrong! Error details have been printed.")

			if type(message.channel) == discord.channel.PrivateChannel:
				for i in self.games:
					try:
						if message.author in i.forwards:
							await self.games[i.forwards[message.author]].newHangman(message)
							i.forwards = None
					except TypeError:
						pass
					except AttributeError:
						pass
						
			return

		command = {"command": data[0].lstrip("".join(settings[message.server.id]['prefixes'])), "args": data[1:]}

		try:
			if command["command"] in adminCommands and type(message.channel) != discord.channel.PrivateChannel and any([role.name in settings[message.server.id]["admins"] for role in message.author.roles]) and len(message.author.roles) > 1:
				await adminCommands[command["command"]](self, message, *command["args"])
			elif command["command"] not in settings[message.server.id]['disallowedCmds']:
				await commands[command["command"]](self, message, *command["args"])
			else:
				raise AttributeError

		except AttributeError:
			try:
				await client.send_message(message.channel, "'{}' is not a command.".format(command["command"]))

			except discord.errors.Forbidden:
				await client.send_message(message.author, "'{}' is not a command.".format(command["command"]))

		except discord.errors.Forbidden:
			try:
				self.tempchannel = message.channel
				message.channel = message.author
				if any([role.name in settings[message.server.id]["admins"] for role in message.author.roles]) and len(message.author.roles) > 1:
					await adminCommands[command["command"]](self, message, *command["args"])
				else:
					await commands[command["command"]](message, *command["args"])

			except Exception as e:
				await self.send_file(message.author, "data/Quality Twingo Memes/" + random.choice(os.listdir("data/Quality Twingo Memes")), content = "I don't have permission to post in #{} - please contact the server owner! In the meantime, here's a random Twingo meme:".format(self.tempchannel.name))

		except Exception as e:
			if type(e) == KeyError:
				try:
					await client.send_message(message.channel, "'{}' is not a command.".format(command["command"]))

				except discord.errors.Forbidden:
					await client.send_message(message.author, "'{}' is not a command.".format(command["command"]))
				return
			print(e)            
			try:
				await client.send_message(message.channel, "Something went wrong! Error details have been printed.")
			except:
				await client.send_message(message.author, "Something went wrong! Error details have been printed (tell Jynji to check bot logs).")

	async def on_member_join(self, member): # Sends message to new users
		if not member:
			raise Exception ("Missing member argument")
		print("Welcoming {.name} to server...".format(member))
		server = member.server
		if settings[server.id]["welcome"]:
			await self.send_message(member, settings[server.id]["welcomeMessage"].format(member, server))

	# Multi-game interaction code

	async def on_reaction_add(self, reaction, user):
		if reaction.message.author.id == client.user.id and not user.id == client.user.id:
			for i in [i for i in self.games if i != None]:
				if reaction.message.id in i.reactionMessages:
					await i.handleEmoji(reaction, user)

client = camel()
client.run(Token)