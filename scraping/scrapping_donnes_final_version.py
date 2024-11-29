import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import datetime
import openmeteo_requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import time
import requests_cache
import pandas as pd
from retry_requests import retry
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions

import random
import json
import mysql.connector

from config_bdd import host, user, password, database


# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)


def scrapping(lat,long):
    
    def scrapping_open_meteo(lat,long):
        todays_date = datetime.today().strftime('%Y-%m-%d')
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": long,
            "start_date": "2024-01-01",
            "end_date": todays_date,
            "daily": ["sunshine_duration", "temperature_2m_max","temperature_2m_min", "precipitation_sum"]
        }
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        daily = response.Daily()
        daily_sunshine_duration= daily.Variables(0).ValuesAsNumpy()
        daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
        daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
        daily_precipitation_sum = daily.Variables(3).ValuesAsNumpy()


        daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s"),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s"),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left")}

        daily_data["sunshine_duration"] = daily_sunshine_duration
        daily_data["temperature"] = (daily_temperature_2m_max + daily_temperature_2m_min)/2
        daily_data["precipitation_sum"] = daily_precipitation_sum

        print("data Successfully collected from {} to {}".format(params["start_date"], todays_date))
        
        daily_data
        return(daily_data)

    def scrapping_irradiance(lat, long):
        # Path to geckodriver (ensure geckodriver is installed and accessible)
        geckodriver_path = r"scripts final\geckodriver.exe"
        firefox_service = FirefoxService(geckodriver_path)
        
        # Setting Firefox options (headless for running without opening browser window)
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        # Initialize the Firefox driver
        driver = webdriver.Firefox(service=firefox_service, options=firefox_options)
        driver.get(f"https://globalsolaratlas.info/detail?m=site&s={lat},{long}")
        time.sleep(random.randint(5, 8))
        
        # Get the page content
        content = driver.page_source
        soup = bs(content, "lxml")
        driver.quit()
        
        # Scraping the irradiance data
        try:
            irradiance_per_year = soup.find("div", class_="col-auto site-data__unit-value ng-star-inserted").find("sg-unit-value-inner").get_text()
        except:
            print("Data not collected")
            return None

        # Convert the irradiance to daily value
        irradiance = float(irradiance_per_year) / 365
        return irradiance


    data_dict=scrapping_open_meteo(lat,long)
    irradiance=scrapping_irradiance(lat,long)




    # Create a list to store JSON entries for each date
    json_list = []
    db = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    charset="utf8"  # Définir l'encodage en UTF-8
    )
    with db.cursor() as c:
        try: 
            c.execute("SELECT idpoint FROM 2026_solarx_pointsgps WHERE latitude LIKE %s AND longitude LIKE %s", (lat, long,))
        except:
           db = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset="utf8"  # Définir l'encodage en UTF-8
            )
           c.execute("SELECT idpoint FROM 2026_solarx_pointsgps WHERE latitude LIKE %s AND longitude LIKE %s", (lat, long,))
        id_point = c.fetchone()[0]

    db.close()
    # Iterate over the dates and create JSON entries
    for i in range(len(data_dict['date'])):
        
        if not pd.isna(data_dict['temperature'][i]) :
            temp=float(data_dict['temperature'][i])
        else :
            temp=None
        
        if not pd.isna((data_dict['sunshine_duration'][i])):
            ensoleillement=float(data_dict['sunshine_duration'][i])
        else :
            temp=None

        if not pd.isna(float(data_dict['precipitation_sum'][i])) :
            precipitation=float(data_dict['precipitation_sum'][i])
        else :
            temp=None
        
        json_entry = {
        
                    "temperature": temp  ,
                    "ensoleillement": ensoleillement,
                    "irradiance": float(irradiance),
                    "precipitation": precipitation,
                    "date_collecte": str(data_dict['date'][i]),
                    "idpoint":id_point
        }
        json_list.append(json_entry)
        json_dict={"mesures":json_list}
    print("données météo converties en JSON")
    return json_dict
    
