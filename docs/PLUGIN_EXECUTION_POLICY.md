# Plugin execution policy and operational health

OPlague keeps its 18 built-in plugins as explicit, standard-library Python
adapters. The Java framework comparison is applied at the contract level:
dependency injection is explicit, dispatch is allowlisted, and runtime policy
is owned by the host rather than hidden in the plugin.

## Added host policy

`PluginExecutionPolicy` configures:

| Parameter | Default | Bound |
|---|---:|---:|
| `max_input_bytes` | 4 MiB | 1 B–64 MiB |
| `max_output_bytes` | 8 MiB | 1 B–128 MiB |
| `max_runtime_ms` | 30,000 ms | 1 ms–10 min |
| `max_concurrent_per_plugin` | 4 | 1–64 |

The host checks finite JSON-compatible arguments/results, admits only a bounded
number of concurrent invocations per plugin, rejects excess input/output and
records invocation counts, failures, in-flight work and observed durations.

`PluginManager.health()` returns `oplage.plugin-health.v1` with liveness,
readiness, plugin state, policy parameters and per-plugin metrics. Readiness
means the reviewed built-in handler registry is complete; it is not a live
Windows device-health verdict.

## Runtime and safety boundary

Python synchronous handlers cannot safely be forcefully interrupted by this
manager. `max_runtime_ms` is therefore an observed deadline: a result that
returns late is rejected and measured, but the handler is not pre-empted while
it is running. A future hard deadline requires cooperative cancellation or
isolated worker processes with bounded IPC and cleanup.

All built-ins remain static/read-only adapters. No plugin loads arbitrary
Python modules, installs drivers, invokes a shell, writes hardware state or
turns this workbench into a remote service.

## Java framework crosswalk

| Framework capability | OPlague implementation |
|---|---|
| Spring IoC / DI | Explicit plugin specs, handler table and host-owned manager policy |
| Spring Boot Actuator | In-process health/readiness snapshot and per-plugin invocation metrics |
| Quarkus / Micronaut build-time checks | Bounded manifest/source inspection and validation before dispatch |
| Jakarta/MicroProfile contracts | Stable plugin IDs, versioned JSON evidence and C ABI adapter boundaries |
| Resilience4j bulkhead | Per-plugin bounded semaphore admission |
| Resilience4j timeout | Observed post-return deadline; not hard cancellation |
| OpenTelemetry | Duration and correlation metrics are available as local data; no OTLP exporter is claimed |
| Hibernate / jOOQ / MyBatis | Not applicable: local evidence JSON, no database persistence layer |
| Camel / Kafka / Flink | Not applicable to the current offline, user-initiated inspection workflow |

## Verification

The regression suite covers input/output budgets, disabled-plugin rejection,
concurrency saturation and health metrics. Run:

```sh
python -m unittest tests.test_plugins -v
python -m unittest discover -s tests -v
```

These tests are added in the adaptation branch; they must pass in CI before
this change is merged.
