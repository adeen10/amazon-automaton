# Queue System Documentation

## Overview

The Amazon Automation system now includes a queue management system that allows multiple data submissions to be processed sequentially when the scraper is busy.

## How It Works

### 1. Submission Flow
- When a user clicks "Submit Data" on the frontend, the system checks if the scraper is currently running
- If the scraper is **not running**: Data is processed immediately as before
- If the scraper **is running**: Data is added to a queue file (`queue.json`) and the user receives a notification

### 2. Queue Processing
- When the scraper finishes processing its current pipeline, it automatically:
  - Checks for any items in the queue
  - Processes each queued item one by one
  - Clears the queue file after processing is complete

### 3. User Experience
- **Scraper Free**: User sees "✅ Submitted successfully! The scraper is now running in the background."
- **Scraper Busy**: User sees "✅ Data submitted to queue, will start processing once scraper is free"

## Technical Implementation

### Backend Changes

#### `main_loop.py`
- Added queue management functions:
  - `is_scraper_running()`: Check if scraper is currently active
  - `set_scraper_running(status)`: Set scraper running status
  - `add_to_queue(payload)`: Add data to queue file
  - `get_queue()`: Retrieve all queued items
  - `clear_queue()`: Remove queue file
  - `process_queue()`: Process all queued items

- Modified `run_scraper_main()`:
  - Sets scraper as running at start
  - Sets scraper as not running at end
  - Automatically processes queue after completion

#### `main.py`
- Updated `/api/submissions` endpoint to check scraper status
- Added `/api/scraper-status` endpoint for status checking
- Returns appropriate messages based on scraper state

### Frontend Changes

#### `App.jsx`
- Updated submit handler to show different messages based on response
- Handles both immediate processing and queued processing scenarios

## Queue File Format

The `queue.json` file contains an array of payload objects:

```json
[
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
                "url": "https://amazon.com/product",
                "keyword": "search keyword",
                "categoryUrl": "https://amazon.com/category"
              }
            ]
          }
        ]
      }
    ]
  }
]
```

## Error Handling

- Queue operations are wrapped in try-catch blocks
- Failed queue items are logged but don't stop processing of other items
- Queue file is cleared after processing regardless of individual item success/failure
- System maintains backward compatibility with existing functionality

## Benefits

1. **No Data Loss**: Users can submit data even when scraper is busy
2. **Sequential Processing**: Ensures data is processed in order of submission
3. **Automatic Management**: No manual intervention required
4. **User Feedback**: Clear messaging about data status
5. **Reliability**: Robust error handling and recovery

## Testing

The queue system has been tested to ensure:
- Items are correctly added to queue when scraper is running
- Queue is processed automatically when scraper finishes
- Appropriate messages are shown to users
- Queue file is properly managed (created, read, cleared)
