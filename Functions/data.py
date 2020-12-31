try:
	from Functions.dates import DATES
except ModuleNotFoundError:
	from dates import DATES

import numpy as np
import json
import os

class DATA():
	"""
	Wrapper class for handling the TWOW Glicko data
	"""

	RD_CUTOFF = 500		# Sheet RD cutoff

	DEFAULT_PLAYER = [550, 900, 175, 0]			# Stat values for the default player
	DEFAULT_PLAYER_C = [2750, 4500, 875, 0]		# Default values converted to sheet scale

	with open(f'JSON Data/resultdaily.json', encoding='utf-8') as f:
		RESULTDAILY = json.load(f)
		print("Loaded RESULTDAILY.JSON")
	
	with open(f'JSON Data/history.json', encoding='utf-8') as f:
		HISTORY = json.load(f)
		print("Loaded HISTORY.JSON")
	
	with open(f'JSON Data/ranks.json', encoding='utf-8') as f:
		RANKS = json.load(f)
		print("Loaded RANKS.JSON")
	
	with open(f'JSON Data/rounds.json', encoding='utf-8') as f:
		ROUNDS = json.load(f)
		print("Loaded ROUNDS.JSON")

	with open(f'JSON Data/totm.json', encoding='utf-8') as f:
		TOTM = json.load(f)
		print("Loaded TOTM.JSON")
	
	@classmethod
	def starting_date(cls, player):
		"""Outputs the starting date of a player"""

		return cls.RESULTDAILY[player][0]
	
	
	@classmethod
	def true_name(cls, player):
		"""Convert an alias and/or arbitrary-case player name into official name"""

		PLAYERS = cls.RESULTDAILY.keys()

		# If player is already a true name
		if player in PLAYERS:
			return player
		
		player = player.lower()

		lower_names = [x.lower() for x in PLAYERS]

		# If player is an arbitrary-case variation of a true name
		if player in lower_names:
			ind = lower_names.index(player)

			return list(PLAYERS)[ind]
		
		autocompletes = [x for x in lower_names if x.startswith(player)]

		# If there's only one possible autocompletion for player
		if len(autocompletes) == 1:
			ind = lower_names.index(autocompletes[0])

			return list(PLAYERS)[ind]
		
		with open('Data/alias.txt', 'r', encoding='utf-8') as f:
			lower_aliases = f.read().lower().splitlines()

		# If player is an arbitrary-case variation of an alias
		if player in lower_aliases:
			cycled = [player]

			while lower_aliases.index(player) % 2 == 0:
				player = lower_aliases[lower_aliases.index(player) + 1]

				if player in cycled:
					break
				
				cycled.append(player)
		
		# If player is nowhere to be found in general
		if player not in lower_names:
			return False

		ind = lower_names.index(player)
		player = list(PLAYERS)[ind]
		return player
	
	"""
	---> Statistic gathering functions
	"""

	@classmethod
	def player_rank(cls, player, date):
		"""Returns the leaderboard rank of a player on a given day"""

		try:
			P_RANKS = cls.RANKS[player]
		except KeyError:	# If player does not exist
			return False

		init_date = P_RANKS[0]

		# If player hadn't played yet by the date specified
		if date < init_date:
			return False
		
		date_ind = DATES.day_diff(date, init_date)

		rank = P_RANKS[date_ind + 1]
		
		return rank


	@classmethod
	def player_info(cls, player, date, convert=False):
		"""Outputs [score, RM, RD, RP] for a player on any day
		
		Can output directly in the sheet scale if convert is activated"""

		convert = 5 if convert else 1

		try:
			PLAYER_RESULT = cls.RESULTDAILY[player]
		except KeyError:	# If player does not exist
			return False

		init_date = PLAYER_RESULT[0]
		date = DATES.to_ID(date)

		# If player hadn't played yet by the date specified
		if date < init_date:
			return cls.DEFAULT_PLAYER_C if convert else cls.DEFAULT_PLAYER
		
		date_ind = DATES.day_diff(date, init_date)

		date_info = PLAYER_RESULT[date_ind + 1]

		# Incomplete date_info means only [RD], meaning RM and RP info
		# is carried over from a previous day entry
		if len(date_info) == 1:
			RD = date_info[0]

			for step_back in range(date_ind):
				previous_info = PLAYER_RESULT[date_ind - step_back]

				if len(previous_info) > 1:
					RM, RP = previous_info[1:]
					break
			
		else:
			RD, RM, RP = date_info[:3]
		
		score = RM - 2 * RD

		return [score * convert, RM * convert, RD * convert, RP]


	@classmethod
	def date_leaderboard(cls, date, limit=False, cutoff=False):
		"""Returns the top (limit) players in TWOW Glicko in a given day
		
		If there is no limit, returns all players"""

		date = DATES.to_ID(date)

		date_rankings = []

		PLAYERS = cls.RESULTDAILY.keys()

		for player in PLAYERS:
			score, RM, RD, RP = cls.player_info(player, date, convert=True)
			
			date_rankings.append([player, score, RM, RD, RP])
		
		date_rankings = sorted(date_rankings, key=lambda m: m[1], reverse=True)

		if cutoff and min([p[3] for p in date_rankings]) < cls.RD_CUTOFF:
			date_rankings = [p for p in date_rankings if p[3] < cls.RD_CUTOFF]
		
		if limit:
			date_rankings = date_rankings[:limit]
		
		return date_rankings
	
	
	"""
	---> Helper functions for season and round information
	"""

	@classmethod
	def all_seasons(cls, verbose=False):
		"""Lists all seasons for which data is available

		If verbose, returns season_info on each one"""

		with open('Data/index.txt', 'r', encoding='utf-8') as f:
			season_list = f.read().splitlines()
		
		folder_list = os.listdir('Data')

		# Seasons that are both in the season index and have a folder
		valid_seasons = [
			season_name
			for season_name in season_list
			if cls.season_folder(season_name) in folder_list
		]

		if verbose:
			for ind, season_name in enumerate(valid_seasons):
				valid_seasons[ind] = cls.season_info(season_name)

		return valid_seasons
	
	
	@classmethod
	def season_info(cls, season):
		"""Outputs a list of overall statistics of a season"""

		raw_info = cls.season_rounds(season)

		info = [
			season,										# 0 -> Season name
			len(raw_info),								# 1 -> Amount of rounds
			min([round[1] for round in raw_info]),		# 2 -> Starting date
			max([round[1] for round in raw_info]),		# 3 -> Latest round date
			np.mean([round[3] for round in raw_info])	# 4 -> Average round strength
		]

		return info


	@classmethod
	def season_rounds(cls, season):
		"""Outputs information on each round of a season"""
		
		folder_name = cls.season_folder(season)
		round_list = os.listdir(f'Data/{folder_name}')

		all_rounds = []

		for round_file in round_list:
			with open(f'Data/{folder_name}/{round_file}', 'r', encoding='utf-8') as f:
				round_info = f.read().splitlines()

			round_number = round_file[:-4]
			full_round_name = f"{season} R{round_number}"

			round_date = int(round_info[0])
			lookup_ind = DATES.month_diff(round_date, DATES.MIN_DATE)

			# If the round isn't actually counted for TWOW Glicko
			if full_round_name not in cls.ROUNDS[lookup_ind].keys():
				continue

			contestant_count = len(round_info) - 1

			strength = cls.ROUNDS[lookup_ind][full_round_name][0]

			all_rounds.append([
				round_number,
				round_date,
				contestant_count,
				strength
			])
		
		return all_rounds


	@classmethod
	def round_info(cls, season, round_n):
		"""Outputs information on a single round and all its players"""

		folder_name = cls.season_folder(season)

		# If the round does not exist in the folder for that season
		if f"{round_n}.txt" not in os.listdir(f'Data/{folder_name}'):
			return False

		with open(f'Data/{folder_name}/{round_n}.txt', 'r', encoding='utf-8') as f:
			round_info = f.read().splitlines()

		round_date = int(round_info[0])
		lookup_ind = DATES.month_diff(round_date, DATES.MIN_DATE)

		full_round_name = f"{season} R{round_n}"

		M_ROUNDS = cls.ROUNDS[lookup_ind]
		M_HISTORY = cls.HISTORY[lookup_ind]

		# If that round was not counted for TWOW Glicko
		if full_round_name not in M_ROUNDS.keys():
			return False

		strength = M_ROUNDS[full_round_name][0]

		rankings = round_info[1:]
		RM_change = []

		for ind, name in enumerate(rankings):
			name = name.strip()

			# If this name does not map to any players
			if not (name := cls.true_name(name)):
				rankings[ind] = False
				continue
			
			# If the name does map to any players but is not in the history this month
			if name not in M_HISTORY:
				rankings[ind] = False
				continue
			
			# If name is in history but this round is not
			if full_round_name not in M_HISTORY[name]:
				rankings[ind] = False
				continue

			RM_change.append(M_HISTORY[name][full_round_name][0])

			rankings[ind] = name
		
		# Remove entries that were changed into False
		rankings = [cont for cont in rankings if cont]
		
		return [round_date, rankings, RM_change, strength]


	@classmethod
	def is_valid_season(cls, season):
		"""Determines if a season exists, and if so locates its sanitized name"""

		season = season.lower()
		dataset = cls.all_seasons()

		try:	# Check in the all_seasons dataset
			ind = [s.lower() for s in dataset].index(season)
		except ValueError:
			return False
		
		return dataset[ind]


	@classmethod
	def season_folder(cls, season):
		"""Returns corresponding folder name for a season"""

		'''# Google Drive downloads replace these characters automatically
		# I'm implementing this in the code as well for convenience
		season = season.replace("&", "_")
		season = season.replace("'", "_")'''

		# Folder names are ANSI versions of the season name
		# This is important in names like "Lé Unicorn" which get
		# converted incorrectly as folder names
		season = season.encode(encoding="utf-8")
		season = season.decode(encoding="cp1252", errors="ignore")

		return season