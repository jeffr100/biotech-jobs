"""Decide whether a job location string is in the United States."""
import re

STATES = ("Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|"
          "Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|"
          "Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|"
          "Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|"
          "Wisconsin|Wyoming|District of Columbia|Puerto Rico")
ABBR = ("AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|"
        "RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC|PR")
CITIES = ("Boston|Cambridge, MA|San Diego|San Francisco|South San Francisco|Seattle|New York City|NYC|Chicago|Houston|Dallas|"
          "Austin|Philadelphia|Pittsburgh|Baltimore|Bethesda|Gaithersburg|Rockville|Durham|Raleigh|Research Triangle|"
          "Salt Lake City|Denver|Boulder|Madison|Indianapolis|Princeton|Waltham|Lexington, MA|Redwood City|Menlo Park|"
          "Palo Alto|Mountain View|Sunnyvale|Foster City|Hayward|Emeryville|Brisbane, CA|Carlsbad|Irvine|Los Angeles|"
          "Atlanta|Nashville|Minneapolis|St\\. Louis|Saint Louis|Phoenix|Tampa|Miami|Orlando|Portland|Rochester|Ann Arbor|"
          "Detroit|Cleveland|Columbus|Cincinnati|Kansas City|Omaha|Richmond|Charlotte|Tarrytown|Rahway|Kenilworth|"
          "Bridgewater|Titusville|Spring House|Thousand Oaks|Lake County|Lenexa|Marlborough|Morrisville|Frederick|"
          "Tarrytown|Sleepy Hollow|Rensselaer|Renss|East Hanover|Hopewell|Raritan|Summit, NJ|Basking Ridge|Plainsboro|"
          "Lawrenceville|Pennington|New Brunswick|Somerset|Morristown|Parsippany|Florham Park|Madison, NJ|Whippany|"
          "Collegeville|Malvern|King of Prussia|Horsham|Exton|West Point|Upper Gwynedd|Lansdale|Wilmington|Newark|"
          "Burlington|Durham|Research Triangle Park|RTP|Greenville|Sanford|Holly Springs|Indianapolis|Lebanon, IN|"
          "Kalamazoo|Groton|New Haven|Branford|Andover|Framingham|Bedford|Woburn|Lexington|Norwood|Watertown|Somerville|"
          "Thermo|Pittsburgh|Rockford|Grand Island|Carlsbad|Fremont|Pleasanton|Vacaville|Oceanside|Thousand Oaks|"
          "Juncos|Manati|Humacao|Gurabo|Dorado|Holly Springs|Novato|Brisbane|Alameda|Hercules|Petaluma|Santa Clara|"
          "San Jose|Austin|Round Rock|Fort Worth|Plano|Irving|Logan|Middleton|Verona|Fitchburg|Marietta|Duluth|"
          "St Louis|Saint Charles|Maryland Heights|Chesterfield|Olathe|Lenexa|Overland Park|Tempe|Chandler|Scottsdale")
FOREIGN = ("Canada|Mexico|Brazil|Argentina|Chile|Colombia|Peru|United Kingdom|\\bUK\\b|England|Scotland|Wales|Ireland|France|"
           "Germany|Deutschland|Spain|Italy|Portugal|Netherlands|Belgium|Switzerland|Austria|Sweden|Norway|Denmark|Finland|"
           "Poland|Czech|Hungary|Romania|Bulgaria|Greece|Turkey|Israel|India|China|Japan|Korea|Singapore|Taiwan|Hong Kong|"
           "Australia|New Zealand|Philippines|Malaysia|Thailand|Vietnam|Indonesia|South Africa|Egypt|Nigeria|Kenya|UAE|"
           "Saudi|Qatar|Shanghai|Beijing|Tokyo|Seoul|Bangalore|Bengaluru|Hyderabad|Mumbai|Pune|London|Paris|Berlin|Munich|"
           "Basel|Zurich|Amsterdam|Copenhagen|Dublin|Toronto|Montreal|Vancouver|Ontario|Quebec|British Columbia|Alberta|"
           "Tel Aviv|Sydney|Melbourne|Madrid|Barcelona|Milan|Rome|Warsaw|Prague|Budapest|Lisbon|Brussels|Stockholm|Oslo|Helsinki|EMEA|APAC|LATAM")

_US = re.compile(r"United States|\bU\.?S\.?A\b|\bU\.S\.|(^|[\s,(\-/])US($|[\s,)\-/])|\bUS[- ]|Remote[ -]+US|"
                 r"\b(" + STATES + r")\b")
_US_WEAK = re.compile(r",\s*(" + ABBR + r")\b|^(" + ABBR + r")\b|\s(" + ABBR + r")$")
_CITY = re.compile(r"\b(" + CITIES + r")\b", re.I)
_FOREIGN = re.compile(r"\b(" + FOREIGN + r")\b", re.I)


def is_us(location, default_remote=True):
    """True if the location is in the US. Multi-country strings count if any part is US.
    A bare 'Remote' (no country) counts as US when default_remote is True."""
    loc = (location or "").strip()
    if not loc:
        return default_remote
    if _US.search(loc):
        return True
    if _FOREIGN.search(loc):
        return False
    if _CITY.search(loc):
        return True
    if _FOREIGN.search(loc):
        return False
    if _US_WEAK.search(loc):
        return True
    if re.fullmatch(r"(fully |100% )?remote( - anywhere)?|anywhere|hybrid|\d+ locations?|multiple locations", loc, re.I):
        return default_remote
    return False
