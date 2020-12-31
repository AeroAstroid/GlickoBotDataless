import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES

import asyncio

class seasonlist(commands.Cog):
	"""
	Displays the list of seasons in the TWOW Glicko data.
	"""

	FORMAT = "(page)"

	USAGE = """Using `gl/seasonlist` will display a paged list of all seasons 
	that make up the TWOW Glicko data. Adding a number, like `gl/seasonlist 6`, 
	will take you to the corresponding page. /ln/ You can also navigate the pages 
	using the ⬅️ and ➡️ reactions. /ln/ By default, the list is sorted 
	alphabetically. You can cycle through different sorting methods with the ⏺️ 
	reaction, and you can reverse the current sorting with the ↕️ reaction.
	""".replace("\n", "").replace("\t", "").replace(" /ln/ ", "\n")


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="seasonlist", aliases=['s', 'sl', 'season', 'seasons'])
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		sorting = [
			# Category, ascending label, descending label, default rev
			["name", "alphabetical order", "reverse-alphabetical order", False],
			["round count", "shortest", "longest", True],
			["start date", "oldest", "newest", False],
			["average strength", "weakest", "strongest", True]
		]
		
		sort_info = [0, False]

		page_number = 1

		# Check if a page was specified (argument past 1)
		if level > 1:
			if not is_int(args[-1]):
				await message.channel.send(
				f"**`{args[-1]}`** is not a valid page number!")
				return
			
			page_number = int(args[-1])
		
		season_list = DATA.all_seasons(verbose=True)
		per_page = 20
		total_pages = len(season_list) // per_page + 1

		# Check if a requested page number is actually valid
		if not 1 <= page_number <= total_pages:
			await message.channel.send(
			f"There is no page **`{page_number}`** of the seasons list!")
			return
		
		msg = "```md\n"
		msg += "# Glicko Season List\n"
		msg += f"-> {len(season_list)} seasons\n\n"

		msg += (
		"|Pos.|          Season         || Rounds || Starting Day -> Latest Round ||  Avg Str\n")
		
		# Wrapper function to customize page generation
		def gen_page(p_n, sort=0, rev=False):
			rev = sorting[sort][3] ^ rev

			real_sort = sort
			# Skip over season_info index 3 in sorting
			if sort >= 3:
				real_sort += 1
			
			season_subset = sorted(season_list, key=lambda m: m[real_sort], reverse=rev)
			season_subset = season_subset[per_page*(p_n - 1):per_page*p_n]
			
			add_msg = ""

			for ind, season_info in enumerate(season_subset):
				name, round_count, start_date, end_date, avg_str = season_info

				pos = ind + 1 + per_page*(p_n - 1)

				start_date = DATES.as_YMD(start_date)
				end_date = DATES.as_YMD(end_date)

				add_msg += (
				f"[{pos:3}]:  {name:<22} ||   {round_count:02}   || [{start_date}] -> [{end_date}] ||  {avg_str:.2f}\n")
			
			add_msg += "\n"

			# Show page information
			bounds = [
				per_page * (p_n - 1) + 1,
				min(per_page * p_n, len(season_list))
			]
			add_msg += (
			f"< Page [{p_n} / {total_pages}] -- Seasons [{bounds[0]} ~ {bounds[1]}] of [{len(season_list)}]>\n")

			# Show season sorting information
			add_msg += (f"< [{sorting[sort][0].upper()}] type sorting -- ordered by [{sorting[sort][1 + int(rev)].upper()}] >\n")
			
			add_msg += "```"

			return msg + add_msg
		
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
	BOT.add_cog(seasonlist(BOT))