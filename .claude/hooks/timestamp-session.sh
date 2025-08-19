#!/bin/bash

# timestamp-session.sh - Session start tracker for CLAUDE.md
# Records session starts to help track work continuity

CLAUDE_MD="${CLAUDE_PROJECT_DIR}/CLAUDE.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
DATE=$(date "+%Y-%m-%d")
SESSION_LOG="${CLAUDE_PROJECT_DIR}/.claude/hooks/sessions.log"

# Ensure log directory exists
mkdir -p "$(dirname "$SESSION_LOG")"

# Log session start
echo "[$TIMESTAMP] Session started" >> "$SESSION_LOG"

# Check if CLAUDE.md exists
if [ ! -f "$CLAUDE_MD" ]; then
    echo "[$TIMESTAMP] Warning: CLAUDE.md not found at $CLAUDE_MD" >> "$SESSION_LOG"
    exit 0
fi

# Update or add Last Session marker in CLAUDE.md
if grep -q "^### Last Session:" "$CLAUDE_MD"; then
    # Update existing timestamp
    sed -i '' "s/^### Last Session:.*/### Last Session: $TIMESTAMP/" "$CLAUDE_MD"
else
    # Add timestamp section after the header if not present
    awk '/^# Learning Laboratory Workspace Configuration/ {
        print
        print ""
        print "### Last Session: '"$TIMESTAMP"'"
        next
    }
    {print}' "$CLAUDE_MD" > "${CLAUDE_MD}.tmp" && mv "${CLAUDE_MD}.tmp" "$CLAUDE_MD"
fi

# Check for work gaps (sessions more than 24 hours apart)
if [ -f "$SESSION_LOG" ]; then
    LAST_SESSION=$(tail -2 "$SESSION_LOG" | head -1 | cut -d' ' -f1 | tr -d '[]')
    
    if [ -n "$LAST_SESSION" ] && [ "$LAST_SESSION" != "$TIMESTAMP" ]; then
        # Convert to epoch for comparison (macOS compatible)
        if command -v gdate >/dev/null 2>&1; then
            # GNU date (from coreutils)
            CURRENT_EPOCH=$(gdate -d "$TIMESTAMP" +%s)
            LAST_EPOCH=$(gdate -d "$LAST_SESSION" +%s 2>/dev/null || echo 0)
        else
            # BSD date (macOS default)
            CURRENT_EPOCH=$(date -j -f "%Y-%m-%d %H:%M:%S" "$TIMESTAMP" +%s 2>/dev/null || date +%s)
            LAST_EPOCH=$(date -j -f "%Y-%m-%d %H:%M:%S" "$LAST_SESSION" +%s 2>/dev/null || echo 0)
        fi
        
        if [ "$LAST_EPOCH" -gt 0 ]; then
            GAP_HOURS=$(( (CURRENT_EPOCH - LAST_EPOCH) / 3600 ))
            
            if [ "$GAP_HOURS" -gt 24 ]; then
                echo "[$TIMESTAMP] Work gap detected: ${GAP_HOURS} hours since last session" >> "$SESSION_LOG"
                
                # Add work resumption marker
                if ! grep -q "### Work Resumption Notice" "$CLAUDE_MD"; then
                    echo -e "\n### Work Resumption Notice\n- Returning after ${GAP_HOURS} hour gap ($TIMESTAMP)\n- Review current focus and active experiments above" >> "$CLAUDE_MD"
                else
                    sed -i '' "s/^- Returning after .* hour gap.*/- Returning after ${GAP_HOURS} hour gap ($TIMESTAMP)/" "$CLAUDE_MD"
                fi
            fi
        fi
    fi
fi

# Track session frequency for learning velocity insights
SESSIONS_TODAY=$(grep -c "\[$DATE" "$SESSION_LOG" 2>/dev/null || echo 1)
echo "[$TIMESTAMP] Session #$SESSIONS_TODAY for $DATE" >> "$SESSION_LOG"

# Add daily session count to CLAUDE.md if multiple sessions
if [ "$SESSIONS_TODAY" -gt 1 ]; then
    if grep -q "^### Today's Sessions:" "$CLAUDE_MD"; then
        sed -i '' "s/^### Today's Sessions:.*/### Today's Sessions: $SESSIONS_TODAY ($DATE)/" "$CLAUDE_MD"
    else
        echo -e "\n### Today's Sessions: $SESSIONS_TODAY ($DATE)" >> "$CLAUDE_MD"
    fi
fi

# Rotate session log monthly
LOG_SIZE=$(stat -f%z "$SESSION_LOG" 2>/dev/null || stat -c%s "$SESSION_LOG" 2>/dev/null || echo 0)
if [ "$LOG_SIZE" -gt 5242880 ]; then  # 5MB
    ARCHIVE_NAME="${SESSION_LOG}.$(date +%Y%m)"
    mv "$SESSION_LOG" "$ARCHIVE_NAME"
    echo "[$TIMESTAMP] Session log archived to $ARCHIVE_NAME" > "$SESSION_LOG"
fi

exit 0