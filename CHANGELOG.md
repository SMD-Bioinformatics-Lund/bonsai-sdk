## [Unreleased]

### Added

- Serialize a computed STX `gene_symbol` display field containing distinct symbols in hit order. Regenerate it from `hits` when loading results, retaining every supporting hit. [#27](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/27)
- Parse Kraken reports into species predictions in the Bracken format, keeping only species-level rows with reads.

### Changed

### Fixed

- Include STX genes from the general virulence database alongside all dedicated `stx` database hits for VirulenceFinder v2/v3. Preserve hit origins in `ref_database`, using v2 database keys and v3 JSON reference attributes. [#20](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/20)
- Return every VirulenceFinder v2/v3 STX match in a `hits` collection instead of a single best-hit result. Load stored multi-hit results into the STX result model. [#20](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/20)
- Assign unique Mykrobe variant IDs across all drug rows in each parsed AMR result so ID-based curation, position lookup, and exports can distinguish findings. [#21](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/21)
- Assign unique Mykrobe variant IDs across all drug rows in each parsed AMR result so ID-based curation, position lookup, and exports can distinguish findings. Existing stored results and curations are not migrated. [#21](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/21)
- Report unreadable or invalid ResFinder and MLST JSON as parser errors instead of absent results or "No findings"; validate MLST result counts. [#25](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/25)
- Preserve parser exceptions as error envelopes in the shared wrapper instead of falling through with an uninitialized result. [#25](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/25)
- Rewind multipart file streams to the beginning before retrying uploads after timeouts or connection failures, preserving analysis, coverage, and signature content. Fail explicitly if a stream cannot be rewound instead of retrying with empty files. Retries resend whole files, including caller-provided streams. [#24](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/24)
- Preserve ResFinder gene antibiotic annotations in parsed and serialized results; previously the gene model silently discarded them. [#18](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/18)

### Migration

- Existing multi-hit STX records can be loaded and serialized with the new display field without reparsing their original reports. Persisting it for database summary queries requires a backfill or re-import; upgrading alone does not modify stored records. [#27](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/27)
- Reparse and reimport existing VirulenceFinder JSON results to populate each STX hit's `ref_database`, include previously omitted general-database STX hits, and convert older single-gene results to the `hits` format. Upgrading alone does not update stored results. The original JSON files can be reused without rerunning VirulenceFinder. [#20](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/20)
- To correct IDs in existing Mykrobe AMR results, reparse and reimport the original Mykrobe CSV files with the updated parser. Upgrading alone does not renumber stored results; rerunning Mykrobe or reloading other analyses is unnecessary. Existing curations are not migrated. Where manual annotations exist, reconcile them against the actual variants before replacing results, since old numeric IDs may identify multiple findings. [#21](https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk/pull/21)

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
