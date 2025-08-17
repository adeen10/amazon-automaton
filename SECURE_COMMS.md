# Security Setup Guide

## Overview

This application uses API key authentication to secure communication between the frontend and backend. Only requests with a valid API key will be processed.

## How It Works

1. **API Key Configuration**: Both frontend and backend use the same API key from environment files
2. **Key Storage**: The key is stored in `.env` files on both frontend and backend
3. **Authentication**: All API requests must include the key in the `X-API-Key` header
4. **CORS Protection**: Only specific origins are allowed (localhost:5173)

## Setup Instructions

### Step 1: Create API Key

Generate a secure API key (you can use any secure random string generator):

```bash
# Example: Generate a 32-character random string
# You can use online generators or command line tools
```

### Step 2: Configure Backend Environment

Create a `.env` file in the backend directory:

```bash
# In apps/backend/.env
API_KEY=your_secure_api_key_here
```

### Step 3: Configure Frontend Environment

Create a `.env` file in the frontend directory:

```bash
# In apps/frontend/.env
VITE_API_BASE_URL=http://38.242.252.12:4000
VITE_API_KEY=your_secure_api_key_here
```

**Important**: Use the same API key in both files!

### Step 4: Start Backend

```bash
# On your VPS
python main.py
```

### Step 5: Start Frontend

```bash
# On your local PC
npm run dev
```

## Security Features

### ✅ API Key Authentication
- 32-character secure random key
- Required for all API endpoints except `/health`
- Invalid keys return 401/403 errors

### ✅ CORS Protection
- Only allows requests from `localhost:5173` and `127.0.0.1:5173`
- Blocks requests from other origins

### ✅ Origin Validation
- Backend validates request origins
- Prevents unauthorized cross-origin requests

## Testing Security

### Test 1: Valid Request (Should Work)
```bash
curl -H "X-API-Key: your_api_key_here" \
     -H "Content-Type: application/json" \
     -X POST http://38.242.252.12:4000/api/submissions \
     -d '{"brands":[]}'
```

### Test 2: Invalid API Key (Should Fail)
```bash
curl -H "X-API-Key: wrong_key" \
     -H "Content-Type: application/json" \
     -X POST http://38.242.252.12:4000/api/submissions \
     -d '{"brands":[]}'
# Expected: 403 Forbidden
```

### Test 3: No API Key (Should Fail)
```bash
curl -H "Content-Type: application/json" \
     -X POST http://38.242.252.12:4000/api/submissions \
     -d '{"brands":[]}'
# Expected: 401 Unauthorized
```

## File Locations

- **Backend Config**: `apps/backend/.env`
- **Frontend Config**: `apps/frontend/.env`
- **Security Code**: `apps/backend/main.py`

## Changing API Key

If you need to change the API key:

1. Update the API key in both `.env` files
2. Restart both frontend and backend
3. Ensure both files have the same API key

## Security Best Practices

1. **Keep API Key Secret**: Never commit the API key to version control
2. **Use HTTPS**: In production, use HTTPS for all communications
3. **Rotate Keys**: Regularly regenerate API keys
4. **Monitor Logs**: Watch for failed authentication attempts
5. **Restrict Origins**: Only allow necessary frontend origins

## Troubleshooting

### Frontend Can't Connect
- Check that `VITE_API_KEY` is set in `.env`
- Verify the API key matches the one in backend `.env`
- Ensure frontend is running on `localhost:5173`

### Backend Rejects Requests
- Check that the `X-API-Key` header is being sent
- Verify the API key is correct
- Check CORS origins are properly configured

### API Key Not Loaded
- Ensure both `.env` files exist and have the same API key
- Check that `python-dotenv` is installed: `pip install python-dotenv`
- Verify environment variables are being loaded correctly
