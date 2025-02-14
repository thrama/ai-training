import math
import random             # just for generating random mountains                                   

# generate random mountains                                                                                
w = [random.random()/3, random.random()/3, random.random()/3]
h = [1.+math.sin(1+x/6.)*w[0]+math.sin(-.3+x/9.)*w[1]+math.sin(-.2+x/30.)*w[2] for x in range(100)]
h[0] = 0.0; h[99] = 0.0

def climb(x, h):
    # keep climbing until we've found a summit
    summit = False

    while not summit:
        summit = True         # stop unless there's a way up
        
        # Check both left and right directions
        # The boundary checks (x > 0 and x < len(h) - 1) ensure Venla doesn't try to climb outside the mountain range
        left_higher = x > 0 and h[x - 1] > h[x]
        right_higher = x < len(h) - 1 and h[x + 1] > h[x]
        
        if left_higher or right_higher:
            if right_higher:  # prioritize right if both are possible
                x = x + 1
            else:   
                x = x - 1
            summit = False    # and keep going
            
    return x

def main(h):
    # start at a random place                                                                                   
    x0 = random.randint(1, 98)
    x = climb(x0, h)

    print("Venla started at %d and got to %d" % (x0, x))
    return x0, x

main(h)