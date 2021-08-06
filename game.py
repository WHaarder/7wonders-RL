#!/usr/bin/python
#
# Copyright 2015 - Jonathan Gordon
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This software is distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY
# KIND, either express or implied.

import random

from common import *
from cards import helpers
from players import *
import logger
import pandas as pd
import numpy as np
import inspect


def init_games():
	global __all_cards
	global __all_wonders

	__all_cards = helpers.read_cards_file("card-descriptions.txt")
	__all_wonders = Wonders.read_wonders_file("wonders.txt")

class GameState:
	def __init__(self, players):

		self.player_count = len(players)
		self.players = []
		self.ages = []
		self.decks = [[]] * len(players)
		self.discard_pile = []
		self.logger = logger.Logger()
		for i in range(len(players)):
			name, persona, arg = players[i]
			self.players.append(Players.Player(name))
			if inspect.isclass(persona):
				self.players[i].set_personality(persona(arg))
			else:
				self.players[i].set_personality(persona)
		
	def setup_age_cards(self, cards):
		age_1 = [c for c in cards if c.age == 1 and c.players <= self.player_count]
		age_2 = [c for c in cards if c.age == 2 and c.players <= self.player_count]
		age_3 = [c for c in cards if c.age == 3 and c.get_colour() != CARDS_PURPLE and c.players <= self.player_count]
		purple = [c for c in cards if c.age == 3 and c.get_colour() == CARDS_PURPLE and c.players <= self.player_count]

		random.shuffle(age_1)
		random.shuffle(age_2)
		random.shuffle(purple)
		age_3 += purple[0 : self.player_count + 2]
		random.shuffle(age_3)
		
		self.ages = [age_1, age_2, age_3]
	
	def deal_age_cards(self, age):
		cards = self.ages[age][0:]
		p = 0
		for i in range(self.player_count):
			self.decks[i] = []
		while len(cards):
			self.decks[p].append(cards[0])
			p += 1
			p %= self.player_count
			cards = cards[1:]
	
	def _get_west_player(self, playerid):
		return self.players[(playerid + self.player_count - 1) % self.player_count]

	def _get_east_player(self, playerid):
		return self.players[(playerid + 1) % self.player_count]
	
	def play_turn(self, offset):
		for i in range(self.player_count):
			player = self.players[i]
			west_player = self._get_west_player(i)
			east_player = self._get_east_player(i)
			deckid = (i + offset) % self.player_count
			#player.print_tableau()
			# This loop is actually wrong.
			# Everyone should choose the card they will play, server
			# validates the move is legal, then each player plays the card
			# Then each player adds the new card to their tableau
			while True:
				action, card = player.play_hand(self.decks[deckid], west_player, east_player)
				if action == ACTION_PLAYCARD:
					can_buy = False
					# see if the player can buy the card
					if player.can_build_with_chain(card):
						can_buy = True
						self.logger.log_buy_card_with_chain(player, card)
					else:
						buy_options = player.buy_card(card, west_player, east_player)
						if len(buy_options) == 0:
							continue
						self.logger.log_buy_card(player, card, buy_options[0])
						can_buy = True
						player.money -= buy_options[0].total_cost
						east_player.money += buy_options[0].east_cost
						west_player.money += buy_options[0].west_cost
					if can_buy:
						card.play(player, west_player, east_player)
						player.get_cards().append(card)
						break
				elif action == ACTION_DISCARD:
					self.logger.log_action(player, action, card)
					self.discard_pile.append(card)
					player.money += 3
					break
				elif action == ACTION_STAGEWONDER:
					self.logger.log_action(player, action, card)
					# make sure we can do that
					break
			self.decks[deckid].remove(card)
			
	
	def game_loop(self):
		for age in range(3):
			self.logger.log_age_header(age)
			self.deal_age_cards(age)
			offset = 0
			while len(self.decks[0]) > 1:
				self.play_turn(offset);
				offset = (offset + [1, self.player_count - 1, 1][age]) % self.player_count
			# everyone discards the last card
			for p in range(self.player_count):
				self.discard_pile.append(self.decks[p][0])
			
			# score military
			for p in range(self.player_count):
				west = self._get_west_player(p)
				east = self._get_east_player(p)
				player = self.players[p]
				player_strength, opponent_strength, score = helpers.score_military(player, west, age)
				self.logger.log_military_battle(player.get_name(), player_strength, west.get_name(), opponent_strength, score)
				self.players[p].military.append(score)
				player_strength, opponent_strength, score = helpers.score_military(player, east, age)
				self.logger.log_military_battle(player.get_name(), player_strength, east.get_name(), opponent_strength, score)
				self.players[p].military.append(score)
                
		self.count_scores()
		self.find_winner()
		self.reinforcement_q_update()
            
	def count_scores(self):
		self.max_score = 0
		for i in range(self.player_count):
			player = self.players[i]
			west = self._get_west_player(i)
			east = self._get_east_player(i)
			score = 0
			bluescore = helpers.score_blue(player)
			(_,_,_,), greenscore = helpers.score_science(player)
			score += greenscore
			redscore = 0
			for military in player.military:
				redscore += military
			moneyscore = player.money / 3
			yellowscore = helpers.score_yellow(player, west, east)
			purplescore = helpers.score_purple(player, west, east)
			#player.print_tableau()
			totalscore = bluescore + greenscore + redscore + moneyscore + yellowscore + purplescore
			player.score = totalscore
			text = "Final score: Blue: %d, Green: %d, red: %d, yellow: %d, purple: %d, $: %d, total: %d" % (bluescore, greenscore, redscore, yellowscore, purplescore, moneyscore, totalscore)
			self.logger.log_freetext(player.get_name() + " " + text)
			#print (text)
			if totalscore > self.max_score:
				self.max_score = totalscore
		
		logfile = open("logfile.txt", "w")
		self.logger.dump(logfile)
		logfile.close()

	def find_winner(self):
		temp_frame = pd.DataFrame()
		for i in range(self.player_count):
			self.players[i].status = "looser"
			temp_frame=temp_frame.append({"player": int(i), "score": self.players[i].score}, ignore_index = True)
		self.possible_winners=temp_frame.loc[temp_frame["score"] == temp_frame["score"].max(),'player']
		if len(self.possible_winners) == 1: 
			self.players[self.possible_winners.index[0]].status = "winner"
		else:
			for i in range(len(self.possible_winners)):
				self.players[self.possible_winners.index[i]].status = "draw"

				
			
	def reinforcement_q_update(self): #brug score????
		#print("==============")
		for player in self.players:
			if player.personality.is_rl_ai:
				#if player.status == "winner":
					#print("Winner: " + player.name + ". Score:  " + str(player.score))
				player.personality.reward = player.score
				#elif player.status == "draw":
				#	player.personality.reward = 0
				#else:
				#	player.personality.reward = -1
					#print("Looser: " + player.name + ". Score:  " + str(player.score))
				player.personality.store() 
		#print("==============")
                    
				#td_delta = player.reward - player.personality.Q[player.personality.state][player.personality.action] 
				#player.personality.Q[player.personality.state][player.personality.action] += alpha * td_delta 
import matplotlib.pyplot as plt


plt.style.use('ggplot')

def movingaverage(interval, window_size):
	window= np.ones(int(window_size))/float(window_size)
	return np.convolve(interval, window, 'valid')

init_games()
game_first = GameState([("Alice", Personalities.StupidAI,""), 
					("Bobby", Personalities.StupidAI,""), 
					("DJ Kaffe", Personalities.Q_learning_agent,__all_cards),
					("Bob", Personalities.Q_learning_agent,__all_cards),
					("Frank", Personalities.Q_learning_agent,__all_cards)])
game_first.logger.card_list = __all_cards
game_first.setup_age_cards(__all_cards)
game_first.game_loop()


agents = []
for game_player in game_first.players:
	agent = game_player.personality 
	agents.append(agent)



batch_size = 64
num_of_episodes = 1000000

wins_frank = 0
wins_bob = 0
wins_dj_kaffe = 0
score_frank = []


from pylab import plot, ylim, xlim, show, xlabel, ylabel, grid
line = []

for e in range(0, num_of_episodes):

	game_next = GameState([("Alice", agents[0],""), 
						("Bobby", agents[1],""),
						("DJ Kaffe", agents[2],""),
						("Bob", agents[3],""),
						("Frank", agents[4],"")])
	game_next.logger.card_list = __all_cards
	game_next.setup_age_cards(__all_cards)
	game_next.game_loop() 

	
	agents = []
	for game_player in game_next.players:
		agent = game_player.personality
		agents.append(agent)

	if game_next.players[3].status == "winner":
		wins_frank +=1
	if game_next.players[4].status == "winner":
		wins_bob +=1
	if game_next.players[2].status == "winner":
		wins_dj_kaffe +=1
	score_frank.append(game_next.players[4].score)
	if e % 25 == 0:
		score_frank_avg = movingaverage(score_frank, 200)
		plot(score_frank)
		plot(score_frank_avg)
		show()
		print("Frank wins: "+ str(wins_frank))
		print("Bob wins: " + str(wins_bob))
		print("DJ Kaffe wins: " + str(wins_dj_kaffe))


	if len(agents[2].expirience_replay) > 50:
		agents[2].train(batch_size)
		agents[3].train(batch_size)
		agents[4].train(batch_size)



#p = game.players[0]
#p.money = 10
#p.tableau += [find_card(__all_cards, "quarry"), find_card(__all_cards, "clay pit"), find_card(__all_cards, "press")]
#game.players[1].tableau += [find_card(__all_cards, "glassworks"), find_card(__all_cards, "sawmill"), find_card(__all_cards, "foundry")]

#p.buy_card(find_card(__all_cards, "fortification"), game.players[1], game.players[2])

#game.players[0].tableau += [find_card(__all_cards, "study"), find_card(__all_cards, "lodge"), find_card(__all_cards, "scientist guild")]
#print helpers.score_science(game.players[0])
