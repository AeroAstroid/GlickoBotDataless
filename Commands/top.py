import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES

import numpy as np
import asyncio

class top(commands.Cog):
	"""
	Shows a leaderboard of all TWOW Glicko players at a specific date.
	"""

	FORMAT = "[date] ('cutoff')"

	USAGE = """Using `gl/top` with a YYYY MM DD date - say, `gl/top25 2020 7 28`, 
	will return the full TWOW Glicko leaderboard for that day. Including `cutoff` 
	at the end of the command applies the standard 500 RD cutoff used in the sheet. 
	/ln/ The leaderboard is divided into pages which can be navigated using the ⬅️ 
	and ➡️ reactions. /ln/ By default, the list is sorted by highest score. You can 
	cycle through different sorting methods with the ⏺️ reaction, and you can 
	reverse the current sorting with the ↕️ reaction.
	""".replace("\n", "").replace("\t", "").replace(" /ln/ ", "\n")


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="top", aliases=['t', 'leaderboard', 'lb'])
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		RD_cutoff = False
		if args[-1].lower() == "cutoff":
			RD_cutoff = True
			args = args[:-1]
			level = len(args)
		
		# Needs at least 4 arguments: command, year, month, day
		if level < 4:
			await message.channel.send(
			"Include the date for which you want to see a leaderboard!")
			return
		
		try:
			ymd_list = [int(x) for x in args[-3:]]
		except ValueError:
			ymd_list = ', '.join([f'`{arg}`' for arg in args[-3:]])
			await message.channel.send(
			f"Could not interpret {ymd_list} as a year, month and date!")
			return
		
		try:
			DATES.to_DT(ymd_list)
		except ValueError:
			await message.channel.send(
			f"`{DATES.as_YMD(ymd_list)}` is an invalid date!")
			return
		
		requested = DATES.to_ID(ymd_list)

		if requested < DATES.MIN_DATE:
			await message.channel.send(
			f"Can't get information for dates before {DATES.as_FULL(DATES.MIN_DATE)}")
			return

		if requested > DATES.MAX_DATE:
			await message.channel.send(
			f"No info available for dates past {DATES.as_FULL(DATES.MAX_DATE)}!")
			return
		
		sorting = [
			# Category, ascending label, descending label, default rev
			["name", "alphabetical order", "reverse-alphabetical order", False],
			["score", "worst score", "best score", True],
			["RM", "worst RM", "best RM", True],
			["RD", "most active", "most inactive", False],
			["RP", "least rounds played", "most rounds played", True]
		]

		sort_info = [1, False]

		all_players = DATA.date_leaderboard(requested, cutoff=RD_cutoff)

		msg = "```md\n"
		msg += "# TWOW Glicko Leaderboard\n"
		msg += f"< {DATES.as_FULL(requested)} >```"

		msg += "```c\n"
		msg += "# Rank    Contestant               Score       RM        RD      RP\n"

		per_page = 25
		player_count = len(all_players)
		total_pages = int(np.ceil(player_count / per_page))

		def gen_page(p_n, sort=1, rev=False):
			rev = sorting[sort][3] ^ rev

			player_subset = sorted(all_players, key=lambda m: m[sort], reverse=rev)
			player_subset = player_subset[per_page*(p_n-1):per_page*p_n]

			add_msg = ""

			for rank, info in enumerate(player_subset):
				p_rank = per_page * (p_n - 1) + rank + 1
				name, score, RM, RD, RP = info

				add_msg += (
				f"# {p_rank:<4} || {name[:20]:<20} || {score:.2f} || {RM:.1f} || {RD:.1f} || {RP}\n")
			
			bounds = [
				per_page * (p_n - 1) + 1,
				min(per_page * p_n, player_count)
			]
			
			add_msg += "``````md\n"
			add_msg += (
			f"< Page [{p_n} / {total_pages}] -- Players [{bounds[0]} ~ {bounds[1]}] of [{player_count}] >")
			add_msg += (
			f"\n< [{sorting[sort][0].upper()}] type sorting -- ordered by [{sorting[sort][1 + int(rev)].upper()}] >")
			
			add_msg += "```"

			return msg + add_msg
		
		page_number = 1
		page = gen_page(page_number, sort=sort_info[0], rev=sort_info[1])

		page_msg = await message.channel.send(page)
		await page_msg.edit(content=page)

		reaction_list = ['⬅️', '➡️', '⏺️', '↕️']

		for r in reaction_list:
			await page_msg.add_reaction(r)

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
	BOT.add_cog(top(BOT))