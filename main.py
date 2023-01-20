from surveydata import *
from export import *
from weatherdata import *


if __name__ == '__main__':
    # Where is our noise survey data?
    path = r"Data.csv"
    # Create NoiseSurvey object (handles the processing of noise data)
    data = SurveyData(path, decimals=1, thirds_to_octaves=False)
    # # Weather history requires you to sign up at openweathermap.com for the One Call API
    # # Then store your API key in a text file named "openweather_appid.txt"
    weather_hist = test_weather_obj(w_dict)
    print(weather_hist)
    _, _, _, img = weather_hist.plot_time_history()

    # Create Export object (handles the conversion of noise data into MS Word format)
    report = DataExport()
    report.figure(img, 12)
    report.figure(data.plot_time_history(), 15)

    # Get N-th highest Lmax levels for each night, resampling the data where required
    print(f"Lmaxes")
    print(data.get_nth_lmaxes(nth=10, sampling_period=2))
    report.spl_table(data.get_nth_lmaxes(), "Night-time Lmax") # Add an Lmax table to the MS Word file

    # Get Daytime and Night-time Leqs and add tables to the MS Word file
    print(f"Leqs")
    print(data.get_leq_summary())
    report.spl_table(data.get_leq_summary()[0], "Daytime Leq")
    report.spl_table(data.get_leq_summary()[1], "Night-time Leq")
    report.weather_table(weather_hist.get_weather_summary(), heading="Meteorological Summary")
    report.export(path=os.getcwd())

    # # Plots
    # data.lmax_histogram_by_day()
    # data.lmax_histogram_count()
    # data.time_history_plot()
    # data.l90_histogram_count()
    #

    #
    # # Export the MS Word file
    # report.export(path=os.getcwd())
