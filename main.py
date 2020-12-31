import datetime
import os
import traceback

print(f"Booting up on {datetime.datetime.utcnow()}")

from discord.ext import commands
from discord import Game

GLICKO_BOT = commands.Bot(command_prefix = "gl/")

GLICKO_BOT.remove_command("help")

@GLICKO_BOT.event
async def on_ready():
	print(f"Logged in on {datetime.datetime.utcnow()}\n")
	
	await GLICKO_BOT.change_presence(
	activity=Game(name="gl/help"))

@GLICKO_BOT.event
async def on_command(ctx):
	print("Command from", ctx.message.author)

	try:
		print(ctx.message.channel.name, f"({ctx.message.channel.id})")
		print(ctx.message.guild.name, f"({ctx.message.guild.id})")
	except AttributeError:
		print("Sent in DMs")
	
	print("-->", ctx.message.content, "\n")

@GLICKO_BOT.event
async def on_command_error(ctx, error):
	if type(error) == commands.errors.CommandNotFound:
		cmd = ctx.message.content.split(" ")[0].lower()
		await ctx.send(
		f"⚠️ The command **`{cmd}`** does not exist!")
		return
	if type(error) == commands.errors.CheckFailure:
		await ctx.send(
		"⚠️ You do not have permission to run this command!")
		return
	
	await ctx.send(
	"⚠️ Uh oh! This command has raised an unexpected error.")

	print("-[ERROR]- "*10)
	traceback.print_exception(type(error), error, None)
	print("-[ERROR]- "*10)

print("-"*50)

for cog in os.listdir("Commands"):
	if not cog.endswith('py'):
		continue

	GLICKO_BOT.load_extension(f"Commands.{cog[:-3]}")

	print(f"Loaded command {cog[:-3].upper()}")

print("-"*50)

GLICKO_BOT.run(os.getenv("GLICKO_BOT_TOKEN"))