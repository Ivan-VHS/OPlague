# Improvement, dissonance, and conflict resolution

## Purpose and scope

This contract turns the supplied 20 triplets into a repeatable engineering improvement process for **OPlague**, a Windows-first, read-only workbench for device inventory and driver-package diagnostics.

It complements the existing quality and commercial-readiness controls. It does not replace security review, package-format specifications, CI, or operator judgment.

## The 20-control vocabulary

| # | Improvement outcome | Dissonance signal | Conflict pattern | Acceptance intent |
|---:|---|---|---|---|
| 1 | Совершенствование | Дисгармония | Конфликты | Align acceptance criteria and observed outcomes. |
| 2 | Преображение | Разлад | Противоречия | Restore reliability when recovery, state, or error handling is inconsistent. |
| 3 | Оптимизация | Несозвучие | Столкновения | Close unsafe or ambiguous input and permission paths. |
| 4 | Модернизация | Дисбаланс | Несовместимости | Modernize stale interfaces without breaking supported consumers. |
| 5 | Улучшение | Диспропорция | Разногласия | Prioritize high-value work and remove accidental complexity. |
| 6 | Развитие | Несогласованность | Расхождения | Align modules and dependencies around clear ownership. |
| 7 | Преимущественное развитие | Разноречие | Коллизии | Direct effort toward the project's primary outcomes. |
| 8 | Усовершенствование | Противоречивость | Споры | Make disputed design decisions explicit and evidence-led. |
| 9 | Реконструкция | Какофония | Несогласованности | Rebuild fragile structures at a stable boundary when local patches accumulate. |
| 10 | Рефакторинг | Дискретность | Противоборства | Refactor for clarity while preserving externally observable behavior. |
| 11 | Переосмысление | Разобщённость | Соперничества | Re-evaluate assumptions when the current design no longer serves supported workflows. |
| 12 | Обновление | Неоднородность | Раздвоения | Keep versions, schemas, documentation, and configuration synchronized. |
| 13 | Преобразование | Несоответствие | Пересечения | Transform data and workflows without losing provenance or meaning. |
| 14 | Обогащение | Расхождение | Накладки | Combine complementary capabilities without hidden coupling. |
| 15 | Усиление | Разноголосица | Неувязки | Strengthen weak points revealed by repeated failures. |
| 16 | Доработка | Дисгармоничность | Диссонансы | Finish edge cases before marking a capability complete. |
| 17 | Возвышение | Конфликтность | Антагонизмы | Improve clarity and accessibility without changing task semantics. |
| 18 | Прогрессирование | Неслаженность | Несоответствия | Tune performance and precision using measured evidence. |
| 19 | Эволюционирование | Раздвоенность | Разобщённости | Evolve architecture incrementally while retaining supported compatibility. |
| 20 | Комплексное совершенствование | Поляризация | Раздоры | Review emergent issues across modules, builds, tests, security, documentation, and repositories. |

The first column names the intended positive change. The second names a symptom that warrants investigation. The third names a possible conflict class. These terms are diagnostic vocabulary, not findings: a word in the registry does not prove that a defect exists.

## Resolution lifecycle

1. **Detect:** record the affected device/provider/package/report, source digest, environment, expected result, actual result, and a reproducible example.
2. **Reproduce:** reduce the report to a bounded test using synthetic or explicitly selected input.
3. **Confirm the root cause:** distinguish a true data or contract conflict from missing evidence, non-matching identifiers, or unsupported platform capability.
4. **Remediate:** make the smallest coherent change that preserves provenance, privacy, resource bounds, and the read-only product boundary.
5. **Verify:** add regression coverage, run package/path and platform checks, and compare documentation with actual report behavior.
6. **Promote:** use a reviewable branch and pull request. Do not force-push over protected work, bypass required checks, or silently merge unresolved conflicts.

## Priority and acceptance

- **P0:** unintended device/driver writes, package execution, privacy exposure, path traversal, or unbounded resource use; block release until contained.
- **P1:** incorrect diagnostics, corrupted evidence, or broken package/report contracts; fix before promotion.
- **P2:** build, integration, repeatability, or significant operator-workflow regressions; fix or document an evidence-backed deferral.
- **P3:** clarity, maintainability, and non-blocking usability improvements; schedule with an owner and acceptance criteria.

A control may move to `detected`, `root_cause_confirmed`, `remediated`, `verified`, or `deferred`. Any assessed state must include repository-relative evidence. `verified` requires evidence that exists in the repository. A deferral requires a concise reason in the profile's `note` field. Never label an item verified solely because a branch or PR exists.

## Project-specific non-negotiables

- Device inventory, package inspection, and compatibility analysis remain read-only; the tool does not install, modify, load, or execute drivers.
- Imported INF, ZIP, and UDRV content is untrusted input and must retain existing path, size, and digest validation.
- Exact normalized hardware-ID matches are evidence for operator review, not a compatibility verdict or driver ranking.
- Device identifiers and exported reports retain existing pseudonymization, privacy, and consent requirements.
- A proposed shortcut that removes one of these safeguards is a P0 conflict, not an optimization.

## Validation

The versioned profile is `improvement-conflict.v1.json`; its structure is described by `schemas/improvement-conflict.v1.schema.json`.

```bash
python -m unittest discover -s tests -p test_improvement_conflict.py -v
python tools/improvement_conflict.py
python tools/improvement_conflict.py --format json
```

The validator checks the exact 20 triplets, identifiers, required remediation and verification fields, lifecycle states, and repository-relative evidence paths. It validates the governance register; it is **not** a static source-code conflict scanner and does not claim that unassessed controls have been resolved.
