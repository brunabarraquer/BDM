import requests

url = "https://movies-tv-shows-database.p.rapidapi.com/"

querystring = {"movieid":"tt1375666"}

headers = {
	"x-rapidapi-key": "3a882cd6f9mshef33335c57b457dp157e81jsn7b9cf44c6af4",
	"x-rapidapi-host": "movies-tv-shows-database.p.rapidapi.com",
	"Type": "get-movies-images-by-imdb"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())