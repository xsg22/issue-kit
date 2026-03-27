#!/usr/bin/env bash
# PyPI 发布（纯 shell，不依赖额外 Python 发布脚本）
#
# 依赖：pip install -e ".[release]" ；凭据见 ~/.pypirc 或 TWINE_* 环境变量
#
# 用法：
#   ./scripts/release.sh patch|minor|major   # 升版并发布
#   ./scripts/release.sh --set 1.0.0         # 指定版本并发布
#   ./scripts/release.sh                     # 不升版，按当前版本构建并上传
#   ./scripts/release.sh patch --dry-run --repository testpypi
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

PYPROJECT="$ROOT/pyproject.toml"
INIT_PY="$ROOT/src/issuekit/__init__.py"

usage() {
  cat <<'EOF'
PyPI 发布：./scripts/release.sh [patch|minor|major] [选项]

选项：
  --set VERSION        指定版本（x.y.z）
  --repository NAME    pypi（默认）或 testpypi
  --skip-tests         跳过 pytest
  --dry-run            构建并检查，不上传
  -h, --help           显示本说明
EOF
}

read_pyproject_version() {
  grep -E '^version[[:space:]]*=' "$PYPROJECT" | head -1 \
    | sed -E 's/^version[[:space:]]*=[[:space:]]*"([^"]*)".*/\1/'
}

write_versions() {
  local v="$1"
  local tmp
  tmp="$(mktemp)"
  sed "s/^version = \".*\"/version = \"${v}\"/" "$PYPROJECT" >"$tmp" && mv "$tmp" "$PYPROJECT"
  tmp="$(mktemp)"
  sed "s/^__version__[[:space:]]*=[[:space:]]*\".*\"/__version__ = \"${v}\"/" "$INIT_PY" >"$tmp" && mv "$tmp" "$INIT_PY"
}

bump_semver() {
  local ver="$1" kind="$2"
  local major minor patch
  if [[ ! "$ver" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "无法自动升版（仅支持纯 x.y.z，请用 --set）：$ver" >&2
    exit 1
  fi
  IFS='.' read -r major minor patch <<<"$ver"
  case "$kind" in
    patch) patch=$((patch + 1)) ;;
    minor) minor=$((minor + 1)); patch=0 ;;
    major) major=$((major + 1)); minor=0; patch=0 ;;
    *) echo "invalid bump: $kind" >&2; exit 1 ;;
  esac
  echo "${major}.${minor}.${patch}"
}

BUMP=""
SET_VERSION=""
REPOSITORY="pypi"
SKIP_TESTS=0
DRY_RUN=0

# 首参 patch|minor|major 快捷方式
if [[ "${1:-}" =~ ^(patch|minor|major)$ ]]; then
  BUMP="$1"
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --set)
      SET_VERSION="${2:?--set 需要版本号}"
      shift 2
      ;;
    --repository)
      REPOSITORY="${2:?--repository 需要 pypi 或 testpypi}"
      shift 2
      ;;
    --skip-tests) SKIP_TESTS=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "未知参数: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -n "$BUMP" && -n "$SET_VERSION" ]]; then
  echo "不要同时使用升版档位与 --set" >&2
  exit 1
fi

CURRENT="$(read_pyproject_version)"
NEW_VERSION=""

if [[ -n "$BUMP" ]]; then
  NEW_VERSION="$(bump_semver "$CURRENT" "$BUMP")"
elif [[ -n "$SET_VERSION" ]]; then
  if [[ ! "$SET_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "--set 仅支持 x.y.z 格式: $SET_VERSION" >&2
    exit 1
  fi
  NEW_VERSION="$SET_VERSION"
fi

if [[ -n "$NEW_VERSION" ]]; then
  write_versions "$NEW_VERSION"
  echo "Version: ${CURRENT} -> ${NEW_VERSION}"
else
  echo "Version: ${CURRENT} (unchanged)"
fi

if [[ "$SKIP_TESTS" -eq 0 ]]; then
  if ! python -c "import pytest" 2>/dev/null; then
    echo "未检测到 pytest，正在安装发布依赖: pip install -e \".[release]\""
    python -m pip install -q -e ".[release]"
  fi
  echo "+ python -m pytest"
  # 退出码 5 = 未收集到测试（旧版 pytest 或未开 suppress_no_test_exit_code 时仍视为可继续发布）
  set +e
  python -m pytest
  pytest_ec=$?
  set -e
  if [[ "$pytest_ec" -ne 0 && "$pytest_ec" -ne 5 ]]; then
    exit "$pytest_ec"
  fi
  if [[ "$pytest_ec" -eq 5 ]]; then
    echo "提示: pytest 未收集到任何测试（退出码 5），继续构建与上传。" >&2
  fi
fi

echo "+ clean dist/build artifacts"
rm -rf dist build ./*.egg-info src/issuekit.egg-info 2>/dev/null || true

echo "+ python -m build"
python -m build

echo "+ twine check dist/*"
python -m twine check dist/*

# 使用 -r pypi|testpypi（勿用 --repository-url），Twine 才会按名称读取 ~/.pypirc 里对应段落及凭据
if [[ "$REPOSITORY" == "testpypi" ]]; then
  TWINE_REPO=( -r testpypi )
else
  TWINE_REPO=( -r pypi )
fi

VER_FOR_MSG="${NEW_VERSION:-$CURRENT}"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "+ (dry-run) skipping: python -m twine upload ${TWINE_REPO[*]} dist/*"
  echo "Done (dry-run)."
  exit 0
fi

echo "+ python -m twine upload ${TWINE_REPO[*]} dist/*"
python -m twine upload "${TWINE_REPO[@]}" dist/*

echo "Uploaded to ${REPOSITORY}. Verify: pip install issuekit==${VER_FOR_MSG}"
