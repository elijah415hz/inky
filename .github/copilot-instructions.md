# GitHub Copilot Instructions for Inky Project

## Development Environment
- This project uses **pipenv** for dependency management
- Always run Python scripts using: `pipenv run python <script_name>.py`
- Never use direct `python` commands

## Environment Variables
- API keys and secrets are stored in `.env` file
- Use `os.getenv()` to read environment variables (no need for python-dotenv)
- Never put secrets directly in source code

## API Keys in .env:
- `WSDOT_API_ACCESS_CODE` - Washington State Ferries API
- `GOOGLE_MAPS_API_KEY` - Google Maps/Routes API
- `OPEN_WEATHER_API_KEY` - Weather API

## Project Structure
- Main entry point: `main.py`
- Ferry functions: `ferries.py` 
- Route functions: `routes.py`
- Weather functions: `weather.py`
- Pages: `pages/` directory

## Code Style
- Follow existing patterns in the codebase
- Use type hints where appropriate
- Include proper error handling for API calls
