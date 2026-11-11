#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -u

ARTIFACTS="${1:?artifacts directory}"
SCENARIO="${2:?scenario name}"
export GZ_PARTITION="grc_${SCENARIO}"

TOPIC_LIST="${ARTIFACTS}/gz_topics_${SCENARIO}.txt"
OUT="${ARTIFACTS}/contact_debug_${SCENARIO}.json"

gz topic -l > "${TOPIC_LIST}" 2>&1 || true

TOPIC_LIST="${TOPIC_LIST}" OUT_PATH="${OUT}" SCENARIO="${SCENARIO}" python3 <<'PY'
import json
import os

topic_path = os.environ["TOPIC_LIST"]
out_path = os.environ["OUT_PATH"]
scenario = os.environ["SCENARIO"]
try:
    with open(topic_path, encoding="utf-8") as f:
        topics = [ln.strip() for ln in f if ln.strip()]
except OSError:
    topics = []

contact_topics = [t for t in topics if "contact" in t.lower() or "touch" in t.lower()]
payload = {
    "scenario": scenario,
    "topic_count": len(topics),
    "contact_topics": contact_topics,
    "contact_sample": None,
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
PY
