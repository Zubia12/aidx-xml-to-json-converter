# 🚀 Deployment Guide

This guide provides step-by-step instructions for deploying the AIDX XML to JSON Converter to various cloud platforms.

## 📋 Prerequisites

- Git installed on your local machine
- GitHub account
- Python 3.9+ (for local testing)

## 🌐 Platform Options

### 1. Heroku (Recommended)

Heroku provides easy deployment with automatic builds and free tier options.

#### Step-by-Step Heroku Deployment

1. **Create Heroku Account**
   - Sign up at [heroku.com](https://heroku.com)
   - Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```
   Replace `your-app-name` with your desired app name.

4. **Set Environment Variables**
   ```bash
   heroku config:set FLASK_DEBUG=False
   heroku config:set SECRET_KEY=$(openssl rand -base64 32)
   heroku config:set MAX_CONTENT_LENGTH=16777216
   ```

5. **Deploy to Heroku**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

6. **Open Your App**
   ```bash
   heroku open
   ```

#### One-Click Heroku Deploy

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/yourusername/aidx-xml-to-json-converter)

### 2. Railway

Railway offers modern deployment with automatic HTTPS and easy GitHub integration.

#### Railway Deployment Steps

1. **Sign up at [railway.app](https://railway.app)**
2. **Connect GitHub Repository**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
3. **Configure Environment Variables**
   ```
   FLASK_DEBUG=False
   SECRET_KEY=your-secret-key-here
   MAX_CONTENT_LENGTH=16777216
   ```
4. **Deploy**
   - Railway automatically builds and deploys
   - Get your live URL from the dashboard

### 3. Render

Render provides free static site hosting and web services.

#### Render Deployment Steps

1. **Sign up at [render.com](https://render.com)**
2. **Create New Web Service**
   - Connect your GitHub repository
   - Choose "Web Service"
3. **Configure Build Settings**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: `Python 3`
4. **Set Environment Variables**
   ```
   FLASK_DEBUG=False
   SECRET_KEY=your-secret-key-here
   MAX_CONTENT_LENGTH=16777216
   ```
5. **Deploy**
   - Render automatically builds and deploys
   - Get your live URL from the dashboard

### 4. Vercel

Vercel is optimized for frontend applications but can handle Python with serverless functions.

#### Vercel Deployment Steps

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Create vercel.json**
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "app.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "app.py"
       }
     ]
   }
   ```

4. **Deploy**
   ```bash
   vercel
   ```

### 5. Google Cloud Platform

For enterprise-grade deployment with advanced features.

#### GCP Deployment Steps

1. **Install Google Cloud SDK**
2. **Create app.yaml**
   ```yaml
   runtime: python39
   
   env_variables:
     FLASK_DEBUG: "False"
     SECRET_KEY: "your-secret-key-here"
     MAX_CONTENT_LENGTH: "16777216"
   
   automatic_scaling:
     min_instances: 1
     max_instances: 10
   ```

3. **Deploy**
   ```bash
   gcloud app deploy
   ```

## 🔧 Environment Variables

Set these environment variables on your deployment platform:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_DEBUG` | Enable debug mode | `False` | No |
| `SECRET_KEY` | Flask secret key | Generated | Yes |
| `MAX_CONTENT_LENGTH` | Max file size (bytes) | `16777216` | No |
| `PORT` | Server port | `5000` | No |
| `HOST` | Server host | `0.0.0.0` | No |

## 🔍 Post-Deployment Checklist

After deployment, verify:

- [ ] Application loads successfully
- [ ] File upload works
- [ ] XML to JSON conversion functions
- [ ] Error handling works properly
- [ ] All static files (CSS, JS) load correctly
- [ ] HTTPS is enabled (automatic on most platforms)

## 🐛 Troubleshooting

### Common Issues

1. **Application won't start**
   - Check logs: `heroku logs --tail` (Heroku)
   - Verify all dependencies in requirements.txt
   - Ensure Python version compatibility

2. **File upload fails**
   - Check MAX_CONTENT_LENGTH setting
   - Verify upload directory permissions
   - Check platform file size limits

3. **Static files not loading**
   - Verify static file paths in templates
   - Check Flask static file configuration
   - Ensure files are included in deployment

4. **CORS errors**
   - Update CORS_ORIGINS in app configuration
   - Add your domain to allowed origins

### Getting Help

- Check platform-specific documentation
- Review application logs
- Test locally first: `python app.py`
- Verify all environment variables are set

## 📊 Monitoring

### Health Check Endpoint

Your deployed app includes a health check endpoint:
```
GET /health
```

Use this for monitoring and uptime checks.

### Logging

Application logs include:
- Request processing times
- File upload details
- Conversion statistics
- Error information

Access logs through your platform's dashboard or CLI tools.

## 🔄 Updates

To update your deployed application:

1. **Make changes locally**
2. **Test thoroughly**
3. **Commit changes**
   ```bash
   git add .
   git commit -m "Update description"
   ```
4. **Deploy**
   ```bash
   git push heroku main  # Heroku
   git push origin main  # Other platforms with auto-deploy
   ```

## 🎯 Performance Tips

- Use a CDN for static files in production
- Enable gzip compression
- Monitor memory usage with large files
- Consider implementing file caching
- Use a proper WSGI server (gunicorn is included)

---

**Need help?** Open an issue on GitHub or check the platform-specific documentation.