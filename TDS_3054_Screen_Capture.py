##						TDS_3000_Waveform_Acquisition.py
##Purpose: Provide a reference to conrol TDS3000 series oscilloscopes using Python.
##		   This code retrieves waveforms from specified channels on a Tektronix TDS3000 
##		   series oscilloscope and saves the wavefom data to a log file.
##Written By:  Jarvis Hill, hilljarvis@gmail.com
##Date: 30-NOV-2018

##Modules	
import serial       ##Used for serial comms with TDS3000 oscilloscope
import time			##used to implement delays	
import math			##used for advanced math operations

##Serial COM Parameters
port = 'COM1'                   ##COM port 
baud = 9600                     ##Baud rate
EOL = '\n'                      ##End of line terminator

##GLOBALS
act_probe_chs = ['1','3']       ##List of active scope channels
data_file_str = "data.txt"



##Reads response from instrument
def read_data(instr):
    line = ''			##Define empty string
    while True:			##Read characters until '\n' EOL terminator is received
        ch = instr.read()
        line +=ch		##Add character to string
        if ch == '\n': break
    #print line			##Print received data for debbuging
    return line



##Configures serial port                
def Config_serial_comms():
        ser = serial.Serial(port,baud,timeout =10)  ##Establishes serial connection with instrument
        ser.write("*IDN?"+EOL)                      ##Identify instrument
        time.sleep(.5)                              ##Delay
        print(read_data(ser))                       ##Read intsr response
        #time.sleep(5)
        return ser                                  ##Return instr object
    

def Config_instr(instr):
 
    instr.write("ACQuire:MODe SAMple"+EOL)          ##Sample Mode
    instr.write("HORizontal:RESOlution HIGH"+EOL)   ##Sets high resolution data acquisition 10000 data points
    instr.write("HORizontal:MAIn:SCAle 40E-6"+EOL)  ##Sets main time scale per division
    instr.write("TRIGger:A:PULse:SOUrce CH3"+EOL)   ##Sets trigger source
    instr.write("TRIGger:A:TYPe EDGe"+EOL)          ##Sets trigger type
    instr.write("TRIGGER:A:EDGE:COUPLING DC"+EOL)   ##Sets trigger coupling
    instr.write("TRIGGER:A:EDGE:SLOPE FALL"+EOL)    ##Sets trigger Edge
    instr.write("TRIGGER:A:LEVEL 1.5"+EOL)          ##Set trigger level
    instr.write("TRIGGER:A:MODE NORMal"+EOL)        ##Sets trigger mode
    instr.write("CH"+act_probe_chs[0]+":POSITION 0.0E+00"+EOL)         ##Places CH at 0 divisons about the display center line
    instr.write("CH"+act_probe_chs[1]+":POSITION 2.0E+00"+EOL)        ##Places CH at 2 divisons about the display center line

    #Set CH properties
    for probe in act_probe_chs:
        instr.write("CH"+probe+":BANdwidth FULl"+EOL)          ##Channel bandwidth  
        instr.write("CH"+probe+":COUPling DC"+EOL)             ##Channel coupling
        instr.write("CH"+probe+":IMPedance MEG"+EOL)           ##Channel impeadance
        instr.write("CH"+probe+":VOLTS 2.00E0"+EOL)            ##Channel voltage scale

    

    
    

        
def ACQ_WFM(instr):

    #Declare local lists for CH wfm data
    voltage_data1 = []
    voltage_data2 = []
    count = 1
	
	#Configures and retrieves waveform data from all scope channels listed in global list "act_probe_chs"
    for ch in act_probe_chs:
        #Set how measurement data is encoded
        instr.write("DATa:SOUrce CH"+ch+EOL)                    ##Set CH data source
        instr.write("DATa:ENCDG ASCIi"+EOL)                     ##Set encoding of CH acquired/measurement data
        instr.write("DATA:WIDth 1"+EOL)                         ##Set data width (1 = 1 byte per data point)
		
	#Set data buffer size to retrieve when a wfm request is made (e.g. "CURVe?" cmd)  
        instr.write("DATA:START 1"+EOL)				##Set start index of measurement buffer data	
        instr.write("DATA:STOP 100"+EOL)			##Set stop index of measurement buffer data		
        time.sleep(0.1)

	#Request X&Y constants (these are needed to convert the digital data in the instrument buffer into analog values)
        instr.write("WFMPre:YZEro?"+EOL)
        YZE = float(read_data(instr))

        instr.write("WFMPre:YMUlt?"+EOL)
        YMU = float(read_data(instr))

        instr.write("WFMPre:YOFf?"+EOL)
        YOF = float(read_data(instr))

    ##  print("%f %f %f" % (YZE, YMU, YOF))                   	##Print waveform preamble params for DEBUG
       
        #Request waveform from a specified CH
        instr.write("CURVe?"+EOL)				##Send waveforem acquisition request to instrument
        wfm_str = read_data(instr)
        wfm_data = wfm_str[:-1].split(',')                      ##Remove the EOL at the end of the returned wfm string, parses the comma 
								##delimited string for each data point and stores all points/wfm measurements in a list of strings    

        ##Convert digital(ASCII) encoded scope wfm data into analog voltages
        for point in wfm_data:
            temp_data = int(point)				##Cast string wfm data point into an integer 							
            voltage = YZE + (YMU*(temp_data-YOF))
            if count == 1:
                voltage_data1.append(voltage)			##Store analog data in a list of floats
            elif count == 2:
                voltage_data2.append(voltage)			##Store analog data in a list of floats

        count += 1
        
            
##    print(voltage_data1)                                   	##Print CH wavform data for DEBUG
##    print(voltage_data2)
##    print(len(voltage_data1))
##    print(len(voltage_data2))

    ##Write data to file
    f = open(data_file_str,'w')					##Open file in working directory (place where Python script lives)
    f.write("Time[s]\tWFM1 Voltage[V]\tWFM2 Voltage[V]\n")	##Write file header
    for i in range(0,len(voltage_data1)):			##Write data from all active channels to the file
        f.write("\t"+str(voltage_data1[i])+"\t"+str(voltage_data2[i])+"\n")		

    f.close()																	##Close file
                   
    

##Main Program
def main():

    #Connect with TDS3000 series oscilloscope 
    scope = Config_serial_comms()
    
    #Configure instrument
    Config_instr(scope)
	
    #Acquire waveform
    ACQ_WFM(scope)

    #Close instrument connection
    scope.close()


    
#How you create a Main program section in Python	
if __name__ == '__main__':
    main()						      ##This tells Python which function you'd like to execute 1st 
							      ##(does not need to be called 'main()')
