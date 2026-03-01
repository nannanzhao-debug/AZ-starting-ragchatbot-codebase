#!/usr/bin/env bash
# Run all code quality checks. Exit on first failure unless --all is passed.
set -euo pipefail

ALL=false
FIX=false

for arg in "$@"; do
    case $arg in
        --all)  ALL=true ;;
        --fix)  FIX=true ;;
        --help) echo "Usage: $0 [--fix] [--all]"
                echo "  --fix   Auto-fix formatting issues instead of just checking"
                echo "  --all   Run all checks even if one fails"
                exit 0 ;;
    esac
done

FAILED=0

run_check() {
    local name=$1
    shift
    echo "=== $name ==="
    if "$@"; then
        echo "PASSED"
    else
        echo "FAILED"
        FAILED=$((FAILED + 1))
        if [ "$ALL" = false ]; then
            exit 1
        fi
    fi
    echo ""
}

if [ "$FIX" = true ]; then
    echo "Auto-fixing formatting issues..."
    echo ""
    run_check "black (formatting)" uv run black src/
    run_check "isort (import order)" uv run isort src/
else
    run_check "black (formatting)" uv run black --check src/
    run_check "isort (import order)" uv run isort --check-only src/
fi

run_check "flake8 (linting)" uv run flake8 src/ --max-line-length 88 --extend-ignore E203,W503

if [ "$FAILED" -gt 0 ]; then
    echo "$FAILED check(s) failed."
    exit 1
else
    echo "All quality checks passed!"
fi
