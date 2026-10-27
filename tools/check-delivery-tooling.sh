#!/usr/bin/env bash
# Exercise the real task and installed message hook without creating commits.
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
cd "$repo_root"

git init --quiet "$scratch/repo"
mise exec -- prek validate-config prek.toml
# Prek requires its config to be staged. Stage a copy only in the disposable
# repository, adapting the entry's working directory to exercise the real task.
sed 's/entry = "mise run commit:check"/entry = "bash commit-check"/' prek.toml > "$scratch/repo/prek.toml"
# Prek passes a repository-relative path; resolve it before the adapter changes
# directories. The actual project hook runs at the project root already.
printf '#!/usr/bin/env bash\nmessage=$1\nif [[ $message != /* ]]; then message="$PWD/$message"; fi\nexec mise -C %q run commit:check "$message"\n' "$repo_root" > "$scratch/repo/commit-check"
git -C "$scratch/repo" add prek.toml commit-check
mise exec -- prek -C "$scratch/repo" install
for stage in pre-commit commit-msg; do
  test -x "$scratch/repo/.git/hooks/$stage"
done

message_file="$scratch/commit message.txt"
check_message() {
  local expected=$1 label=$2 message=$3 runner status
  printf '%s' "$message" > "$message_file"
  for runner in task hook; do
    if [[ $runner == task ]]; then
      if mise run commit:check "$message_file" > "$scratch/output" 2>&1; then
        status=0
      else
        status=$?
      fi
    else
      if (cd "$scratch/repo" && .git/hooks/commit-msg "$message_file") > "$scratch/output" 2>&1; then
        status=0
      else
        status=$?
      fi
    fi
    if { [[ $expected == accept && $status != 0 ]]; } ||
      { [[ $expected == reject ]] && { [[ $status == 0 ]] || ! grep -qi 'commit validation: failed' "$scratch/output"; }; }; then
      cat "$scratch/output"
      printf 'FAIL: %s through %s (exit %s)\n' "$label" "$runner" "$status" >&2
      exit 1
    fi
    if [[ $runner == hook ]] && ! grep -q 'Conventional Commit message' "$scratch/output"; then
      cat "$scratch/output"
      printf 'FAIL: message hook did not run\n' >&2
      exit 1
    fi
  done
  printf 'PASS: %s (%s through task and hook)\n' "$label" "$expected"
}

check_message accept plain 'feat: add ingress validation'
check_message accept scoped $'chore(tooling): check commit messages\n\nRefs #107\n'
check_message accept breaking 'feat(api)!: change the telemetry route'
check_message accept breaking-footer $'feat(api): change the telemetry route\n\nBREAKING CHANGE: the route requires an asset identifier\n'
check_message accept merge "Merge branch 'main' into chore/107-task-delivery-conventions"
check_message accept revert 'revert: remove the previous telemetry route'
check_message accept empty ''
check_message reject unstructured 'update things'
check_message reject branch-name 'chore/107-task-delivery-conventions'
check_message reject missing-description 'feat: '
check_message reject git-revert 'Revert "add ingress validation"'
check_message reject fixup 'fixup! feat: add ingress validation'
check_message reject squash 'squash! feat: add ingress validation'
check_message reject amend 'amend! feat: add ingress validation'

formatter_root="$scratch/formatting"
mkdir -p "$formatter_root"
cp dprint.json "$formatter_root/dprint.json"
printf '# Heading\n\n-   item\n' > "$formatter_root/sample.md"
printf '{"answer":42}\n' > "$formatter_root/sample.json"
printf '// comment\n{"answer":42}\n' > "$formatter_root/sample.jsonc"
printf 'answer:    42\n' > "$formatter_root/sample.yaml"
printf 'answer:    42\n' > "$formatter_root/sample.yml"
printf 'answer=42\n' > "$formatter_root/sample.toml"
for directory in .pixi node_modules .pytest_cache .ruff_cache .mypy_cache __pycache__ simulator-output docs/experiments/artifacts tests/fixtures dist build; do
  mkdir -p "$formatter_root/$directory"
  printf 'intentionally invalid generated JSON\n' > "$formatter_root/$directory/generated.json"
done
printf 'intentionally invalid generated YAML\n' > "$formatter_root/pnpm-lock.yaml"

mise exec -- dprint output-file-paths --config "$formatter_root/dprint.json" > "$scratch/paths"
test "$(wc -l < "$scratch/paths")" -eq 7
for extension in md json jsonc yaml yml toml; do
  grep -Fx "$formatter_root/sample.$extension" "$scratch/paths" > /dev/null
done

find "$formatter_root" -type f -exec cksum {} + | LC_ALL=C sort > "$scratch/before-check"
if mise exec -- dprint check --config "$formatter_root/dprint.json" > "$scratch/output" 2>&1; then
  printf 'FAIL: unformatted files passed the formatting check\n' >&2
  exit 1
fi
find "$formatter_root" -type f -exec cksum {} + | LC_ALL=C sort > "$scratch/after-check"
cmp "$scratch/before-check" "$scratch/after-check"

mise exec -- dprint fmt --config "$formatter_root/dprint.json"
mise exec -- dprint check --config "$formatter_root/dprint.json"
find "$formatter_root" -type f -exec cksum {} + | LC_ALL=C sort > "$scratch/first-format"
mise exec -- dprint fmt --config "$formatter_root/dprint.json"
find "$formatter_root" -type f -exec cksum {} + | LC_ALL=C sort > "$scratch/second-format"
cmp "$scratch/first-format" "$scratch/second-format"
printf 'PASS: formatter coverage, exclusions, read-only checks, and repeatability\n'

printf 'Delivery tooling checks passed; no commits created.\n'
