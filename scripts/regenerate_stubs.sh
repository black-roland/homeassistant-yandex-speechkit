#!/usr/bin/env bash

# Regenerate vendored SpeechKit protobuf/gRPC stubs.
#
#   scripts/regenerate_stubs.sh
#
# Pins grpcio-tools==1.83.1 so the generated gRPC version check accepts the
# grpcio==1.83.1 runtime shipped with Home Assistant 2026.10. Protobuf gencode
# is 7.x and loads on HA's protobuf==7.36. Review the diff before committing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/custom_components/yandex_speechkit"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

python3 -m venv "$WORKDIR/venv"
"$WORKDIR/venv/bin/pip" install -q "protobuf>=7.36,<8" "grpcio-tools==1.83.1"
git clone --depth 1 --recurse-submodules https://github.com/yandex-cloud/cloudapi.git "$WORKDIR/cloudapi"

mkdir -p "$WORKDIR/generated"
(
  cd "$WORKDIR/cloudapi"
  "$WORKDIR/venv/bin/python" -m grpc_tools.protoc \
    -I . \
    -I third_party/googleapis \
    --python_out="$WORKDIR/generated" \
    --grpc_python_out="$WORKDIR/generated" \
    yandex/cloud/ai/stt/v3/stt.proto \
    yandex/cloud/ai/stt/v3/stt_service.proto \
    yandex/cloud/ai/tts/v3/tts.proto \
    yandex/cloud/ai/tts/v3/tts_service.proto \
    yandex/cloud/operation/operation.proto \
    yandex/cloud/api/operation.proto \
    yandex/cloud/validation.proto \
    google/rpc/status.proto \
    google/api/annotations.proto \
    google/api/http.proto
)

"$WORKDIR/venv/bin/python" - "$WORKDIR" "$DEST" << 'PY'
import os
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path

workdir = Path(sys.argv[1])
dest = Path(sys.argv[2])
generated = workdir / "generated"
cloudapi = workdir / "cloudapi"

needed = [
    "yandex/cloud/ai/stt/v3/stt_pb2.py",
    "yandex/cloud/ai/stt/v3/stt_pb2_grpc.py",
    "yandex/cloud/ai/stt/v3/stt_service_pb2.py",
    "yandex/cloud/ai/stt/v3/stt_service_pb2_grpc.py",
    "yandex/cloud/ai/tts/v3/tts_pb2.py",
    "yandex/cloud/ai/tts/v3/tts_pb2_grpc.py",
    "yandex/cloud/ai/tts/v3/tts_service_pb2.py",
    "yandex/cloud/ai/tts/v3/tts_service_pb2_grpc.py",
    "yandex/cloud/api/operation_pb2.py",
    "yandex/cloud/operation/operation_pb2.py",
    "yandex/cloud/validation_pb2.py",
    "google/api/annotations_pb2.py",
    "google/api/http_pb2.py",
    "google/rpc/status_pb2.py",
]
packages = [
    "yandex",
    "yandex/cloud",
    "yandex/cloud/ai",
    "yandex/cloud/ai/stt",
    "yandex/cloud/ai/stt/v3",
    "yandex/cloud/ai/tts",
    "yandex/cloud/ai/tts/v3",
    "yandex/cloud/api",
    "yandex/cloud/operation",
    "google/api",
    "google/rpc",
]

for tree in (dest / "yandex", dest / "google"):
    if tree.exists():
        shutil.rmtree(tree)

for rel in needed:
    target = dest / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(generated / rel, target)

for rel in packages:
    init = dest / rel / "__init__.py"
    init.parent.mkdir(parents=True, exist_ok=True)
    init.write_text("")

# Do not add google/__init__.py. A regular package there would shadow the
# top-level google namespace if this component directory is ever placed on
# sys.path, breaking google.protobuf.

pat = re.compile(r"^from ((?:yandex|google)(?:\.\w+)*) import (\w+)(?: as (\w+))?\s*$")


def rewrite(path: Path) -> None:
    lines = path.read_text().splitlines(True)
    out = []
    for line in lines:
        match = pat.match(line.rstrip("\n"))
        if not match:
            out.append(line)
            continue
        package, module, alias = match.group(1), match.group(2), match.group(3)
        target = dest.joinpath(*f"{package}.{module}".split("."))
        module_file = target.with_suffix(".py")
        if not module_file.is_file():
            out.append(line)
            continue
        rel = os.path.relpath(module_file.parent, path.parent)
        hops = rel.split(os.sep)
        up = sum(1 for part in hops if part == "..")
        down = [part for part in hops if part not in (".", "..")]
        dots = "." * (up + 1)
        suffix = ".".join(down)
        imported = f"{module} as {alias}" if alias else module
        out.append(
            f"from {dots}{suffix} import {imported}\n"
            if suffix
            else f"from {dots} import {imported}\n"
        )
    path.write_text("".join(out))


for rel in needed:
    rewrite(dest / rel)

shutil.copy2(cloudapi / "LICENSE", dest / "yandex" / "LICENSE")
shutil.copy2(cloudapi / "third_party" / "googleapis" / "LICENSE", dest / "google" / "LICENSE")

commit = subprocess.check_output(
    ["git", "-C", str(cloudapi), "rev-parse", "HEAD"], text=True
).strip()
tools = subprocess.check_output(
    [sys.executable, "-m", "pip", "show", "grpcio-tools"], text=True
)
tools_version = next(
    line.split(": ", 1)[1] for line in tools.splitlines() if line.startswith("Version: ")
)
header = (dest / "yandex/cloud/ai/stt/v3/stt_pb2.py").read_text().splitlines()
gencode = next(line for line in header if "Protobuf Python Version" in line)
(dest / "yandex" / "VENDOR.txt").write_text(
    "\n".join(
        [
            "Generated SpeechKit protobuf/gRPC stubs.",
            "source: https://github.com/yandex-cloud/cloudapi",
            f"commit: {commit}",
            f"generator: grpcio-tools {tools_version}",
            gencode.lstrip("# ").strip(),
            "license: MIT (see LICENSE)",
            "Supporting google.api and google.rpc stubs are under ../google (Apache-2.0).",
            "Imports are rewritten to be relative so they resolve inside this component",
            "and do not shadow a top-level yandex package.",
            "",
        ]
    )
)

sys.dont_write_bytecode = True
comp_name = "custom_components.yandex_speechkit"
comp = types.ModuleType(comp_name)
comp.__path__ = [str(dest)]
comp.__package__ = comp_name
parent = types.ModuleType("custom_components")
parent.__path__ = [str(dest.parent)]
sys.modules["custom_components"] = parent
sys.modules[comp_name] = comp
from custom_components.yandex_speechkit.yandex.cloud.ai.stt.v3 import (  # noqa: E402
    stt_pb2,
    stt_service_pb2_grpc,
)
from custom_components.yandex_speechkit.yandex.cloud.ai.tts.v3 import (  # noqa: E402
    tts_pb2,
    tts_service_pb2_grpc,
)

assert hasattr(stt_service_pb2_grpc, "RecognizerStub")
assert hasattr(tts_service_pb2_grpc, "SynthesizerStub")
assert hasattr(tts_pb2, "ContainerAudio")
assert stt_pb2.ContainerAudio.OGG_OPUS
print("Imports OK")
print(f"cloudapi {commit}")
PY

echo "Stubs copied to custom_components/yandex_speechkit/{yandex,google}."
echo "Review the diff before committing."
