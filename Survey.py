import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import cm


class Survey:
    def __init__(self, data={}):
        self._survey_positions = data  # Dict of NoiseData objects

    def get_positions(self):
        return self._survey_positions

    def add_position(self, data={}):
        for key in data.keys():
            self._survey_positions[key] = data[key]

    def get_leq_summary(self, dba_only=False, decimals=1, drop_cols=[("Leq", "31.5")]):
        days = []
        nights = []
        for key in self._survey_positions.keys():
            day, night = self._survey_positions[key].get_leq_summary()
            days.append(day)
            nights.append(night)
        day_combi = pd.concat(objs=days, axis=0, keys=self._survey_positions.keys()).drop(labels=drop_cols, axis=1)\
            .round(decimals=decimals)
        night_combi = pd.concat(objs=nights, axis=0, keys=self._survey_positions.keys())\
            .drop(labels=drop_cols, axis=1).round(decimals=decimals)
        if decimals == 0:
            day_combi = day_combi.astype("int32")
            night_combi = night_combi.astype("int32")
        if dba_only:
            return day_combi["LAeq"], night_combi["LAeq"]
        else:
            return day_combi, night_combi

    def get_nth_lmaxes(self, nth=10, night_only=True, sampling_period=2,
                       dba_only=False, decimals=1, drop_cols=[("Lmax", "31.5")]):
        # TODO: Implement daytime
        positions = []
        for key in self._survey_positions.keys():
            maxes = self._survey_positions[key].\
                get_nth_lmaxes(nth=nth, night_only=night_only, sampling_period=sampling_period)
            positions.append(maxes)
        maxes_combi = pd.concat(objs=positions, axis=0, keys=self._survey_positions.keys()).\
            drop(labels=drop_cols, axis=1).round(decimals=decimals)
        if decimals == 0:
            maxes_combi = maxes_combi.astype("int32")
        if dba_only:
            return maxes_combi["LAFmax"]
        else:
            return maxes_combi

    def get_lowest_l90(self, day_t=60, night_t=15, dba_only=False, decimals=1, drop_cols=[("L90", "31.5")]):
        day_positions = []
        night_positions = []
        for key in self._survey_positions.keys():
            day, night = self._survey_positions[key].get_lowest_l90(day_t=day_t, night_t=night_t)
            day_positions.append(day)
            night_positions.append(night)
        day_combi = pd.concat(objs=day_positions, axis=0, keys=self._survey_positions.keys()).\
            drop(labels=drop_cols, axis=1).round(decimals=decimals)
        night_combi = pd.concat(objs=night_positions, axis=0, keys=self._survey_positions.keys()).\
            drop(labels=drop_cols, axis=1).round(decimals=decimals)
        if decimals == 0:
            day_combi = day_combi.astype("int32")
            night_combi = night_combi.astype("int32")
        if dba_only:
            return day_combi["LA90"], night_combi["LA90"]
        else:
            return day_combi, night_combi


