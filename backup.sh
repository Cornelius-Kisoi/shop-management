#!/bin/bash

# Database backup script
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${DB_NAME:-shopmanagement}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-db}"

# Create backup filename
BACKUP_FILE="${BACKUP_DIR}/backup_${DATE}.sql"

echo "Starting database backup at $(date)"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: $BACKUP_FILE"

    # Compress the backup
    gzip $BACKUP_FILE
    echo "Backup compressed: ${BACKUP_FILE}.gz"

    # Keep only last 7 days of backups
    find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
    echo "Old backups cleaned up"
else
    echo "Backup failed!"
    exit 1
fi

echo "Backup process completed at $(date)"