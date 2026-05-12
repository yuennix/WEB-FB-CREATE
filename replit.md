# WEYN Facebook Account Creator

## Overview
A Flask web application for automating the creation of Facebook accounts. Features a key-based access system, multi-threaded registration workers, and an optional Telegram bot for admin management.

## Project Structure
- `app.py` - Main Flask web server and entry point
- `main.py` - Core automation logic (Facebook registration, email verification)
- `auth.py` - Key-based access system + Telegram admin bot
- `storage.py` - Dual-backend storage (PostgreSQL or local JSON files)
- `domains.py` - Email domain management
- `templates/` - Jinja2 HTML templates (login, index, admin)
- `static/` - Static assets

## Running the App
The app starts with gunicorn on port 5000 using gevent workers for concurrent SSE streams:
```
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload --worker-class gevent --workers 4 --worker-connections 1000 --timeout 300 app:app
```

## Dependencies
All dependencies are in `requirements.txt` and managed via pip:
- Flask, gunicorn - Web framework and server
- psycopg2-binary - PostgreSQL driver
- beautifulsoup4 - HTML parsing
- fake-useragent, faker - User agent & fake data generation
- requests - HTTP requests
- pyotp - OTP support
- email_validator, flask-sqlalchemy

## Storage
- Uses `DATABASE_URL` environment variable for PostgreSQL (set automatically by Replit)
- Falls back to local JSON files if no DB is configured
- Created accounts are saved to the `accounts` table or `weynFBCreate.txt`

## Optional Environment Variables (Secrets)
- `TG_BOT_TOKEN` - Telegram bot token for admin notifications (optional)
- `TG_CHAT_ID` - Telegram chat/group ID for admin (optional)

## Features
- Key-based access control (users request keys, admin approves via Telegram)
- Multi-threaded Facebook account creation (50 parallel workers)
- Real-time SSE progress updates in the browser
- Automatic email verification via temp email APIs or IMAP
- Webhook support for email confirmation codes
- Admin panel for user and domain management

## User Preferences
- Use gunicorn (not Flask dev server) for running the app
- Keep the dual-backend storage (PostgreSQL + JSON fallback)
