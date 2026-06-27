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
- Command Bar: منوهای `Home`, `File`, `Edit`, `View`, `Insert`, `Draw`, `Modify`.
- Start Bar: ابزارهای سریع مثل `Select`, `Line`, `Vector`, `Angle`, `Text`, `Grid`, `Snap`, `Zoom`.
- Properties: پنل سمت چپ برای تنظیمات ابزار یا شیء انتخاب‌شده.
- Canvas: بوم مرکزی گریدبندی‌شده.
- Layers: پنل سمت راست برای ساختار صفحه و آبجکت‌ها.
- Page Bar: بخش Page و Add Page.
- Status Bar: tool select، مختصات، zoom و unit.

## قانون File Dialog

پنجره‌هایی مثل File/Open/Save باید ظاهر استاندارد خود پروژه را داشته باشند. پشت پرده می‌توانند از `QFileDialog` یا API استاندارد سیستم‌عامل استفاده کنند، اما پنجره‌ای که کاربر ابتدا می‌بیند باید با طراحی خود پروژه هماهنگ باشد.

## قانون Select

هرجا ابزار Select لازم شد، باید از یک الگوی واحد استفاده شود:

- آیکن Select باید یک نشانگر واضح انتخاب باشد.
- کلیک روی آبجکت باید آن را highlight کند.
- اطلاعات آبجکت انتخاب‌شده باید در Properties نمایش داده شود.
- چند ابزار مختلف نباید رفتار Select جداگانه و ناسازگار داشته باشند.

## قانون Properties

پنل Properties فقط لیست ساده نیست. هر ابزار باید schema تنظیمات خودش را داشته باشد و Properties بر اساس ابزار یا آبجکت انتخاب‌شده تغییر کند. فعلاً placeholderهای پایه ساخته شده‌اند؛ طراحی جزئی بعداً با تأیید کاربر تکمیل می‌شود.
