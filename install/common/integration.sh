#!/bin/bash

# ==============================================================================
# Integration Helpers (Launcher & Shortcuts)
# ==============================================================================

setup_integration() {
    local install_dir="$1"
    local run_script="$install_dir/run.sh"
    local dry_run="${2:-false}"

    log_info "Phase 7: Integration & Desktop Shortcuts"

    if [[ "$dry_run" == "true" ]]; then
        log_info "Dry run: Skipping integration setup."
        return
    fi

    # 1. Global Launcher (~/.local/bin/truetrack)
    # ---------------------------------------------------------
    local bin_dir="$HOME/.local/bin"
    local launcher="$bin_dir/truetrack"

    if [[ -d "$bin_dir" ]] || mkdir -p "$bin_dir" 2>/dev/null; then
        cat > "$launcher" <<EOF
#!/bin/sh
exec "$run_script" "\$@"
EOF
        chmod +x "$launcher"
        log_success "Created global launcher at $launcher"

        # Check PATH (Informational only)
        if [[ ":$PATH:" != *":$bin_dir:"* ]]; then
            log_warn "$bin_dir is not in your PATH. Add it manually to run 'truetrack' globally."
        fi
    else
        log_warn "Could not create $bin_dir. Skipping global launcher."
    fi

    # 2. Desktop Shortcut
    # ---------------------------------------------------------
    local icon_png="$install_dir/assets/icon/truetrack.png"
    local icon_icns="$install_dir/assets/icon/truetrack.icns"
    local has_icons=true

    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [[ ! -f "$icon_icns" ]]; then has_icons=false; fi
    else
        if [[ ! -f "$icon_png" ]]; then has_icons=false; fi
    fi

    if [[ "$has_icons" != "true" ]]; then
        log_warn "Icon assets not found. Skipping desktop shortcut."
        return
    fi

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS .app wrapper
        local app_dir="$HOME/Desktop/TrueTrack.app"
        local contents="$app_dir/Contents"
        local macos="$contents/MacOS"
        local resources="$contents/Resources"
        
        # Best effort creation
        if mkdir -p "$macos" "$resources" 2>/dev/null; then
            # Info.plist
            cat > "$contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>TrueTrack</string>
    <key>CFBundleIconFile</key>
    <string>truetrack.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.truetrack.launcher</string>
    <key>CFBundleName</key>
    <string>TrueTrack</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
EOF
            # Icon
            cp "$icon_icns" "$resources/truetrack.icns"

            # Executable script
            cat > "$macos/TrueTrack" <<EOF
#!/bin/bash
exec "$run_script"
EOF
            chmod +x "$macos/TrueTrack"
            log_success "Created $app_dir"
        else
            log_warn "Could not create macOS app wrapper on Desktop."
        fi
        
    else
        # Linux .desktop
        local applications_dir="$HOME/.local/share/applications"
        local desktop_file="$applications_dir/truetrack.desktop"
        
        if mkdir -p "$applications_dir" 2>/dev/null; then
            cat > "$desktop_file" <<EOF
[Desktop Entry]
Type=Application
Name=TrueTrack
Comment=TrueTrack Music Pipeline
Exec=$run_script
Path=$install_dir
Icon=$icon_png
Terminal=true
Categories=Audio;Utility;
EOF
            chmod +x "$desktop_file"
            
            # Update cache if possible
            if command -v update-desktop-database &> /dev/null; then
                update-desktop-database "$applications_dir" || true
            fi
            
            log_success "Created application entry: $desktop_file"
        else
             log_warn "Could not create .desktop file in $applications_dir"
        fi
    fi
}
