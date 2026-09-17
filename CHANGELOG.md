## [Unreleased]

### Fixed

- Keep AMRFinder AMR and stress genes in their correct result categories and exclude AMR point variants from stress results. [#PR](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/PR)
- Preserve AMRFinder contig coordinates, alignment lengths, and closest-reference names when parsing gene hits. [#PR](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/PR)

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
