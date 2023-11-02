import os
import time

restarts=0
while True:
    command="python test_pedestal_full.py {}".format(restarts)
    ret=os.system(command)
    if os.WEXITSTATUS(ret)==0:
        restarts+=1
    else:
        pass
    time.sleep(1)
