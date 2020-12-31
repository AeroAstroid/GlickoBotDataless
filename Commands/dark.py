import discord
from discord.ext import commands

from Functions.data import DATA
from Functions.dates import DATES

import random

class dark(commands.Cog):
	"""
	Dark
	"""

	FORMAT = ""

	USAGE = "Dark"


	def __init__(self, BOT):
		self.BOT = BOT
	

	@commands.command(name="dark")
	async def output(self, ctx):
		message = ctx.message
		args = ctx.message.content.split(" ")
		level = len(args)
		server = ctx.guild
		
		await self.run_command(message, args, level, server)
		return
	

	async def run_command(self, message, args, level, server):
		chosen_date = random.randrange(DATES.day_diff(
			DATES.MAX_DATE, DATA.starting_date("Dark")
		))
		chosen_date = DATES.date_add(DATA.starting_date("Dark"), chosen_date)

		dark_rank = DATA.player_rank("Dark", chosen_date)
		score, RM, RD, RP = DATA.player_info("Dark", chosen_date, convert=True)

		lucky_dark = (f"""
		
		<@{message.author.id}> you have found the lucky 1/150 small dark!
		https://cdn.discordapp.com/attachments/480838129465688064/770002490287849502/BabyDark.png
		""".replace("\t", "")) if random.randrange(150) == 1 else ''

		minecraft_pig = (f"""
		
		<@{message.author.id}> you have found the lucky 1/50 minecraft pig!
		https://media.discordapp.net/attachments/322051492548837376/610511067868823562/image0.gif?comment=Pigs_are_common_passive_mobs_that_spawn_in_the_Overworld._They_drop_porkchops_upon_death,_and_can_be_ridden_with_saddles._Pigs_typically_appear_in_the_Overworld_in_groups_of_4._They_randomly_oink._Pigs_move_similarly_to_other_passive_mobs;_they_wander_aimlessly,_and_avoid_lava_and_cliffs_high_enough_to_cause_fall_damage._They_make_no_attempt_to_stay_out_of_water,_bobbing_up_and_down_to_stay_afloat._When_they_encounter_obstacles,_pigs_often_hop_up_and_down,_apparently_attempting_to_jump_over_them_regardless_of_whether_it_is_possible._Pigs_can_be_pushed_into_minecarts_and_transported_by_rail._Pigs_follow_any_player_carrying_a_carrot,_carrot_on_a_stick,_potato,_or_beetroot,_and_stops_following_if_the_player_moves_farther_than_approximately_8_blocks_away_from_the_pig._When_a_pig_is_struck_by_lightning_or_hit_by_a_trident_with_the_Channeling_enchantment_during_a_thunderstorm,_it_transforms_into_a_zombie_pigman._If_the_pig_was_equipped_with_a_saddle,_the_saddle_is_lost,_and_a_mounted_player_is_ejected._Pigs_can_be_bred_using_carrots,_potatoes,_and_beetroots._It_takes_about_5_minutes_before_the_parents_can_be_bred_again,_as_with_all_farm_animals._It_takes_at_least_one_full_Minecraft_%27day%27_(20_minutes)_for_piglets_to_mature._The_appearance_of_a_piglet_is_roughly_similar_to_that_of_an_adult_pig,_having_the_same_sized_heads,_but_noticeably_smaller_bodies._Piglets_stay_near_their_parents_until_they_mature,_although_the_parents_cannot_protect_them_from_harm
		""".replace("\t", "")) if random.randrange(50) == 1 else ''

		await message.channel.send(f"dark {DATES.as_FULL(chosen_date).lower()}\n" +
		f"#{dark_rank} - {score} - {RM} - {RD} - {RP}" + lucky_dark + minecraft_pig)
		return


def setup(BOT):
	BOT.add_cog(dark(BOT))