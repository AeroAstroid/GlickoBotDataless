import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES

import numpy as np
import asyncio
import os

class finales(commands.Cog):
	"""
	Shows a list of all of a player's finales - defined as rounds with only two players.
	"""

	FORMAT = "[player]"

	USAGE = """Using `gl/finales PLAYER` outputs a list of all "finales" they've 
	competed in (defined as any round with only two people, not necessarily just 
	the final round of a season). /ln/ Long lists are divided into pages that you 
	can navigate using the ⬅️ and ➡️ reactions. /ln/ By default, the list is sorted 
	by oldest round. You can cycle through different sorting methods with the ⏺️ 
	reaction, and you can reverse the current sorting with the ↕️ reaction. /ln/ 
	Including 'file' on the end of the command, i.e. `gl/finales PLAYER file` outputs 
	the entire finale list in a text file.
	""".replace("\n", "").replace("\t", "").replace(" /ln/ ", "\n")


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="finales", aliases=['f'])
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
			"Include the name of the contestant whose finales you want to see!")
			return
		
		# Check if the user requests a file output
		make_file = False
		if args[-1].lower() == "file":
			make_file = True
			args = args[:-1]
			level = len(args)
		
		raw_cont_name = " ".join(args[1:])

		# Check if player exists
		if not (username := DATA.true_name(raw_cont_name)):
			await message.channel.send(
			f"Could not find a player named **`{raw_cont_name}`** in the data.")
			return

		sorting = [
			# Category, ascending label, descending label, whether default reversed
			["name", "alphabetical order", "reverse-alphabetical order", False],
			["RM change", "largest loss", "highest gain", True],
			["rank", "best rank", "worst rank", False],
			["strength", "weakest", "strongest", True],
			["date", "oldest", "newest", False]
		]

		sort_info = [4, False]

		finales = []
		round_count = 0

		for month in range(len(DATA.HISTORY)):
			if username not in DATA.HISTORY[month]:
				continue
			
			for round_name, round_info in DATA.HISTORY[month][username].items():
				round_count += 1

				if round_info[2] != 2:
					continue

				strength, date = DATA.ROUNDS[month][round_name]
				NR = 2 - round_info[1]

				finales.append([round_name] + round_info[:2] + [strength, date, NR])
				# Finales are [name, gain, rank, strength, date, NR]
		
		# Player hasn't been in any finales
		if len(finales) == 0:
			await message.channel.send(
			f"""```diff
			+ {username}``````md
			# Rounds: {round_count}
			# Finales: 0
			# Finale Ratio: 0.00%```""".replace("\t", ""))
			return

		msg = f"```diff\n+ {username}```"

		per_page = 15
		finale_count = len(finales)
		total_pages = int(np.ceil(finale_count / per_page))

		# Wrapper function to customize page generation
		def gen_page(p_n, sort=4, rev=False):
			add_msg = "```md\n"
			add_msg += f"# Rounds: {round_count}\n"
			add_msg += f"# Finales: {finale_count}\n"
			add_msg += (
			f"# Finale Ratio: {100*finale_count/round_count:.2f}%\n\n")

			w = len([f for f in finales if f[2] == 1])
			l = finale_count - w

			add_msg += f"# W/L Record: {w} / {l}\n"
			add_msg += (
			f"# W/L Ratio: {100 * w / (w + l):.2f}% / {100 * l / (w + l):.2f}%\n\n")

			rev = sorting[sort][3] ^ rev

			subset = sorted(finales, reverse=rev, key=lambda m: m[sort])
			subset = subset[per_page * (p_n - 1) : per_page * (p_n)]

			add_msg += (
			"|   Date   ||          Round Name         || RM Change ||   Ranks   ||   N.R.   || Round Str\n")

			for name, gain, rank, strength, date, NR in subset:
				full_date = DATES.as_YMD(date)

				gain_sign = "+" if gain >= 0 else "-"
				abs_gain = np.abs(round(gain, 2))

				nr_format = "100.0%" if NR == 1 else "0.000%"

				add_msg += (
				f"[{full_date}]:  {name:<26} || {gain_sign} {abs_gain:<7} || {rank:>3} / 2   ||  {nr_format}  ||  {strength:.02f}\n")
			
			add_msg += "\n"

			# Add page info if there's more than one
			if total_pages > 1:
				bounds = [
					per_page * (p_n - 1) + 1,
					min(per_page * p_n, finale_count)
				]
				add_msg += (
				f"< Page [{p_n} / {total_pages}] -- Rounds [{bounds[0]} ~ {bounds[1]}] of [{finale_count}]>\n")

			# Add finale sorting info if there's more than one
			if finale_count > 1:
				add_msg += (
				f"< [{sorting[sort][0].upper()}] type sorting -- ordered by [{sorting[sort][1 + int(rev)].upper()}] >\n")
			
			add_msg += "```"

			return msg + add_msg
		
		# File-writing routine
		if make_file:
			with open(f"{username} Finales {message.id}.txt", "a", encoding="utf-8") as file:
				sort, rev = sort_info

				file.write(f"# Rounds: {round_count}\n")
				file.write(f"# Finales: {finale_count}\n")
				file.write(
				f"# Finale Ratio: {100*finale_count/round_count:.2f}%\n\n")

				w = len([f for f in finales if f[2] == 1])
				l = finale_count - w

				file.write(f"# W/L Record: {w} / {l}\n")
				file.write(
				f"# W/L Ratio: {100 * w / (w + l):.2f}% / {100 * l / (w + l):.2f}%\n\n")

				rev = sorting[sort][3] ^ rev

				finales = sorted(finales, reverse=rev, key=lambda m: m[sort])

				file.write(
				"|   Date   ||          Round Name         || RM Change ||   Ranks   ||   N.R.   || Round Str\n")

				for name, gain, rank, strength, date, NR in finales:
					full_date = DATES.as_YMD(date)

					gain_sign = "+" if gain >= 0 else "-"
					abs_gain = np.abs(round(gain, 2))

					nr_format = "100.0%" if NR == 1 else "0.000%"

					file.write(
					f"[{full_date}]:  {name:<26} || {gain_sign} {abs_gain:<7} || {rank:>3} / 2   ||  {nr_format}  ||  {strength:.02f}\n")
			
			await message.channel.send(msg,
			file=discord.File(f"{username} Finales {message.id}.txt"))

			os.remove(f"{username} Finales {message.id}.txt")
			return
		
		page_number = 1
		page = gen_page(page_number, sort=sort_info[0], rev=sort_info[1])

		page_msg = await message.channel.send(page)
		await page_msg.edit(content=page)

		reaction_list = ['⬅️', '➡️', '⏺️', '↕️']

		if total_pages > 1:
			await page_msg.add_reaction('⬅️')
			await page_msg.add_reaction('➡️')
		if finale_count > 1:
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
	BOT.add_cog(finales(BOT))