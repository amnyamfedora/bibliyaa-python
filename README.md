```markdown
# Joke Parser System

A sophisticated Russian joke parser and management system with offline backup capabilities, background parsing, and persistent storage.

## Overview

This Python application automatically collects, filters, and presents Russian jokes from online sources while maintaining a local database of both viewed and unseen jokes. It features intelligent duplicate detection, background parsing, and graceful fallback to offline mode when internet is unavailable.

## Key Features

### 🤖 Smart Joke Collection
- **Dual-source parsing**: Automatically scrapes jokes from multiple anekdot.ru sections (latest and random)
- **Intelligent filtering**: Validates jokes based on Russian language content, length, and technical pattern filtering
- **Duplicate prevention**: Uses MD5 hashing to ensure no joke is ever repeated

### 💾 Persistent Storage System
- **Two-database architecture**:
  - `shown_jokes.json`: Tracks all displayed jokes with usage statistics
  - `unseen_jokes.json`: Maintains a reserve pool of fresh jokes
- **Automatic backup**: Jokes move from unseen to shown pool after display
- **Usage analytics**: Tracks how many times each joke has been shown

### 🌐 Offline-First Design
- **Background parsing**: Continuously fetches new jokes while you browse
- **Offline fallback**: Seamlessly switches to local database when internet is unavailable
- **Reserve pool**: Always maintains a collection of ready-to-use jokes

### 🎨 User Experience
- **Typewriter effect**: Displays jokes with a pleasant animated typing effect
- **Color-coded interface**: Beautiful terminal output with color differentiation
- **Progress tracking**: Real-time statistics showing joke counts and database sizes
- **Interactive session**: Press Enter for more jokes, Ctrl+C to exit

### 🔧 Technical Features
- **Multi-encoding support**: Automatically detects and handles various text encodings (UTF-8, Windows-1251, CP1251)
- **Thread-safe operations**: File locking prevents data corruption during concurrent access
- **Comprehensive logging**: Debug mode available for development
- **Graceful error handling**: Robust exception management with fallback mechanisms

## Installation

### Prerequisites
- Python 3.6+
- pip package manager

### Dependencies
```bash
pip install requests colorama chardet urllib3
```

Quick Start

```bash
git clone https://github.com/yourusername/joke-parser.git
cd joke-parser
python joke_parser.py
```

Configuration

The JokeConfig dataclass allows customization:

```python
config = JokeConfig(
    min_russian_letters=35,      # Minimum Russian letters for validity
    request_timeout=20,           # HTTP request timeout in seconds
    min_joke_length=40,           # Minimum joke length
    max_joke_length=600,          # Maximum joke length
    background_parsing_interval=2 # Interval between background fetches (seconds)
)
```

How It Works

1. Initialization: Creates JSON databases if they don't exist
2. Background parsing: Starts a daemon thread that continuously fetches new jokes
3. Joke retrieval: Attempts online fetch first, falls back to local database
4. Display: Presents jokes with typewriter animation and color formatting
5. Database management: Updates shown/unseen databases automatically

Database Structure

shown_jokes.json

```json
{
  "hash": {
    "text": "Joke text",
    "source_url": "Source URL",
    "length": 123,
    "added_date": "2024-01-01T12:00:00",
    "used_count": 3
  }
}
```

unseen_jokes.json

```json
{
  "hash": {
    "text": "Joke text",
    "source_url": "Source URL",
    "added_date": "2024-01-01T12:00:00"
  }
}
```

Command Line Interface

```
[*] Инициализация системы...
============================================================
       СИСТЕМА ПОИСКА АНЕКДОТОВ v3.0 (JSON)
============================================================

📊 Показано: 45 | В резерве: 23
💾 БД показанных: 0.12 MB | Резерв: 0.07 MB

┌─────────────────────────────────────────────────────┐
│               АНЕКДОТ #01                          │
└─────────────────────────────────────────────────────┘

[Joke displayed with typewriter effect]

───────────────────────────────────────────────────────
```

Development Mode

Enable debug mode by setting __debugable__ = True in the source. This provides:

· Detailed logging of all operations
· Stack traces for errors
· Debug-level information for troubleshooting

Error Handling

The system includes comprehensive error recovery:

· Connection failures: Automatic retry mechanisms
· Malformed JSON: Resets corrupted files
· Network errors: Graceful fallback to offline mode
· Encoding issues: Multi-encoding detection and fallback

Contributing

Contributions welcome! Areas for improvement:

· Additional joke sources
· Custom filtering rules
· GUI interface
· Export/import functionality
· Performance optimizations

License

This project is open source and available under the MIT License.

```
