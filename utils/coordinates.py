import math, ephem, datetime
from utils.conversion import Convertion
from utils.instances import is_numeric

RAD2DEG = 180 / math.pi
DEG2RAD = math.pi / 180.0

class Coordinates():
    @staticmethod
    def precess_coord(OPD, ra, dec):
        """Correct J2000 values due to Nutation
        :params: OPD is ephem Location, right ascension HMS and dec in DMS format"""
        star = ephem.FixedBody()
        star._ra  = ephem.hours(ra.replace(" ",":"))
        star._dec = ephem.degrees(dec.replace(" ",":"))
        star.compute(OPD)
        ra_hms = str(star.ra).replace(":", " ")
        dec_dms = str(star.dec).replace(":", " ")

        return ra_hms, dec_dms

    @staticmethod
    def get_elevation_azimuth(ha, dec, latitude):
        """Calculates Azimuth and Elevation""" 
        if not is_numeric(ha):
            ha = Convertion.hms_to_hours(ha)
        if not is_numeric(dec):
            dec = Convertion.dms_to_degrees(dec)
        if not is_numeric(latitude):
            latitude = Convertion.dms_to_degrees(latitude)

        H = ha * 15

        #altitude calc
        sinAltitude = (math.sin(dec * DEG2RAD)) * (math.sin(latitude * DEG2RAD)) + (math.cos(dec * DEG2RAD) * math.cos(latitude * DEG2RAD) * math.cos(H * DEG2RAD))
        elevation = math.asin(sinAltitude) * RAD2DEG #altura em graus
        elevation = round(elevation, 2)

        #azimuth calc
        y = -1 * math.sin(H * DEG2RAD)
        x = (math.tan(dec * DEG2RAD) * math.cos(latitude * DEG2RAD)) - (math.cos(H * DEG2RAD) * math.sin(latitude * DEG2RAD))

        #This AZposCalc is the initial AZ for dome positioning
        azimuth = math.atan2(y, x) * RAD2DEG

        #converting neg values to pos
        if (azimuth < 0) :
            azimuth = azimuth + 360    

        return elevation, azimuth

    @staticmethod
    def get_airmass(angle):  
        """Calculates Airmass
        :params: angle in degrees"""  
        if angle<0:
            airmass = 0
        elif angle >=90:
            airmass = 1
        else:
            airMass = 1 / (math.cos(angle * DEG2RAD) + (0.50572 * (96.07995 - angle) ** -1.6364))
            airmass = round(airMass, 2)
        return airmass

    @staticmethod
    def get_observing_time(ha):
        """Check the time of observation of a given object 
        calculates if target is above the horizon, respectin the limits by the engineering team
        :params: hour angle """ 
        if not is_numeric(ha):
            ha = Convertion.hms_to_hours(ha)
        
        #time of observation for an object
        obsTime = 6-ha

        return obsTime

    @staticmethod
    def check_side_pier(ha):
        """Side of the Pier
        :params: hour angle in hours"""
        if not is_numeric(ha):
            ha = Convertion.hms_to_hours(ha)

        if (ha) > 0:
            return "E"
        else:
            return "W"
    
    @staticmethod
    def calc_twilight(latitude, longitude, altitude):
        """Calculates sun altitude, sunset and sunrise
        also calculates moon light %. This is useful when 
        using scripts, and prevent poiting when sun is up"""
        try:
            OPD = Coordinates.get_ephem(latitude, longitude, altitude)
            sun = ephem.Sun(OPD)
            moon = ephem.Moon(OPD)
            moon_phase = moon.moon_phase 
            sun_alt = Convertion.dms_to_degrees(str(sun.alt))      
            sunset = ephem.localtime(OPD.next_setting(sun)) #todays
            sunrise = ephem.localtime(OPD.next_rising(sun)) #tomorrows
            return {"moon": {"phase": moon_phase}, "sun": {"elevation": sun_alt, "set": sunset, "rise": sunrise}}
        except (ephem.AlwaysUpError, ephem.NeverUpError, ValueError) as e:
            return {"error": str(e)}
        
    
    @staticmethod
    def get_ephem(latitude, longitude, altitude):
        OPD=ephem.Observer()
        if not is_numeric(latitude):
            latitude = Convertion.dms_to_degrees(latitude)
        if not is_numeric(longitude):
            longitude = Convertion.dms_to_degrees(longitude)
        try:
            OPD.lat=str(Convertion.dms_to_degrees(latitude))
            OPD.lon=str(Convertion.dms_to_degrees(longitude))            
            OPD.date = datetime.datetime.utcnow()
            if is_numeric(altitude):                
                OPD.elevation = altitude # meters
            else:
                OPD.elevation = 0
        except:
            OPD.lat='-22.5344'
            OPD.lon='-45.5825'
            OPD.date = datetime.datetime.utcnow()
            OPD.elevation = 1864 
        
        OPD.horizon = 0

        return OPD

    @staticmethod
    def check_near_zenith(ha):
        """returns true slightly before RA axis reach Zenith, which would activate
        sensors making telescope to stop. This function prevents this"""
        zenith_status = False        
        
        if 0 < ha < 0.004: 
            zenith_status = True
        return zenith_status
    