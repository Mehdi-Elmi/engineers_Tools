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

پنجره فایل پروژه:
src/engineers_tools/app/project_file_dialog.py

Theme:
src/engineers_tools/app/theme.py

لوگوی اصلی:
پوشه logo/ در ریشه ریپو.
پنجره مادر اولین فایل تصویری معتبر داخل logo/ را به عنوان لوگوی TopBar می‌خواند.
فرمت‌های معتبر: png, jpg, jpeg, bmp, webp.
اگر لوگو خوانده نشد فقط fallback متن AT دیده می‌شود؛ چت‌های بعدی نباید AT را به عنوان لوگوی اصلی طراحی کنند.

قانون ظاهر پنجره مادر:
TopBar و StatusBar باید سرمه‌ای هماهنگ باشند.
StatusBar باید گوشه‌های پایین را گرد کند.
Zoom در سمت چپ StatusBar است و Unit در سمت راست باقی می‌ماند.
Close باید علامت واقعی × باشد، نه x.
Home باید دکمه گرافیکی واضح با آیکن خانه سه‌بعدی و رنگی باشد.
File/Edit/View/Insert/Draw/Help باید متن ساده شبیه منوی ویندوز باشند، نه دکمه برجسته.
وقتی کاربر روی File/Edit/View/Insert/Draw کلیک می‌کند، منو باید دقیقاً زیر همان دکمه مثل dropdown ویندوز پایین بیاید؛ نباید مثل دیالوگ وسط صفحه باز شود.
داخل dropdown نباید عنوان تکراری مثل File یا Edit نمایش داده شود.
خود dropdown باید باکس گرد، شکیل و هماهنگ با پروژه باشد.
عرض dropdown باید Auto Fit و جمع‌وجور باشد.
پنجره مادر و dropdownها باید با mask واقعی گرد شوند تا هیچ مستطیل تیز پشت گوشه‌ها دیده نشود.
Help dropdown ندارد؛ فقط یک کلید است و باید صفحه Help برنامه را باز کند.
Modify حذف شده و نباید بدون دستور جدید کاربر برگردد.
Add Page و دکمه‌های Yes/No/Apply/Confirm باید از الگوی ConfirmButton استفاده کنند.
هر پنجره، دیالوگ و منوی بازشونده باید گوشه گرد و ظاهر هماهنگ با پروژه داشته باشد.

منوهای ثابت پنجره مادر:
File: New, Open, Save, Save As, Page Setup, Print Setup, Import, Export, Properties
Edit: Copy, Cut, Paste, Move, Undo, Redo, Repeat Last Tools, Select All, Group, Ungroup
View: Start Bar, Grid, Ruler, Snap
Insert: فعلاً فقط Text
Draw: فعلاً خالی است.
Help: صفحه Help مستقل باز می‌کند.

قانون انتخاب View و گزینه‌های مشابه:
گزینه‌های روشن/خاموش باید نماد دایره‌ای داشته باشند.
حالت فعال با دایره پر/نقطه داخلی مشخص می‌شود.
حالت غیرفعال با دایره خالی مشخص می‌شود.
این الگو بعداً مبنای Select و انتخاب‌های رادیویی هم هست.

قانون عملکرد منوها:
Undo/Redo/Cut/Copy/Paste/Select All اگر ویجت فعال عملیات واقعی داشته باشد همان را اجرا می‌کند.
کلید Delete همچنان در سطح پنجره ثبت است، حتی اگر در dropdown فعلی Edit نمایش داده نشود.
Grid واقعاً Canvas را روشن و خاموش می‌کند.
Start Bar واقعاً نوار ابزار سریع را روشن و خاموش می‌کند.
Ruler, Snap, Repeat Last Tools, Group, Ungroup, Move تا زمان ساخت موتور آبجکت‌ها وضعیت را در StatusBar اعلام می‌کنند و بعداً به منطق واقعی وصل می‌شوند.

قانون Zoom:
StatusBar یک کنترل Zoom دارد.
مقدار پیش‌فرض 100% است.
کاربر باید بتواند عدد اعشاری مثل 100.25% وارد کند.
فلش‌های بالا و پایین مقدار را با پله 5% تغییر می‌دهند.
Zoom روی کل GridCanvas اعمال می‌شود.
Unit باید در سمت راست StatusBar مشخص و جدا بماند.

قانون File Dialog:
Open/Save/Save As/Import/Export باید از src/engineers_tools/app/project_file_dialog.py استفاده کنند.
شروع عملیات نباید با پنجره خام QFileDialog باشد.
پنجره فایل باید TopBar سرمه‌ای، نوار ناوبری تیره، Back, Up, مسیر فعلی، Places، لیست فایل‌ها، File Name و File Type داشته باشد.
Places باید از مسیرهای واقعی سیستم مثل Desktop, Downloads, Documents, Pictures, OneDrive و driveها ساخته شود.
آیکن فایل‌ها و فولدرها باید از icon provider سیستم گرفته شود تا PDF، فولدر و فایل‌های دیگر نماد مناسب خودشان را داشته باشند.
Open باید PDF، فایل‌های پروژه، SVG و تصاویر را انتخاب کند و مسیر را به workspace بدهد.
Save اگر فایل فعلی وجود داشته باشد همان را ذخیره می‌کند؛ اگر مسیر فعلی ندارد باید Save As باز شود.
Save As مسیر جدید می‌گیرد و پسوند پیش‌فرض مناسب اضافه می‌کند.
ذخیره PDF باید فایل PDF معتبر تولید کند و بعداً به موتور واقعی رندر/پرینت وصل شود.
خروجی فعلی تا قبل از موتور طراحی، placeholder معتبر برای .etools, .pdf, .svg, .png می‌سازد.

قانون New:
New نباید پنجره قبلی را ببندد.
New باید یک workspace جدید از همان ماژول بسازد و پنجره قبلی همچنان در دسترس بماند.
کنترل این رفتار در src/engineers_tools/app/controller.py انجام می‌شود.

قانون Minimize/Maximize:
پنجره‌های ماژول frameless هستند.
minimize باید از _minimize_window استفاده کند.
maximize باید دستی با screen.availableGeometry انجام شود، نه فقط showMaximized ساده.
restore باید از _normal_geometry استفاده کند.

Start Bar مشترک:
src/engineers_tools/ui/start_bar.py

قانون Start Bar:
Start Bar مستقل از پنجره مادر است.
پنجره مادر فقط StartBar را صدا می‌زند.
برای ابزارهای اختصاصی هر ماژول، متد get_start_bar_tools() در workspace همان ماژول override شود.
چت اختصاصی Toolbar نباید برای تغییر آیتم‌ها ساختار module_window.py را خراب کند مگر اینکه قانون عمومی کل پروژه تغییر کند.
ابزارهای Grid, Snap, Unit بعد از طراحی و تأیید باید به ابزارهای ثابت مشترک تبدیل شوند.

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
طراح و برنامه‌نویس باید حرفه‌ای و خلاقانه تصمیم بگیرد؛ اگر الگوی فعلی مناسب نبود، تغییر مسیر با ثبت مستندات مجاز است.
Canvas نباید عنوان اضافه مثل Engineering Design Workspace داخل خودش داشته باشد.
Properties باید بر اساس ابزار یا آبجکت انتخاب‌شده تغییر کند.
Select باید در کل پروژه یک رفتار واحد داشته باشد.

قانون نصب:
installer فقط وقتی commit جدید باشد دانلود و کپی کند.
run_engineers_tools.cmd فقط وقتی .venv وجود ندارد یا requirements.txt تغییر کرده باشد pip install اجرا کند.
```
