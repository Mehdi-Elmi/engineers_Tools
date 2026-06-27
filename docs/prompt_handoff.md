# دستور انتقال به چت بعدی

متن زیر را در شروع چت جدید بده:

```text
پروژه روی GitHub در ریپازیتوری Mehdi-Elmi/engineers_Tools است.
مسیر قبلی Mehdi-Elmi/engineers_Toolses مسیر توسعه فعال نیست.

قبل از هر تغییر این فایل‌ها را بخوان:
README.md
docs/window_pattern.md
docs/prompt_handoff.md
modules/mechanics_dynamics_statics/README.md

قانون اصلی:
لانچر باید کامل باقی بماند و پنج کارت اصلی را نشان دهد:
Engineering Design Tools
Circuit Design
Flowcharts
Barcode
Background

تمرکز فعلی طراحی فقط روی Engineering Design Tools است، اما این موضوع به معنی حذف کارت‌های دیگر یا ساده‌سازی لانچر نیست.
برای پروژه‌های دیگر فقط placeholder موجود را نگه دار و طراحی نهایی نساز مگر اینکه کاربر صریحاً دستور بدهد.

فایل نصب:
install_from_github.cmd

فایل اجرا:
run_engineers_tools.cmd

مسیر نصب ویندوز:
%LOCALAPPDATA%\EngineerTools

مسیر توکن:
%USERPROFILE%\Desktop\token.txt
fallback:
%USERPROFILE%\Desktop\testdoctoken.txt

لانچر:
src/engineers_tools/app/launcher_window.py

کامپوننت کارت گرافیکی لانچر:
src/engineers_tools/ui/launcher_button.py

کنترلر:
src/engineers_tools/app/controller.py

رجیستری ماژول‌ها:
src/engineers_tools/app/modules.py

پنجره مادر:
src/engineers_tools/app/module_window.py

Start Bar مشترک:
src/engineers_tools/ui/start_bar.py

قانون Start Bar:
Start Bar مستقل از پنجره مادر است.
پنجره مادر فقط StartBar را صدا می‌زند.
برای ابزارهای اختصاصی هر ماژول، متد get_start_bar_tools() در workspace همان ماژول override شود.
چت اختصاصی Toolbar نباید برای تغییر آیتم‌ها ساختار module_window.py را خراب کند مگر اینکه قانون عمومی کل پروژه تغییر کند.

مسیر فعال Engineering Design Tools:
modules/mechanics_dynamics_statics/module_entry.py
modules/mechanics_dynamics_statics/workspace.py

entry point فعال:
modules.mechanics_dynamics_statics.module_entry:create_window

قانون __init__.py:
__init__.py فقط برای package/import است.
منطق Toolbar، Properties، Canvas، Select یا File Dialog داخل __init__.py نوشته نشود.
چت Toolbar فقط وقتی با __init__.py کار دارد که package جدید ساخته شود یا مسیر import تغییر کند.

قانون طراحی:
UI انگلیسی باشد.
گزارش فارسی RTL باشد.
هر پنجره جدید ادامه docs/window_pattern.md باشد.
File/Open/Save باید پنجره ظاهری خود پروژه را داشته باشد و فقط پشت پرده از QFileDialog استفاده کند.
Canvas نباید عنوان اضافه مثل Engineering Design Workspace داخل خودش داشته باشد.
Properties باید بر اساس ابزار یا آبجکت انتخاب‌شده تغییر کند.
Select باید در کل پروژه یک رفتار واحد داشته باشد.

قانون نصب:
installer فقط وقتی commit جدید باشد دانلود و کپی کند.
run_engineers_tools.cmd فقط وقتی .venv وجود ندارد یا requirements.txt تغییر کرده باشد pip install اجرا کند.
```
