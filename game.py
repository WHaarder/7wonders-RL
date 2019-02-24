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

import math
import os
import random

import logger
from cards import helpers
from common import *
from players import *

os.system('cls')

def do_print(text):
    a = 1
    # print(text)

def init_games():
    global __all_cards
    global __all_wonders

    __all_cards = helpers.read_cards_file("card-descriptions.txt")
    __all_wonders = Wonders.read_wonders_file("wonders.txt")

class GameState:
    def __init__(self, players):

        self.old_players = players
        self.player_count = len(players)
        self.players = []
        self.ages = []
        self.decks = [[]] * len(players)
        self.discard_pile = []
        self.logger = logger.Logger()
        for i in range(len(players)):
            name, persona = players[i]
            self.players.append(Players.Player(name))
            self.players[i].set_personality(persona())
    

    def reset(self):
        self.__init__(self.old_players)
        self.setup_age_cards(self.old_cards)


    def setup_age_cards(self, cards):
        self.old_cards = cards
        age_1 = [c for c in cards if c.age == 1 and c.players <= self.player_count]
        age_2 = [c for c in cards if c.age == 2 and c.players <= self.player_count]
        age_3 = [c for c in cards if c.age == 3 and c.get_colour() != CARDS_PURPLE and c.players <= self.player_count]
        purple = [c for c in cards if c.age == 3 and c.get_colour() == CARDS_PURPLE and c.players <= self.player_count]

        random.shuffle(age_1)
        random.shuffle(age_2)
        random.shuffle(purple)
        age_3 += purple[0 : self.player_count + 2]
        random.shuffle(age_3)
        
        self.ages = [age_1, age_2, age_3].copy()
    
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
            player.print_tableau()
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
                self.play_turn(offset)
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
        final_text = ''
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
            moneyscore = math.floor(player.money / 3)
            yellowscore = helpers.score_yellow(player, west, east)
            purplescore = helpers.score_purple(player, west, east)
            player.print_tableau()
            totalscore = bluescore + greenscore + redscore + moneyscore + yellowscore + purplescore
            text = "Final score: Blue: {}, Green: {}, red: {}, yellow: {}, purple: {}, $: {}, total: {}".format(bluescore, greenscore, redscore, yellowscore, purplescore, moneyscore, totalscore)
            final_text += player.name + '\t-> ' + text + '\n'
            self.logger.log_freetext(player.get_name() + " " + text)
            do_print(text)
        print(final_text)
        logfile = open("logfile.txt", "w")
        self.logger.dump(logfile)
        logfile.close()

init_games()
players = [("AI1", Personalities.GoodAI), ("AI2", Personalities.GoodAI), ("AI3", Personalities.GoodAI)]
game = GameState(players)

for i in range(100):
    game.logger.card_list = __all_cards.copy()
    game.setup_age_cards(__all_cards.copy())
    game.game_loop()
    for p in game.players:
        print(p.personality.choice)
    # print('================NEW GAME================')
    game.reset()

#p = game.players[0]
#p.money = 10
#p.tableau += [find_card(__all_cards, "quarry"), find_card(__all_cards, "clay pit"), find_card(__all_cards, "press")]
#game.players[1].tableau += [find_card(__all_cards, "glassworks"), find_card(__all_cards, "sawmill"), find_card(__all_cards, "foundry")]

#p.buy_card(find_card(__all_cards, "fortification"), game.players[1], game.players[2])

#game.players[0].tableau += [find_card(__all_cards, "study"), find_card(__all_cards, "lodge"), find_card(__all_cards, "scientist guild")]
#print helpers.score_science(game.players[0])
