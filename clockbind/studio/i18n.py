"""Interface text in English, Hungarian and Persian. Missing keys fall back to English."""
from __future__ import annotations

LANGS = {"en": "English", "hu": "Magyar", "fa": "فارسی"}
RTL = {"fa"}

T = {
    # navigation
    "nav_home": {"en": "Home", "hu": "Kezdőlap", "fa": "خانه"},
    "nav_doctoral": {"en": "Doctoral Programme", "hu": "Doktori program", "fa": "برنامه دکتری"},
    "nav_bridge": {"en": "Bridge", "hu": "Bridge", "fa": "Bridge"},
    "nav_reports": {"en": "Reports", "hu": "Jelentések", "fa": "گزارش‌ها"},
    "nav_stats": {"en": "Statistics", "hu": "Statisztika", "fa": "آمار"},
    "nav_settings": {"en": "Settings", "hu": "Beállítások", "fa": "تنظیمات"},
    "nav_document_audit": {"en": "Document Audit", "hu": "Dokumentum-audit", "fa": "ممیزی اسناد"},
    "nav_privacy": {"en": "Privacy", "hu": "Adatvédelem", "fa": "حریم خصوصی"},
    "nav_reproducibility": {"en": "Reproducibility", "hu": "Reprodukálhatóság", "fa": "بازتولیدپذیری"},
    "nav_publication": {"en": "Publication", "hu": "Publikáció", "fa": "انتشار و پیش‌ثبت"},
    "workspace": {"en": "Research workspace", "hu": "Kutatási munkatér", "fa": "محیط پژوهش"},
    "brand_sub": {"en": "Doctoral research operating system", "hu": "Doktori kutatási rendszer", "fa": "سیستم پژوهشی دوره دکتری"},
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
    "k3d": {"en": "Checks workbooks and documents for names, e-mails, phones, IBANs, ID numbers, amounts and outdated wording. All on this computer; values are never shown.",
            "hu": "Munkafüzetekben és dokumentumokban keres neveket, e-maileket, telefonszámokat, IBAN-okat, azonosítókat, összegeket és elavult megfogalmazást. Minden ezen a gépen történik; az értékeket soha nem mutatja.",
            "fa": "ورک‌بوک‌ها و سندها را برای نام، ایمیل، تلفن، IBAN، کد ملی، مبلغ و عبارت‌های قدیمی بررسی می‌کند. همه‌چیز روی همین کامپیوتر؛ خود داده‌ها هرگز نمایش داده نمی‌شوند."},
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
    "pii_file": {"en": "Files: Excel, CSV, Word, PDF, text or a .zip (e.g. a Google Drive download)", "hu": "Fájlok: Excel, CSV, Word, PDF, szöveg vagy .zip (pl. Google Drive-letöltés)", "fa": "فایل‌ها: Excel، CSV، Word، PDF، متن یا ‎.zip (مثلاً دانلود از Google Drive)"},
    "aud_terms": {"en": "Also check wording against the current Bridge rules (28 Sep 2026)", "hu": "A megfogalmazás ellenőrzése a jelenlegi Bridge-szabályok szerint is (2026. szept. 28.)", "fa": "عبارت‌ها را هم با قواعد فعلی Bridge (۲۸ سپتامبر ۲۰۲۶) بررسی کن"},
    "aud_names": {"en": "Optional: list of names to look for (.txt, one per line; stays on this computer)", "hu": "Nem kötelező: keresendő nevek listája (.txt, soronként egy; ezen a gépen marad)", "fa": "اختیاری: فهرست نام‌ها برای جست‌وجو (‎.txt، هر خط یک نام؛ روی همین کامپیوتر می‌ماند)"},
    "aud_files": {"en": "Files", "hu": "Fájlok", "fa": "فایل‌ها"},
    "aud_find": {"en": "What to fix (locations only; values are never shown)", "hu": "Javítandó (csak helyek; értékek soha nem jelennek meg)", "fa": "چه چیزی باید درست شود (فقط محل؛ مقدارها هرگز نشان داده نمی‌شوند)"},
    "aud_skip": {"en": "Not read", "hu": "Nem olvasott", "fa": "خوانده نشد"},
    "scan": {"en": "Check the files", "hu": "Fájlok ellenőrzése", "fa": "بررسی فایل‌ها"},
    "pii_none": {"en": "No personal-data patterns found. This does not prove the file is anonymous.",
                 "hu": "Nem található személyes adatra utaló minta. Ez nem bizonyítja, hogy a fájl anonim.",
                 "fa": "الگویی از داده‌ی شخصی پیدا نشد. این ثابت نمی‌کند فایل ناشناس است."},
    "pii_found": {"en": "Personal or confidential data found. Remove it or replace it with pseudonymised codes before analysis or sharing.",
                  "hu": "Személyes vagy bizalmas adat található. Elemzés vagy megosztás előtt távolítsa el, vagy cserélje álnevesített kódra.",
                  "fa": "داده‌ی شخصی یا محرمانه پیدا شد. قبل از تحلیل یا اشتراک‌گذاری، آن را حذف یا با کد مستعار جایگزین کنید."},
    "aud_dl": {"en": "Download the findings (Excel)", "hu": "Eredmények letöltése (Excel)", "fa": "دانلود نتایج (Excel)"},
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


# Research Studio page texts (English source -> Hungarian, Persian)
TX = {
 "LOCAL-FIRST": {
  "hu": "HELYBEN",
  "fa": "محلی"
 },
 "WORKSPACE": {
  "hu": "MUNKATÉR",
  "fa": "محیط کار"
 },
 "Files stay on this computer": {
  "hu": "A fájlok ezen a gépen maradnak",
  "fa": "فایل‌ها روی همین کامپیوتر می‌مانند"
 },
 "Upload": {
  "hu": "Feltöltés",
  "fa": "بارگذاری"
 },
 "Configure": {
  "hu": "Beállítás",
  "fa": "تنظیم"
 },
 "Run": {
  "hu": "Futtatás",
  "fa": "اجرا"
 },
 "Review": {
  "hu": "Áttekintés",
  "fa": "بازبینی"
 },
 "Export": {
  "hu": "Exportálás",
  "fa": "خروجی"
 },
 "Bridge": {
  "hu": "Bridge",
  "fa": "Bridge"
 },
 "Evidence → rule engine → defensible claim language.": {
  "hu": "Bizonyíték → szabálymotor → védhető állításszint.",
  "fa": "شواهد ← موتور قاعده ← زبان ادعای قابل‌دفاع."
 },
 "Workbook integrity": {
  "hu": "Munkafüzet-integritás",
  "fa": "سلامت ورک‌بوک"
 },
 "Check formulas, dropdowns, source/episode links, overrides, verdict consistency and privacy flags.": {
  "hu": "Képletek, legördülő listák, forrás–epizód kapcsolatok, felülírások, ítélet-konzisztencia és adatvédelmi jelzések ellenőrzése.",
  "fa": "بررسی فرمول‌ها، فهرست‌های کشویی، پیوند منبع و رویداد، override‌ها، سازگاری حکم و هشدارهای حریم خصوصی."
 },
 "Which clock binds?": {
  "hu": "Melyik óra köt?",
  "fa": "کدام ساعت تعیین‌کننده بود؟"
 },
 "Apply the counterfactual rule, sign-stability test and finance-only temporal actionability.": {
  "hu": "A kontrafaktuális szabály, az előjel-stabilitási teszt és a csak finanszírozásra vonatkozó időbeli cselekvőképesség alkalmazása.",
  "fa": "اجرای قاعدهٔ خلاف واقع، آزمون پایداری علامت و actionability زمانی فقط برای تأمین مالی."
 },
 "Supervisor status": {
  "hu": "Témavezetői állapot",
  "fa": "وضعیت برای استاد راهنما"
 },
 "Generate a bounded report from the current workbook state; no target episode count is imposed.": {
  "hu": "Korlátozott jelentés a munkafüzet jelenlegi állapotából; nincs előírt epizódszám.",
  "fa": "گزارشی محدود از وضعیت فعلی ورک‌بوک؛ هیچ تعداد هدفی برای رویدادها تعیین نمی‌شود."
 },
 "Binding analysis": {
  "hu": "Kötési elemzés",
  "fa": "تحلیل ساعت تعیین‌کننده"
 },
 "Status report": {
  "hu": "Állapotjelentés",
  "fa": "گزارش وضعیت"
 },
 "Supervisor status report": {
  "hu": "Témavezetői állapotjelentés",
  "fa": "گزارش وضعیت برای استاد راهنما"
 },
 "Document Audit": {
  "hu": "Dokumentum-audit",
  "fa": "ممیزی اسناد"
 },
 "Check documents against the current Bridge language and sharing rules.": {
  "hu": "Dokumentumok ellenőrzése a jelenlegi Bridge-megfogalmazás és megosztási szabályok szerint.",
  "fa": "بررسی اسناد با زبان فعلی Bridge و قواعد اشتراک‌گذاری."
 },
 "Drop Word, PDF, Excel, CSV, text or ZIP files": {
  "hu": "Húzzon ide Word-, PDF-, Excel-, CSV-, szöveg- vagy ZIP-fájlokat",
  "fa": "فایل Word، PDF، Excel، CSV، متن یا ZIP را اینجا رها کنید"
 },
 "Current wording rules: Bridge decisions through 28 September 2026.": {
  "hu": "Jelenlegi megfogalmazási szabályok: Bridge-döntések 2026. szeptember 28-ig.",
  "fa": "قواعد فعلی عبارت‌ها: تصمیم‌های Bridge تا ۲۸ سپتامبر ۲۰۲۶."
 },
 "Optional local customer-name list (.txt, one per line)": {
  "hu": "Nem kötelező helyi ügyfélnév-lista (.txt, soronként egy)",
  "fa": "فهرست اختیاری نام مشتری‌ها (‎.txt، هر خط یک نام)"
 },
 "The name list is used locally and is not copied into the findings.": {
  "hu": "A névlista csak helyben használatos, és nem kerül az eredményekbe.",
  "fa": "فهرست نام‌ها فقط روی همین کامپیوتر استفاده می‌شود و در نتایج نمی‌آید."
 },
 "Run document audit": {
  "hu": "Dokumentum-audit futtatása",
  "fa": "اجرای ممیزی اسناد"
 },
 "Reading documents locally…": {
  "hu": "Dokumentumok olvasása helyben…",
  "fa": "خواندن اسناد روی همین کامپیوتر…"
 },
 "Upload one or more files. The audit reports types and locations; detected personal values are never shown.": {
  "hu": "Töltsön fel egy vagy több fájlt. Az audit típusokat és helyeket jelez; a talált személyes értékeket soha nem mutatja.",
  "fa": "یک یا چند فایل بارگذاری کنید. ممیزی نوع و محل را گزارش می‌کند؛ مقدار داده‌های شخصی هرگز نمایش داده نمی‌شود."
 },
 "Files read": {
  "hu": "Beolvasott fájlok",
  "fa": "فایل‌های خوانده‌شده"
 },
 "Outdated wording": {
  "hu": "Elavult megfogalmazás",
  "fa": "عبارت قدیمی"
 },
 "Privacy findings": {
  "hu": "Adatvédelmi találatok",
  "fa": "یافته‌های حریم خصوصی"
 },
 "Not read": {
  "hu": "Nem olvasott",
  "fa": "خوانده نشد"
 },
 "No findings in readable text. This does not prove that a scanned/image-only document is safe.": {
  "hu": "Nincs találat az olvasható szövegben. Ez nem bizonyítja, hogy egy szkennelt/képalapú dokumentum biztonságos.",
  "fa": "در متن قابل‌خواندن یافته‌ای نبود. این ثابت نمی‌کند سند اسکن‌شده یا تصویری امن است."
 },
 "Files not read": {
  "hu": "Nem olvasott fájlok",
  "fa": "فایل‌هایی که خوانده نشدند"
 },
 "Export Excel": {
  "hu": "Excel exportálása",
  "fa": "خروجی Excel"
 },
 "Export PDF": {
  "hu": "PDF exportálása",
  "fa": "خروجی PDF"
 },
 "Privacy": {
  "hu": "Adatvédelem",
  "fa": "حریم خصوصی"
 },
 "Identify personal or confidential data before analysis, coding or sharing.": {
  "hu": "Személyes vagy bizalmas adatok azonosítása elemzés, kódolás vagy megosztás előtt.",
  "fa": "شناسایی داده‌های شخصی یا محرمانه پیش از تحلیل، کدگذاری یا اشتراک‌گذاری."
 },
 "Files to scan": {
  "hu": "Ellenőrizendő fájlok",
  "fa": "فایل‌های مورد بررسی"
 },
 "Optional local name dictionary (.txt)": {
  "hu": "Nem kötelező helyi névszótár (.txt)",
  "fa": "فهرست اختیاری نام‌ها (‎.txt)"
 },
 "Run privacy scan": {
  "hu": "Adatvédelmi ellenőrzés futtatása",
  "fa": "اجرای بررسی حریم خصوصی"
 },
 "Scanning locally…": {
  "hu": "Ellenőrzés helyben…",
  "fa": "بررسی روی همین کامپیوتر…"
 },
 "ClockBind reports the category and location only. It never puts the detected value into the findings table.": {
  "hu": "A ClockBind csak a kategóriát és a helyet jelzi; a talált értéket soha nem teszi az eredménytáblába.",
  "fa": "ClockBind فقط نوع و محل را گزارش می‌کند و مقدار پیدا‌شده را هرگز در جدول نتایج نمی‌گذارد."
 },
 "Findings": {
  "hu": "Találatok",
  "fa": "یافته‌ها"
 },
 "Review these locations before sharing the files.": {
  "hu": "Megosztás előtt nézze át ezeket a helyeket.",
  "fa": "پیش از اشتراک‌گذاری فایل‌ها، این محل‌ها را بررسی کنید."
 },
 "No configured personal-data patterns were found in readable text. This is a screening aid, not proof of anonymity.": {
  "hu": "Az olvasható szövegben nem található beállított személyesadat-minta. Ez szűrési segédlet, nem az anonimitás bizonyítéka.",
  "fa": "در متن قابل‌خواندن الگوی داده‌ی شخصی پیدا نشد. این یک ابزار غربالگری است، نه اثبات ناشناس بودن."
 },
 "Export privacy findings": {
  "hu": "Adatvédelmi találatok exportálása",
  "fa": "خروجی یافته‌های حریم خصوصی"
 },
 "Reproducibility": {
  "hu": "Reprodukálhatóság",
  "fa": "بازتولیدپذیری"
 },
 "Tie every result to the exact data, protocol, software and code used.": {
  "hu": "Minden eredmény a pontosan használt adathoz, protokollhoz, szoftverhez és kódhoz kötve.",
  "fa": "هر نتیجه به دادهٔ دقیق، پروتکل، نرم‌افزار و کد استفاده‌شده گره می‌خورد."
 },
 "Project manifest": {
  "hu": "Projektjegyzék",
  "fa": "شناسنامهٔ پروژه"
 },
 "AI-safe export": {
  "hu": "MI-biztos export",
  "fa": "خروجی امن برای هوش مصنوعی"
 },
 "Run history": {
  "hu": "Futtatási előzmények",
  "fa": "تاریخچهٔ اجراها"
 },
 "Citation": {
  "hu": "Hivatkozás",
  "fa": "استناد"
 },
 "Code hash": {
  "hu": "Kód-hash",
  "fa": "هش کد"
 },
 "Choose the Bridge workbook in Settings to build a project manifest.": {
  "hu": "A projektjegyzékhez válassza ki a Bridge-munkafüzetet a Beállításokban.",
  "fa": "برای ساختن شناسنامهٔ پروژه، ورک‌بوک Bridge را در تنظیمات انتخاب کنید."
 },
 "The export contains aggregate project state and hashes only—no workbook cell values, raw document text, personal-data values or local input paths.": {
  "hu": "Az export csak összesített projektállapotot és hash-eket tartalmaz – cellaértékeket, dokumentumszöveget, személyes adatokat vagy helyi elérési utakat nem.",
  "fa": "این خروجی فقط وضعیت تجمیعی پروژه و هش‌ها را دارد؛ نه مقدار سلول، نه متن سند، نه دادهٔ شخصی و نه مسیر فایل."
 },
 "Create AI-safe research export": {
  "hu": "MI-biztos kutatási export készítése",
  "fa": "ساختن خروجی پژوهشی امن برای هوش مصنوعی"
 },
 "Set a Bridge workbook first.": {
  "hu": "Először állítson be egy Bridge-munkafüzetet.",
  "fa": "اول ورک‌بوک Bridge را تنظیم کنید."
 },
 "No local run manifests were found yet.": {
  "hu": "Még nincs helyi futtatási jegyzék.",
  "fa": "هنوز شناسنامهٔ اجرایی روی این کامپیوتر پیدا نشد."
 },
 "Use the release/version DOI actually assigned to the version used in the study; do not cite a draft DOI as if released.": {
  "hu": "A tanulmányban használt verzióhoz ténylegesen kiadott DOI-t használja; tervezet-DOI-t ne idézzen kiadottként.",
  "fa": "به DOI نسخه‌ای استناد کنید که واقعاً در مطالعه استفاده شده؛ DOI پیش‌نویس را منتشرشده جا نزنید."
 }
}


def tx(text: str, lang: str) -> str:
    """Translate a Research Studio page text; English (or unknown) falls back to the source."""
    return TX.get(text, {}).get(lang, text) if lang != "en" else text
