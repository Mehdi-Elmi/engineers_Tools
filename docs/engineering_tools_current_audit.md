<div dir="rtl" align="right">

# گزارش بازبینی فعلی Engineer Tools

تاریخ تهیه: 2026-07-02

این گزارش برای انتقال دقیق وضعیت پروژه به یک چت یا توسعه‌دهنده‌ی دیگر نوشته شده است. هدف گزارش این است که مشخص شود هر بخش برنامه از کدام فایل می‌آید، کدام فایل‌ها روی هم تداخل دارند، کدام قوانین طراحی باید حفظ شوند، و چرا بخش Text / Equation Math / Backspace / Copy / Paste / Delete دچار شکست شده است.

## هشدار اصلی

وضعیت فعلی برنامه به خاطر Patchهای زیاد و چندلایه شکننده شده است. مخصوصاً بخش Text الان چند مالک هم‌زمان دارد:

- یک فایل Text Box را می‌سازد.
- چند فایل دیگر همان Text Box را دوباره Patch می‌کنند.
- چند فایل جداگانه `keyPressEvent` و `eventFilter` را عوض می‌کنند.
- چند فایل دیگر Copy / Paste / Delete / Backspace را در سطح Canvas یا کل برنامه می‌گیرند.
- بخش Equation Math با درج تصویر داخل `QTextEdit` پیاده شده و این روش برای تایپ زنده، RTL، Backspace، Selection، Copy/Paste و ادامه‌ی جمله مناسب نیست.

نتیجه‌ی مستقیم این تداخل‌ها این است که کاربر داخل Text Box متن را انتخاب می‌کند، اما عملیات به جای محتوای متن گاهی روی خود باکس یا Canvas اجرا می‌شود، یا کلید Backspace کاراکتر درست را پاک نمی‌کند.

## مسیر اجرای برنامه

| بخش | فایل | نقش فعلی |
|---|---|---|
| شروع برنامه | `src/engineers_tools/main.py` | راه‌اندازی برنامه، نصب Patchهای عمومی، نمایش Launcher |
| کنترل انتخاب ماژول | `src/engineers_tools/app/controller.py` | بازکردن ماژول انتخاب‌شده از Launcher |
| پنجره‌ی اصلی ماژول | `src/engineers_tools/app/module_window.py` | قاب اصلی، منو، شورتکات‌ها، Status، File/Edit/View و ساخت پنجره‌ی ماژول |
| نقطه ورود Engineer Design Tools | `modules/mechanics_dynamics_statics/module_entry.py` | زنجیره‌ی Patchهای مخصوص Engineering Design Tools را نصب می‌کند |
| Workspace و Canvas پایه | `modules/mechanics_dynamics_statics/workspace.py` | Canvas، اشیا، انتخاب، Move، Resize، Rotate، Zoom، Page و عملیات اصلی |

## زنجیره‌ی Patch در `module_entry.py`

این فایل در حال حاضر Patchها را پشت سر هم اجرا می‌کند. بخش مهم این است که چند Patch انتهایی دوباره روی Text و Cursor اعمال می‌شوند:

| ترتیب تقریبی | Patch | خطر / نقش |
|---|---|---|
| میانی | `apply_ui_text_tool_final_patch()` | ساخت Text Bar و Text Box پایه |
| میانی | `apply_ui_text_tool_runtime_fix_patch()` | اصلاح Runtime برای Text Tool |
| میانی | `apply_ui_text_runtime_guard_patch()` | نگهبان Runtime برای Text |
| میانی | `apply_text_list_settings_patch()` | تنظیمات Bullet / Numbering اولیه |
| میانی | `apply_text_color_swatch_patch()` | رنگ‌ها و Swatchهای Text |
| میانی | `apply_text_list_settings_final_patch()` | تنظیمات نهایی لیست‌ها |
| میانی | `apply_text_color_inline_palette_patch()` | پالت رنگ Inline |
| انتهایی | `apply_project_dialog_style_cursor_patch()` | هم Style و هم Cursor و هم Text/Math را لمس می‌کند |
| انتهایی | `apply_text_toolbar_word_behavior_patch()` | رفتار شبیه Word برای Text |
| انتهایی | `apply_text_runtime_performance_editing_patch()` | عملکرد و ویرایش Text؛ خودش `keyPressEvent` را لمس می‌کند |
| انتهایی | `apply_final_focus_editing_icons_patch()` | Focus و Editing Icons؛ با رویدادها درگیر است |
| انتهایی | `apply_text_line_math_symbols_patch()` | Line spacing، Math symbols، Bullet/Numbering Popup و key handler |
| انتهایی | `apply_text_lag_final_patch()` | Patch مربوط به Lag و Text |
| آخر | `apply_text_toolbar_final_event_safety_patch()` | مالک نهایی اعلام شده برای Keyboard، Color، Line Spacing، Math، Painting |
| دوباره | `apply_project_dialog_style_cursor_patch()` | دوباره اجرا می‌شود و ممکن است Patch قبلی را تغییر دهد |
| دوباره | `apply_text_toolbar_final_event_safety_patch()` | دوباره اجرا می‌شود تا آخرین مالک باشد |

نکته‌ی مهم: همین اجرای دوباره نشان می‌دهد که سیستم به جای معماری تمیز، با غلبه‌ی آخرین Patch روی Patchهای قبلی اداره می‌شود. این ساختار باید اصلاح شود.

## فایل‌های پایه‌ی طراحی پنجره و منو

| فایل | مسئولیت | قانون طراحی مرتبط |
|---|---|---|
| `src/engineers_tools/app/theme.py` | رنگ‌های اصلی، `WindowRoot`، `TopBar`، `ProjectMenuShell`، `MenuItemButton`، دکمه Close | منوها و پنجره‌ها باید از همین الگو کپی شوند |
| `src/engineers_tools/app/module_window.py` | ساخت TopBar، Logo، منوی File/Edit/View، Context Menu | منوی File نمونه‌ی مرجع منوی بازشونده است |
| `src/engineers_tools/app/project_file_dialog.py` | Open / Save / Save As / Import / Export dialog | مرجع پنجره‌های فایل و پس‌زمینه‌ی استاندارد |
| `src/engineers_tools/app/runtime_ui_patch.py` | Page Setup و بعضی Dialogهای Runtime | بعضی Styleهای Arrow/Spin در اینجا مستقل نوشته شده‌اند و باید یکی شوند |
| `src/engineers_tools/app/engineering_properties_patch.py` | File > Properties، General، Shortcut Key | پنجره Properties باید از نظر عرض و Style دوباره استاندارد شود |

قانون طراحی که باید ثابت بماند:

- پنجره‌ی اصلی و پنجره‌های اصلی داخلی: گوشه‌های گرد کامل.
- Header سرمه‌ای مثل پنجره‌ی اصلی.
- Logo از مسیر واقعی خوانده شود، نه با متن جایگزین.
- دکمه Close در حالت عادی هم‌رنگ Header؛ روی Hover قرمز و X سفید.
- منوی بازشونده مثل File/Edit/View: باکس گرد، ردیف‌های روشن، خط رنگی فقط روی Hover یا انتخاب فعال.
- هیچ زمینه‌ی سفید تیزگوشه زیر منوها نباید دیده شود.

## فایل‌های Canvas، انتخاب، Move، Resize، Rotate

| فایل | نقش |
|---|---|
| `modules/mechanics_dynamics_statics/workspace.py` | منطق پایه‌ی Canvas، اشیا، انتخاب، Move، Resize، Rotate، Copy/Paste پایه |
| `modules/mechanics_dynamics_statics/interaction_fixes.py` | اصلاح تعاملات Canvas، Cursor، Resize/Rotate |
| `modules/mechanics_dynamics_statics/final_interaction_policy_fixes.py` | سیاست نهایی تعاملات؛ هنوز در بعضی مسیرها `hand_open` و `hand_closed` دیده می‌شود |
| `modules/mechanics_dynamics_statics/svg_cursor_assets_activation_patch.py` | Mapping اصلی Cursorها به SVG |
| `modules/mechanics_dynamics_statics/engineering_runtime_audit_final_patch.py` | Redirect بعضی Cursorهای hand به move/rotate |
| `src/engineers_tools/app/engineering_ui_small_fixes_patch.py` | Cursorهای Move/Rotate/Resize در بعضی مسیرها |
| `src/engineers_tools/app/engineering_zoom_print_patch.py` | هنوز در چند نقطه `hand_open.svg` و `hand_closed.svg` برای Rotate/Move دیده می‌شود |
| `modules/mechanics_dynamics_statics/native_cursor_lock_patch.py` | تلاش برای جلوگیری از Cursorهای native ویندوز |

ریشه‌ی مشکل دست در Move/Rotate: چند مسیر مختلف هنوز دست را فراخوانی می‌کنند. تا وقتی همه‌ی Cursorها از یک تابع واحد نیایند، با هر Patch جدید احتمال برگشت دست وجود دارد.

## Assetها و مسیرهای تصویری

| مسیر | محتوا |
|---|---|
| `logo/bar.png` | لوگوی اصلی برنامه برای Headerها |
| `src/engineers_tools/assets/ui_icons/mouse_cursor.svg` | Cursor اصلی موس |
| `src/engineers_tools/assets/ui_icons/move_cursor.svg` | Cursor Move |
| `src/engineers_tools/assets/ui_icons/rotate.svg` | نماد Rotate |
| `src/engineers_tools/assets/ui_icons/rotate_cursor.svg` | Cursor قدیمی Rotate؛ باید به `rotate.svg` یا مسیر واحد وصل شود |
| `src/engineers_tools/assets/ui_icons/hand_open.svg` | مسیر قدیمی دست باز؛ نباید برای Move/Rotate استفاده شود مگر قانون جدید بخواهد |
| `src/engineers_tools/assets/ui_icons/hand_closed.svg` | مسیر قدیمی مشت؛ نباید برای Move/Rotate استفاده شود |
| `src/engineers_tools/assets/ui_icons/resize_horizontal.svg` | Resize افقی |
| `src/engineers_tools/assets/ui_icons/resize_vertical.svg` | Resize عمودی |
| `src/engineers_tools/assets/ui_icons/corner_resize_a.svg` | Resize گوشه NW/SE |
| `src/engineers_tools/assets/ui_icons/corner_resize_b.svg` | Resize گوشه NE/SW |
| `src/engineers_tools/assets/ui_icons/spin_up.svg` | فلش بالا |
| `src/engineers_tools/assets/ui_icons/spin_down.svg` | فلش پایین |
| `src/engineers_tools/assets/ui_icons/combo_down.svg` | فلش ComboBox |

قانون پیشنهادی: هیچ فایل دیگری نباید مستقیم `hand_open.svg`، `hand_closed.svg`، `SizeHorCursor`، `SizeVerCursor` یا Cursor native ویندوز را تنظیم کند. همه باید از یک API مشترک مثل `project_cursor(kind)` استفاده کنند.

## وضعیت Text System

| فایل | مسئولیت فعلی | ریسک |
|---|---|---|
| `modules/mechanics_dynamics_statics/ui_text_tool_final_patch.py` | ساخت `InlineTextBar`، کلاس `_CanvasTextEdit`، ساخت Text Box با کلیک یا Drag، ذخیره متن در Object | پایه‌ی اصلی Text است و باید مالک واحد شود |
| `modules/mechanics_dynamics_statics/ui_text_tool_runtime_fix_patch.py` | اصلاحات Runtime روی نوار Text، Buttonها و Style | می‌تواند با فایل پایه تداخل کند |
| `modules/mechanics_dynamics_statics/ui_text_runtime_guard_patch.py` | نگهبان Runtime برای Text | احتمال تداخل با Eventها |
| `modules/mechanics_dynamics_statics/text_toolbar_word_behavior_patch.py` | رفتار شبیه Word | باید فقط به یک Text Controller وصل شود |
| `modules/mechanics_dynamics_statics/text_runtime_performance_editing_patch.py` | Performance و Editing، Auto Bullet/Number | خودش `EngineeringCanvas.keyPressEvent` را Patch می‌کند |
| `modules/mechanics_dynamics_statics/text_line_math_symbols_patch.py` | Math symbols، Line spacing، Bullet/Numbering popup، بعضی Shortcutها | یکی از منابع اصلی Popups و Key handling |
| `modules/mechanics_dynamics_statics/text_lag_final_patch.py` | کاهش Lag و اصلاح Text | احتمال تداخل با final event safety |
| `modules/mechanics_dynamics_statics/final_focus_editing_icons_patch.py` | Focus و Editing Icons | ممکن است ShortcutOverride یا KeyPress را بگیرد |
| `modules/mechanics_dynamics_statics/project_dialog_style_cursor_patch.py` | Style، Cursor، Text/Math | دوبار در `module_entry.py` اجرا می‌شود و ریسک بالا دارد |
| `modules/mechanics_dynamics_statics/text_toolbar_final_event_safety_patch.py` | مالک نهایی فعلی برای Keyboard/Color/LineSpacing/Math/Painting | بیشترین ریسک فعلی؛ باید کوچک یا حذف شود |
| `src/engineers_tools/app/engineering_text_editor_patch.py` | Patch عمومی Text Editor در سطح App | روی `QTextEdit`, `QPlainTextEdit`, `QLineEdit` اثر می‌گذارد |

## علت محتمل خرابی Backspace / Copy / Paste / Delete

چند فایل هم‌زمان این کلیدها را می‌گیرند:

| فایل | نوع دخالت |
|---|---|
| `modules/mechanics_dynamics_statics/ui_text_tool_final_patch.py` | `_CanvasTextEdit.event` و `_CanvasTextEdit.keyPressEvent` |
| `modules/mechanics_dynamics_statics/text_line_math_symbols_patch.py` | `_handle_editor_key` و Copy/Paste/Delete/Backspace |
| `modules/mechanics_dynamics_statics/text_runtime_performance_editing_patch.py` | Patch روی `EngineeringCanvas.keyPressEvent` |
| `modules/mechanics_dynamics_statics/text_toolbar_final_event_safety_patch.py` | EventFilter جدید، override کلاس `_CanvasTextEdit`، و Routing نهایی کلیدها |
| `src/engineers_tools/app/interaction_ui_patch.py` | شورتکات‌های سطح Window و Canvas، Delete/Backspace برای حذف Object |
| `src/engineers_tools/app/engineering_text_editor_patch.py` | EventFilter عمومی برای Text Editorها |

قاعده‌ی درست باید این باشد:

| وضعیت Focus | Ctrl+C/X/V/A | Delete | Backspace |
|---|---|---|---|
| Cursor داخل Text Editor است | روی متن انتخاب‌شده یا Clipboard متن کار کند | متن انتخاب‌شده یا کاراکتر بعدی را پاک کند | کاراکتر قبل از Caret را پاک کند |
| خود Text Box انتخاب شده، ولی داخل تایپ نیست | Object/Box کپی یا حذف شود | خود Text Box حذف شود | خود Text Box حذف شود فقط اگر قانون Canvas این را بخواهد |
| Canvas فعال است و Text Editor فعال نیست | عملیات روی Objectهای انتخاب‌شده | حذف Object | حذف Object یا عمل تعریف‌شده Canvas |

در وضعیت فعلی این مرزها با هم قاطی شده‌اند.

## وضعیت Equation Math

پیاده‌سازی فعلی Word Equation واقعی نیست. الگوی فعلی در `text_toolbar_final_event_safety_patch.py` تقریباً این است:

- Regex روی آخرین token قبل از Space اجرا می‌شود.
- `a^2` به متن با VerticalAlignment تبدیل می‌شود.
- `a_1` به متن با VerticalAlignment تبدیل می‌شود.
- `a/b` به تصویر PNG داخل `QTextEdit` تبدیل می‌شود.

مشکل‌های این روش:

- تصویر داخل Text Editor قابل ویرایش مثل متن نیست.
- Backspace، Selection و Copy/Paste روی تصویر مثل یک کاراکتر عادی رفتار نمی‌کند.
- در RTL، تصویر ممکن است به ابتدای خط یا سمت غلط برود.
- بعد از تبدیل یک عبارت ریاضی، فرمت باید به حالت معمولی برگردد ولی همیشه درست برنمی‌گردد.
- وسط جمله، جای بعدی Caret و متن بعدی دقیقاً مثل Word Math Equation نمی‌شود.
- Fraction باید inline و روی Baseline جمله قرار بگیرد، نه اینکه خط جدا یا سمت چپ بیفتد.

راه درست پیشنهادی:

1. فعلاً درج تصویر برای Fraction حذف شود.
2. Math به عنوان یک مدل ساختاری ذخیره شود، نه فقط HTML خام یا تصویر.
3. ساختار پیشنهادی برای هر قطعه‌ی متن:
   - `plain_text`
   - `rich_span`
   - `math_fraction`
   - `math_power`
   - `math_subscript`
   - `math_symbol`
4. هنگام ویرایش، Text Editor باید بداند کاربر داخل متن عادی است یا داخل Math Span.
5. هنگام Painting روی Canvas، Math renderer جداگانه Baseline، Fraction، Superscript و Subscript را رسم کند.
6. شورتکات `Convert selected text to math` باید در `File > Properties > Shortcut Key` به عنوان Action رسمی اضافه شود.

تا قبل از این بازطراحی، شبیه‌سازی کامل Word Equation پایدار نخواهد شد.

## وضعیت Color / Add Custom Color

| فایل | نقش |
|---|---|
| `modules/mechanics_dynamics_statics/standard_color_dialog.py` | پنجره Add Custom Color مشترک |
| `modules/mechanics_dynamics_statics/text_color_inline_palette_patch.py` | پالت رنگ Inline در Text Bar |
| `modules/mechanics_dynamics_statics/text_color_swatch_patch.py` | Swatchهای رنگ Text |
| `modules/mechanics_dynamics_statics/text_toolbar_final_event_safety_patch.py` | Redirect بعضی فراخوانی‌های رنگ به `standard_color_dialog` |

قانون نهایی Color:

- فقط یک پنجره‌ی Add Custom Color مشترک وجود داشته باشد.
- همه‌ی Text، Bullet، Numbering، Properties و بخش‌های بعدی همان را صدا بزنند.
- Header سرمه‌ای، Logo واقعی، Close استاندارد، دکمه‌های OK/Cancel استاندارد.
- Basic colors و Custom colors باید در Grid منظم و فشرده باشند.
- Pick Screen Color و Add to Custom Colors باید دکمه‌ی استاندارد برنامه باشند.
- مقدارهای Hue/Sat/Val و Red/Green/Blue/HTML باید قابل تایپ دستی و با فلش استاندارد باشند.
- رنگ اول پیش‌فرض باید مشکی باشد و رنگ‌ها تکراری یا خیلی نزدیک نباشند.

## وضعیت Arrow / Combo / SpinBox

الان چند Style جدا برای فلش‌ها وجود دارد و همین باعث شده بعضی جاها مربع یا باکس تودرتو دیده شود.

| فایل | محل تعریف Style فلش |
|---|---|
| `src/engineers_tools/app/theme.py` | File dialog و پایه‌ی Theme |
| `src/engineers_tools/app/runtime_ui_patch.py` | FileTypeCombo و Page Setup |
| `src/engineers_tools/app/interaction_ui_patch.py` | FileTypeCombo و SpinBoxهای Runtime |
| `src/engineers_tools/app/engineering_print_setup_hotfix.py` | Print Setup SpinBox |
| `src/engineers_tools/app/engineering_print_setup_final_patch.py` | Print Setup نهایی |
| `modules/mechanics_dynamics_statics/ui_text_tool_final_patch.py` | Text Bar Combo/Spin اولیه |
| `modules/mechanics_dynamics_statics/ui_text_tool_runtime_fix_patch.py` | Text Bar Combo/Spin Runtime |
| `modules/mechanics_dynamics_statics/text_toolbar_final_event_safety_patch.py` | Text Bar Combo/Spin نهایی |
| `modules/mechanics_dynamics_statics/text_list_settings_final_patch.py` | Bullet/Numbering Spin/Combo |
| `modules/mechanics_dynamics_statics/file_properties_general_patch.py` | Properties General |

قانون پیشنهادی: یک Helper مشترک مثل `style_engineering_combo(combo)` و `style_engineering_spin(spin)` ساخته شود و همه‌ی فایل‌ها از همان استفاده کنند. تا وقتی هر فایل QSS خودش را بسازد، الگو خراب می‌شود.

## وضعیت Font

قانون کاربر:

- متن‌های ثابت برنامه: `Times New Roman Bold Italic` برای انگلیسی.
- متن‌های فارسی ثابت: خانواده‌ی فونت‌های سری B فارسی، Bold، با رعایت طراحی.
- ورودی‌های دستی کاربر: Bold/Italic پیش‌فرض نباشد؛ مگر کاربر فعال کند.
- Text Box جدید: نباید Bold و Italic باشد.
- دکمه Italic باید خودش با I ایتالیک واقعی نمایش داده شود.

فایل‌های مرتبط:

| فایل | نقش |
|---|---|
| `modules/mechanics_dynamics_statics/ui_text_tool_final_patch.py` | لیست Font و Font Combo اولیه Text Bar |
| `modules/mechanics_dynamics_statics/text_toolbar_final_event_safety_patch.py` | اصلاح Font و Bold/Italic پیش‌فرض |
| `modules/mechanics_dynamics_statics/project_dialog_style_cursor_patch.py` | ممکن است Fontهای UI را دوباره تغییر دهد |
| `src/engineers_tools/app/engineering_properties_patch.py` | Fontها و Style در Properties |
| `src/engineers_tools/app/theme.py` | Font عمومی پنجره‌ها و منوها |

## وضعیت Bullet / Numbering / Line Spacing

| بخش | فایل‌های درگیر | مشکل فعلی |
|---|---|---|
| Bullet/Numbering menu | `text_line_math_symbols_patch.py`, `text_list_settings_patch.py`, `text_list_settings_final_patch.py` | خودکارسازی Enter ناپایدار شده، Start numbering درست اعمال نمی‌شود |
| Custom Bullet/Numbering | `text_list_settings_final_patch.py`, `text_toolbar_final_event_safety_patch.py` | Start indent و Distance to text باید ورودی دستی بگیرند؛ Style فلش‌ها یکسان نیست |
| Line spacing | `text_line_math_symbols_patch.py`, `text_toolbar_final_event_safety_patch.py` | Popup باید مثل منوی File باشد، Custom باید در همان popup با radio و مقدار عددی باشد، نه پنجره‌ی جدا |
| Auto list continuation | `text_runtime_performance_editing_patch.py`, `text_toolbar_word_behavior_patch.py` | Enter باید Bullet/Numbering بعدی بسازد؛ اگر None زده شد به متن عادی برگردد |

قانون مورد نیاز برای Bullet/Numbering:

- وقتی Bullet فعال است و Enter زده می‌شود، Bullet بعدی خودکار ساخته شود.
- وقتی Numbering فعال است و Enter زده می‌شود، شماره بعدی ساخته شود.
- `start numbering` باید عدد شروع همان خط را تعیین کند، نه عدد بعدی یا مقدار پیش‌فرض 2.
- اگر کاربر None را بزند، همان خط از حالت Bullet/Numbering خارج شود و ادامه‌ی تایپ متن عادی باشد.
- Start indent یعنی فاصله‌ی خود Bullet/Number از لبه‌ی Text Box.
- Distance to text یعنی فاصله‌ی متن از Bullet/Number.

## File / Open / Save / Export / Page Setup

| فایل | نقش |
|---|---|
| `modules/mechanics_dynamics_statics/file_export_project_fixes.py` | Save/Export/Page Setup و بعضی خروجی‌ها |
| `src/engineers_tools/app/engineering_export_patch.py` | Export Patch عمومی |
| `src/engineers_tools/app/engineering_print_setup_hotfix.py` | Print Setup Hotfix |
| `src/engineers_tools/app/engineering_print_setup_final_patch.py` | Print Setup نهایی |
| `src/engineers_tools/app/engineering_zoom_print_patch.py` | Zoom و Print و بعضی Cursor/Rotate |
| `modules/mechanics_dynamics_statics/page_setup_properties_hotfix.py` | Page Setup properties |
| `modules/mechanics_dynamics_statics/file_properties_general_patch.py` | File > Properties > General |
| `modules/mechanics_dynamics_statics/file_properties_view_final_patch.py` | File > Properties > View و Text Bar visibility |

مواردی که باید دوباره تست شوند:

- ذخیره و بازکردن `.eTools` و `.eTool` باید محتوا، موقعیت، Rotation، Imageها و Textها را برگرداند.
- SVG نباید فقط بلوک سفید ذخیره کند؛ اشیا باید داخل SVG باشند.
- Remove white background باید روی کل محتوای تصویری اعمال شود، نه فقط Page Box.
- DPI خروجی باید واقعاً روی ابعاد خروجی اثر بگذارد.
- Page Setup باید Width/Height را با Paper و Orientation هماهنگ کند.
- Apply در Page Setup باید تا بسته‌شدن برنامه حفظ شود.
- Show Grid در Print Preview باید داخل Preview هم دیده شود.

## File > Properties

| بخش | فایل | وضعیت |
|---|---|---|
| General | `modules/mechanics_dynamics_statics/file_properties_general_patch.py` | عرض پنجره باید کمتر و استانداردتر شود |
| View | `modules/mechanics_dynamics_statics/file_properties_view_final_patch.py` | باید با منوی View همگام باشد؛ اگر Icon در Properties خاموش شد، تیک View هم خاموش شود |
| Shortcut Key | `src/engineers_tools/app/engineering_properties_patch.py` | ظاهر ساده است و باید با الگوی پنجره‌سازی پروژه بازطراحی شود |
| Action جدید Math | `src/engineers_tools/app/engineering_properties_patch.py` | باید Action برای `Convert selected text to math` اضافه شود |

## فهرست فایل‌های مهم در ماژول Engineering

| فایل | گروه |
|---|---|
| `workspace.py` | پایه Canvas و Objectها |
| `module_entry.py` | زنجیره Patchها |
| `ui_text_tool_final_patch.py` | Text Tool پایه |
| `text_toolbar_final_event_safety_patch.py` | Text Keyboard/Math/Color نهایی فعلی |
| `text_line_math_symbols_patch.py` | Math symbols، Line spacing، Bullet/Numbering popup |
| `text_runtime_performance_editing_patch.py` | Performance و Auto list |
| `text_toolbar_word_behavior_patch.py` | رفتار Word-like |
| `text_lag_final_patch.py` | کاهش Lag Text |
| `final_focus_editing_icons_patch.py` | Focus/Edit icons |
| `project_dialog_style_cursor_patch.py` | Style/Cursor/Text patch ترکیبی |
| `standard_color_dialog.py` | Add Custom Color مشترک |
| `text_color_inline_palette_patch.py` | Inline palette |
| `text_color_swatch_patch.py` | Swatches |
| `text_list_settings_patch.py` | List settings اولیه |
| `text_list_settings_final_patch.py` | List settings نهایی |
| `svg_cursor_assets_activation_patch.py` | Cursor SVG mapping |
| `engineering_runtime_audit_final_patch.py` | Cursor redirect و audit |
| `native_cursor_lock_patch.py` | جلوگیری از Cursor native |
| `file_export_project_fixes.py` | Save/Export/Page setup |
| `file_properties_general_patch.py` | Properties General |
| `file_properties_view_final_patch.py` | Properties View |
| `unit_grid_properties_final_patch.py` | Unit/Grid properties |
| `ruler_unit_origin_final_patch.py` | Ruler/Unit/Origin |
| `window_resize_fixes.py` | Window resize مسیر قدیمی |
| `final_interaction_policy_fixes.py` | سیاست تعامل نهایی |
| `interaction_fixes.py` | اصلاح تعامل Canvas |

## تشخیص ریشه‌ای خرابی فعلی

خرابی فعلی از یک خط کد تنها نیست. معماری فعلی چند مشکل هم‌زمان دارد:

1. تعداد Patchهای Text زیاد است و مالک واحد ندارد.
2. بعضی Patchها دوباره اجرا می‌شوند.
3. چند Patch یک Method مشترک را override می‌کنند.
4. بعضی مسیرها رویداد Text را می‌گیرند و بعضی مسیرها همان رویداد را به Canvas می‌دهند.
5. Equation Math به‌جای مدل ساختاری، به تصویر و Rich HTML تکیه کرده است.
6. Styleهای پنجره و منو در چند فایل کپی شده‌اند، پس تغییر یک جا همه‌جا اعمال نمی‌شود.
7. Cursorها هم از SVG مشترک، هم از native Cursor، هم از hand assetهای قدیمی می‌آیند.

## پیشنهاد اصلاح مرحله‌ای

### مرحله 1: تثبیت فوری Text

- آخرین تغییرهای پرریسک در `text_toolbar_final_event_safety_patch.py` موقتاً کوچک شود.
- `QTextEdit` باید دوباره Native Backspace/Copy/Paste/Delete را خودش انجام دهد.
- Canvas فقط وقتی Delete/Backspace را بگیرد که هیچ Text Editor فعالی وجود ندارد.
- فقط یک فایل مالک `_CanvasTextEdit` باشد: پیشنهاد `ui_text_tool_final_patch.py`.

### مرحله 2: پاکسازی زنجیره‌ی Patchهای Text

- همه‌ی key handlerها به یک TextController منتقل شوند.
- `text_line_math_symbols_patch.py` فقط UI منوها و Actionها را بسازد، نه اینکه Keyboard را بگیرد.
- `text_runtime_performance_editing_patch.py` فقط Performance و Auto list را انجام دهد و مستقیماً `keyPressEvent` را override نکند.
- `project_dialog_style_cursor_patch.py` نباید دوباره Text Keyboard را تغییر دهد.

### مرحله 3: Math واقعی

- درج تصویر PNG برای Fraction حذف شود.
- مدل Math token ساخته شود.
- Renderer جدا برای Math روی Canvas ساخته شود.
- Editor برای Math یا از Inline Object قابل کنترل استفاده کند یا Convert فقط بعد از خروج از Editor روی Object model اعمال شود.
- تبدیل خودکار فقط وقتی رخ دهد که عبارت کامل شده و Caret باید به حالت Normal برگردد.

### مرحله 4: Style System واحد

- برای منوهای بازشونده یک Helper مشترک ساخته شود.
- برای پنجره‌های اصلی یک Helper مشترک ساخته شود.
- برای Combo/Spin فلش‌ها یک Helper مشترک ساخته شود.
- برای Buttonها، Close، OK، Cancel، Add، Pick Screen یک Helper مشترک ساخته شود.
- همه فایل‌ها از این Helperها استفاده کنند و QSS تکراری حذف شود.

### مرحله 5: تست‌های ضروری

چک‌لیست تست بعد از اصلاح:

- Text Box جدید Bold/Italic نباشد.
- Bold و Italic فقط با دکمه فعال شوند.
- Ctrl+A/C/X/V داخل Text Editor روی متن کار کند.
- Delete داخل Text Editor روی متن کار کند.
- Backspace داخل Text Editor کاراکتر قبل از Caret را پاک کند؛ فارسی و انگلیسی.
- Delete/Backspace وقتی خود Text Box انتخاب است، فقط طبق قانون Object عمل کند.
- Bullet با Enter ادامه پیدا کند.
- Numbering با Enter ادامه پیدا کند و از `start numbering` شروع شود.
- None در Bullet/Numbering متن را عادی کند.
- `a^2` داخل جمله به توان تبدیل شود و بعد از آن متن عادی ادامه پیدا کند.
- `a_1` داخل جمله به اندیس تبدیل شود و بعد از آن متن عادی ادامه پیدا کند.
- `a/b` به Fraction inline روی Baseline تبدیل شود و به چپ/خط جدا نپرد.
- Copy/Paste متن Math رفتار پایدار داشته باشد.
- منوی File و منوهای Text از یک الگوی گرد و بدون زمینه‌ی تیز استفاده کنند.
- Cursor Move/Rotate/Resize دیگر به دست یا Cursor native ویندوز برنگردد.

## توصیه برای چت موازی

برای کسی که از این گزارش ادامه می‌دهد:

1. اول `module_entry.py` را بخواند و ترتیب Patchها را بفهمد.
2. سپس فقط روی Text این فایل‌ها را بررسی کند:
   - `ui_text_tool_final_patch.py`
   - `text_toolbar_final_event_safety_patch.py`
   - `text_line_math_symbols_patch.py`
   - `text_runtime_performance_editing_patch.py`
   - `project_dialog_style_cursor_patch.py`
   - `src/engineers_tools/app/engineering_text_editor_patch.py`
3. قبل از اضافه‌کردن هر Patch جدید، مشخص کند مالک نهایی `QTextEdit` کیست.
4. اگر برنامه بعد از آخرین اصلاح خراب‌تر شده، اولین نقطه‌ی برگشت محتمل `text_toolbar_final_event_safety_patch.py` است.
5. برای Math از تصویر داخل Text Editor استفاده نکند؛ این روش علت اصلی بدرفتاری با Caret و RTL است.
6. برای UI، Styleها را از `theme.py` و منوی File بگیرد، نه با QSS جدید پراکنده.

## جمع‌بندی

مشکل فعلی از کمبود جزئیات طراحی نیست؛ مشکل این است که هر بار بخشی از طراحی با یک Patch جدید روی Patchهای قبلی سوار شده و مالکیت نهایی بخش‌ها مشخص نیست. برای اینکه زحمت‌های قبلی حفظ شود، باید اول معماری Text و Style مشترک تثبیت شود، بعد دوباره به سراغ جزئیات زیبایی، Math Equation، Color و Properties برویم.

</div>
