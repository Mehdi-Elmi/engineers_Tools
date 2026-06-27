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
- ابزارهای Start Bar باید طبق قانون مشترک پروژه اضافه شوند.
- هر ابزار جدید باید Properties خودش را در پنل Properties تعریف کند.
- هر گزینه Select باید از یک الگوی واحد انتخاب، highlight و اتصال به Properties استفاده کند.
