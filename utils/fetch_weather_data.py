# pobieranie danych pogodowych
import requests
def weather():
    API_KEY="a250c788440e8ba831eb94d63c218257"
    CITY = "Bukowno"
    URL  = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}"
    response = requests.get(URL)
    return response.json()
