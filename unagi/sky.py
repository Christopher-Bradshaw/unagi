
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sky background related"""

from __future__ import annotations

import os
import copy
import warnings

import numpy as np
from scipy.stats import sigmaclip

from astropy.table import Table

from . import utils

__all__ = ['SkyObjs', 'AperPhot', 'S18A_APER']


class AperPhot():
    """
    Class for aperture photometry in HSC.
    """
    PIX = 0.168 # arcsec/pixe

    def __init__(self, name, rad, rerun='s18a'):
        """Start a aperture photometry object."""
        self.aper_id = name
        self.r_pix = rad
        self.area_pix = np.pi * (rad ** 2.0)
        self.r_arcsec = rad * self.PIX
        self.area_arcsec = np.pi * (self.r_arcsec ** 2.0)

        # Name of the columns for flux and flux error
        self.flux_col = self.flux(rerun=rerun)
        self.err_col = self.err(rerun=rerun)

    def flux(self, band=None, rerun=rerun):
        """Aperture flux column name in S18A."""
        if rerun == 's18a':
            if band is not None:
                return "{0}_apertureflux_{1}_flux".format(band.strip(), self.aper_id)
            return "apertureflux_{0}_flux".format(self.aper_id)
        else:
            raise NotImplementedError("# Only S18A data are available.")

    def err(self, band=None, rerun=rerun):
        """Aperture flux error column name in S18A."""
        if rerun == 's18a':
            if band is not None:
                return "{0}_{1}sigma".format(band.strip(), self.s18a_flux())
            return "{0}sigma".format(self.s18a_flux())
        else:
            raise NotImplementedError("# Only S18A data are available.")

# Aperture flux in S18A
S18A_APER_ID = ['10', '15', '20', '30', '40', '57', '84',
                '118', '168', '235']
S18A_APER_RAD = [3.0, 4.5, 6.0, 9.0, 12.0, 17.0, 25.0, 35.0, 50.0, 70.0]
S18A_APER = {}
for ii, rr in zip(S18A_APER_ID, S18A_APER_RAD):
    S18A_APER['aper{0}'.format(ii)] = AperPhot(ii, rr)


class SkyObjs():
    """
    Class for HSC sky objects.
    """
    # Convert the flux from erg/s/cm^2/Hz to HSC image value
    CGS_TO_MUJY = 1.7378E30

    # List of filters
    FILTER_LIST = ['HSC-G', 'HSC-R', 'HSC-I', 'HSC-Z', 'HSC-Y']

    # Nicknames of filters
    FILTER_SHORT = ['g', 'r', 'i', 'z', 'y']

    def __init__(self, skyobjs, meas=False, nobj_min=5):
        """
        Initialize an object for HSC sky object catalog.
        """
        # Whether it is a forced photometry or a measurement catalog
        if meas:
            self.ra_col = 'i_ra'
            self.dec_col = 'i_dec'
            self.type = 'meas'
            self.meas = True
        else:
            self.ra_col = 'ra'
            self.dec_col = 'dec'
            self.type = 'force'
            self.meas = False

        # If skyobjs is a file name, read in the catalog
        if isinstance(skyobjs, str):
            _, file_ext = os.path.splitext(skyobjs)
            if file_ext == '.npy':
                self.skyobjs = np.load(skyobjs)
            elif file_ext == '.fits':
                self.skyobjs = Table.read(skyobjs).as_array().data
            else:
                raise TypeError("# Wrong file type: npy or fits!")
        elif isinstance(skyobjs, Table):
            try:
                self.skyobjs = skyobjs.as_array().data
            except Exception:
                self.skyobjs = skyobjs.as_array()
        elif isinstance(skyobjs, np.ndarray) or isinstance(skyobjs, np.recarray):
            self.skyobjs = skyobjs

        # Minimum number of sky objects
        self.n_min = nobj_min

        # List of Tracts
        self.tract_list = list(np.unique(self.skyobjs['tract']))
        self.n_tract = len(self.tract_list)

        # List of Patches and Tracts
        self.tract_patch = np.unique(
            ["{0}_{1:03d}".format(t, p) for t, p in
             zip(self.skyobjs['tract'], self.skyobjs['patch'])])
        self.n_tract_patch = len(self.tract_patch)

    def select_tract(self, tract, patch=None, n_min=10) -> 'SkyObjs':
        """Select sky objects on one Tract (and Patch) from the catalog """
        tract_mask = self.skyobjs['tract'] == tract
        if tract_mask.sum() == 0:
            warnings.warn("# Tract {0} is not available!".format(tract))
            return None

        if patch is not None:
            tract_mask = tract_mask & (self.skyobjs['patch'] == patch)
            if tract_mask.sum() == 0:
                warnings.warn("# Tract {0}-Patch {1} is not available!".format(tract, patch))
                return None

        # Number of sky objects available
        n_skyobj = tract_mask.sum()
        if n_skyobj <= n_min:
            warnings.warn("# Less than {0} skyobjs is available.")
            return None

        return SkyObjs(self.skyobjs[tract_mask])

    def select_box(self, ra1, ra2, dec1, dec2, n_min=5) -> 'SkyObjs':
        """Select sky objects in a box region."""
        # Order of the coordinates
        if ra1 >= ra2:
            ra1, ra2 = ra2, ra1
        if dec1 >= dec2:
            dec1, dec2 = dec2, dec1

        # Select sky objects in that region
        box_mask = ((self.skyobjs[self.ra_col] >= ra1) & (self.skyobjs[self.ra_col] <= ra2) &
                    (self.skyobjs[self.dec_col] >= dec1) & (self.skyobjs[self.dec_col] <= dec2))

        if box_mask.sum() == 0:
            warnings.warn(
                "# No sky object in this region: {0}:{1}-{2}:{3}".format(ra1, ra2, dec1, dec2))
            return None

        if box_mask.sum() <= n_min:
            warnings.warn("# Only find {0} sky object(s)".format(box_mask.sum()))

        return SkyObjs(self.skyobjs[box_mask])

    def select_circle(self):
        """Select sky objects within a circle."""
        raise NotImplementedError("# Not yet")

    def flux_stats(self, aper, band, rerun='s18a', sigma=3.5,
                   kde=False, bw=None, to_mujy=True):
        """Basic statistics of the flux."""
        u_factor = self.CGS_TO_MUJY if to_mujy else 1.0
        assert band in self.FILTER_SHORT, "# Wrong filter name: {}".format(band)

        flux_col = aper.flux(rerun=rerun, band=band)

        try:
            flux = self.skyobjs[flux_col] * u_factor
        except ValueError:
            raise Exception("# Wrong flux column name: {0}".format(flux_col))

        return utils.stats_summary(flux, sigma=sigma, n_min=self.n_min,
                                   kde=kde, bw=bw)

    def snr_stats(self, aper, band, rerun='s18a', sigma=3.5, kde=False, bw=None):
        """Basic statistics of the S/N."""
        assert band in self.FILTER_SHORT, "# Wrong filter name: {}".format(band)

        flux_col = aper.flux(rerun=rerun, band=band)
        err_col = aper.err(rerun=rerun, band=band)

        try:
            snr = self.skyobjs[flux_col] / self.skyobjs[err_col]
        except ValueError:
            raise Exception("# Wrong column names: {0}/{1}".format(flux_col, err_col))

        return utils.stats_summary(snr, sigma=sigma, n_min=self.n_min,
                                   kde=kde, bw=bw)

    def mu_stats(self, aper, band, to_mujy=True, rerun='s18a', sigma=3.5,
                 kde=False, bw=None):
        """Basic statistics of the aperture flux density."""
        u_factor = self.CGS_TO_MUJY if to_mujy else 1.0
        assert band in self.FILTER_SHORT, "# Wrong filter name: {}".format(band)

        flux_col = aper.flux(rerun=rerun, band=band)

        try:
            mu = self.skyobjs[flux_col] * u_factor / aper.area_arcsec
        except ValueError:
            raise Exception("# Wrong flux column name: {0}".format(flux_col))

        return utils.stats_summary(mu, sigma=sigma, n_min=self.n_min,
                                   kde=kde, bw=bw)

    def sum_all_filters(self, aper, rerun='s18a'):
        """Provide a summary of sky objects in all five bands."""
        raise NotImplementedError("# Not yet")
