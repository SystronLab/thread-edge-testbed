#python3
import requests
import time
import sys

''' Command options:
   -ch <channel number>                          : default = 15
   -ifs <interframe spacing (ms)>                : default = 1 ms
   -rep <number of frame transmit repititions>   : default = 500000
   
   eg: python3 inject.py -ch 25 -ifs 2 -rep 1000

'''

# These are the same parameters as on the web interface
CHANNEL_DEFAULT = 15
IFS_DEFAULT = 1 # ms
NREPEAT_DEFAULT = 500000 # 2436 seconds worth

IPV4_ADDR = "10.10.10.2"

chn = CHANNEL_DEFAULT
modul = 0
txlevel = 0 #  '0' equiv. to +3dBm
rxen = 0
nrepeat = NREPEAT_DEFAULT
#nrepeat = 800 
tspace = IFS_DEFAULT
autocrc = 1 # must be set to '1'

# Handle command-line arguments #
if (len(sys.argv) > 1):
  
   for i in range(1,len(sys.argv)):
     if(sys.argv[i] == "-ch"):
        if(sys.argv[i+1].isdigit()):
           v = int(sys.argv[i+1])
           if (v > 10 and v < 27):
             chn = v
           else:
             print("channel number out of range!")
             exit()
        else:
          print("invalid channel input!")
          exit()
     elif(sys.argv[i] == "-ifs"):
        if(sys.argv[i+1].isdigit()):
           v = int(sys.argv[i+1])
           if (v > 0 and v < 100):
              tspace = v
           else:
             print("ifs value out of range!")
             exit()
        else:
          print("invalid ifs input!")
          exit()
     elif(sys.argv[i] == "-rep"):
        if(sys.argv[i+1].isdigit()):
           v = int(sys.argv[i+1])
           if (v > 0 and v < 1000000):
              nrepeat = v
           else:
             print("repeat value out of range!")
             exit()
        else:
          print("invalid repeat input!")
          exit()
     elif(sys.argv[i] == "-h"):
       print("options:\n-ch\t- channel number\n-ifs\t- interfame spacing\n-rep\t- number of packet repeats")
       exit()   
                    
# Set payload #
spayload = "6998"  # 0x9869
spayload += "00"   # Seq No. not req.d 
spayload += "0000" # valid PAN ID not req.d 
spayload += "0000" # destination address not req.d
spayload += "0000"# source address not req.d
spayload += "00" # Security control not req.d
spayload += "00000000" # Frame counter
spayload += "00" # Key Ident 
spayload += "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
spayload += "001122334455667788"

packetlen = len(spayload) # minimum valid packet size

PARAMS = {'chn': chn,
          'modul':modul,
          'txlevel':txlevel,
          'rxen':rxen,
          'nrepeat': nrepeat,
          'tspace' : tspace,
          'autocrc' : autocrc,
          'spayload' : spayload,
          'len': packetlen}

INJECT_URL = f"http://{IPV4_ADDR}/inject.cgi"
STATUS_URL = f"http://{IPV4_ADDR}/status.cgi"

print("OpenSniffer command tool")
print("------------------------")
print("channel = %d, ifs = %d ms, packet size = %d bytes, repeat = %d" % (chn, tspace, packetlen, nrepeat))
state = "run"
r = requests.get(url = INJECT_URL, params = PARAMS)
print(r)
if(r.status_code != 200):
    exit()
print("transmitting...")

while True:
    if(state=="run"):
        r = input("$ stop transmitting? (y/n):")
        if (r == 'y' or r == 'Y'):
          r = requests.get(url = STATUS_URL, params = "p=0")      
          state = "stopped"
        elif (r == 'q' or r == 'Q'):
          exit()
    elif (state=="stopped"):
        r = input("$ resume transmitting? (y/n):")  
        if (r == 'y' or r == 'Y'):          
            r = requests.get(url = INJECT_URL, params = PARAMS)
            print("transmitting...")
            state = "run"    
        else:
          print("quitting...")
          exit()
    
    
    


