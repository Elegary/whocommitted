#!/usr/bin/env bash
# Run whocommitted on every repository of a GitHub user/org and merge results by domain.
#
# usage: scripts/owner-emails.sh <user-or-org> [extra whocommitted options...]
#   env: GITHUB_TOKEN  optional, raises the API limit (60 -> 5000 req/h)
#        OUT           output directory (default: whocommitted-<owner>)
#        INCLUDE_FORKS 1 to also scan forks (they carry upstream history)
#        LIMIT         only scan the first N repositories
#        WHOCOMMITTED       whocommitted command (default: whocommitted, else `uv run` in this project)
set -euo pipefail

owner=${1:?usage: $0 <user-or-org> [whocommitted options...]}
shift
out=${OUT:-whocommitted-$owner}
mkdir -p "$out/repos"

if [[ -n "${WHOCOMMITTED:-}" ]]; then
  read -r -a whocommitted <<<"$WHOCOMMITTED"
elif command -v whocommitted >/dev/null; then
  whocommitted=(whocommitted)
else
  whocommitted=(uv run --project "$(cd "$(dirname "$0")/.." && pwd)" whocommitted)
fi

auth=()
[[ -n "${GITHUB_TOKEN:-}" ]] && auth=(-H "Authorization: Bearer $GITHUB_TOKEN")
fork_filter='select(.fork | not)'
[[ "${INCLUDE_FORKS:-0}" == 1 ]] && fork_filter='.'

# 1. list repositories (users/<x>/repos also works for organisations)
: >"$out/repos.txt"
page=1
while :; do
  batch=$(curl -fsSL ${auth[@]+"${auth[@]}"} -H "Accept: application/vnd.github+json" \
    "https://api.github.com/users/$owner/repos?per_page=100&page=$page")
  [[ $(jq length <<<"$batch") -eq 0 ]] && break
  jq -r ".[] | $fork_filter | .full_name" <<<"$batch" >>"$out/repos.txt"
  page=$((page + 1))
done
[[ -n "${LIMIT:-}" ]] && head -n "$LIMIT" "$out/repos.txt" >"$out/repos.tmp" && mv "$out/repos.tmp" "$out/repos.txt"
total=$(wc -l <"$out/repos.txt" | tr -d ' ')
echo "$total repositories to scan" >&2

# 2. extract each repository (already scanned ones are skipped, so the script can be resumed)
i=0
while read -r repo; do
  i=$((i + 1))
  file="$out/repos/${repo//\//__}.json"
  [[ -s "$file" ]] && continue
  echo "[$i/$total] $repo" >&2
  if "${whocommitted[@]}" extract "$repo" -f json "$@" </dev/null 2>/dev/null |
    jq --arg repo "$repo" 'map(. + {repo: $repo})' >"$file.tmp"; then
    mv "$file.tmp" "$file"
  else
    rm -f "$file.tmp"
    echo "  failed, skipped" >&2
  fi
done <"$out/repos.txt"

# 3. merge identities across repositories, group by domain, sort by commits
jq -s '
  add // []
  | group_by(.email)
  | map({
      email: .[0].email,
      domain: .[0].domain,
      name: (max_by(.commits).name),
      names: (map(.names[]) | unique),
      commits: (map(.commits) | add),
      repos: (map(.repo) | unique),
      first_seen: (map(.first_seen // empty) | min),
      last_seen: (map(.last_seen // empty) | max)
    })
  | group_by(.domain)
  | map({
      domain: .[0].domain,
      emails: length,
      commits: (map(.commits) | add),
      last_seen: (map(.last_seen // empty) | max),
      identities: sort_by(-.commits, .email)
    })
  | sort_by(-.commits, .domain)
' "$out"/repos/*.json >"$out/by-domain.json"

jq -r '.[]
  | "# \(.domain) (\(.emails) emails, \(.commits) commits)",
    (.identities[] | "\(.email)\t\(.name)\t\(.commits)\t\(.repos | join(","))"),
    ""' "$out/by-domain.json" >"$out/by-domain.txt"

echo "done: $out/by-domain.json, $out/by-domain.txt" >&2
