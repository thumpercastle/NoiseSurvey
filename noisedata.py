import csv
import os

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import cm

pd.set_option("display.max_rows", 21)
pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 1000)

# Matplotlib formatting
font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 12}

matplotlib.rc('font', **font)

params = {
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'large',
         'ytick.labelsize':'large'}
matplotlib.rcParams.update(params)

#TODO: Subscript in axis and plot titles


# def create_blank_spreadsheet(path=None, spectra="octaves", lowest_band="63 Hz Leq", highest_band="8000 Hz Leq"):
#     assert path is not None
#
#     octave_bands = ["31.5 Hz Leq", "63 Hz Leq", "125 Hz Leq", "250 Hz Leq", "500 Hz Leq", "1000 Hz Leq",
#                     "2000 Hz Leq", "4000 Hz Leq", "8000 Hz Leq"]
#     third_octave_bands = ["25 Hz Leq", "31.5 Hz Leq", "40 Hz Leq", "50 Hz Leq", "63 Hz Leq", "80 Hz Leq", "Leq 100 Hz Leq",
#                           "125 Hz Leq", "160 Hz Leq", "200 Hz Leq", "250 Hz Leq", "315 Hz Leq", "400 Hz Leq",
#                           "500 Hz Leq", "630 Hz Leq", "800 Hz Leq", "1000 Hz Leq", "1250 Hz Leq", "1600 Hz Leq",
#                           "2000 Hz Leq", "2500 Hz Leq", "3150 Hz Leq", "4000 Hz Leq", "5000 Hz Leq", "6300 Hz Leq",
#                           "8000 Hz Leq"]
#
#     centre_freqs = []
#     if spectra == "octaves":
#         centre_freqs = octave_bands
#     elif spectra == "thirds":
#         centre_freqs = third_octave_bands
#     # Eliminate the bands before the lowest band
#     print(centre_freqs)
#     lower_bound = centre_freqs.index(lowest_band)
#     upper_bound = centre_freqs.index(highest_band)
#     centre_freqs = centre_freqs[lower_bound:upper_bound + 1]
#
#     print(centre_freqs)
#     table_header = ["Timestamp", "LAeq", "LAFmax", "LA90"]
#     print(table_header)
#     for band in centre_freqs:
#         table_header.append(band)
#     print(table_header)
#     #TODO: Fix this so that quote marks are removed from centre bands in the csv
#     with open(path, "w", newline="") as csvfile:
#         writer = csv.writer(csvfile, delimiter=" ")
#         writer.writerow(table_header)


class NoiseData:
    def __init__(self, path, meas_interval=1, night_start=23, day_start=7,
                 evening_start=None, decimals=1, thirds_to_octaves=False):
        self.decimals = decimals
        self.csv_path = path
        self.master = pd.read_csv(path, index_col="Time", parse_dates=["Time"], date_parser=lambda col: pd.to_datetime(col, dayfirst=True))
        self._assign_header()

        self.meas_interval = meas_interval
        self.antilogs = self._prep_antilogs()   # Create a copy dataframe of antilogs
        if thirds_to_octaves:
            self._convert_thirds_to_octaves()

        # Assign day, evening, night periods
        self.night_start = night_start
        self.day_start = day_start
        self.evening_start = evening_start

        # Create dataframes and slices for day, evening, nights
        self.nights = self._prep_nights()   # This is a separate dataframe
        self.days = self._prep_days()   # This is a slice of master
        self.evenings = None
        if self.evening_start is not None:
            assert self.evening_start < self.night_start
            self.evenings = self._prep_evenings()   # This is a slice of master

    def _assign_header(self):
        csv_headers = self.master.columns.to_list()
        superheaders = [item.split(" ")[0] for item in csv_headers]
        subheaders = [item.split(" ")[1] for item in csv_headers]
        self.master.columns = [superheaders, subheaders]

    def _prep_antilogs(self):
        return self.master.copy().apply(lambda x: np.power(10, (x/10)))

    # https://pandas.pydata.org/docs/user_guide/timeseries.html#indexing
    def _prep_nights(self):
        nights = self.antilogs[(self.antilogs.index.hour >= self.night_start) |
                               (self.antilogs.index.hour < self.day_start)].copy()
        nights.loc[:, ("night_dates", "night_dates")] = nights.index
        nights.loc[:, ("night_dates", "night_dates")] = nights[("night_dates", "night_dates")].apply(
            lambda x: (x - pd.tseries.offsets.DateOffset(days=1)) if x.hour < self.day_start else x)
        nights.set_index(pd.DatetimeIndex(nights[("night_dates", "night_dates")]), drop=True, inplace=True)
        nights.drop(("night_dates", "night_dates"), axis=1, inplace=True)
        return nights

    def _prep_days(self):
        return self.antilogs[(self.antilogs.index.hour >= self.day_start) |
                             (self.antilogs.index.hour < self.evening_start)]

    def _prep_evenings(self):
        return self.antilogs[(self.antilogs.index.hour >= self.evening_start) |
                             (self.antilogs.index.hour < self.night_start)]

    def _daily_leqs(self):
        night_leq = self.nights[["LAeq", "Leq"]].groupby(self.nights.index.date).mean().apply(
            lambda x: np.round((10 * np.log10(x)), self.decimals))
        day_leq = self.days[["LAeq", "Leq"]].groupby(self.days.index.date).mean().apply(
            lambda x: np.round((10 * np.log10(x)), self.decimals))
        if self.evening_start is not None:
            evening_leq = self.days[["LAeq", "Leq"]].groupby(self.evenings.index.date).mean().apply(
                lambda x: np.round((10 * np.log10(x)), self.decimals))
            return day_leq, evening_leq, night_leq
        else:
            return day_leq, night_leq

    def _convert_thirds_to_octaves(self):
        #TODO: Fix this, having introduced multiheaders

        # Initialise new dataframe
        new_df = pd.DataFrame(self.antilogs[["LAeq", "LAFmax", "LA90"]])

        # Convert Leqs
        leq_cols = self.antilogs.loc[:, self.antilogs.columns.str.contains("Leq", case=True)]
        leq_cols_list = leq_cols.columns.tolist()
        for idx in range(len(leq_cols_list)):
            if (idx + 3) % 3 == 1:
                col_name = leq_cols_list[idx]
                col_before = leq_cols_list[idx - 1]
                col_after = leq_cols_list[idx + 1]
                new_df[col_name] = self.antilogs[[col_before, col_name, col_after]].sum(axis=1)

        # Convert Lmaxes
        lmax_cols = self.antilogs.loc[:, self.antilogs.columns.str.contains("Lmax", case=True)]
        lmax_cols_list = lmax_cols.columns.tolist()
        for idx in range(len(lmax_cols_list)):
            if (idx + 3) % 3 == 1:
                col_name = lmax_cols_list[idx]
                col_before = lmax_cols_list[idx - 1]
                col_after = lmax_cols_list[idx + 1]
                new_df[col_name] = self.antilogs[[col_before, col_name, col_after]].sum(axis=1)

        # TODO: Implement for Ln spectra
        # Assign the single-octave band spectra
        self.antilogs = new_df.copy()

    def _recompute(self, t=10, ave_cols=[("LAeq", "LAeq"), ("LA90", "LA90")], max_cols=[("LAFmax", "LAFmax")]):
        resampling_string = str(t) + "min"
        recomputed = pd.DataFrame(columns=self.antilogs.columns)
        if len(ave_cols) > 0:
            for col in ave_cols:
                recomputed[col] = self.antilogs[col].resample(resampling_string).mean().\
                    apply(lambda x: np.round((10 * np.log10(x)), self.decimals))
        if len(max_cols) > 0:
            for col in max_cols:
                recomputed[col] = self.antilogs[col].resample(resampling_string).max().\
                    apply(lambda x: np.round((10 * np.log10(x)), self.decimals))
        return recomputed[ave_cols + max_cols]

    def get_leq_summary(self):
        if self.evening_start is not None:
            # Drop the lmaxes
            day, evening, night = self._daily_leqs()
            return day, evening, night
        else:
            # Drop the lmaxes
            day, night = self._daily_leqs()
            return day, night

    def get_nth_lmaxes(self, nth=10, night_only=True, sampling_period=2):
        resampling_string = str(sampling_period) + "min"
        if not night_only:
            return None    # TODO: Lmaxes for other periods
        else:
            maxes = self.nights.resample(resampling_string).max().apply(lambda x: np.round((10 * np.log10(x)), self.decimals)).dropna()   # Resample adds in missing rows. Drop them.
            maxes = maxes[(maxes.index.hour < self.day_start) |
                          (maxes.index.hour >= self.night_start)].dropna()
            nth_highest = maxes.sort_values(by=("LAFmax", "LAFmax"), ascending=False)
            nth_highest = nth_highest.groupby(by=nth_highest.index.date).nth(nth - 1)
            return nth_highest[["LAFmax", "Lmax"]]

    def lmax_histogram_by_day(self, night_only=True, sampling_period=2):
        resampling_string = str(sampling_period) + "min"
        if not night_only:
            return None # TODO: Lmax histograms for other periods
        else:
            maxes = self.nights.resample(resampling_string).max().apply(lambda x: np.round((10 * np.log10(x)), 0)).dropna()   # Resample adds in missing rows. Drop them.
            maxes = maxes[(maxes.index.hour < self.day_start) |
                          (maxes.index.hour >= self.night_start)]
            sns.set_theme(style="darkgrid")
            maxes["Day of the week"] = maxes.index.day_name()
            # sns.set(rc={"figure.figsize": (10, 10)})
            ax = sns.catplot(x="Day of the week", y=("LAFmax", "LAFmax"), data=maxes, jitter=True)
            plt.ylabel("LAFmax")
            plt.title("LAmax occurrences by day, night-time", pad=-10)
            plt.show()

    def lmax_histogram_count(self, night_only=True, sampling_period=2):
        resampling_string = str(sampling_period) + "min"
        if not night_only:
            return None # TODO: Lmax histograms for other periods
        else:
            maxes = self.nights.resample(resampling_string).max().apply(lambda x: np.round((10 * np.log10(x)), 0))
            maxes = maxes[(maxes.index.hour < self.day_start) |
                          (maxes.index.hour >= self.night_start)].dropna()   # Resample adds in missing rows. Drop them.
            sns.set_theme(style="darkgrid")
            maxes["Day of the week"] = maxes.index.day_name()
            ax = sns.histplot(x=("LAFmax", "LAFmax"), data=maxes, binwidth=1, stat="count")
            plt.xlabel("LAFmax")
            plt.title("LAmax occurrences, night-time")
            plt.show()

    def plot_time_history(self, sampling_period=15, pos_name="Position 1", img_name="timehistory", img_format=".jpg"):
        # Define the colourmap
        viridis = cm.get_cmap("plasma")
        col = iter(np.linspace(0.0, 1, 4))

        # Resample to a lower frequency for speedier computation and better presentation
        prepped_df = self._recompute(t=sampling_period)
        print("plotting....")
        sns.set_style("whitegrid")
        # pal = iter(sns.color_palette("flare", 6))
        # TODO: Sort out sizes, fonts etc.
        fig, ax1 = plt.subplots(figsize=(14, 10))
        ax1.set_facecolor("xkcd:pale grey")
        ax1.set_ylabel("Sound pressure level dB(A)")
        ax1.set_xlabel("Date")
        # TODO: implement custom colours
        ax1.plot(prepped_df.index, prepped_df[("LAeq", "LAeq")], color=viridis(next(col)), label="LAeq,T", lw=3)
        ax1.plot(prepped_df.index, prepped_df[("LA90", "LA90")], color=viridis(next(col)), label="LA90,T", lw=3)
        ax1.scatter(prepped_df.index, prepped_df[("LAFmax", "LAFmax")], s=8, color=viridis(next(col)), label="LAFmax", linewidths=3)
        ax1.legend()
        # TODO: Try this with shorter or longer surveys
        # TODO: show hours at relevant intervals
        # Configure major ticks at midnight
        major_locator = matplotlib.ticker.FixedLocator(np.unique(prepped_df.index.date))
        ax1.xaxis.set_major_formatter(
            mdates.DateFormatter("%d %b\n%r"))
        # Configure minor ticks every 6 hours
        # ax1.minorticks_on()
        # hour_locator = matplotlib.dates.HourLocator(interval=6)
        # ax1.xaxis.set_minor_locator(hour_locator)
        # Grid
        for axis in ['top', 'bottom', 'left', 'right']:
            ax1.spines[axis].set_linewidth(1.5)
            ax1.spines[axis].set_color("black")
        ax1.grid(True, which="major", lw=1.5, color="black")   # Thicker lines on major ticks
        ax1.grid(True, which="minor", axis="x", lw=0.5, color="black")     # Thinner lines on minor ticks
        print("showing....")
        plt.suptitle(pos_name)
        plt.title("Time history")
        img_pth = os.path.join(os.getcwd(), (img_name + img_format))
        fig.savefig(img_pth)
        plt.show()
        return img_pth

    def l90_histogram_count(self, day_t=60, night_t=15):
        day_resampling_string = str(day_t) + "min"
        l90 = self.antilogs.resample(day_resampling_string).mean()\
            .apply(lambda x: np.round((10 * np.log10(x)), 0)).dropna()   # Resample adds in missing rows. Drop them.
        l90 = l90[(l90.index.hour >= self.day_start) |
                      (l90.index.hour < self.night_start)]
        sns.set_theme(style="darkgrid")
        l90["Day of the week"] = l90.index.day_name()
        fig, ax = plt.subplots()
        ax = sns.histplot(x=("LA90", "LA90"), data=l90, binwidth=1, stat="count", discrete=True)
        plt.xlabel("LA90," + day_resampling_string)
        plt.title("LA90,%s, occurrences, daytime" % day_resampling_string)
        plt.show()

        night_resampling_string = str(night_t) + "min"
        l90 = self.nights.resample(night_resampling_string).mean()\
            .apply(lambda x: np.round((10 * np.log10(x)), self.decimals)).dropna()   # Resample adds in missing rows. Drop them.
        l90 = l90[(l90.index.hour < self.day_start) |
                      (l90.index.hour >= self.night_start)]
        sns.set_theme(style="darkgrid")
        l90["Day of the week"] = l90.index.day_name()
        fig, ax = plt.subplots()
        ax = sns.histplot(x=("LA90", "LA90"), data=l90, binwidth=1, stat="count", discrete=True)
        plt.xlabel("LA90," + night_resampling_string)
        plt.title("LA90,%s occurrences, night-time" % night_resampling_string)
        plt.show()

    def get_lowest_l90(self, day_t=60, night_t=15):
        # Daytime
        day_resampling_string = str(day_t) + "min"
        l90 = self.antilogs.resample(day_resampling_string).mean() \
            .apply(lambda x: np.round((10 * np.log10(x)), self.decimals))
        l90 = l90[(l90.index.hour >= self.day_start) |
                  (l90.index.hour < self.night_start)].dropna()  # Resample adds in missing rows. Drop them.
        day_lowest_l90 = l90.sort_values(by=("LA90", "LA90"), ascending=True)
        day_lowest_l90 = day_lowest_l90.groupby(by=day_lowest_l90.index.date).nth(0)

        # Night-time
        night_resampling_string = str(night_t) + "min"
        l90 = self.nights.resample(night_resampling_string).mean()\
            .apply(lambda x: np.round((10 * np.log10(x)), self.decimals)).dropna()   # Resample adds in missing rows. Drop them.
        l90 = l90[(l90.index.hour < self.day_start) |
                      (l90.index.hour >= self.night_start)]
        night_lowest_l90 = l90.sort_values(by=("LA90", "LA90"), ascending=True)
        night_lowest_l90 = night_lowest_l90.groupby(by=night_lowest_l90.index.date).nth(0)
        return day_lowest_l90[["LA90", "L90"]], night_lowest_l90[["LA90", "L90"]]
