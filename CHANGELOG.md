## [Unreleased]

### Added

- Parse Kraken reports into species predictions in the Bracken format, keeping only species-level rows with reads.

### Changed

### Fixed

- Report unreadable or invalid ResFinder and MLST JSON as parser errors instead of absent results or "No findings"; validate MLST result counts. [#25](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/25)
- Preserve parser exceptions as error envelopes in the shared wrapper instead of falling through with an uninitialized result. [#25](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/25)
- Rewind multipart file streams to the beginning before retrying uploads after timeouts or connection failures, preserving analysis, coverage, and signature content. Fail explicitly if a stream cannot be rewound instead of retrying with empty files. Retries resend whole files, including caller-provided streams. [#24](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/24)
- Preserve ResFinder gene antibiotic annotations in parsed and serialized results; previously the gene model silently discarded them. [#18](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/18)

## [v0.4.0]

### Changed

- `CreateGroupInput` requires a `group_key`, the stable name Bonsai uploads use to reference a group. Callers that created groups without one need to supply it.
- `contig_id` is mandatory on gene hits, so results without it no longer validate.

### Fixed

- Send a sample's groups when creating it; they were dropped.
- Carry a group's `group_key` on group responses.
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
