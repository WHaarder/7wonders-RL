import math
import random
import os

os.system('cls')

class Neuron():
    def __init__(self, inputs=1, weight=0, bias=0, mutation_rate=5):
        self.weight = [weight for i in range(inputs)]
        self.bias = [bias for i in range(inputs)]
        self.input = [0 for i in range(inputs)]
        self.output = 0
        self.mutation_rate = mutation_rate
    
    def __str__(self):
        string = ' '
        for i in self.input:
            string += '{:>5} '.format(i)
        string += '\n*'
        for w in self.weight:
            string += '{:>5} '.format(w)
        string += '\n+'
        for b in self.bias:
            string += '{:>5} '.format(b)
        string += '\n= {:>5f}\n'.format(self.output)
        return string

    def _randomize(self):
        for i in range(len(self.weight)):
            self.weight[i] = random.randint(-100, 100) / 100
            self.bias[i] = random.randint(-100, 100) / 100
    
    def sigmoid(self, number=None):
        if number is None:
            number = self.output

        return 1 / (1 + math.exp(0 - number))
    
    def _set_input(self, inputs=0):
        self.input = inputs
    
    def _get_output(self, process=True):
        self._process()
        return self.output

    def _process(self):
        self.output = 0
        for i in range(len(self.input)):
            self.output += self.input[i] * self.weight[i] + self.bias[i]
        self.output = self.sigmoid(self.output)
    
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
        self.hidden = [Neuron(a) for i in range(b)]
        self.outputs = [Neuron(b) for i in range(c)]
        self.result = []
    
    def __str__(self):
        string = ''
        return string
      
    def __apply_function(self, function=lambda *args: None):
        for i in self.inputs:
            function(i)
        for h in self.hidden:
            function(h)
        for o in self.outputs:
            function(o)

    def _randomize(self):
        self.__apply_function(Neuron._randomize)
    
    def _process(self, inputs):
        for i in self.inputs:
            i.input = inputs
            i._process()

        for h in self.hidden:
            h.input = [i.output for i in self.inputs]
            h._process()
        
        for o in self.outputs:
            o.input = [h.output for h in self.hidden]
            o._process()
        
        self.result = [o.output for o in self.outputs]
        return self.result
    
    def _breed_with(self, other):
        if other is None:
            other = self
        
        for i in range(len(self.inputs)):
            self.inputs[i].breed(other.inputs[i])
        for h in range(len(self.hidden)):
            self.hidden[i].breed(other.hidden[i])
        for o in range(len(self.outputs)):
            self.outputs[i].breed(other.outputs[i])
        
n = NeuralNetwork(3, 5, 2)
n._randomize()

print(n._process([1,1,1]))
n._randomize()
print(n._process([1,1,1]))