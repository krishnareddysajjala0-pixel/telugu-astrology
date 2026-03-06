from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import swisseph as swe
import datetime
import pytz
import os
import threading
import subprocess

app = Flask(__name__)
app.secret_key = 'astrology-secret-key-2024'  # Required for session

# ---------------- Swiss Ephemeris ----------------
# swe.set_ephe_path(".")  # Removed to allow Render to use default pyswisseph bundled files
swe.set_sid_mode(swe.SIDM_LAHIRI)

PLANET_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

RASI_TELUGU = [
    "మేషం","వృషభం","మిథునం","కర్కాటకం",
    "సింహం","కన్య","తులా","వృశ్చికం",
    "ధనస్సు","మకరం","కుంభం","మీనం"
]

PLANETS = {
    "సూర్యుడు": swe.SUN,
    "చంద్రుడు": swe.MOON,
    "కుజుడు": swe.MARS,
    "బుధుడు": swe.MERCURY,
    "గురు": swe.JUPITER,
    "శుక్రుడు": swe.VENUS,
    "శని": swe.SATURN,
    "రాహు": swe.MEAN_NODE
}

SPECIAL_HANDS = {
    "కుజుడు": [90, 210],
    "గురు": [120, 240],
    "శని": [60, 270]
}

# ---------------- Day name Telugu ----------------
DAY_TELUGU = {
    "Sunday": "ఆదివారం",
    "Monday": "సోమవారం",
    "Tuesday": "మంగళవారం",
    "Wednesday": "బుధవారం",
    "Thursday": "గురువారం",
    "Friday": "శుక్రవారం",
    "Saturday": "శనివారం"
}

# ---------------- Nakshatra ----------------
NAKSHATRAS_TELUGU = [
    "అశ్విని","భరణి","కృత్తిక","రోహిణి","మృగశిర","ఆర్ద్ర",
    "పునర్వసు","పుష్యమి","ఆశ్లేష","మఖ",
    "పూర్వఫల్గుణి","ఉత్తరఫల్గుణి",
    "హస్త","చిత్త","స్వాతి","విశాఖ",
    "అనూరాధ","జ్యేష్ఠ","మూల","పూర్వాషాఢ",
    "ఉత్తరాషాఢ","శ్రవణ","ధనిష్ఠ","శతభిష",
    "పూర్వాభాద్ర","ఉత్తరాభాద్ర","రేవతి"
]

NAKSHATRA_SIZE = 13 + 20/60
PADAM_SIZE = NAKSHATRA_SIZE / 4

TELUGU_YEARS = [
    "ప్రభవ", "విభవ", "శుక్ల", "ప్రమోదూత", "ప్రజోత్పత్తి", "ఆంగీరస", "శ్రీముఖ", "భావ", "యువ", "ధాత",
    "ఈశ్వర", "బహుధాన్య", "ప్రమాది", "విక్రమ", "వృష", "చిత్రభాను", "స్వభాను", "తారణ", "పార్థివ", "వ్యయ",
    "సర్వజిత్తు", "సర్వధారి", "విరోధి", "వికృతి", "ఖర", "నందన", "విజయ", "జయ", "మన్మథ", "దుర్ముఖి",
    "హేవిలంబి", "విలంబి", "వికారి", "శార్వరి", "ప్లవ", "శుభకృతు", "శోభకృతు", "క్రోధి", "విశ్వావసు", "పరాభవ",
    "ప్లవంగ", "కీలక", "సౌమ్య", "సాధారణ", "విరోధికృతు", "పరీధావి", "ప్రమాదీచ", "ఆనంద", "రాక్షస", "నల",
    "పింగళ", "కాళయుక్తి", "సిద్ధార్థి", "రౌద్రి", "దుర్మతి", "దుందుభి", "రుధిరోద్గారి", "రక్తాక్షి", "క్రోధన", "అక్షయ"
]

# ---------------- Panchangam Data ----------------
TITHIS_TELUGU = [
    "పాడ్యమి", "విదియ", "తదియ", "చవితి", "పంచమి", "షష్ఠి", "సప్తమి",
    "అష్టమి", "నవమి", "దశమి", "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి", "పౌర్ణమి"
]

TITHIS_KRISHNA_TELUGU = [
    "పాడ్యమి", "విదియ", "తదియ", "చవితి", "పంచమి", "షష్ఠి", "సప్తమి",
    "అష్టమి", "నవమి", "దశమి", "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి", "అమావాస్య"
]

YOGAS_TELUGU = [
    "విష్కంభ", "ప్రీతి", "ఆయుష్మాన్", "సౌభాగ్య", "శోభన", "అతిగండ", "సుకర్మ",
    "ధృతి", "శూల", "గండ", "వృధ్ధి", "ధ్రువ", "వ్యాఘాత", "హర్షణ", "వజ్ర", "సిద్ధి",
    "వ్యతీపాత", "వరియాన్", "పరీఘ", "శివ", "సిద్ధ", "సాధ్య", "శుభ", "శుక్ల",
    "బ్రహ్మ", "ఇంద్ర", "వైధృతి"
]

KARANAS_MOVABLE = ["బవ", "బాలవ", "కౌలవ", "తైతిల", "గర", "వణిజ", "విష్టి"]

# ---------------- DASA CALCULATION DATA ----------------
DASA_ORDER = [
    "సూర్య","చంద్ర","కుజ","రాహు","గురు","భూమి",
    "శని","బుధ","కేతు","శుక్ర","మిత్ర","చిత్ర"
]

DASA_YEARS = {
    "సూర్య":10, "చంద్ర":10, "కుజ":7, "రాహు":10,
    "గురు":13, "భూమి":13, "శని":13, "బుధ":10,
    "కేతు":7, "శుక్ర":13, "మిత్ర":7, "చిత్ర":7
}

PADAS_PER_DASA = 9
TOTAL_NAK_MINUTES = 13*60 + 20  # 800 minutes

# ---------------- ANTHARA DATA ----------------
ANTHARA_MONTHS = {
    "సూర్య": [
        ("సూర్య", 10), ("చంద్ర", 10), ("కుజ", 7), ("రాహు", 10),
        ("గురు", 13), ("భూమి", 13), ("శని", 13), ("బుధ", 10), 
        ("కేతు", 7), ("శుక్ర", 13), ("మిత్ర", 7), ("చిత్ర", 7)
    ],
    "చంద్ర": [
        ("చంద్ర", 10), ("కుజ", 7), ("రాహు", 10), ("గురు", 13),
        ("భూమి", 13), ("శని", 13), ("బుధ", 10), ("కేతు", 7), 
        ("శుక్ర", 13), ("మిత్ర", 7), ("చిత్ర", 7), ("సూర్య", 10)
    ],
    "కుజ": [
        ("కుజ", 4.9), ("రాహు", 7), ("గురు", 9.1), ("భూమి", 9.1),
        ("శని", 9.1), ("బుధ", 7), ("కేతు", 4), ("శుక్ర", 9), 
        ("మిత్ర", 4), ("చిత్ర", 4), ("సూర్య", 7), ("చంద్ర", 7)
    ],
    "రాహు": [
        ("రాహు", 10), ("గురు", 13), ("భూమి", 13), ("శని", 13), ("బుధ", 10),
        ("కేతు", 7), ("శుక్ర", 13), ("మిత్ర", 7), ("చిత్ర", 7),
        ("సూర్య", 10), ("చంద్ర", 10), ("కుజ", 7)
    ],
    "గురు": [
        ("గురు", 16.9), ("భూమి", 16.9), ("శని", 16.9), ("బుధ", 13), ("కేతు", 9),
        ("శుక్ర", 16.9), ("మిత్ర", 9.1), ("చిత్ర", 9.1), 
        ("సూర్య", 13), ("చంద్ర", 13), ("కుజ", 9.1), ("రాహు", 13)
    ],
    "భూమి": [
        ("భూమి", 16.9), ("శని", 16.9), ("బుధ", 13), ("కేతు", 9.1),
        ("శుక్ర", 16.9), ("మిత్ర", 9.1), ("చిత్ర", 9.1),
        ("సూర్య", 13), ("చంద్ర", 13), ("కుజ", 9.1),
        ("రాహు", 13), ("గురు", 16.9)
    ],
    "శని": [
        ("శని", 16.9), ("బుధ", 13), ("కేతు", 9.1), ("శుక్ర", 16.9),
        ("మిత్ర", 9.1), ("చిత్ర", 9.1), ("సూర్య", 13),
        ("చంద్ర", 13), ("కుజ", 9.1), ("రాహు", 13), ("గురు", 16.9), ("భూమి", 16.9)
    ],
    "బుధ": [
        ("బుధ", 10), ("కేతు", 7), ("శుక్ర", 13), ("మిత్ర", 7),
        ("చిత్ర", 7), ("సూర్య", 10), ("చంద్ర", 10),
        ("కుజ", 7), ("రాహు", 10), ("గురు", 13), ("భూమి", 13), ("శని", 13)
    ],
    "కేతు": [
        ("కేతు", 4.9), ("శుక్ర", 9.1), ("మిత్ర", 4.9), ("చిత్ర", 4.9),
        ("సూర్య", 7), ("చంద్ర", 7), ("కుజ", 4.9),
        ("రాహు", 7), ("గురు", 9.1), ("భూమి", 9.1), ("శని", 9.1), ("బుధ", 7)
    ],
    "శుక్ర": [
        ("శుక్ర", 16.9), ("మిత్ర", 9.1), ("చిత్ర", 9.1), 
        ("సూర్య", 13), ("చంద్ర", 13), ("కుజ", 9.1), ("రాహు", 13),
        ("గురు", 16.9), ("భూమి", 16.9), ("శని", 16.9), ("బుధ", 13), ("కేతు", 9.1)
    ],
    "మిత్ర": [
        ("మిత్ర", 4.9), ("చిత్ర", 4.9), ("సూర్య", 7),
        ("చంద్ర", 7), ("కుజ", 4), ("రాహు", 7), ("గురు", 9.1), ("భూమి", 9.1), 
        ("శని", 9.1), ("బుధ", 7), ("కేతు", 4.9), ("శుక్ర", 9.1)
    ],
    "చిత్ర": [
        ("చిత్ర", 4.9), ("సూర్య", 7), ("చంద్ర", 7),
        ("కుజ", 4.9), ("రాహు", 7), ("గురు", 9.1), ("భూమి", 9.1), ("శని", 9.1),
        ("బుధ", 7), ("కేతు", 4.9), ("శుక్ర", 9.1), ("మిత్ర", 4.9)
    ]
}

# ---------------- PLANET COLORS FOR VISUALIZATION ----------------
PLANET_COLORS = {
    "సూర్య": "#FFD700",  "సూర్యుడు": "#FFD700",  # Gold
    "చంద్ర": "#F0F8FF",  "చంద్రుడు": "#F0F8FF",  # Alice Blue
    "కుజ": "#FF4500",    "కుజుడు": "#FF4500",    # Orange Red
    "బుధ": "#32CD32",    "బుధుడు": "#32CD32",    # Lime Green
    "గురు": "#FFA500",   # Orange
    "శుక్ర": "#FF69B4",  "శుక్రుడు": "#FF69B4",  # Hot Pink
    "శని": "#696969",    # Dim Gray
    "రాహు": "#8B4513",   # Saddle Brown
    "కేతు": "#2F4F4F",   # Dark Slate Gray
    "భూమి": "#228B22",   # Forest Green
    "మిత్ర": "#9370DB",  # Medium Purple
    "చిత్ర": "#40E0D0"   # Turquoise
}

PLANET_ICONS = {
    "సూర్య": "☉",
    "చంద్ర": "☽",
    "కుజ": "♂",
    "బుధ": "☿",
    "గురు": "♃",
    "శుక్ర": "♀",
    "శని": "♄",
    "రాహు": "☊",
    "కేతు": "☋",
    "భూమి": "♁",
    "మిత్ర": "☆",
    "చిత్ర": "✦"
}

# Month mappings linking Telugu to English Gregorian periods
TELUGU_MASALU = [
    "చైత్ర", "వైశాఖ", "జ్యేష్ఠ", "ఆషాఢ", "శ్రావణ", "భాద్రపద", 
    "ఆశ్వయుజ", "కార్తీక", "మార్గశిర", "పుష్య", "మాఘ", "ఫాల్గుణ"
]

ENGLISH_MONTHS = [
    "(March - April)", "(April - May)", "(May - June)", "(June - July)",
    "(July - August)", "(August - September)", "(September - October)",
    "(October - November)", "(November - December)", "(December - January)",
    "(January - February)", "(February - March)"
]

# Rutuvulu mappings
TELUGU_RUTUVULU = [
    "వసంత", "గ్రీష్మ", "వర్ష", 
    "శరత్", "హేమంత", "శిశిర"
]

# ---------------- ASTROLOGICAL PARTIES ----------------
# Lagnas belonging to Guru Party
GURU_PARTY_LAGNAS = ["మేషం", "కర్కాటకం", "సింహం", "వృశ్చికం", "ధనస్సు", "మీనం"]
# Lagnas belonging to Sani Party
SANI_PARTY_LAGNAS = ["వృషభం", "మిథునం", "కన్య", "తులా", "మకరం", "కుంభం"]

# Favorable planets for each party
# Note: Rahu & Ketu act depending on house, but standardly align with the party or act as neutral.
# We map standard party friends for the "అనుకూలము (Favorable)" label
GURU_PARTY_PLANETS = ["సూర్య", "చంద్ర", "కుజ", "గురు", "కేతు", "భూమి"] 
SANI_PARTY_PLANETS = ["శని", "బుధ", "శుక్ర", "రాహు", "మిత్ర", "చిత్ర"]

# ---------------- DASA HELPER FUNCTIONS ----------------
def get_running_dasa(nak_index, padam):
    """Calculate running Mahadasha based on nakshatra and padam"""
    global_pada = nak_index * 4 + padam
    
    if global_pada == 0:
        global_pada = 108
    
    while global_pada > 108:
        global_pada -= 108
    
    idx = (global_pada - 1) // PADAS_PER_DASA
    
    idx = max(0, min(idx, len(DASA_ORDER) - 1))
    
    return DASA_ORDER[idx], idx

def is_dasa_favorable(lagna, planet):
    """Determine if a planet's Dasha is favorable based on birth Lagna Party"""
    if lagna in GURU_PARTY_LAGNAS:
        return planet in GURU_PARTY_PLANETS
    elif lagna in SANI_PARTY_LAGNAS:
        return planet in SANI_PARTY_PLANETS
    return False  # Fallback

def add_years(dt, years):
    """Add years to datetime"""
    return dt + datetime.timedelta(days=int(years * 365.25))

def add_months(dt, months):
    """Add months to datetime"""
    return dt + datetime.timedelta(days=int(months * 30.44))

def nak_minutes(h, m):
    """Convert hours and minutes to total minutes"""
    return h * 60 + m

def is_date_within_range(check_date, start_date_str, end_date_str):
    """Check if a date falls within a date range"""
    try:
        check_dt = datetime.datetime.strptime(check_date, "%d-%m-%Y")
        start_dt = datetime.datetime.strptime(start_date_str, "%d-%m-%Y")
        end_dt = datetime.datetime.strptime(end_date_str, "%d-%m-%Y")
        
        return start_dt <= check_dt <= end_dt
    except:
        return False

# ---------------- GITHUB LOGGING HELPER ----------------
def log_user_to_github(name, dob, tob, place):
    """Log user data to user_data.txt and push to GitHub in the background."""
    def background_task(n, d, t, p):
        try:
            log_file = "user_data.txt"
            serial_no = 1
            
            # Read the last serial number if the file exists
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        if last_line and ". " in last_line:
                            try:
                                serial_no = int(last_line.split(". ")[0]) + 1
                            except ValueError:
                                pass
                                
            timestamp = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
            log_entry = f"{serial_no}. [{timestamp}] Name: {n}, DOB: {d}, TOB: {t}, Place: {p}\n"
            
            # Append to file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
                
            # Git add, commit, and push
            try:
                res_add = subprocess.run(["git", "add", log_file], check=True, capture_output=True, text=True, shell=True)
                res_commit = subprocess.run(["git", "commit", "-m", f"Log new user data for {n}"], check=True, capture_output=True, text=True, shell=True)
                res_push = subprocess.run(["git", "push"], check=True, capture_output=True, text=True, shell=True)
                print(f"Successfully logged to Github. Push output: {res_push.stdout}")
            except subprocess.CalledProcessError as e:
                print(f"Git subprocess error. Code: {e.returncode}")
                print(f"Git stdout: {e.stdout}")
                print(f"Git stderr: {e.stderr}")
            
        except Exception as e:
            print(f"Error logging to Github: {e}")
            
    # Start thread so it doesn't block the response
    thread = threading.Thread(target=background_task, args=(name, dob, tob, place))
    thread.daemon = True
    thread.start()

def calculate_anthara_periods(maha_name, start_date, end_date, lagna="", birth_dt=None):
    """Calculate anthara periods for a given Mahadasha"""
    antharas = []
    anthara_start = start_date
    
    if maha_name in ANTHARA_MONTHS:
        for planet, months in ANTHARA_MONTHS[maha_name]:
            anthara_end = add_months(anthara_start, months)
            
            is_favorable = is_dasa_favorable(lagna, planet)
            color = "#22c55e" if is_favorable else "#ef4444"
            
            
            age_start_str = ""
            age_end_str = ""
            if birth_dt:
                age_start_days = (anthara_start - birth_dt).days
                if age_start_days >= 0:
                    age_start_y = age_start_days // 365
                    age_start_m = (age_start_days % 365) // 30
                    age_start_str = f"{age_start_y}సం, {age_start_m}నెలలు"
                
                age_end_days = (anthara_end - birth_dt).days
                if age_end_days >= 0:
                    age_end_y = age_end_days // 365
                    age_end_m = (age_end_days % 365) // 30
                    age_end_str = f"{age_end_y}సం, {age_end_m}నెలలు"

            antharas.append({
                "anthara": planet,
                "start": anthara_start.strftime("%d-%m-%Y"),
                "end": anthara_end.strftime("%d-%m-%Y"),
                "months": months,
                "color": color,
                "icon": PLANET_ICONS.get(planet, "•"),
                "is_favorable": is_favorable,
                "age_start": age_start_str,
                "age_end": age_end_str
            })
            anthara_start = anthara_end
    
    return antharas

def parse_telugu_time(time_str):
    """Parse Telugu time string like '3గం 52ని' to (hours, minutes)"""
    try:
        if 'గం' in time_str:
            parts = time_str.split('గం')
            hours = int(parts[0].strip())
            minutes = int(parts[1].replace('ని', '').strip())
            return hours, minutes
        else:
            # Try English format
            if 'h' in time_str.lower():
                parts = time_str.lower().split('h')
                hours = int(parts[0].strip())
                minutes = int(parts[1].replace('m', '').strip())
                return hours, minutes
            else:
                # Try colon format
                if ':' in time_str:
                    h, m = time_str.split(':')
                    return int(h), int(m)
                else:
                    return 0, 0
    except:
        return 0, 0

def get_planet_color(planet_name):
    """Get color for a planet"""
    return PLANET_COLORS.get(planet_name, "#666666")

def get_planet_icon(planet_name):
    """Get icon for a planet"""
    return PLANET_ICONS.get(planet_name, "•")

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chart", methods=["POST"])
def chart():
    name = request.form.get("name","")
    dob = request.form.get("dob","")
    tob = request.form.get("tob","")
    place = request.form.get("place","")

    lat = request.form.get("lat")
    lon = request.form.get("lon")

    if not lat or not lon:
        return "❌ Please select place from suggestion list"

    lat = float(lat)
    lon = float(lon)
    
    # Log User query to GitHub
    log_user_to_github(name, dob, tob, place)

    # Day name
    day_eng = datetime.datetime.strptime(dob, "%Y-%m-%d").strftime("%A")
    day_name = DAY_TELUGU.get(day_eng, day_eng)

    # Determine Timezone based on Latitude and Longitude
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        timezone_str = tf.certain_timezone_at(lat=lat, lng=lon)
        if not timezone_str:
            timezone_str = "Asia/Kolkata"
    except ImportError:
        timezone_str = "Asia/Kolkata"

    # Time: Local Time → UTC
    local_tz = pytz.timezone(timezone_str)
    local_dt = local_tz.localize(
        datetime.datetime.strptime(dob+" "+tob,"%Y-%m-%d %H:%M")
    )
    utc_dt = local_dt.astimezone(pytz.utc)

    jd = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute/60 + utc_dt.second/3600
    )

    chart_data_temp = {r:[] for r in RASI_TELUGU}
    base_pos = {}

    # Planets
    for name_p, pid in PLANETS.items():
        lonp = swe.calc_ut(jd, pid, PLANET_FLAGS)[0][0]
        base_pos[name_p] = lonp
        rasi = RASI_TELUGU[int(lonp/30)]
        deg = lonp % 30
        d = int(deg)
        m = int((deg-d)*60)
        html_str = f"<b>{name_p}</b> <small>{d}°{m:02d}′</small>"
        chart_data_temp[rasi].append((deg, html_str))

    # Ketu
    rahu = base_pos["రాహు"]
    ketu = (rahu + 180) % 360
    base_pos["కేతు"] = ketu

    r = RASI_TELUGU[int(ketu/30)]
    deg_k = ketu % 30
    d = int(deg_k)
    m = int((deg_k-d)*60)
    html_str = f"<b>కేతు</b> <small>{d}°{m:02d}′</small>"
    chart_data_temp[r].append((deg_k, html_str))

    # Derived planets (Dasacharam Logic - Verified)
    derived = {
        "భూమి": (base_pos["సూర్యుడు"] + 180) % 360,
        "చిత్ర": (rahu + 3.3333) % 360,  # 1 pada offset
        "మిత్ర": (ketu + 3.3333) % 360   # 1 pada offset
    }

    for n, lonp in derived.items():
        base_pos[n] = lonp
        r = RASI_TELUGU[int(lonp/30)]
        deg = lonp % 30
        d = int(deg)
        m = int((deg-d)*60)
        html_str = f"<b>{n}</b> <small>{d}°{m:02d}′</small>"
        chart_data_temp[r].append((deg, html_str))

    # Month mappings linking Telugu to English Gregorian periods
    TELUGU_MASALU = [
        "చైత్ర", "వైశాఖ", "జ్యేష్ఠ", "ఆషాఢ", "శ్రావణ", "భాద్రపద", 
        "ఆశ్వయుజ", "కార్తీక", "మార్గశిర", "పుష్య", "మాఘ", "ఫాల్గుణ"
    ]

    ENGLISH_MONTHS = [
        "(March - April)", "(April - May)", "(May - June)", "(June - July)",
        "(July - August)", "(August - September)", "(September - October)",
        "(October - November)", "(November - December)", "(December - January)",
        "(January - February)", "(February - March)"
    ]

    # Rutuvulu mappings
    TELUGU_RUTUVULU = [
        "వసంత", "గ్రీష్మ", "వర్ష", 
        "శరత్", "హేమంత", "శిశిర"
    ]

# Dasa parameters
    # Hand planets
    for n, base in base_pos.items():
        angles = [180] + SPECIAL_HANDS.get(n,[])
        for a in angles:
            hl = (base + a) % 360
            r = RASI_TELUGU[int(hl/30)]
            deg = hl % 30
            d = int(deg)
            m = int((deg-d)*60)
            html_str = f"<span class='hand'><span style='font-size: 0.7em;'>👉</span> {n} <small>{d}°{m:02d}′</small></span>"
            chart_data_temp[r].append((deg, html_str))

    # Lagna
    houses, ascmc = swe.houses(jd, lat, lon)
    asc_tropical = ascmc[0]
    ayan = swe.get_ayanamsa_ut(jd)
    lagna_lon = (asc_tropical - ayan) % 360

    lagna = RASI_TELUGU[int(lagna_lon/30)]
    
    # Calculate Lagna degree
    lagna_deg = int(lagna_lon % 30)
    lagna_min = int(((lagna_lon % 30) - lagna_deg) * 60)
    lagna_degree_str = f"{lagna_deg}°{lagna_min:02d}′"
    
    # Add Lagna to chart data
    html_str = f"<b>లగ్నం</b> <small>{lagna_degree_str}</small>"
    chart_data_temp[lagna].append((lagna_lon % 30, html_str))
    
    # Sort elements per house by degree
    chart_data = {}
    for r in RASI_TELUGU:
        chart_data_temp[r].sort(key=lambda x: x[0])
        if chart_data_temp[r]:
            chart_data[r] = "<br>".join(item[1] for item in chart_data_temp[r]) + "<br>"
        else:
            chart_data[r] = ""

    # Nakshatra + Padam
    moon_lon = base_pos["చంద్రుడు"]
    nak_index = int(moon_lon / NAKSHATRA_SIZE)
    nakshatra = NAKSHATRAS_TELUGU[nak_index]

    nak_offset = moon_lon - (nak_index * NAKSHATRA_SIZE)
    padam = int(nak_offset / PADAM_SIZE) + 1

    elapsed_h = int((nak_offset / NAKSHATRA_SIZE) * 24)
    elapsed_m = int((((nak_offset / NAKSHATRA_SIZE) * 24) % 1) * 60)

    rem = NAKSHATRA_SIZE - nak_offset
    remain_h = int((rem / NAKSHATRA_SIZE) * 24)
    remain_m = int((((rem / NAKSHATRA_SIZE) * 24) % 1) * 60)

    # House numbers
    houses_map = {}
    idx = RASI_TELUGU.index(lagna)
    for i in range(12):
        houses_map[RASI_TELUGU[(idx+i)%12]] = i+1

    # Calculate Panchangam components (Tithi, Yoga, Karana)
    sun_lon = base_pos["సూర్యుడు"]
    moon_lon = base_pos["చంద్రుడు"]

    # 1. Tithi
    diff = (moon_lon - sun_lon) % 360
    tithi_index = int(diff / 12)
    tithi_paksha = "శుక్ల పక్షం" if tithi_index < 15 else "కృష్ణ పక్షం"
    
    if tithi_index < 15:
        tithi_name = TITHIS_TELUGU[tithi_index]
    else:
        tithi_name = TITHIS_KRISHNA_TELUGU[tithi_index - 15]

    tithi_offset = diff - (tithi_index * 12)
    # Tithi spans 12 degrees roughly representing a 24-hour cycle. 
    # Calculate elapsed and remaining time proportionally
    t_elapsed_h = int((tithi_offset / 12) * 24)
    t_elapsed_m = int((((tithi_offset / 12) * 24) % 1) * 60)
    
    t_rem = 12 - tithi_offset
    t_remain_h = int((t_rem / 12) * 24)
    t_remain_m = int((((t_rem / 12) * 24) % 1) * 60)

    tithi_elapsed_str = f"{t_elapsed_h}గం {t_elapsed_m}ని"
    tithi_remaining_str = f"{t_remain_h}గం {t_remain_m}ని"

    # 2. Yoga
    yoga_index = int(((sun_lon + moon_lon) % 360) / NAKSHATRA_SIZE)
    yoga_name = YOGAS_TELUGU[yoga_index]

    # 3. Karana
    karana_idx = int(diff / 6) + 1
    if karana_idx == 1:
        karana_name = "కింస్తుఘ్న"
    elif 2 <= karana_idx <= 57:
        m_idx = (karana_idx - 2) % 7
        karana_name = KARANAS_MOVABLE[m_idx]
    elif karana_idx == 58:
        karana_name = "శకుని"
    elif karana_idx == 59:
        karana_name = "చతుష్పాద"
    elif karana_idx == 60:
        karana_name = "నాగ"
    else:
        karana_name = "N/A"

    # 4. Telugu Year (Samvatsara) approximation
    # 0 = Prabhava starts roughly near Kaliyuga 0 or offset 1987 CE
    # A standard quick approximation from gregorian year. Note Chaitra month starts the year.
    try:
        dt = datetime.datetime.strptime(dob + " " + tob, "%Y-%m-%d %H:%M")
    except Exception:
        dt = datetime.datetime.now()
        
    year = dt.year
    month = dt.month
    # Approximate leap: if month < 4 (before April/Chaitra), mostly previous year
    adj_year = year - 1 if month < 4 else year
    # Offset based on known cycle starting year (1987 was Prabhava)
    year_index = (adj_year - 1987) % 60
    telugu_year = TELUGU_YEARS[year_index]
    
    # 1987 (Prabhava, index 0) = Kaliyuga 5088. Using the exact cycle multiplier ties it perfectly.
    cycles_since_1987 = (adj_year - 1987) // 60
    kaliyuga_year = 5088 + (cycles_since_1987 * 60) + year_index
    
    # Thraitha Sakamu mapping: 2025 (Viswavasu) = 47.
    # Therefore, adj_year - 2025 gives the offset from 47.
    thraitha_sakamu = 47 + (adj_year - 2025)

    # 5. Sunrise & Sunset times
    # 5. Sunrise & Sunset times
    # Get local midnight to ensure sunrise/sunset are calculated for the birthday itself
    local_midnight = local_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    utc_midnight = local_midnight.astimezone(pytz.utc)
    jd_midnight = swe.julday(
        utc_midnight.year, utc_midnight.month, utc_midnight.day,
        utc_midnight.hour + utc_midnight.minute/60 + utc_midnight.second/3600
    )

    # 5. Sunrise & Sunset times
    # Get local midnight to ensure sunrise/sunset are calculated for the birthday itself
    local_midnight = local_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Using Astral for robust sunrise and sunset calculations instead of PySwisseph 
    # to avoid errors on platforms where Ephemeris files are missing (like Render).
    from astral import LocationInfo
    from astral.sun import sun
    
    loc = LocationInfo("Local", "Region", timezone_str, lat, lon)
    
    try:
        s = sun(loc.observer, date=local_midnight.date(), tzinfo=local_tz)
        res_riseUTC = s["sunrise"]
        res_setUTC = s["sunset"]
        
        # Convert Astral's timezone-aware response directly to the requested format
        suryodayam = res_riseUTC.strftime("%I:%M %p")
        suryastamayam = res_setUTC.strftime("%I:%M %p")
    except Exception as e:
        print(f"Astral Sun Calculation Failed: {e}")
        suryodayam = "06:00 AM"
        suryastamayam = "06:00 PM"
    
    # Astral has already given us formatted 'suryodayam' and 'suryastamayam'

    # 6. Ayanam, Rutuvu, & Telugu Masam
    # Ayanam: Sun between 270 (Capricorn) and 90 (Cancer) is Uttarayana
    if sun_lon >= 270 or sun_lon < 90:
        ayanam = "ఉత్తరాయణం (Uttarayanam)"
    else:
        ayanam = "దక్షిణాయణం (Dakshinayanam)"
        
    # Rutuvu: 6 seasons, each spanning 60 degrees of solar longitude starting from 0 (Vasantha)
    rutu_index = int((sun_lon % 360) / 60)
    rutuvu = TELUGU_RUTUVULU[rutu_index]
    
    # Masam (Month): Exact Telugu Lunar Month mapped to Sun/Moon Amavasya boundaries
    def find_amavasya(jd_guess):
        jd_val = jd_guess
        for _ in range(10):
            m = swe.calc_ut(jd_val, swe.MOON)[0][0]
            s = swe.calc_ut(jd_val, swe.SUN)[0][0]
            df = (m - s) % 360
            if df > 180: df -= 360
            jd_val -= df / 12.190749
            if abs(df) < 0.0001:
                break
        return jd_val

    diff_moon_sun = (moon_lon - sun_lon) % 360
    days_since = diff_moon_sun / 12.190749
    days_to = (360 - diff_moon_sun) / 12.190749
    
    jd_start = find_amavasya(jd - days_since)
    jd_end = find_amavasya(jd + days_to)
    
    # Calculate exact month name mapping based on the Amavasya's Solar intersection
    amavasya_sun_lon = swe.calc_ut(jd_start, swe.SUN)[0][0]
    rasi_idx = int((amavasya_sun_lon % 360) / 30)
    masam_index = (rasi_idx + 1) % 12
    telugu_masam_name = TELUGU_MASALU[masam_index]
    
    EN_TO_TELUGU_MONTHS = {
        "january": "జనవరి", "february": "ఫిబ్రవరి", "march": "మార్చి",
        "april": "ఏప్రిల్", "may": "మే", "june": "జూన్",
        "july": "జూలై", "august": "ఆగస్టు", "september": "సెప్టెంబర్",
        "october": "అక్టోబర్", "november": "నవంబర్", "december": "డిసెంబర్"
    }
    
    def format_jd(jd_time):
        y, m_dt, d, h = swe.revjul(jd_time)
        dt_val = datetime.datetime(y, m_dt, d, int(h), int((h%1)*60))
        dt_val = pytz.utc.localize(dt_val).astimezone(local_tz)
        en_month = dt_val.strftime("%B").lower()
        te_month = EN_TO_TELUGU_MONTHS.get(en_month, en_month)
        return f"{te_month}-{d:02d}"

    telugu_masam = f"{masam_index+1}. {telugu_masam_name} మాసం ({format_jd(jd_start)} నుంచి {format_jd(jd_end)} వరకు)"

    # 7. Extract Planetary Positions
    planet_positions = []
    for n, longt in base_pos.items():
        r = RASI_TELUGU[int(longt/30)]
        d = int(longt % 30)
        m = int(((longt % 30) - d) * 60)
        
        # calculate nakshatra for the planet
        p_nak_idx = int(longt / NAKSHATRA_SIZE)
        p_nak_name = NAKSHATRAS_TELUGU[p_nak_idx]
        p_nak_offset = longt - (p_nak_idx * NAKSHATRA_SIZE)
        p_padam = int(p_nak_offset / PADAM_SIZE) + 1
        
        strength_pct = int(((longt % 30) / 30) * 100)
        
        # Check favorability using exact logic from birth chart
        green_planets = ["సూర్యుడు", "భూమి", "కుజుడు", "గురు", "కేతు", "చంద్రుడు"]
        # Favorable for Guru Lagnas, otherwise Sani Lagnas
        positive_lagnas = ["మీనం", "మేషం", "కర్కాటకం", "సింహం", "వృశ్చికం", "ధనస్సు"]
        
        is_green = any(p in n for p in green_planets)
        
        if lagna in positive_lagnas:
            color = "#22c55e" if is_green else "#ef4444"
        else:
            color = "#ef4444" if is_green else "#22c55e"
        
        planet_positions.append({
            "name": n,
            "rasi": r,
            "degree": f"{d}°{m:02d}′",
            "nakshatra": p_nak_name,
            "padam": p_padam,
            "strength": strength_pct,
            "color": color,
            "is_hand": False
        })

        # Process hands for this planet
        angles = [180] + SPECIAL_HANDS.get(n, [])
        for a in angles:
            hl = (longt + a) % 360
            hr = RASI_TELUGU[int(hl/30)]
            hd = int(hl % 30)
            hm = int(((hl % 30) - hd) * 60)
            
            # Use same nakshatra logic for hand
            h_nak_idx = int(hl / NAKSHATRA_SIZE)
            h_nak_name = NAKSHATRAS_TELUGU[h_nak_idx]
            h_nak_offset = hl - (h_nak_idx * NAKSHATRA_SIZE)
            h_padam = int(h_nak_offset / PADAM_SIZE) + 1
            h_strength = int(((hl % 30) / 30) * 100)

            planet_positions.append({
                "name": n,
                "rasi": hr,
                "degree": f"{hd}°{hm:02d}′",
                "nakshatra": h_nak_name,
                "padam": h_padam,
                "strength": h_strength,
                "color": color,
                "is_hand": True
            })


    # Store birth info in session for other pages
    session['birth_info'] = {
        'name': name,
        'dob': dob,
        'tob': tob,
        'place': place,
        'lat': lat,
        'lon': lon,
        'timezone_str': timezone_str,
        'day_name': day_name,
        'nakshatra': nakshatra,
        'padam': padam,
        'nak_elapsed': f"{elapsed_h}గం {elapsed_m}ని",
        'nak_remaining': f"{remain_h}గం {remain_m}ని",
        'nak_index': nak_index,
        'elapsed_h': elapsed_h,
        'elapsed_m': elapsed_m,
        'lagna_deg': lagna_degree_str,
        'lagna': lagna,
        'moon_lon': moon_lon,
        'tithi_paksha': tithi_paksha,
        'tithi_name': tithi_name,
        'tithi_elapsed': tithi_elapsed_str,
        'tithi_remaining': tithi_remaining_str,
        'telugu_year': telugu_year,
        'year_index': year_index,
        'kaliyuga_year': kaliyuga_year,
        'thraitha_sakamu': thraitha_sakamu,
        'suryodayam': suryodayam,
        'suryastamayam': suryastamayam,
        'ayanam': ayanam,
        'rutuvu': rutuvu,
        'telugu_masam': telugu_masam,
        'planet_positions': planet_positions
    }

    return render_template(
        "chart.html",
        chart=chart_data,
        lagna=lagna,
        lagna_deg=lagna_degree_str,
        houses=houses_map,
        name=name,
        dob=dob,
        tob=tob,
        place=place,
        day_name=day_name,
        nakshatra=nakshatra,
        padam=padam,
        nak_elapsed=f"{elapsed_h}గం {elapsed_m}ని",
        nak_remaining=f"{remain_h}గం {remain_m}ని",
        nak_index=nak_index,
        elapsed_h=elapsed_h,
        elapsed_m=elapsed_m,
        all_nakshatras=NAKSHATRAS_TELUGU
    )

@app.route("/chart2", methods=["GET", "POST"])
def chart2():
    # Get birth info from session
    birth_info = session.get('birth_info', {})
    
    # Check for manual correction submission
    correction_type = request.form.get("correction_type")
    if correction_type == "manual":
        # Process new timing overrides
        manual_nakshatra = request.form.get("manual_nakshatra", "")
        if manual_nakshatra:
            birth_info['nakshatra'] = manual_nakshatra
            
        try:
            birth_info['elapsed_h'] = int(request.form.get("manual_elapsed_h", birth_info.get('elapsed_h')))
            birth_info['elapsed_m'] = int(request.form.get("manual_elapsed_m", birth_info.get('elapsed_m')))
            birth_info['nak_index'] = int(request.form.get("manual_nak_index", birth_info.get('nak_index')))
            birth_info['padam'] = int(request.form.get("manual_padam", birth_info.get('padam')))
        except ValueError:
            pass # fallback to current session variables if int(map) fails

        nak_elapsed = request.form.get("manual_nak_elapsed", "")
        nak_remaining = request.form.get("manual_nak_remaining", "")
        
        if nak_elapsed:
            birth_info['nak_elapsed'] = nak_elapsed
        if nak_remaining:
            birth_info['nak_remaining'] = nak_remaining
            
        # Re-save updated birth info properties
        session['birth_info'] = birth_info
    
    # Extract values
    dob = birth_info.get('dob', '')
    tob = birth_info.get('tob', '')
    name = birth_info.get('name', '')
    place = birth_info.get('place', '')
    day_name = birth_info.get('day_name', '')
    nakshatra = birth_info.get('nakshatra', '')
    lagna = birth_info.get('lagna', '')
    nak_elapsed = birth_info.get('nak_elapsed', '0గం 0ని')
    nak_remaining = birth_info.get('nak_remaining', '0గం 0ని')
    nak_index = birth_info.get('nak_index', 0)
    elapsed_h = birth_info.get('elapsed_h', 0)
    elapsed_m = birth_info.get('elapsed_m', 0)
    padam = birth_info.get('padam', 1)

    # Parse birth datetime
    timezone_str = birth_info.get('timezone_str', 'Asia/Kolkata')
    local_tz = pytz.timezone(timezone_str)
    try:
        birth_dt = local_tz.localize(
            datetime.datetime.strptime(dob + " " + tob, "%Y-%m-%d %H:%M")
        )
    except ValueError:
        return "❌ Invalid date/time format"

    # ===== CALCULATE FULL 120-YEAR DASA CYCLE =====
    
    # 1. Calculate birth Mahadasha
    birth_dasa, dasa_index = get_running_dasa(nak_index, padam)
    
    # 2. Calculate elapsed time in birth dasa (Based on Rasi-based 30-degree movement)
    moon_lon = birth_info.get('moon_lon')
    if moon_lon is None:
        # Fallback to manual timing if longitude not stored
        elapsed_minutes = nak_minutes(elapsed_h, elapsed_m)
        fraction = elapsed_minutes / TOTAL_NAK_MINUTES if TOTAL_NAK_MINUTES > 0 else 0
    else:
        # According to the text, each Dasa is 30 degrees (9 padas/1 Rasi)
        fraction = (moon_lon % 30) / 30
    
    birth_dasa_years = DASA_YEARS.get(birth_dasa, 10)
    elapsed_years_in_birth_dasa = birth_dasa_years * fraction
    
    # 3. Calculate start date of birth dasa (before birth)
    birth_dasa_start = birth_dt - datetime.timedelta(days=int(elapsed_years_in_birth_dasa * 365.25))
    birth_dasa_end = add_years(birth_dasa_start, birth_dasa_years)
    
    # 4. Get today's date for current dasa detection
    today = datetime.datetime.now()
    today_str = today.strftime("%d-%m-%Y")
    
    # 5. Calculate ALL 12 Mahadashas in sequence (120 years)
    all_dasas = []
    start_date = birth_dasa_start
    
    # Variables to track current dasa
    current_maha_index = -1
    current_maha_name = ""
    current_maha_start = ""
    current_maha_end = ""
    current_maha_years = 0
    current_maha_age_start = ""
    current_maha_age_end = ""
    
    # Start from birth dasa and go through all 12
    for i in range(12):
        dasa_index_calc = (dasa_index + i) % 12
        dasa_name = DASA_ORDER[dasa_index_calc]
        dasa_years = DASA_YEARS.get(dasa_name, 10)
        
        end_date = add_years(start_date, dasa_years)
        start_str = start_date.strftime("%d-%m-%Y")
        end_str = end_date.strftime("%d-%m-%Y")
        
        # Calculate Anthara dasas for this Mahadasha
        antharas = calculate_anthara_periods(dasa_name, start_date, end_date, lagna, birth_dt)
        
        # Check if TODAY is within this dasa
        is_current_today = is_date_within_range(today_str, start_str, end_str)
        
        # Check if this is the birth dasa
        is_birth_dasa = (i == 0)
        
        # Determine favorability for full Mahadasa
        is_maha_favorable = is_dasa_favorable(lagna, dasa_name)
        
        # Add color and icon to dasa
        dasa_color = "#22c55e" if is_maha_favorable else "#ef4444"
        dasa_icon = PLANET_ICONS.get(dasa_name, "•")
        
        
        # Calculate Age
        age_start_str = ""
        age_end_str = ""
        
        age_start_days = (start_date - birth_dt).days
        if age_start_days >= 0:
            age_start_y = age_start_days // 365
            age_start_m = (age_start_days % 365) // 30
            age_start_str = f"{age_start_y}సం, {age_start_m}నెలలు"
            
        age_end_days = (end_date - birth_dt).days
        if age_end_days >= 0:
            age_end_y = age_end_days // 365
            age_end_m = (age_end_days % 365) // 30
            age_end_str = f"{age_end_y}సం, {age_end_m}నెలలు"

        # Add this Mahadasha to list
        all_dasas.append({
            "maha": dasa_name,
            "start": start_str,
            "end": end_str,
            "years": dasa_years,
            "antharas": antharas,
            "is_current": is_current_today,
            "is_birth_dasa": is_birth_dasa,
            "color": dasa_color,
            "icon": dasa_icon,
            "is_favorable": is_maha_favorable,
            "age_start": age_start_str,
            "age_end": age_end_str
        })
        
        # If this is current dasa, store its info
        if is_current_today:
            current_maha_index = i
            current_maha_name = dasa_name
            current_maha_start = start_str
            current_maha_end = end_str
            current_maha_years = dasa_years
            current_maha_age_start = age_start_str
            current_maha_age_end = age_end_str
        
        # Move to next Mahadasha start date
        start_date = end_date
    
    # 6. If no dasa matches today, use birth dasa as current
    if current_maha_index == -1:
        today_dt = datetime.datetime.strptime(today_str, "%d-%m-%Y")
        birth_start_dt = datetime.datetime.strptime(birth_dasa_start.strftime("%d-%m-%Y"), "%d-%m-%Y")
        
        if today_dt < birth_start_dt:
            current_maha_index = 0
        else:
            current_maha_index = 11
        
        current_maha_name = all_dasas[current_maha_index]["maha"]
        current_maha_start = all_dasas[current_maha_index]["start"]
        current_maha_end = all_dasas[current_maha_index]["end"]
        current_maha_years = all_dasas[current_maha_index]["years"]
        current_dasa_favorable = all_dasas[current_maha_index]["is_favorable"]
        current_maha_age_start = all_dasas[current_maha_index].get("age_start", "")
        current_maha_age_end = all_dasas[current_maha_index].get("age_end", "")
    else:
        current_dasa_favorable = is_dasa_favorable(lagna, current_maha_name)
    
    # 7. Calculate elapsed/remaining for CURRENT dasa
    current_start_dt = datetime.datetime.strptime(current_maha_start, "%d-%m-%Y")
    current_end_dt = datetime.datetime.strptime(current_maha_end, "%d-%m-%Y")
    
    # Calculate elapsed days in current dasa
    total_days_current = (current_end_dt - current_start_dt).days
    elapsed_days_current = (today - current_start_dt).days
    
    # Ensure days are within range
    elapsed_days_current = max(0, min(elapsed_days_current, total_days_current))
    
    elapsed_years_current = elapsed_days_current / 365.25
    remaining_years_current = (total_days_current - elapsed_days_current) / 365.25
    
    # 8. Calculate total years covered
    total_years_covered = sum(dasa.get("years", 10) for dasa in all_dasas)
    
    # 9. Current year for reference
    current_year = datetime.datetime.now().year
    
    # 10. Get planet colors and icons for current dasa
    current_dasa_color = PLANET_COLORS.get(current_maha_name, "#FFD700")
    current_dasa_icon = PLANET_ICONS.get(current_maha_name, "☉")

    return render_template(
        "chart2.html",
        # Compact header info
        name=name,
        dob=dob,
        tob=tob,
        place=place,
        day_name=day_name,
        
        # Nakshatra info
        nakshatra=nakshatra,
        padam=padam,
        nak_elapsed=nak_elapsed,
        nak_remaining=nak_remaining,
        
        # Current dasa info
        maha=current_maha_name,
        maha_start=current_maha_start,
        maha_end=current_maha_end,
        maha_age_start=current_maha_age_start,
        maha_age_end=current_maha_age_end,
        total_years=current_maha_years,
        completed_years=round(elapsed_years_current, 2),
        remaining_years=round(remaining_years_current, 2),
        current_dasa_color=current_dasa_color,
        current_dasa_icon=current_dasa_icon,
        current_dasa_favorable=current_dasa_favorable,
        
        # Full cycle info
        all_dasas=all_dasas,
        total_cycle_years=total_years_covered,
        
        # Planet colors and icons
        planet_colors=PLANET_COLORS,
        planet_icons=PLANET_ICONS,
        
        # Other
        now_date=today_str,
        current_year=current_year
    )

@app.route("/chart3")
def chart3():
    """Display Dwadasa Grahamula Phalitalu"""
    current_year = datetime.datetime.now().year
    birth_info = session.get('birth_info', {})
    lagna = birth_info.get('lagna', '')
    return render_template("chart3.html", current_year=current_year, lagna=lagna)

@app.route("/panchangam")
def panchangam():
    """Display Panchangam Information"""
    birth_info = session.get('birth_info', {})
    if not birth_info:
        return redirect(url_for('index'))
    return render_template("panchangam.html", **birth_info)

@app.route("/go-to-birth-chart")
def go_to_birth_chart():
    """Redirect to birth chart with session data"""
    birth_info = session.get('birth_info', {})
    if birth_info:
        # Instead of just rendering chart.html which requires complex SWISSEPH calculations,
        # we repopulate a pseudo-form request to the main chart endpoint or we can 
        # just regenerate chart() if we refactored it. Since /chart expects POST data,
        # we'll build a simple redirect page that auto-submits.
        return f"""
        <html>
            <body onload="document.forms[0].submit()">
                <form action="/chart" method="POST">
                    <input type="hidden" name="name" value="{birth_info.get('name', '')}">
                    <input type="hidden" name="dob" value="{birth_info.get('dob', '')}">
                    <input type="hidden" name="tob" value="{birth_info.get('tob', '')}">
                    <input type="hidden" name="place" value="{birth_info.get('place', '')}">
                    <input type="hidden" name="lat" value="{birth_info.get('lat', '')}">
                    <input type="hidden" name="lon" value="{birth_info.get('lon', '')}">
                </form>
                <p>Loading Birth Chart...</p>
            </body>
        </html>
        """
    else:
        # Redirect to index if no birth info
        return redirect(url_for('index'))

@app.route("/results", methods=["GET", "POST"])
def results():
    """Calculate and display results based on planet own-house rules and party logic"""
    # Check for password authorization in session
    if 'results_authorized' not in session:
        # Check if password was submitted
        submitted_password = request.form.get('password')
        if submitted_password:
            if submitted_password == '9700836368':
                session['results_authorized'] = True
            else:
                return render_template("results_password.html", error=True)
        else:
            # Not authorized and no password submitted, show password entry page
            return render_template("results_password.html", error=False)

    birth_info = session.get('birth_info', {})
    if not birth_info:
        return redirect(url_for('index'))
    
    planet_positions = birth_info.get('planet_positions', [])
    lagna = birth_info.get('lagna', '')
    
    # Rasi ordering to find Bhava distances
    RASI_ORDER = ["మేషం", "వృషభం", "మిథునం", "కర్కాటకం", "సింహం", "కన్య", "తులా", "వృశ్చికం", "ధనస్సు", "మకరం", "కుంభం", "మీనం"]
    
    # Party Mapping
    GURU_PARTY_LAGNAS = ["మీనం", "మేషం", "కర్కాటకం", "సింహం", "వృశ్చికం", "ధనస్సు"]
    
    native_party = "గురు వర్గము" if lagna in GURU_PARTY_LAGNAS else "శని వర్గము"
    
    GURU_PARTY_PLANETS = ["సూర్యుడు", "భూమి", "కుజుడు", "గురు", "కేతు", "చంద్రుడు"]
    
    # Bitter Enemies (fixed pairs)
    BITTER_ENEMIES = {
        "కుజుడు": "శుక్రుడు",
        "శుక్రుడు": "కుజుడు",
        "మిత్ర": "భూమి",
        "భూమి": "మిత్ర",
        "చిత్ర": "కేతు",
        "కేతు": "చిత్ర",
        "చంద్రుడు": "రాహు",
        "రాహు": "చంద్రుడు",
        "సూర్యుడు": "శని",
        "శని": "సూర్యుడు",
        "బుధుడు": "గురు",
        "గురు": "బుధుడు"
    }

    # Detailed Planetary Rulerships (ఆధీనములో ఉన్నవి)
    PLANET_RULERSHIPS = {
        "సూర్యుడు": "పిత, ఆత్మ, తనువు, రాజ్యము, ప్రభావము, ధైర్యము, అధికారము, నేత్రము, పిత్తము, శూరత్వము, శక్తి, విదేశ పర్యటన, జ్ఞాన తేజము, పరాక్రమము, ఉష్ణము, అగ్ని, ధర్మ ధ్యాస, కడుపు, కన్ను, పాలనాశక్తి, ప్రభుత్వ భూములు, కోర్టు వ్యవహారములు, బంజరు భూములు, గుండ్రని ఆకారముండు పొలములు, రారాజు యోచన, గ్రామాధీన జాగాలు, ఎర్రచందనము, ముద్రాధికారము, తెల్ల జిల్లేడు, తూర్పు, ఆంగ్ల విద్య, ఆదివారము, చైత్రమాసము, రాజభవనములు, వేడిని పుట్టించు నీలి వెలుగులు, పై అంతస్థులు గల భవనములు. (జాతి: క్షత్రియ, రంగు: గోధుమరంగు)",
        "చంద్రుడు": "బుద్ధి, నీరు, స్త్రీలు, మనస్సు, సౌందర్యము, జల సౌఖ్యము, బలము, పంటలు, వెండి, యాత్రలు, గుర్రపుస్వారీ, నిద్ర, వేగము, సుగంధములు, మాతృ ప్రీతి, కోనేర్లు, బావులు, కీర్తి, స్త్రీ సుఖము, తెల్లని మెత్తని గుడ్డలు, సముద్రములు, పుష్ఠి, పూలు, నదులు, యాత్రలు, తెలుపురంగు, చెరువులు, శ్వాస, కడుపు, ముత్యములు, ముఖ అలంకరణ, గర్భము, మృదుత్వము, సుఖభోజనము, పాలు, మనోజపము, విమానయానము, విమానములు, నావలు, అంతస్తుల భవనములు, చౌడు భూములు, లాడ్జీలు, వర్షము, ముద్రణాధికారము, రాజ చిహ్నము, సన్మానము, ధాన్యములో వడ్లు, వెన్నెల, శయన గృహములు, సంతోషము, వీర్యబలము, అశ్వ వాహనము, జ్ఞాపకశక్తి, దూరాలోచన, శిరో ఆరోగ్యము, మెదడు బలము, గ్రాహితశక్తి, ఈతలో నైపుణ్యము, నదీస్నానము, నీటి ప్రదేశములు, చౌడు, జలచరములు, ఇంగ్లీషు భాష, విలాస వస్తువులు, వాయువ్యదిశ, సోమవారము, తెల్లని పూలు, మల్లె తోటలు. (జాతి: బ్రాహ్మణ, రంగు: తెల్లనిరంగు)",
        "కుజుడు": "పరాక్రమము, కోపము, సేనాధిపత్యము, సాహసము, విస్ఫోటనము, బాంబులు, తుపాకులు, మారణాయుధములు, కోతులు, కుక్కలు, కోరలు గల కూరజంతువులు, కొమ్ములుగల ఎద్దులు, శస్త్రవిద్య, తర్కశాస్త్రము, శత్రువృద్ధి, ఉష్ణము, ఎర్రభూమి, రాళ్ళభూమి, కొండలు, బండలు, ఎరుపు రంగు, రక్తము, యవ్వనము, యువకులు, యుక్తవయస్సు స్త్రీల పరిచయము, మెట్టభూమి, పట్టుదల, ప్రభుభక్తి, లక్ష్యమును ఛేదించుట, జయము, దక్షిణ దిక్కు అరణ్యములు, అరణ్య సంచారము, సండ్రచెట్టు, వేట జరుపుట, యువరాజు, కట్టెలు, ప్రవాహము, మరణశిక్ష, కోటలు, బురుజులు, సోదరబలము, చెల్లెండ్రు, వెంట్రుకలు, మీసము, కూరమైన ముఖవర్చస్సు, దీర్ఘబాహువులు, అంగరక్షకులు, పోలీసు, మిలటరీ, కందులు, సన్మానములు, సైన్య బలము, రాతి గుహలు, రచ్చబండలు, మంగమాణ్యములు, కుమ్మర మాణ్యములు, కుమ్మరాములు, వ్రణ వైద్యము, పిందెలు, కాయలు, మంగళవారము, నక్సలైట్లు. (జాతి: నాయిబ్రాహ్మణ, రంగు: ఎరుపురంగు)",
        "బుధుడు": "జ్యోతిష్యము, గణితశాస్త్రము, మంత్రములు, యంత్రములు, వ్యాపారము, తల్లివైపు బంధువులు, మామగారు, యుక్తి, శిల్పవిద్య, మంత్ర తంత్రవిద్యలు, వేద విచారణ, హాస్యము, వైద్యము, జ్ఞానము, లిపి, పైత్యము, దృష్టిబలము, ఆకుపచ్చరంగు, శిల్పకళ, చిత్రలేఖనము, శివభక్తి, దాస దాసీ జన అభివృద్ధి, సంధిచేయుట, చాకచక్యముగా మాట్లాడుట, పొట్టితనము, విచిత్ర రచనలు, యుక్తియుక్త జ్ఞానము, చమత్కారము, సైంటిస్టు, ఉత్తరము దిక్కు బుధవారము, స్మశానభూములు, గోరీలు, దిబ్బలు, దింపుడు కల్లములు, దయ్యాల ఇండ్లు, బలి ఇచ్చుస్థానములు, దయ్యాలు, పాడుపడిన స్థలములు, వ్యాపార స్థలములు, అంగళ్ళు, శూన్యములు, సూక్ష్మములు, భూతవైద్యము, ఉత్తరేణి చెట్టు, పెసలు ధాన్యము. (జాతి: వైశ్య, రంగు: ఆకుపచ్చ రంగు)",
        "గురు": "భూమిమీదున్న ప్రపంచ ధనము, వేదవిద్య, ప్రపంచ విద్య, పుత్రులు, జ్యోతిష్యము, గురువుగా ఉండుట, సత్కర్మ చేయుట, శబ్దశాస్త్రము, బ్రాహ్మణత్వము, యజ్ఞాది క్రతువులు, బంగారు, గృహము, అశ్వము, గజము, ఆచారము, సుజనత్వము, శాంతము, మంత్రిత్వము, ఐశ్వర్యము, బంధువృద్ధి, సత్యము, పురాణములు, పౌరాణికము, పుత్రపౌత్ర వృద్ధి, మంచి సంతతి, పూజనీయత, అధికార గౌరవములు, గ్రామాధికారము, పసుపు రంగు, మాట చమత్కారము, మేథావి, తీర్థయాత్ర దేవతా దర్శనములు, గ్రంథ పఠనము, అగ్రస్థానము, తియ్యని ఆహారము, సంస్కృతి, పాండిత్యములో ప్రతిభ, బంధుబలము, సంస్కృత భాష, గ్రంథరచన, ముక్తి సాధన, పౌరోహిత్యము, యజుర్వేదము, సమయస్ఫూర్తి, మత సిద్ధాంతము, దేవాలయ నిర్మాణము, చవుటి భూములు, కళ్యాణ మందిరములు, భజన మందిరములు నిర్మించుట, బోధనావృత్తి. (జాతి: బ్రాహ్మణ, రంగు: పసుపు రంగు)",
        "శుక్రుడు": "వివాహము, నాటక సాహిత్యము, స్త్రీ సౌఖ్యము, కామము, భోగము, వ్యభిచారము, వాహన సుఖము, ఆభరణములు, ఐశ్వర్యము, ముద్రణాధికారము, హాస్యము, మేహము, వేశ్యా సంభోగము, కన్యత్వ లభ్యము, తెల్లని వస్త్రము, సుగంధములు, సౌందర్యము, జలక్రీడ, చిత్రలేఖనము, కవిత్వము, గ్రంథరచన, సంగీతము, సామవేదము, మద్యపానము, నృత్యము, యువతి, మనోభావములు, అష్ట భోగములు, అష్ట ఐశ్వర్యములు, శృంగార కావ్య రచనలు, దేహసుఖము, సౌందర్యము, సుకుమారము, వీణ లేక వేణు గానము, వాహన సౌఖ్యము, అన్యస్త్రీల ఆలింగనము, బహు స్త్రీ సంగమము, కళానైపుణ్యము, వీర్యబలము, శివభక్తి, శాంభవీ విద్య, మృధురతి, స్త్రీలకు మిక్కిలి ప్రియముగా ఉండుట, వివాహములలో విందులలో పాల్గొనుట, సభా సన్మానములు, వేశ్యలు సన్నిహితముగా ఉండుట, వ్యసనాలలో స్త్రీకి లొంగిపోవడము, తాంబూలము, మాంసభక్షణ, శక్తిపూజలు, పశువుల ఇండ్లు, బండ్లు విడుచు స్థలము, వ్యభిచార గృహములు, పశువుల ఇళ్ళు, వంట కట్టెలు పెట్టుచోటు, శయన గృహములు, నవ యవ్వనుల మిత్రత్వము, కామకేళీ విలాసము. (జాతి: నంభీబ్రాహ్మణ, రంగు: తెలుపు రంగు)",
        "శని": "ఆయుషు, నీచవిద్య, నీచ దేవతోపాసన, మరణము, దుఃఖము, అసత్యము, అధర్మము, బంధనము, కురూపము, శాంతము, దుష్ప్రవర్తన, పాపము, నరకము, నీచ జీవనము, రోగములు, దాసీజన సౌఖ్యము, విధవ సౌఖ్యము, నపుంసకత్వము, పౌరుషహీనము, పాపార్జన, అనాచారము, జైలు, కృశించిన శరీరము గలవాడు, చినిగిన వస్త్రములు కలవాడు, బ్రాహ్మణ ద్వేషి, దున్నలకు అధిపతి, భయంకరుడు, జంతువులతో రమించువాడు, నీచదేవతోపాసన, పాతాళ గృహము, కంచర గాడిదలు, చెడు ప్రవర్తన, దారిద్ర్యము, వంటలవాడు, మద్యపానము విక్రయించువాడు, మాంసవిక్రయుడు, మాంసవిక్రయశాల, భోజనవిక్రయము, ఇనుము అంగడి, శిథిల గృహము దాని నివాసము, కాఫీ హోటళ్ళు, దిబ్బలు, మలవిసర్జన స్థలములు, స్మశానము, చీకటిల్లు, సమాధులు, జమ్మిచెట్టు, నూగులు, వృత్వము, మారణాస్త్రములు, నలుపురంగు, కామదహన స్థలము, పీర్ల గుండము, సారాయి, కల్లు, అంగళ్ళు, ఇనుము, ఇనుప వ్యాపారము. (జాతి: మాదిగ/మాల, రంగు: నలుపు రంగు)",
        "రాహు": "కౄరత్వము, పాపము, నీచవిద్య, నీచ జీవనము, చోర జీవనము, విషములు, సర్పములు, తేళ్ళు, మండ్రగబ్బలు, క్రిమికీటకాదులు, పాడు పడిన గృహములు, పుట్టలు, చెదలు, వంపులు, మినుములు ధాన్యము, గరికగడ్డి, మాంస విక్రయము, మాసిన వస్త్రములు ధరించుట, పొగరంగు, మోసము చేయుట, పాములు పట్టుట, చెప్పులు కుట్టుట, దొంగతనము చేయుట, మత్తు పదార్థములను అమ్ముట, మత్తు పదార్థములను సేవించుట, అపసవ్యముగా తిరుగుట, చండాలత్వము, రాక్షసత్వము, హత్యలు చేయడము. (జాతి: వాల్మీకి/బోయ, రంగు: సిమెంటు రంగు)",
        "కేతు": "ఆత్మజ్ఞానము, సన్న్యాసత్వము, నిరాకార భక్తి, దైవభక్తి, ఆశ్రమ నివాసము, సన్న్యాసులతో స్నేహము, వేదాంతము, దేవుని ధ్యాస, చిత్రవర్ణము, దర్భమొక్కలు, ఉలవల ధాన్యము, తపస్సు, మౌనము, అపసవ్య లిపిని వ్రాయడము లేక చదవడము, వైరాగ్యము, శూద్రగోష్టి, మహమ్మదీయులు, హేతువాదము. (జాతి: ఇస్లామీయులు, రంగు: కొన్ని కలిసిన రంగులు)",
        "భూమి": "గనులు, ఖనిజములు, ఇళ్ళ స్థలములు, గుహలు, మంచు ప్రదేశములు, హిమపాతము, అరికాళ్ళు అరిచేతులు నవ్వలు రావడము, అరికాళ్ళు అరిచేతులు చీలడము, చర్మరోగములు, సువాసనలు, సుగంధ ద్రవ్యములు, మొలలు. (జాతి: జైనులు, రంగు: నీలిరంగు)",
        "మిత్ర": "నిద్ర, నిద్రలోని కదలికలు, నిద్రలోవచ్చు తలనొప్పి, నిద్రలేమి, మానసిక వ్యాధులు, ఆత్మజ్ఞానమునకు దారి, స్వప్నములు, నిద్రలోని కదలికలు, స్వప్నములోని కదలికలు. (జాతి: క్రైస్తవులు, రంగు: వక్క (పోక) రంగు)",
        "చిత్ర": "అకాల మరణము తర్వాత పరకాయ ప్రవేశము, సూక్ష్మశరీర ముఖ జ్ఞానము, సూక్ష్మములచేత బాధింపబడడము, అకాలమృత్యువు, తాత్కాలిక మరణము, మనో బాధలు లేకుండా జ్ఞానచింతలో ఉండుట, అదృశ్యముగా ఉండి కొన్ని నిమిషములు కనిపించుట. (జాతి: సిక్కులు, రంగు: లేత పసుపు)"
    }

    # Detailed Bhava Interpretations from user text
    DETAILED_BHAVA_MEANINGS = {
        1: {
            "title": "ప్రథమ స్థానము (తనువు)",
            "meaning": "శరీరము, ఆత్మ, రూపము, స్వభావము, అంగ సౌష్టవమును గురించిన విషయములు.",
            "shubha": "మంచి బలమైన శరీరము, అందమైన రూపం, మంచి కొలతలు గల అంగసౌష్టవం కల్గియుండును.",
            "paapa": "బలహీనమైన దేహం, అంగలోపం, అనారోగ్యాలకు అనువుగా ఉన్న దేహం, అంగసౌష్టవం లేని దేహం లభించును.",
            "neutral": "మధ్యతరగతి ఆరోగ్యము, అందము, అంగసౌష్టవముగల శరీరముండును."
        },
        2: {
            "title": "ద్వితీయ స్థానము (ధనము)",
            "meaning": "ధనము, వాక్కు, కుటుంబము, నేత్రము, కర్ణము, ముఖ వర్చస్సు, మరణము.",
            "shubha": "ముఖవర్చస్సులో ప్రత్యేకత, ఆకర్షణీయమైన కళ్ళు, ఆయుర్బలం, దైవభక్తి గల మంచి కుటుంబం లభించును. వాక్చాతురత కల్గియుండును.",
            "paapa": "ముఖంలో అందం ఉండదు, మాటలో ఆకర్షణ ఉండదు, కుటుంబంలో అన్యోన్యత లోపించును, ధన ఇబ్బందులు ఎదురవుతాయి.",
            "neutral": "రెండవ స్థానములోని విషయములు మధ్యరకముగా అందుచుండును. మంచి చెడు కాకుండా తటస్థముగా ఉండును."
        },
        3: {
            "title": "తృతీయము (సోదర స్థానము)",
            "meaning": "సోదరులు, ధైర్యము, పరాక్రమము.",
            "shubha": "అన్నదమ్ముల వలన సుఖము లేకున్నా వ్యతిరేఖము లేకుండా సాధారణముగా ఉందురు. కష్టముండదు.",
            "paapa": "సోదర వర్గం వలన బాధలు, వివాహం ఆలస్యం, దాయాదులతో ఇబ్బందులు, ఉత్సాహం లేని నీచ జీవనం, సేవక వృత్తి.",
            "neutral": "సాధారణ ఫలితాలు ఉండును."
        },
        4: {
            "title": "చతుర్థము (మాతృస్థానము)",
            "meaning": "తల్లి, వాహనము, భూమి, గృహము, వ్యవసాయము, పంటలు, బంధువులు.",
            "shubha": "గృహము, వస్తు వాహనములు, భూములు, జలాశయములు కల్గును. బంధు మిత్రుల బలము, మాతృప్రీతి, సుఖ సౌఖ్యములు కల్గును.",
            "paapa": "పైన చెప్పిన శుభ ఫలితములకు వ్యతిరేఖ ప్రభావం ఉండును. సుఖ సౌఖ్యములు లోపించును.",
            "neutral": "వస్తు భూమి లాభాలు మధ్యరకముగా ఉండును."
        },
        5: {
            "title": "పంచమము (విద్యాస్థానము)",
            "meaning": "విద్య, జ్ఞానము, జ్ఞప్తి శక్తి, సంతానము, మంత్రి పదవి, వివేకము.",
            "shubha": "మంచి సంతానం, మంత్రి పదవి, వివేకము, వినయము, పాండిత్యం, గ్రంథ రచనలో ప్రావీణ్యం కలుగును.",
            "paapa": "పుణ్యమును అందించదు, కానీ పాపము లేదు కనుక చెడు చేయదు. ఫలితాలు సామాన్యంగా ఉండును.",
            "neutral": "విద్య సంతాన విషయములు సామాన్యము."
        },
        6: {
            "title": "ఆరవది (శత్రుస్థానము)",
            "meaning": "శత్రువు, ఋణము, రోగము, సమస్యలు.",
            "shubha": "శత్రు, ఋణ, రోగ సమస్యలు ఉండవు. వడ్డీ వ్యాపారం లేదా వైద్యవృత్తితో ధనార్జన కలుగును.",
            "paapa": "శత్రు, ఋణ, రోగ సమస్యలు జీవితమంతా వేధించవచ్చు. మనోచింత, అపవాదులు, అప్పుల చిక్కులు ఉండును.",
            "neutral": "మధ్య రకముగా జరుగుచుండును."
        },
        7: {
            "title": "సప్తమము (కళత్ర స్థానము)",
            "meaning": "భార్య/భర్త, వివాహము, శరీర సుఖము.",
            "shubha": "కళత్రము నుండి సుఖము, ఆకర్షణీయమైన భార్య/భర్త, ధనము, ఇతర సుఖములు సకాలంలో లభించును.",
            "paapa": "భార్య/భర్త సౌఖ్యం ఉండదు, వివాహ సమస్యలు, మనోశాంతి లేకపోవడము. ఒకవేళ 8వ స్థాన దోషముంటే ఆత్మహత్య ప్రేరణ.",
            "neutral": "వివాక సౌఖ్యము సామాన్యము."
        },
        8: {
            "title": "అష్టమము (ఆయుస్థానము)",
            "meaning": "ఆయుష్షు, మరణము, జీవనము, దుఃఖము.",
            "shubha": "దీర్ఘాయువు, పుష్టి కలిగిన శరీరం, వీర్యపుష్టి, సౌఖ్యములు కల్గును. అకాల మృత్యు భయం ఉండదు.",
            "paapa": "అల్పాయుష్కుడగును, అకాల మృత్యువు, కారాగార ప్రాప్తి, పరాభవములు కలుగును. కామవాంఛ లోపించును.",
            "neutral": "మధ్యరకపు ఆయుర్దాయం."
        },
        9: {
            "title": "నవమ స్థానము (పితృ స్థానము)",
            "meaning": "తండ్రి ఆస్తి, భాగ్యము, ధనము, దైవభక్తి, జ్ఞానము.",
            "shubha": "తండ్రి ఆస్తి లభించును, సకల ఐశ్వర్యములు, నిలువయుండే ధనము, భాగ్యము, దైవభక్తి కల్గును.",
            "paapa": "నిర్భాగ్యుడగును, తీవ్ర పేదరికం, దైవభక్తి లోపం, ఆస్తి నష్టములు కలుగును.",
            "neutral": "భాగ్యము సామాన్యము."
        },
        10: {
            "title": "దశమ స్థానము (జీవన స్థానము)",
            "meaning": "వృత్తి, ఉద్యోగము, కీర్తి, గౌరవము, రాజకీయము.",
            "shubha": "ఉన్నత వృత్తి, రాజకీయ పదవులు, కీర్తి గౌరవము, అష్టభోగములు. నిగ్రహశక్తి కలిగిన జీవితం.",
            "paapa": "జీవనమునకు నిరంతర పోరాటం, గౌరవ లోపం, వృత్తిలో ఇబ్బందులు ఎదురవుతాయి.",
            "neutral": "కేవలం జీవనోపాధి లభించును."
        },
        11: {
            "title": "ఏకాదశ స్థానము (లాభ స్థానము)",
            "meaning": "లాభము, ఆదాయము, అదనపు ధనార్జన.",
            "shubha": "వివిధ రూపాలలో ఆదాయం, లాటరీ లాభాలు, కట్నకానుకలు, భారీ ధన లాభములు కలుగును.",
            "paapa": "ఆదాయంలో ఆటంకాలు, లాభాల్లో నష్టాలు, తండ్రి ఆస్తి నష్టం, దుర్వ్యసనాలు కలుగును.",
            "neutral": "సామాన్య లాభం."
        },
        12: {
            "title": "ద్వాదశ స్థానము (व्यయ స్థానము)",
            "meaning": "ఖర్చు, ప్రారబ్ధ కర్మ ముగింపు, మోక్షము, మరణ చివరి భాగము.",
            "shubha": "మంచి కార్యాలకు ఖర్చు, ఆధ్యాత్మిక చింతన, మరణ సమయమున సుఖము, స్వర్గలోక ప్రాప్తి.",
            "paapa": "బంధువులు లేని అనాధ చావు, దుర్వినియోగమయ్యే ఖర్చులు, నిరాశతో కూడిన మరణం.",
            "neutral": "ఖర్చులు ఆదాయానికి తగినట్లు ఉండును."
        }
    }

    # Own house mapping
    OWN_HOUSE_RULES = {
        "కుజుడు": "మేషం",
        "మిత్ర": "వృషభం",
        "చిత్ర": "మిథునం",
        "చంద్రుడు": "కర్కాటకం",
        "సూర్యుడు": "సింహం",
        "బుధుడు": "కన్య",
        "శుక్రుడు": "తులా",
        "భూమి": "వృశ్చికం",
        "కేతు": "ధనస్సు",
        "రాహు": "మకరం",
        "శని": "కుంభం",
        "గురు": "మీనం"
    }

    try:
        lagna_idx = RASI_ORDER.index(lagna)
    except ValueError:
        lagna_idx = 0

    # Process planets
    results_data = []
    for p in planet_positions:
        p_name = p['name']
        p_rasi = p['rasi']
        
        # is_friend?
        is_green = any(gp in p_name for gp in GURU_PARTY_PLANETS)
        is_friend = (is_green == (native_party == "గురు వర్గము"))
        
        # is_own_house?
        own_house = "N/A"
        is_own_house = False
        for rule_name, rule_house in OWN_HOUSE_RULES.items():
            if rule_name in p_name:
                own_house = rule_house
                is_own_house = (p_rasi == rule_house)
                break
        
        # bitter_enemy?
        bitter_enemy = None
        for be_key, be_val in BITTER_ENEMIES.items():
            if be_key in p_name:
                bitter_enemy = be_val
                break

        # detailed Rulership
        rulership = "N/A"
        for r_name, r_text in PLANET_RULERSHIPS.items():
            if r_name in p_name:
                rulership = r_text
                break

        results_data.append({
            "name": p_name,
            "current_rasi": p_rasi,
            "own_house": own_house,
            "is_own_house": is_own_house,
            "is_friend": is_friend,
            "bitter_enemy": bitter_enemy,
            "color": p.get('color', '#ffffff'),
            "degree": p.get('degree', ''),
            "strength": p.get('strength', 0),
            "nakshatra": p.get('nakshatra', ''),
            "padam": p.get('padam', ''),
            "rulership": rulership,
            "is_hand": p.get('is_hand', False)
        })

    # Group into Friends and Enemies (only real planets for these general lists)
    friends = [p for p in results_data if p['is_friend'] and not p.get('is_hand')]
    enemies = [p for p in results_data if not p['is_friend'] and not p.get('is_hand')]

    # Bhava Report
    bhava_report = []
    for i in range(12):
        house_num = i + 1
        house_rasi = RASI_ORDER[(lagna_idx + i) % 12]
        # Planets in this house
        occ_planets = [p for p in results_data if p['current_rasi'] == house_rasi]
        p_info = [{
            "name": p['name'], 
            "degree": p['degree'], 
            "strength": p.get('strength', 0),
            "color": p['color'],
            "is_hand": p.get('is_hand', False)
        } for p in occ_planets]
        
        # Determine house state based on occupants
        # Rule: House is 'shubha' if at least one friend is present and NO enemies OR if more friends than enemies.
        # Simplified: If any friend, status = shubha. If only enemies, status = paapa. If empty, neutral.
        friends_in_house = [p for p in occ_planets if p['is_friend']]
        enemies_in_house = [p for p in occ_planets if not p['is_friend']]

        if friends_in_house:
            state = "shubha"
        elif enemies_in_house:
            state = "paapa"
        else:
            state = "neutral"

        bhava_data = DETAILED_BHAVA_MEANINGS[house_num]
        interpretation = bhava_data.get(state, bhava_data["neutral"])
        
        # Specific Logic Expansion
        special_note = ""
        
        # ----------------- SPECIFIC PLANETARY RULES (Life Scenarios) -----------------
        
        # 4th House: Sun Rules
        if house_num == 4:
            sun_p = [p for p in occ_planets if "సూర్యుడు" in p['name']]
            if sun_p:
                p = sun_p[0]
                if p['is_friend']:
                    special_note += "సూర్యుడు 4వ రాశిలో ఉండటమువలన మీకు పై అంతస్థు భవనములు కట్టించు ప్రేరణ చేయును. ఒకవేళ పేదవారైనా ఆ ఇంటిలో నివాసము కల్గునట్లు చేయును. "
                else:
                    special_note += "సూర్యుడు శత్రుగ్రహమై 4వ రాశిలో ఉన్నందున గృహ సుఖములు లోపించును. ఉన్న పెద్ద ఇల్లును కూడా అమ్మి చిన్న ఇల్లును కొందామనుకొనును. "

        # 8th House: Mars and others
        if house_num == 8 and enemies_in_house:
            for p in enemies_in_house:
                if "రాహు" in p['name']: special_note += "పాముకాటు లేదా విషాహారం వలన ప్రమాదం. "
                elif "చంద్రుడు" in p['name']: special_note += "నీటి గండముతో మరణ భయం. "
                elif "శుక్రుడు" in p['name']: special_note += "అగ్ని వలన ప్రమాదం. "
                elif "బుధుడు" in p['name']: special_note += "దయ్యాల పీడ లేదా వైద్యులకు అంతుచిక్కని రోగము. "
                elif "కుజుడు" in p['name']: special_note += "ఆయుధాల చేత లేదా రక్తసిక్త ప్రమాదము (బాంబులు/తుపాకులు). "

        # 6th House: Mars, Mercury
        if house_num == 6:
            for p in occ_planets:
                if "కుజుడు" in p['name'] and not p['is_friend']:
                    special_note += "మృగముల చేత గాయపడుట, ఆయుధములచేత దాడి, వ్రణములు, లేదా టీబీ/క్యాన్సర్ వంటి రోగముల భయము. "
                if "బుధుడు" in p['name']:
                    if p['is_friend']:
                        special_note += "వైద్య విద్యలో రాణించుట, భూతవైద్యము కూడా తెలిసియుండుట. "
                    else:
                        special_note += "దయ్యాల బాధలు, దయ్యములు శరీరములో రోగరూపముగా ఉండి బాధింపవచ్చును. "

        # 7th House: Venus, Mars
        if house_num == 7:
            for p in occ_planets:
                if "శుక్రుడు" in p['name']:
                    if p['is_friend']:
                        special_note += "అందమైన, అనుకూలమైన భార్య/భర్త లభించును. ఆమె/అతని వలన మనశ్శాంతి, సుఖము ఉండును. "
                    else:
                        special_note += "కళత్రము వలన కష్టములు, మనఃశ్శాంతి లోపించును. "
                if "కుజుడు" in p['name'] and not p['is_friend']:
                    special_note += "యుక్తవయస్సులో వివాహము ఆలస్యమగును. "

        # 3rd House: Jupiter Gold Logic
        if house_num == 3:
            for p in occ_planets:
                if "గురు" in p['name']:
                    if p['is_friend']:
                        special_note += "బంగారము లేదా ధనము ఏదో ఒక విధంగా లభ్యమగుట (వ్యాపార లాభం లేదా అదృష్టం). "
                    else:
                        special_note += "ఉన్న బంగారమును కూడా అమ్మవలసిన పరిస్థితులు ఏర్పడును. "
            # Rahu behind Jupiter logic
            rahu_in_3 = any("రాహు" in p['name'] for p in occ_planets)
            guru_in_3 = any("గురు" in p['name'] for p in occ_planets)
            if rahu_in_3 and guru_in_3:
                special_note += "రాహువు గురువు కలిసి ఉండటము వలన బంగారు దొంగలు ఎత్తుకొని పోవు భయమున్నది. "

        # 10th House: Career (Existing but enhanced)
        if house_num == 10 and occ_planets:
            for p in occ_planets:
                if "సూర్యుడు" in p['name'] or "చంద్రుడు" in p['name']:
                    special_note += "ప్రభుత్వ ఉన్నత ఉద్యోగి (కలెక్టర్) లేదా మంత్రి పదవి యోగం. "
                elif "కుజుడు" in p['name']:
                    if any("సూర్యుడు" in p2['name'] or "చంద్రుడు" in p2['name'] for p2 in occ_planets):
                        special_note += "మిలిటరీలో పెద్ద డాక్టరుగా పేరు తెచ్చుకొందురు. "
                    else:
                        special_note += "ప్రభుత్వ డాక్టరుగా లేదా గొప్ప సర్జన్ గా పేరు తెచ్చుకొందురు. "
                elif "శుక్రుడు" in p['name']:
                    special_note += "అష్టైశ్వర్యములతో కూడిన సుఖమయ జీవితం. "

        # 11th House: Gains
        if house_num == 11 and friends_in_house:
            for p in friends_in_house:
                if "బుధుడు" in p['name']: special_note += "కట్నకానుకల రూపంలో లబ్ది. "
                elif "గురు" in p['name']: special_note += "డొనేషన్లు లేదా విద్యాసంస్థల ద్వారా లాభం. "

        # 4th House again: Rahu illegal wealth
        if house_num == 4:
            for p in occ_planets:
                if "రాహు" in p['name']:
                    if p['is_friend']:
                        special_note += "దొంగవృత్తి లేదా దోపిడీల ద్వారా లక్షలు సంపాదించుట, సమాజములో భయంతో కూడిన గౌరవము. "
                    else:
                        special_note += "దొంగతనములలో దొరికిపోవుట, పోలీస్ కేసులు, జైలు జీవితము అనుభవించవలసి రావచ్చు. "

        # 5th House: Ketu God logic
        if house_num == 5:
            for p in occ_planets:
                if "కేతు" in p['name']:
                    if p['is_friend']:
                        special_note += "దేవుని వైపు చింత, హేతువాదిక జ్ఞానము, సత్యాన్వేషణలో దైవభక్తి పెరగడము. "
                    else:
                        special_note += "దైవజ్ఞానము మీద ఆసక్తి ఉండదు, పూర్తిగా ప్రపంచ జ్ఞానములోనే ఉండిపోవుట. "

        # Moon general water issues
        is_moon_enemy = any("చంద్రుడు" in p['name'] for p in enemies_in_house) if enemies_in_house else False
        if is_moon_enemy:
            special_note += "చంద్రుడు వ్యతిరేఖముగా ఉన్నందున నీటి ఇబ్బందులు (బావులు ఎండిపోవుట, ఇంటిలో నీరు కారుట, బాత్ రూమ్ పైపులు చెడిపోవుట). "

        # Saturn general iron logic
        for p in occ_planets:
            if "శని" in p['name'] and p['is_friend']:
                special_note += "ఇనుము వ్యాపారములో మంచి లాభములు పొంది ధనికులయ్యే యోగము. "

        # ----------------- ADVANCED Q&A LOGIC -----------------

        # 7th House: Multiple Marriages / Secret Relations (Rahu/Ketu)
        if house_num == 7:
            rk_p = [p for p in occ_planets if any(x in p['name'] for x in ["రాహు", "కేతు"])]
            if rk_p:
                # Count opposing planets to see if Rahu/Ketu's effect is suppressed
                # "Opposing" here means planets not in their natural party
                rk_name = "రాహు" if "రాహు" in rk_p[0]['name'] else "కేతు"
                opposing_count = 0
                for p in occ_planets:
                    if rk_name == "రాహు" and any(x in p['name'] for x in ["సూర్యుడు", "చంద్రుడు", "కుజుడు", "గురు"]):
                        opposing_count += 1
                    elif rk_name == "కేతు" and any(x in p['name'] for x in ["శుక్రుడు", "శని", "బుధుడు"]):
                        opposing_count += 1
                
                if opposing_count >= 2:
                    special_note += f"{rk_p[0]['name']} 7వ స్థానములో ఉన్నప్పటికీ, వ్యతిరేక గ్రహముల ప్రభావమువలన రెండవ వివాహము లేదా అక్రమ సంబంధముల ఆటంకములు తొలగిపోవును. "
                else:
                    special_note += f"{rk_p[0]['name']} 7వ స్థానములో ఉన్నందున రెండవ పెళ్ళికి లేదా అక్రమ సంబంధములకు అవకాశమున్నది. "

        # Lagna (1st House): Discord Logic (Mars + Venus)
        if house_num == 1:
            has_mars = any("కుజుడు" in p['name'] for p in occ_planets)
            has_venus = any("శుక్రుడు" in p['name'] for p in occ_planets)
            if has_mars and has_venus:
                # Check if they are enemies for this lagna
                # Mars is Guru party, Venus is Sani party. They are always bitter enemies.
                special_note += "కుజుడు మరియు శుక్రుడు ఇద్దరూ లగ్నములో కలిసి ఉన్నందున, భార్యాభర్తల మధ్య అన్యోన్యత లోపించి తరచూ పోట్లాటలు జరిగే సూచనలున్నవి. "

        # 5th House vs 3, 7, 11: Intelligence (Moon)
        if house_num == 5:
            moon_p = [p for p in occ_planets if "చంద్రుడు" in p['name']]
            if moon_p:
                special_note += "చంద్రుడు 5వ స్థానములో ఉన్నందున మీరు గొప్ప మేధాశక్తి మరియు మంచి బుద్ధి గలవారై ఉంటారు. ఏ సమస్యకైనా సులభముగా జవాబు చెప్పగలరు. "
        elif house_num in [3, 7, 11]:
            moon_p = [p for p in occ_planets if "చంద్రుడు" in p['name']]
            if moon_p:
                special_note += "చంద్రుడు పాపస్థానములో (3, 7, 11) ఉన్నందున తెలివితేటలు తక్కువగా ఉండును లేదా ప్రవర్తనలో అజ్ఞానము కనిపించవచ్చును. "

        # 4th House: Pathway/Road Disputes (Mars)
        if house_num == 4:
            mars_p = [p for p in occ_planets if "కుజుడు" in p['name']]
            if mars_p and not mars_p[0]['is_friend']:
                special_note += "కుజుడు 4వ స్థానములో వ్యతిరేఖముగా ఉన్నందున గృహము లేదా పొలము వద్ద దారికి సంబంధించిన తగాదాలు (దక్షిణ దిశలో) వచ్చే అవకాశమున్నది. "

        # Mercury: Logic for Interest in Astrology
        for p in occ_planets:
            if "బుధుడు" in p['name']:
                if house_num == 5 and p['is_friend']:
                    special_note += "బుధుడు 5వ స్థానములో అనుకూలముగా ఉన్నందున మీకు జ్యోతిష్యము మరియు శాస్త్రముల మీద మంచి ఆసక్తి, అవగాహన కల్గును. "
                elif not p['is_friend'] and any(x in p['name'] for x in ["చంద్రుడు"]):
                    special_note += "బుధుడు చంద్రునితో కలిసి శత్రువుగా ఉన్నందున వ్యాపార విషయాలలో తెలివితక్కువతనము ప్రదర్శించవచ్చును. "

        # Wealth: Jupiter (Stored) vs Venus (Flowing)
        for p in occ_planets:
            if "గురు" in p['name'] and not p['is_friend']:
                special_note += "గురువు వ్యతిరేఖముగా ఉన్నందున ధనము నిలువ చేయడములో ఇబ్బందులు కల్గును. "
            if "శుక్రుడు" in p['name'] and not p['is_friend']:
                special_note += "శుక్రుడు వ్యతిరేఖముగా ఉన్నందున చేతిలో డబ్బు నిలువక ప్రవాహములా ఖర్చైపోవును. "

        bhava_report.append({
            "number": house_num,
            "title": bhava_data["title"],
            "rasi": house_rasi,
            "meaning": bhava_data["meaning"],
            "planets": p_info,
            "interpretation": interpretation,
            "special_note": special_note,
            "state": state
        })

    return render_template("results.html", 
                           results=results_data,
                           friends=friends,
                           enemies=enemies,
                           bhava_report=bhava_report,
                           native_party=native_party,
                           lagna=lagna,
                           name=birth_info.get('name', ''),
                           dob=birth_info.get('dob', ''),
                           tob=birth_info.get('tob', ''),
                           place=birth_info.get('place', ''))


@app.route("/go-to-dasha-chart")
def go_to_dasha_chart():
    """Redirect to dasha chart with session data"""
    birth_info = session.get('birth_info', {})
    if birth_info:
        # Trigger the full dasha cycle calculation
        return chart2()
    else:
        # Redirect to index if no birth info
        return redirect(url_for('index'))

@app.route("/check-birth-data")
def check_birth_data():
    """Check if birth data exists in session"""
    birth_info = session.get('birth_info', {})
    return jsonify({
        'has_data': bool(birth_info.get('name') and birth_info.get('dob') and birth_info.get('tob'))
    })

@app.route("/manual_nakshatra", methods=["POST"])
def manual_nakshatra():
    """Route for manual nakshatra correction"""
    # Get basic info
    dob = request.form.get("dob", "")
    tob = request.form.get("tob", "")
    name = request.form.get("name", "")
    place = request.form.get("place", "")
    
    # Get auto-calculated values
    try:
        auto_nak_index = int(request.form.get("nak_index", 0))
        auto_elapsed_h = int(request.form.get("elapsed_h", 0))
        auto_elapsed_m = int(request.form.get("elapsed_m", 0))
    except (ValueError, TypeError):
        auto_nak_index = 0
        auto_elapsed_h = 0
        auto_elapsed_m = 0
    
    # Get manual correction values - if not present, use auto values
    manual_nakshatra_name = request.form.get("manual_nakshatra")
    raw_manual_h = request.form.get("manual_elapsed_h")
    raw_manual_m = request.form.get("manual_elapsed_m")
    
    # If this is the FIRST time entering (no manual values yet), pre-fill with auto values
    if manual_nakshatra_name is None:
        manual_nakshatra_name = NAKSHATRAS_TELUGU[auto_nak_index] if auto_nak_index < len(NAKSHATRAS_TELUGU) else ""
        manual_h = auto_elapsed_h
        manual_m = auto_elapsed_m
    else:
        try:
            manual_h = int(raw_manual_h) if raw_manual_h else 0
            manual_m = int(raw_manual_m) if raw_manual_m else 0
        except:
            manual_h = 0
            manual_m = 0
    
    # Calculate remaining time (total 24 hours)
    manual_remain_h = 24 - manual_h
    manual_remain_m = 60 - manual_m
    if manual_remain_m == 60:
        manual_remain_m = 0
        manual_remain_h += 1
    
    # Format time strings
    nak_elapsed = f"{manual_h}గం {manual_m}ని"
    nak_remaining = f"{manual_remain_h}గం {manual_remain_m}ని"
    
    # Find nakshatra index
    nak_index = 0
    if manual_nakshatra_name in NAKSHATRAS_TELUGU:
        nak_index = NAKSHATRAS_TELUGU.index(manual_nakshatra_name)
    else:
        nak_index = auto_nak_index
    
    # Calculate padam from elapsed time
    elapsed_minutes = manual_h * 60 + manual_m
    padam = int((elapsed_minutes / (24*60)) * 4) + 1
    padam = max(1, min(padam, 4))
    
    # Store in session
    session['birth_info'] = {
        'name': name,
        'dob': dob,
        'tob': tob,
        'place': place,
        'day_name': session.get('birth_info', {}).get('day_name', ''),
        'nakshatra': manual_nakshatra_name,
        'padam': padam,
        'nak_elapsed': nak_elapsed,
        'nak_remaining': nak_remaining,
        'nak_index': nak_index,
        'elapsed_h': manual_h,
        'elapsed_m': manual_m,
        'lagna': session.get('birth_info', {}).get('lagna', ''),
        'lagna_deg': session.get('birth_info', {}).get('lagna_deg', ''),
        'tithi_paksha': session.get('birth_info', {}).get('tithi_paksha', ''),
        'tithi_name': session.get('birth_info', {}).get('tithi_name', ''),
        'yoga_name': session.get('birth_info', {}).get('yoga_name', ''),
        'karana_name': session.get('birth_info', {}).get('karana_name', ''),
        'telugu_year': session.get('birth_info', {}).get('telugu_year', ''),
        'suryodayam': session.get('birth_info', {}).get('suryodayam', ''),
        'suryastamayam': session.get('birth_info', {}).get('suryastamayam', ''),
        'planet_positions': session.get('birth_info', {}).get('planet_positions', [])
    }
    
    return render_template(
        "manual_correction.html",
        dob=dob,
        tob=tob,
        name=name,
        place=place,
        auto_nakshatra=NAKSHATRAS_TELUGU[auto_nak_index] if auto_nak_index < len(NAKSHATRAS_TELUGU) else "",
        auto_elapsed_h=auto_elapsed_h,
        auto_elapsed_m=auto_elapsed_m,
        manual_nakshatra=manual_nakshatra_name,
        manual_elapsed_h=manual_h,
        manual_elapsed_m=manual_m,
        nak_elapsed=nak_elapsed,
        nak_remaining=nak_remaining,
        nakshatra=manual_nakshatra_name,
        padam=padam,
        nak_index=nak_index,
        elapsed_h=manual_h,
        elapsed_m=manual_m,
        all_nakshatras=NAKSHATRAS_TELUGU
    )

@app.route("/reset_user_data", methods=["POST"])
def reset_user_data():
    """Reset the user_data.txt file if password is correct"""
    password = request.form.get("password")
    if password == "USHA":
        try:
            log_file = "user_data.txt"
            # Truncate the file
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("")
            
            # Git push to keep GitHub in sync
            subprocess.run(["git", "add", log_file], check=True, capture_output=True, text=True, shell=True)
            subprocess.run(["git", "commit", "-m", "Reset user data log"], check=True, capture_output=True, text=True, shell=True)
            subprocess.run(["git", "push"], check=True, capture_output=True, text=True, shell=True)
            
            return jsonify({"status": "success", "message": "Data reset successfully!"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    else:
        return jsonify({"status": "error", "message": "Invalid password!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)