import serial.tools.list_ports

def com_ports():
    """load comports"""
    listP = serial.tools.list_ports.comports()
    connected = []
    for element in listP:
        connected.append(element.device)
    return(connected)