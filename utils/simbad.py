from astroquery.simbad import Simbad


class SimbadQ():
    @staticmethod
    def get_radec(id):
        """Input: Simbad ID
        Return ra (hours), dec (degrees)"""
        identifier = id  
        try:

            result_table = Simbad.query_object(identifier)

            ra = result_table["RA"][0]
            dec = result_table["DEC"][0]

        except:
            ra = None 
            dec = None
        return(ra, dec)