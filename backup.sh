#!/bin/bash
# CORAL Backup Script
# Creates timestamped backups of database and configuration

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="coral_backup_${TIMESTAMP}"

echo "Creating backup: $BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup subdirectory
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
mkdir -p "$BACKUP_PATH"

# Backup database
if [ -f "coral/coral.db" ]; then
    cp coral/coral.db "$BACKUP_PATH/coral.db"
    echo "✓ Database backed up"
else
    echo "⚠️  No database found"
fi

# Backup configuration
if [ -f "config.yaml" ]; then
    cp config.yaml "$BACKUP_PATH/config.yaml"
    echo "✓ Configuration backed up"
fi

# Create manifest
cat > "$BACKUP_PATH/MANIFEST.txt" << EOF
CORAL Backup
Created: $(date)
Hostname: $(hostname)
Version: 1.0

Contents:
- coral.db (database)
- config.yaml (configuration)

Restore:
1. Stop CORAL
2. Copy files back to their locations
3. Restart CORAL
EOF

# Compress backup
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"
cd ..

echo "✓ Backup created: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"

# Cleanup old backups (keep last 7)
cd "$BACKUP_DIR"
ls -t coral_backup_*.tar.gz | tail -n +8 | xargs rm -f 2>/dev/null || true
cd ..

echo "✓ Old backups cleaned"
echo "Done!"
