import discord
from discord.ext import commands

class help(commands.Cog):
	"""
	Displays a screen containing every command you can use and information on it
	"""

	FORMAT = "(command)"

	USAGE = """Using `gl/help` shows you a list of commands. Filling in the parameter 
	`(command)` shows you information on a specific command. In command help pages, 
	parameters marked with **[brackets]** are mandatory. Those marked with 
	**(parentheses)** are optional.""".replace("\n", "").replace("\t", "")
	

	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="help", aliases=['h'])
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		embed = discord.Embed(color=0x42495E)
		commands = self.BOT.cogs

		# If user asks for general help
		if level == 1:
			embed.title = "Glicko Bot"

			embed.description = f"""A bot for TWOW Glicko data visualization, made 
			by <@184768535107469314> /ln/ These are all the commands available. 
			Use `gl/help (command)` to find out more about a specific command. /ln/ 
			\u200b""".replace("\n", "").replace("\t", "").replace(" /ln/ ", "\n")
			
			embed.set_thumbnail(
			url=self.BOT.user.avatar_url_as(static_format="png"))

			command_list = ""

			for name, cls in commands.items():
				if cls.get_commands()[0].hidden:
					continue
				
				command_list += f"**`{name}`**\n"

			embed.add_field(
				name="Here are all the currently available commands.",
				value=command_list
			)

			await message.channel.send(embed=embed)
			return
		
		requested = args[1].lower()
		
		# Check if the requested command is an alias
		if requested not in commands.keys():
			for name, cls in commands.items():
				if requested in cls.get_commands()[0].aliases:
					requested = name
					break
			
			else:
				await message.channel.send(
				"Invalid command to get help for!")
				return
		
		COG = commands[requested]
		CMD = COG.get_commands()[0]

		if CMD.hidden:
			await message.channel.send(
			"Invalid command to get help for!")
			return
		
		embed.title = f"gl/{requested}"
		embed.description = COG.description

		if len(CMD.aliases) > 0:
			alias_list = ', '.join([f'**`gl/{al.lower()}`**' for al in CMD.aliases])

			embed.description += f"\nAliases: {alias_list}"

		embed.description += "\n\u200b"

		# Some commands have list USAGEs because their USAGE is >1024 chars
		if not isinstance((use := COG.USAGE), list):
			use = [use]
		
		# Add each USAGE individually
		for ind, u in enumerate(use):
			embed.add_field(
			name=f"**gl/{requested} {COG.FORMAT}**" if ind == 0 else '\u200b',
			value=u, inline=False)

		await message.channel.send(embed=embed)
		return


def setup(BOT):
	BOT.add_cog(help(BOT))