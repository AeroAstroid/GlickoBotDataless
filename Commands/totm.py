import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES

import numpy as np
import asyncio

class totm(commands.Cog):
	"""
	Displays a list of the best TWOWers ranked by their performance in a specific month
	"""

	FORMAT = "[year] [month]"

	USAGE = """Using `gl/totm YEAR MONTH` outputs a list of TWOWers ranked on their 
	performance in that month. The performance is measured by the RM they'd have at 
	the end of the month if they started the month with 4500 RM and 875 RD, increasing 
	and decreasing according to the rounds they played. /ln/ The list is divided into 
	pages which can be navigated using the ⬅️ and ➡️ reactions.
	""".replace("\n", "").replace("\t", "").replace(" /ln/ ", "\n")


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="totm", aliases=['twowerofthemonth'])
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		# Needs at least 3 arguments: command, year, month
		if level < 3:
			await message.channel.send(
			"Include a year and month!")
			return
		
		try:
			year, month = [int(x) for x in args[-2:]]

		except ValueError:
			year, month = args[1:3]
			await message.channel.send(
			f"**`Year {year}, Month {month}`** is not a valid month!")
			return
		
		month_ind = month - 1 + 12 * (year - 2016)

		# If the month picked is before the MIN_DATE
		if month_ind < 0:
			await message.channel.send(
			f"You can't pick a month before {DATES.as_FULL(DATES.MIN_DATE, only_month=True)}!")
			return
		
		# If the month picked is after the MAX_DATE
		if month_ind > DATES.month_diff(DATES.MAX_DATE, DATES.MIN_DATE):
			await message.channel.send(
			f"You can't pick a month after {DATES.as_FULL(DATES.MAX_DATE, only_month=True)}!")
			return
		
		TOTM = DATA.TOTM[month_ind]

		current_results = sorted([
			[cont, info*5]
			for cont, info in TOTM.items()
		], reverse=True, key=lambda m: m[1])
		
		total_players = len(current_results) 

		msg = "```md\n"
		msg += "# TWOWers of the Month\n"
		msg += f"< {DATES.as_FULL([year, month, 1])} >\n"
		msg += f"-> {total_players} players\n\n"

		msg += "|Rank|            Player           ||   Rating"

		per_page = 30
		total_pages = int(np.ceil(total_players / per_page))

		def gen_page(p_n):
			subset = current_results[(p_n-1)*per_page:p_n*per_page]
			add_msg = "\n"

			for ind, cont in enumerate(subset):
				rank = per_page * (p_n - 1) + ind + 1

				add_msg += (
				f"[{rank:>3}]:  {cont[0][:26]:<26} || {cont[1]:.2f} RM\n")
			
			# Add page info if there's more than one
			if total_pages > 1:
				add_msg += "\n"
				add_msg += (
				f"< Page [{p_n} / {total_pages}] -- Players [{(p_n-1)*per_page+1} ~ {rank}] of [{total_players}] >")
			
			add_msg += "```"

			return msg + add_msg
		
		page_number = 1
		page = gen_page(page_number)

		page_msg = await message.channel.send(page)
		await page_msg.edit(content=page)

		reaction_list = ['⬅️', '➡️']
		
		if total_pages > 1:
			await page_msg.add_reaction('⬅️')
			await page_msg.add_reaction('➡️')

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

				page = gen_page(page_number)
				await page_msg.edit(content=page)
				continue


def setup(BOT):
	BOT.add_cog(totm(BOT))