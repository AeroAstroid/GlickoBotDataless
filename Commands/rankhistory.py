import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES
from Functions.general import is_int

import numpy as np
import asyncio

class rankhistory(commands.Cog):
	"""
	Command description
	"""

	FORMAT = "('top') [number]"

	USAGE = """Use `gl/rankhistory NUMBER` to see a list of players and the 
	amount of days they've occupied a given rank. Using `gl/rankhistory top 
	NUMBER` outputs a similar list but where they've occupied any rank equal 
	to or below `NUMBER`. /ln/ For long lists, the list is divided into pages 
	that you can navigate using the ⬅️ and ➡️ reactions. /ln/ By default, 
	the list is sorted by the most prominent player (most days). You can cycle 
	through different sorting methods with the ⏺️ reaction, and you can reverse 
	the current sorting with the ↕️ reaction.
	""".replace("\n", "").replace("\t", "").replace(" /ln/ ", "\n")


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="rankhistory", aliases=['ranks', 'rank'])
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		# Needs at least 2 arguments: command, number
		if level < 2:
			await message.channel.send(
			"Include a rank you want to search for!")
			return
		
		look_above = False
		if args[1].lower() == "top":
			args = [args[0]] + args[2:]
			level -= 1
			look_above = True
		
		if not is_int(requested := args[1]):
			await message.channel.send(
			f"**`{requested}`** is not a valid rank number!")
			return
		
		requested = int(requested)

		day_counts = []

		RANKS = DATA.RANKS

		for player, rank_h in RANKS.items():
			all_ranks = [
				r for r in rank_h[1:]
				if (r == requested
				or (r < requested and look_above))
			]

			if len(all_ranks) != 0:
				day_counts.append(
					[player,						# Player name
					len(all_ranks),					# How many times in that rank
					len(all_ranks)/len(rank_h[1:])	# % of their total time in that rank
				])
		
		sorting = [
			# Category, ascending label, descending label, default rev
			["name", "alphabetical order", "reverse-alphabetical order", False],
			["days", "shortest time", "longest time", True],
			["ratio", "shortest proportional time", "longest proportional time", True]
		]

		sort_info = [1, False]
		
		total_applicable = len(day_counts)
		per_page = 20
		total_pages = int(np.ceil(total_applicable / per_page))

		if look_above:
			time_in_what = f"in the top {requested}"
		else:
			time_in_what = f"at rank #{requested}"
		
		msg = "```md\n"
		msg += f"# Players ordered by time {time_in_what}\n\n"

		msg += " Pos.|         Player         || # Days ||  Ratio\n"

		def gen_page(p_n, sort=1, rev=False):
			rev = sorting[sort][3] ^ rev

			info_subset = sorted(day_counts, key=lambda m: m[sort], reverse=rev)
			info_subset = info_subset[per_page*(p_n - 1):per_page*p_n]

			add_msg = ""

			for ind, info in enumerate(info_subset):
				name, days, ratio = info

				pos = per_page*(p_n - 1) + 1 + ind

				ratio_str = f"{ratio*100:.4f}"[:6] + "%"

				add_msg += f"[{pos:>3}]:  {name[:21]:<21} ||  {days:<4}  || {ratio_str}\n"

			# Show page information if there's more than one
			if total_pages > 1:
				bounds = [
					per_page * (p_n - 1) + 1,				# First in the page
					min(per_page * p_n, total_applicable)	# Last in the page
				]
				add_msg += (
				f"\n< Page [{p_n} / {total_pages}] -- Rounds [{bounds[0]} ~ {bounds[1]}] of [{total_applicable}]>\n")
			
			# Show player sorting information if there's more than one
			if total_applicable > 1:
				add_msg += (
				f"< [{sorting[sort][0].upper()}] type sorting -- ordered by [{sorting[sort][1 + int(rev)].upper()}] >")
			
			add_msg += "```"
			
			return msg + add_msg
		
		page_number = 1
		page = gen_page(page_number, sort=sort_info[0], rev=sort_info[1])

		page_msg = await message.channel.send(page)
		await page_msg.edit(content=page)
		
		reaction_list = ['⬅️', '➡️', '⏺️', '↕️']

		if total_pages > 1:
			await page_msg.add_reaction('⬅️')
			await page_msg.add_reaction('➡️')
		if total_applicable > 1:
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
	BOT.add_cog(rankhistory(BOT))