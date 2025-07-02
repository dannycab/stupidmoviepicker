# 🚀 Installation Guide

This guide provides comprehensive installation instructions for YouTube Movie Picker across different environments and deployment scenarios.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **RAM**: Minimum 512MB, Recommended 1GB+
- **Storage**: 100MB+ for application, additional space for database
- **Network**: Internet connection for YouTube API calls and movie metadata

### Required Software

#### Docker Installation (Recommended)
- **Docker**: Version 20.0+ 
- **Docker Compose**: Version 2.0+

#### Manual Installation
- **Python**: Version 3.12+
- **pip**: Python package manager
- **Git**: For cloning the repository

## 🔐 User Authentication Setup

**New in v2.0**: YouTube Movie Picker now includes multi-user support with authentication.

### First Time Setup
1. **Database Migration**: The first run will automatically migrate the database to support users
2. **Default Admin User**: An admin account is created automatically:
   - **Username**: `admin`
   - **Password**: `admin123`
   - **⚠️ IMPORTANT**: Change this password immediately after first login!

### User Management
- **Registration**: New users can register at `/register`
- **Login**: Access the app at `/login`
- **Profile**: Users can manage their profile at `/profile`
- **Multi-User**: Each user maintains their own private movie collection

## 🐳 Docker Installation (Recommended)

Docker provides the easiest and most reliable deployment method.

### Step 1: Install Docker

#### Ubuntu/Debian
```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install -y docker.io docker-compose

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group (optional, requires logout/login)
sudo usermod -aG docker $USER
```

#### CentOS/RHEL
```bash
# Install Docker
sudo yum install -y docker docker-compose

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### macOS
```bash
# Using Homebrew
brew install docker docker-compose

# Or download Docker Desktop from https://docker.com
```

#### Windows
Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)

### Step 2: Clone Repository
```bash
git clone https://github.com/your-username/YTMoviePicker.git
cd YTMoviePicker
```

### Step 3: Configure Environment (Optional)
```bash
# Copy example environment file
cp .env.example .env

# Edit with your preferred settings
nano .env
```

Example `.env` file:
```env
# OMDb API Key (optional, for rich movie metadata)
OMDB_API_KEY=your_omdb_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=5000
FLASK_DEBUG=false
```

### Step 4: Fix Permissions
```bash
# Ensure Docker can write to data directory
sudo chown -R 1000:1000 ./data
```

### Step 5: Start Application
```bash
# Start in background
docker-compose up -d

# View logs (optional)
docker-compose logs -f

# Check status
docker-compose ps
```

### Step 6: Access Application
- **Web Interface**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/docs/

### Docker Management Commands
```bash
# Stop application
docker-compose down

# Restart application
docker-compose restart

# Update application
git pull
docker-compose down
docker-compose up -d --build

# View logs
docker-compose logs app

# Access container shell
docker-compose exec app bash
```

## 🔧 Manual Installation

For development or environments where Docker isn't available.

### Step 1: Install Python Dependencies

#### Ubuntu/Debian
```bash
# Update package index
sudo apt update

# Install Python and required packages
sudo apt install -y python3 python3-pip python3-venv git

# Install system dependencies
sudo apt install -y build-essential
```

#### CentOS/RHEL
```bash
# Install Python and tools
sudo yum install -y python3 python3-pip git gcc
```

#### macOS
```bash
# Using Homebrew
brew install python3 git

# Or use system Python 3
```

### Step 2: Clone and Setup
```bash
# Clone repository
git clone https://github.com/your-username/YTMoviePicker.git
cd YTMoviePicker

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Initialize Database
```bash
# Create data directory
mkdir -p data

# Initialize database
python init_db.py
```

### Step 4: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

### Step 5: Run Application
```bash
# Development mode
export FLASK_DEBUG=true
python app.py

# Production mode
export FLASK_DEBUG=false
python app.py
```

### Step 6: Access Application
- **Web Interface**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/docs/

## 🌐 Production Deployment

### Using Reverse Proxy (Recommended)

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Apache Configuration
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    ProxyPass / http://localhost:5000/
    ProxyPassReverse / http://localhost:5000/
    ProxyPreserveHost On
</VirtualHost>
```

### Systemd Service (Linux)
```ini
# /etc/systemd/system/ytmoviepicker.service
[Unit]
Description=YouTube Movie Picker
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/YTMoviePicker
Environment=PATH=/opt/YTMoviePicker/venv/bin
ExecStart=/opt/YTMoviePicker/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ytmoviepicker
sudo systemctl start ytmoviepicker
```

## 🔒 Security Considerations

### Firewall Configuration
```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 5000/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### SSL/HTTPS Setup
For production deployments, always use HTTPS:

1. Obtain SSL certificate (Let's Encrypt recommended)
2. Configure your reverse proxy for SSL termination
3. Update port mappings in docker-compose.yml if needed

### Environment Security
- Never commit `.env` files to version control
- Use strong, unique values for production
- Regularly rotate API keys
- Monitor access logs

## 🔍 Troubleshooting

### Common Issues

#### Permission Denied (Docker)
```bash
# Fix data directory permissions
sudo chown -R 1000:1000 ./data

# Add user to docker group (requires logout/login)
sudo usermod -aG docker $USER
```

#### Port Already in Use
```bash
# Check what's using port 5000
sudo lsof -i :5000

# Change port in docker-compose.yml or .env file
```

#### Database Issues
```bash
# Reset database (WARNING: This deletes all data)
rm -f data/movies.db
python init_db.py
```

#### Container Won't Start
```bash
# Check logs
docker-compose logs app

# Rebuild container
docker-compose down
docker-compose up --build
```

### Log Locations
- **Docker**: `docker-compose logs app`
- **Manual**: Check console output or configure logging
- **System**: `/var/log/` (if using systemd service)

## 📞 Getting Help

If you encounter issues:

1. Check this installation guide thoroughly
2. Review the [main README](README.md) for configuration options
3. Check [GitHub Issues](https://github.com/your-username/YTMoviePicker/issues)
4. Create a new issue with:
   - Your operating system and version
   - Installation method (Docker/Manual)
   - Complete error messages
   - Steps to reproduce the problem

## 🎯 Next Steps

After installation:

1. **Add Your First Movie**: Use the "➕ Add Movie" button
2. **Configure OMDb API**: Get an API key for rich movie metadata
3. **Explore Features**: Try the random movie picker and genre browser
4. **Check Admin Panel**: Visit `/admin` for management tools
5. **Read API Docs**: Visit `/api/docs/` for API documentation

Happy movie discovering! 🎬
