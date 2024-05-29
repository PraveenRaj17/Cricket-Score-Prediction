import requests

url = "https://livescore6.p.rapidapi.com/matches/v2/list-live"

querystring = {"Category":"cricket"}

headers = {
	"X-RapidAPI-Key": "xxx",
	"X-RapidAPI-Host": "xxx"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
