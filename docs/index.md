---
layout: default
title: YouTube Movie Picker
description: A simple YouTube movie picker web app. Add movies by URL or search, filter by genre, and randomly pick what to watch.
---

# 🎬 YouTube Movie Picker

> ⚡ **Vibe Coding Project** ⚡  
> This project is not maintained. There is no roadmap. There is no support. There is only vibe coding.

## What is this?

Paste YouTube movie links. Filter by genre. Click random. Sometimes it works. Sometimes it doesn't. If it breaks, open an issue and I'll vibe code a fix. No promises. No explanations. No PRs.

## Features

- 🔗 **Easy Movie Adding** - Add movies by pasting YouTube URLs or using search
- 🎭 **Genre Filtering** - Organize and filter your movies by genre
- 🎲 **Random Picker** - Can't decide what to watch? Let fate decide!
- 📊 **Admin Dashboard** - Built-in admin interface for managing your collection
- 🔧 **REST API** - Full API endpoints with Swagger documentation at `/api/docs/`
- 🐳 **Docker Ready** - Comes with Docker support for easy deployment
- 📱 **Mobile Friendly** - Responsive design that works everywhere

## Quick Start

```bash
# Clone the repository
git clone https://github.com/dannycab/ytmoviepicker.git
cd ytmoviepicker

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

### Or use Docker:

```bash
docker-compose up
```

## Current Limitations

- ❌ **No playlist support yet** (manual URL entry only)
- ❌ **Search is slow** (doesn't use YouTube API by default)
- ❌ **No bulk import features**

## API Documentation

The app includes a full REST API with Swagger documentation. Once running, visit:
- Local: `http://localhost:5000/api/docs/`
- API endpoints for movies, genres, admin functions, and search

## Roadmap

**There is no roadmap.** Sometimes I add things if the vibes are right. Sometimes I don't. Features may appear, disappear, or never happen at all. If you want something, open an issue and maybe the vibes will deliver.

## Contributing

**No pull requests.**

If you want something, open an issue. I will respond with code only. No explanations. No reviews. No merges. Just pure, unfiltered vibe coding until it works (or doesn't).

## Tech Stack

- 🐍 **Python** - Backend language
- 🌶️ **Flask** - Web framework
- 🗄️ **SQLite** - Database
- 🎥 **YouTube** - Video source
- 🎬 **OMDb API** - Movie metadata
- 🐳 **Docker** - Containerization

---

Made with ✨ vibe coding ✨ • No license, no warranty, no promises
