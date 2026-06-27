# Engineer Tools

این ریپازیتوری مسیر رسمی فعلی پروژه است:

```text
Mehdi-Elmi/engineers_Tools
```

مسیر قبلی `Mehdi-Elmi/engineers_Toolses` دیگر مسیر توسعه فعال نیست و نباید برای فایل‌های جدید استفاده شود.

## وضعیت فعلی

در این مرحله فقط محیط اصلی `Engineering Design Tools` فعال شده است. پروژه‌های دیگر فعلاً ساخته نمی‌شوند تا ابتدا الگوی اصلی پنجره، منوها، Start Bar، Properties، Canvas، Layers و File Dialog به تأیید برسد.

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

## مسیر فعال لانچر

لانچر فقط یک کارت فعال دارد:

```text
Engineering Design Tools
```

entry point فعال:

```text
modules.mechanics_dynamics_statics.module_entry:create_window
```

فایل پنجره فعال:

```text
modules/mechanics_dynamics_statics/workspace.py
```

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
