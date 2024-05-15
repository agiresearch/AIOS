# bottom two lines fix src import error 
# replace path with your path to AIOS

# import sys, os
# sys.path.append('/Users/rama2r/AIOS')

from src.custom_kernels.kernels import GPTKernel

g = GPTKernel()

g.execute('Write me a 300 word essay on horses please')
# g.execute('What is the magnificent name of horses?')

import time


time.sleep(2) 
# Now let's pause for 2 seconds
print("Pausing...")
g.pause()
time.sleep(2)  # Simulate some processing time

# Let's play for 3 seconds
print("Playing...")
g.play()
