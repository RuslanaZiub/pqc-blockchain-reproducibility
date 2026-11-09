# GitHub → Zenodo release notes

Recommended repository name: `pqc-blockchain-reproducibility`

1. Create the GitHub repository and push these files.
2. Connect the GitHub account to Zenodo.
3. In Zenodo: Profile → GitHub → Sync now → enable this repository.
4. Only then create GitHub release/tag `v1.0`.
5. Zenodo will ingest the release automatically.

`.zenodo.json` contains the five creators and ORCID identifiers and is the metadata source used by Zenodo for GitHub release archiving.

License metadata is intentionally not set in `.zenodo.json` yet because the archive contains components under different upstream licenses and the license for author-owned scripts must be confirmed before release.
