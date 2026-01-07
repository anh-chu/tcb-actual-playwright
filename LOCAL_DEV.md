# Local Development Guide

This guide shows you how to run and debug the application locally without Docker.

## Prerequisites

1. **Python 3.12+**
   ```bash
   python3 --version
   ```

2. **Node.js 20+** (for frontend)
   ```bash
   node --version
   ```

3. **Playwright browsers**
   ```bash
   playwright install chromium
   ```

## Setup

### 1. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
# This installs Chromium for Playwright
playwright install chromium
```

### 3. Build Frontend (Optional)

If you want to test the full UI:

```bash
cd frontend
npm install
npm run build
cd ..
```

For frontend development with hot reload:
```bash
cd frontend
npm run dev  # Runs on http://localhost:5173
```

## Running the Backend

### Option 1: Direct Python (Recommended for debugging)

```bash
# From project root
python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag enables auto-restart on code changes.

### Option 2: With debugger (VS Code)

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI: Debug",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

Then press F5 to start debugging with breakpoints.

### Option 3: PyCharm

1. Create a new "Python" run configuration
2. Set script path to: `uvicorn`
3. Set parameters to: `app:app --reload --host 0.0.0.0 --port 8000`
4. Set working directory to project root

## Environment Variables

Create a `.env` file in the project root:

```bash
# Optional: Set a persistent secret key
SECRET_KEY=your-secret-key-here-min-32-chars

# Database will be created at data/database.db automatically
```

## Accessing the Application

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend** (if built): http://localhost:8000
- **Frontend Dev Server** (if running npm run dev): http://localhost:5173

## Debugging Tips

### 1. Enable Verbose Logging

In `modules/logger.py`, set level to DEBUG:

```python
logger.setLevel(logging.DEBUG)
```

### 2. View Browser During Automation

In `service.py`, change `headless=True` to `headless=False`:

```python
self._browser = await self._playwright.chromium.launch(
    headless=False,  # Change this to see the browser
    args=[...]
)
```

### 3. Slow Down Automation

Add delays to see what's happening:

```python
await self._page.wait_for_timeout(2000)  # Wait 2 seconds
```

### 4. Take Screenshots Manually

```python
await self._page.screenshot(path="debug.png")
```

### 5. Print Page Content

```python
content = await self._page.content()
print(content)
```

### 6. Check Database

```bash
# Install sqlite3 if needed
brew install sqlite3

# Open database
sqlite3 data/database.db

# View tables
.tables

# View users
SELECT * FROM user;

# View settings
SELECT * FROM settings;

# Exit
.quit
```

## Common Issues

### Issue: "Module not found"
**Solution**: Make sure virtual environment is activated and dependencies are installed.

### Issue: "Playwright browser not found"
**Solution**: Run `playwright install chromium`

### Issue: "Port 8000 already in use"
**Solution**: 
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Issue: Database locked
**Solution**: Stop all running instances and delete `data/database.db` to start fresh.

## Hot Reload Development

For the best development experience:

1. **Terminal 1** - Backend with auto-reload:
   ```bash
   source venv/bin/activate
   uvicorn app:app --reload
   ```

2. **Terminal 2** - Frontend dev server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open http://localhost:5173 (Vite dev server proxies API calls to :8000)

## Testing Individual Modules

You can test modules directly:

```bash
# Test conversion module
python3 -c "from modules import convert; print(convert.convert_to_actual_transaction({...}, {}))"

# Test Actual Budget connection
python3 -c "from modules import actual; print(actual.init_actual({...}))"
```

## Cleanup

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv

# Clean database
rm -rf data/
```
