using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Reflection;
using System.IO;

namespace TeluguAstrology.WinApp
{
    public static class SwissEphemerisPInvoke
    {
        private const string DllName = "swedll.dll"; // logical name used in DllImport
        private static IntPtr nativeHandle = IntPtr.Zero;

        // Ensure native library is loaded (extract from embedded resource if necessary)
        static SwissEphemerisPInvoke()
        {
            // If a swedll exists next to the exe, prefer that
            try
            {
                Assembly asm = Assembly.GetExecutingAssembly();
                string exeDir = AppContext.BaseDirectory;
                string[] candidates = new[] { "swedll.dll", "swedll64.dll", "swedll32.dll" };
                string found = null;
                foreach (var c in candidates)
                {
                    var p = Path.Combine(exeDir, c);
                    if (File.Exists(p)) { found = p; break; }
                }

                if (found != null)
                {
                    nativeHandle = NativeLibrary.Load(found);
                }
                else
                {
                    // Look for embedded resource variant (resource name may include namespace)
                    string resourceName = null;
                    foreach (var rn in asm.GetManifestResourceNames())
                    {
                        if (rn.EndsWith("swedll.dll", StringComparison.OrdinalIgnoreCase) || rn.EndsWith("swedll64.dll", StringComparison.OrdinalIgnoreCase) || rn.EndsWith("swedll32.dll", StringComparison.OrdinalIgnoreCase))
                        {
                            resourceName = rn; break;
                        }
                    }
                    if (resourceName != null)
                    {
                        using var rs = asm.GetManifestResourceStream(resourceName);
                        if (rs != null)
                        {
                            string outPath = Path.Combine(Path.GetTempPath(), "swedll_" + Guid.NewGuid().ToString() + ".dll");
                            using (var fs = File.OpenWrite(outPath))
                            {
                                rs.CopyTo(fs);
                            }
                            nativeHandle = NativeLibrary.Load(outPath);
                        }
                    }
                }

                // Register resolver so DllImport calls for "swedll.dll" resolve to our loaded handle
                if (nativeHandle != IntPtr.Zero)
                {
                    NativeLibrary.SetDllImportResolver(asm, (name, assembly, searchPath) =>
                    {
                        if (name.Equals(DllName, StringComparison.OrdinalIgnoreCase) || name.Equals("swedll", StringComparison.OrdinalIgnoreCase))
                        {
                            return nativeHandle;
                        }
                        return IntPtr.Zero;
                    });
                }
            }
            catch
            {
                // swallow - fallback to normal DllImport behavior (external DLL must be present)
            }
        }
        
        // Common planet ID constants (match values in sweph.h)
        public const int SE_SUN = 0;
        public const int SE_MOON = 1;
        public const int SE_MERCURY = 2;
        public const int SE_VENUS = 3;
        public const int SE_MARS = 4;
        public const int SE_JUPITER = 5;
        public const int SE_SATURN = 6;
        public const int SE_URANUS = 7;
        public const int SE_NEPTUNE = 8;
        public const int SE_PLUTO = 9;
        public const int SE_MEAN_NODE = 10;
        public const int SE_TRUE_NODE = 11;

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi)]
        public static extern void swe_set_ephe_path(string path);

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern void swe_set_sid_mode(int sidmode);

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern double swe_julday(int year, int month, int day, double hour, int gregflag);

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi)]
        public static extern int swe_calc_ut(double tjd_ut, int ipl, int iflag, [In, Out] double[] xx, StringBuilder serr);

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern void swe_houses(double tjd_ut, double geolat, double geolon, byte hsys, [In, Out] double[] cusps, [In, Out] double[] ascmc);

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern double swe_get_ayanamsa_ut(double tjd_ut);
    }
}
