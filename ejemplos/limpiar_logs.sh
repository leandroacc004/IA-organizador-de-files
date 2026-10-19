#!/bin/sh
find ./logs -name "*.log" -mtime +30 -delete
