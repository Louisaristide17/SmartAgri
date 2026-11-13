"""
Route météo — Sources de données réelles (sans clé API requise) :
  1. Open-Meteo API (gratuite, sans clé) — météo actuelle + prévisions 7 jours
  2. OpenWeatherMap (si clé configurée dans .env) — fallback de qualité
  3. Données agronomiques enrichies selon la saison ivoirienne

Open-Meteo : https://open-meteo.com/ (licence libre)
"""
from fastapi import APIRouter, HTTPException
import os, httpx, random, math
from asyncio import gather as asyncio_gather
from datetime import date, timedelta

router = APIRouter(prefix="/api/meteo", tags=["Météo"])

OWM_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ─── Coordonnées GPS des villes de Côte d'Ivoire ─────────────────
VILLES_COORDS = {
    # Capitales et grandes villes
    "abidjan":       {"lat":  5.3600, "lon":  -4.0083, "nom": "Abidjan"},
    "yamoussoukro":  {"lat":  6.8276, "lon":  -5.2893, "nom": "Yamoussoukro"},
    "bouaké":        {"lat":  7.6906, "lon":  -5.0301, "nom": "Bouaké"},
    "bouake":        {"lat":  7.6906, "lon":  -5.0301, "nom": "Bouaké"},
    "daloa":         {"lat":  6.8774, "lon":  -6.4502, "nom": "Daloa"},
    "san-pédro":     {"lat":  4.7485, "lon":  -6.6363, "nom": "San-Pédro"},
    "san-pedro":     {"lat":  4.7485, "lon":  -6.6363, "nom": "San-Pédro"},
    "korhogo":       {"lat":  9.4580, "lon":  -5.6290, "nom": "Korhogo"},
    "man":           {"lat":  7.4125, "lon":  -7.5537, "nom": "Man"},
    "gagnoa":        {"lat":  6.1319, "lon":  -5.9503, "nom": "Gagnoa"},
    # Villes agricoles importantes
    "abengourou":    {"lat":  6.7297, "lon":  -3.4965, "nom": "Abengourou"},
    "bondoukou":     {"lat":  8.0400, "lon":  -2.7968, "nom": "Bondoukou"},
    "divo":          {"lat":  5.8374, "lon":  -5.3573, "nom": "Divo"},
    "issia":         {"lat":  6.4829, "lon":  -6.5851, "nom": "Issia"},
    "mankono":       {"lat":  8.0588, "lon":  -6.1891, "nom": "Mankono"},
    "odienné":       {"lat":  9.5046, "lon":  -7.5604, "nom": "Odienné"},
    "odiénné":       {"lat":  9.5046, "lon":  -7.5604, "nom": "Odienné"},
    "odienne":       {"lat":  9.5046, "lon":  -7.5604, "nom": "Odienné"},
    "soubré":        {"lat":  5.7864, "lon":  -6.5965, "nom": "Soubré"},
    "soubre":        {"lat":  5.7864, "lon":  -6.5965, "nom": "Soubré"},
    "tabou":         {"lat":  4.4229, "lon":  -7.3581, "nom": "Tabou"},
    "tingréla":      {"lat": 10.4745, "lon":  -6.3989, "nom": "Tingréla"},
    "touba":         {"lat":  8.2833, "lon":  -7.6833, "nom": "Touba (CI)"},
}

# ─── Codes WMO → description + icône OWM ─────────────────────────
WMO_CODES = {
    0:  ("Ciel dégagé",           "01d"),
    1:  ("Principalement dégagé", "01d"),
    2:  ("Partiellement nuageux", "02d"),
    3:  ("Couvert",               "04d"),
    45: ("Brouillard",            "50d"),
    48: ("Brouillard givrant",    "50d"),
    51: ("Bruine légère",         "09d"),
    53: ("Bruine modérée",        "09d"),
    55: ("Bruine dense",          "09d"),
    61: ("Pluie légère",          "10d"),
    63: ("Pluie modérée",         "10d"),
    65: ("Pluie forte",           "10d"),
    71: ("Neige légère",          "13d"),
    73: ("Neige modérée",         "13d"),
    75: ("Neige forte",           "13d"),
    80: ("Averses légères",       "09d"),
    81: ("Averses modérées",      "09d"),
    82: ("Averses violentes",     "09d"),
    95: ("Orage",                 "11d"),
    96: ("Orage avec grêle",      "11d"),
    99: ("Orage fort avec grêle", "11d"),
}


def wmo_to_info(code: int):
    return WMO_CODES.get(code, ("Variable", "02d"))


async def geocode_ville(ville: str) -> dict | None:
    """Récupère les coordonnées GPS d'une ville via Nominatim (OpenStreetMap)."""
    try:
        async with httpx.AsyncClient(timeout=5,
            headers={"User-Agent": "SmartAgri/1.0 (agro-app)"}) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": ville, "countrycodes": "ci", "format": "json", "limit": 1}
            )
        if resp.status_code == 200:
            results = resp.json()
            if results:
                return {
                    "lat": float(results[0]["lat"]),
                    "lon": float(results[0]["lon"]),
                    "nom": results[0].get("display_name", ville).split(",")[0].strip()
                }
    except Exception:
        pass
    return None


async def get_coords(ville: str) -> dict:
    """Résout les coordonnées GPS d'une ville (cache local → geocoding)."""
    key = ville.lower().strip()

    # 1. Dictionnaire local
    if key in VILLES_COORDS:
        return VILLES_COORDS[key]

    # 2. Geocoding Nominatim
    coords = await geocode_ville(ville)
    if coords:
        return coords

    # 3. Fallback : Abidjan
    return VILLES_COORDS["abidjan"]


async def fetch_open_meteo_current(lat: float, lon: float) -> dict:
    """
    Interroge Open-Meteo pour la météo actuelle.
    Variables : temperature, humidité, pression, vent, code météo.
    """
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":  lat,
                "longitude": lon,
                "current": ",".join([
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "weather_code",
                    "surface_pressure",
                    "wind_speed_10m",
                    "wind_gusts_10m",
                ]),
                "timezone": "Africa/Abidjan",
            }
        )
    resp.raise_for_status()
    return resp.json()


async def fetch_open_meteo_forecast(lat: float, lon: float) -> dict:
    """
    Interroge Open-Meteo pour les prévisions 7 jours.
    Variables journalières : temp max/min, précipitations, code météo.
    """
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":  lat,
                "longitude": lon,
                "daily": ",".join([
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                    "et0_fao_evapotranspiration",
                ]),
                "timezone":  "Africa/Abidjan",
                "forecast_days": 7,
            }
        )
    resp.raise_for_status()
    return resp.json()


# ─── Route météo actuelle ─────────────────────────────────────────
@router.get("/{ville}", summary="Météo actuelle d'une ville (Open-Meteo)")
async def get_meteo(ville: str):
    coords = await get_coords(ville)
    lat, lon, nom_ville = coords["lat"], coords["lon"], coords.get("nom", ville.capitalize())

    # ── Essai 1 : Open-Meteo (sans clé, toujours disponible) ────
    try:
        data = await fetch_open_meteo_current(lat, lon)
        cur  = data["current"]
        code = cur.get("weather_code", 0)
        desc, icon = wmo_to_info(code)

        return {
            "ville":             nom_ville,
            "temperature":       round(cur["temperature_2m"], 1),
            "ressenti":          round(cur["apparent_temperature"], 1),
            "humidite":          cur["relative_humidity_2m"],
            "description":       desc,
            "icone":             icon,
            "vent":              round(cur["wind_speed_10m"], 1),   # déjà en km/h
            "rafales":           round(cur.get("wind_gusts_10m", cur["wind_speed_10m"]), 1),
            "pression":          round(cur["surface_pressure"]),
            "precipitations":    round(cur.get("precipitation", 0), 1),
            "latitude":          lat,
            "longitude":         lon,
            "source":            "Open-Meteo (temps réel)",
        }
    except Exception as e_om:
        pass  # Fallback OWM

    # ── Essai 2 : OpenWeatherMap si clé disponible ───────────────
    if OWM_KEY:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={"lat": lat, "lon": lon, "appid": OWM_KEY,
                            "units": "metric", "lang": "fr"}
                )
            if resp.status_code == 200:
                d = resp.json()
                return {
                    "ville":          d["name"],
                    "temperature":    round(d["main"]["temp"], 1),
                    "ressenti":       round(d["main"]["feels_like"], 1),
                    "humidite":       d["main"]["humidity"],
                    "description":    d["weather"][0]["description"].capitalize(),
                    "icone":          d["weather"][0]["icon"],
                    "vent":           round(d["wind"]["speed"] * 3.6, 1),
                    "rafales":        round(d["wind"].get("gust", d["wind"]["speed"]) * 3.6, 1),
                    "pression":       d["main"]["pressure"],
                    "precipitations": d.get("rain", {}).get("1h", 0),
                    "latitude":       lat,
                    "longitude":      lon,
                    "source":         "OpenWeatherMap",
                }
        except Exception:
            pass

    # ── Fallback : données saison réaliste Côte d'Ivoire ─────────
    mois = date.today().month
    # CI : grande saison des pluies (mars-juil), petite saison (sept-nov)
    est_pluies = (3 <= mois <= 7) or (9 <= mois <= 11)
    # Zone forestière (Abidjan, Daloa) vs savane (Korhogo, Bouaké)
    temp  = round(random.uniform(25, 32) if est_pluies else random.uniform(28, 36), 1)
    pluie = round(random.uniform(5, 30) if est_pluies else random.uniform(0, 5), 1)
    hum   = random.randint(70, 92) if est_pluies else random.randint(35, 60)

    return {
        "ville":          nom_ville,
        "temperature":    temp,
        "ressenti":       round(temp + random.uniform(-2, 2), 1),
        "humidite":       hum,
        "description":    "Données estimées (saison ivoirienne)",
        "icone":          "10d" if est_pluies else "01d",
        "vent":           random.randint(8, 20),
        "rafales":        random.randint(15, 30),
        "pression":       random.randint(1008, 1016),
        "precipitations": pluie,
        "latitude":       lat,
        "longitude":      lon,
        "source":         "Estimation saisonnière",
    }


# ─── Route prévisions 7 jours ─────────────────────────────────────
@router.get("/{ville}/previsions", summary="Prévisions 7 jours (Open-Meteo)")
async def get_previsions(ville: str):
    coords = await get_coords(ville)
    lat, lon, nom_ville = coords["lat"], coords["lon"], coords.get("nom", ville.capitalize())

    JOURS_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

    # ── Open-Meteo prévisions ────────────────────────────────────
    try:
        data = await fetch_open_meteo_forecast(lat, lon)
        daily = data["daily"]
        previsions = []

        for i, d in enumerate(daily["time"]):
            jour_date = date.fromisoformat(d)
            delta = (jour_date - date.today()).days
            if delta == 0:   label = "Aujourd'hui"
            elif delta == 1: label = "Demain"
            else:            label = JOURS_FR[jour_date.weekday()]

            code = daily["weather_code"][i]
            desc, icon = wmo_to_info(code)
            temp_max = round(daily["temperature_2m_max"][i], 1)
            temp_min = round(daily["temperature_2m_min"][i], 1)
            temp_moy = round((temp_max + temp_min) / 2, 1)
            pluie    = round(daily["precipitation_sum"][i], 1)
            prob     = daily.get("precipitation_probability_max", [0]*7)[i]
            vent_max = round(daily.get("wind_speed_10m_max", [10]*7)[i], 1)
            etp      = round(daily.get("et0_fao_evapotranspiration", [5]*7)[i], 1)

            previsions.append({
                "label":       label,
                "date":        d,
                "temp":        temp_moy,
                "temp_max":    temp_max,
                "temp_min":    temp_min,
                "pluie":       pluie,
                "prob_pluie":  prob,
                "vent_max":    vent_max,
                "icone":       icon,
                "description": desc,
                "etp":         etp,      # évapotranspiration (mm) — utile pour l'irrigation
            })

        # Total pluie 7 jours — utile pour la prédiction de rendement
        total_pluie_7j = sum(p["pluie"] for p in previsions)
        pluie_mensuelle_estimee = round(total_pluie_7j * 4.3, 1)  # projection mensuelle

        return {
            "ville":                    nom_ville,
            "latitude":                 lat,
            "longitude":                lon,
            "previsions":               previsions,
            "total_pluie_7j":           round(total_pluie_7j, 1),
            "pluie_mensuelle_estimee":  pluie_mensuelle_estimee,
            "source":                   "Open-Meteo (temps réel)",
        }
    except Exception:
        pass

    # ── Fallback saisonnier Côte d'Ivoire ────────────────────────
    mois = date.today().month
    est_pluies = (3 <= mois <= 7) or (9 <= mois <= 11)
    previsions = []
    total_pluie = 0

    for i in range(7):
        jour_date = date.today() + timedelta(days=i)
        delta = i
        if delta == 0:   label = "Aujourd'hui"
        elif delta == 1: label = "Demain"
        else:            label = JOURS_FR[jour_date.weekday()]

        temp_max = round(random.uniform(28, 34) if est_pluies else random.uniform(30, 38), 1)
        temp_min = round(temp_max - random.uniform(5, 9), 1)
        pluie    = round(random.uniform(10, 40) if est_pluies else random.uniform(0, 3), 1)
        total_pluie += pluie

        previsions.append({
            "label":       label,
            "date":        str(jour_date),
            "temp":        round((temp_max + temp_min) / 2, 1),
            "temp_max":    temp_max,
            "temp_min":    temp_min,
            "pluie":       pluie,
            "prob_pluie":  random.randint(50, 90) if est_pluies else random.randint(0, 15),
            "vent_max":    round(random.uniform(8, 22), 1),
            "icone":       "10d" if (est_pluies and pluie > 8) else "01d",
            "description": "Estimation saisonnière",
            "etp":         round(random.uniform(4, 7), 1),
        })

    return {
        "ville":                   nom_ville,
        "latitude":                lat,
        "longitude":               lon,
        "previsions":              previsions,
        "total_pluie_7j":          round(total_pluie, 1),
        "pluie_mensuelle_estimee": round(total_pluie * 4.3, 1),
        "source":                  "Estimation saisonnière",
    }


# ─── Route météo agronomique pour la prédiction ──────────────────
@router.get("/{ville}/agro", summary="Données météo agronomiques pour la prédiction")
async def get_meteo_agro(ville: str):
    """
    Retourne les paramètres météo optimisés pour alimenter le modèle de prédiction :
    - pluviométrie mensuelle estimée (mm)
    - température moyenne (°C)
    - humidité relative (%)
    - ETP journalière (mm) — besoin en irrigation
    """
    coords = await get_coords(ville)
    lat, lon, nom_ville = coords["lat"], coords["lon"], coords.get("nom", ville.capitalize())

    try:
        current_data, forecast_data = await asyncio_gather(
            fetch_open_meteo_current(lat, lon),
            fetch_open_meteo_forecast(lat, lon)
        )
        cur   = current_data["current"]
        daily = forecast_data["daily"]

        temp_moy  = round(sum(
            (mx + mn) / 2
            for mx, mn in zip(daily["temperature_2m_max"], daily["temperature_2m_min"])
        ) / len(daily["time"]), 1)
        pluie_7j  = sum(daily["precipitation_sum"])
        pluie_mois = round(pluie_7j * 4.3, 1)
        etp_moy   = round(sum(daily.get("et0_fao_evapotranspiration", [5]*7)) / 7, 1)

        return {
            "ville":              nom_ville,
            "temperature_moy":    temp_moy,
            "humidite":           cur["relative_humidity_2m"],
            "pluviometrie_mois":  pluie_mois,
            "pluviometrie_7j":    round(pluie_7j, 1),
            "etp_journaliere":    etp_moy,
            "source":             "Open-Meteo (temps réel)",
        }
    except Exception:
        mois = date.today().month
        est_p = (3 <= mois <= 7) or (9 <= mois <= 11)
        return {
            "ville":             nom_ville,
            "temperature_moy":   27.0 if est_p else 31.0,
            "humidite":          80   if est_p else 45,
            "pluviometrie_mois": 180.0 if est_p else 20.0,
            "pluviometrie_7j":   42.0  if est_p else 5.0,
            "etp_journaliere":   5.0,
            "source":            "Estimation saisonnière",
        }
