import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES
from Functions.calc import CALC
from Functions.general import *

import numpy as np
import asyncio

class roundinfo(commands.Cog):
	"""
	Displays info on a round or a collection of a season's rounds.
	"""

	FORMAT = "['all'/roundname/seasonname] (time)"

	USAGE = ["""Using `gl/roundinfo ROUNDNAME` (where `ROUNDNAME` is `SEASON 
	ROUNDNUMBER`) shows you the rankings for any round in the TWOW Glicko data. 
	You can also use `gl/roundinfo SEASONNAME` to display a list of all available 
	rounds in a given season. /ln/ The round rankings are divided into pages which can 
	be navigated using the ⬅️ and ➡️ reactions. /ln/ By default, the list is sorted 
	by best performance. You can cycle through different sorting methods with the ⏺️ 
	reaction, and you can reverse the current sorting with the ↕️ reaction.
	""".replace("\n", "").replace("\t", "").replace(" /ln/ ", "\n"),

	"""Additionally, you can use `gl/roundinfo all` to receive a list of all the rounds 
	in the TWOW Glicko data. You can filter rounds chronologically by using `gl/roundinfo 
	all TIME` to get all rounds that happened during `TIME` or `gl/roundinfo all TIME1 to 
	TIME2` to get all rounds that happened between two separate times - `TIME` being in the 
	form of YYYY, YYYY MM, or YYYY MM DD. /ln/ This round list is also paged and can be 
	sorted in much the same way as the round rankings described above.
	""".replace("\n", "").replace("\t", "").replace(" /ln/ ", "\n")]


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="roundinfo", aliases=['r', 'ri', 'round', 'rounds'])
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		# Needs at least 2 arguments: command, round/season
		if level < 2:
			await message.channel.send(
			"Include a round or season to get information on!")
			return
		
		if args[1].lower() == "all":
			# If all rounds are requested

			all_seasons = DATA.all_seasons(verbose=True)

			time_list = [[]]
			time_args = args[2:]

			for arg in time_args:
				if is_int(arg) and len(time_list[-1]) < 3:
					time_list[-1].append(int(arg))

				elif arg.lower() == "to" and len(time_list) == 1:
					time_list.append([])
			
			# Remove duplicates
			time_list = [t for ind, t in enumerate(time_list) if time_list.index(t) == ind]

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
			
			if len(time_list[0]) == 0:
				# If no time was specified, the time range becomes the entire database range
				l_start_date, l_end_date = [DATES.MIN_DATE, DATES.MAX_DATE]

			elif len(time_list) == 1:
				# If only one time was specified, the range is the span of that time
				l_start_date, l_end_date = DATES.time_lookup_range(
					time_list[0],
					time_list[0]
				)[0]

			else:
				# If both times were specified, calculate the range they span
				l_start_date, l_end_date = DATES.time_lookup_range(
					time_list[0],
					time_list[1]
				)[0]

				# Check that their order isn't reversed
				if l_start_date > l_end_date:
					l_start_date, l_end_date = DATES.time_lookup_range(
						time_list[1],
						time_list[0]
					)[0]

			for ind, season in enumerate(all_seasons):
				_, _, s_date, e_date, _ = season

				if s_date > l_end_date or e_date < l_start_date:
					all_seasons[ind] = False
			
			all_seasons = [s for s in all_seasons if s]

			all_rounds = []

			# Find all valid rounds to populate the all_rounds array
			for s in all_seasons:
				s_rounds = DATA.season_rounds(s[0])

				for r in s_rounds:
					_, r_date, _, _ = r

					if l_end_date >= r_date >= l_start_date:
						r[0] = f"{s[0]} R{r[0]}"
						all_rounds.append(r)
			
			sorting = [
				# Category, ascending label, descending label, default rev
				["round name", "alphabetical order", "reverse-alphabetical order", False],
				["date", "oldest", "newest", False],
				["size", "smallest round", "largest round", True],
				["strength", "weakest round", "strongest round", True],
			]

			sort_info = [1, False]

			page_number = 1
			data_count = len(all_rounds)
			per_page = 15
			total_pages = int(np.ceil(data_count / per_page))

			# Wrapper function to customize page generation
			def gen_page(p_n, sort=0, rev=False):
				msg = "```md\n# All TWOW Glicko Rounds\n"

				if len(time_list[0]) != 0:
					msg += (
					f"< {DATES.as_FULL(l_start_date)} > to < {DATES.as_FULL(l_end_date)} >\n")
				
				msg += f"# Rounds: {data_count}\n\n"

				rev = sorting[sort][3] ^ rev
				
				subset = sorted(all_rounds, key=lambda m: m[sort], reverse=rev)
				subset = subset[per_page*(p_n - 1):per_page*p_n]

				msg += (
				"|   Date   ||          Round Name         || Size  || Round Str\n")

				for round_name, date, size, strength in subset:
					msg += (
					f"[{DATES.as_YMD(date)}]:  {round_name:<26} || {size:<5} ||  {strength:.02f}\n")
				
				# Show page information if there's more than one
				if total_pages > 1:
					bounds = [
						per_page * (p_n - 1) + 1,			# First in the page
						min(per_page * p_n, data_count)	# Last in the page
					]
					msg += (
					f"\n< Page [{p_n} / {total_pages}] -- Rounds [{bounds[0]} ~ {bounds[1]}] of [{data_count}] >")
				
				# Show round sorting information if there's more than one
				if data_count > 1:
					msg += (
					f"\n< [{sorting[sort][0].upper()}] type sorting -- ordered by [{sorting[sort][1 + int(rev)].upper()}] >")
				
				msg += "```"

				return msg

		else:
			# If the person is asking for a round or season

			page_number = 1
			round_number = False
			season_name = " ".join(args[1:])

			# Checks if the last argument is a round number or page
			if (is_int(args[-1])
			or (args[-1].lower().startswith("r")
			and is_int(args[-1][1:]))):

				if (level > 2 
				and is_int(args[-2])
				or (args[-2].lower().startswith("r")
				and is_int(args[-2][1:]))):

					season_name = " ".join(args[1:-2])

					if is_int(args[-2]):
						round_number = int(args[-2])
					else:
						round_number = int(args[-2][1:])

					page_number = int(args[-1])
				
				else:
					season_name = " ".join(args[1:-1])

					if is_int(args[-1]):
						round_number = int(args[-1])
					else:
						round_number = int(args[-1][1:])
			
			# If the season doesn't exist
			if not (defacto_season := DATA.is_valid_season(season_name)):
				await message.channel.send(
				f"Could not find **`{season_name}`** in the season list.")
				return
			
			# List of rounds for reference ahd info
			round_list = sorted(DATA.season_rounds(defacto_season), key=lambda m: m[1])

			# If no round number was specified, return season summary
			if not round_number:
				_, data_count, start_date, late_date, avg_str = DATA.season_info(defacto_season)

				msg = f"```md\n# Here are all the rounds of {defacto_season}.\n"
				msg += f"# Rounds: {data_count}\n"
				msg += f"# Avg. Strength: {avg_str:.2f}\n\n"

				msg += (
				f"From < {DATES.as_FULL(start_date)} > to < {DATES.as_FULL(late_date)} >\n\n")

				msg += (
				"|   Date   ||  Number      ||  Size    || Round Str\n")

				for number, date, size, strength in round_list:
					msg += (
					f"[{DATES.as_YMD(date)}]:  Round {number:<3}   ||  {size:<3}     ||  {strength:.2f}\n")
				
				msg += "```"

				await message.channel.send(msg)
				return

			# If the round does not exist
			if not (round_info := DATA.round_info(defacto_season, round_number)):
				await message.channel.send(
				f"There is no Round **`{round_number}`** in **{defacto_season}**.")
				return
			
			round_date, rankings, gains, strength = round_info
			round_date = DATES.to_ID(round_date)

			sorting = [
				# Category, ascending label, descending label, default rev
				["rank", "best performance", "worst performance", False],
				["name", "alphabetical order", "reverse-alphabetical order", False],
				["RM change", "largest loss", "highest gain", True],
				["player RM", "weakest player", "strongest player", True],
			]

			sort_info = [0, False]

			data_count = len(rankings)

			per_page = 15
			total_pages = int(np.ceil(data_count / per_page))

			if not 1 <= page_number <= total_pages:
				await message.channel.send(
				f"There is no page **`{page_number}`** in this round!")
				return
			
			# Find average matchup certainty weight - for performance calculation
			round_overall_g = []
			for p in rankings:
				RD = DATA.player_info(p, DATES.day_before(round_date))[2]
				round_overall_g.append(CALC.G(RD))
			
			round_overall_g = np.mean(round_overall_g)

			performances = []
			for R in range(data_count):
				NR = (data_count - 1 - R) / (data_count - 1)
				
				if NR == 1:
					performances.append("[+∞]")
				elif NR == 0:
					performances.append("[-∞]")
				else:
					performances.append(round(
					5 * CALC.performance(NR, strength/5 + 100, round_overall_g)
					))
			
			# Wrapper function to customize page generation
			def gen_page(p_n, sort=0, rev=False):
				msg = f"```md\n# {defacto_season} Round {round_number}\n"
				msg += f"({DATES.as_FULL(round_date)})\n"
				msg += f"Strength: {strength:.2f} Score ({strength + 500:.2f} RM)\n\n"

				rev = sorting[sort][3] ^ rev
				
				RM_before = []
				for cont in rankings:
					RM_before.append(DATA.player_info(cont, DATES.day_before(round_date), convert=True)[1])
				
				all_info = list(zip(range(1, 1+data_count), rankings, gains, RM_before, performances))

				all_info = sorted(all_info, key=lambda m: m[sort], reverse=rev)
				
				info_subset = all_info[per_page*(p_n - 1):per_page*p_n]

				msg += (
				"Rank |         Player         || RM Change ( Before // After  ) ||  N.R.  || Performance\n")

				for rank, name, gain, RM_before, RM_level in info_subset:
					gain_sign = "+" if gain >= 0 else "-"
					abs_gain = np.abs(round(gain, 2))

					NR_raw = (data_count - rank)/(data_count - 1)
					NR = f"{100*NR_raw:.3f}"[:5]

					RM_after = f"{RM_before + gain:.2f}"
					RM_before = f"{RM_before:.2f}"

					rank_tag = f"[{rank:>3}]:"

					msg += (
					f"{rank_tag}  {name[:21]:<21} || {gain_sign} {abs_gain:<7} ({RM_before:>7} -> {RM_after:<7}) || {NR}% || {RM_level:>6} RM\n")
				
				# Show page information if there's more than one
				if total_pages > 1:
					msg += (
					f"\n< Page [{p_n} / {total_pages}] -- Players [{per_page*(p_n - 1)+1} ~ {min(data_count, per_page*p_n)}] of [{data_count}] >")
				
				# Show player sorting information
				msg += (
				f"\n< [{sorting[sort][0].upper()}] type sorting -- ordered by [{sorting[sort][1 + int(rev)].upper()}] >")
				
				msg += "```"

				return msg

		# Generate the page with the page function given
		page = gen_page(page_number, sort=sort_info[0], rev=sort_info[1])

		page_msg = await message.channel.send(page)
		await page_msg.edit(content=page)

		reaction_list = ['⬅️', '➡️', '⏺️', '↕️']

		if total_pages > 1:
			await page_msg.add_reaction('⬅️')
			await page_msg.add_reaction('➡️')
		if data_count > 1:
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
	BOT.add_cog(roundinfo(BOT))