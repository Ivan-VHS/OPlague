# Cross-repository plugin federation

OPlague adds a Python 3.10+ host for the shared 18-plugin catalog. Its adapters provide bounded, read-only inspection, validation, static analysis and dry-run planning.

## Use from Python

\`\`\`python
from oplague.plugins import PluginManager

host = PluginManager()
plugins = host.list_plugins()
inventory = host.run("Pyemont", path=".")
plan = host.run("Dropaul", steps=[
    {"id": "scan", "depends_on": []},
    {"id": "review", "depends_on": ["scan"]},
])
\`\`\`

Use a stable ID such as \`keel-koh\` or the display name \`Keel Koh\`. Plugins can be enabled or disabled per manager instance with \`set_enabled(name, bool)\`. A disabled plugin cannot dispatch.

## Included operations

Operandu inspects typed values; Dropaul and Prossee produce deterministic DAG/critical-path dry-runs; Zdoro and Profe inspect repository baselines; Pyemont inventories files; Dilly checks token sets; Baplap produces bounded SHA-256 file indexes; Sretuo discovers tests; Kali scans static secret patterns; Zalam checks simple versioned contract lists; Liur measures on-disk file sizes; Keel Koh indexes local Markdown headings/links; Vorof parses Python AST structure; Vprof reports AST shape estimates; Vprossee checks evidence paths; Professiya derives learning paths from local docs; Profevo creates semantic-version migration plans.

## Safety boundary

These are local adapters, not an unrestricted plugin loader. They do not execute inspected project code, run shell commands, install drivers, access the network or modify the inspected workspace. File indexing is limited to 5,000 files, 2 MiB per file and 50 MiB total indexed content. Kali is a bounded static pattern scan, not a complete security audit; Vprof reports AST estimates, not runtime profiling; Vprossee checks source existence, not the truth of claims.

## Compatibility

The shared catalog and host declarations are in \`federation/plugins/\`. Catalog schema: \`schemas/ivan-vhs.plugin-catalog.v1.schema.json\`. Host contract: \`ivan-vhs.plugin-host.v1\`, API version 1.
