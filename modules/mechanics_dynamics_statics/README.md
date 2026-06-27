# Engineering Design Tools

این پوشه مسیر فعال فعلی پروژه است. لانچر فقط باید از این entry point وارد محیط طراحی مهندسی شود:

```text
modules.mechanics_dynamics_statics.module_entry:create_window
```

فایل فعال پنجره:

```text
modules/mechanics_dynamics_statics/workspace.py
```

## محدوده فعلی

- Statics
- Dynamics
- Robotics
- Vector drawing
- Engineering drawing canvas

## قانون توسعه

- تغییرات این محیط باید روی `workspace.py` و کلاس `EngineeringDesignWorkspace` ادامه پیدا کند.
- پنجره مادر از `src/engineers_tools/app/module_window.py` می‌آید.
- Start Bar به‌صورت جدا در مسیر زیر تعریف شده است:

```text
src/engineers_tools/ui/start_bar.py
```

- اگر ابزارهای Engineering Design Tools با بقیه ماژول‌ها فرق داشت، در `EngineeringDesignWorkspace` متد `get_start_bar_tools()` override شود.
- خود پنجره مادر برای تغییر ابزارهای Start Bar دستکاری نشود مگر اینکه ساختار عمومی کل پروژه تغییر کند.
- هر ابزار جدید باید Properties خودش را در `properties_schema` تعریف کند.
- هر گزینه Select باید از یک الگوی واحد انتخاب، highlight و اتصال به Properties استفاده کند.
- عنوان اضافه داخل Canvas حذف شده است؛ Canvas باید فضای کاری تمیز و مستقیم باشد.
