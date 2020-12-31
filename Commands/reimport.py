import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES
from Functions.general import ensure_perms

class reimport(commands.Cog):
	"""
	Instantly updates a command, optionally replacing it with one uploaded

	Primarily meant to test out short-term changes quickly and without
	having to commit and wait for Heroku to restart the bot
	"""

	FORMAT = ""

	USAGE = ""


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="reimport", aliases=['re'], hidden=True)
	@ensure_perms()
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		if level == 1:
			await message.channel.send("Include command name.")
			return
		
		file_name = args[1].lower()

		if len(message.attachments) != 0:
			await message.attachments[0].save(f"Commands/{file_name}.py")

		self.BOT.unload_extension(f"Commands.{file_name}")
		self.BOT.load_extension(f"Commands.{file_name}")

		await message.channel.send("File updated successfully.")
		
		return


def setup(BOT):
	BOT.add_cog(reimport(BOT))