import swisseph as swe
import datetime
import pytz

def find_amavasya(jd_guess):
    jd = jd_guess
    for _ in range(10):
        m = swe.calc_ut(jd, swe.MOON)[0][0]
        s = swe.calc_ut(jd, swe.SUN)[0][0]
        diff = (m - s) % 360
        if diff > 180:
            diff_to_0 = diff - 360
        else:
            diff_to_0 = diff
        jd -= diff_to_0 / 12.190749
        if abs(diff_to_0) < 0.0001:
            break
    return jd

def get_lunar_month_dates(jd_current, sun_lon, moon_lon):
    diff = (moon_lon - sun_lon) % 360
    
    # Approx days
    days_since = diff / 12.190749
    days_to = (360 - diff) / 12.190749
    
    jd_start_guess = jd_current - days_since
    jd_end_guess = jd_current + days_to
    
    jd_start = find_amavasya(jd_start_guess)
    jd_end = find_amavasya(jd_end_guess)
    
    def format_jd(jd_time):
        year, month, day, hour = swe.revjul(jd_time)
        dt = datetime.datetime(year, month, day, int(hour), int((hour%1)*60))
        dt = pytz.utc.localize(dt).astimezone(pytz.timezone('Asia/Kolkata'))
        return dt.strftime("%B-%d").lower()
    
    start_str = format_jd(jd_start)
    end_str = format_jd(jd_end)
    
    # Calculate exact month name mapping based on the Amavasya's Solar intersection
    amavasya_sun_lon = swe.calc_ut(jd_start, swe.SUN)[0][0]
    rasi_idx = int((amavasya_sun_lon % 360) / 30)
    
    TELUGU_MASALU = [
        "చైత్ర", "వైశాఖ", "జ్యేష్ఠ", "ఆషాఢ", "శ్రావణ", "భాద్రపద", 
        "ఆశ్వయుజ", "కార్తీక", "మార్గశిర", "పుష్య", "మాఘ", "ఫాల్గుణ"
    ]
    masam_index = (rasi_idx + 1) % 12
    month_name = TELUGU_MASALU[masam_index]
    
    return f"{month_name} మాసం ({start_str} nunchi {end_str} varaku)"

# Test with current date
now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
dt_ut = now.astimezone(pytz.utc)
jd_now = swe.julday(dt_ut.year, dt_ut.month, dt_ut.day, dt_ut.hour + dt_ut.minute/60.0)

s = swe.calc_ut(jd_now, swe.SUN)[0][0]
m = swe.calc_ut(jd_now, swe.MOON)[0][0]

print(get_lunar_month_dates(jd_now, s, m))
