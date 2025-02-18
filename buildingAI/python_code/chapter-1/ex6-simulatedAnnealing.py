### Simulated Annealing
#
# 1D simulated annealing: modify the program below to use simulated annealing instead of plain 
# hill climbing. In simulated annealing the probability of accepting a solution that lowers the 
# score is given by prob = exp(-(S_old - S_new)/T). Setting the temperature T and gradually 
# decreasing can be done in many ways, some of which lead to better outcomes than others. A
# good choice in this case is for example: T = 2*max(0, ((steps-step*1.2)/steps))**3.
#
# Running the code produces something like the following chart, where the black box marks the 
# starting point. The code below uses the plain hill-climbing strategy to only go up towards a 
# peak. The solution is marked by a red star. As you can see, the hill-climbing strategy tends to 
# get stuck in local optima.
#
# [see the file '1.3-Exercise 6-Simulate_annealing.svg']
#
# Your task is to modify the code to use simulated annealing. Use the cooling schedule for setting 
# the temperature provided above, and modify the acceptance criterion from only accepting 
# upward moves to accepting also downward moves with the proper probability. Remember that 
# in this exercise the score in simulated annealing is the height of a given location on the 
# mountain. Also note that you will need to handle T=0 case separately, since the acceptance 
# probability for a worse score should be zero for zero temperature, but the formula used for the 
# probability will result in division by zero.
#
# If plotting the code takes too long, use this gist to plot the code locally on your computer. It 
# should be significantly faster.
#
###


import math, random        	# just for generating random mountains                                 	 
import numpy as np

n = 10000 # size of the problem: number of possible solutions x = 0, ..., n-1

# generate random mountains                                                                               	 
def mountains(n):
    h = [0]*n
    for i in range(50):
        c = random.randint(20, n-20)
        w = random.randint(3, int(math.sqrt(n/5)))**2
        s = random.random()
        h[max(0, c-w):min(n, c+w)] = [h[i] + s*(w-abs(c-i)) for i in range(max(0, c-w), min(n, c+w))]

    # scale the height so that the lowest point is 0.0 and the highest peak is 1.0
    low = min(h)
    high = max(h)
    h = [y - low for y in h]
    h = [y / (high-low) for y in h]
    return h

h = mountains(n)

# start at a random place
x0 = random.randint(1, n-1)
x = x0

# keep climbing for 5000 steps
steps = 5000

def main(h, x):
    n = len(h)
    # the climbing starts here
    for step in range(steps):
        # this is our temperature to be used for simulated annealing
        # it starts large and decreases with each step. you don't have to change this
        #
        # temperature calculation explanation:
        # - steps-step*1.2: decreases linearly from steps to negative values
        # - max(0, ...): ensures non-negative values
        # - (...)/steps: normalizes between 0 and 1
        # - **3: applies cubic decay to slow initial cooling
        # - 2*: scales initial max temperature to 2
        #
        # result: T starts at 2 and gradually decreases to 0
        T = 2*max(0, ((steps-step*1.2)/steps))**3

        # let's try randomly moving (max. 1000 steps) left or right
        # making sure we don't fall off the edge of the world at 0 or n-1
        # the height at this point will be our candidate score, S_new
        # while the height at our current location will be S_old
        x_new = random.randint(max(0, x-1000), min(n-1, x+1000))

        if h[x_new] > h[x]:
            x = x_new           # the new position is higher, go there
        else:
            if T == 0:
                continue  # At T=0, reject all downward moves
            
            # Calculate acceptance probability using Metropolis criterion
            p = np.exp((h[x_new] - h[x]) / T)
            
            if random.random() < p:
                x = x_new  # Accept worse position with probability p

    return x

x = main(h, x0)
print("ended up at %d, highest point is %d" % (x, np.argmax(h)))
