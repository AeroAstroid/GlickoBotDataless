from dateutil.relativedelta import relativedelta as delta
import datetime as dt

class DATES():
	"""
	Wrapper class for various datetime functions

	Built for easy conversion between TWOW Glicko date IDs,
	datetime objects, and [year, month, day] lists
	"""

	MIN_DATE = 160101	# First ever TWOW round
	MAX_DATE = 201130	# Current point of data

	MIN_YEAR = 2000		# Minimum and maximum values that are
	MAX_YEAR = 2099		# considered years when parsing
	
	@classmethod
	def as_YMD(cls, date):
		"""Write any date type in YYYY-MM-DD format"""

		date = cls.to_YMD(date)

		date = '-'.join([f'{a:02}' for a in date])

		return date


	@classmethod
	def as_FULL(cls, date, only_month=False):
		"""Write any date type in full Month Day Year format"""

		date = cls.to_DT(date)
		
		date = date.strftime("%B %Y" if only_month else "%B %d %Y")

		return date
	

	@classmethod
	def time_lookup_range(cls, tb1, tb2):
		"""Return a specialized lookup range [day range, month index range]
		from two arbitrary YMD lists"""

		early_bound = cls.time_range(*tb1)[0]
		late_bound = cls.time_range(*tb2)[1]

		early_month = cls.month_diff(early_bound, cls.MIN_DATE)
		late_month = cls.month_diff(late_bound, cls.MIN_DATE)

		return [[early_bound, late_bound], [early_month, late_month]]


	@classmethod
	def time_range(cls, year, month=None, day=None):
		"""Take a single arbitrary time and output its day range"""

		early_bound = [
			year,								# A year is mandatory and contains its own bound
			(1 if month is None else month),	# If it's just a year, start from month 1
			(1 if day is None else day)			# If it's just a month, start from day 1
		]

		late_bound = [
			year,								# A year is mandatory and contains its own bound
			(12 if month is None else month),	# If it's just a year, end at month 12
			(31 if day is None else day)		# If it's just a month, end at day 31
		]

		# Iteratively check if late_bound is a valid date (sometimes it's
		# not because it always assumes the month ends on a day 31 if unspecified)
		while True:
			try:
				final_day = cls.to_DT(late_bound)
				break # When a valid final_day is found, break the loop
				
			except ValueError:
				# If the date is invalid, deincrement a day and try again
				late_bound[2] -= 1
		
		final_day = cls.to_ID(final_day)
		start_day = cls.to_ID(early_bound)

		return [start_day, final_day]


	@classmethod
	def day_diff(cls, later, prior):
		"""Difference in days between two dates of any type"""

		later = cls.to_DT(later)
		prior = cls.to_DT(prior)
		
		diff = (later - prior).days

		return diff
	
	
	@classmethod
	def month_diff(cls, later, prior):
		"""Difference in months between two dates of any type"""

		later = cls.to_DT(later)
		prior = cls.to_DT(prior)
		
		month_diff = delta(later, prior).months
		month_diff += delta(later, prior).years * 12

		return month_diff


	@classmethod
	def date_add(cls, date, days=0, months=0, years=0):
		"""Add a certain number of days, months or years to any date type"""

		parsed_date = cls.to_DT(date)
		
		parsed_date += delta(days=days, months=months, years=years)
		
		# Convert parseddate back to whichever format the original date was
		if isinstance(date, int):
			parsed_date = cls.to_ID(parsed_date)
		elif isinstance(date, list):
			parsed_date = cls.to_YMD(parsed_date)
		
		return parsed_date


	@classmethod
	def day_before(cls, date):
		"""A 'yesterday' function for convenience"""

		return cls.date_add(date, days=-1)
	

	"""
	---> General conversion functions
	"""

	@classmethod
	def to_DT(cls, date):
		"""Converts any date type to DT"""

		if isinstance(date, int): 		# Date ID to DT
			date = cls.ID_to_DT(date)
		elif isinstance(date, list):	# YMD list to DT
			date = cls.YMD_to_DT(date)
		
		return date
	

	@classmethod
	def to_ID(cls, date):
		"""Converts any date type to date ID"""

		if isinstance(date, dt.date):	# DT to date ID
			date = cls.DT_to_ID(date)
		elif isinstance(date, list):	# YMD list to date ID
			date = cls.YMD_to_ID(date)
		
		return date
	

	@classmethod
	def to_YMD(cls, date):
		"""Converts any date type to YMD list"""

		if isinstance(date, dt.date):	# DT to YMD list
			date = cls.DT_to_YMD(date)
		elif isinstance(date, int):		# Date ID to YMD list
			date = cls.ID_to_YMD(date)
		
		return date
	

	"""
	---> Individual conversion functions
	"""

	@classmethod
	def YMD_to_DT(cls, ymd_list):
		"""Converts YMD list to DT"""

		year, month, day = ymd_list

		date = dt.date(year, month, day)

		return date
	

	@classmethod
	def YMD_to_ID(cls, ymd_list):
		"""Converts YMD list to date ID"""

		year, month, day = ymd_list

		date_ID = 10000 * (year % 100) + 100 * month + day

		return date_ID
	

	@classmethod
	def DT_to_ID(cls, date):
		"""Converts DT to date ID"""

		date_ID = int(date.strftime('%y%m%d'))

		return date_ID
	

	@classmethod
	def DT_to_YMD(cls, date):
		"""Converts DT to YMD list"""

		ymd_list = [date.year, date.month, date.day]

		return ymd_list
	

	@classmethod
	def ID_to_DT(cls, date_ID):
		"""Converts date ID to DT"""

		date_ID = str(date_ID)

		year, month, day = (date_ID[:2], date_ID[2:4], date_ID[4:])
		year = '20' + year

		date = dt.date(int(year), int(month), int(day))

		return date
	
	@classmethod
	def ID_to_YMD(cls, date_ID):
		"""Converts date ID to YMD list"""

		date_ID = str(date_ID)

		year, month, day = (date_ID[:2], date_ID[2:4], date_ID[4:])
		year = '20' + year

		ymd_list = [int(year), int(month), int(day)]

		return ymd_list