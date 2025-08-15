# Amazon Automation - Setup and Usage Guide

This guide explains how to set up and use the Amazon Automaton system, which consists of a frontend, backend, and Python scraper.

## System Overview

The system has three main components:
1. **Frontend** (React/Vite) - User interface for data entry
2. **Backend** (Python/FastAPI) - API server that receives data and triggers the scraper
3. **Scraper** (Python) - Main automation script that processes the data

## Prerequisites

- **Python** (v3.8 or higher) - [Download here](https://python.org/)
- **Google Chrome** - Required for the scraper automation

## Quick Start

### Step 1: Start the Backend Server

1. Navigate to the backend directory: `apps/backend/`
2. Double-click `START_BACKEND.bat` (Windows) or run `npm start` (Mac/Linux)
3. The backend will start on `http://localhost:4000`

### Step 2: Start the Frontend

1. Navigate to the frontend directory: `apps/frontend/`
2. Double-click `START_FRONTEND.bat` (Windows) or run `npm run dev` (Mac/Linux)
3. The frontend will open in your browser at `http://localhost:5173`

### Step 3: Use the System

1. Fill in the form with your brand and product information
2. Click "Submit all" when ready
3. The system will automatically run the Python scraper with your data

## Detailed Setup Instructions

### Backend Setup

```bash
cd apps/backend
pip install -r requirements.txt
python main.py
```

**Windows users:** Double-click `START_BACKEND.bat`
**Mac/Linux users:** Run `./start_backend.sh`

### Frontend Setup

```bash
cd apps/frontend
npm install
npm run dev
```

### Python Dependencies

The backend and scraper require Python packages. Install them with:

```bash
cd apps/backend
pip install -r requirements.txt
pip install playwright
playwright install chromium
# Add other required packages as needed
```

## Data Format

The system expects data in this format:

```json
{
  "brands": [
    {
      "brand": "Brand Name",
      "countries": [
        {
          "name": "US",
          "products": [
            {
              "productname": "Product Name",
              "url": "https://www.amazon.com/product-url",
              "keyword": "search keyword",
              "categoryUrl": "https://www.amazon.com/category-url"
            }
          ]
        }
      ]
    }
  ]
}
```

## How It Works

1. **Frontend**: User enters brand and product information through a web form
2. **Backend**: Receives the form data and validates it
3. **Scraper**: Python script processes the data and runs the automation
4. **Results**: Output is saved to `full_runs.json` and optionally logged to Google Sheets

## Troubleshooting

### Common Issues

1. **"Python not found"**: Install Python from https://python.org/
2. **"Port already in use"**: Close other applications using ports 4000 or 5173
3. **"Scraper failed"**: Check that Chrome is installed and Python dependencies are set up

### Backend Issues

- Check that the backend is running on `http://localhost:4000`
- Verify that all dependencies are installed with `pip install -r requirements.txt`
- Check the console for error messages
- API documentation available at `http://localhost:4000/docs`

### Frontend Issues

- Ensure the backend is running before starting the frontend
- Check browser console for JavaScript errors
- Verify that all form fields are filled before submitting

### Scraper Issues

- Ensure Python is installed and in your PATH
- Install required Python packages
- Check that Chrome browser is installed
- Verify that the payload format is correct

## File Structure

```
amazon-automaton/
├── apps/
│   ├── frontend/          # React frontend
│   │   ├── START_FRONTEND.bat
│   │   └── src/
│   └── backend/           # Python FastAPI backend + scraper
│       ├── main.py
│       ├── requirements.txt
│       ├── START_BACKEND.bat
│       ├── start_backend.sh
│       ├── main_loop.py   # Main scraper logic
│       ├── sheet_writer.py
│       ├── helium_boot.py
│       ├── gpt.py
│       ├── cerebro.py
│       ├── competitors.py
│       ├── monthlyrev.py
│       ├── profitcal.py
│       ├── getCategoryRev.py
│       ├── Launch.py
│       ├── csv_picker.py
│       ├── full_runs.json
│       └── exports/       # Output files
└── SETUP_AND_USAGE.md
```

## Development

### Adding New Features

1. **Frontend**: Modify `apps/frontend/src/App.jsx`
2. **Backend**: Add endpoints in `apps/backend/main.py`
3. **Scraper**: Modify `apps/backend/main_loop.py`

### Testing

1. Start the backend: `cd apps/backend && python main.py`
2. Start the frontend: `cd apps/frontend && npm run dev`
3. Fill out the form and submit
4. Check the scraper output in the console

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify all prerequisites are installed
3. Ensure all services are running
4. Check the file paths and permissions
