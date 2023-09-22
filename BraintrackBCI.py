from asyncio.windows_events import NULL
from cortex import Cortex
from serial import Serial,serialutil
import time
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import sys
import signal

isDebug = False

# identification data necessary to save files and identify different experiments
rwPath = '' #path of data files, it assumes that both MET and POW files are in the same folder
userID = ''
MfileName = userID + 'MetData.txt'
PfileName = userID + 'PowData.txt'

# decide wether to include anagraphical data in the file
includeAnagraphicalData = True
Gender = ''
Age = ''

useFile = True
ex_decription = ''
isBaseLine = False #if isBaseLine the data will be averaged

# variables used to calculate the baseline values
b_GammaAlphaPz = []
b_BetaAlphaT8 = []
b_recordCount = 0
b_avg_GammaAlphaPz = 0.2 #the mean of gamma-alpha-Pz values is stored here 
b_avg_BetaAlphaT8 = 0.2 #the mean of beta-alpha-T8 values is stored here


requiresFocus = 1 # does this experimental phase need the user to be focused?
                  # (1 - yes; 0 - No), adds "1" or "0" to the json file for offline statistical analysis

is_running = True #while true: the data is displayed on graph and saved in the appropriate variables
T8_Bhigh = np.zeros(20)
T8_Alphas = np.zeros(20)
PZ_Gammas = np.zeros(20)
PZ_Alphas = np.zeros(20)
PZ_Buffer = []
T8_Buffer = []
buffer_recordCount = 0 #we want to measure the data once every # seconds
maximum_records = 18 #with roughly 6 data points per second the data is measured once every 3 seconds
xs = range(20)

# Application-specific variables
serialOnline = True
try:
    arduino = Serial(port='COM3', baudrate=115200, timeout=.1)
except serialutil.SerialException:
    print("Arduino not connected")
    serialOnline = False
#variables used to handle the output, in our case it regulates the slot cars speed:
outRange = (120,230) #maximum and minimum output, adjusted to our slot car track
minRange = 140 #min range and min count are used to adjust the baseline on the run
minCount = 0 #they're used to lower the threshold and help the user accelerate
arduino_output = 135 #initial output
arduino_output_Mult = [5,2,2,5] #acceleration of the car, used to handle the data
arduino_output_array = np.zeros(20) #used to plot the output trend



# Events to handle keypress on UI:
def on_key(event):
    global subscription
    global is_running
    global ex_decription
    if event.key == 'q': #QUIT
        global xs
        global ys
        xs = np.array([])
        ys = np.array([])
        plt.close()
        sys.exit(0)
    elif event.key == 'p': #PAUSE
        is_running = not is_running
    elif event.key == 'n': #NEW: new run, if last run was a baseline run it computes the mean
        if not is_running:
            global isBaseLine
            if isBaseLine:
                isBaseLine = False
                global b_avg_GammaAlphaPz
                global b_avg_BetaAlphaT8
                b_avg_GammaAlphaPz = sum(b_GammaAlphaPz)/b_recordCount
                b_avg_BetaAlphaT8 = sum(b_BetaAlphaT8)/b_recordCount
                if isDebug:
                    print(b_GammaAlphaPz)
                    print(b_BetaAlphaT8)
                print("avg GA PZ: " + str(b_avg_GammaAlphaPz))
                print("avg BA T8: " + str(b_avg_BetaAlphaT8))
            
            keepBase = input("keep the baseline (1) halve it (2) keep default values (3)?  ")
            if keepBase == '2': #1 should be enough, 2 & 3 are to be used as last resorts for on-the-go corrections
                b_avg_GammaAlphaPz /= 2
                b_avg_BetaAlphaT8 /= 2
            elif keepBase == '3':
                b_avg_BetaAlphaT8 = 0.2
                b_avg_GammaAlphaPz = 0.2
            print("avg GA PZ: " + str(b_avg_GammaAlphaPz))
            print("avg BA T8: " + str(b_avg_BetaAlphaT8))
            ex_decription = input("Descrizione esperimento:")
            writeOnFile(ex_decription + '\n','P')
            writeOnFile(ex_decription + '\n','M')


def writeOnFile(data,mode): #append data to the MET or POW files
        if mode == 'M':
            file = open(rwPath+'\\'+ MfileName,"a")
            file.write(data)
            file.close()
        else:
            file = open(rwPath+'\\'+ PfileName,"a")
            file.write(data)
            file.close()



class Subcribe():
    # A class to subscribe to data streams.
    def __init__(self):
        """
        Constructs cortex client and bind a function to handle subscribed data streams
        If you do not want to log request and response message , set debug_mode = False. The default is True
        met è quello che usiamo, data e pow potrebbero essere utili
        """   
        self.c = Cortex(user, debug_mode=True)
        self.c.bind(new_data_labels=self.on_new_data_labels)
        self.c.bind(new_met_data=self.on_new_met_data)
        self.c.bind(new_pow_data=self.on_new_pow_data)

    def do_prepare_steps(self):
        """
        Do prepare steps before training.
        Step 1: Connect a headset. For simplicity, the first headset in the list will be connected in the example.
                If you use EPOC Flex headset, you should connect the headset with a proper mappings via EMOTIV Launcher first 
        Step 2: requestAccess: Request user approval for the current application for first time.
                       You need to open EMOTIV Launcher to approve the access
        Step 3: authorize: to generate a Cortex access token which is required parameter of many APIs
        Step 4: Create a working session with the connected headset
        Returns
        -------
        None
        """
        self.c.do_prepare_steps()

    def sub(self, streams):
        """
        To subscribe to one or more data streams
        'met' : Performance metric
        'pow' : Band power

        Parameters
        ----------
        streams : list, required
            list of streams. For example, ['met', 'pow']

        Returns
        -------
        None
        """
        self.c.sub_request(streams)


    def on_new_data_labels(self, *args, **kwargs):
        """
        To handle data labels of subscribed data 
        Returns
        -------
        data: list  
              array of data labels
        name: stream name
        For example:
            met : ['eng.isActive', 'eng', 'exc.isActive', 'exc', 'lex', 'str.isActive', 'str', 'rel.isActive', 'rel', 'int.isActive', 'int', 'foc.isActive', 'foc']
            pow: ['AF3/theta', 'AF3/alpha', 'AF3/betaL', 'AF3/betaH', 'AF3/gamma', 'T7/theta', 'T7/alpha', 'T7/betaL', 'T7/betaH', 'T7/gamma', 'Pz/theta', 'Pz/alpha', 'Pz/betaL', 'Pz/betaH', 'Pz/gamma', 'T8/theta', 'T8/alpha', 'T8/betaL', 'T8/betaH', 'T8/gamma', 'AF4/theta', 'AF4/alpha', 'AF4/betaL', 'AF4/betaH', 'AF4/gamma']
        """
        
        data = kwargs.get('data')
        stream_name = data['streamName']
        stream_labels = data['labels']
        print('{} labels are : {}'.format(stream_name, stream_labels))
        if stream_name == 'met':
            if includeAnagraphicalData:
                MfileContent = ("UserN: " + userID + "  " + Gender + Age + '\n')
            MfileContent =  ('Metrics:,' + str(stream_labels) + '\n' + ex_decription + '\n')
            MfileContent += ('Reading begins:,' + datetime.now().strftime("%d/%m/%Y") + '\n')
            writeOnFile(MfileContent,'M')
        else:
            if includeAnagraphicalData:
                PfileContent = ("UserN: " + userID + "  " + Gender + Age + '\n')
            PfileContent = (ex_decription + '\n')
            PfileContent += ('Reading begins:,' + datetime.now().strftime("%d/%m/%Y") + '\n')
            PfileContent += ('Waves:,' + ','.join(stream_labels) + '\n')
            writeOnFile(PfileContent,'P')
        
    def on_new_met_data(self, *args, **kwargs):
        """
        To handle performance metrics data emitted from Cortex

        Returns
        -------
        data: dictionary
             The values in the array met match the labels in the array labels return at on_new_data_labels
        For example: {'met': [True, 0.5, True, 0.5, 0.0, True, 0.5, True, 0.5, True, 0.5, True, 0.5], 'time': 1627459390.4229}
        per leggere: 
        data = kwargs.get('data')
        #print(data["met"][N])
        N: 1 = engagement, 8 = relax, 12 = focus

        """
        if is_running:  #while the experiment is running save every instance of MET data received
            data = kwargs.get('data')["met"]
            my_string = str(data) + '\n'
            if isDebug:
                print(data)
            if useFile:
                MfileContent =  datetime.now().strftime("%H:%M:%S ") + my_string
                writeOnFile(MfileContent,'M')


    def on_new_pow_data(self, *args, **kwargs):
        """
        To handle band power data emitted from Cortex

        Returns
        -------
        data: dictionary
             The values in the array pow match the labels in the array labels return at on_new_data_labels
                            0               1           2           3               4           5           6           7           8           9           10          11          12          13              14          15          16      17         18
                       pow: ['AF3/theta', 'AF3/alpha', 'AF3/betaL', 'AF3/betaH', 'AF3/gamma', 'T7/theta', 'T7/alpha', 'T7/betaL', 'T7/betaH', 'T7/gamma', 'Pz/theta', 'Pz/alpha', 'Pz/betaL', 'Pz/betaH', 'Pz/gamma', 'T8/theta', 'T8/alpha', 'T8/betaL', 'T8/betaH', 'T8/gamma', 'AF4/theta', 'AF4/alpha', 'AF4/betaL', 'AF4/betaH', 'AF4/gamma']                             
        For example: {'pow': [5.251, 4.691, 3.195, 1.193, 0.282, 0.636, 0.929, 0.833, 0.347, 0.337, 7.863, 3.122, 2.243, 0.787, 0.496, 5.723, 2.87, 3.099, 0.91, 0.516, 5.783, 4.818, 2.393, 1.278, 0.213], 'time': 1627459390.1729}
        """

        if is_running:
            global b_GammaAlphaPz
            global b_BetaAlphaT8
            global b_recordCount

            global T8_Bhigh
            global T8_Alphas
            global PZ_Gammas
            global PZ_Alphas
            global xs

            data = kwargs.get('data')
            #print('pow data: {}'.format(data))
            if(data['pow'][11] == 0):
                data['pow'][11] = 0.001 #avoid divide by zero
            if(data['pow'][16] == 0):
                data['pow'][16] = 0.001 #avoid divide by zero
            #Gather channel data
            PZ_Alphas = np.append(PZ_Alphas, data['pow'][11])
            PZ_Gammas = np.append(PZ_Gammas, data['pow'][14])       
            T8_Bhigh = np.append(T8_Bhigh, data['pow'][18])
            T8_Alphas = np.append(T8_Alphas, data['pow'][16])
         
            PZ_Alphas = np.delete(PZ_Alphas,0)
            PZ_Gammas = np.delete(PZ_Gammas,0)
            T8_Bhigh = np.delete(T8_Bhigh,0)
            T8_Alphas = np.delete(T8_Alphas,0)
            #Update graphs
            axs[0].cla()
            axs[1].cla()
            axs[0].set_title('Data readings', fontsize = 12, fontweight = 'bold')
            axs[0].set_ylabel('PZ: Gamma / Alpha', fontsize = 9)
            axs[1].set_ylabel('T8: Beta / Alpha', fontsize = 9)
     
            if isBaseLine: #baseline: add data and record count to calculate the mean 
                           #after the recording is done
                b_GammaAlphaPz.append(data['pow'][14]/data['pow'][11])
                b_BetaAlphaT8.append(data['pow'][18]/data['pow'][16])
                b_recordCount += 1
                axs[0].plot(xs,PZ_Gammas/PZ_Alphas, label = "PZ: A/G")
                axs[1].plot(xs,T8_Bhigh/T8_Alphas, label = "PZ: G/Bh")
                if isDebug:
                    print(T8_Bhigh/T8_Alphas)
            else:
                #if I'm not recording a baseline
                global PZ_Buffer
                global T8_Buffer
                global buffer_recordCount #save up data until the maximum is reached
                if (buffer_recordCount < maximum_records):
                    PZ_Buffer.append((data['pow'][14]/data['pow'][11])/b_avg_GammaAlphaPz)
                    T8_Buffer.append((data['pow'][18]/data['pow'][16])/b_avg_BetaAlphaT8)
                    buffer_recordCount += 1
                else:
                    avgPZ = sum(PZ_Buffer)/len(PZ_Buffer)
                    avgT8 = sum(T8_Buffer)/len(T8_Buffer)

                    dataSend((avgPZ+avgT8)/2)
                    PZ_Buffer = []
                    T8_Buffer = []
                    buffer_recordCount = 0

                axs[0].plot(xs,(PZ_Gammas/PZ_Alphas), label = "PZ: A/G")
                axs[1].plot(xs,(T8_Bhigh/T8_Alphas), label = "PZ: G/Bl")
                axs[0].axhline(b_avg_GammaAlphaPz, color ='green')
                axs[1].axhline(b_avg_BetaAlphaT8,color ='green')


            if useFile:
                converted_List = [str(element) for element in data['pow']]
                PfileContent = datetime.now().strftime("%H:%M:%S ") + ', ' + ",".join(converted_List) + ",RF=" + str(requiresFocus) + "\n"
                writeOnFile(PfileContent,'P')
        plt.pause(0.01)

#handle output data
def dataSend(x):
    global arduino_output
    global arduino_output_array
    global arduino_output_Mult
    global minCount
    if x > 3:
        minCount = 0
        arduino_output_Mult[3] *= 1.1
        arduino_output_Mult[2] = 2
        arduino_output_Mult[1] = 2
        arduino_output_Mult[0] = 5 
        if arduino_output_Mult[3] > 10:
            arduino_output_Mult[3] = 10

        arduino_output += arduino_output_Mult[3]
    elif x > 2:
        minCount -= 1
        arduino_output_Mult[3] = 5
        arduino_output_Mult[2] *= 1.1
        arduino_output_Mult[1] = 2
        arduino_output_Mult[0] = 5 
        if arduino_output_Mult[2] > 6:
            arduino_output_Mult[2] = 6

        arduino_output += 0.5*arduino_output_Mult[2]
    elif x < 0.01:
        arduino_output_Mult[3] = 5
        arduino_output_Mult[2] = 2
        arduino_output_Mult[1] = 2
        arduino_output_Mult[0] = 5 

        arduino_output = 0
    elif x < 1:
        minCount += 1
        arduino_output_Mult[3] = 5
        arduino_output_Mult[2] = 2
        arduino_output_Mult[1] = 2
        arduino_output_Mult[0] *= 1.1 
        if arduino_output_Mult[0] > 10:
            arduino_output_Mult[0] = 10
        if(arduino_output < minRange):
            if minCount > 3:
                global b_avg_GammaAlphaPz
                global b_avg_BetaAlphaT8
                b_avg_GammaAlphaPz /= 1.13
                b_avg_BetaAlphaT8 /= 1.13
                minCount -= 1
            
        arduino_output -= 1 * arduino_output_Mult[0] 
    elif x < 1.5:
        arduino_output_Mult[3] = 5
        arduino_output_Mult[2] = 2
        arduino_output_Mult[1] *= 1.1
        arduino_output_Mult[0] = 5 
        if arduino_output_Mult[1] > 6:
            arduino_output_Mult[1] = 6            
        arduino_output -= 0.5 * arduino_output_Mult[1]
    
    if(arduino_output > outRange[1]):
        arduino_output = outRange[1]
    elif  arduino_output < outRange[0]:
        arduino_output = outRange[0]  
    arduino_output_array = np.append(arduino_output_array, arduino_output)
         
    arduino_output_array = np.delete(arduino_output_array,0)    
    axs[2].cla()
    axs[2].set_ylabel('Output [0-255]', fontsize = 9)     
    axs[2].plot(arduino_output_array, label = "output")

    print("x = " + str(x) + " output = " + str(arduino_output))
    if serialOnline:
        arduino.write(bytes(str(arduino_output), 'utf-8'))

# -----------------------------------------------------------
#
# Application start: select the correct client_id and client_secret provided by EMOTIV
#
# -----------------------------------------------------------



user = {
    "license" : "",
    "client_id" : "",
    "client_secret" : "",
    "debit" : 100
}
subscription = Subcribe()

# Do prepare steps
subscription.do_prepare_steps()

# sub multiple streams
streams = ['met','pow']

# or only sub for one
# streams = ['pow']
# streams = ['met']

if useFile:
    Mfile = open(rwPath+'\\'+ MfileName,"a")
    Pfile = open(rwPath+'\\'+ PfileName,"a")
    
fig, axs = plt.subplots(3, 1)
fig.canvas.mpl_connect('key_press_event', on_key)

axs[0].set_title('Data readings', fontsize = 12, fontweight = 'bold')
axs[0].set_ylabel('PZ: Gamma / Alpha', fontsize = 9)
axs[1].set_ylabel('T8: Beta / Alpha', fontsize = 9)
axs[2].set_ylabel('Output [0-255]', fontsize = 9)

plt.ion()
plt.show()

if(input("Baseline? (1) = yes;  (0) = no:")=='1'):
    if isDebug:
        print('isBaseline OK')
    isBaseLine = True

subscription.sub(streams)

# -----------------------------------------------------------
