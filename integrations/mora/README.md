# Mora integration

This directory describes OPlague as an optional application in a future native Mora launcher.

## Manifest

\`manifest.json\` follows the DuckOS Mora application manifest v1.0.0 contract and references the existing \`oplague_app.py\` implementation entry point through Python 3.

The manifest is a **registration declaration only**. It does not create an active OS launcher, change OPlague's read-only design, request device permissions or execute driver packages. The current browser-based Mora shell cannot start local processes.

The declared UI can inspect saved data on supported Python/Tkinter platforms. Full live Plug and Play inventory depends on Windows and PowerShell; that restriction remains part of OPlague's own contract.

## Local launch

From the repository root:

\`\`\`sh
python oplague_app.py
\`\`\`

The repository also exposes the correctly spelled \`oplague_app.py\` entry point which delegates to the existing implementation module.

## Security boundary

A native launcher must validate this manifest, resolve the entry point within a trusted OPlague installation, invoke a known Python runtime directly, avoid shell interpolation and ask for explicit first-launch approval. OPlague remains read-only: Mora must not add driver installation or package execution behavior.

Project: [Ivan-VHS/OPlague](https://github.com/Ivan-VHS/OPlague). Project author/developer: Ivan-VHS.