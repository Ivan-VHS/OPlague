# Mora integration · OPlague

OPlague adopts the shared Mora brand/action tokens in its native Tk/ttk theme adapter. The light and dark system-following palettes keep their established semantic backgrounds and high-contrast product controls; primary actions, progress indicators and focus language use the shared Mora violet/teal accents.

The white-blue-red device/driver meaning is retained in semantic data and danger states. Existing accessibility checks, system theme detection, persisted preference format, DPI awareness and Reduce Motion / Eco Visuals controls remain intact.

The token mirror is stored in `mora/theme.json`; the native adapter is `ui_theme.py`.

## Implementation map

| Surface | Mora behavior |
|---|---|
| Page and cards | retain OPlague light/dark surface semantics |
| Primary actions | shared violet brand and on-brand text |
| Progress indicators | shared violet brand |
| Focus and secondary actions | shared teal accent |
| Device and package meaning | keep OPlague semantic blue/red states |
| Motion | preserve Reduce Motion and Eco Visuals |

Mora is applied through Tk/ttk. The application remains a native inspector; its package-reading, compatibility evidence and read-only safety boundaries are unchanged.
