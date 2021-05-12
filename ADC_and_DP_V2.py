'''
    SEED TEAM 11
    MAGNETIC STIMULATION OF CARDIOMYOCYTES
    2020/2021

    This program is what the user runs on the Raspberry Pi to create the waveforms
    used in stimulating the cardiomyocytes. The program takes input from the
    potentiometers on the UI box and the mode switch on the user interface box. The
    voltage values from the pots are used to adjust the amplitude, on time, and delay
    of the pulses being created by the Raspberry Pi. The input from the switch is used to
    determine if the pulses will be created by the Raspberry Pi or an external function
    generator. Much of the program is dedicated to the design of the GUI that is displayed
    to the user showing the current mode the device is in as well as the values for
    amplitude, on time, and delay.

    These are the functions used in this program and their descriptions can be
    found above the functon definitions.
    analogInput(channel)
    write_pot(input)
    read_and_write_labels()

    Author: Carson Kurtz-Rossi
'''

#import the necessary libraries
import RPi.GPIO as GPIO
import spidev
import tkinter as tk
import sys
import os
from numpy import interp
from time import sleep

'''This fuction gets a value from 0 to 1023 representing the voltage on a
   specific channel of the ADC.
   Inputs:
   channel - an integer between 0 and 7 representing the channel from the ADC to read
   Outputs:
   data - an integer between 0 and 1023 representing the voltage reading
          from the given channel
'''
def analogInput(channel):
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

'''This function writes a resistance to a digital potentiometer.
   Inputs:
   input - an integer between 0 and 128 to represent the different
           resistance steps of the digipot
'''
def write_pot(input):
    spi.max_speed_hz = 976000
    msb = input >> 8
    lsb = input & 0xFF
    spi.xfer([msb,lsb])

'''This function gets data from the analog pots, interperates the data using the ADC,
   and then writes that data to the digital pots. It also determines the what state the
   raspberry pi should be in updates the gui labels accordingly with all this info.
'''
def read_and_write_labels():

    #enable the ADC to read the delay
    GPIO.output(CS_ADC,GPIO.LOW)
    #take data from channel 0 of the ADC
    output_delay = analogInput(0)
    #disable the ADC
    GPIO.output(CS_ADC,GPIO.HIGH)
    #map the output to a 1s to 10s delay
    output_delay = interp(output_delay,[0,1023],[1,0.1])
    #change the frequency of the pwm pin based on the maped value
    pi_pwm.ChangeFrequency(output_delay)

    #enable the ADC to read the on time
    GPIO.output(CS_ADC,GPIO.LOW)
    #take data from channel 1 of the ADC
    output_on = analogInput(1)
    #disable the ADC
    GPIO.output(CS_ADC,GPIO.HIGH)
    #map the output to a hex number between 0 and 128 because the digipot
    #has 128 steps
    output_on = interp(output_on,[0,1023],[0x80,0x00])
    #turn this value to an int
    output_on = int(output_on.item())

    #enable the ADC to read the amplitude
    GPIO.output(CS_ADC,GPIO.LOW)
    #take the data from channel 2 of the ADC
    output_amp = analogInput(2)
    #disable the ADC
    GPIO.output(CS_ADC,GPIO.HIGH)
    #map the output to a hex number between 0 and 128 because the digipot
    #has 128 steps
    output_amp = interp(output_amp,[0,1023],[0x00,0x80])
    #turn this value to an int
    output_amp = int(output_amp.item())

    #write to the on time pot
    GPIO.output(CS_POT_ON,GPIO.LOW)
    write_pot(output_on)
    GPIO.output(CS_POT_ON,GPIO.HIGH)
    #write to the amplitude pot
    GPIO.output(CS_POT_AMP,GPIO.LOW)
    write_pot(output_amp)
    GPIO.output(CS_POT_AMP,GPIO.HIGH)

    #determine the state of the switch
    up_state = GPIO.input(UP)
    down_state = GPIO.input(DOWN)

    #define the case where the switch in in function generator mode
    if (up_state == 1 and down_state == 0):
        #ensure that the pwm pin is sending pulses to the 555 timer
        pi_pwm.ChangeDutyCycle(99)
        #write the multiplexer GPIO pin to high to use function gen mode
        GPIO.output(MUX,GPIO.HIGH)
        #update the gui text colors and labels
        label_state_value['text'] = 'FUNCTION GEN'
        label_amplitude_value.configure(fg='red')
        label_on_time_value.configure(fg='black')
        label_delay_value.configure(fg='black')
    #define the state where the switch is in standby
    if (up_state == 0 and down_state == 1):
        #make the duty cycle from the pwm pin 100% so the 555 timer
        #is not triggered and there is no output from the pi
        pi_pwm.ChangeDutyCycle(100)
        #the multiplexer GPIO pin is low because function gen mode is off
        GPIO.output(MUX,GPIO.LOW)
        #update the gui text colors and labels
        label_state_value['text'] = 'STANDBY'
        label_amplitude_value.configure(fg='red')
        label_on_time_value.configure(fg='red')
        label_delay_value.configure(fg='red')
    #define the state where the switch is in pi pulse mode
    if (up_state == 0 and down_state == 0):
        #ensure that the pwm pin is sending pulses to the 555 timer
        pi_pwm.ChangeDutyCycle(99)
        #the multiplexer GPIO pin is low because function gen mode is off
        GPIO.output(MUX,GPIO.LOW)
        #update the gui text colors and labels
        label_state_value['text'] = 'PI PULSE'
        label_amplitude_value.configure(fg='black')
        label_on_time_value.configure(fg='black')
        label_delay_value.configure(fg='black')

    #format the delay value as a string
    delay = '{:.2f}'.format(1/output_delay)
    #the 555 is designed for an on time range of 250us to 5ms, this line
    #converts the output of the digipot to the 555 on time
    on_time = 250*10**-3+(128-output_on)*3.7109*10**-2
    on_time = '{:.2f}'.format(on_time)
    #with 128 steps between 0V and 5V each step corresponds to 0.0391V
    amp = output_amp*0.0391
    amp = '{:.2f}'.format(amp)

    #update the gui labels with the correct amplitude, on time, and delay values
    label_amplitude_value['text'] = amp
    label_on_time_value['text'] = on_time
    label_delay_value['text'] = delay

    #run this function every 1 ms
    root.after(1, read_and_write_labels)

#define the gpio pins
PULSE_PIN = 12
CS_POT_ON = 23
CS_POT_AMP = 25
CS_ADC = 24
UP = 17
DOWN = 27
MUX = 22

GPIO.setwarnings(False) #disable warnings
GPIO.setmode(GPIO.BCM) #set pin numbering system

#start spi connection with the ADC
spi = spidev.SpiDev()
spi.open(0,0)

#set up the PWM pin
GPIO.setup(PULSE_PIN,GPIO.OUT)
pi_pwm = GPIO.PWM(PULSE_PIN,100)
pi_pwm.start(99)

#set up the pots and the ADC pins
GPIO.setup(CS_POT_ON,GPIO.OUT)
GPIO.setup(CS_POT_AMP,GPIO.OUT)
GPIO.setup(CS_ADC,GPIO.OUT)
GPIO.output(CS_POT_ON,GPIO.HIGH)
GPIO.output(CS_POT_AMP,GPIO.HIGH)
GPIO.output(CS_ADC,GPIO.HIGH)

#setup the logic for the mux
GPIO.setup(UP,GPIO.IN)
GPIO.setup(DOWN,GPIO.IN)
GPIO.setup(MUX,GPIO.OUT)
GPIO.output(MUX,GPIO.HIGH)

#this code prevents the program from crashing if it is run via ssh
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using :0.0')
    os.environ.__setitem__('DISPLAY', ':0.0')

#create the main window for the gui
root = tk.Tk()
root.geometry("500x200")
root.title("Pulse Data Display")

#create the main container
frame = tk.Frame(root)
frame.config(bg='#ffb3fe')

#lay out the main container, specify that we want it to grow with window size
frame.pack(fill=tk.BOTH, expand=True)

#allow middle cell of grid to grow when window is resized
frame.columnconfigure(1, weight=1)
frame.rowconfigure(1, weight=1)
frame.rowconfigure(2, weight=1)

#create widgets
label_amplitude = tk.Label(frame,text='Amplitude',font=("Arial", 25),
                           bg='#ffb3fe')
label_on_time = tk.Label(frame,text='On Time',font=("Arial", 25),
                         bg='#ffb3fe')
label_delay = tk.Label(frame,text='Delay',font=("Arial", 25),
                       bg='#ffb3fe')
label_state = tk.Label(frame,text = 'State',font=("Arial", 25),
                       bg='#ffb3fe')
label_amplitude_value = tk.Label(frame,text='placeholder',font=("Arial", 25),
                                 bg='#ffb3fe')
label_on_time_value = tk.Label(frame,text='placeholder',font=("Arial", 25),
                               bg='#ffb3fe')
label_delay_value = tk.Label(frame,text='placeholder',font=("Arial", 25),
                             bg='#ffb3fe')
label_state_value = tk.Label(frame,text='placeholder',font=("Arial", 25),
                             bg='#ffb3fe')
label_amplitude_units = tk.Label(frame,text='V',font=("Arial", 25),
                                 bg='#ffb3fe')
label_on_time_units = tk.Label(frame,text='ms',font=("Arial", 25),
                               bg='#ffb3fe')
label_delay_units = tk.Label(frame,text='s',font=("Arial", 25),
                             bg='#ffb3fe')

#lay out the widgets
label_state.grid(row=0, column=0)
label_amplitude.grid(row=1, column=0)
label_on_time.grid(row=2, column=0)
label_delay.grid(row=3, column=0)
label_state_value.grid(row=0, column=1)
label_amplitude_value.grid(row=1, column=1)
label_on_time_value.grid(row=2, column=1)
label_delay_value.grid(row=3, column=1)
label_amplitude_units.grid(row=1, column=2)
label_on_time_units.grid(row=2, column=2)
label_delay_units.grid(row=3, column=2)

#run the program
read_and_write_labels()
root.mainloop()
