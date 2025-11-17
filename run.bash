#!/bin/bash
# Generated using Microsoft Copilot
URL="http://localhost:5173"

cd docker/
docker compose up -d
cd ..

echo "Waiting for server to be ready..."
until curl -s --head --request GET "$URL" | grep "200 OK" > /dev/null; do
    sleep 2
done

case "$(uname)" in
    Linux*) xdg-open "$URL" ;;
    Darwin*) open "$URL" ;;
    MINGW*|MSYS*|CYGWIN*) start "$URL" ;;
    *) echo "Unsupported OS" ;;
esac