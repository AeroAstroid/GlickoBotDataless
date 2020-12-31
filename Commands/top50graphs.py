import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES
from Functions.general import r_int, is_int, Assistant, AssistantBold, ensure_perms

from PIL import Image, ImageDraw
import os
import numpy as np

class top50graphs(commands.Cog):
	"""
	Command description
	"""

	FORMAT = ""

	USAGE = ""


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="top50graphs", hidden=True)
	@ensure_perms()
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		# Needs at least 2 arguments: command, date ID
		if level < 2:
			await message.channel.send("Include date!")
			return
		
		if not is_int(args[1]):
			await message.channel.send("Invalid date!")
			return
		
		date = int(args[1])

		limit = 50
		if level == 3 and is_int(args[2]):
			limit = int(args[2])

		# Top 50. Reversed so #50 is the first graph generated
		current_top_50 = reversed(DATA.date_leaderboard(
			date, limit=limit, cutoff=True))
		
		# Constants for the base graph images
		graph_shear = 37
		graph_slope = graph_shear / 183

		graph_base = Image.open("Images/graph_base.png")
		graph_mask = Image.open("Images/graph_mask.png")
		transparent = Image.new("RGBA", graph_base.size, (0, 0, 0, 0))

		graph_min, graph_max = [30, 150]

		for player, score, _, _, _ in current_top_50:
			score_points = [score]

			# Iteratively step back a day to get all scores in the month
			for step_back in range(1, DATES.to_DT(date).day + 1):
				current_day = DATES.date_add(date, days=-step_back)

				day_score = DATA.player_info(player, current_day, convert=True)[0]

				score_points.append(day_score)

			max_score = max(score_points)
			min_score = min(score_points)
			score_range = max_score + min_score

			if score_range < 100:
				# For a small range, ensure it's at least 100
				avg = min_score + score_range / 2

				series_min, series_max = [avg - 60, avg + 60]	# Bounds of the score series
				label_min, label_max = [avg - 100, avg + 100]	# Bounds of where markings are drawn

			else:
				series_min, series_max = [
					min_score - 25,
					max_score + 25
				]
				label_min, label_max = [
					min_score - score_range / 3,
					max_score + score_range / 3
				]

			score_points = list(reversed(score_points))

			# Labels are drawn on an upright image then skewed
			labels = Image.new("RGBA", (60, 183), (0, 0, 0, 0))
			draw = ImageDraw.Draw(labels)

			score_range = series_max - series_min
			
			if score_range < 125: intervals = 25
			elif score_range < 300: intervals = 50
			elif score_range < 550: intervals = 100
			elif score_range < 1100: intervals = 150
			else: intervals = 250

			minor_label_lower = int(np.ceil(label_min / intervals))
			minor_label_upper = int(np.ceil(label_max / intervals))

			major_label_lower = int(np.ceil(label_min / (2 * intervals)))
			major_label_upper = int(np.ceil(label_max / (2 * intervals)))

			minor_label_range = [
				ind * intervals
				for ind in range(minor_label_lower, minor_label_upper)
			]
			major_label_range = [
				ind * intervals * 2
				for ind in range(major_label_lower, major_label_upper)
			]
			
			lines_base = Image.new("RGBA", graph_base.size, (0, 0, 0, 0))
			lines_draw = ImageDraw.Draw(lines_base)

			# Minor graph marks
			for mark in minor_label_range:
				# Calculate the position in percentage of the graph
				y_pct = 1 - (mark - series_min) / (series_max - series_min)

				y_pos = r_int(y_pct * (graph_max - graph_min) + graph_min)
				x_off = r_int(graph_shear * (1 - y_pct))	# Offset due to graph shear

				# Minor graph marks contain major ones, so check if this
				# is also a major marking and treat it differently
				if mark in major_label_range:
					# Draw the marking value
					x, _ = draw.textsize(str(mark), AssistantBold(29))
					draw.text((30 - r_int(x/2), y_pos - 20),
						str(mark), (96, 106, 229), AssistantBold(29))
					
					# Draw the marking line
					lines_draw.line((90 + 160 + x_off, y_pos, 900, y_pos),
					fill=(96, 106, 229, 100), width=5)
				
				else:
					# Draw the marking value
					x, _ = draw.textsize(str(mark), AssistantBold(22))
					draw.text((30 - r_int(x/2), y_pos - 16),
						str(mark), (96, 106, 229, 190), AssistantBold(22))
					
					# Draw the marking line
					lines_draw.line((90 + 160 + x_off, y_pos, 900, y_pos),
					fill=(96, 106, 229, 50), width=5)

			# Shearing the label image to look in line with the background
			new_width = 60 + graph_shear
			labels = labels.transform(
				(new_width, 183),
				Image.AFFINE, (
					1, graph_slope,
					-graph_shear if graph_slope > 0 else 0,
					0, 1, 0),
				Image.BICUBIC
			)

			line_path = []

			for ind, score in enumerate(score_points):
				y_pct = 1 - (score - series_min) / (series_max - series_min)
				y_pos = r_int(y_pct * (graph_max - graph_min) + graph_min)

				x_off = graph_shear * (1 - y_pct)
				x_base = 265 + (825 - 265) * (ind/(len(score_points)-1))

				line_path.append((r_int(x_base + x_off), y_pos))

			lines_draw.ellipse(
				(line_path[0][0]-9, line_path[0][1]-9,
				line_path[0][0]+9, line_path[0][1]+9),
				fill=(0, 0, 0, 0)
			)
			lines_draw.ellipse(
				(line_path[-1][0]-9, line_path[-1][1]-9,
				line_path[-1][0]+9, line_path[-1][1]+9),
				fill=(0, 0, 0, 0)
			)

			lines_draw.line(
				tuple(line_path),
				fill=(0, 0, 0, 0),
				width=17, joint="curve"
			)
			# Draw the series
			lines_draw.line(
				tuple(line_path),
				fill=(96, 106, 229),
				width=9, joint="curve"
			)

			# Paste the labels and mask them to confine them to the background
			lines_base.paste(labels, (13+160, 0), labels)
			lines_base = Image.composite(lines_base, transparent, graph_mask)

			'''# Paste in the series line
			current_graph = graph_base.copy()
			current_graph.paste(lines_base, (0, 0), lines_base)'''
			current_graph = lines_base

			# Send the graph along with the player's name
			current_graph.save(f"graph_{player}.png")
			await message.channel.send(f"**{player}**",
			file=discord.File(f"graph_{player}.png"))
			os.remove(f"graph_{player}.png")
		
		await message.channel.send(
		f"Done generating graphs for {DATES.as_FULL(date)}!")


def setup(BOT):
	BOT.add_cog(top50graphs(BOT))