# OPlague — UI/UX Profile — Stage 0.5

**Stage convention:** [Product Stage Naming Standard](https://github.com/Ivan-VHS/DAK/blob/main/docs/STAGE_NAMING_STANDARD.md).  
**Shared standard:** [DAK UI/UX Foundation — Stage 0.1](https://github.com/Ivan-VHS/DAK/blob/main/docs/UI_UX_STAGE_0_1.md).

This file keeps only the OPlague workbench toolkit notes and implementation boundaries. The shared specification owns common interaction rules, accessibility budgets, theme/component contracts and the definition of done.

### OPlague — локальная реализация

- Инвентаризация, совместимость и доказательства остаются read-only по умолчанию; внешний вид не должен создавать впечатление, что драйвер уже установлен/изменён.
- Для отчётов, INF/архивов, хэшей и сведений устройства сохраняются моноширинные идентификаторы, копирование, время проверки и источник доказательства.
- Theme tokens проверяются на контраст, а статусы scan/compatible/warning/error различаются текстом и семантическим токеном.
- Motion никогда не задерживает перечисление устройств, хэширование, проверку границ архивов, построение отчёта и driver inspection.
- Никакой автоматический «ремонт» или изменение драйвера не запускается как визуальная реакция; последствия и ручное подтверждение остаются явными.
