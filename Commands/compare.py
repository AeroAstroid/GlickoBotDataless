import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES
from Functions.calc import CALC

from Functions.general import *

class compare(commands.Cog):
	"""
	Compares the statistics of two different players at any point in time.
	"""

	FORMAT = "[player1] vs [player2]"

	USAGE = """Using `gl/compare PLAYER1 vs PLAYER2` outputs a list of statistics 
	comparing both players, as of the latest Glicko update. Adding a YYYY MM DD date, 
	like for example `gl/compare PLAYER1 vs PLAYER2 2020 6 16` will do the comparison 
	using the players' statistics on that given day.
	""".replace("\n", "").replace("\t", "")
	

	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="compare", aliases=['c'])
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		# Needs at least 4 arguments: command, player1, vs, player2
		if level < 4:
			await message.channel.send(
			"Include two contestants you want compared, separated by `vs`!")
			return
		
		# "vs." works as well as "vs"
		args = ["vs" if arg == "vs." else arg for arg in args]

		# If a vs separator can't be found
		if "vs" not in [arg.lower() for arg in args]:
			await message.channel.send(
			"Include the word `vs` to separate the name of the two contestants!")
			return
		
		# If the last three arguments are vaLid integers, parse them as YMD
		if False not in [is_int(value) for value in args[-3:]]:
			ymd_list = [int(value) for value in args[-3:]]

			try:
				date_ID = DATES.to_ID(ymd_list)

			except ValueError:
				ymd_list = DATES.as_YMD(ymd_list)

				await message.channel.send(
				f"`{ymd_list}` is an invalid date!")
				return
			
			args = args[:-3]
			level = len(args)
		
		else:
			date_ID = DATES.MAX_DATE
		
		# Divider between cont_0 and cont_1
		divider = [arg.lower() for arg in args].index("vs")

		raw_cont_name_0 = " ".join(args[1:divider])
		raw_cont_name_1 = " ".join(args[divider+1:])

		# Check that players exist
		if not (cont_0 := DATA.true_name(raw_cont_name_0)):
			await message.channel.send(
			f"Could not find a player named **`{raw_cont_name_0}`** in the data.")
			return
		if not (cont_1 := DATA.true_name(raw_cont_name_1)):
			await message.channel.send(
			f"Could not find a player named **`{raw_cont_name_1}`** in the data.")
			return
		
		# Check that the date falls within acceptable bounds
		if date_ID < DATES.MIN_DATE:
			await message.channel.send(
			f"Can't get information for dates before {DATES.as_FULL(DATES.MIN_DATE)}!")
			return
		if date_ID > DATES.MAX_DATE:
			await message.channel.send(
			f"Can't get information for dates after {DATES.as_FULL(DATES.MAX_DATE)}!")
			return
		
		info_0 = DATA.player_info(cont_0, date_ID, convert=True)
		info_1 = DATA.player_info(cont_1, date_ID, convert=True)

		# Check if either were unranked as of this day
		if info_0 == DATA.DEFAULT_PLAYER:
			await message.channel.send(
			f"Can't find data for the player **`{cont_0}`** on {DATES.as_FULL(date_ID)}!")
			return
		
		if info_1 == DATA.DEFAULT_PLAYER:
			await message.channel.send(
			f"Can't find data for the player **`{cont_1}`** on {DATES.as_FULL(date_ID)}!")
			return
		
		win_chance_0 = CALC.win_chance(info_0, info_1, convert=True)
		win_chance_1 = 1 - win_chance_0

		max_length = max(len(cont_0), len(cont_1))

		msg = "```diff\n"

		msg += f"+ {cont_0}\n"
		msg += f"--- vs. -> ({DATES.as_FULL(date_ID)})\n"
		msg += f"- {cont_1}\n\n"

		rank_0 = DATA.player_rank(cont_0, date_ID)
		rank_1 = DATA.player_rank(cont_1, date_ID)

		score_0, RM_0, RD_0, RP_0 = info_0
		score_1, RM_1, RD_1, RP_1 = info_1

		msg += f"+ {cont_0} - Ranked #{rank_0}\n"
		msg += f"+ Score : {round(score_0, 2):<10} RP : {RP_0}\n"
		msg += f"+ RM    : {round(RM_0, 2):<10} RD : {round(RD_0, 2)}\n\n"

		msg += f"- {cont_1} - Ranked #{rank_1}\n"
		msg += f"- Score : {round(score_1, 2):<10} RP : {RP_1}\n"
		msg += f"- RM    : {round(RM_1, 2):<10} RD : {round(RD_1, 2)}\n\n"

		msg += "Win Chance\n"

		bar_0 = f"[{'█'*round(50*win_chance_0):—<50}]"
		bar_1 = f"[{'█'*round(50*win_chance_1):—<50}]"

		msg += f"+ {cont_0:<{max_length}}  :  {round(win_chance_0*100, 2):6}%  {bar_0}\n"
		msg += f"- {cont_1:<{max_length}}  :  {round(win_chance_1*100, 2):6}%  {bar_1}\n"

		msg += "```"
		
		await message.channel.send(msg)
		return

def setup(BOT):
	BOT.add_cog(compare(BOT))