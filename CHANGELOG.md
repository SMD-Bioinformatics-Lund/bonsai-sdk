## [Unreleased]

### Fixed

- Send a sample's groups when creating it; they were dropped.
- Carry a group's `group` slug, the stable key Bonsai uploads use to reference a group.
- Lower the scipy floor to 1.14 so older Linux systems can install a prebuilt wheel with `pip install --prefer-binary`.
- Declare `email-validator`, which the API client models need.
- Replace the stale sample configs in `tests/fixtures` with manifests in the current `jasentool create-yaml` format, and test that they point to existing files.

- Return LIMS export bytes from the underlying HTTP response instead of accessing a nonexistent attribute on ApiResponse. [#12](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/12)
- Keep AMRFinder AMR and stress genes in their correct result categories and exclude AMR point variants from stress results. [#11](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/11)
- Preserve AMRFinder contig coordinates, alignment lengths, and closest-reference names when parsing gene hits. [#11](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/11)

## [v0.3.0]

### Added

- Added reusable analysis parsers migrated from Bonsai PRP, including support for current and legacy result formats.
- Added API client support for reference genomes, annotation tracks, external sample IDs, analysis subcommands, and server-generated group IDs.
- Added post-alignment QC parsing from samtools coverage and legacy output files.

## [v0.2.1]

### Fixed

- Fixed sample and analysis-result upload response handling.

## [v0.2.0]

### Added

- Added API client methods for creating and retrieving users and groups.
- Added shared request helpers and response models.

### Changed

- Improved API error handling and JSON serialization of sample models.

## [v0.1.0]

### Added

- Initial release of the Bonsai SDK API client.
