# Market development, positioning and commercialization standard

## Purpose and boundary

This standard turns market, commercial, advertising, branding, distribution and customer vocabulary into an evidence-led product practice. It is a planning and governance layer, not a claim that demand, revenue, conversion, market share or profitability has been achieved.

The project-specific source of truth is `market-development.v1.json`, validated against `schemas/market-development.v1.schema.json`. It records intended audiences, product promise, differentiators, go-to-market stages, promotion channels, commercial gates and measurement policy. **Implemented** requires a real repository artifact or existing channel; **planned** is an intention; **not_assessed** means evidence has not been collected.

## Market and customer operating model

1. **Discover the job, not just the demographic.** Describe the user's task, current workaround, friction and desired outcome. Separate users, evaluators, buyers and maintainers when they differ.
2. **Position from verifiable behaviour.** State the category, primary use case, concrete benefit and evidence. Keep technical proof separate from future roadmap.
3. **Package a clear offer.** Explain what is included, supported platforms, prerequisites, limitations, license and the first successful workflow.
4. **Promote through relevant channels.** Prefer technical documentation, reproducible demonstrations, release notes, specialist communities and user-requested updates. Advertising must be factual, proportionate and attributable.
5. **Close the feedback loop.** Convert issues, support questions and structured feedback into prioritized product work. Do not infer broad demand from a handful of comments.
6. **Gate commercialization.** Pricing, paid distribution and monetization remain unset until demand, legal rights, operating cost, support obligations and license compatibility have been reviewed.

## Vocabulary-to-control crosswalk

Repeated vocabulary clusters are consolidated into 20 operational controls; repeated terms do not create duplicate requirements.

| # | Vocabulary cluster | Operational control |
|---:|---|---|
| 1 | Маркетизация · Рыночное · Маркетинг | Define the market, category and user problem before choosing promotional tactics. |
| 2 | Коммерциализация · Коммерческое · Продвижение | Turn verified product value into a clearly scoped offer and release path. |
| 3 | Рыночнизация · Рекламное · Рекламирование | Use audience-relevant, factual promotion with claims tied to evidence. |
| 4 | Продвижение · Продвиженческое · Продвиженчество | Maintain a measurable discovery-to-first-success journey. |
| 5 | Рекламизация · Сбытовое · Рыночное продвижение | Align launch messages, release notes and distribution pages. |
| 6 | Брендизация · Предпринимательское · Коммерциализация | Express a consistent product promise and defensible reason to choose it. |
| 7 | Товаризация · Торговое · Брендинг | Package features, formats, prerequisites, license and limitations as one coherent offer. |
| 8 | Монетизация · Брендинговое · Позиционирование | Keep monetization separate from positioning; do not set prices without evidence. |
| 9 | Коммерциализирование · Клиентское · Медиапродвижение | Publish useful, audience-specific media and technical explanations. |
| 10 | Рыночное освоение · Потребительское · Рекламная деятельность | Validate needs through observed workflows and consent-based feedback. |
| 11 | Предприниматизация · Конъюнктурное · Рыночная деятельность | Review relevant market changes without chasing unsupported trends. |
| 12 | Сбытовая интеграция · Дистрибуционное · Предпринимательство | Make installation, release retrieval and first use explicit and reproducible. |
| 13 | Позиционирование · Товарное · Сбытовая деятельность | Keep category, product promise and user journey consistent. |
| 14 | Популяризация · Экономическое · Товаропродвижение | Demonstrate value with examples, previews and reproducible outcomes. |
| 15 | Клиентизация · Финансовое · Клиентопривлечение | Reduce onboarding friction and distinguish users, evaluators and purchasers. |
| 16 | Промоизация · Коммуникационное · Популяризация | Use a consistent editorial voice across documentation, releases and community posts. |
| 17 | Дистрибутизация · Позиционирующее · Монетизация | Measure distribution separately from paid conversion and revenue. |
| 18 | Рыночная адаптация · Коммерциализационное · Коммерческое развитие | Update the offer and roadmap from evidence, not assumptions. |
| 19 | Коммерческое развитие · Рыночно-ориентированное · Рыночное освоение | Prioritize changes by user value, feasibility, risk and maintenance cost. |
| 20 | Маркетинговая интеграция · Промоциональное · Маркетинговая стратегия | Keep messages, release artifacts and project boundaries aligned across the federation. |

## Minimum go-to-market sequence

- **Discover:** record the user segment, job, alternatives and evidence gaps.
- **Validate:** observe real workflows; record feedback with context and date.
- **Explain:** publish a concise value proposition, supported capabilities and non-claims.
- **Distribute:** provide a traceable release/source path, prerequisites and license notices.
- **Retain:** maintain a support route, compatibility notes, changelog and issue triage.
- **Review:** revisit positioning and priorities when new evidence materially changes the picture.

## Measurement and ethical promotion

Use only metrics with an explicit definition and reliable source. Repository views, release downloads, successful setup, first completed task, repeat use, issue resolution and conversion are different measures. Mark unavailable measures as **not_assessed**.

Do not add hidden telemetry, fingerprinting, undisclosed tracking, misleading urgency, fake testimonials, fabricated compatibility claims or unverified performance comparisons. Any future in-product analytics must be documented, proportionate, privacy-reviewed and user-controlled. Do not repurpose user feedback as a testimonial without permission.

## Commercial release gates

- **Market validation:** observed target-user workflows and documented feedback.
- **Pricing:** a reviewed model supported by willingness-to-pay evidence; otherwise keep it unset.
- **Unit economics:** measured development, packaging, hosting, distribution and support costs.
- **Licensing and rights:** manual review of dependencies, source assets, trademarks and redistribution terms.
- **Support:** named ownership, issue intake, supported-platform policy and maintenance lifecycle.
- **Distribution:** reproducible artifacts, integrity information, release notes and clear use instructions.

A gate is not passed merely because the repository contains a plan or profile file.

## Federation rule

Shared terminology and document structure may be reused across Pytyliki, Reaper, OPlague and VentuSample. Audience, positioning, evidence, product claims and commercial gates remain project-specific. Cross-promotion must not imply technical integration, compatibility or shared support where repository contracts do not establish it.


## Project-specific application: OPlague

### Product position
A Windows-first workbench for hardware inventory, driver-package inspection, integrity evidence and structured diagnostic reports; it does not install or modify drivers.

**Primary audiences**
- **IT support technicians and system administrators:** Inspect hardware and driver packages while retaining a clear evidence trail. Value: A read-only workflow for inventory, package review and diagnostic reporting.
- **Computer repair and maintenance services:** Understand device identity and package metadata before separate administrative action. Value: Structured evidence without automated installation or destructive changes.
- **Driver packagers and hardware QA teams:** Review package structure, hashes and declared metadata under resource limits. Value: Bounded inspection and deterministic report composition.

**Positioning statement:** OPlague is a read-only Windows workbench for inspecting hardware identity and driver-package evidence before any separate maintenance action.

**Proof points**
- Read-only Windows Plug and Play inventory.
- Bounded INF, ZIP and UDRV package inspection without payload execution.
- Evidence-linked reports and normalized device snapshots.

**Claims to avoid**
- OPlague does not install, update, remove or modify drivers.
- Inspection results are not a guarantee of device compatibility or a certified driver recommendation.
- Market demand, paid conversion and profitability are not established.

### Current promotion and validation posture
- **GitHub repository and Windows release information — implemented:** Explain read-only capabilities, supported package inputs and safety boundaries. Guardrail: Never advertise automated driver updates or universal compatibility.
- **Technical walkthroughs — planned:** Demonstrate inventory, package inspection and evidence reports. Guardrail: Use sanitized examples; do not expose device identifiers or personal machine data.
- **IT support and repair communities — planned:** Collect real operator workflows and usability feedback. Guardrail: No unsupported repair guarantees or aggressive promotion.
- **Release notes and compatibility matrix — planned:** Make supported Windows versions and tested formats discoverable. Guardrail: List exact tested versions and keep unknown combinations explicit.

**Brand promise:** Make hardware and driver-package inspection safer, clearer and evidence-led.

**Voice:** cautious, precise, operator-focused, transparent.

**Message pillars:** Read-only inspection; Evidence before recommendation; Bounded untrusted-input handling; Explicit compatibility limits.

## Adoption checklist

- [ ] Confirm audience and problem statements using dated, observed feedback.
- [ ] Verify every proof point against current source, tests, contracts or release artifacts.
- [ ] Publish one reproducible end-to-end demonstration for the primary user journey.
- [ ] Review license, third-party assets, rights and distribution requirements.
- [ ] Define supported platforms, support ownership and maintenance commitments.
- [ ] Reassess pricing and unit economics only after validation evidence exists.
