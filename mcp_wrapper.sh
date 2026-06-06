#!/bin/bash
/home/cia-one/dev/hermes-agent/node_modules/.bin/obsidian-mcp "$@" | while IFS= read -r line; do
  if [[ "$line" =~ ^\{ ]]; then
    echo "$line"
  else
    echo "$line" >&2
  fi
done

