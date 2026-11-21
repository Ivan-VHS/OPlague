# Quality, execution and commercial readiness

## Scope

OPlague is a Windows-first, read-only hardware and driver-package diagnostic workbench. The matrix applies the supplied 20 triplets to product quality, operational controls and commercial governance.

## 20 × 3 control matrix

| # | Quality | Execution | Commercial | Acceptance intent |
|---:|---|---|---|---|
| 1 | Качественность | Качество | Коммерческий | Каждый диагностический вывод должен иметь критерий приёмки и проверяемые исходные данные. |
| 2 | Добротность | Добротность | Торговый | Сохранность, ограничения ресурсов и предсказуемая обработка ошибок обязательны. |
| 3 | Безупречность | Безупречность | Предпринимательский | Импортируемые пакеты и идентификаторы рассматриваются как недоверенный ввод. |
| 4 | Совершенство | Совершенство | Рыночный | Сборки, отчёты и релизы воспроизводимы и регрессионно проверяемы. |
| 5 | Цельность | Мастерство | Деловой | Инвентаризация, анализ, отчётность и интерфейс образуют цельный рабочий процесс. |
| 6 | Целостность | Профессионализм | Финансовый | Доверие обеспечивают provenance, псевдонимизация и явные границы полномочий. |
| 7 | Монолитность | Надёжность | Прибыльный | Пакетные операции и инспекция сохраняют ограничения по объёму и времени. |
| 8 | Согласованность | Основательность | Доходный | Рекомендации опираются на точные совпадения и документированные доказательства. |
| 9 | Последовательность | Гармоничность | Экономический | Повторные проверки дают детерминированные результаты и отслеживаемые метрики. |
| 10 | Системность | Согласованность | Хозяйственный | Политики импорта, доступа, экспорта и хранения согласованы. |
| 11 | Структурированность | Цельность | Бизнесовый | Форматы INF, UDRV, snapshot и inspection bundle имеют версионированные контракты. |
| 12 | Упорядоченность | Целостность | Маркетинговый | Интерфейс и материалы ясно объясняют операторскую ценность и безопасные сценарии. |
| 13 | Непротиворечивость | Монолитность | Клиентский | Отчёты, документация, схемы и фактическое поведение не противоречат друг другу. |
| 14 | Однородность | Нераздельность | Сбытовой | Путь от обнаружения устройства до аудируемого отчёта последователен. |
| 15 | Унификация | Единство | Промышленный | Интеграции и экспорт используют ограниченные и стабильные форматы. |
| 16 | Стандартизация | Слаженность | Корпоративный | Выпуски desktop-приложения и изменения проходят автоматические проверки. |
| 17 | Полнота | Ритмичность | Инвестиционный | Доказательства позволяют провести независимую техническую и правовую проверку пакета. |
| 18 | Точность | Размеренность | Монетизируемый | Монетизация требует подтверждённого спроса, допустимых прав и прозрачного ценообразования. |
| 19 | Выверенность | Синхронность | Рентабельный | Доходность требует измерения разработки, сопровождения и поддержки. |
| 20 | Профессионализм | Упорядоченность | Капитализированный | Код, отчёты, лицензии и релизные активы должны оставаться прослеживаемыми. |

## Evaluation

The root profile **quality-commercial.v1.json** records 60 controls. Run **python tools/quality_commercial.py** or add **--format json**. CI runs the evaluator and its regression tests. Maturity states are **implemented** (declared and artifact-linked), **planned** (25% credit), **not_assessed** (zero credit) and **not_applicable** (excluded). The evaluator checks structure and file presence only; it does not run tests, install drivers or certify compatibility.

## Commercial gates

- Market validation: not assessed; gather actual operator and IT-support workflow evidence.
- Pricing: not set; no price or willingness-to-pay is inferred.
- Unit economics: not assessed; measure packaging, maintenance and support costs.
- Licensing: manual review required, including bundled dependencies and third-party notices.
- Support: planned; define supported Windows versions, triage and maintenance lifecycle.
- Distribution: Windows desktop packaging and release workflow exist; distribution is not proof of paid demand.

## Product and safety boundaries

OPlague remains read-only. Driver packages are untrusted input and are not executed or installed. Exact normalized hardware-ID matches are evidence for operator review, not a compatibility verdict or driver ranking. SHA-256 establishes byte integrity, not publisher identity or safety. Device identifiers remain subject to the existing HMAC-pseudonymization and consent controls.

Commercial claims require separate customer, financial, licensing and support evidence. No automatic control state represents profit, revenue, return on investment or compatibility certification.


## Operational cohesion and prioritized next steps

The second axis (**Execution**) measures the cohesion of the end-to-end operating model: consistent module ownership, bounded workflows, aligned interfaces, reproducible release steps and synchronized documentation. “Monolithic” means a consistent product journey and a single source of truth; it does not mean collapsing independent modules into one source file or removing project boundaries.

The evaluator now emits a prioritized action plan derived from the declared commercial controls:

| Priority | Required next step | Acceptance evidence |
|---|---|---|
| P0 | Complete license and third-party rights review | License compatibility, notices, bundled dependencies and asset permissions are reviewed before commercial redistribution claims. |
| P1 | Define support ownership and release delivery | Maintenance owner, supported versions, issue route, release artifacts and reproducible installation are documented; no SLA is implied. |
| P2 | Validate user demand and unit economics | Actual user workflows and delivery/support costs are recorded before market-fit or margin claims. |
| P3 | Consider pricing only after evidence | User value, rights, operating costs and support scope are assessed; no willingness-to-pay is invented. |

Run `python tools/quality_commercial.py` for the text report or `python tools/quality_commercial.py --format json` for structured output. The action plan is advisory; declared statuses do not prove sales, revenue, profitability or investment readiness.
