from discord.ext import commands
from PIL import ImageFont

"""
Miscellaneous helper functions
"""

def is_int(n):
	"""Determines if a value is a valid integer"""

	try:
		int(n)
		return True
	except ValueError:
		return False

def r_int(n):
	"""round() but it returns an integer"""

	return int(round(n))

def ensure_perms():
	"""Decorator for staff commands"""

	def is_staff(ctx):
		return ctx.message.author.id in [
			# Everyone with bot staff permissions
			184768535107469314
		]
	return commands.check(is_staff)

# Returns the Assistant font in the given size
Assistant = lambda size: ImageFont.truetype("Images/Fonts/Assistant-Regular.ttf", size)

# Returns the Assistant Bold font in the given size
AssistantBold = lambda size: ImageFont.truetype("Images/Fonts/Assistant-Bold.ttf", size)