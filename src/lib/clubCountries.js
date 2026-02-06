/**
 * Club to Country mapping for accurate flag display
 * This overrides any incorrect flags from the database
 */

// Country code to flag emoji mapping
const FLAGS = {
  EN: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", // England
  SC: "🏴󠁧󠁢󠁳󠁣󠁴󠁿", // Scotland
  WA: "🏴󠁧󠁢󠁷󠁬󠁳󠁿", // Wales
  ES: "🇪🇸", // Spain
  DE: "🇩🇪", // Germany
  IT: "🇮🇹", // Italy
  FR: "🇫🇷", // France
  NL: "🇳🇱", // Netherlands
  PT: "🇵🇹", // Portugal
  BR: "🇧🇷", // Brazil
  AR: "🇦🇷", // Argentina
  TR: "🇹🇷", // Turkey
  GR: "🇬🇷", // Greece
  RU: "🇷🇺", // Russia
  UA: "🇺🇦", // Ukraine
  BE: "🇧🇪", // Belgium
  CH: "🇨🇭", // Switzerland
  AT: "🇦🇹", // Austria
  PL: "🇵🇱", // Poland
  CZ: "🇨🇿", // Czech Republic
  HR: "🇭🇷", // Croatia
  RS: "🇷🇸", // Serbia
  RO: "🇷🇴", // Romania
  BG: "🇧🇬", // Bulgaria
  DK: "🇩🇰", // Denmark
  SE: "🇸🇪", // Sweden
  NO: "🇳🇴", // Norway
  FI: "🇫🇮", // Finland
  IE: "🇮🇪", // Ireland
  MX: "🇲🇽", // Mexico
  US: "🇺🇸", // USA
  JP: "🇯🇵", // Japan
  CN: "🇨🇳", // China
  KR: "🇰🇷", // South Korea
  AU: "🇦🇺", // Australia
  SA: "🇸🇦", // Saudi Arabia
  AE: "🇦🇪", // UAE
  QA: "🇶🇦", // Qatar
  EG: "🇪🇬", // Egypt
  MA: "🇲🇦", // Morocco
  NG: "🇳🇬", // Nigeria
  ZA: "🇿🇦", // South Africa
  CO: "🇨🇴", // Colombia
  CL: "🇨🇱", // Chile
  UY: "🇺🇾", // Uruguay
  PY: "🇵🇾", // Paraguay
  PE: "🇵🇪", // Peru
  EC: "🇪🇨", // Ecuador
  VE: "🇻🇪", // Venezuela
  IL: "🇮🇱", // Israel
  CY: "🇨🇾", // Cyprus
  SK: "🇸🇰", // Slovakia
  SI: "🇸🇮", // Slovenia
  HU: "🇭🇺", // Hungary
  BA: "🇧🇦", // Bosnia
  MK: "🇲🇰", // North Macedonia
  AL: "🇦🇱", // Albania
  XK: "🇽🇰", // Kosovo
  ME: "🇲🇪", // Montenegro
  LV: "🇱🇻", // Latvia
  LT: "🇱🇹", // Lithuania
  EE: "🇪🇪", // Estonia
  BY: "🇧🇾", // Belarus
  KZ: "🇰🇿", // Kazakhstan
  UZ: "🇺🇿", // Uzbekistan
  GE: "🇬🇪", // Georgia
  AZ: "🇦🇿", // Azerbaijan
  AM: "🇦🇲", // Armenia
  IN: "🇮🇳", // India
  ID: "🇮🇩", // Indonesia
  TH: "🇹🇭", // Thailand
  MY: "🇲🇾", // Malaysia
  SG: "🇸🇬", // Singapore
  VN: "🇻🇳", // Vietnam
  PH: "🇵🇭", // Philippines
};

// Club name patterns to country code mapping
// Using patterns (lowercase) to match club names
const CLUB_PATTERNS = {
  // England
  EN: [
    "manchester united", "manchester city", "liverpool", "chelsea", "arsenal",
    "tottenham", "spurs", "everton", "newcastle", "aston villa", "west ham",
    "leicester", "wolverhampton", "wolves", "brighton", "crystal palace",
    "fulham", "brentford", "nottingham forest", "bournemouth", "burnley",
    "sheffield united", "sheffield wednesday", "luton", "leeds", "southampton",
    "watford", "norwich", "west brom", "middlesbrough", "sunderland",
    "blackburn", "bolton", "portsmouth", "charlton", "reading", "wigan",
    "stoke", "swansea", "hull", "qpr", "queens park", "birmingham",
    "derby", "ipswich", "coventry", "millwall", "blackpool", "cardiff",
    "oxford", "plymouth", "bristol", "huddersfield", "rotherham", "preston",
  ],
  // Scotland
  SC: [
    "celtic", "rangers", "aberdeen", "hearts", "hibernian", "dundee",
    "motherwell", "kilmarnock", "st mirren", "livingston", "ross county",
    "st johnstone", "partick",
  ],
  // Wales
  WA: ["swansea", "cardiff", "wrexham", "newport"],
  // Spain
  ES: [
    "real madrid", "barcelona", "atlético madrid", "atletico madrid",
    "sevilla", "villarreal", "real sociedad", "athletic bilbao", "betis",
    "valencia", "getafe", "celta", "osasuna", "mallorca", "las palmas",
    "alavés", "alaves", "granada", "cádiz", "cadiz", "almería", "almeria",
    "girona", "rayo vallecano", "espanyol", "levante", "eibar", "leganés",
    "leganes", "huesca", "valladolid", "elche", "deportivo", "zaragoza",
    "málaga", "malaga", "racing santander", "recreativo", "tenerife",
    "numancia", "sporting gijón", "sporting gijon", "real oviedo", "murcia",
  ],
  // Germany
  DE: [
    "bayern", "borussia dortmund", "dortmund", "bayer leverkusen", "leverkusen",
    "rb leipzig", "leipzig", "eintracht frankfurt", "frankfurt", "wolfsburg",
    "borussia mönchengladbach", "gladbach", "mönchengladbach", "monchengladbach",
    "freiburg", "hoffenheim", "union berlin", "köln", "koln", "mainz",
    "augsburg", "werder bremen", "bremen", "bochum", "heidenheim", "darmstadt",
    "stuttgart", "hertha", "schalke", "düsseldorf", "dusseldorf", "hannover",
    "nürnberg", "nurnberg", "hamburg", "hsv", "kaiserslautern", "1860 münchen",
    "1860 munich", "greuther fürth", "greuther furth", "paderborn", "bielefeld",
    "st. pauli", "st pauli", "karlsruher", "braunschweig",
  ],
  // Italy
  IT: [
    "juventus", "inter", "internazionale", "milan", "ac milan", "napoli",
    "roma", "lazio", "atalanta", "fiorentina", "torino", "bologna", "udinese",
    "sassuolo", "empoli", "monza", "lecce", "verona", "hellas verona", "genoa",
    "cagliari", "frosinone", "salernitana", "sampdoria", "spezia", "venezia",
    "parma", "brescia", "palermo", "catania", "bari", "reggina", "siena",
    "chievo", "pescara", "novara", "cesena", "crotone", "benevento", "spal",
    "perugia", "vicenza", "modena", "ascoli", "livorno", "piacenza", "treviso",
    "ternana", "avellino", "como",
  ],
  // France
  FR: [
    "paris saint-germain", "paris saint germain", "psg", "marseille", "lyon",
    "monaco", "lille", "nice", "rennes", "lens", "reims", "montpellier",
    "toulouse", "nantes", "strasbourg", "brest", "le havre", "lorient", "metz",
    "clermont", "auxerre", "bordeaux", "saint-étienne", "saint etienne",
    "angers", "troyes", "ajaccio", "dijon", "amiens", "caen", "guingamp",
    "sochaux", "nancy", "bastia", "sedan", "le mans", "valenciennes", "evian",
  ],
  // Netherlands
  NL: [
    "ajax", "psv", "psv eindhoven", "feyenoord", "az", "az alkmaar", "twente",
    "utrecht", "vitesse", "heerenveen", "groningen", "sparta rotterdam",
    "nec", "go ahead eagles", "fortuna sittard", "excelsior", "volendam",
    "almere city", "heracles", "ado den haag", "willem ii", "roda", "breda",
    "waalwijk", "zwolle", "cambuur", "emmen", "venlo",
  ],
  // Portugal
  PT: [
    "benfica", "porto", "sporting", "sporting cp", "sporting lisbon", "braga",
    "vitória guimarães", "vitoria guimaraes", "famalicão", "famalicao",
    "boavista", "rio ave", "paços de ferreira", "pacos de ferreira", "gil vicente",
    "estoril", "arouca", "chaves", "portimonense", "marítimo", "maritimo",
    "santa clara", "vizela", "casa pia", "moreirense", "farense", "setúbal",
    "setubal", "académica", "academica", "belenenses", "nacional", "leiria",
  ],
  // Brazil
  BR: [
    "flamengo", "palmeiras", "corinthians", "são paulo", "sao paulo", "santos",
    "grêmio", "gremio", "internacional", "fluminense", "atlético mineiro",
    "atletico mineiro", "cruzeiro", "botafogo", "vasco", "bahia", "fortaleza",
    "athletico paranaense", "red bull bragantino", "bragantino", "cuiabá",
    "cuiaba", "goiás", "goias", "coritiba", "américa mineiro", "america mineiro",
    "ceará", "ceara", "juventude", "avaí", "avai", "chapecoense", "sport recife",
    "náutico", "nautico", "vitória", "vitoria", "ponte preta", "guarani",
    "portuguesa", "paraná", "parana", "figueirense", "criciúma", "criciuma",
  ],
  // Argentina
  AR: [
    "boca juniors", "river plate", "racing", "independiente", "san lorenzo",
    "vélez", "velez", "estudiantes", "lanús", "lanus", "argentinos juniors",
    "newell's", "newells", "rosario central", "huracán", "huracan", "defensa",
    "talleres", "godoy cruz", "banfield", "unión", "union", "colón", "colon",
    "central córdoba", "central cordoba", "patronato", "platense", "arsenal",
    "arsenal de sarandí", "gimnasia", "belgrano", "tigre", "sarmiento",
    "atlético tucumán", "atletico tucuman", "barracas central",
  ],
  // Turkey
  TR: [
    "galatasaray", "fenerbahçe", "fenerbahce", "beşiktaş", "besiktas",
    "trabzonspor", "başakşehir", "basaksehir", "konyaspor", "antalyaspor",
    "alanyaspor", "kasımpaşa", "kasimpasa", "sivasspor", "kayserispor",
    "gaziantep", "ankaragücü", "ankaragucu", "adana demirspor", "giresunspor",
    "hatayspor", "pendikspor", "samsunspor", "rizespor", "istanbulspor",
    "fatih karagümrük", "fatih karagumruk", "ümraniyespor", "umraniyespor",
    "göztepe", "goztepe", "denizlispor", "malatyaspor", "akhisar", "bursaspor",
    "eskişehirspor", "eskisehirspor",
  ],
  // Greece
  GR: [
    "olympiacos", "olympiakos", "panathinaikos", "aek", "aek athens", "paok",
    "aris", "aris thessaloniki", "asteras tripolis", "atromitos", "volos",
    "ionikos", "lamia", "ofi", "ofi crete", "panionios", "pas giannina",
    "giannina", "panaitolikos", "levadiakos", "xanthi", "larissa", "apollon",
    "kerkyra", "ergotelis", "kavala", "iraklis", "skoda xanthi", "panthrakikos",
  ],
  // Russia
  RU: [
    "zenit", "cska moscow", "cska", "spartak moscow", "spartak", "lokomotiv moscow",
    "lokomotiv", "dynamo moscow", "krasnodar", "rubin", "rubin kazan", "sochi",
    "rostov", "akhmat grozny", "akhmat", "orenburg", "ural", "fakel voronezh",
    "krylya sovetov", "nizhny novgorod", "pari nn", "khimki", "torpedo",
    "arsenal tula", "ufa", "anzhi", "terek", "amkar", "kuban", "tom tomsk",
    "volga", "saturn",
  ],
  // Ukraine
  UA: [
    "shakhtar", "shakhtar donetsk", "dynamo kyiv", "dynamo kiev", "dnipro",
    "zorya", "zorya luhansk", "vorskla", "chornomorets", "metalist", "metalurh",
    "karpaty", "arsenal kyiv", "tavriya",
  ],
  // Belgium
  BE: [
    "club brugge", "anderlecht", "union saint-gilloise", "union sg", "antwerp",
    "gent", "genk", "standard liège", "standard liege", "mechelen", "westerlo",
    "cercle brugge", "charleroi", "kortrijk", "sint-truiden", "sint truiden",
    "stvv", "eupen", "oostende", "leuven", "mouscron", "waasland-beveren",
    "lokeren", "zulte waregem", "beerschot",
  ],
  // Switzerland
  CH: [
    "basel", "young boys", "zürich", "zurich", "servette", "lugano", "st. gallen",
    "st gallen", "lausanne", "luzern", "sion", "grasshoppers", "winterthur",
    "yverdon", "stade lausanne", "thun", "aarau", "vaduz", "neuchâtel xamax",
    "neuchatel xamax", "xamax",
  ],
  // Austria
  AT: [
    "salzburg", "red bull salzburg", "rb salzburg", "rapid wien", "rapid vienna",
    "sturm graz", "lask", "austria wien", "austria vienna", "wolfsberger",
    "wolfsberg", "hartberg", "altach", "austria klagenfurt", "ried", "admira",
    "mattersburg", "wacker innsbruck", "grazer ak",
  ],
  // Poland
  PL: [
    "legia warsaw", "legia", "lech poznań", "lech poznan", "raków", "rakow",
    "pogoń szczecin", "pogon szczecin", "śląsk wrocław", "slask wroclaw",
    "jagiellonia", "piast gliwice", "cracovia", "wisła kraków", "wisla krakow",
    "górnik zabrze", "gornik zabrze", "zagłębie lubin", "zaglebie lubin",
    "korona kielce", "warta poznań", "warta poznan", "stal mielec", "ruch chorzów",
    "ruch chorzow", "wisła płock", "wisla plock", "lechia gdańsk", "lechia gdansk",
  ],
  // Saudi Arabia
  SA: [
    "al-hilal", "al hilal", "al-nassr", "al nassr", "al-ahli", "al ahli",
    "al-ittihad", "al ittihad", "al-shabab", "al shabab", "al-ettifaq",
    "al ettifaq", "al-fateh", "al fateh", "al-taawoun", "al taawoun",
    "al-fayha", "al fayha", "al-raed", "al raed", "al-khaleej", "al khaleej",
    "damac", "abha", "al-hazem", "al hazem", "al-tai", "al tai", "al-wehda",
    "al wehda", "al-batin", "al batin",
  ],
  // UAE
  AE: [
    "al-ain", "al ain", "al-wasl", "al wasl", "shabab al-ahli", "al-jazira",
    "al jazira", "baniyas", "al-sharjah", "al sharjah", "ajman",
  ],
  // Qatar
  QA: [
    "al-sadd", "al sadd", "al-duhail", "al duhail", "al-rayyan", "al rayyan",
    "al-arabi", "al arabi", "al-gharafa", "al gharafa", "qatar sc", "umm salal",
    "al-wakrah", "al wakrah", "al-sailiya", "al sailiya", "al-khor", "al khor",
  ],
  // China
  CN: [
    "shanghai shenhua", "shenhua", "guangzhou", "guangzhou fc", "guangzhou evergrande",
    "beijing guoan", "guoan", "shandong taishan", "shandong luneng", "jiangsu",
    "jiangsu suning", "shanghai sipg", "shanghai port", "tianjin", "dalian",
    "wuhan", "chengdu", "henan", "shenzhen", "changchun yatai",
  ],
  // Japan
  JP: [
    "vissel kobe", "kawasaki frontale", "yokohama f. marinos", "yokohama marinos",
    "urawa red diamonds", "urawa reds", "kashima antlers", "nagoya grampus",
    "cerezo osaka", "gamba osaka", "fc tokyo", "sanfrecce hiroshima", "consadole",
    "consadole sapporo", "sagan tosu", "jubilo iwata", "kashiwa reysol",
    "shimizu s-pulse", "shimizu", "albirex niigata", "ventforet kofu",
    "kyoto sanga", "shonan bellmare",
  ],
  // South Korea
  KR: [
    "jeonbuk", "jeonbuk hyundai", "ulsan hyundai", "ulsan", "pohang steelers",
    "fc seoul", "suwon samsung", "suwon bluewings", "daegu fc", "incheon united",
    "jeju united", "gangwon fc", "gwangju fc", "seongnam", "busan ipark",
  ],
  // USA
  US: [
    "la galaxy", "galaxy", "inter miami", "los angeles fc", "lafc", "new york city",
    "nycfc", "atlanta united", "seattle sounders", "philadelphia union",
    "portland timbers", "nashville sc", "fc cincinnati", "new england revolution",
    "new york red bulls", "red bulls", "columbus crew", "austin fc", "orlando city",
    "charlotte fc", "minnesota united", "real salt lake", "sporting kansas city",
    "kansas city", "houston dynamo", "dallas", "fc dallas", "chicago fire",
    "colorado rapids", "san jose earthquakes", "vancouver whitecaps", "toronto fc",
    "cf montréal", "cf montreal", "dc united", "st. louis city", "st louis city",
  ],
  // Mexico
  MX: [
    "club américa", "club america", "américa", "america", "chivas", "guadalajara",
    "cruz azul", "tigres", "monterrey", "pumas", "toluca", "santos laguna",
    "león", "leon", "pachuca", "atlas", "necaxa", "puebla", "tijuana",
    "querétaro", "queretaro", "mazatlán", "mazatlan", "atlético san luis",
    "atletico san luis", "juárez", "juarez",
  ],
  // Australia
  AU: [
    "sydney fc", "melbourne victory", "melbourne city", "western sydney wanderers",
    "brisbane roar", "perth glory", "central coast mariners", "newcastle jets",
    "adelaide united", "wellington phoenix", "western united", "macarthur fc",
  ],
  // Croatia
  HR: [
    "dinamo zagreb", "hajduk split", "rijeka", "osijek", "lokomotiva",
    "gorica", "slaven belupo", "istra",
  ],
  // Serbia
  RS: [
    "red star", "red star belgrade", "crvena zvezda", "partizan", "vojvodina",
    "čukarički", "cukaricki", "tsc bačka topola", "tsc backa topola",
  ],
  // Czech Republic
  CZ: [
    "sparta prague", "slavia prague", "viktoria plzeň", "viktoria plzen",
    "plzeň", "plzen", "baník ostrava", "banik ostrava", "slovan liberec",
    "jablonec", "bohemians", "mladá boleslav", "mlada boleslav",
  ],
  // Denmark
  DK: [
    "copenhagen", "fc copenhagen", "midtjylland", "brøndby", "brondby",
    "nordsjælland", "nordsjaelland", "aab", "aalborg", "silkeborg", "viborg",
    "aarhus", "agf", "randers", "odense", "sønderjyske", "sonderjyske",
    "lyngby", "vejle", "horsens",
  ],
  // Sweden
  SE: [
    "malmö", "malmo", "malmö ff", "malmo ff", "aik", "djurgården", "djurgarden",
    "hammarby", "göteborg", "goteborg", "ifk göteborg", "ifk goteborg",
    "elfsborg", "häcken", "hacken", "kalmar", "norrköping", "norrkoping",
    "sirius", "varberg", "mjällby", "mjallby", "degerfors", "halmstad",
    "helsingborg", "örebro", "orebro",
  ],
  // Norway
  NO: [
    "bodø/glimt", "bodo/glimt", "bodø glimt", "bodo glimt", "molde", "rosenborg",
    "brann", "vålerenga", "valerenga", "viking", "lillestrøm", "lillestrom",
    "strømsgodset", "stromsgodset", "stabæk", "stabaek", "tromsø", "tromso",
    "sarpsborg", "haugesund", "odd", "sandefjord", "kristiansund", "aalesund",
  ],
  // Israel
  IL: [
    "maccabi tel aviv", "maccabi haifa", "hapoel tel aviv", "hapoel beer sheva",
    "beitar jerusalem", "bnei sakhnin", "ashdod", "netanya",
  ],
  // Cyprus
  CY: [
    "apoel", "anorthosis", "omonia", "apollon limassol", "ael limassol", "aek larnaca",
  ],
};

/**
 * Get the correct flag for a club name
 * @param {string} clubName - The club name from the database
 * @param {string} dbFlag - The flag from the database (fallback)
 * @returns {string} The correct flag emoji
 */
export function getClubFlag(clubName, dbFlag = "") {
  if (!clubName) return dbFlag || "🏳️";

  const lowerName = clubName.toLowerCase().trim();

  // Check each country's patterns
  for (const [countryCode, patterns] of Object.entries(CLUB_PATTERNS)) {
    for (const pattern of patterns) {
      if (lowerName.includes(pattern) || pattern.includes(lowerName)) {
        return FLAGS[countryCode] || dbFlag || "🏳️";
      }
    }
  }

  // Fallback to database flag
  return dbFlag || "🏳️";
}

export { FLAGS, CLUB_PATTERNS };
