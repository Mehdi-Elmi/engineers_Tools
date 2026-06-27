# Engineer Tools

این ریپازیتوری مسیر رسمی فعلی پروژه است:

```text
Mehdi-Elmi/engineers_Tools
```

مسیر قبلی `Mehdi-Elmi/engineers_Toolses` دیگر مسیر توسعه فعال نیست و نباید برای فایل‌های جدید استفاده شود.

## وضعیت فعلی

لانچر باید کامل باقی بماند و همه کارت‌های اصلی را نمایش دهد. تمرکز طراحی فعلی فقط روی محیط `Engineering Design Tools` است، اما این موضوع به معنی حذف یا ساده‌سازی لانچر نیست.

کارت‌های فعلی لانچر:

| کارت | مسیر |
|---|---|
| Engineering Design Tools | `modules/mechanics_dynamics_statics` |
| Circuit Design | `modules/electronic_circuits` |
| Engineering Flowcharts | `modules/engineering_flowcharts` |
| Barcode Designer | `modules/barcode_designer` |
| White Background Remover | `modules/white_background_remover` |

چهار بخش غیر از `Engineering Design Tools` فعلاً placeholder هستند تا لانچر سالم بماند و بعداً هر بخش در چت اختصاصی خودش ادامه پیدا کند.

## فایل‌های اجرایی

فایل نصب و آپدیت از GitHub:

```bat
install_from_github.cmd
```

فایل اجرای برنامه:

```bat
run_engineers_tools.cmd
```

فایل alias برای اجرا:

```bat
run_engineer_tools.cmd
```

## قانون نصب

Installer فقط باید نصب اولیه یا آپدیت انجام دهد. اجرای روزمره باید از `run_engineers_tools.cmd` انجام شود.

مسیر نصب ویندوز:

```text
%LOCALAPPDATA%\EngineerTools
```

Installer commit فعلی GitHub را با فایل زیر مقایسه می‌کند:

```text
%LOCALAPPDATA%\EngineerTools\.install_commit
```

اگر commit تغییر نکرده باشد، zip دوباره دانلود نمی‌شود، extract انجام نمی‌شود، xcopy انجام نمی‌شود و برنامه مستقیم اجرا می‌شود.

## قانون Python dependencies

`run_engineers_tools.cmd` فقط وقتی pip install اجرا می‌کند که:

- `.venv` وجود نداشته باشد.
- یا `requirements.txt` نسبت به stamp قبلی تغییر کرده باشد.

بنابراین نصب پکیج‌ها نباید در هر اجرای برنامه تکرار شود.

## مسیر توکن GitHub

مسیر اصلی:

```text
%USERPROFILE%\Desktop\token.txt
```

مسیر fallback قدیمی:

```text
%USERPROFILE%\Desktop\testdoctoken.txt
```

توکن نباید داخل کد، README، لاگ یا GitHub ذخیره شود.

## مسیر فعال کار فعلی

کار طراحی فعلی روی این مسیر انجام می‌شود:

```text
modules/mechanics_dynamics_statics/workspace.py
```

entry point فعال این بخش:

```text
modules.mechanics_dynamics_statics.module_entry:create_window
```

فایل لانچر نباید برای محدودکردن کار فعلی خراب یا تک‌کارت شود. لانچر باید همه کارت‌ها را نگه دارد و فقط مسیر کاری فعلی در پوشه خودش توسعه پیدا کند.

## مسیر مرکزی Main Menu

فایل مادر پنجره، منوهای اصلی، Canvas، Page Bar، Status Bar، File/Edit/View/Insert/Draw/Help و رفتار عمومی پنجره در مسیر مرکزی زیر نگهداری می‌شود:

```text
src/engineers_tools/app/module_window.py
```

این فایل جزو هیچ پروژه اختصاصی مثل مکانیک، مدار، فلوچارت یا بارکد نیست. تمام پروژه‌ها باید از همین الگوی مرکزی استفاده کنند و فقط overrideهای اختصاصی خودشان را داخل پوشه `modules/...` بنویسند.

Theme مشترک پروژه در این مسیر است:

```text
src/engineers_tools/app/theme.py
```

فایل‌های داخل `modules/mechanics_dynamics_statics` فقط تغییرات اختصاصی `Engineering Design Tools` هستند و نباید جایگزین فایل مادر شوند.

## قانون Start Bar

Start Bar از پنجره مادر جدا شده و در این فایل نگهداری می‌شود:

```text
src/engineers_tools/ui/start_bar.py
```

پنجره مادر فقط جایگاه Start Bar را دارد. اگر هر پروژه ابزارهای متفاوتی نیاز داشت، همان workspace باید متد زیر را override کند:

```text
get_start_bar_tools()
```

این ساختار باعث می‌شود چت‌های جداگانه بتوانند ابزارهای Start Bar همان پروژه را تغییر دهند بدون اینکه `module_window.py` یا لانچر خراب شود.

در `Engineering Design Tools` گزینه `View` باید ابزارهای داخل Start Bar را با همان key ابزار فعال یا مخفی کند. این رفتار در مسیر زیر پیاده‌سازی شده است:

```text
modules/mechanics_dynamics_statics/workspace.py
```

Canvas دیگر عنوان اضافه‌ای مثل `Engineering Design Workspace` داخل خودش ندارد و باید فضای کاری تمیز باقی بماند.

## قانون `__init__.py`

فایل `__init__.py` برای این است که Python یک پوشه را به‌عنوان package بشناسد و importهایی مثل موارد زیر درست کار کنند:

```text
src.engineers_tools.app.controller
modules.mechanics_dynamics_statics.module_entry
```

این فایل محل طراحی Toolbar، Properties، Canvas یا منطق ابزارها نیست. در حالت عادی باید خالی یا بسیار سبک بماند.

هر پوشه‌ای که قرار است به‌عنوان package در import استفاده شود باید `__init__.py` داشته باشد. برای مثال:

```text
src/engineers_tools/__init__.py
src/engineers_tools/app/__init__.py
modules/mechanics_dynamics_statics/__init__.py
```

چت‌هایی که فقط روی Toolbar، Start Bar، Properties یا ابزارهای طراحی کار می‌کنند نباید `__init__.py` را تغییر بدهند، مگر اینکه پوشه Python جدید ساخته شود یا مسیر import واقعاً تغییر کند.

## قانون پنجره مادر

تمام پنجره‌های آینده باید ادامه همین الگو باشند:

- Top Bar: نوار سرمه‌ای بالا با لوگو، عنوان، minimize، maximize و close.
- Command Bar: منوهای `Home`, `File`, `Edit`, `View`, `Insert`, `Draw`, `Help`.
- Start Bar: ابزارهای سریع مثل `Select`, `Line`, `Vector`, `Angle`, `Text`, `Grid`, `Snap`, `Zoom`.
- Properties: پنل سمت چپ برای تنظیمات ابزار یا شیء انتخاب‌شده.
- Canvas: بوم مرکزی گریدبندی‌شده.
- Layers: پنل سمت راست برای ساختار صفحه و آبجکت‌ها.
- Page Bar: بخش Page و Add Page.
- Status Bar: tool select، مختصات، unit سمت چپ و zoom سمت راست.

## قانون پنجره‌های داخلی

هر پنجره داخلی مثل `Open`, `Save As`, `Page Setup`, `Properties`, خطاها و پیام‌های تأیید باید از الگوی ثابت پروژه استفاده کند:

- پوسته کلی با گوشه‌های گرد.
- نوار سرمه‌ای بالا.
- لوگوی پروژه در سمت چپ نوار بالا.
- عنوان دقیق پنجره کنار لوگو.
- دکمه close با همان الگوی پروژه.
- نوار دوم سرمه‌ای یا تیره زیر header برای navigation، مسیر، toolbar داخلی یا توضیح کوتاه عملیاتی.
- بدنه روشن، تمیز و متناسب با همان عملیات.

هیچ پنجره‌ای نباید با ظاهر خام سیستم‌عامل به کاربر نمایش داده شود، مگر اینکه پشت پرده برای دسترسی فایل، چاپ یا API سیستم‌عامل لازم باشد.

## قانون File Dialog

پنجره‌هایی مثل File/Open/Save باید ظاهر استاندارد خود پروژه را داشته باشند. پشت پرده می‌توانند از API استاندارد سیستم‌عامل استفاده کنند، اما پنجره‌ای که کاربر ابتدا می‌بیند باید با طراحی خود پروژه هماهنگ باشد.

`File Type` باید گزینه‌ها را واضح و قابل انتخاب نشان دهد و پسوند نهایی باید بر اساس انتخاب کاربر خودکار روی نام فایل اعمال شود.

## قانون Select

هرجا ابزار Select لازم شد، باید از یک الگوی واحد استفاده شود:

- آیکن Select باید یک نشانگر واضح انتخاب باشد.
- کلیک روی آبجکت باید آن را highlight کند.
- اطلاعات آبجکت انتخاب‌شده باید در Properties نمایش داده شود.
- چند ابزار مختلف نباید رفتار Select جداگانه و ناسازگار داشته باشند.

## قانون Properties

پنل Properties فقط لیست ساده نیست. هر ابزار باید schema تنظیمات خودش را داشته باشد و Properties بر اساس ابزار یا آبجکت انتخاب‌شده تغییر کند. فعلاً placeholderهای پایه ساخته شده‌اند؛ طراحی جزئی بعداً با تأیید کاربر تکمیل می‌شود.
