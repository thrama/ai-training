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
