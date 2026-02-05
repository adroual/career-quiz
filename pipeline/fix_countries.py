#!/usr/bin/env python3
"""
Fix missing country_code and country_flag in career_entries table.
Matches club names to countries and updates Supabase.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tjxdbdueayzlxgywigth.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Expanded club -> country mapping
CLUB_COUNTRIES = {
    # ENGLAND (EN)
    "Arsenal": "EN", "Chelsea": "EN", "Liverpool": "EN", "Manchester United": "EN",
    "Manchester City": "EN", "Tottenham": "EN", "Tottenham Hotspur": "EN", "Everton": "EN",
    "Newcastle United": "EN", "Newcastle": "EN", "Aston Villa": "EN", "West Ham": "EN",
    "West Ham United": "EN", "Leeds United": "EN", "Leeds": "EN", "Southampton": "EN",
    "Leicester City": "EN", "Leicester": "EN", "Crystal Palace": "EN", "Wolverhampton": "EN",
    "Wolves": "EN", "Brighton": "EN", "Brighton & Hove Albion": "EN", "Burnley": "EN",
    "Sheffield United": "EN", "Fulham": "EN", "Brentford": "EN", "Nottingham Forest": "EN",
    "Bournemouth": "EN", "AFC Bournemouth": "EN", "Watford": "EN", "Norwich City": "EN",
    "Norwich": "EN", "Sunderland": "EN", "Middlesbrough": "EN", "West Bromwich": "EN",
    "West Brom": "EN", "Blackburn": "EN", "Blackburn Rovers": "EN", "Bolton": "EN",
    "Bolton Wanderers": "EN", "Stoke City": "EN", "Stoke": "EN", "Swansea": "EN",
    "Swansea City": "EN", "Hull City": "EN", "Hull": "EN", "Reading": "EN",
    "Wigan": "EN", "Wigan Athletic": "EN", "Birmingham City": "EN", "Birmingham": "EN",
    "Derby County": "EN", "Derby": "EN", "QPR": "EN", "Queens Park Rangers": "EN",
    "Charlton": "EN", "Charlton Athletic": "EN", "Portsmouth": "EN", "Ipswich": "EN",
    "Ipswich Town": "EN", "Coventry": "EN", "Coventry City": "EN", "Sheffield Wednesday": "EN",
    "Blackpool": "EN", "Wimbledon": "EN", "MK Dons": "EN", "Oldham": "EN",
    "Barnsley": "EN", "Bradford City": "EN", "Luton Town": "EN", "Luton": "EN",
    "Millwall": "EN", "Preston": "EN", "Preston North End": "EN", "Crewe Alexandra": "EN",
    "Crewe": "EN", "Barnet": "EN", "Bristol City": "EN", "Cardiff City": "EN",
    "Huddersfield": "EN", "Huddersfield Town": "EN", "Rotherham": "EN",
    # Additional English lower league clubs
    "Accrington Stanley": "EN", "Accrington": "EN", "Burton Albion": "EN", "Burton": "EN",
    "Carlisle United": "EN", "Carlisle": "EN", "Barrow": "EN", "Barrow AFC": "EN",
    "Colchester United": "EN", "Colchester": "EN", "Crawley Town": "EN", "Crawley": "EN",
    "Doncaster Rovers": "EN", "Doncaster": "EN", "Exeter City": "EN", "Exeter": "EN",
    "Fleetwood Town": "EN", "Fleetwood": "EN", "Forest Green Rovers": "EN", "Forest Green": "EN",
    "Gillingham": "EN", "Grimsby Town": "EN", "Grimsby": "EN", "Harrogate Town": "EN",
    "Hartlepool United": "EN", "Hartlepool": "EN", "Leyton Orient": "EN", "Orient": "EN",
    "Lincoln City": "EN", "Lincoln": "EN", "Mansfield Town": "EN", "Mansfield": "EN",
    "Morecambe": "EN", "Northampton Town": "EN", "Northampton": "EN",
    "Oxford United": "EN", "Oxford": "EN", "Peterborough United": "EN", "Peterborough": "EN",
    "Plymouth Argyle": "EN", "Plymouth": "EN", "Port Vale": "EN", "Rochdale": "EN",
    "Salford City": "EN", "Salford": "EN", "Scunthorpe United": "EN", "Scunthorpe": "EN",
    "Shrewsbury Town": "EN", "Shrewsbury": "EN", "Stevenage": "EN", "Stockport County": "EN",
    "Stockport": "EN", "Swindon Town": "EN", "Swindon": "EN", "Tranmere Rovers": "EN",
    "Tranmere": "EN", "Walsall": "EN", "Wycombe Wanderers": "EN", "Wycombe": "EN",
    "Yeovil Town": "EN", "Yeovil": "EN", "AFC Wimbledon": "EN", "Bristol Rovers": "EN",
    "Cambridge United": "EN", "Cambridge": "EN", "Cheltenham Town": "EN", "Cheltenham": "EN",
    "Chesterfield": "EN", "Macclesfield Town": "EN", "Macclesfield": "EN",
    "Notts County": "EN", "Oldham Athletic": "EN", "Southend United": "EN", "Southend": "EN",
    "Sutton United": "EN", "Sutton": "EN", "Wrexham AFC": "EN", "York City": "EN", "York": "EN",
    "Dagenham & Redbridge": "EN", "Dagenham": "EN", "Darlington": "EN", "Darlington FC": "EN",
    "Aldershot Town": "EN", "Aldershot": "EN", "Boreham Wood": "EN", "Bromley": "EN",
    "Dover Athletic": "EN", "Dover": "EN", "Eastleigh": "EN", "Ebbsfleet United": "EN",
    "Gateshead": "EN", "Halifax Town": "EN", "Halifax": "EN", "Maidenhead United": "EN",
    "Solihull Moors": "EN", "Solihull": "EN", "Torquay United": "EN", "Torquay": "EN",
    "Wealdstone": "EN", "Woking": "EN", "Hereford": "EN", "Hereford United": "EN",
    "Kidderminster Harriers": "EN", "Kidderminster": "EN", "Boston United": "EN", "Boston": "EN",
    "Farnborough": "EN", "Farnborough Town": "EN", "Rushden & Diamonds": "EN",
    "Kettering Town": "EN", "Kettering": "EN", "Nuneaton Borough": "EN", "Nuneaton": "EN",
    "Stafford Rangers": "EN", "Stafford": "EN", "Tamworth": "EN", "Tamworth FC": "EN",
    "Telford United": "EN", "Telford": "EN", "Worcester City": "EN", "Worcester": "EN",
    "Weymouth": "EN", "Weymouth FC": "EN", "Altrincham": "EN", "Altrincham FC": "EN",
    "Chester": "EN", "Chester FC": "EN", "Southport": "EN", "Southport FC": "EN",
    "Cowdenbeath": "EN", "Fylde": "EN", "AFC Fylde": "EN", "King's Lynn Town": "EN",
    "Chesterfield FC": "EN", "Eastbourne Borough": "EN",

    # SPAIN (ES)
    "Real Madrid": "ES", "Barcelona": "ES", "FC Barcelona": "ES", "Atlético Madrid": "ES",
    "Atletico Madrid": "ES", "Atlético de Madrid": "ES", "Sevilla": "ES", "Valencia": "ES",
    "Villarreal": "ES", "Real Sociedad": "ES", "Athletic Bilbao": "ES", "Athletic Club": "ES",
    "Real Betis": "ES", "Betis": "ES", "Celta Vigo": "ES", "Celta": "ES",
    "Espanyol": "ES", "RCD Espanyol": "ES", "Getafe": "ES", "Osasuna": "ES",
    "Mallorca": "ES", "RCD Mallorca": "ES", "Real Valladolid": "ES", "Valladolid": "ES",
    "Granada": "ES", "Levante": "ES", "Alavés": "ES", "Deportivo Alavés": "ES",
    "Eibar": "ES", "Leganés": "ES", "Rayo Vallecano": "ES", "Cádiz": "ES",
    "Elche": "ES", "Almería": "ES", "Real Zaragoza": "ES", "Zaragoza": "ES",
    "Deportivo La Coruña": "ES", "Deportivo": "ES", "Racing Santander": "ES",
    "Sporting Gijón": "ES", "Las Palmas": "ES", "Tenerife": "ES", "Hércules": "ES",
    "Recreativo": "ES", "Numancia": "ES", "Albacete": "ES", "Salamanca": "ES",
    "Real Oviedo": "ES", "Oviedo": "ES", "Girona": "ES",

    # ITALY (IT)
    "Juventus": "IT", "AC Milan": "IT", "Milan": "IT", "Inter Milan": "IT", "Inter": "IT",
    "Internazionale": "IT", "Roma": "IT", "AS Roma": "IT", "Napoli": "IT", "SSC Napoli": "IT",
    "Lazio": "IT", "SS Lazio": "IT", "Fiorentina": "IT", "ACF Fiorentina": "IT",
    "Atalanta": "IT", "Torino": "IT", "Sampdoria": "IT", "Bologna": "IT",
    "Udinese": "IT", "Sassuolo": "IT", "Verona": "IT", "Hellas Verona": "IT",
    "Cagliari": "IT", "Genoa": "IT", "Parma": "IT", "Empoli": "IT",
    "Spezia": "IT", "Salernitana": "IT", "Lecce": "IT", "Monza": "IT",
    "Frosinone": "IT", "Cremonese": "IT", "Brescia": "IT", "SPAL": "IT",
    "Chievo": "IT", "Chievo Verona": "IT", "Palermo": "IT", "Catania": "IT",
    "Siena": "IT", "Livorno": "IT", "Reggina": "IT", "Bari": "IT",
    "Pescara": "IT", "Novara": "IT", "Cesena": "IT", "Modena": "IT",
    "Perugia": "IT", "Piacenza": "IT", "Vicenza": "IT", "Venezia": "IT",
    "Ascoli": "IT", "Ancona": "IT", "Reggiana": "IT", "Benevento": "IT",
    "Crotone": "IT", "Carpi": "IT", "Como": "IT",
    # Additional Italian clubs
    "Arezzo": "IT", "US Arezzo": "IT", "Avellino": "IT", "US Avellino": "IT",
    "Ternana": "IT", "Ternana Calcio": "IT", "Cittadella": "IT", "AS Cittadella": "IT",
    "Pisa": "IT", "AC Pisa": "IT", "Padova": "IT", "Calcio Padova": "IT",
    "Triestina": "IT", "US Triestina": "IT", "Pro Vercelli": "IT", "Virtus Entella": "IT",
    "Trapani": "IT", "Trapani Calcio": "IT", "Foggia": "IT", "US Foggia": "IT",
    "Cosenza": "IT", "Cosenza Calcio": "IT", "Juve Stabia": "IT", "SS Juve Stabia": "IT",
    "Pordenone": "IT", "Pordenone Calcio": "IT", "Virtus Lanciano": "IT",
    "Varese": "IT", "AS Varese": "IT", "Grosseto": "IT", "US Grosseto": "IT",
    "Mantova": "IT", "Mantova FC": "IT", "Rimini": "IT", "AC Rimini": "IT",
    "Pro Patria": "IT", "Aurora Pro Patria": "IT", "AlbinoLeffe": "IT",
    "Treviso": "IT", "Treviso FBC": "IT", "Messina": "IT", "ACR Messina": "IT",
    "Latina": "IT", "US Latina": "IT", "Virtus Verona": "IT", "Südtirol": "IT",
    "FC Südtirol": "IT", "Alto Adige": "IT", "Feralpisalò": "IT",
    "Pergolettese": "IT", "US Pergolettese": "IT", "Alessandria": "IT", "US Alessandria": "IT",
    "Pro Sesto": "IT", "Renate": "IT", "AC Renate": "IT", "Giana Erminio": "IT",
    "Seregno": "IT", "Fidelis Andria": "IT", "Turris": "IT", "SS Turris": "IT",
    "Paganese": "IT", "Paganese Calcio": "IT", "Potenza": "IT", "Potenza Calcio": "IT",
    "Catanzaro": "IT", "US Catanzaro": "IT", "Vibonese": "IT", "US Vibonese": "IT",
    "Cavese": "IT", "Cavese 1919": "IT", "Casertana": "IT", "Casertana FC": "IT",
    "Virtus Francavilla": "IT", "Monopoli": "IT", "SS Monopoli": "IT",
    "Taranto": "IT", "Taranto FC": "IT", "Picerno": "IT", "AZ Picerno": "IT",
    "Reggina 1914": "IT", "US Reggina": "IT", "Acireale": "IT", "Siracusa": "IT",
    "Juventus Next Gen": "IT", "Juventus U23": "IT", "Milan Primavera": "IT",
    "Inter Primavera": "IT", "Atalanta U23": "IT",
    # More Italian lower leagues
    "Bellaria Igea": "IT", "Bellaria Igea Marina": "IT", "Calcio Desenzano": "IT",
    "Desenzano Calvina": "IT", "Pro Sesto": "IT", "AC Pro Sesto": "IT",
    "Fano": "IT", "Alma Juventus Fano": "IT", "Gubbio": "IT", "AS Gubbio": "IT",
    "Imolese": "IT", "Imolese Calcio": "IT", "Ravenna": "IT", "Ravenna FC": "IT",
    "Sanremese": "IT", "Sanremese Calcio": "IT", "Lucchese": "IT", "AS Lucchese": "IT",
    "Pistoiese": "IT", "US Pistoiese": "IT", "Pontedera": "IT", "US Pontedera": "IT",
    "Siena 1904": "IT", "Robur Siena": "IT", "Viterbese": "IT", "US Viterbese": "IT",
    "Rieti": "IT", "FC Rieti": "IT", "Teramo": "IT", "SS Teramo": "IT",
    "Fermana": "IT", "Fermana FC": "IT", "Vis Pesaro": "IT", "Sambenedettese": "IT",
    "Matelica": "IT", "SS Matelica": "IT",

    # GERMANY (DE)
    "Bayern Munich": "DE", "Bayern München": "DE", "Bayern": "DE", "Borussia Dortmund": "DE",
    "Dortmund": "DE", "BVB": "DE", "Bayer Leverkusen": "DE", "Leverkusen": "DE",
    "RB Leipzig": "DE", "Leipzig": "DE", "Schalke 04": "DE", "Schalke": "DE",
    "Wolfsburg": "DE", "VfL Wolfsburg": "DE", "Eintracht Frankfurt": "DE", "Frankfurt": "DE",
    "Borussia Mönchengladbach": "DE", "Mönchengladbach": "DE", "Gladbach": "DE",
    "Hoffenheim": "DE", "TSG Hoffenheim": "DE", "Werder Bremen": "DE", "Bremen": "DE",
    "Hertha BSC": "DE", "Hertha Berlin": "DE", "Hertha": "DE", "Union Berlin": "DE",
    "Freiburg": "DE", "SC Freiburg": "DE", "Mainz": "DE", "Mainz 05": "DE",
    "Augsburg": "DE", "FC Augsburg": "DE", "Köln": "DE", "1. FC Köln": "DE", "Cologne": "DE",
    "Stuttgart": "DE", "VfB Stuttgart": "DE", "Hamburger SV": "DE", "Hamburg": "DE", "HSV": "DE",
    "Hannover 96": "DE", "Hannover": "DE", "Nürnberg": "DE", "1. FC Nürnberg": "DE",
    "Düsseldorf": "DE", "Fortuna Düsseldorf": "DE", "Paderborn": "DE", "Bielefeld": "DE",
    "Arminia Bielefeld": "DE", "Bochum": "DE", "VfL Bochum": "DE", "Darmstadt": "DE",
    "Heidenheim": "DE", "Greuther Fürth": "DE", "Fürth": "DE", "Kaiserslautern": "DE",
    "1. FC Kaiserslautern": "DE", "Duisburg": "DE", "MSV Duisburg": "DE",
    "Karlsruher SC": "DE", "Karlsruhe": "DE", "St. Pauli": "DE", "FC St. Pauli": "DE",
    "Energie Cottbus": "DE", "Cottbus": "DE", "Aachen": "DE", "Alemannia Aachen": "DE",
    "Mönchengladbach": "DE",
    # Additional German clubs
    "1860 Munich": "DE", "TSV 1860 Munich": "DE", "1860 München": "DE",
    "1. FC Magdeburg": "DE", "Magdeburg": "DE", "1. FC Saarbrücken": "DE", "Saarbrücken": "DE",
    "1. FC Schweinfurt 05": "DE", "Schweinfurt": "DE", "1. FC Pforzheim": "DE",
    "1. FC Eibelstadt": "DE", "1. SC Feucht": "DE", "1. SC Göttingen 05": "DE",
    "SpVgg Unterhaching": "DE", "Unterhaching": "DE", "SpVgg Greuther Fürth": "DE",
    "SpVgg Bayreuth": "DE", "Bayreuth": "DE", "SpVgg Fürth": "DE",
    "TSV Havelse": "DE", "Havelse": "DE", "TSV Hartberg": "DE",
    "VfB Oldenburg": "DE", "Oldenburg": "DE", "VfB Leipzig": "DE",
    "VfL Osnabrück": "DE", "Osnabrück": "DE", "VfR Mannheim": "DE", "Mannheim": "DE",
    "Rot-Weiss Essen": "DE", "RW Essen": "DE", "Rot-Weiß Erfurt": "DE", "Erfurt": "DE",
    "Rot-Weiß Oberhausen": "DE", "Oberhausen": "DE", "Alemannia Klein-Auheim": "DE",
    "ASC Schöppingen": "DE", "Eintracht Braunschweig": "DE", "Braunschweig": "DE",
    "Kickers Offenbach": "DE", "Offenbach": "DE", "SV Sandhausen": "DE", "Sandhausen": "DE",
    "Holstein Kiel": "DE", "Kiel": "DE", "Hansa Rostock": "DE", "Rostock": "DE",
    "Dynamo Dresden": "DE", "Dresden": "DE", "Erzgebirge Aue": "DE", "Aue": "DE",
    "Jahn Regensburg": "DE", "Regensburg": "DE", "Wehen Wiesbaden": "DE", "Wiesbaden": "DE",
    "Preußen Münster": "DE", "Münster": "DE", "SV Meppen": "DE", "Meppen": "DE",
    "VfB Lübeck": "DE", "Lübeck": "DE", "Eintracht Trier": "DE", "Trier": "DE",
    "Waldhof Mannheim": "DE", "SV Waldhof": "DE", "Türkgücü München": "DE",
    "Bayern Munich II": "DE", "Bayern München II": "DE", "Borussia Dortmund II": "DE",
    "1860 Munich II": "DE", "Schalke 04 II": "DE", "VfB Stuttgart II": "DE",
    "Elversberg": "DE", "SV Elversberg": "DE", "Viktoria Köln": "DE",
    "SC Verl": "DE", "Verl": "DE", "Würzburger Kickers": "DE", "Würzburg": "DE",
    "SSV Ulm 1846": "DE", "Ulm": "DE", "FC Ingolstadt": "DE", "Ingolstadt": "DE",
    "SV Wacker Burghausen": "DE", "Burghausen": "DE", "FC Homburg": "DE", "Homburg": "DE",
    "SV Darmstadt 98": "DE", "Darmstadt 98": "DE", "Stuttgarter Kickers": "DE",
    "Sportfreunde Siegen": "DE", "Siegen": "DE", "Borussia Neunkirchen": "DE",
    "Carl Zeiss Jena": "DE", "Jena": "DE", "FC Saarbrücken": "DE",
    "Tennis Borussia Berlin": "DE", "Tasmania Berlin": "DE", "Blau-Weiß Berlin": "DE",
    "Wuppertaler SV": "DE", "Wuppertal": "DE", "Bonner SC": "DE", "Bonn": "DE",
    "Viktoria Berlin": "DE", "Berliner FC Dynamo": "DE", "BFC Dynamo": "DE",
    "1. FC Union Berlin": "DE", "1. FC Lokomotive Leipzig": "DE", "Lok Leipzig": "DE",
    "Chemnitzer FC": "DE", "Chemnitz": "DE", "FC Rot-Weiß Erfurt": "DE",
    "FSV Zwickau": "DE", "Zwickau": "DE", "Hallescher FC": "DE", "Halle": "DE",
    "VfB Auerbach": "DE", "FC Bayern Hof": "DE", "Hof": "DE",
    "SV Babelsberg 03": "DE", "Babelsberg": "DE", "FC Viktoria 1889 Berlin": "DE",
    "SC Paderborn 07": "DE", "FC Gütersloh": "DE", "Gütersloh": "DE",
    "Fortuna Köln": "DE", "Bayer 04 Leverkusen": "DE", "Bayer Leverkusen II": "DE",
    "Borussia Mönchengladbach II": "DE", "Werder Bremen II": "DE", "Hamburger SV II": "DE",
    "Eintracht Frankfurt II": "DE", "1. FC Köln II": "DE", "Hertha BSC II": "DE",
    # More German clubs
    "Bayer Uerdingen": "DE", "KFC Uerdingen": "DE", "Uerdingen": "DE",
    "Borussia Fulda": "DE", "Fulda": "DE", "BSG Chemie Böhlen": "DE", "Chemie Böhlen": "DE",
    "BV Burscheid": "DE", "Burscheid": "DE", "Berliner AK 07": "DE", "BAK 07": "DE",
    "Büchen-Siebeneichener SV": "DE", "SG Wattenscheid 09": "DE", "Wattenscheid": "DE",
    "VfR Aalen": "DE", "Aalen": "DE", "SV Rödinghausen": "DE", "Rödinghausen": "DE",
    "TuS Koblenz": "DE", "Koblenz": "DE", "SV Eintracht Trier": "DE",
    "SSV Reutlingen 05": "DE", "Reutlingen": "DE", "SV Stuttgarter Kickers": "DE",
    "VfB Eppingen": "DE", "VfR Heilbronn": "DE", "SSV Jeddeloh": "DE",
    "VfB Hilden": "DE", "Hilden": "DE", "Sportfreunde Lotte": "DE", "Lotte": "DE",
    "SC Wiedenbrück": "DE", "Wiedenbrück": "DE", "Wormatia Worms": "DE", "Worms": "DE",
    "FC Gütersloh 2000": "DE", "SV Lippstadt 08": "DE", "Lippstadt": "DE",
    "Rot-Weiß Ahlen": "DE", "Ahlen": "DE", "Sonnenhof Großaspach": "DE", "Großaspach": "DE",
    "1. FC Lokomotive Leipzig": "DE", "Lok Leipzig": "DE", "VfL Halle 96": "DE",
    "SV Babelsberg": "DE", "FC Carl Zeiss Jena": "DE",
    # Even more German lower league clubs
    "1. FC Kleve": "DE", "FC Kleve": "DE", "BV Lüttringhausen": "DE", "Lüttringhausen": "DE",
    "Eintracht Northeim": "DE", "Northeim": "DE", "FC Amberg": "DE", "Amberg": "DE",
    "FC Anker Wismar": "DE", "Anker Wismar": "DE", "FC Nieder-Wöllstadt": "DE",
    "FC Nöttingen": "DE", "Nöttingen": "DE", "FC Remscheid": "DE", "Remscheid": "DE",
    "EFC Stahl": "DE", "Stahl Eisenhüttenstadt": "DE", "FC Teutonia 05": "DE",
    "Wegberg-Beeck": "DE", "FC Wegberg-Beeck": "DE", "SpVgg Erkenschwick": "DE",
    "TV Emsdetten": "DE", "Emsdetten": "DE", "Kickers Emden": "DE", "Emden": "DE",
    "BSV Rehden": "DE", "Rehden": "DE", "SV Wilhelmshaven": "DE", "Wilhelmshaven": "DE",
    "Concordia Hamburg": "DE", "SC Weiche Flensburg 08": "DE", "Flensburg": "DE",
    "Ratingen": "DE", "Ratingen 04/19": "DE", "Cronenberger SC": "DE",
    "SV Straelen": "DE", "Straelen": "DE", "1. FC Bocholt": "DE", "Bocholt": "DE",
    "VfB Homberg": "DE", "Homberg": "DE", "Schwarz-Weiß Essen": "DE",
    "ETB Schwarz-Weiß Essen": "DE", "TuRU Düsseldorf": "DE", "TuRU": "DE",
    "TSV Steinbach Haiger": "DE", "Steinbach Haiger": "DE", "FC Gießen": "DE", "Gießen": "DE",
    # More German amateur clubs
    "Borussia Freialdenhoven": "DE", "Freialdenhoven": "DE", "FC 08 Villingen": "DE",
    "FC Singen 04": "DE", "Singen": "DE", "FSV Bad Windsheim": "DE", "Bad Windsheim": "DE",
    "FV 07 Ebingen": "DE", "Ebingen": "DE", "FV Bad Honnef": "DE", "Bad Honnef": "DE",
    "FV Biebrich 02": "DE", "Biebrich": "DE", "FV Ravensburg": "DE", "Ravensburg": "DE",
    "FV Weinheim": "DE", "Weinheim": "DE", "FV Zuffenhausen": "DE", "Zuffenhausen": "DE",
    "GSV Maichingen": "DE", "Maichingen": "DE", "1. FC Nuremberg II": "DE", "Nürnberg II": "DE",
    "Erzgebirge Aue II": "DE", "Aue II": "DE",

    # FRANCE (FR)
    "Paris Saint-Germain": "FR", "PSG": "FR", "Marseille": "FR", "Olympique de Marseille": "FR",
    "OM": "FR", "Lyon": "FR", "Olympique Lyonnais": "FR", "OL": "FR", "Monaco": "FR",
    "AS Monaco": "FR", "Lille": "FR", "LOSC": "FR", "LOSC Lille": "FR", "Rennes": "FR",
    "Stade Rennais": "FR", "Nice": "FR", "OGC Nice": "FR", "Lens": "FR", "RC Lens": "FR",
    "Nantes": "FR", "FC Nantes": "FR", "Montpellier": "FR", "Montpellier HSC": "FR",
    "Strasbourg": "FR", "RC Strasbourg": "FR", "Bordeaux": "FR", "Girondins de Bordeaux": "FR",
    "Girondins": "FR", "Saint-Étienne": "FR", "AS Saint-Étienne": "FR", "ASSE": "FR",
    "Toulouse": "FR", "Toulouse FC": "FR", "Reims": "FR", "Stade de Reims": "FR",
    "Brest": "FR", "Stade Brestois": "FR", "Angers": "FR", "Angers SCO": "FR",
    "Metz": "FR", "FC Metz": "FR", "Lorient": "FR", "FC Lorient": "FR",
    "Clermont": "FR", "Clermont Foot": "FR", "Troyes": "FR", "Auxerre": "FR",
    "AJ Auxerre": "FR", "Nîmes": "FR", "Nîmes Olympique": "FR", "Dijon": "FR",
    "Amiens": "FR", "Amiens SC": "FR", "Caen": "FR", "SM Caen": "FR",
    "Guingamp": "FR", "EA Guingamp": "FR", "Le Havre": "FR", "Le Havre AC": "FR",
    "Bastia": "FR", "SC Bastia": "FR", "Nancy": "FR", "AS Nancy": "FR",
    "Sochaux": "FR", "FC Sochaux": "FR", "Valenciennes": "FR", "Le Mans": "FR",
    "Ajaccio": "FR", "AC Ajaccio": "FR", "Sedan": "FR", "AS Cannes": "FR", "Cannes": "FR",

    # PORTUGAL (PT)
    "Benfica": "PT", "SL Benfica": "PT", "Porto": "PT", "FC Porto": "PT",
    "Sporting CP": "PT", "Sporting Lisbon": "PT", "Sporting": "PT", "Braga": "PT",
    "SC Braga": "PT", "Vitória Guimarães": "PT", "Guimarães": "PT", "Boavista": "PT",
    "Marítimo": "PT", "Rio Ave": "PT", "Famalicão": "PT", "Gil Vicente": "PT",
    "Paços de Ferreira": "PT", "Santa Clara": "PT", "Moreirense": "PT", "Tondela": "PT",
    "Portimonense": "PT", "Belenenses": "PT", "Estoril": "PT", "Setúbal": "PT",
    "Nacional": "PT", "Arouca": "PT", "Vizela": "PT", "Casa Pia": "PT",

    # NETHERLANDS (NL)
    "Ajax": "NL", "AFC Ajax": "NL", "PSV Eindhoven": "NL", "PSV": "NL", "Feyenoord": "NL",
    "AZ Alkmaar": "NL", "AZ": "NL", "Twente": "NL", "FC Twente": "NL", "Utrecht": "NL",
    "FC Utrecht": "NL", "Vitesse": "NL", "Heerenveen": "NL", "SC Heerenveen": "NL",
    "Groningen": "NL", "FC Groningen": "NL", "Sparta Rotterdam": "NL", "Sparta": "NL",
    "Heracles": "NL", "Heracles Almelo": "NL", "Willem II": "NL", "Fortuna Sittard": "NL",
    "NEC Nijmegen": "NL", "NEC": "NL", "Cambuur": "NL", "SC Cambuur": "NL",
    "Go Ahead Eagles": "NL", "Excelsior": "NL", "Emmen": "NL", "FC Emmen": "NL",
    "Volendam": "NL", "FC Volendam": "NL", "Waalwijk": "NL", "RKC Waalwijk": "NL",
    "Zwolle": "NL", "PEC Zwolle": "NL", "Roda JC": "NL", "Roda": "NL",
    "NAC Breda": "NL", "NAC": "NL", "Den Haag": "NL", "ADO Den Haag": "NL",
    # Additional Dutch clubs
    "AGOVV": "NL", "AGOVV Apeldoorn": "NL", "De Graafschap": "NL", "Almere City": "NL",
    "Almere City FC": "NL", "FC Dordrecht": "NL", "Dordrecht": "NL", "MVV Maastricht": "NL",
    "MVV": "NL", "FC Oss": "NL", "TOP Oss": "NL", "Jong Ajax": "NL", "Ajax II": "NL",
    "Jong PSV": "NL", "PSV II": "NL", "Jong AZ": "NL", "AZ II": "NL",
    "Jong Utrecht": "NL", "FC Den Bosch": "NL", "Den Bosch": "NL", "Helmond Sport": "NL",
    "FC Eindhoven": "NL", "Eindhoven": "NL", "Telstar": "NL", "SC Telstar": "NL",
    "VVV-Venlo": "NL", "VVV Venlo": "NL", "Venlo": "NL", "FC Wageningen": "NL",
    "Veendam": "NL", "SC Veendam": "NL", "BV Veendam": "NL", "HFC Haarlem": "NL",
    "Haarlem": "NL", "DOS Utrecht": "NL", "Elinkwijk": "NL", "DWS Amsterdam": "NL",
    "Blauw-Wit Amsterdam": "NL", "SVV Schiedam": "NL", "Xerxes": "NL",

    # BELGIUM (BE)
    "Anderlecht": "BE", "RSC Anderlecht": "BE", "Club Brugge": "BE", "Brugge": "BE",
    "Standard Liège": "BE", "Standard": "BE", "Genk": "BE", "KRC Genk": "BE",
    "Gent": "BE", "KAA Gent": "BE", "Antwerp": "BE", "Royal Antwerp": "BE",
    "Mechelen": "BE", "KV Mechelen": "BE", "Charleroi": "BE", "Sporting Charleroi": "BE",
    "Cercle Brugge": "BE", "Sint-Truiden": "BE", "STVV": "BE", "Union Saint-Gilloise": "BE",
    "Oostende": "BE", "KV Oostende": "BE", "Kortrijk": "BE", "KV Kortrijk": "BE",
    "Eupen": "BE", "KAS Eupen": "BE", "Westerlo": "BE", "Leuven": "BE", "OH Leuven": "BE",
    "Waregem": "BE", "Zulte Waregem": "BE", "Lokeren": "BE", "Mouscron": "BE",
    "Beerschot": "BE", "Beveren": "BE", "Lierse": "BE",
    "Berchem Sport": "BE", "K Berchem Sport": "BE", "RWDM": "BE", "RWD Molenbeek": "BE",
    "Lommel": "BE", "Lommel SK": "BE", "Roeselare": "BE", "KSV Roeselare": "BE",
    "Tubize": "BE", "Virton": "BE", "Royal Excelsior Virton": "BE", "Seraing": "BE",
    "RFC Seraing": "BE", "RFC Liège": "BE", "Dender": "BE", "FCV Dender EH": "BE",

    # SCOTLAND (SC)
    "Celtic": "SC", "Rangers": "SC", "Aberdeen": "SC", "Hearts": "SC",
    "Heart of Midlothian": "SC", "Hibernian": "SC", "Hibs": "SC", "Dundee United": "SC",
    "Dundee": "SC", "Motherwell": "SC", "Kilmarnock": "SC", "St Johnstone": "SC",
    "Livingston": "SC", "Ross County": "SC", "St Mirren": "SC",
    "Cowdenbeath": "SC", "Partick Thistle": "SC", "Partick": "SC", "Queen of the South": "SC",
    "Falkirk": "SC", "Inverness CT": "SC", "Inverness": "SC", "Raith Rovers": "SC",
    "Airdrieonians": "SC", "Airdrie": "SC", "Arbroath": "SC", "Greenock Morton": "SC",
    "Morton": "SC", "Dunfermline": "SC", "Dunfermline Athletic": "SC",
    "Hamilton Academical": "SC", "Hamilton": "SC", "Alloa Athletic": "SC", "Alloa": "SC",
    "Queen's Park": "SC", "Queens Park": "SC", "East Fife": "SC", "Stenhousemuir": "SC",
    "Stranraer": "SC", "Ayr United": "SC", "Ayr": "SC", "Clydebank": "SC",

    # TURKEY (TR)
    "Galatasaray": "TR", "Fenerbahçe": "TR", "Fenerbahce": "TR", "Beşiktaş": "TR",
    "Besiktas": "TR", "Trabzonspor": "TR", "Başakşehir": "TR", "Istanbul Basaksehir": "TR",
    "Kasımpaşa": "TR", "Kasimpasa": "TR", "Sivasspor": "TR", "Antalyaspor": "TR",
    "Konyaspor": "TR", "Alanyaspor": "TR", "Rizespor": "TR", "Gaziantep": "TR",
    "Hatayspor": "TR", "Adana Demirspor": "TR", "Kayserispor": "TR", "Ankaragücü": "TR",
    "Göztepe": "TR", "Genclerbirligi": "TR", "Bursaspor": "TR", "Eskişehirspor": "TR",
    "Akhisar": "TR", "Malatyaspor": "TR",
    # Additional Turkish clubs
    "Adanaspor": "TR", "Altay": "TR", "Altay SK": "TR", "Giresunspor": "TR",
    "Samsunspor": "TR", "Denizlispor": "TR", "Gaziantepspor": "TR", "Karagümrük": "TR",
    "Fatih Karagümrük": "TR", "Yeni Malatyaspor": "TR", "Pendikspor": "TR",
    "Istanbulspor": "TR", "Ümraniyespor": "TR", "Eyüpspor": "TR", "Sakaryaspor": "TR",
    "Kocaelispor": "TR", "Boluspor": "TR", "Erzurumspor": "TR", "BB Erzurumspor": "TR",
    "Gençlerbirliği": "TR", "Ankaragücü": "TR", "MKE Ankaragücü": "TR",
    "Ankara Keçiörengücü": "TR", "Keçiörengücü": "TR", "Manisaspor": "TR",
    "Bandırmaspor": "TR", "Tuzlaspor": "TR", "Altınordu": "TR", "Altinordu": "TR",
    "Menemenspor": "TR", "Balıkesirspor": "TR", "Afyonspor": "TR", "Afjet Afyonspor": "TR",
    "Elazığspor": "TR", "Elazigspor": "TR", "Diyarbakırspor": "TR", "Diyarbakirspor": "TR",
    "Mersin İdman Yurdu": "TR", "Orduspor": "TR", "Bucaspor": "TR",
    "Karşıyaka": "TR", "Karsiyaka": "TR", "Kardemir Karabükspor": "TR", "Karabükspor": "TR",
    "Çaykur Rizespor": "TR", "Akhisarspor": "TR", "Akhisar Belediyespor": "TR",
    "Ankaraspor": "TR", "Osmanlıspor": "TR", "Osmanlispor": "TR",

    # RUSSIA (RU)
    "Spartak Moscow": "RU", "CSKA Moscow": "RU", "Zenit": "RU", "Zenit St. Petersburg": "RU",
    "Lokomotiv Moscow": "RU", "Dynamo Moscow": "RU", "Rubin Kazan": "RU", "Kazan": "RU",
    "Krasnodar": "RU", "FC Krasnodar": "RU", "Rostov": "RU", "FC Rostov": "RU",
    "Sochi": "RU", "Akhmat Grozny": "RU", "Ural": "RU", "Ufa": "RU",
    "Orenburg": "RU", "Khimki": "RU", "Arsenal Tula": "RU", "Nizhny Novgorod": "RU",
    "Samara": "RU", "Krylya Sovetov": "RU", "Anzhi": "RU", "Anzhi Makhachkala": "RU",
    "Terek Grozny": "RU", "Amkar Perm": "RU", "Tom Tomsk": "RU",

    # UKRAINE (UA)
    "Shakhtar Donetsk": "UA", "Shakhtar": "UA", "Dynamo Kyiv": "UA", "Dynamo Kiev": "UA",
    "Metalist Kharkiv": "UA", "Dnipro": "UA", "Dnipro Dnipropetrovsk": "UA",
    "Vorskla Poltava": "UA", "Zorya Luhansk": "UA", "Zorya": "UA",
    "Karpaty Lviv": "UA", "Metalurh Donetsk": "UA", "Chornomorets Odesa": "UA",

    # GREECE (GR)
    "Olympiacos": "GR", "Olympiakos": "GR", "Panathinaikos": "GR", "AEK Athens": "GR",
    "AEK": "GR", "PAOK": "GR", "PAOK Thessaloniki": "GR", "Aris": "GR",
    "Aris Thessaloniki": "GR", "Asteras Tripolis": "GR", "Atromitos": "GR",
    "Panetolikos": "GR", "Volos": "GR", "OFI Crete": "GR", "Ionikos": "GR",
    "Giannina": "GR", "PAS Giannina": "GR", "Xanthi": "GR", "Larissa": "GR",
    # Additional Greek clubs
    "AO Kerkyra": "GR", "Kerkyra": "GR", "PAE Kerkyra": "GR", "Lamia": "GR",
    "PAS Lamia": "GR", "Apollon Smyrnis": "GR", "Levadiakos": "GR", "PAS Levadiakos": "GR",
    "Panionios": "GR", "Panionios GSS": "GR", "Kallithea": "GR", "Apollon Kalamarias": "GR",
    "Iraklis": "GR", "Iraklis Thessaloniki": "GR", "Ergotelis": "GR", "Ergotelis FC": "GR",
    "Panthrakikos": "GR", "Veria": "GR", "PAE Veria": "GR", "Kavala": "GR", "AO Kavala": "GR",
    "Panachaiki": "GR", "Panachaiki GE": "GR", "Egaleo": "GR", "Ethnikos Piraeus": "GR",
    "Proodeftiki": "GR", "Doxa Drama": "GR", "Pierikos": "GR", "Diagoras": "GR",
    "OFI": "GR", "OFI FC": "GR", "Platanias": "GR", "Platanias FC": "GR",

    # CROATIA (HR)
    "Dinamo Zagreb": "HR", "Hajduk Split": "HR", "Rijeka": "HR", "HNK Rijeka": "HR",
    "Osijek": "HR", "NK Osijek": "HR", "Lokomotiva Zagreb": "HR", "Gorica": "HR",
    "Slaven Belupo": "HR", "Istra 1961": "HR",
    "Croatia Sesvete": "HR", "NK Croatia Sesvete": "HR", "NK Zagreb": "HR",
    "Varaždin": "HR", "NK Varaždin": "HR", "Inter Zaprešić": "HR", "Zaprešić": "HR",
    "Cibalia": "HR", "HNK Cibalia": "HR", "Šibenik": "HR", "HNK Šibenik": "HR",
    "Split": "HR", "RNK Split": "HR", "Zadar": "HR", "NK Zadar": "HR",

    # SERBIA (RS)
    "Red Star Belgrade": "RS", "Crvena Zvezda": "RS", "Partizan": "RS", "Partizan Belgrade": "RS",
    "Vojvodina": "RS", "Čukarički": "RS", "Radnički Niš": "RS", "TSC Bačka Topola": "RS",

    # SWITZERLAND (CH)
    "Basel": "CH", "FC Basel": "CH", "Young Boys": "CH", "BSC Young Boys": "CH",
    "Zürich": "CH", "FC Zürich": "CH", "Servette": "CH", "Lugano": "CH", "FC Lugano": "CH",
    "St. Gallen": "CH", "FC St. Gallen": "CH", "Luzern": "CH", "FC Luzern": "CH",
    "Grasshoppers": "CH", "Grasshopper Club": "CH", "Sion": "CH", "FC Sion": "CH",
    "Lausanne": "CH", "FC Lausanne": "CH", "Winterthur": "CH", "FC Winterthur": "CH",
    "Thun": "CH", "FC Thun": "CH", "Aarau": "CH", "FC Aarau": "CH", "Neuchâtel Xamax": "CH",
    # Additional Swiss clubs
    "Bellinzona": "CH", "AC Bellinzona": "CH", "FC Baden": "CH", "Baden": "CH",
    "FC Locarno": "CH", "Locarno": "CH", "FC Ibach": "CH", "Ibach": "CH",
    "FC Hard": "CH", "Hard": "CH", "FC Kufstein": "CH", "Kufstein": "CH",
    "FC Oftringen": "CH", "Oftringen": "CH", "FC St.Gallen": "CH",
    "Schaffhausen": "CH", "FC Schaffhausen": "CH", "Vaduz": "CH", "FC Vaduz": "CH",
    "Wil": "CH", "FC Wil": "CH", "Kriens": "CH", "SC Kriens": "CH",
    "Stade Lausanne-Ouchy": "CH", "SLO": "CH", "Chiasso": "CH", "FC Chiasso": "CH",
    "Wohlen": "CH", "FC Wohlen": "CH", "Biel": "CH", "FC Biel-Bienne": "CH",
    "Le Mont": "CH", "FC Le Mont": "CH", "Rapperswil-Jona": "CH", "FC Rapperswil-Jona": "CH",

    # AUSTRIA (AT)
    "Salzburg": "AT", "Red Bull Salzburg": "AT", "RB Salzburg": "AT", "Rapid Vienna": "AT",
    "Rapid Wien": "AT", "Austria Vienna": "AT", "Austria Wien": "AT", "Sturm Graz": "AT",
    "LASK": "AT", "LASK Linz": "AT", "Wolfsberger AC": "AT", "WAC": "AT",
    "Hartberg": "AT", "TSV Hartberg": "AT", "Ried": "AT", "SV Ried": "AT",
    "Admira Wacker": "AT", "Altach": "AT", "SCR Altach": "AT", "Mattersburg": "AT",
    "Wacker Innsbruck": "AT", "Grazer AK": "AT", "Austria Klagenfurt": "AT",
    # Additional Austrian clubs
    "Austria Lustenau": "AT", "SC Austria Lustenau": "AT", "Rheindorf Altach": "AT",
    "ASKÖ Fürnitz": "AT", "Fürnitz": "AT", "First Vienna": "AT", "First Vienna FC": "AT",
    "Wiener Sport-Club": "AT", "Wiener Sportklub": "AT", "FK Austria Wien": "AT",
    "SV Horn": "AT", "Horn": "AT", "FC Liefering": "AT", "Liefering": "AT",
    "Austria Salzburg": "AT", "SV Austria Salzburg": "AT", "FC Wacker Innsbruck": "AT",
    "Kapfenberger SV": "AT", "Kapfenberg": "AT", "Blau-Weiß Linz": "AT",
    "FC Blau-Weiß Linz": "AT", "SK Rapid Wien": "AT", "Wiener Neustadt": "AT",
    "SC Wiener Neustadt": "AT", "Austria Kärnten": "AT", "DSV Leoben": "AT",
    "GAK 1902": "AT", "Grazer AK 1902": "AT", "SC Rheindorf Altach": "AT",
    "WSG Tirol": "AT", "WSG Wattens": "AT", "SV Grödig": "AT", "Grödig": "AT",

    # POLAND (PL)
    "Legia Warsaw": "PL", "Legia Warszawa": "PL", "Lech Poznań": "PL", "Lech Poznan": "PL",
    "Wisła Kraków": "PL", "Wisla Krakow": "PL", "Śląsk Wrocław": "PL", "Slask Wroclaw": "PL",
    "Jagiellonia": "PL", "Jagiellonia Białystok": "PL", "Raków Częstochowa": "PL",
    "Pogoń Szczecin": "PL", "Cracovia": "PL", "Piast Gliwice": "PL",
    "Górnik Zabrze": "PL", "Zagłębie Lubin": "PL", "Korona Kielce": "PL",
    "Warta Poznań": "PL", "Stal Mielec": "PL", "Wisła Płock": "PL",
    "Znicz Pruszków": "PL", "LKS Łódź": "PL", "Widzew Łódź": "PL",
    "Concordia Knurów": "PL", "Delta Warsaw": "PL", "Delta Warszawa": "PL",
    "Ruch Chorzów": "PL", "Ruch Chorzow": "PL", "GKS Katowice": "PL", "Katowice": "PL",
    "Arka Gdynia": "PL", "Gdynia": "PL", "Lechia Gdańsk": "PL", "Lechia Gdansk": "PL",
    "Zawisza Bydgoszcz": "PL", "Bydgoszcz": "PL", "GKS Bełchatów": "PL", "Bełchatów": "PL",
    "Odra Opole": "PL", "Opole": "PL", "Termalica Bruk-Bet": "PL", "Termalica": "PL",
    "Miedź Legnica": "PL", "Legnica": "PL", "Sandecja Nowy Sącz": "PL", "Sandecja": "PL",
    "GKS Tychy": "PL", "Tychy": "PL", "Polonia Warsaw": "PL", "Polonia Warszawa": "PL",

    # CZECH REPUBLIC (CZ)
    "Sparta Prague": "CZ", "Sparta Praha": "CZ", "Slavia Prague": "CZ", "Slavia Praha": "CZ",
    "Viktoria Plzeň": "CZ", "Plzen": "CZ", "Baník Ostrava": "CZ", "Jablonec": "CZ",
    "Slovan Liberec": "CZ", "Liberec": "CZ", "Mladá Boleslav": "CZ", "Teplice": "CZ",
    "Bohemians 1905": "CZ", "Bohemians": "CZ", "Slovácko": "CZ", "Hradec Králové": "CZ",

    # SWEDEN (SE)
    "Malmö FF": "SE", "Malmo FF": "SE", "AIK": "SE", "Djurgården": "SE", "Djurgarden": "SE",
    "Hammarby": "SE", "IFK Göteborg": "SE", "IFK Gothenburg": "SE", "Elfsborg": "SE",
    "IF Elfsborg": "SE", "Häcken": "SE", "BK Häcken": "SE", "Norrköping": "SE",
    "IFK Norrköping": "SE", "Helsingborg": "SE", "Helsingborgs IF": "SE", "Kalmar FF": "SE",
    "Örebro SK": "SE", "Halmstad": "SE", "Halmstads BK": "SE", "Sirius": "SE",
    "IK Sirius": "SE", "Varberg": "SE", "Varbergs BoIS": "SE", "Degerfors": "SE",
    "Mjällby": "SE", "Mjallby": "SE",

    # NORWAY (NO)
    "Rosenborg": "NO", "Molde": "NO", "Bodø/Glimt": "NO", "Bodo/Glimt": "NO",
    "Viking": "NO", "Viking FK": "NO", "Brann": "NO", "SK Brann": "NO",
    "Vålerenga": "NO", "Valerenga": "NO", "Lillestrøm": "NO", "Lillestrom": "NO",
    "Stabæk": "NO", "Stabaek": "NO", "Odd": "NO", "Odds BK": "NO",
    "Strømsgodset": "NO", "Stromsgodset": "NO", "Sarpsborg 08": "NO", "Haugesund": "NO",
    "Tromsø": "NO", "Tromso": "NO", "Start": "NO", "IK Start": "NO",
    "Aalesund": "NO", "Aalesunds FK": "NO", "Sandefjord": "NO", "Sandefjord Fotball": "NO",
    "Kristiansund": "NO", "Kristiansund BK": "NO", "Sogndal": "NO", "Sogndal IL": "NO",
    "Mjøndalen": "NO", "Mjondalen": "NO", "Fredrikstad": "NO", "Fredrikstad FK": "NO",
    "Kongsvinger": "NO", "Kongsvinger IL": "NO", "Moss FK": "NO", "Moss": "NO",
    "Lyn": "NO", "Lyn Oslo": "NO", "Avaldsnes": "NO", "Avaldsnes IL": "NO",
    "HamKam": "NO", "Ham-Kam": "NO", "Jerv": "NO", "FK Jerv": "NO",

    # DENMARK (DK)
    "Copenhagen": "DK", "FC Copenhagen": "DK", "Midtjylland": "DK", "FC Midtjylland": "DK",
    "Brøndby": "DK", "Brondby": "DK", "Nordsjælland": "DK", "FC Nordsjælland": "DK",
    "Silkeborg": "DK", "Silkeborg IF": "DK", "Randers": "DK", "Randers FC": "DK",
    "AGF": "DK", "AGF Aarhus": "DK", "Aarhus": "DK", "AaB": "DK", "AaB Aalborg": "DK",
    "Aalborg": "DK", "Viborg": "DK", "Viborg FF": "DK", "Odense": "DK", "OB": "DK",
    "SønderjyskE": "DK", "Sonderjyske": "DK", "Lyngby": "DK", "Lyngby BK": "DK",
    "Vejle": "DK", "Vejle BK": "DK", "Horsens": "DK", "AC Horsens": "DK",
    "Esbjerg": "DK", "Esbjerg fB": "DK", "Hvidovre": "DK", "Hvidovre IF": "DK",
    "Fremad Amager": "DK", "Amager": "DK", "Helsingør": "DK", "FC Helsingør": "DK",
    "Hobro": "DK", "Hobro IK": "DK", "Kolding": "DK", "Kolding IF": "DK",
    "Næstved": "DK", "Næstved BK": "DK", "Fredericia": "DK", "FC Fredericia": "DK",
    "HB Køge": "DK", "Køge": "DK", "Vendsyssel": "DK", "Vendsyssel FF": "DK",

    # BRAZIL (BR)
    "Flamengo": "BR", "Palmeiras": "BR", "São Paulo": "BR", "Sao Paulo": "BR",
    "Corinthians": "BR", "Santos": "BR", "Grêmio": "BR", "Gremio": "BR",
    "Internacional": "BR", "Atlético Mineiro": "BR", "Atletico Mineiro": "BR",
    "Cruzeiro": "BR", "Fluminense": "BR", "Botafogo": "BR", "Vasco da Gama": "BR",
    "Athletico Paranaense": "BR", "Athletico-PR": "BR", "Bahia": "BR",
    "Fortaleza": "BR", "Ceará": "BR", "Ceara": "BR", "Sport Recife": "BR",
    "Goiás": "BR", "Goias": "BR", "Coritiba": "BR", "América Mineiro": "BR",
    "Cuiabá": "BR", "Cuiaba": "BR", "Bragantino": "BR", "Red Bull Bragantino": "BR",
    "Juventude": "BR", "Chapecoense": "BR", "Avaí": "BR", "Avai": "BR",

    # ARGENTINA (AR)
    "River Plate": "AR", "Boca Juniors": "AR", "Racing Club": "AR", "Independiente": "AR",
    "San Lorenzo": "AR", "Vélez Sarsfield": "AR", "Velez Sarsfield": "AR",
    "Estudiantes": "AR", "Lanús": "AR", "Lanus": "AR", "Banfield": "AR",
    "Talleres": "AR", "Argentinos Juniors": "AR", "Huracán": "AR", "Huracan": "AR",
    "Colón": "AR", "Colon": "AR", "Unión": "AR", "Union Santa Fe": "AR",
    "Rosario Central": "AR", "Newell's Old Boys": "AR", "Newells Old Boys": "AR",
    "Gimnasia La Plata": "AR", "Defensa y Justicia": "AR", "Godoy Cruz": "AR",
    "Tigre": "AR", "Arsenal de Sarandí": "AR", "Central Córdoba": "AR",

    # USA (US)
    "LA Galaxy": "US", "Los Angeles Galaxy": "US", "LAFC": "US", "Los Angeles FC": "US",
    "New York Red Bulls": "US", "Red Bulls": "US", "New York City FC": "US", "NYCFC": "US",
    "Inter Miami": "US", "Miami": "US", "Atlanta United": "US", "Seattle Sounders": "US",
    "Portland Timbers": "US", "Toronto FC": "US", "Columbus Crew": "US",
    "Philadelphia Union": "US", "D.C. United": "US", "DC United": "US",
    "Chicago Fire": "US", "Orlando City": "US", "FC Dallas": "US", "Houston Dynamo": "US",
    "Sporting Kansas City": "US", "Minnesota United": "US", "Real Salt Lake": "US",
    "Colorado Rapids": "US", "San Jose Earthquakes": "US", "New England Revolution": "US",
    "Vancouver Whitecaps": "US", "Nashville SC": "US", "Austin FC": "US",
    "Charlotte FC": "US", "St. Louis City": "US", "CF Montreal": "US",

    # CANADA (CA)
    "Montreal Impact": "CA", "CF Montréal": "CA",

    # MEXICO (MX)
    "Club América": "MX", "America": "MX", "Guadalajara": "MX", "Chivas": "MX",
    "Cruz Azul": "MX", "UNAM": "MX", "Pumas UNAM": "MX", "Tigres UANL": "MX",
    "Tigres": "MX", "Monterrey": "MX", "CF Monterrey": "MX", "Santos Laguna": "MX",
    "Toluca": "MX", "León": "MX", "Leon": "MX", "Pachuca": "MX",
    "Necaxa": "MX", "Atlas": "MX", "Puebla": "MX", "Querétaro": "MX", "Queretaro": "MX",
    "Mazatlán": "MX", "Mazatlan": "MX", "San Luis": "MX", "Atlético San Luis": "MX",
    "Juárez": "MX", "Juarez": "MX", "Tijuana": "MX", "Club Tijuana": "MX",

    # CHINA (CN)
    "Shanghai Shenhua": "CN", "Shenhua": "CN", "Shanghai SIPG": "CN", "Shanghai Port": "CN",
    "Guangzhou Evergrande": "CN", "Guangzhou": "CN", "Guangzhou FC": "CN",
    "Beijing Guoan": "CN", "Guoan": "CN", "Shandong Taishan": "CN", "Shandong Luneng": "CN",
    "Jiangsu FC": "CN", "Jiangsu Suning": "CN", "Tianjin Teda": "CN", "Dalian": "CN",
    "Hebei": "CN", "Hebei FC": "CN", "Shenzhen FC": "CN",

    # JAPAN (JP)
    "Urawa Red Diamonds": "JP", "Urawa Reds": "JP", "Yokohama F. Marinos": "JP",
    "Kawasaki Frontale": "JP", "Vissel Kobe": "JP", "Kashima Antlers": "JP",
    "FC Tokyo": "JP", "Gamba Osaka": "JP", "Cerezo Osaka": "JP", "Nagoya Grampus": "JP",
    "Sanfrecce Hiroshima": "JP", "Kashiwa Reysol": "JP", "Shimizu S-Pulse": "JP",
    "Sagan Tosu": "JP", "Consadole Sapporo": "JP", "Vegalta Sendai": "JP",
    "Jubilo Iwata": "JP", "Albirex Niigata": "JP", "Shonan Bellmare": "JP",

    # SOUTH KOREA (KR)
    "Jeonbuk Hyundai": "KR", "Jeonbuk Motors": "KR", "Ulsan Hyundai": "KR",
    "FC Seoul": "KR", "Suwon Samsung Bluewings": "KR", "Suwon Bluewings": "KR",
    "Pohang Steelers": "KR", "Daegu FC": "KR", "Incheon United": "KR",
    "Gangwon FC": "KR", "Jeju United": "KR", "Seongnam FC": "KR",

    # SAUDI ARABIA (SA)
    "Al Nassr": "SA", "Al-Nassr": "SA", "Al Hilal": "SA", "Al-Hilal": "SA",
    "Al Ahli": "SA", "Al-Ahli": "SA", "Al Ittihad": "SA", "Al-Ittihad": "SA",
    "Al Shabab": "SA", "Al-Shabab": "SA", "Al Fateh": "SA", "Al Ettifaq": "SA",
    "Al Taawoun": "SA", "Al Fayha": "SA", "Damac": "SA", "Abha": "SA",
    "Al-Ettifaq": "SA", "Al-Fayha": "SA", "Al-Taawoun": "SA", "Al-Fateh": "SA",
    "Al-Qadsiah": "SA", "Al Qadsiah": "SA", "Al-Raed": "SA", "Al Raed": "SA",
    "Al-Wehda": "SA", "Al Wehda": "SA", "Al-Khaleej": "SA", "Al Khaleej": "SA",
    "Al-Riyadh": "SA", "Al Riyadh": "SA", "Al-Adalah": "SA", "Al Adalah": "SA",

    # UAE (AE)
    "Al Ain": "AE", "Al-Ain": "AE", "Al Wasl": "AE", "Al-Wasl": "AE",
    "Shabab Al-Ahli": "AE", "Shabab Al Ahli": "AE", "Al Jazira": "AE", "Al-Jazira": "AE",
    "Sharjah": "AE", "Sharjah FC": "AE", "Bani Yas": "AE", "Baniyas": "AE",
    "Al Wahda": "AE", "Al-Wahda": "AE", "Al Nasr Dubai": "AE", "Al-Nasr": "AE",
    "Al Nasr": "AE", "Ajman": "AE", "Ajman Club": "AE", "Emirates Club": "AE",
    "Al Dhafra": "AE", "Al-Dhafra": "AE", "Fujairah": "AE", "Fujairah FC": "AE",
    "Ittihad Kalba": "AE", "Kalba": "AE", "Hatta": "AE", "Hatta Club": "AE",

    # QATAR (QA)
    "Al Sadd": "QA", "Al-Sadd": "QA", "Al Duhail": "QA", "Al-Duhail": "QA",
    "Al Rayyan": "QA", "Al-Rayyan": "QA", "Al Arabi": "QA", "Al-Arabi": "QA",
    "Al Gharafa": "QA", "Al-Gharafa": "QA", "Al Wakrah": "QA", "Al-Wakrah": "QA",
    "Umm Salal": "QA", "Al Ahli Doha": "QA", "Al-Ahli Doha": "QA",
    "Al Shahania": "QA", "Al-Shahania": "QA", "Qatar SC": "QA", "Al Khor": "QA",
    "Al-Khor": "QA", "Al Sailiya": "QA", "Al-Sailiya": "QA",
    "Al Shamal": "QA", "Al-Shamal": "QA", "Al Markhiya": "QA", "Al-Markhiya": "QA",
    "Muaither": "QA", "Muaither SC": "QA",

    # AUSTRALIA (AU)
    "Melbourne Victory": "AU", "Sydney FC": "AU", "Melbourne City": "AU",
    "Western Sydney Wanderers": "AU", "Brisbane Roar": "AU", "Perth Glory": "AU",
    "Adelaide United": "AU", "Wellington Phoenix": "AU", "Central Coast Mariners": "AU",
    "Newcastle Jets": "AU", "Macarthur FC": "AU", "Western United": "AU",
    "Brisbane Strikers": "AU", "South Melbourne": "AU", "South Melbourne FC": "AU",
    "Melbourne Knights": "AU", "Wollongong Wolves": "AU", "Marconi Stallions": "AU",
    "Sydney United": "AU", "Sydney Olympic": "AU", "Adelaide City": "AU",
    "Queensland Roar": "AU", "Gold Coast United": "AU", "North Queensland Fury": "AU",
    "Melbourne Heart": "AU",

    # ISRAEL (IL)
    "Maccabi Tel Aviv": "IL", "Maccabi Haifa": "IL", "Hapoel Tel Aviv": "IL",
    "Hapoel Beer Sheva": "IL", "Beitar Jerusalem": "IL", "Bnei Yehuda": "IL",
    "Maccabi Netanya": "IL", "Hapoel Haifa": "IL", "Ashdod": "IL",

    # CYPRUS (CY)
    "APOEL": "CY", "APOEL Nicosia": "CY", "Omonia Nicosia": "CY", "Omonia": "CY",
    "Anorthosis Famagusta": "CY", "Anorthosis": "CY", "AEL Limassol": "CY",
    "Apollon Limassol": "CY", "Apollon": "CY", "AEK Larnaca": "CY",

    # ROMANIA (RO)
    "Steaua București": "RO", "FCSB": "RO", "Steaua Bucharest": "RO",
    "Dinamo București": "RO", "Dinamo Bucharest": "RO", "CFR Cluj": "RO",
    "Rapid București": "RO", "Rapid Bucharest": "RO", "Universitatea Craiova": "RO",
    "Craiova": "RO", "Sepsi OSK": "RO", "Farul Constanța": "RO",

    # BULGARIA (BG)
    "Ludogorets": "BG", "Ludogorets Razgrad": "BG", "CSKA Sofia": "BG",
    "Levski Sofia": "BG", "Lokomotiv Plovdiv": "BG", "Botev Plovdiv": "BG",
    "Cherno More": "BG", "Slavia Sofia": "BG", "Beroe": "BG",

    # HUNGARY (HU)
    "Ferencváros": "HU", "Ferencvaros": "HU", "Honvéd": "HU", "Budapest Honved": "HU",
    "Újpest": "HU", "Ujpest": "HU", "Debrecen": "HU", "Debreceni VSC": "HU",
    "Videoton": "HU", "Fehérvár": "HU", "MOL Fehérvár": "HU", "Puskás Akadémia": "HU",

    # SLOVAKIA (SK)
    "Slovan Bratislava": "SK", "ŠK Slovan Bratislava": "SK", "Spartak Trnava": "SK",
    "AS Trenčín": "SK", "Trenčín": "SK", "MŠK Žilina": "SK", "Žilina": "SK",
    "DAC Dunajská Streda": "SK", "DAC 1904": "SK", "Ružomberok": "SK", "MFK Ružomberok": "SK",
    "Michalovce": "SK", "MFK Zemplín Michalovce": "SK", "Inter Bratislava": "SK",
    "Košice": "SK", "FC Košice": "SK", "Petržalka": "SK", "Artmedia Petržalka": "SK",

    # NIGERIA (NG)
    "Abia Warriors": "NG", "Enyimba": "NG", "Enyimba FC": "NG", "Kano Pillars": "NG",
    "Rivers United": "NG", "Shooting Stars": "NG", "3SC": "NG", "Sunshine Stars": "NG",
    "Akwa United": "NG", "Plateau United": "NG", "Enugu Rangers": "NG", "Rangers International": "NG",
    "Lobi Stars": "NG", "Nasarawa United": "NG", "Heartland FC": "NG", "Kwara United": "NG",

    # SENEGAL (SN)
    "ASC Jeanne d'Arc": "SN", "Jeanne d'Arc": "SN", "Casa Sports": "SN", "Génération Foot": "SN",
    "AS Douanes": "SN", "Niary Tally": "SN", "Diambars": "SN", "Jaraaf": "SN", "ASC Jaraaf": "SN",

    # MOROCCO (MA)
    "Raja Casablanca": "MA", "Wydad Casablanca": "MA", "WAC": "MA", "FAR Rabat": "MA",
    "AS FAR": "MA", "FUS Rabat": "MA", "Moghreb Tétouan": "MA", "Berkane": "MA",
    "Renaissance Berkane": "MA", "RS Berkane": "MA", "Difaâ El Jadida": "MA",

    # EGYPT (EG)
    "Al Ahly": "EG", "Al-Ahly": "EG", "Zamalek": "EG", "Zamalek SC": "EG",
    "Pyramids FC": "EG", "Ismaily": "EG", "Ismaily SC": "EG", "Enppi": "EG",
    "Ceramica Cleopatra": "EG", "Future FC": "EG", "El Gouna": "EG",

    # SOUTH AFRICA (ZA)
    "Kaizer Chiefs": "ZA", "Orlando Pirates": "ZA", "Mamelodi Sundowns": "ZA",
    "Stellenbosch FC": "ZA", "Cape Town City": "ZA", "SuperSport United": "ZA",
    "AmaZulu": "ZA", "Sekhukhune United": "ZA", "Golden Arrows": "ZA",
    "Bidvest Wits": "ZA", "Wits": "ZA", "BidVest Wits FC": "ZA",
    "Bloemfontein Celtic": "ZA", "Celtic": "ZA", "Maritzburg United": "ZA",
    "Chippa United": "ZA", "Baroka FC": "ZA", "Polokwane City": "ZA",
    "Black Leopards": "ZA", "TS Galaxy": "ZA", "Richards Bay": "ZA",
    "Royal AM": "ZA", "Swallows FC": "ZA", "Moroka Swallows": "ZA",

    # GHANA (GH)
    "Asante Kotoko": "GH", "Hearts of Oak": "GH", "Accra Hearts of Oak": "GH",
    "Medeama": "GH", "Medeama SC": "GH", "Aduana Stars": "GH", "Dreams FC": "GH",

    # IVORY COAST (CI)
    "ASEC Mimosas": "CI", "ASEC Abidjan": "CI", "Africa Sports": "CI",
    "Stade d'Abidjan": "CI", "Séwé Sports": "CI",

    # CAMEROON (CM)
    "Canon Yaoundé": "CM", "Tonnerre Yaoundé": "CM", "Coton Sport": "CM",
    "Cotonsport Garoua": "CM", "Union Douala": "CM", "PWD Bamenda": "CM",

    # ALGERIA (DZ)
    "MC Alger": "DZ", "USM Alger": "DZ", "JS Kabylie": "DZ", "CR Belouizdad": "DZ",
    "ES Sétif": "DZ", "USM Bel Abbès": "DZ", "MC Oran": "DZ", "ASO Chlef": "DZ",

    # TUNISIA (TN)
    "Espérance Tunis": "TN", "Espérance de Tunis": "TN", "Club Africain": "TN",
    "Étoile du Sahel": "TN", "CS Sfaxien": "TN", "US Monastir": "TN",

    # WALES (WA)
    "Cardiff City": "WA", "Swansea City": "WA", "Wrexham": "WA", "Newport County": "WA",
    "The New Saints": "WA", "TNS": "WA", "Connah's Quay Nomads": "WA",
    "Barry Town": "WA", "Bangor City": "WA",

    # NORTHERN IRELAND (NI)
    "Linfield": "NI", "Linfield FC": "NI", "Glentoran": "NI", "Crusaders": "NI",
    "Cliftonville": "NI", "Coleraine": "NI", "Larne": "NI", "Glenavon": "NI",

    # REPUBLIC OF IRELAND (IE)
    "Shamrock Rovers": "IE", "Bohemians": "IE", "Bohemian FC": "IE", "Dundalk": "IE",
    "Dundalk FC": "IE", "St Patrick's Athletic": "IE", "Derry City": "IE",
    "Shelbourne": "IE", "Sligo Rovers": "IE", "Cork City": "IE", "Drogheda United": "IE",

    # COLOMBIA (CO)
    "Atlético Nacional": "CO", "Atletico Nacional": "CO", "Millonarios": "CO",
    "América de Cali": "CO", "Deportivo Cali": "CO", "Junior": "CO", "Junior de Barranquilla": "CO",
    "Independiente Medellín": "CO", "Santa Fe": "CO", "Independiente Santa Fe": "CO",
    "Once Caldas": "CO", "Deportes Tolima": "CO", "Envigado": "CO",

    # ARMENIA (AM)
    "Ararat Moscow": "AM", "Ararat-Armenia": "AM", "Ararat Yerevan": "AM",
    "Pyunik": "AM", "FC Pyunik": "AM", "Alashkert": "AM", "FC Alashkert": "AM",
    "Ararat": "AM", "Shirak": "AM", "FC Shirak": "AM", "Banants": "AM",
    "Urartu": "AM", "FC Urartu": "AM", "Mika": "AM", "FC Mika": "AM",

    # INDIA (IN)
    "Chennaiyin": "IN", "Chennaiyin FC": "IN", "Delhi Dynamos": "IN", "Delhi FC": "IN",
    "Mumbai City": "IN", "Mumbai City FC": "IN", "Bengaluru FC": "IN", "Bengaluru": "IN",
    "Kerala Blasters": "IN", "Kerala Blasters FC": "IN", "ATK Mohun Bagan": "IN",
    "Mohun Bagan": "IN", "ATK": "IN", "East Bengal": "IN", "SC East Bengal": "IN",
    "FC Goa": "IN", "Goa": "IN", "Jamshedpur FC": "IN", "Jamshedpur": "IN",
    "Hyderabad FC": "IN", "NorthEast United": "IN", "NorthEast United FC": "IN",
    "Odisha FC": "IN", "Punjab FC": "IN",

    # PERU (PE)
    "Alianza Lima": "PE", "Club Alianza Lima": "PE", "Universitario": "PE",
    "Universitario de Deportes": "PE", "Sporting Cristal": "PE", "Cristal": "PE",
    "Cienciano": "PE", "Club Cienciano": "PE", "Melgar": "PE", "FBC Melgar": "PE",
    "Deportivo Municipal": "PE", "Municipal": "PE", "César Vallejo": "PE",
    "Universidad San Martín": "PE", "San Martín": "PE", "Sport Boys": "PE",
    "Juan Aurich": "PE", "Unión Comercio": "PE", "Cusco FC": "PE",

    # BRAZIL (additional)
    "Atlético Paranaense": "BR", "Athletico-PR": "BR", "CAP": "BR",
    "Cascavel": "BR", "FC Cascavel": "BR", "Criciúma": "BR", "Criciuma": "BR",
    "Democrata SL": "BR", "Democrata": "BR", "Londrina": "BR", "Londrina EC": "BR",
    "Operário Ferroviário": "BR", "Operário-PR": "BR", "Coritiba FC": "BR",
    "Paraná Clube": "BR", "Paraná": "BR", "Maringá": "BR", "Maringá FC": "BR",
    "América-MG": "BR", "America Mineiro": "BR", "Tombense": "BR", "Tombense FC": "BR",
    "Vila Nova": "BR", "Vila Nova FC": "BR", "Ponte Preta": "BR", "AA Ponte Preta": "BR",
    "Guarani": "BR", "Guarani FC": "BR", "Novorizontino": "BR", "Grêmio Novorizontino": "BR",
    "Ituano": "BR", "Ituano FC": "BR", "Mirassol": "BR", "Mirassol FC": "BR",
    "CRB": "BR", "CRB Maceió": "BR", "CSA": "BR", "CSA Maceió": "BR",
    "Sampaio Corrêa": "BR", "Sampaio Correa": "BR", "Náutico": "BR", "Nautico": "BR",
    "Santa Cruz": "BR", "Santa Cruz FC": "BR", "Remo": "BR", "Clube do Remo": "BR",
    "Paysandu": "BR", "Paysandu SC": "BR", "ABC": "BR", "ABC FC": "BR",

    # VENEZUELA (VE)
    "Atlético Venezuela": "VE", "Caracas FC": "VE", "Caracas": "VE",
    "Deportivo Táchira": "VE", "Táchira": "VE", "Monagas SC": "VE",
    "Zamora FC": "VE", "Deportivo La Guaira": "VE", "Mineros de Guayana": "VE",

    # PORTUGAL (additional)
    "Aves": "PT", "CD Aves": "PT", "Desportivo das Aves": "PT",
    "Leixões": "PT", "Leixoes": "PT", "Académico de Viseu": "PT",
    "Chaves": "PT", "GD Chaves": "PT", "Penafiel": "PT", "FC Penafiel": "PT",
    "Feirense": "PT", "CD Feirense": "PT", "Oliveirense": "PT",
    "Covilhã": "PT", "Sporting Covilhã": "PT", "Mafra": "PT", "CD Mafra": "PT",

    # SPAIN (additional)
    "Basconia": "ES", "CD Basconia": "ES", "Binéfar": "ES", "CD Binéfar": "ES",
    "Alavés B": "ES", "Athletic Bilbao B": "ES", "Bilbao Athletic": "ES",
    "Real Madrid Castilla": "ES", "Castilla": "ES", "Barcelona B": "ES",
    "Barça B": "ES", "Atlético Madrid B": "ES", "Sevilla Atlético": "ES",
    "Real Sociedad B": "ES", "Sanse": "ES", "Villarreal B": "ES",
    "Valencia Mestalla": "ES", "Mestalla": "ES", "Betis Deportivo": "ES",
    "Málaga": "ES", "Malaga": "ES", "CD Málaga": "ES",
    "Sporting de Gijón": "ES", "Sporting Gijón": "ES",
    "Cartagena": "ES", "FC Cartagena": "ES", "Castellón": "ES", "CD Castellón": "ES",
    "Ciudad de Murcia": "ES", "Murcia": "ES", "Real Murcia": "ES",
    "Cornellà": "ES", "UE Cornellà": "ES", "Lorca": "ES", "Lorca FC": "ES",
    "Mérida": "ES", "Mérida AD": "ES", "Ponferradina": "ES", "SD Ponferradina": "ES",
    "Badajoz": "ES", "CD Badajoz": "ES", "Mirandés": "ES", "CD Mirandés": "ES",
    "Ibiza": "ES", "UD Ibiza": "ES", "Fuenlabrada": "ES", "CF Fuenlabrada": "ES",
    "Alcorcón": "ES", "AD Alcorcón": "ES", "Eldense": "ES", "CD Eldense": "ES",
    "Amorebieta": "ES", "SD Amorebieta": "ES", "Racing Ferrol": "ES",
    "Andorra": "ES", "FC Andorra": "ES", "Burgos": "ES", "Burgos CF": "ES",
    "San Fernando": "ES", "San Fernando CD": "ES", "Hércules": "ES", "Hércules CF": "ES",
    "Gimnàstic": "ES", "Gimnàstic de Tarragona": "ES", "Nàstic": "ES",
    "Xerez": "ES", "Xerez CD": "ES", "Xerez Deportivo": "ES", "Écija": "ES",
    "Huesca": "ES", "SD Huesca": "ES", "Lugo": "ES", "CD Lugo": "ES",
    "Sabadell": "ES", "CE Sabadell": "ES", "Logroñés": "ES", "CD Logroñés": "ES",

    # FRANCE (additional)
    "Béziers": "FR", "AS Béziers": "FR", "Beziers": "FR",
    "Laval": "FR", "Stade Lavallois": "FR", "Pau FC": "FR", "Pau": "FR",
    "Paris FC": "FR", "Red Star": "FR", "Red Star FC": "FR",
    "Châteauroux": "FR", "LB Châteauroux": "FR", "Niort": "FR", "Chamois Niortais": "FR",
    "Grenoble Foot 38": "FR", "Grenoble": "FR", "Rodez": "FR", "Rodez AF": "FR",
    "Quevilly Rouen": "FR", "QRM": "FR", "Dunkerque": "FR", "USL Dunkerque": "FR",
    "Orléans": "FR", "US Orléans": "FR", "Créteil": "FR", "US Créteil": "FR",
    "Beauvais": "FR", "AS Beauvais": "FR", "Cannes": "FR",
    "FC Sète": "FR", "Sète": "FR", "Arles-Avignon": "FR", "AC Arles-Avignon": "FR",
    "AC Cambrai": "FR", "Cambrai": "FR", "US Boulogne": "FR", "Boulogne": "FR",
    "Croissy-sur-Seine": "FR", "Évian": "FR", "Évian Thonon Gaillard": "FR",

    # BENIN (BJ)
    "Dragons l'Ouémé": "BJ", "Dragons FC": "BJ", "AS Dragons": "BJ",
    "ASVO": "BJ", "Buffles du Borgou": "BJ", "Requins de l'Atlantique": "BJ",
    "Tonnerre d'Abomey": "BJ", "Mogas 90": "BJ", "Soleil FC": "BJ",

    # LIBERIA (LR)
    "Bong Range United": "LR", "LISCR FC": "LR", "Invincible Eleven": "LR",
    "Mighty Barrolle": "LR", "Watanga FC": "LR", "BYC": "LR", "Barrack Young Controllers": "LR",

    # SENEGAL (additional)
    "Diaraf": "SN", "ASC Diaraf": "SN", "US Gorée": "SN", "Gorée": "SN",
    "Teungueth FC": "SN", "AS Pikine": "SN", "Pikine": "SN", "AS Douanes Dakar": "SN",

    # AUSTRIA (additional)
    "DSV Alpine": "AT", "DSV Leoben": "AT", "Pasching": "AT", "FC Pasching": "AT",
    "Austria Kärnten": "AT", "Austria Carinthia": "AT", "SV Mattersburg": "AT",
    "Admira": "AT", "FC Admira Wacker": "AT", "FC Admira": "AT",
    "SKN St. Pölten": "AT", "St. Pölten": "AT", "SV St. Pölten": "AT",

    # IRAN (IR)
    "Esteghlal": "IR", "Esteghlal FC": "IR", "Persepolis": "IR", "Persepolis FC": "IR",
    "Sepahan": "IR", "Sepahan FC": "IR", "Tractor": "IR", "Tractor FC": "IR",
    "Foolad": "IR", "Foolad FC": "IR", "Zob Ahan": "IR", "Nassaji": "IR",
    "Mes Rafsanjan": "IR", "Aluminium Arak": "IR", "Saipa": "IR", "Saipa FC": "IR",

    # NEW ZEALAND (NZ)
    "Auckland Kingz": "NZ", "Auckland FC": "NZ", "Wellington Phoenix": "NZ",
    "Central United": "NZ", "Team Wellington": "NZ", "Auckland City": "NZ",
    "Canterbury United": "NZ", "Waitakere United": "NZ", "Hawke's Bay United": "NZ",

    # EGYPT (additional)
    "Baladeyet Al-Mahalla": "EG", "Al-Mahalla": "EG", "Ghazl El Mahalla": "EG",
    "El Entag El Harby": "EG", "El Gouna FC": "EG", "ENPPI": "EG",
    "Smouha": "EG", "Smouha SC": "EG", "Al Masry": "EG", "Al-Masry": "EG",
    "Petrojet": "EG", "Wadi Degla": "EG",

    # PORTUGAL (additional)
    "Estrela da Amadora": "PT", "Estrela Amadora": "PT", "CF Estrela": "PT",
    "União de Leiria": "PT", "Leiria": "PT", "Olhanense": "PT", "SC Olhanense": "PT",
    "Académica": "PT", "Académica de Coimbra": "PT", "Vitória Setúbal": "PT",
    "Beira-Mar": "PT", "SC Beira-Mar": "PT", "Alverca": "PT", "FC Alverca": "PT",

    # LUXEMBOURG (LU)
    "FC Differdange 03": "LU", "Differdange": "LU", "F91 Dudelange": "LU", "Dudelange": "LU",
    "Progrès Niederkorn": "LU", "Niederkorn": "LU", "Racing Luxembourg": "LU",
    "Fola Esch": "LU", "CS Fola Esch": "LU", "Jeunesse Esch": "LU",
    "Union Luxembourg": "LU", "Swift Hesperange": "LU",

    # GIBRALTAR (GI)
    "Europa Point": "GI", "Europa FC": "GI", "Gibraltar United": "GI",
    "Lincoln Red Imps": "GI", "Lincoln": "GI", "St Joseph's": "GI",

    # CANADA (additional)
    "Edmonton Drillers": "CA", "Edmonton FC": "CA", "Vancouver 86ers": "CA",
    "Calgary Stampeders": "CA", "Toronto Blizzard": "CA", "York United": "CA",
    "Forge FC": "CA", "Cavalry FC": "CA", "Pacific FC": "CA", "HFX Wanderers": "CA",

    # FINLAND (FI)
    "HJK": "FI", "HJK Helsinki": "FI", "HIFK": "FI", "HIFK Helsinki": "FI",
    "FC Inter Turku": "FI", "Inter Turku": "FI", "KuPS": "FI", "Kuopion Palloseura": "FI",
    "SJK": "FI", "Seinäjoen Jalkapallokerho": "FI", "FC Lahti": "FI", "Lahti": "FI",
    "Ilves": "FI", "Tampere United": "FI", "TPS Turku": "FI", "TPS": "FI",
    "VPS": "FI", "Vaasan Palloseura": "FI", "IFK Mariehamn": "FI", "Mariehamn": "FI",

    # SWEDEN (additional)
    "AFC Eskilstuna": "SE", "Eskilstuna": "SE", "Gefle IF": "SE", "Gefle": "SE",
    "Östers IF": "SE", "Öster": "SE", "Trelleborgs FF": "SE", "Trelleborg": "SE",
    "Landskrona BoIS": "SE", "Landskrona": "SE", "Assyriska FF": "SE", "Assyriska": "SE",
    "Syrianska FC": "SE", "Syrianska": "SE", "Falkenbergs FF": "SE", "Falkenberg": "SE",
    "Örgryte IS": "SE", "Örgryte": "SE", "GAIS": "SE", "Gothenburg": "SE",
    "Brommapojkarna": "SE", "IF Brommapojkarna": "SE", "Västerås SK": "SE",

    # ROMANIA (RO additional)
    "ASA Târgu Mureș": "RO", "Târgu Mureș": "RO", "Argeș Pitești": "RO", "FC Argeș": "RO",
    "Petrolul Ploiești": "RO", "Petrolul": "RO", "Gloria Bistrița": "RO", "Bistrița": "RO",
    "Oțelul Galați": "RO", "Oțelul": "RO", "Gaz Metan Mediaș": "RO", "Mediaș": "RO",
    "Astra Giurgiu": "RO", "Astra": "RO", "Voluntari": "RO", "FC Voluntari": "RO",
    "Botoșani": "RO", "FC Botoșani": "RO", "Chindia Târgoviște": "RO", "Târgoviște": "RO",
    "UTA Arad": "RO", "Arad": "RO", "Politehnica Iași": "RO", "Iași": "RO",
    "Politehnica Timișoara": "RO", "Timișoara": "RO", "FC Vaslui": "RO", "Vaslui": "RO",
    "Unirea Urziceni": "RO", "Urziceni": "RO", "Concordia Chiajna": "RO", "Chiajna": "RO",

    # BULGARIA (BG additional)
    "Balkan Botevgrad": "BG", "Botevgrad": "BG", "Botev Vratsa": "BG", "Vratsa": "BG",
    "Lokomotiv Sofia": "BG", "Lok Sofia": "BG", "Etar Veliko Tarnovo": "BG", "Etar": "BG",
    "Neftochimik Burgas": "BG", "Neftochimik": "BG", "Pirin Blagoevgrad": "BG", "Pirin": "BG",
    "Litex Lovech": "BG", "Litex": "BG", "Montana": "BG", "FC Montana": "BG",
    "Lokomotiv Plovdiv": "BG", "Lok Plovdiv": "BG", "Arda Kardzhali": "BG", "Arda": "BG",
    "Hebros Harmanli": "BG", "Harmanli": "BG", "Spartak Varna": "BG",

    # RUSSIA (RU additional)
    "Baltika Kaliningrad": "RU", "Baltika": "RU", "Alania Vladikavkaz": "RU", "Alania": "RU",
    "Shinnik Yaroslavl": "RU", "Shinnik": "RU", "Saturn Moscow Oblast": "RU", "Saturn": "RU",
    "Fakel Voronezh": "RU", "Fakel": "RU", "Mordovia Saransk": "RU", "Mordovia": "RU",
    "Volga Nizhny Novgorod": "RU", "Volga": "RU", "Sibir Novosibirsk": "RU", "Sibir": "RU",
    "Yenisey Krasnoyarsk": "RU", "Yenisey": "RU", "Chernomorets Novorossiysk": "RU",
    "SKA Rostov-on-Don": "RU", "SKA Rostov": "RU", "Kuban Krasnodar": "RU", "Kuban": "RU",

    # JAPAN (JP additional)
    "Bellmare Hiratsuka": "JP", "Shonan Bellmare": "JP", "Bellmare": "JP",
    "JEF United": "JP", "JEF United Chiba": "JP", "Yokohama FC": "JP",
    "Tokushima Vortis": "JP", "Tokushima": "JP", "Ventforet Kofu": "JP", "Kofu": "JP",
    "Montedio Yamagata": "JP", "Yamagata": "JP", "Omiya Ardija": "JP", "Omiya": "JP",
    "Roasso Kumamoto": "JP", "Kumamoto": "JP", "Avispa Fukuoka": "JP", "Fukuoka": "JP",
    "V-Varen Nagasaki": "JP", "Nagasaki": "JP", "Renofa Yamaguchi": "JP", "Yamaguchi": "JP",

    # ENGLAND (EN additional - non-league)
    "Billericay Town": "EN", "Billericay": "EN", "Braintree Town": "EN", "Braintree": "EN",
    "Chesham United": "EN", "Chesham": "EN", "Dulwich Hamlet": "EN", "Dulwich": "EN",
    "Enfield Town": "EN", "Enfield": "EN", "Hendon": "EN", "Hendon FC": "EN",
    "Kingstonian": "EN", "Kingstonian FC": "EN", "Leatherhead": "EN", "Leatherhead FC": "EN",
    "Margate": "EN", "Margate FC": "EN", "Metropolitan Police": "EN", "Met Police": "EN",
    "Carshalton Athletic": "EN", "Carshalton": "EN", "Tooting & Mitcham": "EN",
    "Walton & Hersham": "EN", "Welling United": "EN", "Welling": "EN",
    "Wingate & Finchley": "EN", "Worthing": "EN", "Worthing FC": "EN",
    "Bishop's Stortford": "EN", "Stortford": "EN", "Canvey Island": "EN",
    "Grays Athletic": "EN", "Grays": "EN", "Harlow Town": "EN", "Harlow": "EN",
    "Hemel Hempstead Town": "EN", "Hemel Hempstead": "EN", "St Albans City": "EN",
    "Wealdstone FC": "EN", "Hayes & Yeading": "EN",

    # SCOTLAND (SC additional)
    "Dumbarton": "SC", "Dumbarton FC": "SC", "Clyde": "SC", "Clyde FC": "SC",
    "Forfar Athletic": "SC", "Forfar": "SC", "Brechin City": "SC", "Brechin": "SC",
    "Peterhead": "SC", "Peterhead FC": "SC", "Montrose": "SC", "Montrose FC": "SC",
    "Elgin City": "SC", "Elgin": "SC", "Annan Athletic": "SC", "Annan": "SC",
    "Stirling Albion": "SC", "Stirling": "SC", "Albion Rovers": "SC", "Coatbridge": "SC",
    "East Stirlingshire": "SC", "East Stirling": "SC", "Berwick Rangers": "SC", "Berwick": "SC",

    # UKRAINE (UA additional)
    "Dynamo-2 Kyiv": "UA", "Dynamo-2": "UA", "Dnipro-1": "UA", "SC Dnipro-1": "UA",
    "Kolos Kovalivka": "UA", "Kolos": "UA", "Inhulets Petrove": "UA", "Inhulets": "UA",
    "Oleksandriya": "UA", "FC Oleksandriya": "UA", "Lviv": "UA", "FC Lviv": "UA",
    "Chornomorets": "UA", "Chornomorets Odesa": "UA", "Kryvbas": "UA", "Kryvbas Kryvyi Rih": "UA",
    "Rukh Lviv": "UA", "Rukh": "UA", "Minaj": "UA", "FC Minaj": "UA",
    "Mariupol": "UA", "FC Mariupol": "UA", "Desna Chernihiv": "UA", "Desna": "UA",

    # CYPRUS (CY additional)
    "Doxa Katokopias": "CY", "Doxa": "CY", "Ethnikos Achna": "CY", "Achna": "CY",
    "Nea Salamis": "CY", "Nea Salamis Famagusta": "CY", "Enosis Neon Paralimni": "CY",
    "Aris Limassol": "CY", "Pafos FC": "CY", "Pafos": "CY", "Karmiotissa": "CY",
    "Ermis Aradippou": "CY", "Ermis": "CY", "Alki Oroklini": "CY", "Alki": "CY",

    # PARAGUAY (PY)
    "Cerro Porteño": "PY", "Cerro": "PY", "Olimpia": "PY", "Club Olimpia": "PY",
    "Libertad": "PY", "Club Libertad": "PY", "Guaraní": "PY", "Club Guaraní": "PY",
    "Nacional Asunción": "PY", "Club Nacional": "PY", "Sol de América": "PY",
    "Sportivo Luqueño": "PY", "Luqueño": "PY", "Rubio Ñu": "PY",

    # PORTUGAL (PT additional)
    "B-SAD": "PT", "Belenenses SAD": "PT", "AVS": "PT", "AVS Futebol SAD": "PT",
    "Vilafranquense": "PT", "União de Leiria": "PT", "Académico Viseu": "PT",
    "Freamunde": "PT", "SC Freamunde": "PT", "Trofense": "PT", "CD Trofense": "PT",

    # IRAN (IR additional)
    "Damash Gilan": "IR", "Damash": "IR", "Naft Tehran": "IR", "Naft": "IR",
    "Rah Ahan": "IR", "Rah Ahan Tehran": "IR", "Paykan": "IR", "Paykan FC": "IR",
    "Machine Sazi": "IR", "Padideh": "IR", "Shahr Khodro": "IR", "Shahr Khodrou": "IR",
    "Gol Gohar": "IR", "Gol Gohar Sirjan": "IR", "Malavan": "IR", "Malavan Bandar Anzali": "IR",

    # SAUDI ARABIA (SA additional)
    "Al-Shoalah": "SA", "Al Shoalah": "SA", "Al-Hazem": "SA", "Al Hazem": "SA",
    "Al-Batin": "SA", "Al Batin": "SA", "Al-Tai": "SA", "Al Tai": "SA",
    "Al-Faisaly": "SA", "Al Faisaly": "SA", "Al-Adalah": "SA",

    # UAE (AE additional)
    "Dubai City": "AE", "Dubai City FC": "AE", "Al Hamriyah": "AE", "Hamriyah": "AE",
    "Emirates": "AE", "Emirates Club": "AE", "Khor Fakkan": "AE", "Khor Fakkan Club": "AE",
    "Dibba Al-Fujairah": "AE", "Dibba": "AE", "Al Orooba": "AE", "Orooba": "AE",

    # ITALY (IT additional - lower leagues)
    "Castel di Sangro": "IT", "Sangiovannese": "IT", "San Giovanni": "IT",
    "Carrarese": "IT", "Carrarese Calcio": "IT", "Pro Piacenza": "IT",
    "Casertana FC": "IT", "Matera": "IT", "FC Matera": "IT", "Catanzaro": "IT",
    "Cavese": "IT", "Cavese 1919": "IT", "Bisceglie": "IT", "AS Bisceglie": "IT",

    # SPAIN (ES additional)
    "Cartagonova": "ES", "FC Cartagonova": "ES", "Cartagena B": "ES",
    "Linares": "ES", "Linares Deportivo": "ES", "Yeclano": "ES", "Yeclano Deportivo": "ES",
    "UCAM Murcia": "ES", "UCAM": "ES", "La Nucía": "ES", "CF La Nucía": "ES",

    # GERMANY (DE additional)
    "Blau-Weiß 90 Berlin": "DE", "Blau-Weiß Berlin": "DE", "BW 90 Berlin": "DE",
    "FC Hanau 93": "DE", "Hanau 93": "DE", "FK Pirmasens": "DE", "Pirmasens": "DE",
    "FSV Oggersheim": "DE", "Oggersheim": "DE", "FC Brandenburg": "DE", "Brandenburg": "DE",
    "FC Eschborn": "DE", "Eschborn": "DE", "FC Mülheim": "DE", "Mülheim": "DE",

    # AUSTRIA (AT additional)
    "ASK Voitsberg": "AT", "Voitsberg": "AT", "Gloggnitz": "AT", "SC Gloggnitz": "AT",
    "SV Ried II": "AT", "Ried II": "AT", "Austria Wien II": "AT", "Austria II": "AT",
    "Rapid Wien II": "AT", "Rapid II": "AT", "Lafnitz": "AT", "SV Lafnitz": "AT",
    "GAK": "AT", "Grazer AK": "AT", "Floridsdorfer AC": "AT", "FAC": "AT",

    # NORWAY (NO additional)
    "Drøbak/Frogn": "NO", "Drøbak": "NO", "Frogn": "NO", "Frigg": "NO", "Frigg Oslo": "NO",
    "Skeid": "NO", "Skeid Oslo": "NO", "Lyn": "NO", "Lyn Oslo": "NO",
    "Follo": "NO", "Follo FK": "NO", "Asker": "NO", "Asker Fotball": "NO",
    "Ullern": "NO", "Ullern IF": "NO", "Bærum SK": "NO", "Bærum": "NO",

    # EGYPT (EG additional)
    "Aswan": "EG", "Aswan SC": "EG", "El Mokawloon": "EG", "Arab Contractors": "EG",
    "Al Masry": "EG", "Al-Masry Club": "EG", "Tala'ea El-Gaish": "EG", "El Gaish": "EG",
    "Haras El Hodoud": "EG", "Hodoud": "EG", "Misr El Makkasa": "EG", "Makkasa": "EG",
    "Ghazl El Mahalla": "EG", "El Mahalla": "EG", "National Bank": "EG", "NBE": "EG",

    # NIGERIA (NG additional)
    "Bendel Insurance": "NG", "Bendel": "NG", "Julius Berger": "NG", "Julius Berger FC": "NG",
    "Iwuanyanwu Nationale": "NG", "Heartland": "NG", "Dolphins FC": "NG", "Dolphins": "NG",
    "El-Kanemi Warriors": "NG", "El-Kanemi": "NG", "Wikki Tourists": "NG", "Wikki": "NG",
    "Niger Tornadoes": "NG", "Tornadoes": "NG", "Gombe United": "NG", "Gombe": "NG",

    # NEPAL (NP)
    "Dhangadhi F.C.": "NP", "Dhangadhi": "NP", "Manang Marshyangdi": "NP", "Manang": "NP",
    "Three Star Club": "NP", "Three Star": "NP", "Machhindra FC": "NP", "Machhindra": "NP",

    # KOSOVO (XK)
    "Ferizaj": "XK", "KF Ferizaj": "XK", "Prishtina": "XK", "FC Prishtina": "XK",
    "Drita": "XK", "KF Drita": "XK", "Ballkani": "XK", "KF Ballkani": "XK",
    "Gjilani": "XK", "SC Gjilani": "XK", "Llapi": "XK", "KF Llapi": "XK",

    # CHINA (CN additional)
    "Gansu Tianma": "CN", "Tianma": "CN", "Hangzhou Greentown": "CN", "Greentown": "CN",
    "Qingdao Hainiu": "CN", "Qingdao": "CN", "Changchun Yatai": "CN", "Yatai": "CN",
    "Wuhan Zall": "CN", "Wuhan": "CN", "Chongqing Lifan": "CN", "Lifan": "CN",
    "Guizhou Hengfeng": "CN", "Hengfeng": "CN", "Liaoning FC": "CN", "Liaoning": "CN",
    "Yanbian Funde": "CN", "Yanbian": "CN", "Shijiazhuang Ever Bright": "CN",

    # FRANCE (FR additional - lower leagues)
    "Gueugnon": "FR", "FC Gueugnon": "FR", "INF Vichy": "FR", "Vichy": "FR",
    "Évian": "FR", "Evian": "FR", "Évian TG": "FR", "Évian Thonon": "FR",
    "Martigues": "FR", "FC Martigues": "FR", "Istres": "FR", "FC Istres": "FR",
    "Wasquehal": "FR", "Wasquehal Football": "FR", "Angoulême": "FR", "AS Angoulême": "FR",

    # BELGIUM (BE additional)
    "FC Ganshoren": "BE", "Ganshoren": "BE", "Germinal Ekeren": "BE", "Ekeren": "BE",
    "Beerschot AC": "BE", "KFC Dessel Sport": "BE", "Dessel": "BE",
    "Patro Eisden": "BE", "Eisden": "BE", "Francs Borains": "BE", "Borains": "BE",

    # SWITZERLAND (CH additional)
    "FC Zug": "CH", "Zug": "CH", "FC Biel-Bienne": "CH", "Biel": "CH",
    "SC Brühl": "CH", "Brühl": "CH", "FC Echallens": "CH", "Echallens": "CH",
    "FC Bulle": "CH", "Bulle": "CH", "Yverdon-Sport": "CH", "Yverdon": "CH",

    # GREECE (GR additional)
    "Ethnikos Asteras": "GR", "Asteras": "GR", "Kallithea FC": "GR",
    "Doxa Dramas": "GR", "Dramas": "GR", "Trikala": "GR", "AO Trikala": "GR",
    "Apollon Pontou": "GR", "Pontou": "GR", "Vyzas Megaron": "GR",

    # ENGLAND (EN additional - more non-league)
    "Halesowen Town": "EN", "Halesowen": "EN", "Harborough Town": "EN", "Harborough": "EN",
    "Ilkeston Town": "EN", "Ilkeston": "EN", "Hurstpierpoint": "EN",
    "Belstone": "EN", "Hednesford Town": "EN", "Hednesford": "EN",
    "Redditch United": "EN", "Redditch": "EN", "Stourbridge": "EN", "Stourbridge FC": "EN",
    "Stratford Town": "EN", "Stratford": "EN", "Banbury United": "EN", "Banbury": "EN",

    # SWEDEN (SE additional)
    "Högaborgs BK": "SE", "Högaborg": "SE", "IFK Sundsvall": "SE", "Sundsvall": "SE",
    "Ängelholms FF": "SE", "Ängelholm": "SE", "Qviding FIF": "SE", "Qviding": "SE",
    "Utsiktens BK": "SE", "Utsikten": "SE", "Värnamo": "SE", "IFK Värnamo": "SE",

    # DENMARK (DK additional)
    "Gladsaxe-Hero": "DK", "Gladsaxe": "DK", "Hero": "DK", "B93": "DK", "B 93": "DK",
    "AB": "DK", "Akademisk Boldklub": "DK", "B 1903": "DK", "B1903": "DK",
    "Fremad Valby": "DK", "Valby": "DK", "HIK": "DK", "Hellerup IK": "DK",

    # MOROCCO (MA additional)
    "IR Tanger": "MA", "Ittihad Tanger": "MA", "Tanger": "MA", "IRT": "MA",
    "Chabab Mohammedia": "MA", "Mohammedia": "MA", "Youssoufia Berrechid": "MA",
    "Olympic Safi": "MA", "Safi": "MA", "Rapide Oued Zem": "MA", "Oued Zem": "MA",

    # NORTHERN IRELAND (NI additional)
    "Institute": "NI", "Institute FC": "NI", "Ballymena United": "NI", "Ballymena": "NI",
    "Carrick Rangers": "NI", "Carrick": "NI", "Dungannon Swifts": "NI", "Dungannon": "NI",
    "Newry City": "NI", "Newry": "NI", "Warrenpoint Town": "NI", "Warrenpoint": "NI",

    # JAMAICA (JM)
    "Harbour View": "JM", "Harbour View FC": "JM", "Portmore United": "JM", "Portmore": "JM",
    "Arnett Gardens": "JM", "Arnett": "JM", "Waterhouse FC": "JM", "Waterhouse": "JM",
    "Cavalier FC": "JM", "Cavalier": "JM", "Tivoli Gardens": "JM", "Tivoli": "JM",

    # COSTA RICA (CR)
    "Herediano": "CR", "Club Sport Herediano": "CR", "Saprissa": "CR", "Deportivo Saprissa": "CR",
    "Alajuelense": "CR", "LD Alajuelense": "CR", "Liga Deportiva": "CR",
    "Cartaginés": "CR", "CS Cartaginés": "CR", "San Carlos": "CR", "AD San Carlos": "CR",

    # ZAMBIA (ZM)
    "Green Buffaloes": "ZM", "Buffaloes": "ZM", "ZESCO United": "ZM", "ZESCO": "ZM",
    "Power Dynamos": "ZM", "Nkana FC": "ZM", "Nkana": "ZM", "Zanaco FC": "ZM", "Zanaco": "ZM",
    "Red Arrows": "ZM", "Forest Rangers": "ZM", "Napsa Stars": "ZM",

    # AUSTRALIA (AU additional)
    "Hume City": "AU", "Hume City FC": "AU", "South Melbourne FC": "AU",
    "Heidelberg United": "AU", "Heidelberg": "AU", "Oakleigh Cannons": "AU", "Oakleigh": "AU",
    "Bentleigh Greens": "AU", "Bentleigh": "AU", "Green Gully": "AU", "Green Gully SC": "AU",

    # FINLAND (FI additional)
    "Hämeenlinna": "FI", "FC Hämeenlinna": "FI", "Mikkelin Palloilijat": "FI", "MP": "FI",
    "Haka": "FI", "FC Haka": "FI", "Honka": "FI", "FC Honka": "FI",
    "RoPS": "FI", "Rovaniemen Palloseura": "FI", "KPV": "FI", "Kokkola": "FI",

    # ITALY (IT additional)
    "Forlì": "IT", "Forli": "IT", "AC Forlì": "IT", "Ancona": "IT", "US Ancona": "IT",
    "Triestina": "IT", "US Triestina": "IT", "Gualdo": "IT", "Gualdo Casacastalda": "IT",

    # GERMANY (DE additional)
    "Germania Grasdorf": "DE", "Grasdorf": "DE", "Erzgebirge Aue": "DE",
    "VfL Wolfsburg II": "DE", "Wolfsburg II": "DE", "Bayern Munich II": "DE", "Bayern II": "DE",
    "Eintracht Frankfurt II": "DE", "Frankfurt II": "DE", "SpVgg Greuther Fürth II": "DE",

    # ISRAEL (IL additional)
    "Ironi Kiryat Shmona": "IL", "Kiryat Shmona": "IL", "Ironi Ramat HaSharon": "IL",
    "Ramat HaSharon": "IL", "Maccabi Petah Tikva": "IL", "Petah Tikva": "IL",
    "Hapoel Kfar Saba": "IL", "Kfar Saba": "IL", "Hapoel Hadera": "IL", "Hadera": "IL",
    "Hapoel Ironi Kiryat Shmona": "IL", "Bnei Sakhnin": "IL", "Sakhnin": "IL",

    # NIGERIA (NG additional)
    "Ifeanyi Ubah": "NG", "Ifeanyi Ubah FC": "NG", "MFM FC": "NG", "MFM": "NG",
    "Warri Wolves": "NG", "Warri": "NG", "Katsina United": "NG", "Katsina": "NG",

    # USA (US additional)
    "Kansas City Wizards": "US", "Wizards": "US", "MLS Pro-40": "US",
    "Tampa Bay Mutiny": "US", "Mutiny": "US", "MetroStars": "US", "NY/NJ MetroStars": "US",
    "San Jose Clash": "US", "Clash": "US", "Miami Fusion": "US", "Fusion": "US",
    "Rochester Rhinos": "US", "Rochester": "US", "Chivas USA": "US",

    # JAPAN (JP additional)
    "J.League U-22": "JP", "J.League U22": "JP", "Kyoto Purple Sanga": "JP", "Kyoto Sanga": "JP",
    "Mito HollyHock": "JP", "Mito": "JP", "Zweigen Kanazawa": "JP", "Kanazawa": "JP",
    "Tochigi SC": "JP", "Tochigi": "JP", "Ehime FC": "JP", "Ehime": "JP",
    "Giravanz Kitakyushu": "JP", "Kitakyushu": "JP", "Tokyo Verdy": "JP", "Verdy": "JP",

    # KAZAKHSTAN (KZ)
    "Kairat": "KZ", "FC Kairat": "KZ", "Kairat Almaty": "KZ", "Astana": "KZ", "FC Astana": "KZ",
    "Tobol": "KZ", "FC Tobol": "KZ", "Shakhter Karagandy": "KZ", "Karagandy": "KZ",
    "Ordabasy": "KZ", "FC Ordabasy": "KZ", "Aktobe": "KZ", "FC Aktobe": "KZ",

    # TURKEY (TR additional)
    "Kayseri Erciyesspor": "TR", "Erciyesspor": "TR", "Kayseri": "TR",
    "Mersin Idman Yurdu": "TR", "Mersin": "TR", "Kardemir Karabük": "TR",

    # HONG KONG (HK)
    "Kitchee": "HK", "Kitchee SC": "HK", "Eastern": "HK", "Eastern SC": "HK",
    "South China": "HK", "South China AA": "HK", "Pegasus": "HK", "TSW Pegasus": "HK",

    # TUNISIA (TN additional)
    "JSK (Kairouan)": "TN", "JS Kairouan": "TN", "Kairouan": "TN",
    "CA Bizertin": "TN", "Bizertin": "TN", "AS Marsa": "TN", "Marsa": "TN",

    # BELGIUM (BE additional)
    "La Louvière": "BE", "RAA Louvièroise": "BE", "Louvière": "BE",
    "Lierse SK": "BE", "KSK Lierse": "BE", "KV Turnhout": "BE", "Turnhout": "BE",

    # NETHERLANDS (NL additional)
    "KVV Losser": "NL", "Losser": "NL", "Kozakken Boys": "NL",
    "Quick Boys": "NL", "ASWH": "NL", "Barendrecht": "NL", "BVV Barendrecht": "NL",

    # FINLAND (FI additional)
    "Klubi 04": "FI", "Klubi-04": "FI", "Kuusysi": "FI", "Kuusysi Lahti": "FI",
    "Reipas Lahti": "FI", "Reipas": "FI", "OPS": "FI", "Oulun Palloseura": "FI",
    "Jazz Pori": "FI", "FC Jazz": "FI", "Jaro": "FI", "FF Jaro": "FI",

    # ITALY (IT additional)
    "L'Aquila": "IT", "L'Aquila Calcio": "IT", "Aquila": "IT",
    "Paganese": "IT", "Paganese Calcio 1926": "IT", "Messina": "IT", "ACR Messina": "IT",

    # GERMANY (DE additional - typos and more)
    "Erzgebirge Auge": "DE", "Köpenicker SC": "DE", "Köpenick": "DE",
    "Lichterfelder FC": "DE", "Lichterfelde": "DE", "Spandauer SV": "DE", "Spandau": "DE",
    "Tennis Borussia": "DE", "TeBe": "DE", "Türkiyemspor Berlin": "DE", "Türkiyemspor": "DE",

    # BRAZIL (BR additional)
    "Joinville": "BR", "Joinville EC": "BR", "JEC": "BR",
    "Paraná": "BR", "Paraná Clube": "BR", "Figueirense": "BR", "Figueirense FC": "BR",
    "Metropolitano": "BR", "Metropolitano SC": "BR", "Marcílio Dias": "BR",

    # FRANCE (FR additional)
    "Louhans-Cuiseaux": "FR", "Louhans": "FR", "Cuiseaux": "FR",
    "Limonest": "FR", "FC Limonest": "FR", "Villefranche": "FR", "FC Villefranche": "FR",

    # COLOMBIA (CO additional)
    "Lanceros Boyacá": "CO", "Lanceros": "CO", "Boyacá": "CO",
    "Patriotas Boyacá": "CO", "Patriotas": "CO", "Rionegro Águilas": "CO", "Águilas Doradas": "CO",

    # RUSSIA (RU additional)
    "FC Yuri Gagarin": "RU", "Yuri Gagarin": "RU", "Torpedo Kutaisi": "GE",

    # ENGLAND (EN additional)
    "Kings Langley": "EN", "Kings Langley FC": "EN", "Biggleswade Town": "EN", "Biggleswade": "EN",
    "Royston Town": "EN", "Royston": "EN", "Hitchin Town": "EN", "Hitchin": "EN",

    # KUWAIT (KW)
    "Kuwait SC": "KW", "Kuwait Sport Club": "KW", "Al-Arabi": "KW", "Al Arabi Kuwait": "KW",
    "Al-Qadsia": "KW", "Qadsia": "KW", "Kazma": "KW", "Kazma SC": "KW",

    # ICELAND (IS)
    "Knattspyrnudeild UMFG": "IS", "UMFG": "IS", "Grindavík": "IS", "UMF Grindavík": "IS",
    "Víkingur Reykjavík": "IS", "Víkingur": "IS", "Valur": "IS", "Valur Reykjavík": "IS",
    "Breiðablik": "IS", "KR Reykjavík": "IS", "KR": "IS", "FH Hafnarfjörður": "IS", "FH": "IS",

    # RÉUNION (FR overseas)
    "JS Saint-Pierroise": "FR", "Saint-Pierroise": "FR", "SS Jeanne d'Arc": "FR",

    # OTHER
    "Celtic": "SC", "Rangers": "SC",

    # INDONESIA (ID)
    "Madura United": "ID", "Madura United FC": "ID", "Persib Bandung": "ID", "Persib": "ID",
    "Persija Jakarta": "ID", "Persija": "ID", "Arema FC": "ID", "Arema Malang": "ID",
    "Bali United": "ID", "Bali United FC": "ID", "PSM Makassar": "ID", "PSM": "ID",
    "Persebaya Surabaya": "ID", "Persebaya": "ID", "Semen Padang": "ID", "Semen Padang FC": "ID",
    "PSIS Semarang": "ID", "PSIS": "ID", "Persela Lamongan": "ID", "Persela": "ID",
    "Persipura Jayapura": "ID", "Persipura": "ID", "PS Barito Putera": "ID", "Barito Putera": "ID",
    "Borneo FC": "ID", "Pusamania Borneo": "ID", "Persik Kediri": "ID", "Persik": "ID",
    "PSS Sleman": "ID", "PSS": "ID", "Persiraja Banda Aceh": "ID", "Persiraja": "ID",
    "Persis Solo": "ID", "Persis": "ID", "PSMS Medan": "ID", "PSMS": "ID",
    "Bhayangkara FC": "ID", "Bhayangkara": "ID", "Dewa United": "ID", "Rans Nusantara": "ID",
    "RANS Cilegon FC": "ID", "Cilegon": "ID",

    # THAILAND (TH)
    "Muangthong United": "TH", "Muangthong": "TH", "Buriram United": "TH", "Buriram": "TH",
    "Bangkok United": "TH", "Bangkok Glass": "TH", "Chonburi FC": "TH", "Chonburi": "TH",
    "Port FC": "TH", "Port Thailand": "TH", "SCG Muangthong": "TH",
    "BG Pathum United": "TH", "BG Pathum": "TH", "Pathum United": "TH",
    "Ratchaburi FC": "TH", "Ratchaburi": "TH", "Chiangrai United": "TH", "Chiangrai": "TH",
    "Nakhon Ratchasima": "TH", "Korat": "TH", "Suphanburi FC": "TH", "Suphanburi": "TH",
    "Police Tero": "TH", "Police Tero FC": "TH", "True Bangkok United": "TH",
    "Singha Chiangrai United": "TH", "PT Prachuap": "TH", "Prachuap": "TH",
    "Samut Prakan": "TH", "Samut Prakan City": "TH", "Khon Kaen United": "TH", "Khon Kaen": "TH",

    # MALAYSIA (MY)
    "Pahang": "MY", "Pahang FA": "MY", "Sri Pahang FC": "MY", "Johor Darul Ta'zim": "MY",
    "JDT": "MY", "Johor": "MY", "Selangor": "MY", "Selangor FA": "MY", "Selangor FC": "MY",
    "Perak": "MY", "Perak FA": "MY", "Perak FC": "MY", "Kedah": "MY", "Kedah FA": "MY",
    "Kelantan": "MY", "Kelantan FA": "MY", "Terengganu": "MY", "Terengganu FA": "MY",
    "Negeri Sembilan": "MY", "NS Matrix": "MY", "Sabah": "MY", "Sabah FA": "MY",
    "Sarawak": "MY", "Sarawak FA": "MY", "Kuala Lumpur": "MY", "KL City": "MY",
    "Penang": "MY", "Penang FA": "MY", "Melaka": "MY", "Melaka United": "MY",
    "Felda United": "MY", "PKNS": "MY", "PKNS FC": "MY", "ATM FA": "MY",
    "Armed Forces FC": "MY", "PDRM FA": "MY", "PDRM": "MY",

    # SINGAPORE (SG)
    "Lion City Sailors": "SG", "Sailors": "SG", "Albirex Niigata (S)": "SG",
    "Tampines Rovers": "SG", "Tampines": "SG", "Geylang International": "SG", "Geylang": "SG",
    "Hougang United": "SG", "Hougang": "SG", "Home United": "SG", "Warriors FC": "SG",
    "Balestier Khalsa": "SG", "Balestier": "SG", "Young Lions": "SG", "Tanjong Pagar": "SG",
    "Woodlands Wellington": "SG", "Woodlands": "SG", "Singapore Armed Forces": "SG", "SAFFC": "SG",

    # VIETNAM (VN)
    "Hoàng Anh Gia Lai": "VN", "HAGL": "VN", "Gia Lai": "VN",
    "Hà Nội FC": "VN", "Hanoi FC": "VN", "Viettel FC": "VN", "Viettel": "VN",
    "Sài Gòn FC": "VN", "Saigon FC": "VN", "Bình Dương": "VN", "Becamex Binh Duong": "VN",
    "Hải Phòng FC": "VN", "Hai Phong": "VN", "SHB Đà Nẵng": "VN", "Da Nang": "VN",
    "Nam Định FC": "VN", "Nam Dinh": "VN", "Song Lam Nghe An": "VN", "SLNA": "VN",
    "Thanh Hóa FC": "VN", "Thanh Hoa": "VN", "Than Quang Ninh": "VN", "Quang Ninh": "VN",

    # PHILIPPINES (PH)
    "Kaya FC": "PH", "Kaya-Iloilo": "PH", "Ceres-Negros": "PH", "Ceres FC": "PH",
    "Azkals Development Team": "PH", "ADT": "PH", "Stallion Laguna": "PH", "Stallion": "PH",
    "Global Makati": "PH", "Global Cebu": "PH", "Davao Aguilas": "PH", "Aguilas": "PH",
    "United City FC": "PH", "United City": "PH", "Maharlika Manila": "PH",

    # MYANMAR (MM)
    "Yangon United": "MM", "Yangon": "MM", "Shan United": "MM", "Shan": "MM",
    "Ayeyawady United": "MM", "Ayeyawady": "MM", "Magwe FC": "MM", "Magwe": "MM",

    # CAMBODIA (KH)
    "Preah Khan Reach Svay Rieng": "KH", "Svay Rieng": "KH", "Phnom Penh Crown": "KH",
    "Boeung Ket": "KH", "Boeung Ket FC": "KH", "Nagaworld FC": "KH", "Nagaworld": "KH",

    # LAOS (LA)
    "Lao Toyota FC": "LA", "Lao Toyota": "LA", "Master 7": "LA",

    # UZBEKISTAN (UZ)
    "Pakhtakor": "UZ", "Pakhtakor Tashkent": "UZ", "Bunyodkor": "UZ", "FC Bunyodkor": "UZ",
    "Lokomotiv Tashkent": "UZ", "Lokomotiv (Tashkent)": "UZ", "Nasaf Qarshi": "UZ", "Nasaf": "UZ",
    "AGMK": "UZ", "AGMK Olmaliq": "UZ",

    # TAJIKISTAN (TJ)
    "Istiklol Dushanbe": "TJ", "Istiklol": "TJ", "FC Istiklol": "TJ",

    # BANGLADESH (BD)
    "Abahani Limited Dhaka": "BD", "Abahani Dhaka": "BD", "Abahani": "BD",
    "Mohammedan SC (Dhaka)": "BD", "Mohammedan Dhaka": "BD", "Bashundhara Kings": "BD",
    "Bashundhara": "BD", "Sheikh Jamal DC": "BD", "Dhaka Abahani": "BD",

    # SRI LANKA (LK)
    "Blue Star SC": "LK", "Blue Star": "LK", "Colombo FC": "LK", "Renown SC": "LK",
    "Saunders SC": "LK", "Saunders": "LK", "Army SC": "LK",

    # PAKISTAN (PK)
    "Pakistan Army": "PK", "KRL": "PK", "Khan Research Laboratories": "PK",
    "WAPDA": "PK", "PIA": "PK", "Pakistan International Airlines": "PK",

    # MALDIVES (MV)
    "Maziya S&RC": "MV", "Maziya": "MV", "TC Sports Club": "MV", "New Radiant": "MV",
    "Club Eagles": "MV", "Eagles": "MV", "Velencia": "MV",

    # MONGOLIA (MN)
    "Ulaanbaatar City": "MN", "Ulaanbaatar": "MN", "Erchim": "MN", "FC Erchim": "MN",

    # BHUTAN (BT)
    "Thimphu City": "BT", "Thimphu": "BT", "Paro FC": "BT", "Paro": "BT",

    # BRUNEI (BN)
    "DPMM FC": "BN", "DPMM": "BN", "MS ABDB": "BN", "Brunei DPMM": "BN",

    # TIMOR-LESTE (TL)
    "Karketu Dili": "TL", "Dili": "TL", "Sport Laulara e Benfica": "TL",

    # AFGHANISTAN (AF)
    "Shaheen Asmayee": "AF", "Shaheen": "AF", "De Maiwand Atalan": "AF", "Simorgh Alborz": "AF",

    # TURKMENISTAN (TM)
    "Altyn Asyr": "TM", "FC Altyn Asyr": "TM", "Ahal FC": "TM", "Ahal": "TM",

    # KYRGYZSTAN (KG)
    "Dordoi Bishkek": "KG", "Dordoi": "KG", "Abdish-Ata Kant": "KG", "Abdish-Ata": "KG",

    # GUAM (GU)
    "Rovers FC (Guam)": "GU", "Guam Shipyard": "GU",

    # TAIWAN (TW)
    "Taipower": "TW", "Taiwan Power Company": "TW", "Tatung FC": "TW", "Tatung": "TW",

    # NORTH KOREA (KP)
    "April 25 SC": "KP", "April 25": "KP", "Pyongyang City": "KP",

    # BAHRAIN (BH)
    "Riffa": "BH", "Al-Riffa": "BH", "Riffa SC": "BH", "Muharraq": "BH", "Al-Muharraq": "BH",
    "Manama Club": "BH", "Manama": "BH", "East Riffa": "BH",

    # OMAN (OM)
    "Al-Seeb": "OM", "Seeb": "OM", "Dhofar Club": "OM", "Dhofar": "OM",
    "Sur SC": "OM", "Sur": "OM", "Al-Oruba": "OM",

    # JORDAN (JO)
    "Al-Faisaly (Jordan)": "JO", "Al-Faisaly Amman": "JO", "Al-Wehdat": "JO", "Wehdat": "JO",
    "Shabab Al-Ordon": "JO", "Al-Jazeera (Amman)": "JO", "Jazeera Amman": "JO",

    # LEBANON (LB)
    "Nejmeh SC": "LB", "Nejmeh": "LB", "Al-Ansar": "LB", "Ansar": "LB",
    "Al-Ahed": "LB", "Ahed": "LB", "Racing Beirut": "LB",

    # SYRIA (SY)
    "Al-Jaish Damascus": "SY", "Al-Jaish": "SY", "Al-Wahda Damascus": "SY", "Wahda Damascus": "SY",
    "Tishreen SC": "SY", "Tishreen": "SY", "Al-Wathba": "SY",

    # PALESTINE (PS)
    "Hilal Al-Quds": "PS", "Hilal": "PS", "Shabab Al-Khalil": "PS", "Khalil": "PS",

    # IRAQ (IQ)
    "Al-Shorta": "IQ", "Shorta": "IQ", "Al-Zawraa": "IQ", "Zawraa": "IQ",
    "Air Force Club": "IQ", "Al-Quwa Al-Jawiya": "IQ", "Erbil SC": "IQ", "Erbil": "IQ",

    # YEMEN (YE)
    "Al-Tilal": "YE", "Tilal": "YE", "Al-Ahli Sanaa": "YE", "Ahli Sanaa": "YE",

    # ADDITIONAL OBSCURE CLUBS (various countries)
    # Germany
    "MSV Normannia 08": "DE", "Normannia 08": "DE", "Meidericher SV": "DE",
    "OSC Bremerhaven": "DE", "Bremerhaven": "DE",
    # England
    "Maidstone United": "EN", "Maidstone": "EN", "Milton Keynes Dons": "EN",
    "Nantwich Town": "EN", "Nantwich": "EN", "Petersfield Town": "EN", "Petersfield": "EN",
    # France
    "Maubeuge": "FR", "US Maubeuge": "FR", "Mulhouse": "FR", "FC Mulhouse": "FR",
    # Italy
    "Morro d'Oro": "IT", "Morro": "IT", "Nuorese": "IT", "Nuorese Calcio": "IT",
    "Pavia": "IT", "FC Pavia": "IT",
    # Belgium
    "Mandel United": "BE", "Mandel": "BE",
    # Portugal
    "Maia": "PT", "FC Maia": "PT", "Naval": "PT", "Naval 1º de Maio": "PT",
    # Brazil
    "Nova Iguaçu": "BR", "Nova Iguacu": "BR", "Nova Iguaçu FC": "BR",
    # Greece
    "Paniliakos": "GR", "Paniliakos FC": "GR",
    # Cyprus
    "Pezoporikos": "CY", "Pezoporikos Larnaca": "CY",
    # Qatar
    "Mesaimeer": "QA", "Mesaimeer SC": "QA",
    # USA
    "Phoenix Rising": "US", "Phoenix Rising FC": "US", "North Texas SC": "US",
    "Palm Beach Stars": "US",
    # India
    "North East United": "IN", "North East United FC": "IN",
    # Australia
    "Parramatta Power": "AU", "Parramatta": "AU",
    # New Zealand
    "North Shore United": "NZ", "North Shore": "NZ",
    # Denmark
    "Nørresundby": "DK", "Nørresundby FB": "DK",
    # Finland
    "MyPa": "FI", "MyPa-47": "FI", "Myllykosken Pallo": "FI",
    # Switzerland
    "Bulova SA": "CH", "FC Bulova": "CH",
    # Ukraine
    "Metalurh Zaporizhzhia": "UA", "Metalurh": "UA", "Metalurg Zaporizhzhia": "UA",

    # MORE ADDITIONAL CLUBS
    # Poland
    "Pogoń Siedlce": "PL", "Siedlce": "PL",
    # Italy
    "Prato": "IT", "AC Prato": "IT", "Rondinella": "IT", "AS Rondinella": "IT",
    # India
    "Pune City": "IN", "FC Pune City": "IN",
    # Brazil
    "Pão de Açúcar": "BR", "Pao de Acucar": "BR",
    # Germany
    "RSV Göttingen 05": "DE", "Göttingen 05": "DE", "Rheydter SV": "DE", "Rheydt": "DE",
    "Rotenburger SV": "DE", "Rotenburg": "DE", "SC Halberg Brebach": "DE", "Brebach": "DE",
    "SC Herford": "DE", "Herford": "DE", "SC Kapellen-Erft": "DE", "Kapellen": "DE",
    "SC Lüstringen": "DE", "Lüstringen": "DE", "SC Oelde 1919": "DE", "Oelde": "DE",
    "SC Pfullendorf": "DE", "Pfullendorf": "DE", "SC Tasmania 1900 Berlin": "DE",
    "Tasmania Berlin": "DE", "SC Union Nettetal": "DE", "Nettetal": "DE",
    "SC Vier-und Marschlande": "DE", "Marschlande": "DE", "SC Weismain": "DE", "Weismain": "DE",
    "SGV Freiberg": "DE", "Freiberg": "DE", "SSV Dillingen": "DE", "Dillingen": "DE",
    # Cameroon
    "Racing Bafoussam": "CM", "Bafoussam": "CM",
    # USA
    "Rayo OKC": "US", "OKC": "US",
    # Ghana
    "Real Tamale United": "GH", "Tamale": "GH",
    # North Macedonia
    "Renova": "MK", "FK Renova": "MK",
    # England
    "Royton Town": "EN", "Royton": "EN",
    # Sweden
    "Råå IF": "SE", "Råå": "SE",
    # Austria
    "SAK Klagenfurt": "AT", "SK VÖEST Linz": "AT", "VÖEST Linz": "AT",
    "SC-ESV Parndorf": "AT", "Parndorf": "AT",
    # Netherlands
    "SC Enschede": "NL", "Enschede": "NL",

    # EVEN MORE OBSCURE CLUBS
    # Germany
    "SSVg Velbert": "DE", "Velbert": "DE", "SV Göppingen": "DE", "Göppingen": "DE",
    "SV Heidingsfeld": "DE", "Heidingsfeld": "DE", "SV Langensteinbach": "DE", "Langensteinbach": "DE",
    "SV Rhenania Bessenich": "DE", "Bessenich": "DE", "SV Rot": "DE", "Rot": "DE",
    "SV Röchling Völklingen": "DE", "Völklingen": "DE", "SV Schwetzingen": "DE", "Schwetzingen": "DE",
    "SV Viktoria Goch": "DE", "Goch": "DE", "SV Wermelskirchen": "DE", "Wermelskirchen": "DE",
    "SV Zweckel": "DE", "Zweckel": "DE",
    # Austria
    "SSW Innsbruck": "AT", "Innsbruck": "AT", "SV Rothenthurn": "AT", "Rothenthurn": "AT",
    "SV Spittal": "AT", "Spittal": "AT",
    # USA
    "Sacramento Republic": "US", "Sacramento": "US", "San Diego Sockers": "US",
    "San Diego Sockers (indoor)": "US",
    # France
    "Saint-Georges": "FR", "Saint-Seurin": "FR",
    # Finland
    "SalPa": "FI", "Salo": "FI",
    # Argentina
    "San Isidro": "AR",
    # Italy
    "Sant'Angelo": "IT", "SantAngelo": "IT",
    # El Salvador
    "Santa Ana": "SV", "CD Santa Ana": "SV",
    # Chile
    "Santiago Wanderers": "CL", "Wanderers": "CL",
    # Hong Kong
    "Seiko": "HK", "Seiko SA": "HK",
    # Norway
    "Selbak IF": "NO", "Selbak": "NO",
    # China
    "Shenzhen Jianlibao": "CN", "Jianlibao": "CN",
    # North Macedonia
    "Shkëndija": "MK", "FK Shkëndija": "MK",
    # Ethiopia
    "Sidama Coffee": "ET", "Sidama": "ET",
    # Canada
    "Sigma FC": "CA",

    # FINAL BATCH OF OBSCURE CLUBS
    # French Guiana
    "Sinnamary": "GF", "ASC Sinnamary": "GF",
    # Albania
    "Skënderbeu": "AL", "KF Skënderbeu": "AL",
    # Italy
    "Sona": "IT", "ASD Sona": "IT", "Tor di Quinto": "IT", "Torres": "IT", "Torres Sassari": "IT",
    # Hong Kong
    "Southern": "HK", "Southern District": "HK",
    # Germany
    "SpVgg Altenerding": "DE", "Altenerding": "DE", "SpVgg Landshut": "DE", "Landshut": "DE",
    "SpVgg Ludwigsburg": "DE", "Ludwigsburg": "DE", "SpVgg Stegaurach": "DE", "Stegaurach": "DE",
    "Sportfreunde Gladbeck": "DE", "Gladbeck": "DE", "TSF Ditzingen": "DE", "Ditzingen": "DE",
    "TSG Backnang": "DE", "Backnang": "DE", "TSG Pfeddersheim": "DE", "Pfeddersheim": "DE",
    "TSG Rheda": "DE", "Rheda": "DE", "TSG Wörsdorf": "DE", "Wörsdorf": "DE",
    "TSV 1860 Rosenheim": "DE", "Rosenheim": "DE", "TSV Benningen": "DE", "Benningen": "DE",
    "TSV Crailsheim": "DE", "Crailsheim": "DE", "TSV DUWO 08": "DE", "DUWO 08": "DE",
    "TURA Untermünkheim": "DE", "Untermünkheim": "DE",
    # Lesotho
    "Stop Out": "LS", "Stop Out FC": "LS",
    # England
    "Stowmarket Town": "EN", "Stowmarket": "EN", "Tiverton Town": "EN", "Tiverton": "EN",
    # Finland
    "TPV": "FI", "TPV Tampere": "FI",
    # Estonia
    "Tallinna Kalev Juunior": "EE", "Kalev": "EE",
    # Slovakia
    "Tatran Prešov": "SK", "Prešov": "SK",
    # China
    "Tianjin Tianhai": "CN", "Tianhai": "CN",
    # Russia
    "Tosno": "RU", "FC Tosno": "RU",
    # France
    "Toulon": "FR", "SC Toulon": "FR", "Tours": "FR", "Tours FC": "FR",
    # San Marino
    "Tre Penne": "SM", "SP Tre Penne": "SM",
    # Norway
    "Trosvik IF": "NO", "Trosvik": "NO",
    # Germany
    "TuS Lingen": "DE", "Lingen": "DE", "TuS Warstein": "DE", "Warstein": "DE",
    "Türk Gücü München": "DE", "Türk Gücü": "DE", "Union Salzgitter": "DE", "Salzgitter": "DE",
    "VfB Altenhausen": "DE", "Altenhausen": "DE", "VfB Gaggenau": "DE", "Gaggenau": "DE",
    "VfB Speldorf": "DE", "Speldorf": "DE", "VfL 06 Benrath": "DE", "Benrath": "DE",
    "VfL Gevelsberg": "DE", "Gevelsberg": "DE", "VfL Kirchheim/Teck": "DE", "Kirchheim": "DE",
    "VfR Hettenleidelheim": "DE", "Hettenleidelheim": "DE", "Viktoria 02": "DE",
    "Viktoria Aschaffenburg": "DE", "Aschaffenburg": "DE",
    # Luxembourg
    "UT Pétange": "LU", "Pétange": "LU",
    # South Korea
    "Ulsan HD": "KR", "Ulsan": "KR",
    # Chile
    "Universidad de Chile": "CL", "U de Chile": "CL",
    # Czech Republic
    "VTJ Karlovy Vary": "CZ", "Karlovy Vary": "CZ",
    # Tajikistan
    "Vakhsh Kourgan‑Tyube": "TJ", "Vakhsh": "TJ",
    # Italy
    "Val di Sangro": "IT", "Villa Nova": "IT",
    # China
    "Vanguard Huandao": "CN", "Huandao": "CN",
    # Mexico
    "Venados Yucatán": "MX", "Venados": "MX", "Veracruz": "MX", "Tiburones Rojos": "MX",
    # Switzerland
    "Vevey Sports": "CH", "Vevey": "CH",
    # Austria
    "VfB Mödling": "AT", "Mödling": "AT",
    # Lithuania
    "Vilnius": "LT", "FK Vilnius": "LT",
    # Vietnam
    "Vissai Ninh Bình": "VN", "Ninh Bình": "VN",

    # LAST FEW CLUBS
    # Sweden
    "Väsby United": "SE", "Väsby": "SE",
    # Argentina (variant spelling)
    "Vélez Sársfield": "AR",
    # Austria
    "WSG Radenthein": "AT", "Radenthein": "AT",
    # Germany
    "Wedeler TSV": "DE", "Wedel": "DE", "Westfalia Herne": "DE", "Herne": "DE",
    # Australia
    "Werribee City": "AU", "Werribee": "AU",
    # England
    "Workington Reds": "EN", "Workington": "EN",
    # Iceland
    "ÍBV": "IS", "ÍBV Vestmannaeyjar": "IS",
    # Turkey (variant spelling)
    "İstanbulspor": "TR",
    # Poland (variant spelling)
    "ŁKS Łódź": "PL", "LKS Lodz": "PL",
}

COUNTRY_FLAGS = {
    "EN": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "ES": "🇪🇸", "IT": "🇮🇹", "DE": "🇩🇪", "FR": "🇫🇷",
    "PT": "🇵🇹", "NL": "🇳🇱", "BE": "🇧🇪", "SC": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "TR": "🇹🇷",
    "RU": "🇷🇺", "UA": "🇺🇦", "GR": "🇬🇷", "HR": "🇭🇷", "RS": "🇷🇸",
    "CH": "🇨🇭", "AT": "🇦🇹", "PL": "🇵🇱", "CZ": "🇨🇿", "SE": "🇸🇪",
    "NO": "🇳🇴", "DK": "🇩🇰", "BR": "🇧🇷", "AR": "🇦🇷", "US": "🇺🇸",
    "CA": "🇨🇦", "MX": "🇲🇽", "CN": "🇨🇳", "JP": "🇯🇵", "KR": "🇰🇷",
    "SA": "🇸🇦", "AE": "🇦🇪", "QA": "🇶🇦", "AU": "🇦🇺", "IL": "🇮🇱",
    "CY": "🇨🇾", "RO": "🇷🇴", "BG": "🇧🇬", "HU": "🇭🇺", "WA": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    # Additional flags
    "SK": "🇸🇰", "NG": "🇳🇬", "SN": "🇸🇳", "MA": "🇲🇦", "EG": "🇪🇬",
    "ZA": "🇿🇦", "GH": "🇬🇭", "CI": "🇨🇮", "CM": "🇨🇲", "DZ": "🇩🇿",
    "TN": "🇹🇳", "NI": "🇬🇧", "IE": "🇮🇪", "CO": "🇨🇴", "AM": "🇦🇲",
    "VE": "🇻🇪", "IN": "🇮🇳", "PE": "🇵🇪", "BJ": "🇧🇯", "LR": "🇱🇷",
    "IR": "🇮🇷", "NZ": "🇳🇿", "LU": "🇱🇺", "GI": "🇬🇮", "FI": "🇫🇮",
    "PY": "🇵🇾", "NP": "🇳🇵", "XK": "🇽🇰", "JM": "🇯🇲", "CR": "🇨🇷", "ZM": "🇿🇲",
    "KZ": "🇰🇿", "HK": "🇭🇰", "KW": "🇰🇼", "IS": "🇮🇸", "GE": "🇬🇪",
    # Southeast Asia
    "ID": "🇮🇩", "TH": "🇹🇭", "MY": "🇲🇾", "SG": "🇸🇬", "VN": "🇻🇳",
    "PH": "🇵🇭", "MM": "🇲🇲", "KH": "🇰🇭", "LA": "🇱🇦", "BN": "🇧🇳",
    "TL": "🇹🇱",
    # Central Asia
    "UZ": "🇺🇿", "TJ": "🇹🇯", "TM": "🇹🇲", "KG": "🇰🇬", "AF": "🇦🇫",
    # South Asia
    "BD": "🇧🇩", "LK": "🇱🇰", "PK": "🇵🇰", "MV": "🇲🇻", "BT": "🇧🇹",
    # East Asia
    "MN": "🇲🇳", "TW": "🇹🇼", "KP": "🇰🇵", "GU": "🇬🇺",
    # Middle East
    "BH": "🇧🇭", "OM": "🇴🇲", "JO": "🇯🇴", "LB": "🇱🇧", "SY": "🇸🇾",
    "PS": "🇵🇸", "IQ": "🇮🇶", "YE": "🇾🇪",
    # Balkans
    "MK": "🇲🇰",
    # Central America & South America
    "SV": "🇸🇻", "CL": "🇨🇱",
    # Africa
    "ET": "🇪🇹", "LS": "🇱🇸",
    # Balkans & Eastern Europe
    "AL": "🇦🇱", "EE": "🇪🇪",
    # French overseas
    "GF": "🇬🇫",
    # More European
    "SM": "🇸🇲", "LT": "🇱🇹",
}


def supabase_request(method, endpoint, data=None):
    """Make a request to Supabase REST API."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"

    if method == "GET":
        resp = requests.get(url, headers=headers)
    elif method == "PATCH":
        headers["Prefer"] = "return=minimal"
        resp = requests.patch(url, headers=headers, json=data)

    return resp


def guess_country(club_name: str) -> tuple[str, str]:
    """Return (country_code, country_flag) for a club name."""
    # Exact match
    if club_name in CLUB_COUNTRIES:
        code = CLUB_COUNTRIES[club_name]
        return code, COUNTRY_FLAGS.get(code, "")

    # Partial match
    club_lower = club_name.lower()
    for known_club, code in CLUB_COUNTRIES.items():
        if known_club.lower() in club_lower or club_lower in known_club.lower():
            return code, COUNTRY_FLAGS.get(code, "")

    return "", ""


def fix_missing_countries():
    """Fetch entries with missing country data and update them."""
    print("Fetching career entries with missing country codes...")

    # Get entries with empty country_code
    resp = supabase_request("GET", "career_entries?country_code=eq.&select=id,club")

    if resp.status_code != 200:
        print(f"Error fetching entries: {resp.status_code} {resp.text}")
        return

    entries = resp.json()
    print(f"Found {len(entries)} entries with missing country codes")

    if not entries:
        print("No entries to fix!")
        return

    # Group by country for batch updates
    updates_by_country = {}
    unmatched = []

    for entry in entries:
        club = entry["club"]
        code, flag = guess_country(club)

        if code:
            key = (code, flag)
            if key not in updates_by_country:
                updates_by_country[key] = []
            updates_by_country[key].append(entry["id"])
        else:
            unmatched.append(club)

    # Perform updates
    total_updated = 0
    for (code, flag), ids in updates_by_country.items():
        print(f"Updating {len(ids)} entries with country {code} {flag}...")

        # Update in batches of 100
        for i in range(0, len(ids), 100):
            batch_ids = ids[i:i+100]
            id_filter = ",".join(batch_ids)

            resp = supabase_request(
                "PATCH",
                f"career_entries?id=in.({id_filter})",
                {"country_code": code, "country_flag": flag}
            )

            if resp.status_code in (200, 204):
                total_updated += len(batch_ids)
            else:
                print(f"Error updating batch: {resp.status_code} {resp.text}")

    print(f"\n=== Results ===")
    print(f"Updated: {total_updated} entries")
    print(f"Unmatched clubs: {len(set(unmatched))}")

    if unmatched:
        print("\nSample unmatched clubs (add these to CLUB_COUNTRIES):")
        for club in sorted(set(unmatched))[:30]:
            print(f"  - {club}")


if __name__ == "__main__":
    if not SUPABASE_KEY:
        print("Error: SUPABASE_SERVICE_KEY not set in .env")
        exit(1)

    fix_missing_countries()
