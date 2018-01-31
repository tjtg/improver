# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2017 Met Office.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""Module for generating the weights for topographic zones."""

import warnings

from cf_units import Unit
import iris
from iris.exceptions import InvalidCubeError
import numpy as np

from improver.generate_ancillaries.generate_ancillary import (
    GenerateOrographyBandAncils, _make_mask_cube)


class GenerateTopographicZoneWeights(object):

    """Generate weights generated by determining where the orography lies
    within the topographic zones."""

    def __init__(self):
        """Initialise the class."""
        pass

    @staticmethod
    def add_weight_to_upper_adjacent_band(
            topographic_zone_weights, orography_band, midpoint, band_number,
            max_band_number):
        """Once we have found the weight for a point in one band,
        we need to add 1-weight to the band above for points that are above
        the midpoint, unless the band being processed is the uppermost band.

        Args:
            topographic_zone_weights (np.ndarray):
                Weights that we have already calculated for the points
                within the orography band.
            orography_band (np.ndarray):
                All points within the orography band of interest.
            midpoint (float):
                The midpoint of the band the point is in.
            band_number (float):
                The index that corresponds to the band that is currently being
                processed.
            max_band_number (float):
                The highest index for the bands coordinate in the weights.

        Returns:
            topographic_zone_weights (np.ndarray):
                Weights that we have already calculated for the points within
                the orography band that has been updated to account for the
                upper adjacent band.

        """
        weights = topographic_zone_weights[band_number]

        # For points above the midpoint.
        with np.errstate(invalid='ignore'):
            mask_y, mask_x = np.where(orography_band > midpoint)
        if band_number == max_band_number:
            adjacent_band_number = band_number
            topographic_zone_weights[adjacent_band_number, mask_y, mask_x] = (
                1.0)
        else:
            adjacent_band_number = band_number+1
            topographic_zone_weights[adjacent_band_number, mask_y, mask_x] = (
                1 - weights[mask_y, mask_x])
        return topographic_zone_weights

    @staticmethod
    def add_weight_to_lower_adjacent_band(
            topographic_zone_weights, orography_band, midpoint, band_number):
        """Once we have found the weight for a point in one band,
        we need to add 1-weight to the band below for points that are below
        the midpoint, unless the band being processed is the lowest band.

        Args:
            topographic_zone_weights (np.ndarray):
                Weights that we have already calculated for the points
                within the orography band.
            orography_band (np.ndarray):
                All points within the orography band of interest.
            midpoint (float):
                The midpoint of the band the point is in.
            band_number (float):
                The index that corresponds to the band that is currently being
                processed.

        Returns:
            topographic_zone_weights (np.ndarray):
                Topographic zone array containing the weights that we have
                already calculated for the points within the orography band
                that has been updated to account for the lower adjacent band.

        """
        weights = topographic_zone_weights[band_number]

        # For points below the midpoint.
        with np.errstate(invalid='ignore'):
            mask_y, mask_x = np.where(orography_band < midpoint)
        if band_number == 0:
            adjacent_band_number = band_number
            topographic_zone_weights[adjacent_band_number, mask_y, mask_x] = (
                1.0)
        else:
            adjacent_band_number = band_number-1
            topographic_zone_weights[adjacent_band_number, mask_y, mask_x] = (
                1 - weights[mask_y, mask_x])
        return topographic_zone_weights

    @staticmethod
    def calculate_weights(points, band):
        """Calculate weights where the weight at the midpoint of a band is 1.0
        and the weights at the edge of the band is 0.5. The midpoint is
        assumed to be in the middle of the band.

        Args:
            points (np.ndarray):
                The points at which to find the weights.
                e.g. np.array([125]) or np.array([125, 140]).
            band (list):
                The band to be used for determining the weight that the
                selected points should have within the band
                e.g. [100., 200.].

        Returns:
            interpolated_weights (np.ndarray):
                The weights generated to indicate the contribution of each
                point to a band.
        """
        weights = [0.5, 1.0, 0.5]
        midpoint = np.mean(band)
        band_points = [band[0], midpoint, band[1]]
        interpolated_weights = np.interp(points, band_points, weights)
        return interpolated_weights

    def process(self, orography, thresholds_dict, landmask=None):
        """Calculate the weights depending upon where the orography point is
        within the topographic zones.

        Args:
            orography (iris.cube.Cube):
                Orography on standard grid.
            thresholds_dict (dict):
                Definition of orography bands required.
                The expected format of the dictionary is e.g.
                `{'land': {'bounds': [[0, 50], [50, 200]], 'units': 'm'}}`
        Keyword Args:
            landmask (iris.cube.Cube):
                Land mask on standard grid. If provided sea points are masked
                out in the output array.
        Returns:
            topographic_zone_weights (iris.cube.Cube):
                Cube containing the weights depending upon where the orography
                point is within the topographic zones.
        """
        # Check that orography is a 2d cube.
        if len(orography.shape) != 2:
            msg = ("The input orography cube should be two-dimensional."
                   "The input orography cube has {} dimensions".format(
                       len(orography.shape)))
            raise InvalidCubeError(msg)

        # Find bands and midpoints from bounds.
        bands = thresholds_dict['bounds']
        threshold_units = thresholds_dict["units"]

        # Create topographic_zone_cube first, so that a cube is created for
        # each band. This will allow the data for neighbouring bands to be
        # put into the cube.
        mask_data = np.zeros(orography.shape)
        topographic_zone_cubes = iris.cube.CubeList([])
        for band in bands:
            sea_points_included = False if landmask else True
            topographic_zone_cube = (
                _make_mask_cube(
                    mask_data, orography.coords(), band,
                    threshold_units, sea_points_included=sea_points_included))
            topographic_zone_cubes.append(topographic_zone_cube)
        topographic_zone_weights = topographic_zone_cubes.concatenate_cube()

        # Ensure topographic_zone coordinate units is equal to orography units.
        topographic_zone_weights.coord("topographic_zone").convert_units(
            orography.units)

        # Read bands from cube, now that they can be guaranteed to be in the
        # same units as the orography. The bands are converted to a list, so
        # that they can be iterated through.
        bands = list(topographic_zone_weights.coord("topographic_zone").bounds)
        midpoints = topographic_zone_weights.coord("topographic_zone").points

        # Raise a warning, if orography extremes are outside the extremes of
        # the bands.
        if np.max(orography.data) > np.max(bands):
            msg = ("The maximum orography is greater than the uppermost band. "
                   "This will potentially cause the topographic zone weights "
                   "to not sum to 1 for a given grid point.")
            warnings.warn(msg)

        if np.min(orography.data) < np.min(bands):
            msg = ("The minimum orography is lower than the lowest band. "
                   "This will potentially cause the topographic zone weights "
                   "to not sum to 1 for a given grid point.")
            warnings.warn(msg)

        # Insert the appropriate weights into the topographic zone cube. This
        # includes the weights from the band that a point is in, as well as
        # the contribution from an adjacent band.
        for band_number, band in enumerate(bands):
            # Determine the points that are within the specified band.
            mask_y, mask_x = (
                np.where((orography.data > band[0]) &
                         (orography.data <= band[1])))
            orography_band = np.full(orography.shape, np.nan)
            orography_band[mask_y, mask_x] = orography.data[mask_y, mask_x]

            # Calculate the weights. This involves calculating the
            # weights for all the orography but only inserting weights
            # that are within the band into the topographic_zone_weights cube.
            weights = self.calculate_weights(orography_band, band)
            topographic_zone_weights.data[band_number, mask_y, mask_x] = (
                weights[mask_y, mask_x])

            # Calculate the contribution to the weights from the adjacent
            # lower band.
            topographic_zone_weights.data = (
                self.add_weight_to_lower_adjacent_band(
                    topographic_zone_weights.data, orography_band,
                    midpoints[band_number], band_number))

            # Calculate the contribution to the weights from the adjacent
            # upper band.
            topographic_zone_weights.data = (
                self.add_weight_to_upper_adjacent_band(
                    topographic_zone_weights.data, orography_band,
                    midpoints[band_number], band_number,
                    len(bands)-1))

        # Metadata updates
        topographic_zone_weights.rename("topographic_zone_weights")
        topographic_zone_weights.units = Unit("1")

        # Mask output weights using a land-sea mask.
        topographic_zone_masked_weights = iris.cube.CubeList([])
        for topographic_zone_slice in topographic_zone_weights.slices_over(
                "topographic_zone"):
            if landmask:
                topographic_zone_slice.data = (
                    GenerateOrographyBandAncils().sea_mask(
                        landmask.data, topographic_zone_slice.data))
            topographic_zone_masked_weights.append(topographic_zone_slice)
        topographic_zone_weights = topographic_zone_masked_weights.merge_cube()
        return topographic_zone_weights
