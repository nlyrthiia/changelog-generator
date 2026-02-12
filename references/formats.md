# Changelog Format Reference

## Keep a Changelog

Follows https://keepachangelog.com/en/1.1.0/

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-02-12

### Breaking Changes
- **auth**: Token format changed from JWT to Paseto (b3c4d5e6)

### Added
- New user authentication flow (a1b2c3d4)
- **api**: Rate limiting middleware (e5f6g7h8)

### Fixed
- Memory leak in connection pool (i9j0k1l2)

### Changed
- Refactored database query layer (m3n4o5p6)

### Deprecated
- **auth**: Basic auth will be removed in v2.0 (q7r8s9t0)

### Performance
- **db**: Optimized batch insert queries (u1v2w3x4)
```

Categories (in order): Breaking Changes, Added, Fixed, Changed, Deprecated, Removed, Performance, Security, Documentation, Tests, Maintenance, Other.

## Conventional Changelog

Used by projects following Conventional Commits (https://www.conventionalcommits.org/).

```markdown
# v1.2.0 (2026-02-12)

### Breaking Changes

* **auth:** token format changed from JWT to Paseto ([b3c4d5e6])

### Added

* **auth:** new user authentication flow ([a1b2c3d4])
* **api:** rate limiting middleware ([e5f6g7h8])

### Fixed

* **db:** memory leak in connection pool ([i9j0k1l2])

### Deprecated

* **auth:** basic auth will be removed in v2.0 ([q7r8s9t0])
```

## Grouped by Date

Simple chronological format, best for internal use.

```markdown
# Changes: v1.1.0 -> HEAD

## 2026-02-12

- feat(auth): new user authentication flow (a1b2c3d4, Alice)
- fix(db): memory leak in connection pool (i9j0k1l2, Bob)
- deprecate(auth): basic auth will be removed in v2.0 (q7r8s9t0, Alice)

## 2026-02-11

- refactor: database query layer (m3n4o5p6, Charlie)
- perf(db): optimized batch insert queries (u1v2w3x4, Dave)
```
