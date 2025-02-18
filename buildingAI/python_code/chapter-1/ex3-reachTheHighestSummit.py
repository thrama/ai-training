### Reach the highest summit
#
# Let the elevation at each point on the mountain be stored in array h of size 100. The elevation at 
# the leftmost point is thus stored in h[0] and the elevation at the rightmost point is stored in 
# h[99].
#
# If we plot the elevation values, they look like something like this: 
# [see the file '1.3-Exercise_3-Reaching_the_highest_summit.svg']
#
# The following program starts at a random position and keeps going to the right until Venla can 
# no longer go up. To make it easier to avoid falling off the map at the boundaries, we set both 
# h[0] and h[100] equal to zero which is lower than any of the values in between.

# You can see the result in the above chart where the starting point is marked with a small green 
# box and the point where Venla stops is marked with a small red triangle. This works fine as long 
# as the summit is to her right, but maybe it is to the left?

# Edit the program so that Venla doesn't stop climbing if she can go up either by moving left or 
# right. If both ways go up, either one is good. To check how your climbing algorithm works in 
# action, you can plot the results of your hill climbing using the Plot button. The summit will be 
# marked with a blue triangle.
#
###






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