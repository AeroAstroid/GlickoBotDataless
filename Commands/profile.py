import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES
from Functions.general import *

import numpy as np
import asyncio
import os

class profile(commands.Cog):
	"""
	Shows a list of a player's rounds in a given time period.
	"""

	FORMAT = "[player] (time) to (time) ('file') ('season:')"

	USAGE = """Using `gl/profile PLAYER` outputs a list of all their rounds. 
	Adding some form of time - either YYYY, YYYY MM or YYYY MM DD - shows you 
	the player's rounds during that year, month and/or day. /ln/ Adding two 
	times separated by "to", i.e. `gl/profile PLAYER YYYY MM DD to YYYY MM DD` 
	limits it to rounds that happened during or between those two times. /ln/ 
	For long profiles, the list is divided into pages that you can navigate using 
	the ⬅️ and ➡️ reactions. /ln/ By default, the list is sorted by oldest round. 
	You can cycle through different sorting methods with the ⏺️ reaction, and 
	you can reverse the current sorting with the ↕️ reaction.
	""".replace("\n", "").replace("\t", "").replace(" /ln/ ", "\n")


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="profile", aliases=['p'])
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		# Needs at least 2 arguments: command, player
		if level < 2:
			await message.channel.send(
			"Include the name of a contestant!")
			return
		
		make_file = False
		# Check for a file request in the last arg
		if args[-1].lower() == "file":
			make_file = True
			args = args[:-1]
			level = len(args)
		
		lookup_name = ""
		# Check for a season request
		if "season:" in [x.lower() for x in args]:
			if args[-1].lower() == "season:":
				args = args[:-1]
				level = len(args)
			
			else:
				name_ind = [x.lower() for x in args].index("season:")
				lookup_name = " ".join(args[name_ind+1:]).lower()
				args = args[:name_ind]
				level = len(args)
		
		# Since the last arg has potentially changed, check for file again
		if args[-1].lower() == "file":
			make_file = True
			args = args[:-1]
			level = len(args)
		
		time_list = [[]]
		cont_args = []

		# Loop to discern time ranges from contestant names
		for arg_n in range(level - 1):
			ind = level - 1 - arg_n
			arg = args[ind]

			if ind == 1:
				cont_args.append(arg)

			elif is_int(arg) and len(time_list[-1]) < 3:
				time_list[-1].append(int(arg))

			elif arg.lower() == "to":
				time_list.append([])
			
			else:
				cont_args.append(arg)
		
		# Fallback for when there's a "to" but not two times
		if len(time_list) > 1:
			if len(time_list[1]) == 0:
				time_list = [time_list[0]]

		cont_name = " ".join(reversed(cont_args))

		# Check if player exists
		if not (username := DATA.true_name(cont_name)):
			await message.channel.send(
			f"Could not find a player named **`{cont_name}`** in the data.")
			return

		sorting = [
			# Category, ascending label, descending label, default rev
			["name", "alphabetical order", "reverse-alphabetical order", False],
			["RM change", "largest loss", "highest gain", True],
			["rank", "best rank", "worst rank", False],
			["round size", "smallest", "largest", True],
			["strength", "weakest", "strongest", True],
			["date", "oldest", "newest", False],
			["NR", "worst NR", "best NR", True]
		]

		sort_info = [5, False]

		# Parse time args into YMD lists
		for t, time in enumerate(time_list):
			
			# If the time is just a year or not specified, no need to do this
			if len(time) <= 1:
				continue
			
			# Check for reversal only if the year is not already the first argument
			if not DATES.MIN_YEAR <= time[0] <= DATES.MAX_YEAR:

				# Reverse the time if the year is the last argument
				if DATES.MIN_YEAR <= time[-1] <= DATES.MAX_YEAR:
					time_list[t] = list(reversed(time))
				
				else: # If neither the first nor last argument can be a year, it's invalid
					time_list[t] = '-'.join([str(value) for value in time_list[t]])
					await message.channel.send(
					f"Please specify a year between 2000 and 2099 in **`{time_list[t]}`**")
					return

			if len(time_list[t]) == 3:
				try: # Try to make YMD list into valid date
					DATES.to_DT(time_list[t])
				
				except ValueError:
					time_list[t] = '-'.join([str(value) for value in time_list[t]])
					await message.channel.send(
					f"**`{time_list[t]}`** is not a valid date!")
					return
			
			else:
				try: # Try to make YM list into valid date
					DATES.to_DT(time_list[t] + [1])

				except ValueError:
					time_list[t] = '-'.join([str(value) for value in time_list[t]])
					await message.channel.send(
					f"**`{time_list[t]}`** is not a valid month!")
					return
		
		time_list = list(reversed(time_list))

		if len(time_list[0]) == 0:
			# If no time was specified, the time range becomes the entire database range
			lookup_range = [
				[DATES.MIN_DATE, DATES.MAX_DATE],							# Range between 1st and last day
				[0, DATES.month_diff(DATES.MAX_DATE, DATES.MIN_DATE)]		# Range between 1st and last month
			]

		elif len(time_list) == 1:
			# If only one time was specified, the range is the span of that time
			lookup_range = DATES.time_lookup_range(
				time_list[0],
				time_list[0]
			)

		else:
			# If both times were specified, calculate the range they span
			lookup_range = DATES.time_lookup_range(
				time_list[0],
				time_list[1]
			)

			# Check that their order isn't reversed
			if lookup_range[0][0] > lookup_range[0][1]:
				lookup_range = DATES.time_lookup_range(
					time_list[1],
					time_list[0]
				)

		starting_date = DATA.starting_date(username)

		if lookup_range[0][1] < starting_date:
			await message.channel.send(
			f"**{username}** only started playing on **{DATES.to_FULL(starting_date)}**!")
			return
		
		if lookup_range[0][0] > DATES.MAX_DATE:
			await message.channel.send(
			f"Can't gather information for dates past **{DATES.to_FULL(DATES.MAX_DATE)}**!")
			return

		# Constrain the ranges between the player's starting date and the data MAX_DATE

		first_day = max(lookup_range[0][0], starting_date)
		last_day = min(DATES.MAX_DATE, lookup_range[0][1])

		first_month = min(DATES.month_diff(DATES.MAX_DATE, DATES.MIN_DATE), lookup_range[1][0])
		last_month = min(DATES.month_diff(DATES.MAX_DATE, DATES.MIN_DATE), lookup_range[1][1])
		
		round_list = []

		# Look inside each month for rounds
		for month in range(first_month, last_month + 1):

			# Skip months where the player didn't play any rounds
			if username not in DATA.HISTORY[month]:
				continue
			
			for round_name, round_info in DATA.HISTORY[month][username].items():
				# Narrows down rounds that don't start with lookup_name
				# By default lookup_name is "" so every round passes it
				if not round_name.lower().startswith(lookup_name):
					continue
				
				strength, date = DATA.ROUNDS[month][round_name]

				# Further check that the round does not bypass day ranges
				if last_day >= date >= first_day:
					rank, size = round_info[1:3]

					NR = (size - rank) / (size - 1)

					round_list.append([round_name] + round_info + [strength, date, NR])
					# Rounds are [name, gain, rank, size, strength, date, NR]
		
		msg = "```diff\n"
		msg += f"+ {username}```"

		if lookup_name == "":
			prior_day = DATES.day_before(first_day)

			msg += "```md\n"
			msg += (
			f"From < {DATES.as_FULL(prior_day)} > to < {DATES.as_FULL(last_day)} >\n\n")
			
			msg +=  "-------     Before  ||  After\n"

			RK_0 = DATA.player_rank(username, prior_day)
			RK_1 = DATA.player_rank(username, last_day)

			if RK_0:
				rank_change = RK_0 - RK_1
				rank_symbol = "●" if rank_change == 0 else ("▲" if rank_change > 0 else "▼")
				rank_change = np.abs(rank_change)

				msg += (
				f"#[Rank]:    {'#' + str(RK_0):>6}  ->  {'#' + str(RK_1):<10} {rank_symbol} {rank_change}\n")

			else:
				msg += (
				f"#[Rank]:   No rank  ->  {'#' + str(RK_1):<10} ● Debut\n")

			S_0, RM_0, RD_0, RP_0 = DATA.player_info(username, prior_day, convert=True)
			S_1, RM_1, RD_1, RP_1 = DATA.player_info(username, last_day, convert=True)

			symbol = "+" if (S_1 - S_0 >= 0) else "-"
			change = np.abs(round(S_1 - S_0, 2))
			msg += (
			f"[Score]:   {round(S_0, 2):>7}  ->  {round(S_1, 2):<10} {symbol} {change}\n")

			symbol = "+" if (RM_1 - RM_0 >= 0) else "-"
			change = np.abs(round(RM_1 - RM_0, 2))
			msg += (
			f"[---RM]:   {round(RM_0, 2):>7}  ->  {round(RM_1, 2):<10} {symbol} {change}\n")

			symbol = "+" if (RD_1 - RD_0 >= 0) else "-"
			change = np.abs(round(RD_1 - RD_0, 2))
			msg += (
			f"[---RD]:   {round(RD_0, 2):>7}  ->  {round(RD_1, 2):<10} {symbol} {change}\n")

			change = RP_1 - RP_0
			msg += (
			f"[---RP]:   {RP_0:>7}  ->  {RP_1:<10} + {change}\n")

		else:
			msg += "```md\n"
			msg += f"Rounds starting with < {lookup_name} >\n"

			if len(round_list) == 0:
				msg += "``````md\n# No rounds found.```"
				await message.channel.send(msg)
				return

			# Try to display all the dates
			all_dates = [r[5] for r in round_list]
			min_date, max_date = [min(all_dates), max(all_dates)]

			min_date = DATES.day_before(min_date)
			
			msg += f"From < {DATES.as_FULL(min_date)} > to < {DATES.as_FULL(max_date)} >\n\n"

		msg += "```"

		per_page = 15
		round_count = len(round_list)
		total_pages = int(np.ceil(round_count / per_page))

		def gen_page(p_n, sort=5, rev=False):
			add_msg = "```md\n"

			add_msg += (
			f"# Rounds: {round_count}\n")
			
			if round_count == 0:
				add_msg += "```"
				return msg + add_msg

			avg_nr = np.mean([rnd[6] for rnd in round_list])
			add_msg += (
			f"# Avg NR: {avg_nr*100:.2f}%\n")

			all_matchups = np.sum([rnd[3] - 1 for rnd in round_list])
			all_won = np.sum([rnd[3] - rnd[2] for rnd in round_list])

			matchups_won = all_won / all_matchups
			add_msg += (
			f"# Matchups won: {matchups_won*100:.2f}%  ({all_won}/{all_matchups})\n\n")

			if lookup_name != "":
				total_gain = sum([rnd[1] for rnd in round_list])
				gain_sign = "+" if total_gain >= 0 else "-"
				abs_gain = np.abs(round(total_gain, 2))
				add_msg += (
				f"# Total RM change: {gain_sign} {abs_gain}\n")

				total_wins = len([x for x in round_list if x[2] == 1])
				add_msg += (
				f"# Round wins: {total_wins}\n\n")

			rev = sorting[sort][3] ^ rev

			subset = sorted(round_list, reverse=rev, key=lambda m: m[sort])
			subset = subset[per_page * (p_n - 1) : per_page * (p_n)]

			add_msg += (
			"|   Date   ||          Round Name         || RM Change ||   Ranks   ||   N.R.   || Round Str\n")

			for name, gain, rank, size, strength, date, NR in subset:
				full_date = DATES.as_YMD(date)

				gain_sign = "+" if gain >= 0 else "-"
				abs_gain = np.abs(round(gain, 2))

				dp_prec = 7 - len(f'{NR * 100:.2f}')
				nr_format = f"{NR * 100:.0{dp_prec}f}%"

				add_msg += (
				f"[{full_date}]:  {name:<26} || {gain_sign} {abs_gain:<7} || {rank:>3} / {size:<3} ||  {nr_format}  ||  {strength:.02f}\n")
			
			add_msg += "\n"

			# Add page info if there's more than one
			if total_pages > 1:
				bounds = [
					per_page * (p_n - 1) + 1,			# First in the page
					min(per_page * p_n, round_count)	# Last in the page
				]
				add_msg += (
				f"< Page [{p_n} / {total_pages}] -- Rounds [{bounds[0]} ~ {bounds[1]}] of [{round_count}]>\n")

			# Add round sorting info if there's more than one
			if round_count > 1:
				add_msg += (
				f"< [{sorting[sort][0].upper()}] type sorting -- ordered by [{sorting[sort][1 + int(rev)].upper()}] >\n")
			
			add_msg += "```"

			return msg + add_msg
		
		page_number = 1
		page = gen_page(page_number, sort=sort_info[0], rev=sort_info[1])

		if make_file:
			if round_count == 0:
				await message.channel.send(
				msg + "\n**No rounds:** can't generate a round list file!")
				return

			with open(f"{username} Profile {message.id}.txt", "a", encoding="utf-8") as file:
				file.write(
				f"# Rounds: {round_count}\n")

				avg_nr = np.mean([rnd[6] for rnd in round_list])
				file.write(
				f"# Avg NR: {avg_nr*100:.2f}%\n")

				all_matchups = np.sum([rnd[3] - 1 for rnd in round_list])
				all_won = np.sum([rnd[3] - rnd[2] for rnd in round_list])
				matchups_won = all_won / all_matchups
				file.write(
				f"# Matchups won: {matchups_won*100:.2f}%  ({all_won}/{all_matchups})\n\n")

				if lookup_name != "":
					total_gain = sum([rnd[1] for rnd in round_list])
					gain_sign = "+" if total_gain >= 0 else "-"
					gain = np.abs(round(total_gain, 2))
					file.write(
					f"# Total RM change: {gain_sign} {gain}\n")

					total_wins = len([rnd for rnd in round_list if rnd[2] == 1])
					file.write(
					f"# Round wins: {total_wins}\n\n")

				rev = sorting[sort_info[0]][3] ^ sort_info[1]

				round_list = sorted(round_list, reverse=rev, key=lambda m: m[sort_info[0]])

				file.write(
				"|   Date   ||          Round Name         || RM Change ||   Ranks   ||   N.R.   || Round Str\n")

				for name, gain, rank, size, strength, date, NR in round_list:
					full_date = DATES.as_YMD(date)

					gain_sign = "+" if gain >= 0 else "-"
					abs_gain = np.abs(round(gain, 2))

					dp_prec = 7 - len(f'{NR * 100:.2f}')
					nr_format = f"{NR * 100:.0{dp_prec}f}%"

					file.write(
					f"[{full_date}]:  {name:<26} || {gain_sign} {abs_gain:<7} || {rank:>3} / {size:<3} ||  {nr_format}  ||  {strength:.02f}\n")
			
			await message.channel.send(msg,
			file=discord.File(f"{username} Profile {message.id}.txt"))

			os.remove(f"{username} Profile {message.id}.txt")
			return

		page_msg = await message.channel.send(page)
		await page_msg.edit(content=page)
		
		reaction_list = ['⬅️', '➡️', '⏺️', '↕️']

		if total_pages > 1:
			await page_msg.add_reaction('⬅️')
			await page_msg.add_reaction('➡️')
		if round_count > 1:
			await page_msg.add_reaction('⏺️')
			await page_msg.add_reaction('↕️')

		# Check that the reaction is what we want
		def check(reaction, user):
			return (user == message.author
			and str(reaction.emoji) in reaction_list
			and reaction.message.id == page_msg.id)
		
		while True:
			try:
				reaction, react_user = await self.BOT.wait_for(
					'reaction_add', timeout=120.0, check=check)

			except asyncio.TimeoutError:
				try:
					await page_msg.clear_reactions()
				except discord.errors.Forbidden:
					for r in reaction_list:
						await page_msg.remove_reaction(r, self.BOT.user)
				break

			else:
				if str(reaction.emoji) == '⬅️':
					try:
						await page_msg.remove_reaction('⬅️', react_user)
					except discord.errors.Forbidden:
						pass
					
					if page_number > 1:
						page_number -= 1
				
				if str(reaction.emoji) == '➡️':
					try:
						await page_msg.remove_reaction('➡️', react_user)
					except discord.errors.Forbidden:
						pass
					
					if page_number < total_pages:
						page_number += 1
				
				if str(reaction.emoji) == '⏺️':
					try:
						await page_msg.remove_reaction('⏺️', react_user)
					except discord.errors.Forbidden:
						pass
					
					sort_info[0] += 1
					sort_info[0] %= len(sorting)
				
				if str(reaction.emoji) == '↕️':
					try:
						await page_msg.remove_reaction('↕️', react_user)
					except discord.errors.Forbidden:
						pass
					
					sort_info[1] = not sort_info[1]

				page = gen_page(page_number, sort=sort_info[0], rev=sort_info[1])
				await page_msg.edit(content=page)
				continue


def setup(BOT):
	BOT.add_cog(profile(BOT))