import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES
from Functions.general import is_int, r_int, Assistant, AssistantBold

from PIL import Image, ImageDraw
import os
import numpy as np

class graph(commands.Cog):
	"""
	Draws a graph of a player's score, RD, RM or RP over time.
	"""

	FORMAT = "[players] (date) to (date) (statistic)"

	USAGE = """Using `gl/graph PLAYER` shows a graph of the player's score 
	throughout the last month in the data. Including two YYYY MM DD dates 
	separated by "to", i.e. `gl/graph PLAYER DATE1 to DATE2`, allows you to 
	graph the player's score between those two dates. You can graph different 
	statistics by including "RM", "RD", or "RP" at the end of the command, 
	e.g. `gl/graph PLAYER RD`. You can also graph up to 5 players at a time 
	by listing all of their names separated by "vs" or "vs.", i.e. `gl/graph 
	PLAYER1 vs PLAYER2 vs PLAYER3`.""".replace("\n", "").replace("\t", "")


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="graph", aliases=['g'])
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
			"Include the name of the contestant whose graph you want to see!")
			return
		
		available_stats = ["Score", "RM", "RD", "RP", "Rank"]

		# If one of the stats was explicitly chosen
		if args[-1].lower() in [arg.lower() for arg in available_stats]:
			chosen_stat = [arg.lower() for arg in available_stats].index(
				args[-1].lower())
			
			args = args[:-1]
			level = len(args)
		
		else:	# Default to 0 (score) otherwise
			chosen_stat = 0
		
		stat_name = available_stats[chosen_stat]

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

		cont_args = list(reversed(cont_args))

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
			start_date, end_date = [DATES.MIN_DATE, DATES.MAX_DATE]	# Range between 1st and last day

		elif len(time_list) == 1:
			# If only one time was specified, the range is the span of that time
			start_date, end_date = DATES.time_lookup_range(
				time_list[0],
				time_list[0]
			)[0]

		else:
			# If both times were specified, calculate the range they span
			start_date, end_date = DATES.time_lookup_range(
				time_list[0],
				time_list[1]
			)[0]

			# Check that their order isn't reversed
			if start_date > end_date:
				start_date, end_date = DATES.time_lookup_range(
					time_list[1],
					time_list[0]
				)[0]
		
		end_date = min(end_date, DATES.MAX_DATE)

		# For cases where the range is only one day
		if start_date == end_date:
			await message.channel.send(
			"Pick a range longer than a single day!")
			return
		
		# Parse "vs" and "vs."
		cont_args = [arg if arg.lower() not in ["vs.", "vs"] else "vs" for arg in cont_args]

		if "vs" in cont_args:
			vs_indices = [ind for ind, arg in enumerate(cont_args) if arg == "vs"]
			vs_indices = [v for v in vs_indices if v != 0 and v != len(cont_args) - 1]

			# More than 4 vs -> more than 5 players
			if len(vs_indices) > 4:
				await message.channel.send(
				"You can only compare 5 players at once.")
				return

			usernames = []

			for vs_ind in range(len(vs_indices) + 1):
				if vs_ind == 0: # If this is the first "vs"
					f_name = " ".join(
					cont_args[:vs_indices[0]])

				elif vs_ind == len(vs_indices):	# If this is the last "vs"
					f_name = " ".join(
					cont_args[vs_indices[-1]+1:])

				else:	# If it's an inbetween "vs"
					f_name = " ".join(
					cont_args[vs_indices[vs_ind-1]+1:vs_indices[vs_ind]])

				# Check if the requested player actually exists
				if not (cont := DATA.true_name(f_name)):
					await message.channel.send(
					f"Could not find a player named **`{f_name}`** in the data.")
					return
				
				usernames.append(cont)

		else:
			f_name = " ".join(cont_args)

			# Check if the requested player actually exists
			if not (cont := DATA.true_name(f_name)):
				await message.channel.send(
				f"Could not find a player named **`{f_name}`** in the data.")
				return
			
			usernames = [cont]
		
		starting_dates = [DATA.starting_date(name) for name in usernames]

		for ind, dt in enumerate(starting_dates):
			if DATES.to_ID(end_date) < dt:
				await message.channel.send(
				f"**`{usernames[ind]}`** only started playing on **{DATES.to_FULL(dt)}**!")
				return

		# Make sure no usernames repeat
		usernames = [
			name
			for ind, name in enumerate(usernames) 
			if usernames.index(name) == ind			# Check if this is the first occurance of the name
		]
		
		# Initialize an array to contain all the dates spanned
		all_days = [end_date]
		
		data_points = []

		for name in usernames:
			if chosen_stat < 4:
				data_points.append(
					[DATA.player_info(name, end_date, convert=True)[chosen_stat]]
				)
			else:
				data_points.append(
					[DATA.player_rank(name, end_date)]
				)
		
		# List to detect if the algorithm is done compiling
		# a given player's statistics
		player_done = [False for _ in usernames]

		while True:
			# Move back one day
			iterated_date = DATES.day_before(all_days[-1])

			# End data gathering if we've reached the starting date
			if iterated_date < start_date:
				break

			for ind, name in enumerate(usernames):
				# If data gathering for this player is done
				if player_done[ind]:
					continue
				
				# If the stat is not rank
				if chosen_stat < 4:
					player_info = DATA.player_info(name, iterated_date, convert=True)
					
					# Check if the player was unranked (a.k.a. a default player)
					if player_info == DATA.DEFAULT_PLAYER_C:
						player_done[ind] = True
						continue
					
					data_point = player_info[chosen_stat]
				
				else:	# If the stat is rank
					# Check if the player was unranked (rank is False)
					if not (data_point := DATA.player_rank(name, iterated_date)):
						player_done[ind] = True
						continue
				
				data_points[ind].append(data_point)

			# If none of the players had data gathered for this day
			if all(player_done):
				# Backtrack to the day iterated before, which was the
				# last day with recorded data
				start_date = DATES.date_add(iterated_date, days=1)
				break
			
			all_days.append(iterated_date)
		
		# Define what constitutes the "Best" label
		peak_function = max if (chosen_stat not in [2, 4]) else min
		peaks = [peak_function(player_data) for player_data in data_points]

		# Find overall min-max points for the graph
		max_points = max([max(p_data) for p_data in data_points])
		min_points = min([min(p_data) for p_data in data_points])
		
		data_range = max_points - min_points

		# Score ranges outside RP and Rank below 25 are
		# considered exceptionally small
		if data_range < 25 and chosen_stat not in [3, 4]:
			data_range = 25
			max_points, min_points = [ 
				(max_points + min_points) / 2 + 12.5,	# Average the extreme points to get
				(max_points + min_points) / 2 - 12.5	# a midpoint; ensure a 25 data_range
			]

		elif data_range < 3 and chosen_stat == 3:
			# For RP, ranges below 3 are small
			data_range = 3
			max_points, min_points = [
				(max_points + min_points) / 2 + 1.5,
				(max_points + min_points) / 2 - 1.5
			]

		# Sets the minimum number of divisions and a base value for
		# intervals between each y-axis marking. This is further
		# adjusted depending on the stat and exact data range value
		div_target = 7
		intervals = data_range / div_target

		if chosen_stat in [0, 1, 3]:
			# SCORE (0), RM (1) and RP (3) scale algorithm

			if data_range < 15:
				# For very zoomed-in scales, just make the intervals 1
				intervals = 1
			
			else:
				# For normal scales of all three stats

				# Provides an integer progression that rises at
				# 25, 50, 100, 200, 400, 800, 1600, 3200, so on
				i = np.floor(np.log2(intervals / 12.5))

				# Raising 2 to its power returns us to approximations
				# of the original [intervals / 12.5] values, but
				# "floored" to the power of 2 below it 
				i = np.power(2, i)

				# Multiplying by 2.5, rounding up then by 5 adjusts
				# for the lower values of initial intervals and ensures
				# that the final interval size never increases above
				# the initial one unless the intervals were too small
				# to work with (intervals < 15)
				intervals = int(np.ceil(2.5 * i) * 5)
			
			# The highest marking that's below the minimum value on the graph
			# (plus the one below it to draw on the outside of the graph)
			lower_interval_index = int(np.ceil(min_points/intervals-1))

			# The lowest marking above the maximum value (plus one more above it)
			upper_interval_index = int(np.ceil(max_points/intervals+1))

			y_markers = [
				round(ind * intervals)	# Multiply the indices by the interval size
				for ind in range(		# to get the actual y-axis marking values
					lower_interval_index, upper_interval_index
				)
			]

		elif chosen_stat in [2, 4]:
			# RD (2) and RANKS (4) have their own hardcoded scales

			if chosen_stat == 2:
				# The RD scale
				scale_marks = [175, 200, 250, 350, 500, 650, 875]

			else:
				# The RANKS scale
				scale_marks = [
					1, 2, 5, 10, 25, 50, 100, 150, 200,
					300, 400, 500, 750, 1000, 1500, 2000,
					2500, 3000, 4000, 5000
				]

			# Find the minimum and maximum markings for the min and max graph values
			min_scale = [x for x in scale_marks if x <= min_points][-1]
			max_scale = [x for x in scale_marks if x > min_scale and x >= max_points][0]

			min_ind, max_ind = [scale_marks.index(min_scale), scale_marks.index(max_scale)]
			
			# If there are too many markings (11 or above -- happens only with RANKS graphs)
			if max_ind - min_ind > 10:
				# Use a condensed scale instead
				scale_marks = [
					1, 10, 50, 100, 250, 500,
					1000, 1500, 2500, 3750, 5000
				]

				# Perform the same calculations
				min_scale = [x for x in scale_marks if x <= min_points][-1]
				max_scale = [x for x in scale_marks if x > min_scale and x >= max_points][0]

				min_ind, max_ind = [scale_marks.index(min_scale), scale_marks.index(max_scale)]
			
			# Add them to the y_markers list
			y_markers = scale_marks[min_ind:max_ind+1]

		# Open the base image for the graph
		graph_base = Image.open("Images/new_graph_base.png")

		# Layer for graph text
		text_img = Image.new("RGBA", graph_base.size, (0, 0, 0, 0))
		text_draw = ImageDraw.Draw(text_img)

		# Layer for graph lines
		lines_img = Image.new("RGBA", graph_base.size, (0, 0, 0, 0))
		lines_draw = ImageDraw.Draw(lines_img)

		extremes = {	# Helpful graph coordinates
			"y_in": [160, 515],		# Y bounds *inside* the graph
			"y_out": [126, 549],	# Y bounds *outside* the graph
			"x_in": [85, 565],		# X bounds *inside* the graph
			"x_out": [51, 599]		# X bounds *outside* the graph
		}

		for ind, mark in enumerate(y_markers):

			if chosen_stat in [2, 4]:
				# Marker placement for RD (2) and RANKS (4)
				# is linear going down from 0% to 100%
				data_pct = ind / (len(y_markers) - 1)

			else:
				# For other stats, use the max_points and min_points
				# as 0% and 100% references for data_pct
				data_pct = (max_points - mark) / (max_points - min_points)
			
			# Calculate the position in pixels to draw the marker
			data_pos = extremes["y_in"][0] + data_pct * (extremes["y_in"][1] - extremes["y_in"][0])

			lines_draw.line(
				(extremes["x_out"][0], data_pos,
				extremes["x_out"][1], data_pos),
			fill=(220, 220, 230, 90), width=4)

			x, _ = text_draw.textsize(str(mark), AssistantBold(25))

			# To make an outline draw text in different angles, circling
			# around where the main text will be
			outline = 5
			for step in range(10):
				angle = step * 2 * np.pi / 10

				text_draw.text(
					(30 - r_int(x/2) - outline * np.cos(angle),
					data_pos - 17 - outline * np.sin(angle)),
				str(mark), (20, 20, 30), AssistantBold(25))

			# Draw main text
			text_draw.text((30 - r_int(x/2), data_pos - 17),
			str(mark), (220, 220, 230), AssistantBold(25))
		
		line_mask = Image.open("Images/line_mask.png")
		text_mask = Image.open("Images/text_mask.png")

		# Transparency object to use as the lower layer for opacity masks
		transp = Image.new("RGBA", graph_base.size, (0, 0, 0, 0))
		lines_img = Image.composite(lines_img, transp, line_mask)
		text_img = Image.composite(text_img, transp, text_mask)

		# Text to be overlaid atop other elements
		top_text_img = Image.new("RGBA", graph_base.size, (0, 0, 0, 0))
		top_text_draw = ImageDraw.Draw(top_text_img)

		outline = 9
		for step in range(20):
			angle = step * 2 * np.pi / 20

			top_text_draw.text(
				(15 - outline * np.cos(angle),
				53 - outline * np.sin(angle)),
			f"{DATES.as_FULL(start_date)} to {DATES.as_FULL(end_date)}",
			(40, 40, 70), AssistantBold(35))
		
		for step in range(20):
			angle = step * 2 * np.pi / 20

			top_text_draw.text(
				(15 - outline * np.cos(angle),
				5 - outline * np.sin(angle)),
			f"{stat_name} graph over {len(all_days)} days",
			(40, 40, 70), AssistantBold(45))

		top_text_draw.text((15, 53),
		f"{DATES.as_FULL(start_date)} to {DATES.as_FULL(end_date)}",
		(220, 220, 230), AssistantBold(35))

		top_text_draw.text((15, 5),
		f"{stat_name} graph over {len(all_days)} days",
		(220, 220, 230), AssistantBold(45))

		# Colors to draw the graph with
		if len(usernames) == 1:
			colors = [
				(220, 220, 220)		# White
			]

		else:
			colors = [
				(120, 230, 120),	# Green
				(230, 120, 120),	# Red
				(120, 120, 230),	# Blue
				(230, 220, 120),	# Yellow
				(220, 120, 230)		# Pink
			]

		user_stats = []
		
		for player_ind, score_list in enumerate(data_points):
			line_path = []

			for day_ind, score in enumerate(score_list):

				if chosen_stat in [2, 4]:
					# Score placement for RD (2) and RANKS (4)
					base_ind = len([y for y in y_markers if y < score])

					if base_ind != len(y_markers):
						# Find the score's position inbetween its neighboring markers
						# Note: distances inbetween adjacent markers are always linear,
						# even if the intervals between markers are not constant
						total_diff = (y_markers[base_ind] - score)
						diff_proportion = total_diff / (y_markers[base_ind] - y_markers[base_ind - 1])

						# Find the score's position across the entire list of markers
						data_pct = (base_ind - diff_proportion) / (len(y_markers) - 1)

					else:
						# Anything past the last marker is automatically 100%
						data_pct = 1
					
				else:
					# For other stats, use the max_points and min_points
					# as 0% and 100% references for data_pct
					data_pct = (max_points - score) / (max_points - min_points)
				
				# Calculate the position in pixels to draw the marker
				data_pos = extremes["y_in"][0] + data_pct * (extremes["y_in"][1] - extremes["y_in"][0])

				# Find x position of the current day across the entire day range
				x_pct = (len(all_days) - 1 - day_ind) / (len(all_days) - 1)
				x_pos = extremes["x_in"][0] + x_pct * (extremes["x_in"][1] - extremes["x_in"][0])
				
				# Store the final (index 0) position of the line
				if day_ind == 0:
					ending_pos = np.array([x_pos, data_pos])

				# Add another point for the line to pass through
				line_path.append((x_pos, data_pos))
			
			user_stats.append([
				usernames[player_ind],	# Name
				score_list[0],			# Current score
				peaks[player_ind],		# Best score
				ending_pos				# Position of last score
			])

			# Draw the whole line
			top_text_draw.line(
				tuple(line_path),
				fill=colors[player_ind],
				width=6, joint="curve")

			# Background-colored "outline" circle
			top_text_draw.ellipse(
				(ending_pos[0] - 8, ending_pos[1] - 8,
				ending_pos[0] + 8, ending_pos[1] + 8),
			fill=(20, 20, 30))

			# Marking circle
			top_text_draw.ellipse(
				(ending_pos[0] - 6, ending_pos[1] - 6,
				ending_pos[0] + 6, ending_pos[1] + 6),
			fill=colors[player_ind])

		if chosen_stat in [0, 1, 3]:
			# For SCORE (0), RM (1), RP (3), higher is better
			user_stats = sorted(user_stats, reverse=True, key=lambda e: e[1])

		else:
			# For RD (2), RANKS (4), lower is better
			user_stats = sorted(user_stats, key=lambda e: e[1])

		y_center = (125 + 425 / 2)

		# Layer for the "tether" connecting the info box to the last marker
		connect_img = Image.new("RGBA", graph_base.size, (0, 0, 0, 0))
		connect_draw = ImageDraw.Draw(connect_img)

		for player_ind, info in enumerate(user_stats):
			player, score, peak, target_pos = info
			user_ind = usernames.index(player)

			# Find the center of this index's info box
			this_center = r_int(y_center - 42.5 * (len(usernames) - 1 - player_ind) + 42.5 * player_ind)

			# Position of the left side of the info box
			current_pos = np.array([618, this_center])

			distance = np.sqrt((target_pos[0] - current_pos[0])**2 + (target_pos[1] - current_pos[1])**2)
			step_total = r_int(distance / 1.2)

			# Draw the circles composing the "tether"
			for step in range(step_total):
				pct = step / step_total
				pos = (1 - pct) * current_pos + pct * target_pos

				size = 6 - np.abs(4 - (step / 1.5) % 8)

				connect_draw.ellipse(
					(r_int(pos[0] - size/2), r_int(pos[1] - size/2),
					r_int(pos[0] + size/2), r_int(pos[1] + size/2)),
				fill=colors[user_ind] + (80,))
			
			# Draw a width-1 brighter line connecting them
			connect_draw.line((tuple(current_pos), tuple(target_pos)),
			colors[user_ind] + (150,), width=1)

			# Ellipse on the left of the box
			top_text_draw.ellipse(
				(612, this_center - 15, 
				640, this_center + 15),
				fill=colors[user_ind])

			# Background-color "outline" rectangle
			top_text_draw.rectangle(
				(618, this_center - 37,
				792, this_center + 37),
			fill=(20, 20, 30, 200),
			outline=colors[user_ind],
			width=6)

			# Player-colored info box outlines
			top_text_draw.rectangle(
				(625, this_center - 30,
				785, this_center + 30),
			outline=colors[user_ind],
			width=4)

			# Draw the player name with adaptive font size to ensure it fits
			font_size = 30
			x, _ = top_text_draw.textsize(player, AssistantBold(font_size))

			if x > 140:
				font_size = int(np.floor(font_size * 140 / x))
				x, _ = top_text_draw.textsize(player, AssistantBold(font_size))
			
			top_text_draw.text(
				(705 - r_int(x / 2),
				this_center - 12 - r_int(font_size * 0.7)),
			player, colors[user_ind],
			AssistantBold(font_size))

			if chosen_stat != 3:
				# Draw Current and Best labels
				x, _ = top_text_draw.textsize("Current", AssistantBold(10))
				top_text_draw.text(
					(670 - r_int(x/2),
					this_center - 2),
				"Current", colors[user_ind],
				AssistantBold(10))

				x, _ = top_text_draw.textsize(str(round(score)), AssistantBold(15))
				top_text_draw.text(
					(670 - r_int(x/2),
					this_center + 7),
				str(round(score)), colors[user_ind],
				AssistantBold(15))

				x, _ = top_text_draw.textsize("Best", AssistantBold(10))
				top_text_draw.text(
					(740 - r_int(x/2),
					this_center - 2),
				"Best", colors[user_ind],
				AssistantBold(10))

				x, _ = top_text_draw.textsize(str(round(peak)), AssistantBold(15))
				top_text_draw.text(
					(740 - r_int(x/2),
					this_center + 7),
				str(round(peak)), colors[user_ind],
				AssistantBold(15))

			else:
				# Draw the round number label

				plural = '' if score == 1 else 's'

				x, _ = top_text_draw.textsize(f"{score} round{plural}", AssistantBold(18))
				top_text_draw.text(
					(705 - r_int(x / 2),
					this_center),
				f"{score} round{plural}", colors[user_ind],
				AssistantBold(18))

		# Add all layers in order
		graph_base.paste(lines_img, (0, 0), lines_img)
		graph_base.paste(text_img, (0, 0), text_img)
		graph_base.paste(connect_img, (0, 0), connect_img)
		graph_base.paste(top_text_img, (0, 0), top_text_img)
		
		graph_base.save(f"Graph {message.id}.png")
		await message.channel.send(
		file=discord.File(f"Graph {message.id}.png"))
		os.remove(f"Graph {message.id}.png")

		return


def setup(BOT):
	BOT.add_cog(graph(BOT))