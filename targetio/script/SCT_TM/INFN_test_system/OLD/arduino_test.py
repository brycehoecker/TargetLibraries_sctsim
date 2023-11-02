from arduino_utils import *

class arduino_manager:

  __init__



  def find_all_arduinos(self):
    try:
      self.TBOBport = get_usbport("TBOB")
      self.BOB1port = get_usbport("BOB1")
      self.BOB2port = get_usbport("BOB2")

    except OSError:
      print("oserror caught")


a = arduino_manager()


print ("BOB1 port = " + str(a.BOB1port))
print ("BOB2 port = " + str(a.BOB2port))
print ("TBOB port = " + str(a.TBOBport))
