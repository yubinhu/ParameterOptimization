#!/bin/env python3

import inspect
import itertools
import time
import types
import signal
import numpy as np
import datetime

import venus_utils.venusplc as venusplc
import plcauto.dbwriter as dbwriter
import plcauto.maths as maths

venus = venusplc.VENUSController('../scripts/venus_utils/config.ini')

while 1:  # repeat some loop

    # Some of the things we'll want to control
    if 0:
        venus.write({'inj_i':new_Iinj})         # injection solenoid current [A]
        venus.write({'ext_i':new_Iext})         # extraction solenoid current [A]
        venus.write({'mid_i':new_Imid})         # middle solenoid current [A]


    while monitoring:  #  monitor the system for some time watching the following parameters
        # things you'll want to monitor for settling of new setting
        Ifc = venus.read(['fcv1_i'])*1e6        # faraday cup current (single species current) in microamps
        Idrain = venus.read(['extraction_i'])   # drain current ~ total extracted beam current [mA]
        Pinj = venus.read(['inj_mbar'])         # injection pressure [torr]

        # things also worth monitoring to understand system
        Ibias = venus.read(['bias_i'])          # bias disk current [mA]
        Ipull = venus.read(['puller_i'])        # puller electrode current [mA]
        Xsrc = venus.read(['x_ray_source'])     # amount of x-rays produced by source [?]
        Pext = venus.read(['ext_mbar'])         # pressure just outside source [torr]
        HHe = venus.read(['four_k_heater_power'])   # liquid He heater power [W]

