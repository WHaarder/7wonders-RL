import math
import random


class Neuron():
    def __init__(self, input=1, weight=0, bias=0, mutation_rate=5):
        self.weight = [weight for i in range(input)]
        self.bias = [bias for i in range(input)]
        self.input = [0 for i in input]
        self.output = 0
        self.mutation_rate = mutation_rate

    def _randomize(self):
        self.weight = random.randint(-100, 100) / 100
        self.bias = random.randint(-100, 100) / 100
    
    def sigmoid(self, number=self.output):
        return number
    
    def _set_input(self, input=0):
        self.input = input
    
    def _get_output(self, process=True):
        self.process()
        return self.output

    def process(self):
        self.ouput = 0
        for i in self.input:
            self.output += i.input * i.weight + i.bias
        self.output = self.sigmoid()
    
    def _mutate_mod(self):
        return random.randint(0, self.mutation_rate) / 100 + 1

    def breed(self, other=None):
        if other is None:
            other = self
        new_bias = self._mutate_mod() * (self.bias + other.bias) / 2
        new_weight = self._mutate_mod() * (self.weight + other.weight) / 2
        new_mutation_rate = (self.mutation_rate + other.mutation_rate) / 2
        new_neuron = Neuron(new_weight, new_bias, new_mutation_rate)
        return new_neuron


class NeuralNetwork():
    def __init__(self, a=3, b=5, c=1, n_inputs=3):
        self.inputs = [Neuron(n_inputs) for i in range(a)]
        self.hidden = [Neuron(a) for i range(b)]
        self.outputs = [Neuron(b) for i in range(c)]
        self.result = []
      
    def __apply_function(self, function=lambda *args: None):
        for i in self.layer:
            for k in i:
                function(k)

    def _randomize(self):
        self.__apply_function(Neuron._randomize)
    
    def process(self, inputs):
        for i in self.inputs:
            i.input = inputs
            i._process()

        for h in self.hidden:
            h.input = [i.output for i in self.inputs]
            h._process()
        
        for o in self.outputs:
            o.input = [h.output for h in self.hidden]
            o._process()
        
        self.result = [o.output for o in self.output]
    
    def _breed_with(self, other):
        if other is None:
            other = self
        
        for i in self.inputs:
            pass
        for h in self.hidden:
            pass
        for o in self.output:
            pass
        
        

n = Neuron()
n._randomize()

