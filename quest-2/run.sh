#!/usr/bin/env bash
set -euo pipefail

# Run from the directory this script lives in so relative paths work.
cd "$(dirname "$0")"

# shellcheck disable=SC1091
source path/to/venv/bin/activate
streamlit run bedrock_app_st.py
