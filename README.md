# EXTREME TECH Shop Management System

A comprehensive Django-based shop management system with PWA capabilities, designed for production deployment.

## Features

- 🛒 **Point of Sale (POS)** - Complete sales management
- 📊 **Dashboard & Reports** - Real-time analytics and reporting
- 👥 **User Management** - Role-based access control
- 📦 **Inventory Management** - Product and stock tracking
- 💰 **Financial Reports** - Sales, revenue, and profit analysis
- 📱 **PWA Support** - Installable web app with offline capabilities
- 🌙 **Dark Mode** - Modern UI with theme switching
- 🔒 **Production Ready** - Security, performance, and monitoring

## Production Deployment

### Prerequisites

- Docker & Docker Compose
- PostgreSQL (for production database)
- Redis (for caching)
- SSL certificate (recommended)

### Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd extreme-tech-shop
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env.production
   # Edit .env.production with your production settings
   ```

3. **Deploy:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

### Manual Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d --build
   ```

2. **Run migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Collect static files:**
   ```bash
   docker-compose exec web python manage.py collectstatic
   ```

## Environment Configuration

### Required Environment Variables

```bash
# Security
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=shopmanagement_prod
DB_USER=shopmanagement_user
DB_PASSWORD=secure-password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/1

# Security Headers
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Production Features

### Security
- ✅ SSL/HTTPS enforcement
- ✅ Security headers (HSTS, CSP, X-Frame-Options)
- ✅ CSRF protection
- ✅ Secure cookies
- ✅ Rate limiting
- ✅ Input validation

### Performance
- ✅ Redis caching
- ✅ Gunicorn WSGI server
- ✅ WhiteNoise static file serving
- ✅ Database connection pooling
- ✅ Compressed static files

### Monitoring
- ✅ Health check endpoint (`/health/`)
- ✅ Structured logging
- ✅ Database connection monitoring
- ✅ Cache monitoring

### Backup & Recovery
- ✅ Automated database backups
- ✅ Backup retention (7 days)
- ✅ Easy rollback procedures

### Deployment
- ✅ Docker containerization
- ✅ Nginx reverse proxy
- ✅ Load balancing ready
- ✅ Zero-downtime deployments

## API Documentation

The system provides REST APIs for:
- User management
- Product management
- Sales transactions
- Customer management
- Reports and analytics

Access the API at: `http://yourdomain.com/api/`

## Health Checks

- **Application Health**: `GET /health/`
- **Database Status**: Included in health check
- **Cache Status**: Included in health check

## Maintenance Mode

Enable maintenance mode by setting the `MAINTENANCE_MODE` environment variable to `True`.

Access maintenance page at: `http://yourdomain.com/maintenance/`

## Backup & Restore

### Automated Backups
- Daily backups at 2 AM
- Stored in `./backups/` directory
- 7-day retention period

### Manual Backup
```bash
docker-compose exec db pg_dump -U username -d dbname > backup.sql
```

### Restore
```bash
docker-compose exec -T db psql -U username -d dbname < backup.sql
```

## Monitoring & Logs

### Application Logs
```bash
docker-compose logs web
```

### Database Logs
```bash
docker-compose logs db
```

### Nginx Logs
```bash
docker-compose logs nginx
```

## SSL Configuration

1. Obtain SSL certificate (Let's Encrypt recommended)
2. Place certificates in `./nginx/ssl/`
3. Update nginx configuration
4. Set `SECURE_SSL_REDIRECT=True`

## Scaling

### Horizontal Scaling
- Add more web service instances in docker-compose.yml
- Configure load balancer (nginx can handle this)

### Database Scaling
- Use read replicas for read-heavy workloads
- Implement database sharding if needed

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Permission errors**: Ensure proper file permissions
3. **Database connection**: Check database credentials
4. **Static files**: Run `collectstatic` after code changes

### Debug Mode
Set `DEBUG=True` in environment for development debugging.

## Support

For support and issues:
- Email: support@extremetech.com
- Phone: +254 723 276 482

## License

Copyright © 2026 EXTREME TECH. All rights reserved.