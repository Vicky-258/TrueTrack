#!/bin/bash

# ==============================================================================
# Environment File Writer
# ==============================================================================

# Args: source_file target_file key value [key value ...]
write_env_file() {
    local src="$1"
    local dest="$2"
    shift 2
    local updates=("$@")

    if [[ ! -f "$src" ]]; then
        fail "Source env file not found: $src"
    fi

    log_info "Generating $dest from $src..."

    # Create a temporary file
    local temp_env
    temp_env=$(mktemp)

    cp "$src" "$temp_env"

    # Process updates in pairs
    for ((i=0; i<${#updates[@]}; i+=2)); do
        local key="${updates[i]}"
        local value="${updates[i+1]}"
        
        # Escape slashes for sed
        local escaped_value
        escaped_value=$(echo "$value" | sed 's/\//\\\//g')

        # Regex to uncomment and update, or update existing
        # This handles:
        # # KEY=val
        # KEY=val
        # KEY=
        if grep -qE "^#?[\s]*$key=" "$temp_env"; then
            sed -i "s/^#\?[\s]*$key=.*/$key=$escaped_value/" "$temp_env"
        else
            # Append if not found
            echo "$key=$value" >> "$temp_env"
        fi
    done

    mv "$temp_env" "$dest"
    log_success "Environment configuration written to $dest"
}
