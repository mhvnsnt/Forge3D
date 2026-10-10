#!/bin/bash
# egl-restore.sh — Auto-restore the EGL stack after daemon restarts.
#
# Problem: Daemon restarts wipe /usr/lib/x86_64-linux-gnu/libEGL.so.1,
# breaking Blender renders. This script restores it from the local backup.
#
# The backup was created from the official Ubuntu libegl1 .deb package.
# If the backup is missing, it downloads the .deb directly.
#
# Usage: sudo ./egl-restore.sh
# Called automatically by blender-egl-restore.service on boot.

set -e

EGL_BACKUP_DIR="$HOME/workspace/tools/egl-stack/usr/lib/x86_64-linux-gnu"
EGL_TARGET_DIR="/usr/lib/x86_64-linux-gnu"
DEB_URL="http://azure.archive.ubuntu.com/ubuntu/pool/main/libg/libglvnd/libegl1_1.7.0-1build1_amd64.deb"

log() { echo "[egl-restore] $1"; }

# Check if EGL is already working
if [ -f "$EGL_TARGET_DIR/libEGL.so.1" ]; then
    if nm -D "$EGL_TARGET_DIR/libEGL.so.1" 2>/dev/null | grep -q "eglGetDisplay"; then
        log "EGL stack is healthy, nothing to do"
        exit 0
    else
        log "EGL library is broken (missing symbols), restoring..."
    fi
else
    log "EGL library missing, restoring..."
fi

# Try backup first
if [ -f "$EGL_BACKUP_DIR/libEGL.so.1.1.0" ]; then
    log "Restoring from local backup..."
    cp "$EGL_BACKUP_DIR/libEGL.so.1"* "$EGL_TARGET_DIR/"
    log "Restored from backup"
else
    log "No backup found, downloading .deb..."
    TMP_DEB=$(mktemp --suffix=.deb)
    wget -q "$DEB_URL" -O "$TMP_DEB"
    TMP_DIR=$(mktemp -d)
    dpkg-deb -x "$TMP_DEB" "$TMP_DIR"
    cp "$TMP_DIR/usr/lib/x86_64-linux-gnu/libEGL.so.1"* "$EGL_TARGET_DIR/"
    rm -rf "$TMP_DEB" "$TMP_DIR"
    log "Downloaded and installed from .deb"
fi

# Verify
if nm -D "$EGL_TARGET_DIR/libEGL.so.1" 2>/dev/null | grep -q "eglGetDisplay"; then
    log "EGL restore SUCCESSFUL"
    # Update backup for next time
    cp "$EGL_TARGET_DIR/libEGL.so.1"* "$EGL_BACKUP_DIR/" 2>/dev/null || true
else
    log "EGL restore FAILED - manual intervention needed"
    exit 1
fi

# Ensure blender symlink exists
if [ ! -e /usr/local/bin/blender ]; then
    ln -sf "$HOME/workspace/tools/blender/blender-4.0.2-linux-x64/blender" /usr/local/bin/blender
    log "Restored blender symlink"
fi

log "Done"
