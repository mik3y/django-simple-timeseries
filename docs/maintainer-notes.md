# Maintainer notes

Notes for maintainers of `django-simple-timeseries`. If you are just using the library, see the [README](../README.md).

## Releasing

To cut a new release, run the `bump` tool:

```
make bump       # bumps the patch version (default)
make bump minor # bumps the minor version
make bump major # bumps the major version
```

Equivalently, you can call the script directly:

```
./scripts/bump.py [patch|minor|major]
```

`bump` will:

1. Increment `version` in `pyproject.toml` (patch by default).
2. Stamp the pending changelog section (`## Current version ...`) in `CHANGELOG.md` with the new version and today's date, and open a fresh pending section for the next release.
3. Refresh `uv.lock`, which records the project's own version.
4. Run `pre-commit` over the changed files (re-staging anything it reformats).
5. Create a commit named `vX.Y.Z` and a matching git tag.

Nothing is pushed automatically. Review the commit and tag, then `git push && git push --tags` when you're happy.

Pushing the tag triggers the `Publish` workflow, which builds the package, creates a GitHub release, and uploads to PyPI.

## PyPI trusted publishing

Uploads authenticate with PyPI over OIDC ([trusted publishing](https://docs.pypi.org/trusted-publishers/)), so there is no API token stored in the repository's secrets.

This has to be configured once on PyPI, under *Account settings → Publishing*, with:

| Field | Value |
| --- | --- |
| PyPI Project Name | `django-simple-timeseries` |
| Owner | `mik3y` |
| Repository name | `django-simple-timeseries` |
| Workflow name | `publish.yml` |
| Environment name | *(unset)* |

The workflow filename is part of what PyPI matches on, so renaming `.github/workflows/publish.yml` means updating the publisher too.
