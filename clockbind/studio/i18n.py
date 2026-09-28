"""Interface text in English, Hungarian and Persian. Missing keys fall back to English."""
from __future__ import annotations

LANGS = {"en": "English", "hu": "Magyar", "fa": "فارسی"}
RTL = {"fa"}

T = {
    # navigation
    "nav_home": {"en": "Home", "hu": "Kezdőlap", "fa": "خانه"},
    "nav_bridge": {"en": "Bridge", "hu": "Bridge", "fa": "Bridge"},
    "nav_reports": {"en": "Reports", "hu": "Jelentések", "fa": "گزارش‌ها"},
    "nav_stats": {"en": "Statistics", "hu": "Statisztika", "fa": "آمار"},
    "nav_settings": {"en": "Settings", "hu": "Beállítások", "fa": "تنظیمات"},
    "brand_sub": {"en": "Research assistant · Bridge study", "hu": "Kutatási asszisztens · Bridge-vizsgálat", "fa": "دستیار پژوهش · مطالعه‌ی Bridge"},
    # profiles
    "who": {"en": "Who is using ClockBind?", "hu": "Ki használja a ClockBindot?", "fa": "چه کسی از ClockBind استفاده می‌کند؟"},
    "who_sub": {"en": "Profiles stay on this computer. No password, no online account.",
                "hu": "A profilok ezen a gépen maradnak. Nincs jelszó, nincs online fiók.",
                "fa": "پروفایل‌ها روی همین کامپیوتر می‌مانند. بدون رمز و بدون حساب آنلاین."},
    "new_profile": {"en": "Add a person", "hu": "Új személy", "fa": "افزودن شخص"},
    "name": {"en": "Name as it should appear (e.g. Mr Alavi)", "hu": "Megjelenő név (pl. Alavi úr)", "fa": "نام نمایشی (مثلاً آقای علوی)"},
    "language": {"en": "Language", "hu": "Nyelv", "fa": "زبان"},
    "continue": {"en": "Continue", "hu": "Tovább", "fa": "ادامه"},
    "switch_user": {"en": "Switch person", "hu": "Személy váltása", "fa": "تغییر شخص"},
    "hello_m": {"en": "Good morning, {n}", "hu": "Jó reggelt, {n}", "fa": "صبح بخیر، {n}"},
    "hello_a": {"en": "Good afternoon, {n}", "hu": "Jó napot, {n}", "fa": "عصر بخیر، {n}"},
    "hello_e": {"en": "Good evening, {n}", "hu": "Jó estét, {n}", "fa": "شب بخیر، {n}"},
    # home
    "home_sub_nofile": {"en": "Choose your Bridge workbook once in Settings; ClockBind then shows where the study stands every time you open it.",
                        "hu": "Válassza ki egyszer a Bridge-munkafüzetet a Beállításokban; a ClockBind ezután minden megnyitáskor mutatja, hol tart a vizsgálat.",
                        "fa": "یک بار در تنظیمات، ورک‌بوک Bridge را انتخاب کنید؛ از آن به بعد ClockBind هر بار نشان می‌دهد مطالعه کجاست."},
    "home_sub": {"en": "Step {s}: {left} sources still to review. Pick a task; files stay on this computer.",
                 "hu": "{s}. lépés: még {left} forrás vár átnézésre. Válasszon feladatot; a fájlok ezen a gépen maradnak.",
                 "fa": "قدم {s}: {left} منبع مانده. یک کار را انتخاب کنید؛ فایل‌ها روی همین کامپیوتر می‌مانند."},
    "sources_done": {"en": "sources done", "hu": "forrás kész", "fa": "منبع تمام‌شده"},
    "r_a": {"en": "Evidence", "hu": "Bizonyítékok", "fa": "مدرک"},
    "r_b": {"en": "Criteria", "hu": "Kritériumok", "fa": "معیارها"},
    "r_c": {"en": "Freeze", "hu": "Rögzítés", "fa": "Freeze"},
    "r_d": {"en": "Timelines", "hu": "Idővonalak", "fa": "خط زمانی"},
    "r_e": {"en": "Writing", "hu": "Írás", "fa": "نوشتن"},
    "levels_t": {"en": "Evidence levels", "hu": "Bizonyítéki szintek", "fa": "سطح‌های شواهد"},
    "l3": {"en": "Level 3 · binding clock", "hu": "3. szint · kötő óra", "fa": "سطح ۳ · ساعت binding"},
    "l2": {"en": "Level 2 · mechanism", "hu": "2. szint · mechanizmus", "fa": "سطح ۲ · مکانیزم"},
    "l1": {"en": "Level 1 · typology", "hu": "1. szint · tipológia", "fa": "سطح ۱ · گونه‌شناسی"},
    "held": {"en": "episodes held at S0", "hu": "S0-n tartott epizód", "fa": "رویداد Held در S0"},
    "wb_errors": {"en": "workbook errors", "hu": "munkafüzet-hiba", "fa": "خطای ورک‌بوک"},
    "start": {"en": "Start", "hu": "Indítás", "fa": "شروع"},
    "k1": {"en": "Check my Bridge workbook", "hu": "Bridge-munkafüzet ellenőrzése", "fa": "فایل Bridge را بررسی کن"},
    "k1d": {"en": "See what is missing, which cells to fix and the level of every episode.",
            "hu": "Megmutatja, mi hiányzik, mely cellákat kell javítani, és melyik epizód milyen szinten áll.",
            "fa": "می‌بینید چه کم است، کدام خانه باید درست شود و سطح هر رویداد چیست."},
    "k2": {"en": "Which clock binds?", "hu": "Melyik óra köt?", "fa": "کدام ساعت تعیین‌کننده بود؟"},
    "k2d": {"en": "Enter an episode timeline and get the verdict under the registered rule.",
            "hu": "Adja meg egy epizód idővonalát, és megkapja a regisztrált szabály szerinti ítéletet.",
            "fa": "خط زمانی یک رویداد را وارد کنید و حکم را طبق قانون ثبت‌شده بگیرید."},
    "k3": {"en": "Any personal data?", "hu": "Van személyes adat?", "fa": "داده‌ی شخصی دارد؟"},
    "k3d": {"en": "Finds names, e-mails, phones, IBANs and ID numbers. Values are never shown.",
            "hu": "Neveket, e-maileket, telefonszámokat, IBAN-okat és azonosítókat keres. Az értékeket soha nem mutatja.",
            "fa": "نام، ایمیل، تلفن، IBAN و کد ملی را پیدا می‌کند. خود داده‌ها هرگز نمایش داده نمی‌شوند."},
    "k4": {"en": "Make a report", "hu": "Jelentés készítése", "fa": "گزارش بساز"},
    "k4d": {"en": "A ready PDF for your supervisor or the file: status, levels, checks and date.",
            "hu": "Kész PDF a témavezetőnek vagy az aktába: állapot, szintek, ellenőrzések és dátum.",
            "fa": "یک PDF آماده برای استاد راهنما یا پرونده: وضعیت، سطح‌ها، بررسی‌ها و تاریخ."},
    "next_t": {"en": "Next steps", "hu": "Következő lépések", "fa": "قدم‌های بعدی"},
    "n1": {"en": "Workbook checked without errors", "hu": "Munkafüzet hibamentesen ellenőrizve", "fa": "ورک‌بوک بدون خطا بررسی شد"},
    "n2": {"en": "Review remaining sources", "hu": "A hátralévő források átnézése", "fa": "بررسی منابع باقی‌مانده"},
    "n3": {"en": "Freeze protocol and register on OSF", "hu": "Protokoll rögzítése és OSF-regisztráció", "fa": "Freeze پروتکل و ثبت در OSF"},
    "n4": {"en": "Blind coder packet", "hu": "Csomag a vak kódolónak", "fa": "بسته‌ی کدگذار مستقل"},
    "n5": {"en": "Send the revision to the supervisor", "hu": "A javított kézirat elküldése a témavezetőnek", "fa": "ارسال نسخه‌ی اصلاح‌شده به استاد راهنما"},
    "left": {"en": "left", "hu": "hátra", "fa": "مانده"},
    "done": {"en": "done", "hu": "kész", "fa": "انجام شد"},
    "chat_t": {"en": "ClockBind in your chat", "hu": "ClockBind a csevegőben", "fa": "ClockBind در چت"},
    "chat_on": {"en": "Connected to Claude Desktop", "hu": "Csatlakoztatva: Claude Desktop", "fa": "متصل به Claude Desktop"},
    "chat_off": {"en": "Not connected", "hu": "Nincs csatlakoztatva", "fa": "متصل نیست"},
    "chat_note": {"en": "Only results reach the chat, never cell values.", "hu": "Csak eredmények jutnak a csevegőbe, cellaértékek soha.",
                  "fa": "فقط نتیجه به چت می‌رسد، نه محتوای خانه‌ها."},
    "local": {"en": "Files stay on this computer", "hu": "A fájlok ezen a gépen maradnak", "fa": "فایل‌ها روی همین کامپیوتر می‌مانند"},
    "set_workbook": {"en": "Choose Bridge workbook", "hu": "Bridge-munkafüzet kiválasztása", "fa": "انتخاب ورک‌بوک Bridge"},
    # check wizard
    "step1": {"en": "1. Choose file", "hu": "1. Fájl kiválasztása", "fa": "۱. انتخاب فایل"},
    "step2": {"en": "2. Check", "hu": "2. Ellenőrzés", "fa": "۲. بررسی"},
    "step3": {"en": "3. Result and what to fix", "hu": "3. Eredmény és teendők", "fa": "۳. نتیجه و کارهای لازم"},
    "use_project": {"en": "Use my Bridge workbook", "hu": "A saját Bridge-munkafüzetem", "fa": "ورک‌بوک Bridge خودم"},
    "or_upload": {"en": "or drop another workbook", "hu": "vagy húzzon ide másik munkafüzetet", "fa": "یا ورک‌بوک دیگری را اینجا رها کنید"},
    "check_now": {"en": "Check now", "hu": "Ellenőrzés most", "fa": "همین حالا بررسی کن"},
    "checking": {"en": "Checking every sheet…", "hu": "Minden munkalap ellenőrzése…", "fa": "در حال بررسی همه‌ی شیت‌ها…"},
    "must_fix": {"en": "must be fixed", "hu": "javítandó", "fa": "باید درست شود"},
    "should_check": {"en": "worth checking", "hu": "érdemes megnézni", "fa": "بهتر است بررسی شود"},
    "ok": {"en": "correct", "hu": "rendben", "fa": "درست است"},
    "n_fix": {"en": "{n} item(s) to fix", "hu": "{n} javítandó tétel", "fa": "{n} مورد را باید درست کنید"},
    "all_good": {"en": "Nothing to fix: every check passed", "hu": "Nincs teendő: minden ellenőrzés rendben", "fa": "چیزی برای درست کردن نیست: همه‌ی بررسی‌ها درست است"},
    "locations_only": {"en": "Only cell locations are shown, never their contents.", "hu": "Csak a cellák helye látszik, a tartalmuk soha.",
                       "fa": "فقط محل خانه‌ها نشان داده می‌شود، نه محتوای آن‌ها."},
    "pdf": {"en": "PDF report", "hu": "PDF-jelentés", "fa": "گزارش PDF"},
    "again": {"en": "Check again", "hu": "Újraellenőrzés", "fa": "دوباره بررسی کن"},
    "back_home": {"en": "Back to Home", "hu": "Vissza a kezdőlapra", "fa": "بازگشت به خانه"},
    "all_checks": {"en": "All checks", "hu": "Minden ellenőrzés", "fa": "همه‌ی بررسی‌ها"},
    "levels_now": {"en": "Episode levels now", "hu": "Az epizódok jelenlegi szintje", "fa": "سطح فعلی رویدادها"},
    # clock / privacy / reports
    "tpl": {"en": "Blank timeline template", "hu": "Üres idővonal-sablon", "fa": "قالب خالی خط زمانی"},
    "tl_file": {"en": "Timeline workbook (sheets Episodes and Steps)", "hu": "Idővonal-munkafüzet (Episodes és Steps lap)", "fa": "ورک‌بوک خط زمانی (شیت‌های Episodes و Steps)"},
    "compute": {"en": "Compute verdicts", "hu": "Ítéletek számítása", "fa": "محاسبه‌ی حکم‌ها"},
    "clock_rule": {"en": "Counterfactual critical path with ex-ante durations; verdicts at the earliest and latest date bounds. If they differ, the verdict is Indeterminate.",
                   "hu": "Kontrafaktuális kritikus út előre várt időtartamokkal; ítélet a legkorábbi és a legkésőbbi dátumhatáron. Ha eltérnek, az ítélet: Indeterminate.",
                   "fa": "مسیر بحرانی خلاف واقع با مدت‌های ex-ante؛ حکم در زودترین و دیرترین تاریخ. اگر فرق کنند، حکم Indeterminate است."},
    "pii_file": {"en": "Data file (.xlsx or .csv)", "hu": "Adatfájl (.xlsx vagy .csv)", "fa": "فایل داده (‎.xlsx یا ‎.csv)"},
    "scan": {"en": "Scan for personal data", "hu": "Személyes adatok keresése", "fa": "جست‌وجوی داده‌ی شخصی"},
    "pii_none": {"en": "No personal-data patterns found. This does not prove the file is anonymous.",
                 "hu": "Nem található személyes adatra utaló minta. Ez nem bizonyítja, hogy a fájl anonim.",
                 "fa": "الگویی از داده‌ی شخصی پیدا نشد. این ثابت نمی‌کند فایل ناشناس است."},
    "pii_found": {"en": "Replace these columns with pseudonymised codes before analysis or sharing.",
                  "hu": "Elemzés vagy megosztás előtt cserélje ezeket az oszlopokat álnevesített kódokra.",
                  "fa": "قبل از تحلیل یا اشتراک‌گذاری، این ستون‌ها را با کد مستعار جایگزین کنید."},
    "rep_t": {"en": "Bridge status report", "hu": "Bridge-állapotjelentés", "fa": "گزارش وضعیت Bridge"},
    "rep_make": {"en": "Make the report", "hu": "Jelentés elkészítése", "fa": "ساختن گزارش"},
    "rep_desc": {"en": "One PDF with the study status, the screening flow, episode levels and every check. Suitable for your supervisor.",
                 "hu": "Egy PDF a vizsgálat állapotával, a szűrési folyamattal, az epizódszintekkel és minden ellenőrzéssel. Témavezetőnek is megfelel.",
                 "fa": "یک PDF با وضعیت مطالعه، جریان غربالگری، سطح رویدادها و همه‌ی بررسی‌ها؛ مناسب برای استاد راهنما."},
    "need_workbook": {"en": "Choose your Bridge workbook in Settings first.", "hu": "Először válassza ki a Bridge-munkafüzetet a Beállításokban.",
                      "fa": "اول در تنظیمات ورک‌بوک Bridge را انتخاب کنید."},
    # settings
    "s_profile": {"en": "Profile", "hu": "Profil", "fa": "پروفایل"},
    "s_project": {"en": "Bridge project", "hu": "Bridge-projekt", "fa": "پروژه‌ی Bridge"},
    "s_wb_path": {"en": "Workbook file on this computer", "hu": "Munkafüzet ezen a gépen", "fa": "فایل ورک‌بوک روی همین کامپیوتر"},
    "s_wb_help": {"en": "Paste the full path, e.g. /Users/you/Documents/Bridge_workbook.xlsx (in Finder: right-click the file, hold Option, Copy as Pathname).",
                  "hu": "Illessze be a teljes elérési utat, pl. /Users/on/Documents/Bridge_workbook.xlsx (Finderben: jobb klikk, Option lenyomva, Másolás útvonalként).",
                  "fa": "مسیر کامل را بچسبانید، مثلاً ‎/Users/you/Documents/Bridge_workbook.xlsx (در Finder: کلیک راست روی فایل، Option را نگه دارید، Copy as Pathname)."},
    "s_gates": {"en": "Protocol file (leave empty for the built-in v3.3 draft)", "hu": "Protokollfájl (üresen hagyva a beépített v3.3 tervezet)",
                "fa": "فایل پروتکل (خالی بگذارید تا نسخه‌ی پیش‌نویس v3.3 داخلی استفاده شود)"},
    "save": {"en": "Save", "hu": "Mentés", "fa": "ذخیره"},
    "saved": {"en": "Saved", "hu": "Mentve", "fa": "ذخیره شد"},
    "not_found": {"en": "File not found on this computer.", "hu": "A fájl nem található ezen a gépen.", "fa": "فایل روی این کامپیوتر پیدا نشد."},
    "s_chat": {"en": "Chat tools", "hu": "Csevegőeszközök", "fa": "ابزار چت"},
    "connect": {"en": "Connect to Claude Desktop", "hu": "Csatlakoztatás a Claude Desktophoz", "fa": "اتصال به Claude Desktop"},
    "online_later": {"en": "Online accounts (Google, Microsoft) can be added later; profiles are local for now.",
                     "hu": "Online fiókok (Google, Microsoft) később hozzáadhatók; a profilok most helyiek.",
                     "fa": "حساب آنلاین (Google، Microsoft) را بعداً می‌شود اضافه کرد؛ فعلاً پروفایل‌ها محلی‌اند."},
    "stats_intro": {"en": "Point-and-click statistics: open data, run analyses, export results.", "hu": "Statisztika kattintással: adatok megnyitása, elemzések, eredmények exportja.",
                    "fa": "آمار با کلیک: باز کردن داده، اجرای تحلیل و خروجی گرفتن از نتایج."},
}

# plain-language explanation of workbook-check findings: check name (prefix) -> (title, how to fix)
FIX = {
    "Formula errors": {
        "en": ("A formula shows an error (#DIV/0!, #REF! …)", "Open the cell in Excel and correct the formula or the cells it refers to."),
        "hu": ("Egy képlet hibát mutat (#DIV/0!, #REF! …)", "Nyissa meg a cellát az Excelben, és javítsa a képletet vagy a hivatkozott cellákat."),
        "fa": ("یک فرمول خطا نشان می‌دهد (‎#DIV/0!، ‎#REF! …)", "خانه را در Excel باز کنید و فرمول یا خانه‌هایی را که به آن ارجاع می‌دهد درست کنید.")},
    "Formulas without a calculated value": {
        "en": ("Formulas have not been recalculated", "Open the file in Excel, press Ctrl+Alt+F9 (Mac: Cmd+Alt+F9 or Formulas › Calculate Now) and save."),
        "hu": ("A képletek nincsenek újraszámolva", "Nyissa meg a fájlt az Excelben, nyomja meg a Ctrl+Alt+F9-et (Mac: Képletek › Számolás most), majd mentsen."),
        "fa": ("فرمول‌ها دوباره محاسبه نشده‌اند", "فایل را در Excel باز کنید، Ctrl+Alt+F9 بزنید (در Mac: Formulas › Calculate Now) و ذخیره کنید.")},
    "Sheet name starting with a digit": {
        "en": ("A formula may break in Excel", "The sheet name in this formula needs quotes, e.g. '05_Level_Assessment'!A1. ClockBind can fix it if you send the file."),
        "hu": ("Egy képlet hibás lehet az Excelben", "A képletben a munkalap nevét idézőjelbe kell tenni, pl. '05_Level_Assessment'!A1."),
        "fa": ("ممکن است یک فرمول در Excel خراب شود", "نام شیت در این فرمول باید داخل نقل‌قول باشد، مثلاً ‎'05_Level_Assessment'!A1.")},
    "Entries outside the dropdown list": {
        "en": ("A value is not in the allowed list", "Choose one of the values from the cell's dropdown (for criteria: Yes, No or PENDING)."),
        "hu": ("Egy érték nem szerepel a megengedett listában", "Válasszon a cella legördülő listájából (kritériumoknál: Yes, No vagy PENDING)."),
        "fa": ("مقداری خارج از فهرست مجاز است", "یکی از مقدارهای منوی کشویی خانه را انتخاب کنید (برای معیارها: Yes، No یا PENDING).")},
    "Episode IDs unique": {
        "en": ("The same episode code appears twice", "Give each episode its own code (E20, E21 …) or delete the duplicate row."),
        "hu": ("Ugyanaz az epizódkód kétszer szerepel", "Adjon minden epizódnak saját kódot (E20, E21 …), vagy törölje az ismétlődő sort."),
        "fa": ("یک کد رویداد دو بار آمده است", "به هر رویداد کد جداگانه بدهید (E20، E21 …) یا ردیف تکراری را حذف کنید.")},
    "Level overrides have reason and date": {
        "en": ("A manual level change has no reason or date", "Write the reason (column AN) and the date (column AO), or remove the manual level (column AM)."),
        "hu": ("Egy kézi szintmódosításnál hiányzik az indoklás vagy a dátum", "Írja be az indoklást (AN oszlop) és a dátumot (AO oszlop), vagy törölje a kézi szintet (AM oszlop)."),
        "fa": ("برای تغییر دستی سطح، دلیل یا تاریخ ثبت نشده است", "دلیل (ستون AN) و تاریخ (ستون AO) را بنویسید، یا سطح دستی (ستون AM) را پاک کنید.")},
    "Ceiling overrides have reason and date": {
        "en": ("A manual claim-ceiling change has no reason or date", "Write the reason (AY) and the date (AZ), or remove the manual ceiling (AX)."),
        "hu": ("Egy kézi állítási plafonnál hiányzik az indoklás vagy a dátum", "Írja be az indoklást (AY) és a dátumot (AZ), vagy törölje a kézi plafont (AX)."),
        "fa": ("برای تغییر دستی سقف ادعا، دلیل یا تاریخ ثبت نشده است", "دلیل (AY) و تاریخ (AZ) را بنویسید، یا سقف دستی (AX) را پاک کنید.")},
    "Binding verdicts consistent": {
        "en": ("A binding verdict does not fit its episode", "Verdicts belong to Level 3 episodes only, and a verdict that changes between date bounds must be Indeterminate (see column BA)."),
        "hu": ("Egy kötési ítélet nem illik az epizódhoz", "Ítélet csak 3. szintű epizódnál lehet, és ha a dátumhatárok között változik, Indeterminate kell legyen (BA oszlop)."),
        "fa": ("حکم binding با رویداد جور نیست", "حکم فقط برای رویدادهای سطح ۳ است، و حکمی که بین زودترین و دیرترین تاریخ عوض شود باید Indeterminate باشد (ستون BA).")},
    "No invalid final levels": {
        "en": ("A final level is invalid", "Usually a manual level without reason or date. Complete or remove it."),
        "hu": ("Érvénytelen végső szint", "Általában indoklás vagy dátum nélküli kézi szint. Egészítse ki vagy törölje."),
        "fa": ("سطح نهایی نامعتبر است", "معمولاً سطح دستی بدون دلیل یا تاریخ است. آن را کامل کنید یا پاک کنید.")},
    "Source codes unique": {
        "en": ("A source code appears twice", "Each source (SRC-001 … SRC-045) must appear once in the extraction sheet."),
        "hu": ("Egy forráskód kétszer szerepel", "Minden forrás (SRC-001 … SRC-045) csak egyszer szerepelhet a kivonatolási lapon."),
        "fa": ("یک کد منبع دو بار آمده است", "هر منبع (SRC-001 … SRC-045) باید فقط یک بار در شیت استخراج بیاید.")},
    "COMPLETE source without a number of episodes": {
        "en": ("A COMPLETE source has no episode count", "Write how many distinct episodes the source contains (0 if none, with a short reason)."),
        "hu": ("Egy COMPLETE forrásnál hiányzik az epizódok száma", "Írja be, hány külön epizódot tartalmaz a forrás (0, ha egyet sem, rövid indoklással)."),
        "fa": ("منبع COMPLETE تعداد رویداد ندارد", "بنویسید منبع چند رویداد مستقل دارد (اگر هیچ، ۰ با یک دلیل کوتاه).")},
    "COMPLETE source without episode codes": {
        "en": ("A COMPLETE source has no episode codes", "Write the episode codes of this source, or 0 episodes with a reason."),
        "hu": ("Egy COMPLETE forrásnál hiányoznak az epizódkódok", "Írja be a forrás epizódkódjait, vagy 0 epizódot indoklással."),
        "fa": ("منبع COMPLETE کد رویداد ندارد", "کد رویدادهای این منبع را بنویسید، یا ۰ رویداد با دلیل.")},
    "Every episode code in the extraction sheet has a row": {
        "en": ("An episode has no row in the assessment sheet", "Add a row for this episode code in 05_Level_Assessment."),
        "hu": ("Egy epizódnak nincs sora az értékelő lapon", "Vegyen fel egy sort ennek az epizódkódnak a 05_Level_Assessment lapon."),
        "fa": ("یک رویداد در شیت ارزیابی ردیف ندارد", "برای این کد رویداد در 05_Level_Assessment یک ردیف اضافه کنید.")},
    "Episode marked COMPLETE only when its source is COMPLETE": {
        "en": ("An episode is COMPLETE but its source is not", "Finish the source in 03_Source_Extraction first, or set the episode back to PENDING."),
        "hu": ("Az epizód COMPLETE, de a forrása nem", "Előbb fejezze be a forrást a 03_Source_Extraction lapon, vagy állítsa vissza az epizódot PENDING-re."),
        "fa": ("رویداد COMPLETE است ولی منبعش نه", "اول منبع را در 03_Source_Extraction کامل کنید، یا رویداد را به PENDING برگردانید.")},
    "Episode source codes exist": {
        "en": ("An episode points to an unknown source", "Correct the source code so it matches a row in 03_Source_Extraction."),
        "hu": ("Egy epizód ismeretlen forrásra hivatkozik", "Javítsa a forráskódot, hogy egyezzen a 03_Source_Extraction egyik sorával."),
        "fa": ("یک رویداد به منبع ناشناخته ارجاع می‌دهد", "کد منبع را طوری درست کنید که با یکی از ردیف‌های 03_Source_Extraction یکی باشد.")},
    "Evidence references exist": {
        "en": ("An evidence reference is not in the metadata sheet", "Add the document to 04_Source_Metadata or correct the reference."),
        "hu": ("Egy bizonyítékhivatkozás nincs a metaadat-lapon", "Vegye fel a dokumentumot a 04_Source_Metadata lapra, vagy javítsa a hivatkozást."),
        "fa": ("یک ارجاع سند در شیت متادیتا نیست", "سند را به 04_Source_Metadata اضافه کنید یا ارجاع را درست کنید.")},
    "Possible personal data": {
        "en": ("Possible personal data", "Replace names, contacts and ID numbers with pseudonymised codes; keep the key file separately."),
        "hu": ("Lehetséges személyes adat", "Cserélje a neveket, elérhetőségeket és azonosítókat álnevesített kódokra; a kulcsfájlt külön tárolja."),
        "fa": ("داده‌ی شخصی احتمالی", "نام، اطلاعات تماس و شماره‌های شناسایی را با کد مستعار جایگزین کنید؛ فایل کلید را جدا نگه دارید.")},
    "Header 'Episode ID' not found": {
        "en": ("The assessment sheet has no 'Episode ID' header", "Check that 05_Level_Assessment still has its header row (row 3)."),
        "hu": ("Az értékelő lapon nincs 'Episode ID' fejléc", "Ellenőrizze, hogy a 05_Level_Assessment lap fejlécsora (3. sor) megvan-e."),
        "fa": ("شیت ارزیابی سرستون 'Episode ID' ندارد", "بررسی کنید ردیف سرستون 05_Level_Assessment (ردیف ۳) سر جایش باشد.")},
}


def t(key: str, lang: str, **kw) -> str:
    d = T.get(key, {})
    s = d.get(lang) or d.get("en") or key
    return s.format(**kw) if kw else s


def fix_text(check: str, lang: str):
    for k, v in FIX.items():
        if check.startswith(k):
            return v.get(lang) or v["en"]
    return (check, "")


def digits(s, lang: str) -> str:
    s = str(s)
    return s.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")) if lang == "fa" else s
