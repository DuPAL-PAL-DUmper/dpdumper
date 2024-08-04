# Changelog
Changelog for the dpdumper utility

## [0.2.0] - 2024-08-04
### Changed
- Require dupicolib ~0.3.0

### Added
- Added progress bar to track read/write completion

## [0.1.2] - 2024-08-03
### Fixed
- Fix execution in case the --definition parameter is not passed

## [0.1.1] - 2024-08-02
### Fixed
- Actually compare the hw definition required in the TOML files with the current board revision

## [0.1.0] - 2024-08-02
### Changed
- Changed the definition format, so that pin mapping is specified on a single entry, and everything else use the normal IC pin numbering

### Fixed
- Some notes in example TOML files were plain wrong

## [0.0.3] - 2024-07-29
### Changed
- Depends on dupicolib 0.2.0

### Added
- Print the adapter notes when present, and allow them to be skipped
- Add timed notice before starting the self-test
- Read firmware version from board
- Support different command classes depending on model and fw version

## [0.0.2] - 2024-07-26
- Initial release
