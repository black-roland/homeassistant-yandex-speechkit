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

# Service protos also import google.api, yandex.cloud.operation, and
# yandex.cloud.validation. Those filenames are registered by yandexcloud and
# googleapis-common-protos. Vendoring a second copy collides in the process-wide
# descriptor pool. The integration only calls RecognizeStreaming and
# UtteranceSynthesis, so generate service stubs without those imports.
mkdir -p \
  "$WORKDIR/overlay/yandex/cloud/ai/stt/v3" \
  "$WORKDIR/overlay/yandex/cloud/ai/tts/v3" \
  "$WORKDIR/generated"
cat > "$WORKDIR/overlay/yandex/cloud/ai/stt/v3/stt_service.proto" << 'EOF'
syntax = "proto3";

package speechkit.stt.v3;

import "yandex/cloud/ai/stt/v3/stt.proto";

option go_package = "github.com/yandex-cloud/go-genproto/yandex/cloud/ai/stt/v3;stt";
option java_package = "yandex.cloud.api.ai.stt.v3";

service Recognizer {
  rpc RecognizeStreaming(stream StreamingRequest) returns (stream StreamingResponse);
}
EOF
cat > "$WORKDIR/overlay/yandex/cloud/ai/tts/v3/tts_service.proto" << 'EOF'
syntax = "proto3";

package speechkit.tts.v3;

import "yandex/cloud/ai/tts/v3/tts.proto";

option go_package = "github.com/yandex-cloud/go-genproto/yandex/cloud/ai/tts/v3;tts";
option java_package = "yandex.cloud.api.ai.tts.v3";

service Synthesizer {
  rpc UtteranceSynthesis(UtteranceSynthesisRequest) returns (stream UtteranceSynthesisResponse);
  rpc StreamSynthesis(stream StreamSynthesisRequest) returns (stream StreamSynthesisResponse);
}
EOF
"$WORKDIR/venv/bin/python" -m grpc_tools.protoc \
  -I "$WORKDIR/overlay" \
  -I "$WORKDIR/cloudapi" \
  -I "$WORKDIR/cloudapi/third_party/googleapis" \
  --python_out="$WORKDIR/generated" \
  --grpc_python_out="$WORKDIR/generated" \
  yandex/cloud/ai/stt/v3/stt.proto \
  yandex/cloud/ai/stt/v3/stt_service.proto \
  yandex/cloud/ai/tts/v3/tts.proto \
  yandex/cloud/ai/tts/v3/tts_service.proto

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
]
packages = [
    "yandex",
    "yandex/cloud",
    "yandex/cloud/ai",
    "yandex/cloud/ai/stt",
    "yandex/cloud/ai/stt/v3",
    "yandex/cloud/ai/tts",
    "yandex/cloud/ai/tts/v3",
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
            "Service stubs omit google.api, yandex.cloud.operation, and yandex.cloud.validation.",
            "Those filenames are registered by yandexcloud; a second copy collides in the",
            "process-wide protobuf descriptor pool.",
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

echo "Stubs copied to custom_components/yandex_speechkit/yandex."
echo "Review the diff before committing."
