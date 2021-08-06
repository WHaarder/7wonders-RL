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
import numpy as np
from sys import stdin
from common import *
import cards
from collections import defaultdict
import pandas as pd
from keras.models import Sequential
from keras.layers import Dense, Dropout, Conv2D, MaxPooling2D, Activation, Flatten, Embedding, Reshape
from keras.callbacks import TensorBoard
from keras.optimizers import Adam
from collections import deque
import random
import time

class Personality:
	def __init__(self):
		pass

	def make_choice(self, options, state):
		pass


class StupidAI(Personality):
	def __init__(self, arg):
		self.is_rl_ai = False

	def make_choice(self, options, state):
		return np.random.randint(len(options))


class Human(Personality):
	def __init__(self, arg):
		self.is_rl_ai = False

	def make_choice(self, options, state):
		return int(stdin.readline())


class Q_learning_agent(Personality):
	def __init__(self, __all_cards):
		pass

        ##
		# state is the cards on the players hand. encoded as 0/1 (other players current cards should be added here)
		##
		# actions is all possible actions - choose or discard: vector a choose or discard per card are the aciton vector. this has to be filtered when 
		## the user makes an action, according to only cards on the hand.
		##
		#self.expirience_replay = deque(maxlen=20000)
		self.expirience_replay = pd.DataFrame()
		self.expirience_replay_current = deque(maxlen=2000)

		self.epsilon = 0.50
		self.is_rl_ai = True

		self.full_state = np.unique([str(i) for i in __all_cards])

		#self.all_actions = dict.fromkeys(__all_cards, 0)
		self.all_actions = pd.DataFrame({'cards': self.full_state, "action": 0}).append(
		    pd.DataFrame({'cards': self.full_state, "action": 1}))

		self.all_actions = self.all_actions.reset_index().drop("index",axis=1)
		self.all_actions["a_index"] = self.all_actions.index

		self.q_network = self.init_model(len(self.full_state), len(self.all_actions))

	def random_choice(self,options_pd):
		choice = options_pd['original_index'].sample(1).iloc[0]
		opt = options_pd.merge(self.all_actions)
		self.action = opt[opt['original_index'] == choice].a_index.iloc[0]
		return choice

	def act(self, options_pd):
		if np.random.rand() <= self.epsilon:
			choice = self.random_choice(options_pd)
			return choice

		q_values = self.q_network.predict(np.expand_dims(self.state_nn_input,axis=0))[0]
		#save action for training
		q_values_reduced = q_values[options_pd.merge(self.all_actions).a_index]
		q_options = options_pd.merge(self.all_actions)
		q_options['q_values'] = q_values_reduced
        
		self.action = q_options.a_index.iloc[np.argmax(q_options['q_values'])]
		choice = q_options.original_index.iloc[np.argmax(q_options['q_values'])]
        
		#print(q_options);print(choice)
		return choice


	
	def make_choice(self, options, state):
		
		#options = [str(i[1]) for i in options]
		state = [str(i) for i in state]
		options_pd = pd.DataFrame(options)
		options_pd.columns = ["action","cards"]
		options_pd.cards = options_pd.cards.apply(str)
		options_pd['original_index'] = options_pd.index
		
		options_pd_0 = options_pd[options_pd.action == 0]
		if len(options_pd_0) == 0:
			options_pd = options_pd[options_pd.action == 1]
		else:
			options_pd = options_pd_0
			
		#print(options_pd.merge(self.all_actions)); time.sleep(0.5)
		#print(state) ; time.sleep(0.1)

		#add capability to handle non-unique if other players hands are included in state..
		self.state_nn_input = [1 if i in state else 0 for i in self.full_state]

		if len(self.expirience_replay) > 50:
			choice = self.act(options_pd)
		else:
			choice = self.random_choice(options_pd)

		self.store_current()
		return choice
	
	def store_current(self):
		self.expirience_replay_current.append((self.state_nn_input, self.action))

	def store(self):
		current_replay = pd.DataFrame(self.expirience_replay_current)
		current_replay.columns = "state", "action"
		current_replay["reward"] = self.reward
		self.expirience_replay = self.expirience_replay.append(current_replay)
		#self.expirience_replay.append((self.state_nn_input, self.action, self.reward))

	def train(self, batch_size):
		#minibatch = random.sample(self.expirience_replay, batch_size)
		minibatch = self.expirience_replay.sample(batch_size,replace=True)
		#print(minibatch)

		#for state, action, reward in minibatch:
		for index, row in minibatch.iterrows():
			target = self.q_network.predict(np.expand_dims(row['state'],axis=0))
			target[0][row["action"]] = row["reward"]
			#print(target[0])
	

			self.q_network.fit(np.expand_dims(row['state'],axis=0), np.array(target), epochs=1, verbose=0)

#https://rubikscode.net/2019/07/08/deep-q-learning-with-python-and-tensorflow-2-0/

	def init_model(self, state_space_size, action_space_size):
		model = Sequential()
		model.add(Dense(units = 50, input_shape = (state_space_size,)))
		model.add(Dense(50, activation='relu'))
		#model.add(Dropout(0.3))
		model.add(Dense(50, activation='relu'))
		#model.add(Dropout(0.3))
		model.add(Dense(action_space_size, activation='linear'))  # action_space_size = how many choices
        
		model.compile(loss="mse", optimizer=Adam(lr=0.01), metrics=['accuracy'])
		return model
		


# self.policy = createEpsilonGreedyPolicy(self.Q, 0.1, len(self.all_actions))
# self.Q = defaultdict(lambda: np.zeros(len(all_actions))) 

# def createEpsilonGreedyPolicy(Q, epsilon, num_actions): 
#    def policyFunction(state): 
   
#        Action_probabilities = np.ones(num_actions, 
#                dtype = float) * epsilon / num_actions 
                  
#        best_action = np.argmax(Q[state]) 
#        Action_probabilities[best_action] += (1.0 - epsilon) 
#        return Action_probabilities 
   
#    return policyFunction 



['lumber yard (brown) -> W',
 'ore vein (brown) -> O',
 'clay pool (brown) -> B',
 'stone pit (brown) -> S',
 'timer yard (brown) -> S/W',
 'clay pit (brown) -> B/O',
 'loom (grey) -> L',
 'glassworks (grey) -> G',
 'press (grey) -> P',
 'east trading post (yellow) -> trade-${WOBS} >',
 'west trading post (yellow) -> trade-${WOBS} <',
 'marketplace (yellow) -> trade-${GLP} <>',
 'altar (blue) -> 2 points',
 'theatre (blue) -> 2 points',
 'baths (blue) -> 3 points',
 'stockade (red) -> 1',
 'barracks (red) -> 1',
 'guard tower (red) -> 1',
 'apothecary (green) -> C',
 'workshop (green) -> G',
 'scriptorium (green) -> T',
 'lumber yard (brown) -> W',
 'ore vein (brown) -> O',
 'excavation (brown) -> S/B',
 'tavern (yellow) -> $$$$$',
 'pawnshop (blue) -> 3 points',
 'guard tower (red) -> 1',
 'scriptorium (green) -> T',
 'clay pool (brown) -> B',
 'stone pit (brown) -> S',
 'forest cave (brown) -> W/O',
 'tavern (yellow) -> $$$$$',
 'altar (blue) -> 2 points',
 'barracks (red) -> 1',
 'apothecary (green) -> C',
 'tree farm (brown) -> W/B',
 'mine (brown) -> S/O',
 'loom (grey) -> L',
 'glassworks (grey) -> G',
 'press (grey) -> P',
 'marketplace (yellow) -> trade-${GLP} <>',
 'theatre (blue) -> 2 points',
 'east trading post (yellow) -> trade-${WOBS} >',
 'west trading post (yellow) -> trade-${WOBS} <',
 'marketplace (yellow) -> trade-${GLP} <>',
 'tavern (yellow) -> $$$$$',
 'baths (blue) -> 3 points',
 'pawnshop (blue) -> 3 points',
 'stockade (red) -> 1',
 'sawmill (brown) -> WW',
 'foundry (brown) -> OO',
 'brickyard (brown) -> BB',
 'quarry (brown) -> SS',
 'loom (grey) -> L',
 'glassworks (grey) -> G',
 'press (grey) -> P',
 'caravansery (yellow) -> +resource{W/S/O/B}',
 'forum (yellow) -> +resource{G/L/P}',
 'vineyard (yellow) -> ${brown} <v>',
 'temple (blue) -> 3 points',
 'courthouse (blue) -> 4 points',
 'statue (blue) -> 4 points',
 'aqueduct (blue) -> 5 points',
 'stables (red) -> 2',
 'archery range (red) -> 2',
 'walls (red) -> 2',
 'library (green) -> T',
 'laboratory (green) -> G',
 'dispensary (green) -> C',
 'school (green) -> T',
 'sawmill (brown) -> WW',
 'foundry (brown) -> OO',
 'brickyard (brown) -> BB',
 'quarry (brown) -> SS',
 'bazaar (yellow) -> $${grey} <v>',
 'dispensary (green) -> C',
 'training ground (red) -> 2',
 'loom (grey) -> L',
 'glassworks (grey) -> G',
 'press (grey) -> P',
 'caravansery (yellow) -> +resource{W/S/O/B}',
 'courthouse (blue) -> 4 points',
 'laboratory (green) -> G',
 'stables (red) -> 2',
 'caravansery (yellow) -> +resource{W/S/O/B}',
 'forum (yellow) -> +resource{G/L/P}',
 'vineyard (yellow) -> ${brown} <v>',
 'temple (blue) -> 3 points',
 'library (green) -> T',
 'archery range (red) -> 2',
 'training ground (red) -> 2',
 'forum (yellow) -> +resource{G/L/P}',
 'bazaar (yellow) -> $${grey} <v>',
 'statue (blue) -> 4 points',
 'aqueduct (blue) -> 5 points',
 'school (green) -> T',
 'walls (red) -> 2',
 'training ground (red) -> 2',
 'gardens (blue) -> 5 points',
 'senate (blue) -> 6 points',
 'town hall (blue) -> 6 points',
 'pantheon (blue) -> 7 points',
 'palace (blue) -> 8 points',
 'university (green) -> T',
 'observatory (green) -> G',
 'lodge (green) -> C',
 'study (green) -> G',
 'academy (green) -> C',
 'siege workshop (red) -> 3',
 'fortification (red) -> 3',
 'arsenal (red) -> 3',
 'arena (yellow) -> $$$V{yellow}',
 'lighthouse (yellow) -> $V{wonder}',
 'haven (yellow) -> $V{brown}',
 'workers guild (purple) -> V{brown} <>',
 'craftsmens guild (purple) -> VV{grey} <>',
 'shipowners guild (purple) -> V{brown | grey | purple}',
 'traders guild (purple) -> V{yellow} <>',
 'magistrates guild (purple) -> V{blue} <>',
 'builders guild (purple) -> V{wonder} <v>',
 'philosophers guild (purple) -> V{green} <>',
 'scientist guild (purple) -> +science{C / T / G}',
 'spies guild (purple) -> V{red} <>',
 'strategists guild (purple) -> V{war lose} <>',
 'architects guild (purple) -> V{purple} <>',
 'gardens (blue) -> 5 points',
 'university (green) -> T',
 'arsenal (red) -> 3',
 'circus (red) -> 3',
 'haven (yellow) -> $V{brown}',
 'chamber of commerce (yellow) -> $$VV{grey}',
 'senate (blue) -> 6 points',
 'town hall (blue) -> 6 points',
 'study (green) -> G',
 'siege workshop (red) -> 3',
 'circus (red) -> 3',
 'arena (yellow) -> $$$V{yellow}',
 'town hall (blue) -> 6 points',
 'pantheon (blue) -> 7 points',
 'lodge (green) -> C',
 'circus (red) -> 3',
 'lighthouse (yellow) -> $V{wonder}',
 'chamber of commerce (yellow) -> $$VV{grey}',
 'palace (blue) -> 8 points',
 'observatory (green) -> G',
 'academy (green) -> C',
 'fortification (red) -> 3',
 'arsenal (red) -> 3',
 'arena (yellow) -> $$$V{yellow}']