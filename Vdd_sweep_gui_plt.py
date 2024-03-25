#ESE 272 VDD sweep script used in labs for data collection

#imports
import matplotlib.pyplot as plt
import numpy as np
import PySimpleGUI as sg
import pyvisa as visa
import sys
import time


#connect to intruments
rm = visa.ResourceManager()
assets = np.array(rm.list_resources())
print (assets)


#find power supply
for asset in assets:
    location = np.flatnonzero(np.core.defchararray.find(asset,'::0x1102::')!=-1)
    if (location != -1):
        try:
            ps = rm.open_resource(asset)
        except:
            continue
        break
print ('Power supply identity: ' + ps.query ('*IDN?'))


#find dmm
for asset in assets:
    location = np.flatnonzero(np.core.defchararray.find(asset,'::0x1301::')!=-1)
    if (location != -1):
        try:
            dmm = rm.open_resource(asset)
        except:
            continue
        break
print ('DMM identity: ' + dmm.query ('*IDN?'))


#get parameters
layout = [[sg.Text("Starting Vdd voltage (non-negative):")],
    [sg.Input(key='-init_VDD-')],
    [sg.Text("Ending Vdd voltage (non-negative):")],
    [sg.Input(key='-final_VDD-')],
    [sg.Text("Current limit in amps (non-negative):")],
    [sg.Input(key='-I_lim-')],
    [sg.Text("Number of steps:")],
    [sg.Input(key='-N-')],
    [sg.Text("File name:")],
    [sg.Input(key='-FILE_NAME-')],
    [sg.Button('Run'), sg.Button('Cancel')]]
paramWindow = sg.Window('ESE 272 - Vdd sweep', layout)
while True:
    event, values = paramWindow.read()
    if event == sg.WINDOW_CLOSED or event == 'Cancel':
        break
    if event == 'Run':
        if values['-init_VDD-'] != "":
            Vdd0 = float(values['-init_VDD-'])
        else:
            errorWindow = sg.Window('Invalid parameter(s)', [[sg.Text("Please check your prameters and try again.")], [sg.Button("OK")]])
            break
        if values['-final_VDD-'] != "":
            Vddf = float(values['-final_VDD-'])
        else:
            errorWindow = sg.Window('Invalid parameter(s)', [[sg.Text("Please check your prameters and try again.")], [sg.Button("OK")]])
            break
        if values['-I_lim-'] != "":
            Idd = float(values['-I_lim-'])
        else:
            errorWindow = sg.Window('Invalid parameter(s)', [[sg.Text("Please check your prameters and try again.")], [sg.Button("OK")]])
            break
        if values['-N-'] != "":
            steps = int(values['-N-'])
        else:
            errorWindow = sg.Window('Invalid parameter(s)', [[sg.Text("Please check your prameters and try again.")], [sg.Button("OK")]])
            break
        if values['-FILE_NAME-'] != "":
            file_name = values['-FILE_NAME-']+'.csv'
        else:
            errorWindow = sg.Window('Invalid parameter(s)', [[sg.Text("Please check your prameters and try again.")], [sg.Button("OK")]])
            break
    break
paramWindow.close()

layout = [[sg.Text("Data collection is running. Press ""Stop"" to end data collection early.")],
    [sg.Button("Stop")]]
    
runWindow = sg.Window("ESE 272 - Vdd sweep", layout)


#draw axes
plt.axis([Vdd0,Vddf,0,3])
plt.xlabel('power supply potential [V]')
plt.ylabel('DMM potential [V]')


#open file
file = open(file_name, 'w+')
file.write ('index, Vdd voltage, Vref\n')


#measure
step_size = (Vddf-Vdd0)/(steps - 1)
for index in range (steps):
    event, values = runWindow.read(timeout=10)
    if event == "Stop" or event == sg.WINDOW_CLOSED:
        break
    set_volt = Vdd0 + index * step_size
    #print (index, set_volt)
    command = 'APPL CH2, ' + str(set_volt) + ', ' + str(Idd)
    #print (command)
    ps.write (command)
    #time.sleep(0.1)
    meas_Vdd = float (ps.query ('MEAS:VOLT? CH2'))
    meas_outvolt = float (dmm.query ('MEAS:VOLT:DC?'))
    file.write ("%d, %f, %f\n" % (index, meas_Vdd, meas_outvolt))
    plt.scatter(meas_Vdd, meas_outvolt)
    print ("%d, %f, %f\n" % (index, meas_Vdd, meas_outvolt))
    plt.show(block=False)
    
    
#turn power supply off and write file
ps.write ('APPL CH2, 0, 0.1')
print ('power supply off')
file.close()
runWindow.close()
