from src.custom_kernels.kernels import GPTKernel

g = GPTKernel()

g.execute('Write me a 300 word essay on horses please')
# g.execute('What is the magnificent name of horses?')

import time


time.sleep(2) 

print("Pausing...")
g.pause()
time.sleep(2)  # Simulate some processing time

print("Playing...")
g.play()
