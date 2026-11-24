# Windows release distribution

## Release workflow

The Windows x64 executable is packaged by `.github/workflows/desktop-build.yml` when a `v*` tag is pushed. The build job compiles and tests the Windows application, prepares `OPlague-windows-x64.zip`, and writes a SHA-256 sidecar. The publication job downloads both files, verifies the checksum with `sha256sum --check`, and creates only a **draft** GitHub Release.

The release job uses the GitHub Environment `release-review`. Repository administrators must configure required reviewers for this environment in GitHub Settings before this can be treated as an enforced approval gate. The workflow does not claim that environment settings have already been configured. A maintainer must inspect and manually publish the draft.

## Integrity and product boundary

The SHA-256 sidecar detects byte changes relative to the recorded digest; it is not a digital signature and does not authenticate the publisher. This workflow does not claim Authenticode signing, certified SBOM provenance or a deployment service.

OPlague remains a local, read-only Windows device/package inspection tool. The release workflow does not install drivers, load binaries, alter devices or deploy an online service.

## Rollback

A candidate can be withdrawn by closing or deleting the draft. For a published distribution, use the previous known-good tagged release/archive. There is no running service to roll back.
