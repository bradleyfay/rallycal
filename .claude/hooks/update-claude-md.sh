#!/bin/bash

# update-claude-md.sh - Intelligent CLAUDE.md updater hook
# Triggered by PostToolUse events to maintain workspace context

CLAUDE_MD="${CLAUDE_PROJECT_DIR}/CLAUDE.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
LOG_FILE="${CLAUDE_PROJECT_DIR}/.claude/hooks/update.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log hook execution
echo "[$TIMESTAMP] Hook triggered for tool: ${CLAUDE_TOOL_NAME}" >> "$LOG_FILE"

# Function to update section in CLAUDE.md
update_section() {
    local section_pattern="$1"
    local new_content="$2"
    local temp_file=$(mktemp)
    
    # Use awk to update the specific section
    awk -v pattern="$section_pattern" -v content="$new_content" '
        $0 ~ pattern { print; print content; skip=1; next }
        skip && /^###/ { skip=0 }
        !skip { print }
    ' "$CLAUDE_MD" > "$temp_file"
    
    mv "$temp_file" "$CLAUDE_MD"
}

# Detect what type of update might be needed based on tool and context
case "${CLAUDE_TOOL_NAME}" in
    "Bash")
        # Check if it's a git operation
        if echo "${CLAUDE_TOOL_ARGS}" | grep -q "git"; then
            # Extract git status info
            GIT_STATUS=$(cd "${CLAUDE_PROJECT_DIR}" && git status --short 2>/dev/null || echo "")
            if [ -n "$GIT_STATUS" ]; then
                echo "[$TIMESTAMP] Git activity detected, updating workspace status" >> "$LOG_FILE"
                
                # Check for completed milestones in recent commits
                RECENT_COMMITS=$(cd "${CLAUDE_PROJECT_DIR}" && git log --oneline -5 2>/dev/null || echo "")
                
                # Update last activity timestamp
                sed -i '' "s/^Last Updated:.*/Last Updated: $TIMESTAMP/" "$CLAUDE_MD" 2>/dev/null || \
                echo "### Last Updated: $TIMESTAMP" >> "$CLAUDE_MD"
            fi
        fi
        ;;
        
    "Write"|"Edit"|"MultiEdit")
        # Track file modifications for learning capture
        FILE_PATH="${CLAUDE_TOOL_ARGS}"
        
        # Check if working on key project files
        if echo "$FILE_PATH" | grep -qE "(PROJECT_INDEX|status\.md|active/|LEARNING)"; then
            echo "[$TIMESTAMP] Project status file modified: $FILE_PATH" >> "$LOG_FILE"
            
            # Extract project name from path
            PROJECT=$(echo "$FILE_PATH" | grep -oE "(autodoc-mcp|agenticlearninglab\.dev|claude-code-dev-environment|execution-planning)" | head -1)
            
            if [ -n "$PROJECT" ]; then
                # Update project status in CLAUDE.md
                echo "[$TIMESTAMP] Updating status for project: $PROJECT" >> "$LOG_FILE"
            fi
        fi
        ;;
        
    "TodoWrite")
        # Track todo list changes for progress monitoring
        echo "[$TIMESTAMP] Todo list updated" >> "$LOG_FILE"
        
        # Could parse todo completion patterns here
        ;;
esac

# Check for learning insights patterns in recent activity
if [ -f "${CLAUDE_PROJECT_DIR}/.claude/recent_activity.log" ]; then
    # Look for patterns indicating completed experiments or discoveries
    if grep -q "experiment.*complete\|discovery\|insight" "${CLAUDE_PROJECT_DIR}/.claude/recent_activity.log" 2>/dev/null; then
        echo "[$TIMESTAMP] Learning insight detected, flagging for capture" >> "$LOG_FILE"
        
        # Add a marker for manual review
        if ! grep -q "### Pending Learning Capture" "$CLAUDE_MD"; then
            echo -e "\n### Pending Learning Capture\n- Review recent activity for insights ($TIMESTAMP)" >> "$CLAUDE_MD"
        fi
    fi
fi

# Rotate log if it gets too large (>1MB)
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt 1048576 ]; then
    mv "$LOG_FILE" "${LOG_FILE}.old"
    echo "[$TIMESTAMP] Log rotated" > "$LOG_FILE"
fi

exit 0