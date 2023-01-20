import os
import requests
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

appid = ""

w_dict = {
    "start": "2022-09-16 12:00:00",
    "end": "2022-09-22 18:00:00",
    "interval": 12,
    "api_key": appid,
    "lat": 51.4780,
    "lon": 0.0015,
    "tz": "GB"
}

def test_weather_obj(weather_test_dict):
    # print(os.getcwd())
    os.chdir("..") # API key is stored in parent folder
    # print(os.path.abspath(os.curdir))
    with open("openweather_app_id.txt") as f:
        appid = f.readlines()[0]
    print(appid)
    os.chdir("NoiseSurvey")  # Change current working directory back
    w_dict["api_key"] = appid
    hist = WeatherHistory(start=w_dict["start"], end=w_dict["end"], interval=w_dict["interval"],
                          api_key=w_dict["api_key"], lat=w_dict["lat"], lon=w_dict["lon"], tz=w_dict["tz"])
    hist.compute_weather_history()
    return hist


class WeatherHistory:
    def __init__(self, start="", end="", interval=6, api_key="", lat=00.00001,
                 lon=00.0001, tz=""):
        self._start = dt.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        self._end = dt.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        self._interval = interval
        self._api_key = str(api_key)
        self._lat = str(lat)
        self._lon = str(lon)
        self._hist = None

    def _construct_api_call(self, timestamp):
        base = "https://api.openweathermap.org/data/3.0/onecall/timemachine?"
        query = str(base + "lat=" + self._lat + "&" + "lon=" + self._lon + "&" + "dt=" + str(timestamp) + "&" + "appid=" + \
              self._api_key)
        print(query)
        return query

    def _construct_timestamps(self):
        next_ts = self._start
        timestamps = []
        while next_ts < self._end:
            timestamps.append(int(next_ts.timestamp()))
            next_ts += dt.timedelta(hours=self._interval)
        return timestamps

    def _make_and_parse_api_call(self, query):
        response = requests.get(query)
        print(response.json())
        # This drops some unwanted cols like lat, lon, timezone and tz offset.
        resp_dict = response.json()["data"][0]
        del resp_dict["weather"]    # delete weather key as not useful.
        # TODO: parse 'weather' nested dict.
        return resp_dict

    def compute_weather_history(self):
        # construct timestamps
        timestamps = self._construct_timestamps()
        # make calls to API
        responses = []
        for ts in timestamps:
            print(f"ts: {ts}")
            query = self._construct_api_call(timestamp=ts)
            response_dict = self._make_and_parse_api_call(query=query)
            responses.append(pd.Series(response_dict))
        df = pd.concat(responses, axis=1).transpose()
        for col in ["dt", "sunrise", "sunset"]:
            df[col] = df[col].apply(lambda x: dt.datetime.fromtimestamp(int(x)))  # convert timestamp into datetime
        print(df)
        # Convert temp from Kelvin to Celcius
        df["temp"] = df["temp"].apply(lambda x: x - 273.15)
        self._hist = df
        return df

    def get_weather_history(self):
        return self._hist

    def plot_time_history(self, img_name="weather_hist", img_format=".jpg"):
        fig, ax1 = plt.subplots()
        ax1.set_ylabel("Temp, deg C")
        ax1.set_xlabel("Time")
        quantity1 = ax1.plot(self._hist.dt, self._hist.temp, "blue", label="Time")
        ax2 = ax1.twinx()
        ax2.set_ylabel("Wind speed, m/s")
        ax2.set_xlabel("Time")
        quantity2 = ax2.plot(self._hist.dt, self._hist.wind_speed, "green", label="Wind speed")

        # X-ticks
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=20) # rotate the xticks
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%r")) # format time to date and time
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        ax1.xaxis.set_major_locator(locator)
        ax1.xaxis.set_major_formatter(formatter)
        #TODO: spacing of X-ticks for shorter or longer surveys

        # Add legend
        quants = quantity1 + quantity2
        labels = [l.get_label() for l in quants]
        ax1.legend(quants, labels, loc=0)
        plt.title("Weather time history")
        fig.set_size_inches(9, 7)
        fig.set_dpi(100)
        img_pth = os.path.join(os.getcwd(), (img_name + img_format))
        # Save the current figure
        fig.savefig(img_pth)
        plt.show()
        return fig, ax1, ax2, img_pth

        # plt.plot(weather_hist._hist.dt, weather_hist._hist.temp)
        # plt.xticks(rotation=20)
        # plt.show()

    def get_weather_summary(self):
        max = self._hist.max()
        min = self._hist.min()
        ave = self._hist.mean()
        combi = pd.concat([min, max, ave], axis=1)
        combi = combi.round(decimals=1)
        combi = combi.rename(columns={0: "min", 1: "max", 2: "mean"})
        return combi
