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
    echo ""
    read -p "Create global command 'truetrack'? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        local bin_dir="$HOME/.local/bin"
        local launcher="$bin_dir/truetrack"

        mkdir -p "$bin_dir"

        # Create launcher script
        cat > "$launcher" <<EOF
#!/bin/sh
exec "$run_script" "\$@"
EOF
        chmod +x "$launcher"
        log_success "Created launcher at $launcher"

        # Check PATH
        if [[ ":$PATH:" != *":$bin_dir:"* ]]; then
            log_warn "$bin_dir is not in your PATH."
            read -p "Add to PATH in shell config? [y/N] " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                local shell_rc=""
                if [[ "$SHELL" == */zsh ]]; then shell_rc="$HOME/.zshrc";
                elif [[ "$SHELL" == */bash ]]; then shell_rc="$HOME/.bashrc"; fi

                if [[ -n "$shell_rc" ]]; then
                    echo "" >> "$shell_rc"
                    echo "# TrueTrack PATH" >> "$shell_rc"
                    echo "export PATH=\"\$PATH:$bin_dir\"" >> "$shell_rc"
                    log_success "Added to $shell_rc"
                else
                    log_warn "Could not detect shell config. Please add $bin_dir to PATH manually."
                fi
            fi
        fi
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
        log_warn "Icon assets not found. Desktop launcher not created."
        return
    fi

    echo ""
    read -p "Create desktop launcher? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS .app wrapper
            local app_dir="$HOME/Desktop/TrueTrack.app"
            local contents="$app_dir/Contents"
            local macos="$contents/MacOS"
            local resources="$contents/Resources"
            
            mkdir -p "$macos" "$resources"
            
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
            # Linux .desktop
            local desktop_file="$HOME/.local/share/applications/truetrack.desktop"
            mkdir -p "$(dirname "$desktop_file")"
            
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
            
            # Copy to desktop if dir exists
            local user_desktop="$HOME/Desktop"
            if [[ -d "$user_desktop" ]]; then
                cp "$desktop_file" "$user_desktop/truetrack.desktop"
                chmod +x "$user_desktop/truetrack.desktop"
                log_success "Created shortcut on Desktop."
            else
                log_success "Created menu entry: $desktop_file"
            fi
        fi
    fi
}
