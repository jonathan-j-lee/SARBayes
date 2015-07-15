#!/bin/bash
# SARbayes/ISRID/update.sh
# Note: This script is user-specific. Change as necessary.

# Sanity check
# Verify that original file is not overwritten
echo "MD5 checksums: "
echo "  Local copy:     $(md5sum ./ISRIDclean.xlsx)"
echo "  Master copy:    $(md5sum ~/Downloads/ISRIDclean.xlsx)"
echo ""

# Update with arguments
python3 update.py ISRIDclean.xlsx ISRID-updated.xlsx settings.yaml > output.log
