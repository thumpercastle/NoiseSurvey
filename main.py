from noisedata import *
from export import *
from weatherdata import *
from Survey import *


if __name__ == '__main__':
    # Where is our noise survey data?
    path1 = r"Pos1_Parsed.csv"
    path2 = r"Pos2_Parsed.csv"
    # Create NoiseSurvey object (handles the processing of noise data)
    data1 = NoiseData(path1, decimals=1, thirds_to_octaves=False)
    data2 = NoiseData(path2, decimals=1, thirds_to_octaves=False)
    survey = Survey(data={"Pos 1": data1, "Pos 2": data2})
    day, night = survey.get_leq_summary()
    lmax = survey.get_nth_lmaxes()
    day, night = survey.get_lowest_l90()

    # # Weather history requires you to sign up at openweathermap.com for the One Call API
    # # Then store your API key in a text file named "openweather_appid.txt"
    weather_hist = test_weather_obj(w_dict)
    print(weather_hist)
    _, _, _, img = weather_hist.plot_time_history()
    # #
    # # # Create Export object (handles the conversion of noise data into MS Word format)
    report = DataExport()
    report.figure(img, 12)
    report.figure(data1.plot_time_history(), 15)
    # #
    # # # Get N-th highest Lmax levels for each night, resampling the data where required
    report.spl_table(survey.get_nth_lmaxes(dba_only=False, decimals=0), "Night-time Lmax") # Add an Lmax table to the MS Word file
    # #
    # # # Get Daytime and Night-time Leqs and add tables to the MS Word file

    report.spl_table(survey.get_leq_summary(dba_only=False, decimals=0)[0], "Daytime Leq")
    report.spl_table(survey.get_leq_summary(dba_only=False, decimals=0)[1], "Night-time Leq")
    report.weather_table(weather_hist.get_weather_summary(), heading="Meteorological Summary")
    report.export(path=os.getcwd())

    # # Plots
    data1.lmax_histogram_by_day()
    data1.lmax_histogram_count()
    data1.plot_time_history()
    data1.l90_histogram_count()

    #

    #
    # # Export the MS Word file
    report.export(path=os.getcwd())
