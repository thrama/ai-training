### Probabilities
#
# Recall the program that prints out the word 'dog' with 20% probability. Modify the program so 
# that it prints either the word 'dog' or the word 'cat' (but never both, because either you're a dog 
# erson or a cat person, but not both, right?)
#
# Change the probability of the word 'dog' to be 80% probability (because apparently there are 
# more dog lovers than cat lovers in the world) so that the probability of the word 'cat' is 20%.
#
###


import random

def main():
    prob = 0.20

    if random.random() < prob:
        print('cat')
    else:
        print('dog')

main()