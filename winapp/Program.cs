using System;
using System.Text;
using TeluguAstrology.WinApp;

class Program
{
    // Dasa / Nakshatra constants and helper data
    static readonly string[] DASA_ORDER = new string[] {
        "సూర్య","చంద్ర","కుజ","రాహు","గురు","భూమి",
        "శని","బుధ","కేతు","శుక్ర","మిత్ర","చిత్ర"
    };

    static readonly System.Collections.Generic.Dictionary<string,double> DASA_YEARS = new System.Collections.Generic.Dictionary<string,double>() {
        {"సూర్య",10}, {"చంద్ర",10}, {"కుజ",7}, {"రాహు",10},
        {"గురు",13}, {"భూమి",13}, {"శని",13}, {"బుధ",10},
        {"కేతు",7}, {"శుక్ర",13}, {"మిత్ర",7}, {"చిత్ర",7}
    };

    const int PADAS_PER_DASA = 9;
    const int TOTAL_NAK_MINUTES = 13*60 + 20; // 800

    // Planet colors and icons (copied from app.py)
    static readonly System.Collections.Generic.Dictionary<string,string> PLANET_COLORS = new System.Collections.Generic.Dictionary<string,string>() {
        {"సూర్య","#FFD700"}, {"చంద్ర","#F0F8FF"}, {"కుజ","#FF4500"}, {"బుధ","#32CD32"},
        {"గురు","#FFA500"}, {"శుక్ర","#FF69B4"}, {"శని","#696969"}, {"రాహు","#8B4513"},
        {"కేతు","#2F4F4F"}, {"భూమి","#228B22"}, {"మిత్ర","#9370DB"}, {"చిత్ర","#40E0D0"}
    };

    static readonly System.Collections.Generic.Dictionary<string,string> PLANET_ICONS = new System.Collections.Generic.Dictionary<string,string>() {
        {"సూర్య","☉"}, {"చంద్ర","☽"}, {"కుజ","♂"}, {"బుధ","☿"},
        {"గురు","♃"}, {"శుక్ర","♀"}, {"శని","♄"}, {"రాహు","☊"},
        {"కేతు","☋"}, {"భూమి","♁"}, {"మిత్ర","☆"}, {"చిత్ర","✦"}
    };

    // Anthara months mapping (copied & translated from app.py data)
    static readonly System.Collections.Generic.Dictionary<string, Tuple<string,double>[]> ANTHARA_MONTHS = new System.Collections.Generic.Dictionary<string, Tuple<string,double>[]> {
        {"సూర్య", new Tuple<string,double>[] {
            Tuple.Create("సూర్య",10.0), Tuple.Create("చంద్ర",10.0), Tuple.Create("కుజ",7.0), Tuple.Create("రాహు",10.0),
            Tuple.Create("గురు",13.0), Tuple.Create("భూమి",13.0), Tuple.Create("శని",13.0), Tuple.Create("బుధ",10.0),
            Tuple.Create("కేతు",7.0), Tuple.Create("శుక్ర",13.0), Tuple.Create("మిత్ర",7.0), Tuple.Create("చిత్ర",7.0)
        }},
        {"చంద్ర", new Tuple<string,double>[] {
            Tuple.Create("చంద్ర",10.0), Tuple.Create("కుజ",7.0), Tuple.Create("రాహు",10.0), Tuple.Create("గురు",13.0),
            Tuple.Create("భూమి",13.0), Tuple.Create("శని",13.0), Tuple.Create("బుధ",10.0), Tuple.Create("కేతు",7.0),
            Tuple.Create("శుక్ర",13.0), Tuple.Create("మిత్ర",7.0), Tuple.Create("చిత్ర",7.0), Tuple.Create("సూర్య",10.0)
        }},
        {"కుజ", new Tuple<string,double>[] {
            Tuple.Create("కుజ",4.9), Tuple.Create("రాహు",7.0), Tuple.Create("గురు",9.1), Tuple.Create("భూమి",9.1),
            Tuple.Create("శని",9.1), Tuple.Create("బుధ",7.0), Tuple.Create("కేతు",4.0), Tuple.Create("శుక్ర",9.0),
            Tuple.Create("మిత్ర",4.0), Tuple.Create("చిత్ర",4.0), Tuple.Create("సూర్య",7.0), Tuple.Create("చంద్ర",7.0)
        }},
        {"రాహు", new Tuple<string,double>[] {
            Tuple.Create("రాహు",10.0), Tuple.Create("గురు",13.0), Tuple.Create("భూమి",13.0), Tuple.Create("శని",13.0), Tuple.Create("బుధ",10.0),
            Tuple.Create("కేతు",7.0), Tuple.Create("శుక్ర",13.0), Tuple.Create("మిత్ర",7.0), Tuple.Create("చిత్ర",7.0),
            Tuple.Create("సూర్య",10.0), Tuple.Create("చంద్ర",10.0), Tuple.Create("కుజ",7.0)
        }},
        {"గురు", new Tuple<string,double>[] {
            Tuple.Create("గురు",16.9), Tuple.Create("భూమి",16.9), Tuple.Create("శని",16.9), Tuple.Create("బుధ",13.0), Tuple.Create("కేతు",9.0),
            Tuple.Create("శుక్ర",16.9), Tuple.Create("మిత్ర",9.1), Tuple.Create("చిత్ర",9.1), Tuple.Create("సూర్య",13.0), Tuple.Create("చంద్ర",13.0), Tuple.Create("కుజ",9.1), Tuple.Create("రాహు",13.0)
        }},
        {"భూమి", new Tuple<string,double>[] {
            Tuple.Create("భూమి",16.9), Tuple.Create("శని",16.9), Tuple.Create("బుధ",13.0), Tuple.Create("కేతు",9.1), Tuple.Create("శుక్ర",16.9), Tuple.Create("మిత్ర",9.1), Tuple.Create("చిత్ర",9.1),
            Tuple.Create("సూర్య",13.0), Tuple.Create("చంద్ర",13.0), Tuple.Create("కుజ",9.1), Tuple.Create("రాహు",13.0), Tuple.Create("గురు",16.9)
        }},
        {"శని", new Tuple<string,double>[] {
            Tuple.Create("శని",16.9), Tuple.Create("బుధ",13.0), Tuple.Create("కేతు",9.1), Tuple.Create("శుక్ర",16.9), Tuple.Create("మిత్ర",9.1), Tuple.Create("చిత్ర",9.1), Tuple.Create("సూర్య",13.0),
            Tuple.Create("చంద్ర",13.0), Tuple.Create("కుజ",9.1), Tuple.Create("రాహు",13.0), Tuple.Create("గురు",16.9), Tuple.Create("భూమి",16.9)
        }},
        {"బుధ", new Tuple<string,double>[] {
            Tuple.Create("బుధ",10.0), Tuple.Create("కేతు",7.0), Tuple.Create("శుక్ర",13.0), Tuple.Create("మిత్ర",7.0), Tuple.Create("చిత్ర",7.0), Tuple.Create("సూర్య",10.0), Tuple.Create("చంద్ర",10.0),
            Tuple.Create("కుజ",7.0), Tuple.Create("రాహు",10.0), Tuple.Create("గురు",13.0), Tuple.Create("భూమి",13.0), Tuple.Create("శని",13.0)
        }},
        {"కేతు", new Tuple<string,double>[] {
            Tuple.Create("కేతు",4.9), Tuple.Create("శుక్ర",9.1), Tuple.Create("మిత్ర",4.9), Tuple.Create("చిత్ర",4.9), Tuple.Create("సూర్య",7.0), Tuple.Create("చంద్ర",7.0), Tuple.Create("కుజ",4.9),
            Tuple.Create("రాహు",7.0), Tuple.Create("గురు",9.1), Tuple.Create("భూమి",9.1), Tuple.Create("శని",9.1), Tuple.Create("బుధ",7.0)
        }},
        {"శుక్ర", new Tuple<string,double>[] {
            Tuple.Create("శుక్ర",16.9), Tuple.Create("మిత్ర",9.1), Tuple.Create("చిత్ర",9.1), Tuple.Create("సూర్య",13.0), Tuple.Create("చంద్ర",13.0), Tuple.Create("కుజ",9.1), Tuple.Create("రాహు",13.0),
            Tuple.Create("గురు",16.9), Tuple.Create("భూమి",16.9), Tuple.Create("శని",16.9), Tuple.Create("బుధ",13.0), Tuple.Create("కేతు",9.1)
        }},
        {"మిత్ర", new Tuple<string,double>[] {
            Tuple.Create("మిత్ర",4.9), Tuple.Create("చిత్ర",4.9), Tuple.Create("సూర్య",7.0), Tuple.Create("చంద్ర",7.0), Tuple.Create("కుజ",4.0), Tuple.Create("రాహు",7.0), Tuple.Create("గురు",9.1), Tuple.Create("భూమి",9.1),
            Tuple.Create("శని",9.1), Tuple.Create("బుధ",7.0), Tuple.Create("కేతు",4.9), Tuple.Create("శుక్ర",9.1)
        }},
        {"చిత్ర", new Tuple<string,double>[] {
            Tuple.Create("చిత్ర",4.9), Tuple.Create("సూర్య",7.0), Tuple.Create("చంద్ర",7.0), Tuple.Create("కుజ",4.9), Tuple.Create("రాహు",7.0), Tuple.Create("గురు",9.1), Tuple.Create("భూమి",9.1), Tuple.Create("శని",9.1),
            Tuple.Create("బుధ",7.0), Tuple.Create("కేతు",4.9), Tuple.Create("శుక్ర",9.1), Tuple.Create("మిత్ర",4.9)
        }}
    };

    static void Main(string[] args)
    {
        // Interactive console port of app.py core calculations
        SwissEphemerisPInvoke.swe_set_ephe_path(".");

        Console.WriteLine("Telugu Astrology - Windows console (Swiss Ephemeris FFI)");
        Console.Write("Name: ");
        var name = Console.ReadLine() ?? "";
        Console.Write("Date of birth (YYYY-MM-DD): ");
        var dob = Console.ReadLine() ?? "2024-01-01";
        Console.Write("Time of birth (HH:MM) in local IST: ");
        var tob = Console.ReadLine() ?? "12:00";
        Console.Write("Latitude (e.g. 17.3850): ");
        var latStr = Console.ReadLine() ?? "17.3850";
        Console.Write("Longitude (e.g. 78.4867): ");
        var lonStr = Console.ReadLine() ?? "78.4867";

        if (!double.TryParse(latStr, out double lat)) lat = 17.3850;
        if (!double.TryParse(lonStr, out double lon)) lon = 78.4867;

        // Parse local IST datetime and convert to UTC
        var tz = TimeZoneInfo.FindSystemTimeZoneById("India Standard Time");
        if (!DateTime.TryParseExact(dob + " " + tob, "yyyy-MM-dd HH:mm", null, System.Globalization.DateTimeStyles.None, out DateTime localDt))
        {
            Console.WriteLine("Invalid date/time format, using 2024-01-01 12:00");
            localDt = new DateTime(2024, 1, 1, 12, 0, 0);
        }

        var utcDt = TimeZoneInfo.ConvertTimeToUtc(localDt, tz);
        int gregflag = 1; // Gregorian
        double hourDecimal = utcDt.Hour + utcDt.Minute / 60.0 + utcDt.Second / 3600.0;
        double jd = SwissEphemerisPInvoke.swe_julday(utcDt.Year, utcDt.Month, utcDt.Day, hourDecimal, gregflag);
        Console.WriteLine($"Julian day (UTC): {jd}");

        // Ayanamsa (used to convert tropical -> sidereal)
        double ayan = SwissEphemerisPInvoke.swe_get_ayanamsa_ut(jd);

        // Telugu Rasi names
        string[] RASI_TELUGU = new string[] {
            "మేషం","వృషభం","మిథునం","కర్కాటకం",
            "సింహం","కన్య","తులా","వృశ్చికం",
            "ధనస్సు","మకరం"," కుంభం","మీనం"
        };

        // Planet mapping using swisseph IDs
        var PLANETS = new System.Collections.Generic.Dictionary<string,int>() {
            {"సూర్యుడు", SwissEphemerisPInvoke.SE_SUN},
            {"చంద్రుడు", SwissEphemerisPInvoke.SE_MOON},
            {"కుజుడు", SwissEphemerisPInvoke.SE_MARS},
            {"బుధుడు", SwissEphemerisPInvoke.SE_MERCURY},
            {"గురు", SwissEphemerisPInvoke.SE_JUPITER},
            {"శుక్రుడు", SwissEphemerisPInvoke.SE_VENUS},
            {"శని", SwissEphemerisPInvoke.SE_SATURN},
            {"రాహు", SwissEphemerisPInvoke.SE_MEAN_NODE}
        };

        var chart_data = new System.Collections.Generic.Dictionary<string, string>();
        foreach (var r in RASI_TELUGU) chart_data[r] = "";
        var base_pos = new System.Collections.Generic.Dictionary<string,double>();

        double[] xx = new double[6];
        var serr = new StringBuilder(256);

        // Calculate planets (get tropical then convert to sidereal via ayanamsa)
        foreach (var kv in PLANETS)
        {
            int pid = kv.Value;
            int ret = SwissEphemerisPInvoke.swe_calc_ut(jd, pid, 0, xx, serr);
            if (ret < 0)
            {
                Console.WriteLine($"Error calculating {kv.Key}: " + serr.ToString());
                continue;
            }
            double lon_tropical = xx[0];
            double lon_sidereal = (lon_tropical - ayan) % 360.0;
            if (lon_sidereal < 0) lon_sidereal += 360.0;
            base_pos[kv.Key] = lon_sidereal;
            int rasiIndex = (int)(lon_sidereal / 30.0);
            int d = (int)(lon_sidereal % 30);
            int m = (int)(((lon_sidereal % 30) - d) * 60);
            chart_data[RASI_TELUGU[rasiIndex]] += $"{kv.Key} {d}°{m:00}′\n";
        }

        // Ketu
        double rahu = base_pos["రాహు"];
        double ketu = (rahu + 180.0) % 360.0;
        base_pos["కేతు"] = ketu;
        int rIdx = (int)(ketu / 30.0);
        chart_data[RASI_TELUGU[rIdx]] += $"కేతు {(int)(ketu%30)}°{(int)((((ketu%30)-(int)(ketu%30))*60)):00}′\n";

        // Derived planets
        base_pos["భూమి"] = (base_pos["సూర్యుడు"] + 180.0) % 360.0;
        base_pos["చిత్ర"] = (rahu + 3.3) % 360.0;
        base_pos["మిత్ర"] = (ketu + 3.3) % 360.0;

        foreach (var kv in base_pos)
        {
            // Already added many, but ensure derived are printed
        }

        // Hands (similar to app.py)
        var SPECIAL_HANDS = new System.Collections.Generic.Dictionary<string,int[]>() {
            {"కుజుడు", new int[]{90,210}},
            {"గురు", new int[]{120,240}},
            {"శని", new int[]{60,270}}
        };

        foreach (var kv in base_pos)
        {
            string n = kv.Key;
            double baseLon = kv.Value;
            var angles = new System.Collections.Generic.List<int>(){180};
            if (SPECIAL_HANDS.ContainsKey(n)) angles.AddRange(SPECIAL_HANDS[n]);
            foreach (var a in angles)
            {
                double hl = (baseLon + a) % 360.0;
                int ri = (int)(hl / 30.0);
                int d = (int)(hl % 30);
                int m = (int)(((hl % 30) - d) * 60);
                chart_data[RASI_TELUGU[ri]] += $"{n} hand {d}°{m:00}′\n";
            }
        }

        // Houses
        double[] cusps = new double[36];
        double[] ascmc = new double[12];
        SwissEphemerisPInvoke.swe_houses(jd, lat, lon, (byte)'P', cusps, ascmc);
        double asc_tropical = ascmc[0];
        double lagna_lon = (asc_tropical - ayan) % 360.0;
        if (lagna_lon < 0) lagna_lon += 360.0;
        string lagna = RASI_TELUGU[(int)(lagna_lon/30.0)];
        int lagna_deg = (int)(lagna_lon % 30.0);
        int lagna_min = (int)(((lagna_lon % 30.0) - lagna_deg) * 60.0);
        string lagna_str = $"{lagna_deg}°{lagna_min:00}′";
        chart_data[lagna] = "లగ్నం " + lagna_str + "\n" + chart_data[lagna];

        // Nakshatra
        double moon_lon = base_pos.ContainsKey("చంద్రుడు") ? base_pos["చంద్రుడు"] : 0.0;
        double NAKSHATRA_SIZE = 13 + 20.0/60.0; // 13deg20'
        double PADAM_SIZE = NAKSHATRA_SIZE / 4.0;
        string[] NAKSHATRAS_TELUGU = new string[]{
            "అశ్విని","భరణి","కృత్తిక","రోహిణి","మృగశిర","ఆర్ద్ర",
            "పునర్వసు","పుష్యమి","ఆశ్లేష","మఖ",
            "పూర్వఫల్గుణి","ఉత్తరఫల్గుణి",
            "హస్త","చిత్త","స్వాతి","విశాఖ",
            "అనూరుాధ","జ్యేష్ఠ","మూల","పూర్వాషాఢ",
            "ఉత్తరాషాఢ","శ్రవణ","ధనిష్ఠ","శతభిష",
            "పూర్వాభాద్ర","ఉత్తరాభాద్ర","రేవతి"
        };

        int nak_index = (int)(moon_lon / NAKSHATRA_SIZE);
        string nakshatra = NAKSHATRAS_TELUGU[nak_index];
        double nak_offset = moon_lon - (nak_index * NAKSHATRA_SIZE);
        int padam = (int)(nak_offset / PADAM_SIZE) + 1;

        // elapsed nakshatra time (hours/mins)
        int elapsed_h = (int)((nak_offset / NAKSHATRA_SIZE) * 24.0);
        int elapsed_m = (int)((((nak_offset / NAKSHATRA_SIZE) * 24.0) % 1.0) * 60.0);

        // Remaining time (not used for dasa but kept like app.py)
        double rem = NAKSHATRA_SIZE - nak_offset;
        int remain_h = (int)((rem / NAKSHATRA_SIZE) * 24.0);
        int remain_m = (int)(((((rem / NAKSHATRA_SIZE) * 24.0) % 1.0) * 60.0));

        // Output simple chart
        Console.WriteLine("\n--- Chart Data ---");
        foreach (var r in RASI_TELUGU)
        {
            Console.WriteLine($"{r}:\n{chart_data[r]}");
        }
        Console.WriteLine($"Lagna: {lagna} ({lagna_str})");
        Console.WriteLine($"Nakshatra: {nakshatra} padam {padam}");

        // ---- Dasa cycle computation (port of chart2 logic) ----
        // get running dasa and index
        var (birth_dasa, dasa_index) = GetRunningDasa(nak_index, padam);

        // elapsed minutes in current nakshatra padam
        int elapsed_minutes = elapsed_h * 60 + elapsed_m;
        double fraction = TOTAL_NAK_MINUTES > 0 ? (double)elapsed_minutes / TOTAL_NAK_MINUTES : 0.0;

        double birth_dasa_years = DASA_YEARS.ContainsKey(birth_dasa) ? DASA_YEARS[birth_dasa] : 10.0;
        double elapsed_years_in_birth_dasa = birth_dasa_years * fraction;

        // birth datetime in local (localDt) already set above
        DateTime birth_dt = localDt;
        DateTime birth_dasa_start = birth_dt.AddDays(-elapsed_years_in_birth_dasa * 365.25);
        DateTime birth_dasa_end = AddYears(birth_dasa_start, birth_dasa_years);

        DateTime today = DateTime.Now;
        string today_str = today.ToString("dd-MM-yyyy");

        // Build all 12 mahadashas starting from birth_dasa_start
        var all_dasas = new System.Collections.Generic.List<System.Collections.Generic.Dictionary<string, object>>();
        DateTime start_date = birth_dasa_start;

        int current_maha_index = -1;
        string current_maha_name = "";
        string current_maha_start = "";
        string current_maha_end = "";
        double current_maha_years = 0.0;

        for (int i = 0; i < 12; i++)
        {
            int dasa_index_calc = (dasa_index + i) % 12;
            string dasa_name = DASA_ORDER[dasa_index_calc];
            double dasa_years = DASA_YEARS.ContainsKey(dasa_name) ? DASA_YEARS[dasa_name] : 10.0;

            DateTime end_date = AddYears(start_date, dasa_years);
            string start_str = start_date.ToString("dd-MM-yyyy");
            string end_str = end_date.ToString("dd-MM-yyyy");

            var antharas = CalculateAntharaPeriods(dasa_name, start_date, end_date);

            bool is_current_today = IsDateWithinRange(today_str, start_str, end_str);
            bool is_birth_dasa = (i == 0);

            string dasa_color = PLANET_COLORS.ContainsKey(dasa_name) ? PLANET_COLORS[dasa_name] : "#666666";
            string dasa_icon = PLANET_ICONS.ContainsKey(dasa_name) ? PLANET_ICONS[dasa_name] : "•";

            var dasaEntry = new System.Collections.Generic.Dictionary<string, object>() {
                {"maha", dasa_name}, {"start", start_str}, {"end", end_str}, {"years", dasa_years},
                {"antharas", antharas}, {"is_current", is_current_today}, {"is_birth_dasa", is_birth_dasa}, {"color", dasa_color}, {"icon", dasa_icon}
            };

            all_dasas.Add(dasaEntry);

            if (is_current_today)
            {
                current_maha_index = i;
                current_maha_name = dasa_name;
                current_maha_start = start_str;
                current_maha_end = end_str;
                current_maha_years = dasa_years;
            }

            start_date = end_date;
        }

        if (current_maha_index == -1)
        {
            DateTime today_dt = DateTime.ParseExact(today_str, "dd-MM-yyyy", null);
            DateTime birth_start_dt = DateTime.ParseExact(birth_dasa_start.ToString("dd-MM-yyyy"), "dd-MM-yyyy", null);

            if (today_dt < birth_start_dt)
                current_maha_index = 0;
            else
                current_maha_index = 11;

            current_maha_name = (string)all_dasas[current_maha_index]["maha"];
            current_maha_start = (string)all_dasas[current_maha_index]["start"];
            current_maha_end = (string)all_dasas[current_maha_index]["end"];
            current_maha_years = (double)all_dasas[current_maha_index]["years"];
        }

        DateTime current_start_dt = DateTime.ParseExact(current_maha_start, "dd-MM-yyyy", null);
        DateTime current_end_dt = DateTime.ParseExact(current_maha_end, "dd-MM-yyyy", null);

        int total_days_current = (int)(current_end_dt - current_start_dt).TotalDays;
        int elapsed_days_current = (int)(today - current_start_dt).TotalDays;
        elapsed_days_current = Math.Max(0, Math.Min(elapsed_days_current, total_days_current));

        double elapsed_years_current = elapsed_days_current / 365.25;
        double remaining_years_current = (total_days_current - elapsed_days_current) / 365.25;

        double total_years_covered = 0.0;
        foreach (var d in all_dasas) total_years_covered += (double)d["years"];

        int current_year = DateTime.Now.Year;

        string current_dasa_color = PLANET_COLORS.ContainsKey(current_maha_name) ? PLANET_COLORS[current_maha_name] : "#FFD700";
        string current_dasa_icon = PLANET_ICONS.ContainsKey(current_maha_name) ? PLANET_ICONS[current_maha_name] : "☉";

        // Print compact header info similar to chart2
        Console.WriteLine($"\nMahadasha at birth: {birth_dasa}");
        Console.WriteLine($"Current Mahadasha: {current_maha_name} ({current_maha_start} - {current_maha_end})");
        Console.WriteLine($"Completed years in current: {Math.Round(elapsed_years_current,2)} Remaining years: {Math.Round(remaining_years_current,2)}");
        Console.WriteLine($"Total cycle years: {total_years_covered}");

        // Optional: print all mahadashas
        Console.WriteLine("\nFull Mahadasha cycle:");
        foreach (var d in all_dasas)
        {
            Console.WriteLine($"{d["maha"]}: {d["start"]} -> {d["end"]} ({d["years"]} yrs)");
        }

        Console.WriteLine("Done.");
    }

    static (string, int) GetRunningDasa(int nak_index, int padam)
    {
        int global_pada = nak_index * 4 + padam;
        if (global_pada == 0) global_pada = 108;
        while (global_pada > 108) global_pada -= 108;
        int idx = (global_pada - 1) / PADAS_PER_DASA;
        idx = Math.Max(0, Math.Min(idx, DASA_ORDER.Length - 1));
        return (DASA_ORDER[idx], idx);
    }

    static DateTime AddYears(DateTime dt, double years)
    {
        int days = (int)(years * 365.25);
        return dt.AddDays(days);
    }

    static DateTime AddMonths(DateTime dt, double months)
    {
        int days = (int)(months * 30.44);
        return dt.AddDays(days);
    }

    class Anthara
    {
        public string anthara { get; set; } = "";
        public string start { get; set; } = "";
        public string end { get; set; } = "";
        public double months { get; set; } = 0.0;
        public string color { get; set; } = "";
        public string icon { get; set; } = "";
    }

    static System.Collections.Generic.List<Anthara> CalculateAntharaPeriods(string maha_name, DateTime start_date, DateTime end_date)
    {
        var antharas = new System.Collections.Generic.List<Anthara>();
        DateTime anthara_start = start_date;
        if (ANTHARA_MONTHS.ContainsKey(maha_name))
        {
            foreach (var t in ANTHARA_MONTHS[maha_name])
            {
                string planet = t.Item1;
                double months = t.Item2;
                DateTime anthara_end = AddMonths(anthara_start, months);
                antharas.Add(new Anthara {
                    anthara = planet,
                    start = anthara_start.ToString("dd-MM-yyyy"),
                    end = anthara_end.ToString("dd-MM-yyyy"),
                    months = months,
                    color = PLANET_COLORS.ContainsKey(planet) ? PLANET_COLORS[planet] : "#666666",
                    icon = PLANET_ICONS.ContainsKey(planet) ? PLANET_ICONS[planet] : "•"
                });
                anthara_start = anthara_end;
            }
        }
        return antharas;
    }

    static bool IsDateWithinRange(string checkDate, string startDateStr, string endDateStr)
    {
        try
        {
            DateTime check_dt = DateTime.ParseExact(checkDate, "dd-MM-yyyy", null);
            DateTime start_dt = DateTime.ParseExact(startDateStr, "dd-MM-yyyy", null);
            DateTime end_dt = DateTime.ParseExact(endDateStr, "dd-MM-yyyy", null);
            return start_dt <= check_dt && check_dt <= end_dt;
        }
        catch
        {
            return false;
        }
    }
}
