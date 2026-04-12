import requests
import json
import random
from bs4 import BeautifulSoup

__MAX_POKEMON_ID = 1025

def scrape_pokemon(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    data= {}

    # Name
    # The “Name” appears in the header “#251 Celebi” and also “Celebi (en) – Celebi (jap)”
    # We pick the primary German name from heading
    header = soup.find("h1")
    if header:
        name = header.get_text(strip=True)
    else:
        # fallback: title
        name = soup.title.get_text(strip=True)

    data["pokedex"], data["Name"] = name.split(" ")

    eigenschaften = soup.find(string="Eigenschaften")
    table = eigenschaften.find_next().find("dl")
    
    dts, dd = table.find_all("dt"), table.find_all("dd")
    
    types = dd[0].find_all("img")
    types = [t["alt"] for t in types]
    data[dts[0].text] = types
    for i in range(1, len(dts)):
        data[dts[i].text] = dd[i].text.strip()

    fahigkeiten = soup.find(string="Fähigkeiten")
    table = fahigkeiten.find_next().find("dl")
    dts, dd = table.find_all("dt"), table.find_all("dd")
    
    for i in range(len(dts)):
        data[dts[i].text] = dd[i].text.strip()
    
    return data

if __name__ == "__main__":
    pokemon_id = random.randint(1, __MAX_POKEMON_ID)
    url = f"https://www.bisafans.de/pokedex/{pokemon_id:03}.php"
    pokemon = scrape_pokemon(url)
    write_dic = {
        "pokedex": pokemon.get("pokedex"),
        "name": pokemon.get("Name"),
        "types": ", ".join(pokemon.get("Typ")),
        "size": pokemon.get("Größe"),
        "weight": pokemon.get("Gewicht"),
        "gender": pokemon.get("Geschlecht"),
        "species": pokemon.get("Art") + "-Pokémon",
        "abilities": pokemon.get("Fähigkeit 1") + (", " + pokemon.get("Fähigkeit 2") if pokemon.get("Fähigkeit 2") != "Keine" else "") + (", " + pokemon.get("Versteckte Fähigkeit") + " (VF)" if pokemon.get("Versteckte Fähigkeit") != "Keine" else ""),
        "artwork": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pokemon_id}.png"
    }
    with open("data/pokemon.json", mode="w", encoding="utf-8") as file:
        file.write(json.dumps(write_dic, indent=4, ensure_ascii=False))
