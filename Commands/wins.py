import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES

import numpy as np
import asyncio
import os

class wins(commands.Cog):
	"""
	Shows a list of all of a player's round wins.
	"""

	FORMAT = "[player] ('file')"

	USAGE = """Using `gl/wins PLAYER` outputs a list of rounds they've won. /ln/ 
	Long lists are divided into pages that you can navigate using the ⬅️ and ➡️ 
	reactions. /ln/ By default, the list is sorted by oldest round. You can cycle 
	through different sorting methods with the ⏺️ reaction, and you can reverse 
	the current sorting with the ↕️ reaction. /ln/ Including 'file' on the end of 
	the command, i.e. `gl/wins PLAYER file` outputs the entire win list in a text 
	file.""".replace("\n", "").replace("\t", "").replace(" /ln/ ", "\n")


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="wins", aliases=['w'])
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
			"Include the name of the contestant whose wins you want to see!")
			return
		
		# Check if the user requested file output
		make_file = False
		if args[-1].lower() == "file":
			make_file = True
			args = args[:-1]
			level = len(args)
		
		cont_args = " ".join(args[1:])

		# Check if the player exists
		if not (username := DATA.true_name(cont_args)):
			await message.channel.send(
			f"Could not find a player named **`{cont_args}`** in the data.")
			return

		sorting = [
			# Category, ascending label, descending label, default rev
			["name", "alphabetical order", "reverse-alphabetical order", False],
			["RM change", "largest loss", "highest gain", True],
			["rank", "best rank", "worst rank", False],
			["round size", "smallest", "largest", True],
			["strength", "weakest", "strongest", True],
			["date", "oldest", "newest", False]
		]

		sort_info = [5, False]

		wins = []
		round_count = 0

		for month in range(len(DATA.HISTORY)):
			# Make sure the user participated this month
			if username not in DATA.HISTORY[month]:
				continue
			
			for round_name, round_info in DATA.HISTORY[month][username].items():
				round_count += 1

				gain, rank, size = round_info

				if rank != 1:
					continue

				strength, date = DATA.ROUNDS[month][round_name]

				wins.append([round_name, gain, rank, size, strength, date])
		
		# If the player has no wins
		if len(wins) == 0:
			await message.channel.send(
			f"""```diff
			+ {username}``````md
			# Rounds: {round_count}
			# Wins: 0
			# Win Ratio: 0.00%```""".replace("\t", ""))
			return

		msg = f"```diff\n+ {username}```"

		rounds_per_page = 20
		total_wins = len(wins)
		total_pages = int(np.ceil(total_wins  / rounds_per_page))

		def gen_page(p_n, sort=5, rev=False):
			add_msg = "```md\n"
			add_msg += f"# Rounds: {round_count}\n"
			add_msg += f"# Wins: {total_wins}\n"
			add_msg += f"# Win Ratio:  {100*total_wins/round_count:.2f}%\n\n"

			rev = sorting[sort][3] ^ rev

			subset = sorted(wins, reverse=rev, key=lambda m: m[sort])
			subset = subset[rounds_per_page * (p_n - 1) : rounds_per_page * (p_n)]

			add_msg += (
			"|   Date   ||          Round Name         || RM Change ||   Ranks   || Round Str\n")

			for name, gain, rank, size, strength, date in subset:
				full_date = DATES.as_YMD(date)

				gain_sign = "+" if gain >= 0 else "-"
				abs_gain = np.abs(round(gain, 2))

				add_msg += f"[{full_date}]:  {name:<26} || {gain_sign} {abs_gain:<7} || {rank:>3} / {size:<3} ||  {strength:.02f}\n"
			
			add_msg += "\n"

			if total_pages > 1:
				bounds = [
					rounds_per_page * (p_n - 1) + 1,
					min(rounds_per_page * p_n, total_wins)
				]
				add_msg += (
				f"< Page [{p_n} / {total_pages}] -- Rounds [{bounds[0]} ~ {bounds[1]}] of [{total_wins}]>\n")

			if total_wins > 1:
				add_msg += (
				f"< [{sorting[sort][0].upper()}] type sorting -- ordered by [{sorting[sort][1 + int(rev)].upper()}] >\n")
			
			add_msg += "```"

			return msg + add_msg
		
		if make_file:
			with open(f"{username} Wins {message.id}.txt", "a", encoding="utf-8") as file:
				file.write(f"# Rounds: {round_count}\n")
				file.write(f"# Wins: {total_wins}\n")
				file.write(f"# Win Ratio:  {100*len(wins)/round_count:.2f}%\n\n")

				rev = sorting[sort_info[0]][3] ^ sort_info[1]

				wins = sorted(wins, reverse=rev, key=lambda m: m[sort_info[0]])

				file.write(
				"|   Date   ||          Round Name         || RM Change ||   Ranks   || Round Str\n")

				for name, gain, rank, size, strength, date in wins:
					full_date = DATES.as_YMD(date)

					gain_sign = "+" if gain >= 0 else "-"
					abs_gain = np.abs(round(gain, 2))

					file.write(
					f"[{full_date}]:  {name:<26} || {gain_sign} {abs_gain:<7} || {rank:>3} / {size:<3} ||  {strength:.02f}\n")
			
			await message.channel.send(msg,
			file=discord.File(f"{username} Wins {message.id}.txt"))
			os.remove(f"{username} Wins {message.id}.txt")
			return
		
		page_number = 1
		page = gen_page(page_number, sort=sort_info[0], rev=sort_info[1])

		page_msg = await message.channel.send(page)
		await page_msg.edit(content=page)

		reaction_list = ['⬅️', '➡️', '⏺️', '↕️']

		if total_pages > 1:
			await page_msg.add_reaction('⬅️')
			await page_msg.add_reaction('➡️')
		if total_wins > 1:
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
	BOT.add_cog(wins(BOT))