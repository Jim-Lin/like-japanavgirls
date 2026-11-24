#!/usr/bin/env bash
# Build a statically linked Linux x86_64 (amd64) binary using Docker.
#
# Output: target/linux-amd64/api
#
# - Uses musl, so the binary has no glibc dependency and runs on any x86_64 Linux.
# - Works from Apple Silicon too (Docker runs the amd64 image under emulation).
# - Sources are streamed in via tar instead of a bind mount, so it also works when
#   macOS privacy settings block Docker from reading ~/Documents.
# - Cargo registry and build cache live in named volumes, so rebuilds are much faster.
set -euo pipefail

cd "$(dirname "$0")"
OUT_DIR=target/linux-amd64
mkdir -p "$OUT_DIR"

tar -cf - Cargo.toml Cargo.lock src \
  | docker run --rm -i \
      --platform linux/amd64 \
      -v api-cargo-registry:/usr/local/cargo/registry \
      -v api-cargo-target:/build/target \
      rust:1-alpine \
      sh -c '
        set -e
        # linux-headers provides <linux/random.h>. Without it aws-lc falls back to
        # getentropy() only, which aborts ("getentropy failed.") on kernels < 3.17
        # that lack the getrandom syscall. With it, aws-lc can fall back to /dev/urandom.
        apk add --no-cache musl-dev linux-headers >/dev/null
        mkdir -p /build && cd /build
        rm -rf src && tar -xf -
        cargo build --release --locked --target x86_64-unknown-linux-musl >&2
        tar -cf - -C target/x86_64-unknown-linux-musl/release api
      ' \
  | tar -xf - -C "$OUT_DIR"

echo "built: $OUT_DIR/api"
file "$OUT_DIR/api" 2>/dev/null || true
