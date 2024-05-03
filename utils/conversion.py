import math
from datetime import datetime
from utils.instances import check_format, is_numeric 

class Convertion():
    @staticmethod
    def get_julian_datetime(date):
        # Ensure correct format
        if not isinstance(date, datetime):
            raise TypeError('Invalid type for parameter "date" - expecting datetime')
        elif date.year < 1801 or date.year > 2099:
            raise ValueError('Datetime must be between year 1801 and 2099')

        # Perform the calculation
        julian_datetime = 367 * date.year - int((7 * (date.year + int((date.month + 9) / 12.0))) / 4.0) + int(
            (275 * date.month) / 9.0) + date.day + 1721013.5 + (
                            date.hour + date.minute / 60.0 + date.second / math.pow(60,
                                                                                    2)) / 24.0 - 0.5 * math.copysign(
            1, 100 * date.year + date.month - 190002.5) + 0.5

        return julian_datetime
    
    @staticmethod
    def ra_to_ah(ra, lst):
        """Calculates hour angle from RA and Sidereal"""
        if not is_numeric(ra):
            ra = Convertion.hms_to_hours(ra)
        if not is_numeric(lst):
            lst = Convertion.hms_to_hours(lst)
        ah = 0.2618*(lst - ra)
        if ah > math.pi:
            ah -= 2 * math.pi
        if ah < -math.pi:
            ah += 2 * math.pi
        ah = ah/0.2618
        return ah
    
    @staticmethod
    def ha_to_ra(ah, lst):
        """Calculates right ascension from Hour Angle and Sidereal"""
        return((lst - ah)%24)
    
    @staticmethod
    def hours_to_hms(hours, decimal_digits=0):
        """
        Converts Float Hour to string Hour, in format hh:mm:ss:cc
        :param hours: Hours (float)
        """
        if is_numeric(hours):        
            sign = "-" if hours < 0 else ""
            hours = abs(hours)
            whole_hours = int(hours)
            fractional_hours = hours - whole_hours

            minutes = int(fractional_hours * 60)
            fractional_minutes = fractional_hours * 60 - minutes

            seconds = int(fractional_minutes * 60)
            fractional_seconds = fractional_minutes * 60 - seconds

            seconds_str = f"{seconds:02}.{int(fractional_seconds * (10 ** decimal_digits)):02d}"

            time_string = f"{sign}{whole_hours:02}:{minutes:02}:{seconds_str}"
            
            return time_string
        else:
            return None

    @staticmethod
    def degrees_to_dms(degrees):
        """
        Converts Degrees to string, in format dd:mm:ss:cc
        :param hours: Degrees (float)
        """
        if is_numeric(degrees):
            sign = "-" if degrees < 0 else "+"
            degrees = abs(degrees)
            degrees_int = int(degrees)
            minutes = int((degrees - degrees_int) * 60)
            seconds = int(((degrees - degrees_int) * 60 - minutes) * 60)
            seconds_decimal = int((((degrees - degrees_int) * 60 - minutes) * 60 - seconds) * 100)

            # Formated value
            degrees_string = f'{sign}{degrees_int:02}:{minutes:02}:{seconds:02}.{seconds_decimal:02}'

            return degrees_string
        else:
            return None

    @staticmethod
    def hms_to_hours(time_string):
        """
        Converts Hours string to float
        :param time_string: Hours String (hh:mm:ss.ss)
        """        
        # Verify separator
        components = check_format(time_string)

        if components:
            hours = abs(int(components[0]))
            minutes = int(components[1])
            seconds = float(components[2])

            total_hours = hours + minutes / 60 + seconds / 3600

            sign = -1 if "-" in time_string else 1
            return sign*total_hours
        else:
            return None

    @staticmethod
    def dms_to_degrees(degrees_string):
        """
        Converts Degrees string to float
        :param degrees_string: Degrees String (dd:mm:ss.ss)
        """
        # Verify separator
        components = check_format(degrees_string)

        if components:
            degrees_int = abs(int(components[0]))
            minutes = int(components[1])    
            seconds = float(components[2])

            degrees = degrees_int + minutes / 60 + seconds / 3600

            sign = -1 if "-" in degrees_string else 1
            return sign*degrees
        else:
            return None
    