#!/bin/env python3

import inspect
import itertools
import time
import types
import signal
import numpy as np
import datetime
import time

import matplotlib.pyplot as plt
from bayes_opt import BayesianOptimization, UtilityFunction
import warnings
warnings.filterwarnings("ignore")

import venus_utils.venusplc as venusplc
import plcauto.dbwriter as dbwriter
import plcauto.maths as maths

class Venus:
    
    def __init__(
        self,
        inj_limits=[175, 185],
        mid_limits=[145, 155],
        ext_limits=[135, 145],
        beam_range=[50, 100],
    ):
        """The limits on the magnetic solenoids currents and the beam range (ouput).
        A random jitter can be added also (fraction of 1.)."""
        self.inj_limits = inj_limits
        self.mid_limits = mid_limits
        self.ext_limits = ext_limits
        self.beam_range = beam_range
        self.currents = np.zeros(3)
        self.rng = np.random.default_rng(42)

        self.venus = venusplc.VENUSController('../scripts/venus_utils/config.ini')


    def set_mag_currents(self, inj, mid, ext):
        """Set the magnetic currents on the coils."""
        for v, lim in zip([inj, mid, ext], [self.inj_limits, self.mid_limits, self.ext_limits]):
            if v < lim[0] or v > lim[1]:
                raise ValueError("Setting outside limits")
        # self.currents = np.array([inj, mid, ext])
        venus = self.venus
        venus.write({'inj_i':inj})         # injection solenoid current [A]
        venus.write({'ext_i':ext})         # extraction solenoid current [A]
        venus.write({'mid_i':mid})         # middle solenoid current [A]

    
    def get_noise_level(self):
        # return std of the noise
        # noise = self.jitter*(self.beam_range[1] - self.beam_range[0])
        return 0.1 # assume 0.1% noise
    
    def get_bounds(self, i):
        if i == 0:
            return self.inj_limits
        elif i==1:
            return self.mid_limits
        elif i==2:
            return self.ext_limits
    
    def _rescale_output(self, output):
        """assume 10mA is the largest possible imput, scale that to 100"""
        bench = 10                          # 10 mA. Assumed best current. 
        return output / bench * 100

    def get_beam_current(self):
        """Read the current value of the beam current"""
        venus = self.venus
        Ifc = venus.read(['fcv1_i'])*1e6    # faraday cup current (single species current) in microamps
        return self._rescale_output(Ifc)

    def monitor(self):
        venus = self.venus
        Ifc = venus.read(['fcv1_i'])*1e6        # faraday cup current (single species current) in microamps
        Idrain = venus.read(['extraction_i'])   # drain current ~ total extracted beam current [mA]
        Pinj = venus.read(['inj_mbar'])         # injection pressure [torr]

        # things also worth monitoring to understand system
        Ibias = venus.read(['bias_i'])          # bias disk current [mA]
        Ipull = venus.read(['puller_i'])        # puller electrode current [mA]
        Xsrc = venus.read(['x_ray_source'])     # amount of x-rays produced by source [?]
        Pext = venus.read(['ext_mbar'])         # pressure just outside source [torr]
        HHe = venus.read(['four_k_heater_power'])   # liquid He heater power [W]

        # TODO: write to database or somewhere

venus = Venus()



# Define the black box function to optimize.
def black_box_function(A, B, C):
    venus.set_mag_currents(A, B, C)
    t_end = time.time() + 5 * 60 # wait for 5min
    while time.time() < t_end:
        venus.monitor()

    t_end = time.time() + 10 # data acquisition for 10s
    v_list = []
    while time.time() < t_end:
        v = venus.get_beam_current()
        v_list.append(v)
    v_mean = sum(v_list) / len(v_list)
    # save the v list?
    return v_mean

pbounds = {"A": (175, 185), "B": (145, 155), "C": (135, 145)}

optimizer = BayesianOptimization(f = black_box_function, pbounds = pbounds, verbose = 1)
noise = venus.get_noise_level()
optimizer.maximize(init_points = 5, n_iter = 30, kappa=4.2, alpha=noise**2) # 
print("Best result: {}; f(x) = {}.".format(optimizer.max["params"], optimizer.max["target"]))

