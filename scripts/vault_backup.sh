#!/bin/bash

# Configuration
TIM_VAULT="/home/cia-one/dev/hermes-agent/data/tim/obsidian"
CHRISANN_VAULT="/home/cia-one/dev/hermes-agent/data/chrisann/obsidian"

DATE=$(date +"%Y-%m-%d %H:%M")
COMMIT_MSG="Auto-commit from hermes-agent server: $DATE"

function backup_vault() {
    local vault_path=$1
    if [ -d "$vault_path/.git" ]; then
        cd "$vault_path" || exit
        
        # Check if there are changes
        if [[ `git status --porcelain` ]]; then
            git add .
            git commit -m "$COMMIT_MSG"
        fi
    fi
}

backup_vault "$TIM_VAULT"
backup_vault "$CHRISANN_VAULT"
