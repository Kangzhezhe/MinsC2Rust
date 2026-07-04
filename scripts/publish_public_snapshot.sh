#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/publish_public_snapshot.sh [options]

Create or update a clean public snapshot repository without copying private Git
history. By default this script commits the snapshot locally in a temporary
clone and does not push. Use --push to update the public remote.

Options:
  --push                  Push the generated snapshot to the public remote.
  --workdir PATH          Temporary public clone path.
                          Default: /tmp/minsc2rust-public
  --remote-url URL        Public repository URL.
                          Default: https://github.com/Kangzhezhe/MinsC2Rust.git
  --branch NAME           Public branch name. Default: master
  --message TEXT          Commit message. Default: Update public snapshot
  --allow-tracked-dirty   Allow uncommitted tracked changes in the private repo.
  -h, --help              Show this help.

Environment overrides:
  PUBLIC_WORKDIR, PUBLIC_REMOTE_URL, PUBLIC_BRANCH, PUBLIC_COMMIT_MESSAGE
USAGE
}

repo_root="$(git rev-parse --show-toplevel)"
workdir="${PUBLIC_WORKDIR:-/tmp/minsc2rust-public}"
remote_url="${PUBLIC_REMOTE_URL:-https://github.com/Kangzhezhe/MinsC2Rust.git}"
branch="${PUBLIC_BRANCH:-master}"
message="${PUBLIC_COMMIT_MESSAGE:-Update public snapshot}"
push=0
allow_tracked_dirty=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --push)
      push=1
      shift
      ;;
    --workdir)
      workdir="${2:?missing value for --workdir}"
      shift 2
      ;;
    --remote-url)
      remote_url="${2:?missing value for --remote-url}"
      shift 2
      ;;
    --branch)
      branch="${2:?missing value for --branch}"
      shift 2
      ;;
    --message)
      message="${2:?missing value for --message}"
      shift 2
      ;;
    --allow-tracked-dirty)
      allow_tracked_dirty=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

cd "$repo_root"

if [[ "$allow_tracked_dirty" -eq 0 ]]; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    cat >&2 <<'MSG'
Refusing to publish from a repo with uncommitted tracked changes.
Commit or stash tracked changes first, or pass --allow-tracked-dirty if you
intentionally want to publish the current HEAD only.
MSG
    exit 1
  fi
fi

paths=(
  .cc-mini.example.toml
  .gitignore.public
  LICENSE
  README.md
  README_zh.md
  assets/framework.png
  Tool/CMakeLists.txt
  Tool/LICENSE
  Tool/pyproject.toml
  Tool/requirements.txt
  Tool/Tool_py
  Tool/clean.py
  Tool/decompose.sh
  Tool/fake_libc_include
  Tool/func_result
  Tool/rust_ast_project
  Tool/test_project
  Tool/run.sh
  Tool/run_post_process.sh
  cc_mini
  benchmarks/arraylist
  benchmarks/c-algorithm
  benchmarks/crown/Input
  configs/config.example.ini
  configs/config_c_algorithm.ini
  configs/config_crown.ini
  scripts/README.md
  scripts/run.sh
  scripts/smoke_test.sh
  scripts/publish_public_snapshot.sh
)

tmp_extract="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_extract"
}
trap cleanup EXIT

echo "[public-snapshot] source repo: $repo_root"
echo "[public-snapshot] public workdir: $workdir"
echo "[public-snapshot] public remote: $remote_url"
echo "[public-snapshot] public branch: $branch"

rm -rf "$workdir"
if git ls-remote --exit-code --heads "$remote_url" "$branch" >/dev/null 2>&1; then
  git clone --branch "$branch" --single-branch "$remote_url" "$workdir"
else
  mkdir -p "$workdir"
  git -C "$workdir" init
  git -C "$workdir" checkout -B "$branch"
  git -C "$workdir" remote add origin "$remote_url"
fi

find "$workdir" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +

git archive --format=tar HEAD -- "${paths[@]}" | tar -x -C "$tmp_extract"
mv "$tmp_extract/.gitignore.public" "$tmp_extract/.gitignore"
cp -a "$tmp_extract"/. "$workdir"/

cd "$workdir"
git add -A

echo "[public-snapshot] scanning staged content"
scan_output="$(
  git grep --cached -n -I -E 'sk-[A-Za-z0-9_-]{16,}|sk_[A-Za-z0-9_-]{16,}|Bearer sk-|/root/ds_test' -- . ':!scripts/publish_public_snapshot.sh' || true
)"

if [[ -n "$scan_output" ]]; then
  if grep -Ev 'ask_and_print_callgraph|sk_test_should_be_redacted|mask|masked' <<<"$scan_output" >/tmp/public_snapshot_scan_hits.$$; then
    echo "[public-snapshot] possible sensitive content found:" >&2
    cat /tmp/public_snapshot_scan_hits.$$ >&2
    rm -f /tmp/public_snapshot_scan_hits.$$
    exit 1
  fi
  rm -f /tmp/public_snapshot_scan_hits.$$
fi

if git diff --cached --quiet; then
  echo "[public-snapshot] no public changes to commit"
else
  git commit -m "$message"
fi

if [[ "$push" -eq 1 ]]; then
  git push origin "HEAD:$branch" --force-with-lease
  echo "[public-snapshot] pushed to $remote_url ($branch)"
else
  echo "[public-snapshot] snapshot committed locally only"
  echo "[public-snapshot] push with:"
  echo "  cd $workdir && git push origin HEAD:$branch --force-with-lease"
fi
