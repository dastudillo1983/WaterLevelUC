from network import WLAN, LoRa
from machine import I2C, RTC, Timer, Pin, deepsleep
import machine
import ustruct
import socket
import pycom
import time
import sys

############################-----Disable WiFi-----##############################
wlan = WLAN()
wlan.deinit()

pycom.heartbeat(False)

i2c = I2C(0)                         # create on bus 0
i2c = I2C(0, I2C.MASTER)             # create and init as a master
i2c.init(I2C.MASTER, baudrate=100000) # init as a master

###################-----host-port:comunication with app-----####################
host=''
port=80

#############################---ADS1115-CHANNELS---#############################
_CHANNEL0=const(0xC3)   #channel waterLevelSensor
_CHANNEL1=const(0xD3)   #channel battery
_CHANNEL2=const(0xE3)
_CHANNEL3=const(0xF3)

#####################--ID--station and sensor-2bytes---#########################
stationId=7         #4bits
sensorIdWl=18       #12bits
sensorIdBl=20       #12bits
stationId_bits="{0:b}".format(stationId)
sensorIdWl_bits="{0:b}".format(sensorIdWl)
sensorIdBl_bits="{0:b}".format(sensorIdBl)
stationId_bits=(4-len(stationId_bits))*'0'+stationId_bits
sensorIdWl_bits=(12-len(sensorIdWl_bits))*'0'+sensorIdWl_bits
sensorIdBl_bits=(12-len(sensorIdBl_bits))*'0'+sensorIdBl_bits
IDWl=(int('0b'+stationId_bits+sensorIdWl_bits,2))
IDBl=(int('0b'+stationId_bits+sensorIdBl_bits,2))

##########################---loRaTransmission---################################
_LORA_PKG_FORMAT = "BBB%ds"
_LORA_PKG_ACK_FORMAT = "BBB"

DEVICE_ID = 0x02
PKG_TYPE = 0x01

lora = LoRa(mode=LoRa.LORA, frequency=915000000, tx_iq=True)
lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setblocking(False)

#################################--RTC-DS1307--#################################
def ds1307init_sinc():
    reloj_rtc_int=rtc.now()
    hora_rtc_ext= str(reloj_rtc_int[3])
    hora_rtc_ext_hex = int(decode_ds1307(hora_rtc_ext))
    min_rtc_ext= str(reloj_rtc_int[4])
    min_rtc_ext_hex= int(decode_ds1307(min_rtc_ext))
    seg_rtc_ext= str(reloj_rtc_int[5])
    seg_rtc_ext_hex = int(decode_ds1307(seg_rtc_ext))
    dia_rtc_ext= str(reloj_rtc_int[2])
    dia_rtc_ext_hex = int(decode_ds1307(dia_rtc_ext))
    mes_rtc_ext= str(reloj_rtc_int[1])
    mes_rtc_ext_hex = int(decode_ds1307(mes_rtc_ext))
    ann_rtc_ext= str(reloj_rtc_int[0])
    ann_rtc_ext_hex = int(decode_ds1307(ann_rtc_ext[2:4]))

    i2c.init()
    i2c.writeto(0x68,chr(0xD0))
    i2c.writeto(0x68,chr(0))
    i2c.writeto_mem(0x68,0,chr(seg_rtc_ext_hex))
    i2c.writeto_mem(0x68,1,chr(min_rtc_ext_hex))
    i2c.writeto_mem(0x68,2,chr(hora_rtc_ext_hex))
    i2c.writeto_mem(0x68,4,chr(dia_rtc_ext_hex))
    i2c.writeto_mem(0x68,5,chr(mes_rtc_ext_hex))
    i2c.writeto_mem(0x68,6,chr(ann_rtc_ext_hex))
    i2c.writeto_mem(0x68,7,0x10)
    i2c.deinit()

def decode_ds1307(valor_rtc_int):
    binstring = ''
    x=int(valor_rtc_int)
    while True:
        q, r = divmod(x, 10)
        nibble = bin(r).replace('0b', "")
        while len(nibble) < 4:
            nibble = '0' + nibble
        binstring = nibble + binstring
        if q == 0:
            break
        else:
            x = q
    valorhex = int(binstring, 2)
    return valorhex

def code_ds1307(valor_ds1307):
    valor=hex(ord(valor_ds1307))
    valor1= int(valor) & 15
    valor2= int(valor)>>4
    valorint= int(str(valor2)+str(valor1))
    return valorint

def obtener_ds1307():
    i2c.init()
    i2c.writeto(0x68,chr(0xD0))
    i2c.writeto(0x68,chr(0))
    i2c.writeto(0x68,chr(0xD1))
    segundos=i2c.readfrom_mem(0x68,0,1)
    segundosint= code_ds1307(segundos)
    minutos=i2c.readfrom_mem(0x68,1,1)
    minutosint=code_ds1307(minutos)
    horas=i2c.readfrom_mem(0x68,2,1)
    horasint=code_ds1307(horas)
    dia=i2c.readfrom_mem(0x68,4,1)
    diaint=code_ds1307(dia)
    mes=i2c.readfrom_mem(0x68,5,1)
    mesint=code_ds1307(mes)
    ann=i2c.readfrom_mem(0x68,6,1)
    annint=code_ds1307(ann)
    print(segundosint, minutosint, horasint, diaint, mesint, annint)
    i2c.deinit()

def sinc_RTC_ds1307():
    i2c.init()
    i2c.writeto(0x68,chr(0xD0))
    i2c.writeto(0x68,chr(0))
    i2c.writeto(0x68,chr(0xD1))
    segundos=i2c.readfrom_mem(0x68,0,1)
    segundosint= code_ds1307(segundos)
    minutos=i2c.readfrom_mem(0x68,1,1)
    minutosint=code_ds1307(minutos)
    horas=i2c.readfrom_mem(0x68,2,1)
    horasint=code_ds1307(horas)
    dia=i2c.readfrom_mem(0x68,4,1)
    diaint=code_ds1307(dia)
    mes=i2c.readfrom_mem(0x68,5,1)
    mesint=code_ds1307(mes)
    ann=i2c.readfrom_mem(0x68,6,1)
    annint=code_ds1307(ann)+2000
    rtc.init((annint, mesint, diaint, horasint, minutosint, segundosint, 5000, 0),source=RTC.INTERNAL_RC)
    i2c.deinit()
    print(rtc.now())
##############################################################################

###############################----Paths----####################################
#pathConfigFile:archivo de configuracion, contiene el Vmin y la pendiente
#pathLogsWl:directorio donde se almacenan archivos diarios con la medida del nivel de agua cada ...
#pathCurrentFile:archivo que almacena el hx cada 5min
pathConfigFile='/flash/configFile/wl400_0'
pathLogsWl='/flash/logsDir/wl'
pathLogsBl='/flash/logsDir/bl'
pathCurrentFile='/flash/logsDir/currentFile'

########################----clockSynchronization----############################
#Sincronización del rtc-LoPy con el dateTime recibido por el gps o ds1307
def clockSynchronization(dateTime):
    rtc.init(dateTime)
    print(rtc.now())

##############################----configFile----################################
#Lee los valores de configuracion de la memoria flash,
#existen dos archivos de configuracion: wl400_00 y wl400_01, el 1ero se crea
#por defecto con parámetros pre-establecidos, y el 2do se crea al momento de
#calibrar el dispositivo mediante WiFi.
def configFile():
    try:
        files=os.listdir('/flash/configFile')
        lenFile=len(files)
        print('read:', files[lenFile-1])
        if files[lenFile-1]=='wl400_0'+str(lenFile):
            if os.stat(pathConfigFile+str(lenFile))[6]==8:
                print('configFile a leer:', pathConfigFile+str(lenFile))
                config=readFile(pathConfigFile,'r',str(lenFile))
            else:
                print('error en config:',pathConfigFile+str(lenFile))
                print('leyendo:',pathConfigFile+str(lenFile-1))
                config=readFile(pathConfigFile,'r',str(lenFile-1))

    except Exception as e:#MyError:
        print("configFile doesn't exist")
        #Parámetros: calibración del sensor wl400 (valores obtenidos en basea mediciones, pueden ser modificados)
        vMin=2804        #~mV
        hMin=80
        v1=2902          #~mV
        h1=130           #altura[mm] correspondiente a V1
        config=ustruct.pack('HHHH',vMin,hMin,v1,h1)     #estructura el archivo de configuracion 2bytes para cada valor
        os.mkdir('/flash/configFile')       #Directorio configFile que contendrá los archivos wl400_0x
        writeFile(pathConfigFile,'wb',1,config)
        time.sleep(0.1)
    return config

#logsDir
#Verifica que esté creado el dir para el almacenamiento de logs, si no existe lo crea
def logsDir():
    try:
        files=os.listdir('logsDir')
        #os.remove(pathCurrentFile)
    except Exception as e:
        print("logsDir doesn't exist")
        os.mkdir('/flash/logsDir')
        time.sleep(0.1)

##############################----readFile----##################################
#Lee un archivo, path:ubicación del archivo, mode: tipo de lectura 'r' o 'rb'
#typeFile:En caso de haber archivos con nombres similares, se especifica la variacion
#i.e config01 y config02, config es el path, 01 y 02 corresponden al typeFile
def readFile(path,mode,typeFile):
    f = open(path+str(typeFile), mode)
    config=f.readall()
    f.close()
    return config

##############################----writeFile----#################################
#Escribe un archivo, path:ubicación del archivo, mode: tipo de escritura 'w' o 'wb'
#files:archivo a guardar
#typeFile:En caso de haber archivos con nombres similares, se especifica la variacion
#i.e config01 y config02, config es el path, 01 y 02 corresponden al typeFile
def writeFile(path,mode,typeFile,files):
    f = open(str(path)+str(typeFile), mode)
    f.write(files)
    f.close()

#############################----slope----######################################
#calcula la pendiente en base a los dos puntos almacenados en config,
#devuelve equationParameters: P1x,P1y,pendiente
def slope(config):
    config=ustruct.unpack('HHHH',config)
    m=(config[2]-config[0])/(config[3]-config[1])
    equationParameters=(config[0],config[1],m)
    return equationParameters

###########################----calibrationType----##############################
#Llamado desde el method:wifi, redirecciona a los métodos:
    #h0Calibration:             Calibra P1
    #h1Calibration:             Calibra P2
    #clockSynchronizationApp:   Sincroniza el reloj del LoPy con la app.
    #restoreConfigFile:         Elimina el config generado por la app.
    #levelWaterUpdate:          Envía a la app nos niveles de agua
    #finishCalibration:         Finaliza la conexión con la app.
def calibrationType(argCalibration):
    print('argCalibration: ', argCalibration[0])
    switcher = {
        97: h0Calibration,
        98: h1Calibration,
        99: finishCalibration,
        100: clockSynchronizationApp,
        101:restoreConfigFile,
        102:levelWaterUpdate,
    }
    func = switcher.get(argCalibration[0])       # Get the function from switcher dictionary
    return func(argCalibration)                  # Execute the function
#############################----h0Calibration----##############################
#almacena el valor de P1: P1(vMin,0).
def h0Calibration(none):
    ads1115Write(_CHANNEL0)
    vMin=ads1115Read()
    p1=ustruct.pack('HH',vMin,0)
    writeFile(pathConfigFile,'wb',2,p1)
    msg='Calibración de P1 realizada con éxito'
    return True, msg
##############################----h1Calibration----#############################
#almacena el valor de P2: P2(Vx,hx)
def h1Calibration(hx):
    ads1115Write(_CHANNEL0)
    v1=ads1115Read()
    p1=readFile(pathConfigFile,'rb',2) #tupla binaria con p1
    p1=ustruct.unpack('HH',p1)
    config=ustruct.pack('HHHH',p1[0],p1[1],v1,int(hx[1:]))
    writeFile(pathConfigFile,'wb',2,config)
    msg='Calibración de P2 realizada con éxito'
    return True,msg
#########################----clockSynchronizationApp----########################
def clockSynchronizationApp(date):
    dateTime=time.gmtime(int(date[1:]))
    msg='Fecha Actualizada'
    clockSynchronization(dateTime)
    ds1307init_sinc()
    return True,msg
############################----restoreConfigFile----###########################
def restoreConfigFile(none):
    if len(os.listdir('/flash/configFile'))==1:
        msg='Actualmente se ejecuta con la configuración de Fabrica'
    else:
        os.remove(pathConfigFile+'2')
        msg='Restaurado a configuración de Fabrica'
    return True,msg
#############################----levelWaterUpdate----###########################
def levelWaterUpdate(none):
    ads1115Write(_CHANNEL0)
    vX=ads1115Read()
    config=configFile()
    equationParameters=slope(config)
    hX=waterLevel(equationParameters,vX)
    print(hX)
    tStamp=rtc.now()
    print(tStamp[:6])
    tStamp=str(tStamp[0])+'/'+str(tStamp[1])+'/'+str(tStamp[2])+' '+str(tStamp[3])+':'+str(tStamp[4])+':'+str(tStamp[5])
    msg=str(hX)
    msg='-'+msg+' '+tStamp
    return True,msg
############################----finishCalibration----###########################
def finishCalibration(none):
    msg='Finish wifi LoPy'
    pycom.rgbled(False)
    return False,msg

##################################----WiFi----##################################
#Activa el WiFi ssid:waterLevel, clave: ucuenca1234.
#Parámetros del socket con ipServer:"host" y puerto:"port" (definidos al inicio)
#luego del proceso de calibración se desactiva el wifi.
def wifi():
    print('wifi init')
    pycom.rgbled(0x009999) # blue
    wlan = WLAN(mode=WLAN.AP, ssid='waterLevel', auth=(WLAN.WPA2,'ucuenca1234'), channel=7, antenna=WLAN.INT_ANT)
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        serversocket.bind(socket.getaddrinfo(host,port)[0][-1])     #ipServer 192.168.4.1
    except Exception as e:
        print('bind failed, error code: ',str(e[0]))
        sys.exit()
    serversocket.listen(1)
    print('socket is now listening over port: ', port)

    wifiSocket=True
    while (wifiSocket):
        print('socket init')
        sc, addr = serversocket.accept()
        print('sc: ',sc,' addr: ',addr)
        recibido = sc.recv(16)
        print('valor recibido :', recibido)
        print('dato[0]: ',recibido[0])
        wifiSocket, msg=calibrationType(recibido)
        sc.send(msg)
    print('closing wifi and socket')
    sc.close()
    serversocket.close()
    wlan.deinit()

############################----waterLevel----##################################
#Calcula la profundidad del agua, Vx:nuevo valor del sensor,
#equationParameters: contiene los valores Punto y pendiente de la
#ecuación lineal, retorna hx en [mm]
def waterLevel(equationParameters,vX):
    hX=((vX-equationParameters[0])/equationParameters[2])+equationParameters[1]
    print('altura Vx: ',hX)
    if hX<0:
        hX=0
    hX=round(hX)
    return hX

##############################----batteryLevel----##############################
#Devuelve el nivel de voltaje medido en batt (valor analógico del channel_1)
def batteryLevel(batt):
    volBatt=round((batt*1181)/22046)
    return volBatt

#############################----_measurementAlarm----##########################
#alarma para realizar las mediciones.
def _measurementAlarm(alarm):
    print("measurement alarm")
    global measurementAlarm, timeStamp_measurement
    measurementAlarm.cancel()
    timeStamp_measurement=time.mktime(time.gmtime())
    global measurementMain
    measurementMain=True

##############################----activeAlarmM----##############################
#Activa la alarma _measurementAlarm cada alarm [segundos]
def activeAlarmM(segM):
    print('alarma activada cada',segM)
    measurementAlarm = Timer.Alarm(_measurementAlarm, segM, periodic=True)
    return measurementAlarm

def loraTransmission(value):
    print('loRaTransmission',value)

#############################----ads1115Write----###############################
#Configura el ads1115 en modo Single-Shot, y habilita el canal (channel)
def ads1115Write(channel):
    data = ustruct.pack('>BBB', 0x01,channel,0x83)
    i2c.init()
    i2c.writeto(0x48, data)
    time.sleep(0.5)
    i2c.deinit()
################################----ads1115Read----#############################
#Adquiere los datos analógicos de channel(habilitado en ads1115Write)
def ads1115Read():
    i2c.init()
    data = i2c.readfrom_mem(0x48, 0x00, 2 )
    i2c.deinit()
    time.sleep(0.1)
    vX=ustruct.unpack('>H', data)[0]
    print(vX)
    return vX

#################################----segAlarm----###############################
#Segundos que faltan para los siguientes measurementTime
def segAlarm():
    timeStampM=time.localtime()
    minM = measurementTime-(timeStampM[4] % measurementTime)
    segM=minM*60-timeStampM[5]
    print('timeStampM:segAlarm',timeStampM)
    return segM

################################################################################
##################################-----MAIN-----################################
################################################################################
rtc = RTC()
sinc_RTC_ds1307()

config=configFile()
print('config parameters: ',ustruct.unpack('HHHH',config))
equationParameters=slope(config)
print('equationParameters',equationParameters)
logsDir()

###########---CALIBRACIÓN DEL CRONÓMETRO PARA LA TOMA DE DATOS---###############
global measurementTime        #tiempo en minutos para la adquisión de datos.
measurementTime=5
sendTime=measurementTime      #tiempo para hacer la transmision [minutos]

P8 = Pin('P8', mode=Pin.IN, pull=Pin.PULL_UP)
machine.pin_deepsleep_wakeup([P8], machine.WAKEUP_ALL_LOW, True)
wifiMain=False

###########################----WAKEREASON_PIN----###############################
#Test a P8 durante 3[segundos] para confirmar la activación del WiFi
if machine.wake_reason()[0]==1:
    print('PIN sleep')
    i=0
    while P8()==0:
        print('dentro del while')
        pycom.rgbled(0x009999) # blue
        time.sleep(0.5)
        pycom.rgbled(False)
        time.sleep(0.5)
        i=i+1
        if i==3:
            pycom.rgbled(0x009900) # RED
            time.sleep(1)
            pycom.rgbled(False)
            time.sleep(1)
            wifiMain=True

segM=segAlarm()     #segundos faltantes para los siguientes measurementTime(5min)
if segM>15 and wifiMain==False:
    print('init sleep',segM-10)
    deepsleep((segM-10)*1000)
if segM<=15 and wifiMain==False:
    segM=segAlarm()     #segundos faltantes para los siguientes measurementTime(5min)
    measurementAlarm = activeAlarmM(segM)   #activa la alarma cada segM

transmissionMain=False
measurementMain=False

typeWrite="wb"

while True:
    time.sleep(1)
    if wifiMain:
        wifi()
        print('alarma activada al finalizar el wifi:',segM, 'new configFile:')
        config=configFile()
        print('config parameters: ',ustruct.unpack('HHHH',config))
        equationParameters=slope(config)
        print('equationParameters',equationParameters)

        wifiMain=False
        segM=segAlarm()
        if segM>15:
            print('init sleep',segM-10)
            deepsleep((segM-10)*1000)
        else:
            segM=segAlarm()
            measurementAlarm = activeAlarmM(segM)

    if measurementMain:
        measurementMain=False
        pycom.rgbled(0xFFFF99) # blue
        print(rtc.now())
        #######################-----SENSOR-----###############################
        ads1115Write(_CHANNEL0)     #config the channel_0 for to read the sensor
        vX=ads1115Read()
        hX=waterLevel(equationParameters,vX)
        print(hX)#print(ustruct.unpack('H', hX)[0])
        ######################-----BATTERY-----###############################
        ads1115Write(_CHANNEL1)     #config the channel_1 for to read the battery
        batt=ads1115Read()
        volBatt=batteryLevel(batt)
        print('battery level:',volBatt)

        #####record:contiene (timeStampEpoch(I-4bytes) - profundidad(H-2bytes))
        recordWl=ustruct.pack('IHH', timeStamp_measurement,hX,volBatt)        #empaqueta timeStamp_measurement(EPOCH) - hX
        print('recordWl: timeStampEpoch - hX - volBatt',ustruct.unpack('IHH', recordWl))
        Date=(time.localtime(timeStamp_measurement))
        dateFile=str(Date[0])+'-'+str(Date[1])+'-'+str(Date[2])+'.log'    #cambiar 3 a 2 para el almacenamiento de archivos diario

        ##################################---STORAGE---########################################
        writeFile(pathLogsWl,"ab",dateFile,recordWl)              #almacenamiento en el archivo diario
        #recordTemporal=ustruct.pack('HIH', IDWl,timeStamp_measurement, hX)        #Empaqueta: ID - timeStampEpoch - hX, archivos temporales para el envío
        writeFile(pathCurrentFile,typeWrite,'',recordWl)          #almacenamiento en el archivo temporal

        #leer datos int para corroborar el almacenamiento*********
        #*********************************************************
        #currentFileBin=readFile(pathLogsWl,'rb',dateFile)
        tmFile=os.stat(pathLogsWl+dateFile)[6]
        print('num de datos flash:', tmFile/8)
        #fmt='H'*(int(tmFile/2))
        #currentFileInt=ustruct.unpack(fmt,currentFileBin)
        #print(currentFileInt) #+++++++++++++++datos almacenados
        #*********************************************************
        #leer datos int para corroborar el almacenamiento*********
        #*********************************************************
        #temporalFile=readFile(pathCurrentFile,'rb','')
        tmFile=os.stat(pathCurrentFile)[6]
        print('num de datos temporales:', tmFile/8)
        #fmt='IH'*(int(tmFile/6))
        #currentFileInt=ustruct.unpack(fmt,temporalFile)
        #print(currentFileInt) +++++datos almacenados
        #*********************************************************
        pycom.rgbled(False)

        ###############---VERIFICA EL sendTime PARA TRANSMITIR---##############
        if (Date[4])/sendTime-int(Date[4]/sendTime)==0 and int(Date[5])==0:
            transmissionMain=True
            #if Date[4]==0:
                #ads1115Write(_CHANNEL1)     #config the channel_1 for to read the battery
                #batt=ads1115Read()
                #volBatt=batteryLevel(batt)
                #print('battery level:',batt)

                #recordBl=ustruct.pack('IH', timeStamp_measurement,volBatt)        #empaqueta timeStamp_measurement(EPOCH) - batt
                #writeFile(pathLogsBl,"ab",dateFile,recordBl)                      #almacenamiento en el archivo diario

                #recordTemporalBl=ustruct.pack('HIH',IDBl, timeStamp_measurement,volBatt)        #empaqueta: timeStamp_measurement(EPOCH) - batt
                #writeFile(pathCurrentFile,typeWrite,'',recordTemporalBl)          #almacenamiento en el archivo temporal

        typeWrite="ab"
        if transmissionMain==False:
            segM=segAlarm()     #segundos que faltan para los siguientes measurementTime(5min)
            print('sleep:',segM-10)
            deepsleep((segM-10)*1000)

    if transmissionMain:
        print('TRANSMISION - LoRa')

        ######################-----TRANSMISIÓN-LORA-----########################
        pkg_transmit = ustruct.pack(">HIHH",IDWl,timeStamp_measurement,hX,volBatt)
        pkg = ustruct.pack(_LORA_PKG_FORMAT % len(pkg_transmit), DEVICE_ID, len(pkg_transmit),0,pkg_transmit)  # type_pkg=0 paquete de datos
        lora_sock.send(pkg)
        ########################################################################

        #leer datos int para corroborar el almacenamiento*********
        #*********************************************************
        #currentFileBin=readFile(pathCurrentFile,'rb','')
        #tmFile=os.stat('logsDir/currentFile')[6]        #number of bytes
        #print('# bytes a trasnmitir:', tmFile)
        #fmt='IH'*(int(tmFile/6))
        #currentFileInt=ustruct.unpack(fmt,currentFileBin)
        #print(currentFileInt)
        #*********************************************************
        #loraTransmission(currentFileBin)
        typeWrite="wb"
        transmissionMain=False

        segM=segAlarm()     #segundos que faltan para los siguientes measurementTime(5min)
        print('sleep:',segM-10)
        deepsleep((segM-10)*1000)
