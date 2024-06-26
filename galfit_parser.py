#
# This module will read in the galfit best fit values and uncertainties
#

import sys

pyvers = sys.version_info[0]

from astropy.io import fits

"""
  to create an object containing galfit results, use obj = GalfitResult('<output block fits file>')
  you can access to the output parameters by:
       obj.component_num.param
"""


class GalfitComponent(object):
    """
    stores results from one component of the fit
    """

    def __init__(self, galfitheader, component_number):
        """
        takes in the fits header from HDU 3 (the galfit model) from a galfit output file
        and the component number to extract
        """
        # checks
        assert component_number > 0
        assert "COMP_" + str(component_number) in galfitheader

        self.component_type = galfitheader["COMP_" + str(component_number)]
        self.component_number = component_number

        flagged_numerical_params = []

        headerkeys = [i for i in galfitheader.keys()]
        comp_params = []
        for i in headerkeys:
            if i.startswith(str(component_number) + "_"):
                comp_params.append(i)
        for param in comp_params:
            val = galfitheader[param]
            # we know that val is a string formatted as 'result +/- uncertainty'
            # if val is fixed in GalFit, it is formatted as '[result]'
            paramsplit = param.split("_")

            # If there's some numerical error, should output a warning (*)
            if "*" in val:
                flagged_numerical_params.append(paramsplit[1].lower())

            if "[" in val:  # fixed parameter
                if pyvers == 2:
                    val = val.translate(None, "[]*")
                elif pyvers == 3:
                    val = val.translate(str.maketrans("", "", "[]*"))
                else:
                    raise ValueError(
                        "python version {} not recognized!".format(pyvers)
                    )
                setattr(self, paramsplit[1].lower(), float(val))
                setattr(self, paramsplit[1].lower() + "_err", None)

            elif "{" in val:  # constrained parameter (eg to another comp)
                if pyvers == 2:
                    val = val.translate(None, "{}*")
                elif pyvers == 3:
                    val = val.translate(str.maketrans("", "", "{}*"))
                else:
                    raise ValueError(
                        "python version {} not recognized!".format(pyvers)
                    )
                setattr(self, paramsplit[1].lower(), float(val))
                setattr(self, paramsplit[1].lower() + "_err", None)

            elif paramsplit[1].upper() in ["TINNR", "TOUTR", "INNER", "OUTER"]:
                # Variables dealing with truncation settings / parameters
                if pyvers == 2:
                    val = val.translate(None, "*").split()
                elif pyvers == 3:
                    val = val.translate(str.maketrans("", "", "*")).split()
                else:
                    raise ValueError(
                        "python version {} not recognized!".format(pyvers)
                    )
                setattr(self, paramsplit[1].lower(), float(val[0]))
            else:  # normal variable parameter
                if pyvers == 2:
                    val = val.translate(None, "*").split()
                elif pyvers == 3:
                    val = val.translate(str.maketrans("", "", "*")).split()
                else:
                    raise ValueError(
                        "python version {} not recognized!".format(pyvers)
                    )
                setattr(self, paramsplit[1].lower(), float(val[0]))
                setattr(self, paramsplit[1].lower() + "_err", float(val[2]))

        self.flagged_numerical_params = flagged_numerical_params


class GalfitResults(object):
    """
    This class stores galfit results information
    INPUT:
        galfit_fits_file: the block fits file generated by GalFit
    """

    def __init__(self, galfit_fits_file):
        """
        init method for GalfitResults. Take in a string that is the name
        of the galfit output fits file
        """
        hdulist = fits.open(galfit_fits_file)
        # now some checks to make sure the file is what we are expecting
        assert len(hdulist) == 4
        galfitmodel = hdulist[2]
        galfitheader = galfitmodel.header
        galfit_in_comments = False
        for i in galfitheader["COMMENT"]:
            galfit_in_comments = galfit_in_comments or "GALFIT" in i
        assert True == galfit_in_comments
        assert "COMP_1" in galfitheader
        # now we've convinced ourselves that this is probably a galfit file

        self.galfit_fits_file = galfit_fits_file
        # read in the input parameters
        self.input_initfile = galfitheader["INITFILE"]
        self.input_datain = galfitheader["DATAIN"]
        self.input_sigma = galfitheader["SIGMA"]
        self.input_psf = galfitheader["PSF"]
        self.input_constrnt = galfitheader["CONSTRNT"]
        self.input_mask = galfitheader["MASK"]
        self.input_fitsect = galfitheader["FITSECT"]
        self.input_convbox = galfitheader["CONVBOX"]
        self.input_magzpt = galfitheader["MAGZPT"]

        # read in the chi-square value
        self.chisq = galfitheader["CHISQ"]
        self.ndof = galfitheader["NDOF"]
        self.nfree = galfitheader["NFREE"]
        self.reduced_chisq = galfitheader["CHI2NU"]

        # read in galfit flags:
        self.galfit_flags = galfitheader["FLAGS"].split(" ")

        # find the number of components
        num_components = 1  # already verified above
        while True:
            if "COMP_" + str(num_components + 1) in galfitheader:
                num_components = num_components + 1
            else:
                break
        self.num_components = num_components

        for i in range(1, self.num_components + 1):
            setattr(
                self, "component_" + str(i), GalfitComponent(galfitheader, i)
            )

        hdulist.close()
