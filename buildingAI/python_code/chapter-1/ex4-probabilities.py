import random

def main():
    prob = 0.20

    if random.random() < prob:
        print('cat')
    else:
        print('dog')

main()