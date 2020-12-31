import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES

import numpy as np

class matchup(commands.Cog):
	"""
	Compares the track record of two players' matchups against each other.
	"""

	FORMAT = "[player1] vs [player2]"
	
	USAGE = """Using `gl/matchup PLAYER1 vs PLAYER2` outputs statistics regarding 
	only rounds that both contestants played in (and where there was a matchup of 
	those two players).""".replace("\n", "").replace("\t", "")


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="matchup", aliases=['m'])
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
		if "vs" not in [x.lower() for x in args]:
			await message.channel.send(
			"Include the word `vs` to separate the name of the two contestants!")
			return
		
		# Divider between cont_0 and cont_1
		divider = [arg.lower() for arg in args].index('vs')

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

		shared_rounds = []

		for month in range(len(DATA.HISTORY)):
			if (cont_0 not in DATA.HISTORY[month] or
				cont_1 not in DATA.HISTORY[month]):
				continue
			
			month_rounds = []

			# Populate the list with info of all rounds cont_0 had
			for round_name, round_info in DATA.HISTORY[month][cont_0].items():
				_, round_date = DATA.ROUNDS[month][round_name]
				NR = (round_info[2] - round_info[1]) / (round_info[2] - 1)

				month_rounds.append([round_name, round_date, NR])
			
			cont_0_rounds = [rnd[0] for rnd in month_rounds]

			# Iterate through cont_1 rounds
			for round_name, round_info in DATA.HISTORY[month][cont_1].items():
				NR = (round_info[2] - round_info[1]) / (round_info[2] - 1)

				# Only add cont_1 NRs to rounds that cont_0 also had
				if round_name in cont_0_rounds:
					month_rounds[cont_0_rounds.index(round_name)] += [NR]
			
			month_rounds = [
				rnd						# All shared rounds this month
				for rnd in month_rounds
				if len(rnd) == 4		# If there's NR data for both contestants
			]

			shared_rounds += month_rounds
		
		# If they haven't shared a round
		if len(shared_rounds) == 0:
			await message.channel.send(
			f"**`{cont_0}`** and **`{cont_1}`** haven't played in any rounds together!")
			return
		
		# NR averages
		cont_0_avg = sum([x[2] for x in shared_rounds]) / len(shared_rounds)
		cont_1_avg = sum([x[3] for x in shared_rounds]) / len(shared_rounds)

		# Average NR distance
		cont_0_leverage = (cont_0_avg - cont_1_avg) / 2
		cont_1_leverage = -cont_0_leverage

		cont_0_sign = "+" if cont_0_leverage > 0 else "-"
		cont_1_sign = "+" if cont_0_sign == "-" else "-"

		cont_0_wins = len([x for x in shared_rounds if x[2] > x[3]])
		cont_1_wins = len(shared_rounds) - cont_0_wins

		msg = "```md\n"
		msg += f"< {cont_0} >\n"
		msg += f"vs. -> {len(shared_rounds)} matchup{'s' if len(shared_rounds) > 1 else ''}\n"
		msg += f"< {cont_1} >```"

		max_len = max(len(cont_0), len(cont_1)) + 1

		cont_0_rec = cont_0_wins / len(shared_rounds)
		cont_0_pct = f"{(100 * cont_0_rec):.02f}%"

		cont_1_rec = 1 - cont_0_rec
		cont_1_pct = f"{(100 * cont_1_rec):.02f}%"

		msg += "```diff\n"
		msg += "Matchup Records\n"
		
		msg += f"+ {cont_0:<{max_len}} :  {cont_0_wins:>3} / {len(shared_rounds):<4}  {cont_0_pct}\n"
		msg += f"+ [{'█'*round(40*cont_0_rec):—<40}]\n"

		msg += f"- {cont_1:<{max_len}} :  {cont_1_wins:>3} / {len(shared_rounds):<4}  {cont_1_pct}\n"
		msg += f"- [{'█'*round(40*cont_1_rec):—<40}]\n\n"

		cont_0_lstr = f"{np.abs(200*cont_0_leverage):.02f}%"
		cont_1_lstr = f"{np.abs(200*cont_1_leverage):.02f}%"

		msg += "NR Leverage\n"

		msg += f"+ {cont_0:<{max_len}} :  {cont_0_sign} {cont_0_lstr:<8} (Average NR: {100*cont_0_avg:.02f}%)\n"
		msg += f"+ [{'█'*round(40*(0.5+cont_0_leverage)):—<40}]\n"
		
		msg += f"- {cont_1:<{max_len}} :  {cont_1_sign} {cont_1_lstr:<8} (Average NR: {100*cont_1_avg:.02f}%)\n"
		msg += f"- [{'█'*round(40*(0.5+cont_1_leverage)):—<40}]"

		shared_rounds = sorted(shared_rounds, key=lambda m: m[2] - m[3], reverse=True)

		msg += f"``````md\n# Best < {cont_0} > rounds:\n"

		for rnd in shared_rounds[:3]:
			name, date, NR_0, NR_1 = rnd

			diff = f"{100 * np.abs(NR_0 - NR_1):.02f}%"
			sign = "+" if (NR_0 - NR_1) > 0 else "-"

			NR_0 = f"{100 * NR_0:.02f}%"
			NR_1 = f"{100 * NR_1:.02f}%"

			msg += f"[{DATES.as_YMD(date)}]:  {name:<26} ||  {sign} {diff:<8} ||{NR_0:>8} vs. {NR_1:<8}\n"

		msg += f"\n# Best < {cont_1} > rounds:\n"

		for rnd in reversed(shared_rounds[-3:]):
			name, date, NR_0, NR_1 = rnd

			diff = f"{100 * np.abs(NR_1 - NR_0):.02f}%"
			sign = "+" if (NR_1 - NR_0) > 0 else "-"

			NR_0 = f"{100 * NR_0:.02f}%"
			NR_1 = f"{100 * NR_1:.02f}%"

			msg += f"[{DATES.as_YMD(date)}]:  {name:<26} ||  {sign} {diff:<8} ||{NR_1:>8} vs. {NR_0:<8}\n"
		
		msg += "```"

		await message.channel.send(msg)

		return


def setup(BOT):
	BOT.add_cog(matchup(BOT))