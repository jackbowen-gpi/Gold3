#!/bin/bash
# Wiki Page Management Script for GOLD3
# Helps manage and deploy wiki pages to MediaWiki

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WIKI_DIR="$PROJECT_ROOT/wiki"
HTML_DIR="$PROJECT_ROOT"

echo "GOLD3 Wiki Page Management"
echo "=========================="
echo

# Function to list available wiki pages
list_pages() {
    echo "Available wiki pages:"
    echo

    if [ -d "$WIKI_DIR" ]; then
        echo "Markdown files in wiki/ directory:"
        find "$WIKI_DIR" -name "*.md" -type f | while read -r file; do
            basename "$file" .md
        done
        echo
    fi

    echo "HTML files in project root:"
    find "$HTML_DIR" -maxdepth 1 -name "wiki_page*.html" -type f | while read -r file; do
        basename "$file" .html
    done
    echo
}

# Function to copy HTML pages to wiki directory
copy_to_wiki() {
    echo "Copying HTML wiki pages to wiki directory..."

    if [ ! -d "$WIKI_DIR" ]; then
        echo "Creating wiki directory..."
        mkdir -p "$WIKI_DIR"
    fi

    # Copy HTML files
    find "$HTML_DIR" -maxdepth 1 -name "wiki_page*.html" -type f | while read -r file; do
        filename=$(basename "$file")
        echo "Copying $filename to wiki directory..."
        cp "$file" "$WIKI_DIR/"
    done

    echo "Copy complete!"
}

# Function to validate HTML syntax
validate_html() {
    echo "Validating HTML syntax..."

    if ! command -v xmllint &> /dev/null; then
        echo "xmllint not found. Installing..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y libxml2-utils
        elif command -v yum &> /dev/null; then
            sudo yum install -y libxml2
        else
            echo "Please install libxml2-utils manually"
            return 1
        fi
    fi

    find "$HTML_DIR" -maxdepth 1 -name "wiki_page*.html" -type f | while read -r file; do
        echo "Validating $(basename "$file")..."
        if xmllint --html --noout "$file" 2>/dev/null; then
            echo "✓ $(basename "$file") is valid HTML"
        else
            echo "✗ $(basename "$file") has HTML errors"
        fi
    done
}

# Function to show usage
usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  list      - List all available wiki pages"
    echo "  copy      - Copy HTML pages to wiki directory"
    echo "  validate  - Validate HTML syntax of wiki pages"
    echo "  help      - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 copy"
    echo "  $0 validate"
}

# Main script logic
case "${1:-help}" in
    "list")
        list_pages
        ;;
    "copy")
        copy_to_wiki
        ;;
    "validate")
        validate_html
        ;;
    "help"|*)
        usage
        ;;
esac
