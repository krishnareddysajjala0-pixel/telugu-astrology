from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import swisseph as swe
import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'astrology-secret-key-2024'  # Required for session

# ---------------- Swiss Ephemeris ----------------
swe.set_ephe_path(".")
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
    "సూర్య": "#FFD700",  # Gold
    "చంద్ర": "#F0F8FF",  # Alice Blue
    "కుజ": "#FF4500",    # Orange Red
    "బుధ": "#32CD32",    # Lime Green
    "గురు": "#FFA500",   # Orange
    "శుక్ర": "#FF69B4",  # Hot Pink
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

# ---------------- ASTROLOGICAL PARTIES ----------------
# Lagnas belonging to Guru Party
GURU_PARTY_LAGNAS = ["మేషం", "కర్కాటకం", "సింహం", "వృశ్చికం", "ధనస్సు", "మీనం"]
# Lagnas belonging to Sani Party
SANI_PARTY_LAGNAS = ["వృషభం", "మిథునం", "కన్య", "తులా", "మకరం", "కుంభం"]

# Favorable planets for each party
# Note: Rahu & Ketu act depending on house, but standardly align with the party or act as neutral.
# We map standard party friends for the "అనుకూలము (Favorable)" label
GURU_PARTY_PLANETS = ["సూర్య", "చంద్ర", "కుజ", "గురు", "కేతు"] 
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

def calculate_anthara_periods(maha_name, start_date, end_date, lagna=""):
    """Calculate anthara periods for a given Mahadasha"""
    antharas = []
    anthara_start = start_date
    
    if maha_name in ANTHARA_MONTHS:
        for planet, months in ANTHARA_MONTHS[maha_name]:
            anthara_end = add_months(anthara_start, months)
            
            antharas.append({
                "anthara": planet,
                "start": anthara_start.strftime("%d-%m-%Y"),
                "end": anthara_end.strftime("%d-%m-%Y"),
                "months": months,
                "color": PLANET_COLORS.get(planet, "#666666"),
                "icon": PLANET_ICONS.get(planet, "•"),
                "is_favorable": is_dasa_favorable(lagna, planet)
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

    # Day name
    day_eng = datetime.datetime.strptime(dob, "%Y-%m-%d").strftime("%A")
    day_name = DAY_TELUGU.get(day_eng, day_eng)

    # Time: IST → UTC
    ist = pytz.timezone("Asia/Kolkata")
    local_dt = ist.localize(
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

    # Derived planets
    derived = {
        "భూమి": (base_pos["సూర్యుడు"] + 180) % 360,
        "చిత్ర": (rahu + 3.3) % 360,
        "మిత్ర": (ketu + 3.3) % 360
    }

    for n, lonp in derived.items():
        base_pos[n] = lonp
        r = RASI_TELUGU[int(lonp/30)]
        deg = lonp % 30
        d = int(deg)
        m = int((deg-d)*60)
        html_str = f"<b>{n}</b> <small>{d}°{m:02d}′</small>"
        chart_data_temp[r].append((deg, html_str))

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

    # Store birth info in session for other pages
    session['birth_info'] = {
        'name': name,
        'dob': dob,
        'tob': tob,
        'place': place,
        'day_name': day_name,
        'nakshatra': nakshatra,
        'padam': padam,
        'nak_elapsed': f"{elapsed_h}గం {elapsed_m}ని",
        'nak_remaining': f"{remain_h}గం {remain_m}ని",
        'nak_index': nak_index,
        'elapsed_h': elapsed_h,
        'elapsed_m': elapsed_m,
        'lagna_deg': lagna_degree_str,
        'lagna': lagna
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
    ist = pytz.timezone("Asia/Kolkata")
    try:
        birth_dt = ist.localize(
            datetime.datetime.strptime(dob + " " + tob, "%Y-%m-%d %H:%M")
        )
    except ValueError:
        return "❌ Invalid date/time format"

    # ===== CALCULATE FULL 120-YEAR DASA CYCLE =====
    
    # 1. Calculate birth Mahadasha
    birth_dasa, dasa_index = get_running_dasa(nak_index, padam)
    
    # 2. Calculate elapsed time in birth dasa
    elapsed_minutes = nak_minutes(elapsed_h, elapsed_m)
    fraction = elapsed_minutes / TOTAL_NAK_MINUTES if TOTAL_NAK_MINUTES > 0 else 0
    
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
    
    # Start from birth dasa and go through all 12
    for i in range(12):
        dasa_index_calc = (dasa_index + i) % 12
        dasa_name = DASA_ORDER[dasa_index_calc]
        dasa_years = DASA_YEARS.get(dasa_name, 10)
        
        end_date = add_years(start_date, dasa_years)
        start_str = start_date.strftime("%d-%m-%Y")
        end_str = end_date.strftime("%d-%m-%Y")
        
        # Calculate Anthara dasas for this Mahadasha
        antharas = calculate_anthara_periods(dasa_name, start_date, end_date, lagna)
        
        # Check if TODAY is within this dasa
        is_current_today = is_date_within_range(today_str, start_str, end_str)
        
        # Check if this is the birth dasa
        is_birth_dasa = (i == 0)
        
        # Add color and icon to dasa
        dasa_color = PLANET_COLORS.get(dasa_name, "#666666")
        dasa_icon = PLANET_ICONS.get(dasa_name, "•")
        
        # Determine favorability for full Mahadasa
        is_maha_favorable = is_dasa_favorable(lagna, dasa_name)
        
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
            "is_favorable": is_maha_favorable
        })
        
        # If this is current dasa, store its info
        if is_current_today:
            current_maha_index = i
            current_maha_name = dasa_name
            current_maha_start = start_str
            current_maha_end = end_str
            current_maha_years = dasa_years
        
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

@app.route("/go-to-birth-chart")
def go_to_birth_chart():
    """Redirect to birth chart with session data"""
    birth_info = session.get('birth_info', {})
    if birth_info:
        # Pass data to chart.html template
        return render_template("chart.html", **birth_info)
    else:
        # Redirect to index if no birth info
        return redirect(url_for('index'))

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
    # Get data from form
    dob = request.form.get("dob", "")
    tob = request.form.get("tob", "")
    name = request.form.get("name", "")
    place = request.form.get("place", "")
    
    # Get auto-calculated values
    auto_nak_index = int(request.form.get("nak_index", 0))
    auto_elapsed_h = int(request.form.get("elapsed_h", 0))
    auto_elapsed_m = int(request.form.get("elapsed_m", 0))
    
    # Get manual correction values
    manual_nakshatra_name = request.form.get("manual_nakshatra", "")
    manual_elapsed_h = request.form.get("manual_elapsed_h", "0")
    manual_elapsed_m = request.form.get("manual_elapsed_m", "0")
    
    # Convert manual values
    try:
        manual_h = int(manual_elapsed_h) if manual_elapsed_h else 0
        manual_m = int(manual_elapsed_m) if manual_elapsed_m else 0
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
        # Fallback to auto-calculated
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
        'nakshatra': manual_nakshatra_name or NAKSHATRAS_TELUGU[auto_nak_index],
        'padam': padam,
        'nak_elapsed': nak_elapsed,
        'nak_remaining': nak_remaining,
        'nak_index': nak_index,
        'elapsed_h': manual_h,
        'elapsed_m': manual_m,
        'lagna': session.get('birth_info', {}).get('lagna', '')
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
        nakshatra=manual_nakshatra_name or NAKSHATRAS_TELUGU[auto_nak_index],
        padam=padam,
        nak_index=nak_index,
        elapsed_h=manual_h,
        elapsed_m=manual_m,
        all_nakshatras=NAKSHATRAS_TELUGU
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)