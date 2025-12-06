#!/bin/bash
set -e

echo "🚀 Starting Recipe Chatbot Agent..."

# Kiểm tra xem có index files không
if [ ! -f "$VECTOR_INDEX_PATH" ] || [ ! -f "$VECTOR_META_PATH" ]; then
    echo "⚠️  Index files not found at startup."
    echo "📝 You can create them by:"
    echo "   1. Using the /train endpoint after the service starts"
    echo "   2. Or mounting pre-built index files to /app/data/"
    echo ""
    echo "💡 The service will start but /search endpoint will not work until index is created."
else
    echo "✅ Found index files: $VECTOR_INDEX_PATH and $VECTOR_META_PATH"
fi

# Chạy command được truyền vào
exec "$@"

