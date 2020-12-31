import numpy as np

class CALC():
	"""
	Class with several functions and variables for Glicko-related calculations
	"""

	Q = np.log(10) / 400	# General calibration constant
	C = 30.6186218			# RD decay constant (250 RD -> 875 RD in 2.5 years)

	@classmethod
	def performance(cls, NR, strength, round_G):
		"""Calculates the RM level performance of an NR in a certain round strength

		Mathematically, this is also the inverse of the E formula in terms of RM0"""

		p = (round_G * strength * np.log(10) - 400 * np.log(1 / NR - 1))
		p /= (round_G * np.log(10))

		return p


	@classmethod
	def win_chance(cls, player1, player2, convert=False):
		"""Calculates player 1's win chance in a match against player 2
		
		Adapted from the E formula"""

		convert = 5 if convert else 1

		RM_1, RD_1 = [value / convert for value in player1[1:3]]
		RM_2, RD_2 = [value / convert for value in player2[1:3]]

		combined_RD = np.sqrt(RD_1 ** 2 + RD_2 ** 2)
		chance_1 = 1 / (1 + 10 ** (- cls.G(combined_RD) * (RM_1 - RM_2) / 400))

		return chance_1


	@classmethod
	def E(cls, RM_1, RM_2, RD_2, convert=False):
		"""Player 1's expected score against player 2"""

		convert = 5 if convert else 1

		RM_1 /= convert
		RM_2 /= convert
		RD_2 /= convert

		expected = 1 / (1 + 10 ** (- cls.G(RD_2) * (RM_1 - RM_2) / 400))

		return expected


	@classmethod
	def G(cls, RD):
		"""Calculates the matchup certainty weight for a given RD"""

		result = np.sqrt(1 / (1 + 3 * cls.Q**2 * RD**2 / np.pi**2))

		return result
	

	@classmethod
	def decay_RD(cls, RD, days=1):
		"""Decays an RD value by a given number of days"""

		for _ in range(days):
			if RD < 50:
				RD = (29 * RD + 50) / 30
			
			RD = np.sqrt(RD**2 + cls.C**2/30)
			RD = min(175, RD)
		
		return RD
	

	@classmethod
	def round_weight(cls, cont_count):
		"""Returns the matchup weight for a round of a given size"""

		if cont_count < 5:
			w_i = cont_count - 1
		else:
			w_i = 0.0547 * cont_count + 4 * np.sqrt(cont_count) - 5.7663

		return w_i