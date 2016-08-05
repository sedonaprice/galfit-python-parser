#
# This module will read in the galfit best fit values and uncertainties
#

# Small edits to handle fixed parameters, especially in the sky parameter component:
#   galfit header entry sometimes has format '[VALUE]' instead of 'RESULT +/- ERR'
# SHP, 2015-12-05

# Edit to read in galfit flags from header
# SHP, 2016-02-10

from astropy.io import fits

class GalfitComponent(object):
    """
    stores results from one component of the fit
    """
    def __init__(self,galfitheader,component_number):
        """
        takes in the fits header from HDU 3 (the galfit model) from a galfit output file
        and the component number to extract
        """
        #checks
        assert component_number > 0
        assert "COMP_" + str(component_number) in galfitheader
        
        self.component_type = galfitheader["COMP_" + str(component_number)]
        self.component_number = component_number
        
        headerkeys = [i for i in galfitheader.keys()]
        comp_params = []
        component_flag = 0
        for i in headerkeys:
            # # Will match 11_ for 1_, etc:
            #if str(component_number) + '_' in i:
            if i.startswith(str(component_number)+'_'):
                comp_params.append(i)
        for param in comp_params:
            val = galfitheader[param]
            #we know that val is a string formatted as 'result +/- uncertainty'
            val = val.split()
            paramsplit = param.split('_')
            try:
                if len(val) > 1:
                    setattr(self,paramsplit[1].lower(),float(val[0]))
                    setattr(self,paramsplit[1].lower() + '_err',float(val[2]))
                else:
                    # Fixed parameter: formatted as [value] or relative so {value}
                    val = val[0]
                    if val[0] == '[':
                        val = val.split(']')[0].split('[')
                    elif val[0] == '{':
                        val = val.split('}')[0].split('{')
                    setattr(self,paramsplit[1].lower(),float(val[1]))
                    setattr(self,paramsplit[1].lower() + '_err',float(0.))
            except:
                if len(val) > 1:
                    val0 = val[0].split('*')
                    val2 = val[2].split('*')
                    setattr(self,paramsplit[1].lower(),float(val0[1]))
                    setattr(self,paramsplit[1].lower() + '_err',float(val2[1]))
                else:
                    # Fixed parameter: formatted as [value]
                    val = val[0]
                    val = val.split(']')[0].split('[')
                    val = val[1].split('*')
                    setattr(self,paramsplit[1].lower(),float(val[1]))
                    setattr(self,paramsplit[1].lower() + '_err',float(0.))
                    
                component_flag += 1
                
            # For case of ar: add a component renaming it to "q":
            if paramsplit[1].lower() == 'ar':
                setattr(self, 'q', self.__dict__[paramsplit[1].lower()])
                setattr(self, 'q_err', self.__dict__[paramsplit[1].lower()+"_err"])
        
        setattr(self, 'flag', component_flag)
        
            
class GalfitResults(object):
    """
    This class stores galfit results information
    """
    def __init__(self, galfit_fits_file):
        """
        init method for GalfitResults. Take in a string that is the name
        of the galfit output fits file
        """
        hdulist = fits.open(galfit_fits_file)
        #now some checks to make sure the file is what we are expecting
        assert len(hdulist) == 4
        galfitmodel = hdulist[2]
        galfitheader = galfitmodel.header
        galfit_in_comments = False
        for i in galfitheader['COMMENT']:
            galfit_in_comments = galfit_in_comments or "GALFIT" in i
        assert True == galfit_in_comments
        assert "COMP_1" in galfitheader
        #now we've convinced ourselves that this is probably a galfit file
        
        self.galfit_fits_file = galfit_fits_file
        #read in the input parameters
        self.input_initfile = galfitheader['INITFILE']
        self.input_datain = galfitheader["DATAIN"]
        self.input_sigma = galfitheader["SIGMA"]
        self.input_psf = galfitheader["PSF"]
        self.input_constrnt = galfitheader["CONSTRNT"]
        self.input_mask = galfitheader["MASK"]
        self.input_fitsect = galfitheader["FITSECT"]
        self.input_convbox = galfitheader["CONVBOX"]
        self.input_magzpt = galfitheader["MAGZPT"]
        
        #read in the chi-square value
        self.chisq = galfitheader["CHISQ"]
        self.ndof = galfitheader["NDOF"]
        self.nfree = galfitheader["NFREE"]
        self.reduced_chisq = galfitheader["CHI2NU"]
        
        #read in galfit flags:
        self.galfit_flags = galfitheader["FLAGS"].split(" ")
        
        #find the number of components
        num_components = 1 #already verified above
        while True:
            if "COMP_" + str(num_components + 1) in galfitheader:
                num_components = num_components + 1
            else:
                break
        self.num_components = num_components
        
        for i in range(1, self.num_components + 1):
            setattr(self,"component_" + str(i),GalfitComponent(galfitheader,i))
            
        hdulist.close()
        
