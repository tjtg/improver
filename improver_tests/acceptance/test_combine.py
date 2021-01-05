# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2017-2020 Met Office.
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
"""Tests for the combine CLI"""

import pytest

from . import acceptance as acc

pytestmark = [pytest.mark.acc, acc.skip_if_kgo_missing]
SCREEN_TEMP = "temperature_at_screen_level"
RAIN_ACCUM = "rainfall_accumulation"
CLI = acc.cli_name_with_dashes(__file__)
run_cli = acc.run_cli(CLI)


def test_basic(tmp_path):
    """Test basic combine operation"""
    kgo_dir = acc.kgo_root() / "combine/basic"
    kgo_path = kgo_dir / "kgo_cloud.nc"
    low_cloud_path = kgo_dir / "low_cloud.nc"
    medium_cloud_path = kgo_dir / "medium_cloud.nc"
    output_path = tmp_path / "output.nc"
    args = [
        "--operation",
        "max",
        "--new-name",
        "cloud_area_fraction",
        low_cloud_path,
        medium_cloud_path,
        "--output",
        f"{output_path}",
    ]
    run_cli(args)
    acc.compare(output_path, kgo_path)


def combine_kgos(kgo_dir, param, suffix=""):
    times = [f"20180101T0{h}00Z-PT000{h}H" for h in (1, 2, 3)]
    temperatures = [kgo_dir / f"{time}-{param}{suffix}.nc" for time in times]
    return temperatures


@pytest.mark.parametrize("minmax", ("_min", "_max"))
def test_minmax_temperatures(tmp_path, minmax):
    """Test combining minimum and maximum temperatures"""
    kgo_dir = acc.kgo_root() / "combine/bounds"
    kgo_path = kgo_dir / f"kgo{minmax}.nc"
    temperatures = combine_kgos(kgo_dir, SCREEN_TEMP, minmax)
    output_path = tmp_path / "output.nc"
    args = ["--operation", f"{minmax[1:]}", *temperatures, "--output", f"{output_path}"]
    run_cli(args)
    acc.compare(output_path, kgo_path)


def test_combine_accumulation(tmp_path):
    """Test combining precipitation accumulations"""
    kgo_dir = acc.kgo_root() / "combine/accum"
    kgo_path = kgo_dir / "kgo_accum.nc"
    rains = combine_kgos(kgo_dir, RAIN_ACCUM)
    output_path = tmp_path / "output.nc"
    args = [*rains, "--output", f"{output_path}"]
    run_cli(args)
    acc.compare(output_path, kgo_path)


def test_mean_temperature(tmp_path):
    """Test combining mean temperature"""
    kgo_dir = acc.kgo_root() / "combine/bounds"
    kgo_path = kgo_dir / "kgo_mean.nc"
    temperatures = combine_kgos(kgo_dir, SCREEN_TEMP)
    output_path = tmp_path / "output.nc"
    args = ["--operation", "mean", *temperatures, "--output", f"{output_path}"]
    run_cli(args)
    acc.compare(output_path, kgo_path)


def test_midpoint(tmp_path):
    """Test option to use midpoint of expanded coordinates"""
    kgo_dir = acc.kgo_root() / "combine/bounds"
    kgo_path = kgo_dir / "kgo_midpoint.nc"
    temperatures = combine_kgos(kgo_dir, SCREEN_TEMP)
    output_path = tmp_path / "output.nc"
    args = [
        "--operation",
        "mean",
        *temperatures,
        "--use-midpoint",
        "--output",
        f"{output_path}",
    ]
    run_cli(args)
    acc.compare(output_path, kgo_path)


def test_combine_broadcast(tmp_path):
    """Test combining precipitation realizations with phaseprob"""
    kgo_dir = acc.kgo_root() / "combine/broadcast"
    kgo_path = kgo_dir / "kgo.nc"
    inputs = [kgo_dir / f for f in ["input_larger_cube.nc", "input_smaller_cube.nc"]]
    output_path = tmp_path / "output.nc"
    args = [
        *inputs,
        "--operation",
        "multiply",
        "--broadcast-to-threshold",
        "--new-name",
        "rainfall_rate",
        "--output",
        f"{output_path}",
    ]
    run_cli(args)
    acc.compare(output_path, kgo_path)
