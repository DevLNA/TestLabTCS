import ephem
import re
import sys, os
import requests
import validators

from datetime import datetime

from PyQt5 import QtWidgets, uic, QtTest, QtWebEngineWidgets
from PyQt5.QtCore import QTimer, QUrl, pyqtSlot, QThreadPool
from PyQt5.QtGui import *
from PyQt5.QtWidgets import qApp, QMessageBox
import controllers.MoveAxis as AxisDevice

import threading
from api.server import FlaskApp

from utils.connection import com_ports
from utils.conversion import Convertion
from utils.coordinates import Coordinates

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

main_ui_path = resource_path('tcspd.ui')

class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        uic.loadUi(main_ui_path, self)
        self.thread_manager = QThreadPool()

        """Precess e point"""
        self.btnPoint.clicked.connect(self.point)
        self.btnPrecessP.clicked.connect(self.precess)
        self.btnAbort.clicked.connect(self.stop)
        self.btnReset.clicked.connect(self.reset_uc)

        """Manete"""
        self.btnWest.clicked.connect(self.move_west)
        self.btnEast.clicked.connect(self.move_east)

        """Telescope Status"""
        self.telescope_status = {}
        self.ra_target = None
        self.dec_target = None
        self.telescope_status["slewing"] = False
        self.telescope_status["decJog"] = False
        self.telescope_status["decRapid"] = False

        global ss
        ss = self.txtPointRA.styleSheet() #original saved
        global statbuf
        statbuf = None
        self.device = None
        self.opd_device = None
        self.azimuth_cup = 0
        self.latitude = '-22:32:04'
        self.btnPrecess.clicked.connect(self.select_to_precess)
        self.btnBSC.clicked.connect(self.load_bsc_default)
        self.btnStart.clicked.connect(self.start_timer)
        self.listWidget.itemDoubleClicked.connect(self.select_to_precess)
        self.sliderTrack.sliderMoved.connect(self.check_track)

        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True  # Set the thread as a daemon to stop it when the main thread exits
        server_thread.start()
        self.timer_update = QTimer()
        self.load_bsc_default()        
        
        self.load_3dmodel()
        self.boxCOM.clear()
        self.boxCOM.addItems(com_ports())
          
    def start_timer(self):
        self.timer_update.timeout.connect(self.update_data)
        self.timer_update.stop()
        self.timer_update.start(1000)
        self.device = self.boxDevice.currentText()
        self.opd_device = AxisDevice.AxisControll(self.device, self.boxCOM.currentText(), 9600)
        self.encDEC.setText('-22:32:04')
        self.statDEC.setStyleSheet("background-color: lightgreen")
        self.statDome.setStyleSheet("background-color: lightgreen")

    def check_track(self):
        if self.sliderTrack.value() == 0:
            try:
                self.opd_device.sideral_ligar()
            except Exception as e:
                print(e)
        elif self.sliderTrack.value() == 1:
            try:
                self.opd_device.sideral_desligar()
            except Exception as e:
                print(e)       

    def select_to_precess(self):
        """select an object and send to precess area"""
        if self.listWidget.selectedItems():
            nameObj = ([item.text().split("\t")[0].strip() for item in self.listWidget.selectedItems()])[0]
            raObj = ([item.text().split("\t")[1].strip() for item in self.listWidget.selectedItems()])[0]
            decObj = ([item.text().split("\t")[2].strip() for item in self.listWidget.selectedItems()])[0]
            magObj = ([item.text().split("\t")[3].strip() for item in self.listWidget.selectedItems()])[0]
            ramObj = ([item.text().split("\t")[4].strip() for item in self.listWidget.selectedItems()])[0]
            decmObj = ([item.text().split("\t")[5].strip() for item in self.listWidget.selectedItems()])[0]
            self.set_precess(nameObj, raObj, decObj, magObj, ramObj, decmObj)
            self.objName.setText(nameObj)
            self.objRA.setText(raObj)
            self.objDEC.setText(decObj)
            self.tabWidget_2.setCurrentIndex(1)
    
    def get_sidereal(self):
        OPD=ephem.Observer()
        OPD.lat='-22.5344'
        OPD.lon='-45.5825'        
        utc = datetime.utcnow()
        OPD.date = utc
        # %% these parameters are for super-precise estimates, not necessary.
        OPD.elevation = 1864 # meters
        OPD.horizon = 0    
        sidereal_time = OPD.sidereal_time()
        return str(sidereal_time), str(utc)[12:19]

    def set_precess(self, nameObj, raObj, decObj, magObj, ramObj, decmObj):
        """Checks object if observable or not"""
        self.txtPointRA.setText(raObj)
        self.txtPointOBJ.setText(nameObj)
        self.txtPointDEC.setText(decObj)
        self.txtPointMag.setText(magObj)
        latitude = '-22:32:04'
        
        sideral, utc = self.get_sidereal()

        #self.working_area(raObj, decObj, latitude, sideral)

    def stop(self):
        """stop any movement and abort slew"""
        try:
            self.opd_device.prog_parar()
            self.telescope_status["slewing"] = False
        except Exception as e:
            print(e)

    def load_3dmodel(self):
        """load outlet page"""
        url = QUrl("http://127.0.0.1:5050")
        if url.isValid():
            try:
                self.TelModel.load(url)                
            except Exception as e:
                print(e)

    def start_server(self):
        try:
            FlaskApp.run(host="127.0.0.1", port=5050)
        except Exception as e: 
            print(e)
    
    def update_telescope_position(self):   
             
        url = f"http://127.0.0.1"
        if validators.url(url):             
            try:
                data = {
                'hourAngle': self.telescope_status["hourAngle"],
                'declination': self.telescope_status["declination"]
            }
                response = requests.post(f"{url.rstrip('/')}:5050/api/telescope/position", json=data)
            except Exception as e:
                print(e)


    def precess(self):
        """precess coordinates based on FINALS"""
        sideral, utc = self.get_sidereal()
        ra_p = self.txtPointRA.text()
        dec_p = self.txtPointDEC.text()
        if ra_p is not None and dec_p is not None:
            self.txtPointRA.setStyleSheet(ss) #back to original
            self.txtPointDEC.setStyleSheet(ss) #back to original
            self.txtTargetRA.setStyleSheet(ss) #back to original
            self.txtTargetDEC.setStyleSheet(ss) #back to original
            
            self.working_area(ra_p, dec_p, sideral)
            new_ra, new_dec = Coordinates.precess_coord(self.gatech, ra_p, dec_p)
            self.txtTargetRA.setText(new_ra.replace(",", "."))
            self.txtTargetDEC.setText(new_dec.replace(",", "."))
        else:
            self.txtPointRA.setStyleSheet("border: 1px solid red;") #changed
            self.txtPointDEC.setStyleSheet("border: 1px solid red;") #changed      
    
    def working_area(self, raObj, decObj, sideral):
        """check if object is in observable zone"""  
        ha = Convertion.ra_to_ah(raObj, sideral)
        elevation, azimuth = Coordinates.get_elevation_azimuth(ha, decObj, self.latitude)
        airmass = Coordinates.get_airmass(elevation)
        observation_time = Coordinates.get_observing_time(ha)
        observation_time = Convertion.hours_to_hms(observation_time)          
        if elevation > 0:
            self.txtPointWorkingArea.setText(" IN ")
            self.txtPointWorkingArea.setStyleSheet("background-color: lightgreen")
            self.txtZenitAngle.setText(str(round(90-elevation, 1)))
            self.txtPointObsTime.setText(str(observation_time))
            self.txtPointAirmass.setText(str(airmass))
        else:
            self.txtPointWorkingArea.setText(" OFF ")
            self.txtPointWorkingArea.setStyleSheet("background-color: indianred")
            self.txtZenitAngle.setText("")
            self.txtPointObsTime.setText("")
            self.txtPointAirmass.setText(str(""))
    
    def load_bsc_default(self):
        """loads BSC default file (by LNA)"""
        bsc_file = 'C:\\Users\\rguargalhone\\Documents\\BSC_08.txt'
        if bsc_file and os.path.exists(bsc_file):
            data = open(str(bsc_file), 'r')
            data_list = data.readlines()

            self.listWidget.clear()

            for eachLine in data_list:
                if len(eachLine.strip())!=0:
                    self.listWidget.addItem(eachLine.strip())

    def load_weather_file(self):
        """load weather txt file from weather station"""
        weather_file = 'C:\\Users\\rguargalhone\\Documents\\weatherData\\download.txt'
        if weather_file and os.path.exists(weather_file):
            try:
                data = open(str(weather_file), 'r')
                lines = data.read().splitlines()
                last_line = lines[-2]
                outside_temp = last_line.split()[2]
                wind_speed = last_line.split()[7]
                weather_bar = last_line.split()[15]
                Humidity = last_line.split()[5]  
                Dew = last_line.split()[6]  
                wind_dir = last_line.split()[8]              
                return (outside_temp, wind_speed, weather_bar, Humidity, Dew, wind_dir)
            except Exception as e:
                print("Error weather file: ", e)
                return ("0", "0", "0", "0")
        else:
            return ("0", "0", "0", "0")
    
    def update_weather(self):
        """loads file from weather station and updates"""
        temperature, windspeed, bar_w, humidity, dew, wind_dir = "22", "15", "780", "85", "0", "NE"
        self.txtTemp.setText(temperature)
        self.txtUmid.setText(humidity)
        self.txtWind.setText(windspeed)
        self.txtDew.setText(dew)
        self.txtBar.setText(bar_w)
        self.txtWindDir.setText(wind_dir)
        """if humidity is higher than 90%, closes shutter"""
        if float(humidity) > 90:
            self.txtUmid.setStyleSheet("background-color: indianred")
            return(True)
        elif 80 < float(humidity) <= 90:
            self.txtUmid.setStyleSheet("background-color: gold")
            return(False)
        elif float(humidity) < 10:
            self.txtUmid.setStyleSheet("background-color: lightgrey")
        else:
            self.txtUmid.setStyleSheet("background-color: lightgrey")
            return(False)
    
    def update_data(self):
        """    Update coordinates every 1s    """
        # year = datetime.datetime.now().strftime("%Y")
        # month = datetime.datetime.now().strftime("%m")
        # day = datetime.datetime.now().strftime("%d")
        # hours = datetime.datetime.now().strftime("%H")
        # minute = datetime.datetime.now().strftime("%M")
        utc_time = str(datetime.utcnow().strftime('%H:%M:%S'))

        #ephem
        self.gatech = ephem.Observer()
        self.gatech.lon, self.gatech.lat = '-45.5825', '-22.534444'

        self.txtLST.setText(str(self.gatech.sidereal_time()))
        self.txtUTC.setText(utc_time)

        # #DATA
        self.get_status()
        self.update_weather()
        self.update_telescope_position()
        
        if statbuf:            
            if "*" in statbuf:
                lat = '-22:32:04'
                sideral, utc = self.get_sidereal()
                if "AH" in self.device:
                    ha = statbuf[0:11]
                    dec = Convertion.dms_to_degrees(self.encDEC.text())
                    self.telescope_status["declination"] = dec
                    self.encHA.setText(ha)
                    HA = Convertion.hms_to_hours(ha)
                    self.telescope_status["hourAngle"] = HA
                    lst = Convertion.hms_to_hours(sideral)
                    ra = Convertion.hours_to_hms((lst-HA)%24, 2)
                    self.encRA.setText(ra)
                    if self.telescope_status["slewing"] and self.dec_target:
                        if abs(dec - Convertion.dms_to_degrees(self.dec_target)) < 3:
                            self.telescope_status["decJog"] = True
                            self.telescope_status["decRapid"] = False
                        if self.telescope_status["decRapid"]:
                            factor = .9
                        elif self.telescope_status["decJog"]:
                            factor = .3
                        else:
                            factor = 0                        
                        if abs(dec - Convertion.dms_to_degrees(self.dec_target)) > .31:
                            if dec < Convertion.dms_to_degrees(self.dec_target):
                                self.encDEC.setText(Convertion.degrees_to_dms(dec + factor))
                            elif dec > Convertion.dms_to_degrees(self.dec_target):
                                self.encDEC.setText(Convertion.degrees_to_dms(dec - factor))
                elif "DEC" in self.device:
                    dec = statbuf[0:11]
                    self.telescope_status["declination"] = dec
                    ra = self.txtTargetRA.text()                
                    self.encDEC.setText(dec)                    
                    self.encRA.setText(ra)
                
                elevation, azimuth = Coordinates.get_elevation_azimuth(ha, dec, lat)
                airmass = Coordinates.get_airmass(elevation)
                observation_time = Coordinates.get_observing_time(ha)
                observation_time = Convertion.hours_to_hms(observation_time)

                self.txtTimeTolimit.setText(observation_time)
                self.azimuth_cup = azimuth
                self.txtPointAirmass.setText(str(airmass))                
                
                self.bit_status()
                if "AH" in self.device:
                    self.ah_status()
    
    def ah_status(self):
        """shows ah statbuf and check sideral stat"""
        if statbuf[19] == "1":
            self.sliderTrack.setValue(1)
        else:
            self.sliderTrack.setValue(0)

    def move_west(self):
        vel = self.boxVelMas.value()
        if statbuf[16] == "0":
            self.opd_device.girar_vel(vel)
    
    def move_east(self):
        vel = -1*self.boxVelMas.value()
        if statbuf[16] == "0":
            self.opd_device.girar_vel(vel)

    @pyqtSlot()
    def get_status(self):
        """calls threading stats"""
        self.thread_manager.start(self.get_prog_status)

    @pyqtSlot()
    def get_status(self):
        """get statbuf from controller"""
        global statbuf
        statbuf = self.opd_device.progStatus()

    def bit_status(self):
        hour = datetime.now().hour
        minutes = datetime.now().minute
        if minutes < 10:
            minutes = '0' + str(minutes)
        """sets the labels colors for each statbit"""
        if len(statbuf)>25:
            if statbuf[15] == "1":
                self.stat3.setStyleSheet("background-color: lightgreen")
                if statbuf[16] == "0":
                    error = self.opd_device.prog_error()
                    self.txtSysMsg.append('['+str(hour)+':'+str(minutes)+'] Error - ' + error)
            else:
                self.stat3.setStyleSheet("background-color: darkgreen")
            if statbuf[16] == "1":
                #BUSY
                self.stat4.setStyleSheet("background-color: lightgreen")
                self.telescope_status["busy"] = 1
            else:
                self.telescope_status["busy"] = 0
                self.stat4.setStyleSheet("background-color: darkgreen")
            if statbuf[17] == "1":
                self.stat5.setStyleSheet("background-color: lightgreen")
                self.statSecurity.setStyleSheet("background-color: lightgreen")
            else:
                self.stat5.setStyleSheet("background-color: darkgreen")
                self.statSecurity.setStyleSheet("background-color: darkgreen")
            if statbuf[19] == "1":
                self.stat6.setStyleSheet("background-color: lightgreen")
            else:
                self.stat6.setStyleSheet("background-color: darkgreen")
            if statbuf[21] == "1":
                self.telescope_status["rapid"] = 1
                self.stat7.setStyleSheet("background-color: lightgreen")
                self.statGross.setStyleSheet("background-color: lightgreen")
            else:
                self.telescope_status["rapid"] = 0
                self.stat7.setStyleSheet("background-color: darkgreen")
                self.statGross.setStyleSheet("background-color: darkgreen")
            if statbuf[22] == "1":
                self.stat8.setStyleSheet("background-color: lightgreen")
                self.telescope_status["jog"] = 1
                self.statGross.setStyleSheet("background-color: lightgreen")
                self.statDome.setStyleSheet("background-color: darkgreen")
            else:
                self.telescope_status["jog"] = 0
                self.stat8.setStyleSheet("background-color: darkgreen")
                self.statGross.setStyleSheet("background-color: darkgreen")
                self.statDome.setStyleSheet("background-color: lightgreen")
            if statbuf[23] == "1":
                self.stat9.setStyleSheet("background-color: lightgreen")
                self.statFine.setStyleSheet("background-color: lightgreen")
            else:
                self.stat9.setStyleSheet("background-color: darkgreen")
                self.statFine.setStyleSheet("background-color: darkgreen")
            if statbuf[24] == "1":
                self.stat10.setStyleSheet("background-color: lightgreen")
            else:
                self.stat10.setStyleSheet("background-color: darkgreen")
            if statbuf[25] == "1":
                self.stat11.setStyleSheet("background-color: lightgreen")
            else:
                self.stat11.setStyleSheet("background-color: darkgreen")
            if statbuf[26] == "1":
                self.stat12.setStyleSheet("background-color: lightgreen")
            else:
                self.stat12.setStyleSheet("background-color: darkgreen")
            if statbuf[23] == "1" and statbuf[25] == "1":
                self.statRA.setStyleSheet("background-color: darkgreen")
            else:
                self.statRA.setStyleSheet("background-color: lightgreen")

    def reset_uc(self):
        try:
            self.opd_device.reset()
        except Exception as e:
            print(e)
    
    def point(self):
        """Points the telescope to a given Target"""
        self.ra_target = self.txtTargetRA.text()
        self.dec_target = self.txtTargetDEC.text()

        if "AH" in self.device:
            if abs(Convertion.dms_to_degrees(self.encDEC.text()) - Convertion.dms_to_degrees(self.dec_target)) > 10:
                self.telescope_status["decRapid"] = True
                self.telescope_status["decJog"] = False
            else:
                self.telescope_status["decJog"] = True
                self.telescope_status["decRapid"] = False
            sid, utc = self.get_sidereal()
            lst = Convertion.hms_to_hours(sid)
            ra = Convertion.hms_to_hours(self.ra_target)
            self.ha_target = Convertion.hours_to_hms(lst - ra, 2)
            if self.ha_target:
                try:
                    if statbuf[25] == "0":
                        self.opd_device.sideral_ligar()
                        QtTest.QTest.qWait(100)
                        if 0.4<(lst - ra) or (lst - ra)<-0.4:
                            self.opd_device.mover_rap(self.ha_target)
                        else:
                            self.opd_device.mover_rel("00 00 10")
                        self.telescope_status["slewing"] = True
                    else:
                        self.telescope_status["slewing"] = False
                        print("erro")

                except Exception as exc_err:
                    print("error: ", exc_err)
            else:
                msg = "Ivalid RA"
                self.show_dialog(msg)
        elif "DEC" in self.device:
            dect_txt = self.txtTargetDEC.text()
            if len(dect_txt) > 2:
                try:
                    if statbuf[25] == "0":
                        self.opd_device.mover_rap(dect_txt)
                    else:
                        print("erro")

                except Exception as exc_err:
                    print("error: ", exc_err)
            else:
                msg = "Ivalid DEC inputs"
                self.show_dialog(msg)

    def close_event(self, event):
        """shows a message to the user confirming closing application"""
        close = QMessageBox()
        close.setText("Are you sure?")
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        close = close.exec()

        if close == QMessageBox.Yes:
            self.reset_uc()
            QtTest.QTest.qWait(500)
            self.opd_device.close_port()
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QtWidgets.QApplication(['', '--no-sandbox'])
    window = MyApp()

    window.show()
    sys.exit(app.exec_())