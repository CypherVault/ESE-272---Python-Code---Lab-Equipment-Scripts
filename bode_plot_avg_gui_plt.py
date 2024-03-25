#ESE 272 bode plot averager script utilized in lab.

#imports
import math
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


#find scope
for asset in assets:
    location = np.flatnonzero(np.core.defchararray.find(asset,'::0x17A9::')!=-1)
    if (location != -1):
        try:
            scope = rm.open_resource(asset)
            scope.timeout = 25000
        except:
            continue
        break
print ('Scope identity: ' + scope.query ('*IDN?'))


#find function generator
for asset in assets:
    location = np.flatnonzero(np.core.defchararray.find(asset,'::0x1507::')!=-1)
    if (location != -1):
        try:
            fg = rm.open_resource(asset)
        except:
            continue
        break
print ('Function generator identity: ' + fg.query ('*IDN?'))     


#get parameters
print ('please verify input connected to scope channel 1, output to channel 2 and correct vertical scale factors')
print ('please verify function generator enabled')

layout = [[sg.Text("Peak-to-peak input voltage [Vpp]:")],
          [sg.Input(key='-AMP_PP-')],
          [sg.Text("Number of points per decade:")],
          [sg.Input(key='-N-')],
          [sg.Text("Start frequency [Hz]:")],
          [sg.Input(key='-F_START-')],
          [sg.Text("End frequency [Hz]:")],
          [sg.Input(key='-F_END-')],
          [sg.Text("File name:")],
          [sg.Input(key='-FILE_NAME-')],
          [sg.Button('Run'), sg.Button ('Cancel')]]

paramWindow = sg.Window('ESE 272 - Bode Plot', layout)

while True:
    event, values = paramWindow.read()
    if event == sg.WINDOW_CLOSED or event == 'Cancel':
        break
    if event == 'Run':
        if values['-AMP_PP-'] != "":
            amp_pp = float(values['-AMP_PP-'])
        else:
            errorWindow = sg.Window('Invalid parameter(s)', [[sg.Text("Please check your parameters and try again.")], [sg.Button("OK")]])
            break
        if values ['-N-'] != "":
            n = int(values['-N-'])
            a = 10**(1/n)
        else:
            errorWindow = sg.Window('Invalid parameter(s)', [[sg.Text("Please check your parameters and try again.")], [sg.Button("OK")]])
            break
        if values['-F_START-'] != "":
            f_start = float(values ['-F_START-'])
        else:
            errorWindow = sg.Window('Invalid parameter(s)', [[sg.Text("Please check your parameters and try again.")], [sg.Button("OK")]])
            break
        if values['-F_END-'] != "":
            f_end = float(values ['-F_END-'])
            end = round(math.log10(f_end/f_start)* n) + 1
        else:
            errorWindow = sg.Window('Invalid parameter(s)', [[sg.Text("Please check your parameters and try again.")], [sg.Button("OK")]])
            break
        if values ['-FILE_NAME-'] != "":
            file_name = values['-FILE_NAME-'] + '.csv'
        else:
            errorWindow = sg.Window('Invalid parameter(s)', [[sg.Text("Please check your parameters and try again.")], [sg.Button("OK")]])
            break
    if file_name != "":
        break

paramWindow.close()

layout = [[sg.Text("Data collection is running.  Press ""Stop"" to end data collection early.")],
          [sg.Button("Stop")]]

runWindow = sg.Window("ESE 272 - Bode Plot", layout)


#draw axes
plt.axis([f_start, f_end, -20, 30])
plt.xscale('log')
plt.xlabel('frequency [Hz]')
plt.ylabel('gain [dB]')
plt.autoscale (axis='y')


#open file
file = open(file_name, 'w+')
file.write ('index, frequency, ch1 vrms, ch2 vrms, dB, phase\n')


#measure
fg.write ('VOLT:UNIT VPP')
for index in range (end):
    event, values = runWindow.read(timeout=10)
    if event == "Stop" or event == sg.WINDOW_CLOSED:
        break
    fn = f_start * a**index
    command = 'APPL:SIN ' + str(fn) + ', ' + str (amp_pp)
    #print (command)
    fg.write (command)
    sweep = 1/fn
    command = 'TIM:SCAL ' + str(sweep)
    scope.write (command)
    scope.write(':ACQ:TYPE AVER')
    scope.write(':ACQ:COUN 4')
    time.sleep((20/fn)+0.2)
    #scope.write ('DIG: CHANNEL1,CHANNEL2')
    #time.sleep((20/fn)+0.2)
    ch1 = float (scope.query ('MEAS:VRMS? DISP,AC,CHANNEL1'))
    ch2 = float (scope.query ('MEAS:VRMS? DISP,AC,CHANNEL2'))
    phase = float (scope.query ('MEAS:PHAS? CHANNEL2,CHANNEL1'))
    dB = 20 * math.log10 (ch2/ch1)
    file.write ("%d, %f, %f, %f, %f, %f\n" % (index, fn, ch1, ch2, dB, phase))
    plt.scatter(fn, dB)
    print ("%d, %f, %f, %f, %f, %f\n" % (index, fn, ch1, ch2, dB, phase))
    plt.show(block=False)
    
#write file
file.close()
runWindow.close()
    
