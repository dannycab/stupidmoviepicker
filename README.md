



# 🎬 stupidMoviePicker

![version](https://img.shields.io/badge/release-v0.1-blueviolet?style=flat-square)
![performance](https://img.shields.io/badge/v0.9-in--development-orange?style=flat-square)

> **v0.1** — enhanced stupid release. embedded video player, PWA support, video duration tracking, advanced random picker, CSV export. still stupid simple.
>
> **v0.9** — performance upgrade in development. connection pooling, optimized queries, 5x faster. see [UPGRADE_v0.9.md](UPGRADE_v0.9.md) for details.



_This project is not maintained. There is no roadmap. There is no support. There is only vibe coding._


## What is this?

Paste YouTube movie links. Filter by genre. Click random. Sometimes it works. Sometimes it doesn't. If it breaks, open an issue and I'll vibe code a fix. No promises. No explanations. No PRs. Now rebranded as stupidMoviePicker.

## Screenshots

### Main Interface

![Homepage](images/screenshots/home-page.png)
*Main movie grid with genre filtering and random picker*

### Movie Search & Adding

![Movie Search](images/screenshots/main-page-search.png)
*Search functionality for finding movies*


![Add Movie](images/screenshots/main-page-add-movie.png)
*Simple URL-based movie addition interface*

### Movie Details

![Movie Detail](images/screenshots/movie-detail-page.png)
*Rich movie information with OMDb metadata and verification status*

### Genre Management

![Genres Overview](images/screenshots/genres-page.png)
*Browse movies by genre categories*


![Genre Detail](images/screenshots/genre-detail-page.png)
*Detailed view of movies within a specific genre*


> 📸 **Note**: Screenshots show the app in action. Some features may look different due to ongoing vibe coding updates.


## How do I use it?

```sh
git clone https://github.com/dannycab/stupidmoviepicker.git
cd stupidmoviepicker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Or use Docker:

```sh
docker-compose up
```

That's it. Open http://localhost:5000, paste a YouTube movie link, and click random. No login, no accounts, just stupidity.

## API


See [`API.md`](API.md). If you want a new endpoint, open an issue. I'll vibe code it. No docs, just code. Project: stupidMoviePicker.

## Contributing

**No pull requests.**

If you want something, open an issue. I will respond with code only. No explanations. No reviews. No merges. Just pure, unfiltered vibe coding until it works (or doesn't).



## Features

### v0.1 Features
- [x] 🦑 Stupid Simple: No login, no accounts, no setup
- [x] Add movies by YouTube URL or search
- [x] Genre filtering and detail pages
- [x] OMDb metadata (year, rating, poster, etc)
- [x] Random movie picker with advanced filters (genre, year, rating)
- [x] **Embedded video player** - watch movies in-app
- [x] **Video duration tracking** - scraped from YouTube
- [x] **CSV export** - download your movie library
- [x] **PWA support** - installable on mobile devices
- [x] API endpoints for everything
- [x] Color-coded action buttons
- [x] Docker support
- [x] Video ID normalization (prevents duplicates)

### v0.9 Performance Upgrades (In Development)
- [ ] Connection pooling (80% less DB overhead)
- [ ] Optimized SELECT queries (30% faster)
- [ ] Composite database indexes (60% faster filtered queries)
- [ ] Background task optimization (90% faster bulk operations)
- [ ] API result caching (50% fewer wasted calls)
- [ ] **Expected**: 5x performance improvement, 100+ concurrent users

## Roadmap

There is no roadmap. Sometimes I add things if the vibes are right. Sometimes I don't. Features may appear, disappear, or never happen at all. If you want something, open an issue and maybe the vibes will deliver.

Current vibe level: **v0.1 — Embedded player, PWA support, performance analysis complete.**


## Release Notes

- **v0.1** - Embedded video player, PWA support, video duration, advanced filters, CSV export
- **v0.9** (in development) - Performance optimizations: 5x faster, connection pooling, batch operations
- See [UPGRADE_v0.9.md](UPGRADE_v0.9.md) for detailed performance analysis and optimization plan

## More Info

Want to know more? Check these out:
- [INSTALL.md](INSTALL.md) - Installation details
- [API.md](API.md) - API documentation  
- `/api/docs/` - Interactive API docs when running

## License

MIT. Use it, break it, vibe with it. That's it.
