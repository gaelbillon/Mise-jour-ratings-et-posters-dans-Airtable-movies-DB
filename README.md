# Mise-jour-ratings-et-posters-dans-Airtable-movies-DB
&nbsp;&nbsp;
&nbsp;&nbsp;
&nbsp;&nbsp;
## Usage 
&nbsp;&nbsp;
### Prérequis
```bash
python3 -m venv venv && source venv/bin/activate
pip install requests python-dotenv
```
&nbsp;&nbsp;
### Éxecution
```bash
python sync_omdb_airtable.py
```
&nbsp;&nbsp;
&nbsp;&nbsp;
&nbsp;&nbsp;  
## Airtable movie database template utilisé 
[Movies & TV Log and Ratings](https://www.airtable.com/universe/expuPJXnpcp20qEMs/movies-and-tv-log-and-ratings) (à customiser pour colonnes "Année" et "Rating", noms et/ou format)

&nbsp;&nbsp;
&nbsp;&nbsp;
&nbsp;&nbsp;

## Prompt LLM utilisé pour générer le code Python

Crée un script Python qui lit des informations à l'aide de l'API OMDB et les écrit dans une base de données Airtable contenant une liste de films. 

- Clé d'API OMDB : xxxxxxxx
- Personal accès token Airtable : patxxxxxxxxxx
- Nombre de lignes à traiter : 423 
- Limiter le nombre de reqûetes API à : 10 req/s 
- Si OMDB ne trouve rien : laisser vide
- Si un film a déjà un rating/poster : écraser
- Format de rating : imdbRating	

- Noms et formats des champs Airtable à utiliser pour la recherche OMDB :
	* Airtable "Title" -> Single line text
	* Airtable "Année" -> Number

- Noms et formats des champs OMDB à lire dans le JSON retourné par l'API :
	* "Released"
	* "imdbID"
	* "Poster"
	* "imdbRating"
	* "Director"

- Noms et formats des champs Airtable à écrire : 
	* Nom : "Rating", format : Number
	* Nom : "Poster", format : "Attachment"
	* Nom : "Director", format : Single line text
	* Nom : "Movie release date", format : Date
	* Nom : "IMDB Link", format : URL

- Fields mapping OMDB -> Airtable :
	* "imdbRating" -> "Rating"
	* "Poster" -> "Poster"
	* "Director" -> "Director"
	* "Released" -> "Movie release date"
	* "imdbID" -> "IMDB Link"
&nbsp;&nbsp;
&nbsp;&nbsp;
&nbsp;&nbsp; 
 ## Sample JSON pour savoir quels champs sont dispos via OMDB
```json
{
  "Title": "Her",
  "Year": "2013",
  "Rated": "R",
  "Released": "10 Jan 2014",
  "Runtime": "126 min",
  "Genre": "Drama, Romance, Sci-Fi",
  "Director": "Spike Jonze",
  "Writer": "Spike Jonze",
  "Actors": "Joaquin Phoenix, Amy Adams, Scarlett Johansson",
  "Plot": "In the near future, a lonely writer develops an unlikely relationship with an operating system designed to meet his every need.",
  "Language": "English",
  "Country": "United States",
  "Awards": "Won 1 Oscar. 83 wins & 187 nominations total",
  "Poster": "https://m.media-amazon.com/images/M/MV5BMjA1Nzk0OTM2OF5BMl5BanBnXkFtZTgwNjU2NjEwMDE@._V1_SX300.jpg",
  "Ratings": [
    {
      "Source": "Internet Movie Database",
      "Value": "8.0/10"
    },
    {
      "Source": "Rotten Tomatoes",
      "Value": "95%"
    },
    {
      "Source": "Metacritic",
      "Value": "91/100"
    }
  ],
  "Metascore": "91",
  "imdbRating": "8.0",
  "imdbVotes": "704,150",
  "imdbID": "tt1798709",
  "Type": "movie",
  "DVD": "N/A",
  "BoxOffice": "$25,568,251",
  "Production": "N/A",
  "Website": "N/A",
  "Response": "True"
}
```
