#!/usr/bin/python3
import requests
import datetime
from dataclasses import dataclass
from typing import List
import rich
import rich.columns as richcol
import rich.console as richcon
import sys


def exists(obj, index):
    return (not (obj == None or obj == [] or obj == {} or obj == ())) and len(obj) > index


class Direction2D:
    """
    A 2D Direction. can be a
    - vector
    - angle in rad
    - angle in deg
    """

    def __init__(self, angle = None, degrees = True, x1 = None, x2 = None):
        if angle:
            # first convert to radians, then use trigonometry
            self.rad = angle
            if degrees:
                self.rad = (self.rad / 360) * 2 * (22/7) # (22/7) approx pi
            # TODO
            self.x1 = 0 # Realwert von e^{i*rad)
            self.x2 = 0 # Imaginärwert von e^{i*rad}
        else:
            self.x1 = x1
            self.x2 = x2

    def as_vector(self):
        return [x1, x2]

    def as_rad(self):
        # TODO: do fancy trigonometry
        angle = None
        return angle

    def as_deg(self):
        return (as_rad()/(2*(22/7)))*360 # siehe __init__

@dataclass
class Position2D:
    """
    A position in a 2D coordinate system.
    """
    x1: float = 0.0
    x2: float = 0.0



@dataclass
class ForecastPoint:
    """
    A point in time that is associated with specific forecast values.
    """

    timestamp: datetime.datetime

    temperature: float = None
    temperature_min: float = None
    temperature_max: float = None
    precipitation: float = None
    precipitation_probability: float = None
    wind_speed: float = None
    wind_direction: Direction2D = None
    wind_gust: float = None
    air_pressure: float = None
    air_humidity: float = None
    dew_point: float = None
    sunshine: float = None
    uv_index: float = None
    cloud_coverage: float = None

    def summary(self):
        string = str(self.timestamp.time())+" Uhr:\n"
        string += "Temp.:\t"+str(self.temperature)+" °C\n"
        string += "Regen:\t"+str(self.precipitation)+" mm\n"
        string += "Sonne:\t"+str(self.sunshine.total_seconds()/60)+" min\n"
        string += "Wind:\t"+str(self.wind_speed)+" km/h\n"

        return string

    def day_summary(self):
        string = "[bold green]"+str(self.timestamp.date().isoformat())+"[/]:\n"
        string += "Temp. min: [bold blue]"+str(self.temperature_min)+" °C[/]\n"
        string += "Temp. max: [bold red]"+str(self.temperature_max)+" °C[/]\n"
        #string += "Regen:     [bold rgb("+str(255-self.precipitation*4)+","+str(255-self.precipitation*4)+", 255)]"+str(self.precipitation)+" mm[/]\n"
        string += "Regen:     [bold rgb(0, 0, 255)]"+str(self.precipitation)+" mm[/]\n"
        string += "Sonne:     [bold yellow]"+str(self.sunshine.total_seconds()/60)+" min[/]\n"
        string += "Wind:      [bold white]"+str(self.wind_speed)+" km/h[/]\n"

        return string
        


class WeatherProvider:
    """
    Interface that describes a weather provider.
    """

    name: str
    short_name: str
    website: str
    stations: list

    fc_api_url: str
    station_api_url: str


    @staticmethod
    def get_station_data(station) -> list:
        pass

    def get_stations():
        pass

    def get_station_by_name(self, keyword: str):
        # returns the first exact match
        found_stations = []
        for station in self.stations:
            if keyword in station.name or keyword in station.code:
                found_stations.append(station)
        return found_stations



class DWD(WeatherProvider):
    """
    Represents the German national weather service DWD.
    """

    name = "Deutscher Wetterdienst"
    short_name = "DWD"
    website = "dwd.de"
    stations = list()
    fc_api_url = "https://dwd.api.proxy.bund.dev/v30/stationOverviewExtended?stationIds="
    station_api_url = "https://www.dwd.de/DE/leistungen/klimadatendeutschland/statliste/statlex_rich.txt?view=nasPublication"


    @staticmethod
    def get_stations():
        raw_data = requests.get(DWD.station_api_url)
        raw_data.encoding = 'ISO-8859-1'
        if not raw_data.status_code == 200:
            raise IOError
        raw_data = raw_data.text
        raw_data = raw_data.split('\r\n')[3:-1]
        raw_data = [line.split() for line in raw_data]
        #raw_data = list(filter(lambda station: station[2] == "MN", raw_data))
        station_code_map = {}
        for raw_station in raw_data:
            station = WeatherStation(name=raw_station[0],
                              code=raw_station[3],
                              provider=DWD(),
                              position=Position2D(raw_station[5], raw_station[4])
                              )
            if not station_code_map.get(station.code):
                DWD.stations.append(station)
                station_code_map[station.code] = True


    @staticmethod
    def get_station_data(station) -> list:
        # DWD: only automatic stations work (MN)
        raw_data = requests.get(DWD.fc_api_url+station.code).json()
        if not raw_data:
            raise FileNotFoundError("Station is not supported")
        raw_data = raw_data[station.code]
        daily = DWD.get_day_forecast(data=raw_data['days'], station=station)
        three_hourly = DWD.get_list_forecast(data=raw_data['forecast2'], station=station)
        one_hourly = DWD.get_list_forecast(data=raw_data['forecast1'], station=station)
        return [daily, three_hourly, one_hourly]

    @staticmethod
    def get_day_forecast(data: list, station):
        time_offset = datetime.datetime.today() # hope that's fine
        time_resolution = datetime.timedelta(days=1)

        fc = Forecast(station, time_resolution, time_offset)

        for day in data:
            point = ForecastPoint(
                    timestamp = datetime.datetime.fromisoformat(day['dayDate']),
                    temperature = round((float(day['temperatureMax'])/10 + float(day['temperatureMin'])/10)/2, 1),
                    temperature_min = float(day['temperatureMin'])/10,
                    temperature_max = float(day['temperatureMax'])/10,
                    precipitation = float(day['precipitation'])/10,# I hope that /10 is right
                    wind_speed = float(day['windSpeed'])/10,
                    wind_direction = Direction2D(angle=float(day['windDirection'])/10, degrees=True),
                    wind_gust = float(day['windGust'])/10,
                    sunshine = datetime.timedelta(minutes=float(day['sunshine'])/10)
                    )

            fc.append(point)

        return fc

    @staticmethod
    def get_list_forecast(data: dict, station):
        time_offset = datetime.datetime.fromtimestamp(data['start']/1000)
        time_resolution = datetime.timedelta(seconds=data['timeStep']/1000)

        fc = Forecast(station, time_resolution, time_offset)

        for index in range(0, len(data['sunshine'])-1):# any other list should work
            point = ForecastPoint(
                    timestamp = time_offset + index * time_resolution,# hope, arithmetic works with datetime
                    dew_point = float(data['dewPoint2m'][index])/10 if exists(data['dewPoint2m'], index) else None, # data['dewPoint2m'] may be None
                    air_humidity = float(data['humidity'][index])/10 if exists(data['humidity'], index) else None,
                    precipitation  = float(data['precipitationTotal'][index])/10 if exists(data['precipitationTotal'], index) else None, # I hope that /10 is right
                    sunshine = datetime.timedelta(minutes=float(data['sunshine'][index])/10) if exists(data['sunshine'], index) else None,
                    air_pressure = float(data['surfacePressure'][index])/10 if exists(data['surfacePressure'], index) else None,
                    temperature = float(data['temperature'][index])/10 if exists(data['temperature'], index) else None,
                    wind_direction = Direction2D(angle=float(data['windDirection'][index])/10, degrees=True) if exists(data['windDirection'], index) else None,
                    wind_speed = float(data['windSpeed'][index])/10 if exists(data['windSpeed'], index) else None,
                    wind_gust = float(data['windGust'][index])/10 if exists(data['windGust'], index) else None,
                    )
            fc.append(point)
        return fc


        





@dataclass
class WeatherStation:
    """
    Describes a weather station.

    DWD: only automatic stations work (MN)
    """

    name: str
    code: str
    provider: WeatherProvider
    position: Position2D
    notes: str = ""

    def get_forecasts(self) -> list:
        return self.provider.get_station_data(self)

    def rich_summary(self):
        string = "[bold green]"+self.name + "[/]\nCode: [bold red]" + self.code + "[/]\nProvider: " + self.provider.short_name + "\n"
        return string


    

class Forecast(list):

    def __init__(self, station, time_resolution, time_offset):
        super().__init__()
        self.station = station
        self.time_resolution = time_resolution
        self.time_offset = time_offset


    def append(self, point: ForecastPoint):
        """
        Insert in a sorted manner, not at the end.
        """
        #if len(self) == 0:
        #    self.insert(0, point)
        greater_than_index = 0
        while greater_than_index < len(self) and point.timestamp > self[greater_than_index].timestamp:
            greater_than_index += 1
        self.insert(greater_than_index+1, point)


    def insert(self, index: int, point: ForecastPoint):
        """
        Just makes life easier.
        """
        if index >= len(self):
            super().append(point)
        #elif index < len(self):
        else:
            super().insert(index, point)
        #else:
        #    raise IndexError("Index is out of bounds.")

    def rich_summary(self):
        summaries = [point.summary() for point in self]
        cols = richcol.Columns(summaries, equal=True, expand=True)
        return cols

    def day_rich_summary(self):
        summaries = [point.day_summary() for point in self]
        cols = richcol.Columns(summaries, equal=True, expand=True)
        return cols


# Testing functions:
# ==================


def example_fc():
    station_id = "L886"
    station = WeatherStation(name = "Darmstadt", code = station_id, provider = DWD(), position = Position2D(x1 = 8.41, x2=49.53))
    forecasts = station.get_forecasts()
    summaries = [fc.rich_summary() for fc in forecasts]
    console = richcon.Console()
    console.print("Vorhersage für "+station.name+":", style="bold")
    console.print(forecasts[0].day_rich_summary())

def list_dwd_stations():
    DWD.get_stations()
    station_summ = [station.rich_summary() for station in DWD.stations]
    cols = richcol.Columns(station_summ, equal=True, expand=True)
    console = richcon.Console()
    console.print(cols)

def forecast(station_name):
    console = richcon.Console()
    try:
        DWD.get_stations()
    except IOError:
        console.print("[bold white on red]Error: Station list could not be loaded. Try again.[/]")
        return
    stations = DWD().get_station_by_name(station_name)

    failed_stations = []
    if not stations:
        console.print("[bold white on red]Error: Station not found.[/]")
        return
    for station in stations:
        try:
            forecasts = station.get_forecasts()
            console.print("Vorhersage für "+station.name+" ("+station.code+"):", style="bold")
            console.print(forecasts[0].day_rich_summary())
        except FileNotFoundError: # when the API returns {}
            failed_stations.append(station)
    if failed_stations:
        console.print("[bold white on red]These Stations were not shown, because they are not supported:[/]")
        #f_st_string = ""
        #[f_st_string = f_st_string+station.name+" ("+station.code+"), " for station in failed_stations]
        console.print(", ".join([station.name+" ("+station.code+")" for station in failed_stations]))


def help_message():
    console = richcon.Console()
    console.print("""[bold]cliweather.py[/] COMMAND [STATION NAME]
[bold]COMMANDS[/]\tlist\t\tLists all available stations.
\t\tstation\t\tShows a forecast for a station, requires STATION NAME.""")


if __name__ == "__main__":
    args = sys.argv
    if len(args) == 1:
        help_message()
    elif args[1] == "list":
        list_dwd_stations()
    elif args[1] == "station":
        forecast(args[2])
    else:
        help_message()






