import sys
from configobj import ConfigObj
config = ConfigObj("config.ini")

cfg_default=config['DEFAULT']

if cfg_default['TelescopeType']=="field":
    sys.path.append("/home/iceact/anaconda3/envs/cta2/lib/python3.8/site-packages")
elif TelescopeType=="roof":
    sys.path.append("/home/iceact/anaconda3/envs/cta/lib/python3.8/site-packages")
else :
    print("No valid TelescopeType defined")
    sys.exit()

if len(sys.argv)>1:
    RUNTYPE = sys.argv[1]
else:
    print("Please specify Runtype")
    sys.exit()

cfg_run=config[RUNTYPE]
