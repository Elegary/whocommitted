# whocommitted

Extract every email address that ever committed to a git repository: authors,
committers and `Co-authored-by` trailers, across **all branches and tags**.

`whocommitted` performs a metadata-only clone (`git clone --bare --filter=blob:none`)
and reads the history with `git log --all`: no API rate limits, no per-commit HTTP
requests, and it works with any git host.

## Install

```bash
uv tool install git+https://github.com/<you>/whocommitted   # or: uvx --from . whocommitted
```

Requires `git` in `PATH`.

## Usage

```bash
whocommitted extract octocat/Hello-World
whocommitted extract https://github.com/psf/requests --format json | jq length
whocommitted extract git@github.com:owner/repo.git -f csv -o emails.csv
whocommitted extract owner/repo --no-bots --no-noreply --sort commits
whocommitted extract owner/repo --domain corp.io --domain corp.com -f txt
whocommitted extract owner/repo --include-pulls     # also scan GitHub PR heads (forks)
whocommitted extract https://gitlab.com/group/sub/project.git   # any git URL
whocommitted extract ./local/checkout
whocommitted providers
```

Accepted repository specs:

| Spec | Provider |
| --- | --- |
| `owner/repo`, `github:owner/repo` | GitHub |
| `https://github.com/owner/repo[.git][/tree/...]`, `github.com/owner/repo` | GitHub |
| `git@github.com:owner/repo.git`, `ssh://git@github.com/owner/repo` | GitHub |
| any `https://`, `ssh://`, `git://`, `file://`, `user@host:path` URL or local path | generic git |

Output formats: `table` (default), `json`, `csv`, `txt` (`email<TAB>name`).
Progress and errors go to stderr, results to stdout.

Exit codes: `2` invalid spec, `3` git not found, `4` git command failed
(repository missing, private, network…). Private repositories work with your
usual git credentials (credential helper / SSH agent); prompts are disabled.

## Architecture

```
src/whocommitted/
  providers/   spec → RepoRef (clone URL). base.Provider / HostedProvider, github, generic
  git.py       GitClient: bare partial clone, PR refs fetch, streamed `git log --all`
  extractor.py log records → Commit → Identity (aggregated by lower-cased email)
  filters.py   noreply / bot / domain predicates
  output.py    table, json, csv, txt formatters
  cli.py       Typer CLI
```

### Adding a provider (e.g. GitLab)

```python
class GitLabProvider(HostedProvider):
    name = "gitlab"
    description = "gitlab.com repositories"
    host = "gitlab.com"

    def split_path(self, segments: list[str]) -> tuple[str, str]:
        # nested groups: group/sub/project[/-/tree/...]
        if "-" in segments:
            segments = segments[: segments.index("-")]
        *groups, name = segments
        return "/".join(groups), name
```

Register an instance in `PROVIDERS` (`src/whocommitted/providers/__init__.py`).
Extraction is shared since it relies on git itself.

## Development

```bash
uv sync
uv run pre-commit install        # ruff, mypy, conventional commit-msg hook
uv run pytest --cov
uv run ruff check . && uv run ruff format --check . && uv run mypy
```

Commits follow [Conventional Commits](https://www.conventionalcommits.org/);
[release-please](https://github.com/googleapis/release-please) derives versions
and `CHANGELOG.md` from them on `main`.

## License

MIT
