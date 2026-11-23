# Katyuhen integration — OPlague

## Role in the ecosystem

OPlague is Katyuhen's read-only device and driver evidence workbench. It owns Windows PnP inventory, bounded INF/ZIP/PE inspection, normalized hardware identifiers, package metadata and evidence reports.

## Registered interfaces

| Interface | Direction | State | Boundary |
|---|---|---|---|
| OPlague device snapshot v1 | Provides | Specified | Versioned read-only JSON; explicit local exchange |
| Pytyliki C ABI v1 | Optional consumer | Specified | Explicit trusted library path; no implicit DLL/SO search |

## Integration rules

- Preserve the inspection-only model. A registry entry must never become an installation or driver mutation path.
- Hardware-ID matches remain candidates; they do not prove publisher trust, OS compatibility or safe installation.
- Keep PE/COFF inspection separate from loading, executing or authenticating an image.
- Export only bounded, versioned evidence. Consumers must validate schema, version, bounds and provenance.
- OPlague must remain fully usable without Reaper, Pytyliki or network access.

## Workspace and visual identity

Mora is the ecosystem's desktop entry point. OPlague keeps its specialist workbench and evidence-first layout while native UI adapters can map semantic roles to DuckOS's `mora.theme.v1` tokens locally.

The Katyuhen registry is maintained in [DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/ecosystem/katyuhen.v1.json). The local declaration is [integrations/katyuhen/manifest.json](../integrations/katyuhen/manifest.json).

## Validation

Run OPlague's Windows desktop build and read-only inspection tests. Do not mark driver installation, payload extraction or device mutation as supported.
