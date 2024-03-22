import requests

url = "https://livescore6.p.rapidapi.com/matches/v2/list-live"

querystring = {"Category":"cricket"}

headers = {
	"X-RapidAPI-Key": "443409f4c6msh6286dfce62077e0p1ad446jsn97e9eb4f1f69",
	"X-RapidAPI-Host": "livescore6.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())