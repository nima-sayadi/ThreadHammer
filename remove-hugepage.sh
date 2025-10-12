#!/bin/bash

gbFile="/sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages"

if [ -f "$gbFile" ]; then
  echo 0 > "$gbFile"
  echo "All 1G hugepages released."
else
  echo "Hugepage sysfs file not found (are 1G hugepages enabled?)."
fi

if mount | grep -q "/mnt/huge"; then
  umount /mnt/huge
  echo "/mnt/huge unmounted."
fi