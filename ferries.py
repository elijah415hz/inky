# Washington State Ferries API Integration
# Run with: pipenv run python ferries.py
# API key stored in .env as WSDOT_API_ACCESS_CODE

import requests
import os
from datetime import datetime
from typing import Optional, List


def get_kingston_edmonds_sailing_times(api_access_code: Optional[str] = None) -> str:
    """
    Get the next three sailing times from Kingston to Edmonds from the Washington State Ferries API.
    
    To get an API access code:
    1. Visit https://wsdot.wa.gov/traffic/api/
    2. Register for a free developer access code
    3. Pass the code to this function
    
    Args:
        api_access_code: WSDOT API access code. Required for live data.
    
    Returns:
        Comma-separated string of the next three sailing times from Kingston to Edmonds
        
    Example:
        >>> times = get_kingston_edmonds_sailing_times("your_api_code")
        >>> print(times)
        "7:35 AM, 8:50 AM, 10:05 AM"
        
    Raises:
        ValueError: If no API access code is provided or no sailing times found
        requests.RequestException: If API request fails
    """
    
    # API base URL for WSDOT Ferry Schedule
    base_url = "http://www.wsdot.wa.gov/Ferries/API/Schedule/rest"
    
    # Terminal IDs (these are the actual WSDOT terminal IDs)
    # Kingston terminal ID: 12
    # Edmonds terminal ID: 8
    kingston_terminal_id = 12
    edmonds_terminal_id = 8
    
    # Get today's date in the required format
    today = datetime.now().strftime("%Y-%m-%d")
    
    # If no API access code provided, try to get it from environment variables
    if api_access_code is None:
        api_access_code = os.getenv('WSDOT_API_ACCESS_CODE')
        if api_access_code is None:
            raise ValueError(
                "API access code is required. Either pass it as a parameter or set "
                "WSDOT_API_ACCESS_CODE environment variable. Register for free at: "
                "https://wsdot.wa.gov/traffic/api/"
            )
    
    try:
        # First, try to get today's schedule for Kingston to Edmonds
        schedule_url = f"{base_url}/scheduletoday/{kingston_terminal_id}/{edmonds_terminal_id}/false"
        params = {"apiaccesscode": api_access_code}
        
        response = requests.get(schedule_url, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse the response (WSDOT API returns JSON)
        schedule_data = response.json()
        
        # Extract sailing times from the documented response structure
        sailing_times = []
        
        # Response structure: { "TerminalCombos": [{ "Times": [{ "DepartingTime": "/Date(...)/" }] }] }
        for terminal_combo in schedule_data['TerminalCombos']:
            for sailing_time in terminal_combo['Times']:
                departure_time = sailing_time['DepartingTime']
                
                # Parse WSDOT date format: "/Date(928174800000-0700)/"
                # Extract timestamp from the format
                import re
                match = re.search(r'/Date\((\d+)([+-]\d{4})?\)/', departure_time)
                if match:
                    timestamp_ms = int(match.group(1))
                    # Convert from milliseconds to seconds
                    timestamp = timestamp_ms / 1000
                    dt = datetime.fromtimestamp(timestamp)
                    formatted_time = dt.strftime("%I:%M %p").lstrip('0')
                    sailing_times.append(formatted_time)
        
        if not sailing_times:
            return "No sailing times available for Kingston to Edmonds today"
        
        # Remove duplicates and sort
        unique_times = list(dict.fromkeys(sailing_times))  # Preserves order while removing duplicates
        
        # Filter to only future times and get next 3
        current_time = datetime.now()
        future_times = []
        
        for time_str in unique_times:
            # Parse the time string back to datetime for comparison
            try:
                # Convert "6:20 AM" format to datetime for today
                time_obj = datetime.strptime(time_str, "%I:%M %p").replace(
                    year=current_time.year,
                    month=current_time.month,
                    day=current_time.day
                )
                if time_obj > current_time:
                    future_times.append(time_str)
                    if len(future_times) >= 3:
                        break
            except ValueError:
                # If parsing fails, include the time anyway
                future_times.append(time_str)
                if len(future_times) >= 3:
                    break
        
        if not future_times:
            return "No more sailings today from Kingston to Edmonds"
        
        return ", ".join(future_times)
    
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch ferry schedule: {str(e)}")
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to parse ferry schedule data: {str(e)}")


def get_kingston_wait_time(api_access_code: Optional[str] = None) -> str:
    """
    Get wait time guidance for Kingston ferry terminal.
    
    Note: This API provides general wait time recommendations rather than real-time wait times.
    
    Args:
        api_access_code: WSDOT API access code. Required for live data.
    
    Returns:
        String describing wait time recommendations for Kingston terminal
        
    Example:
        >>> wait_info = get_kingston_wait_time("your_api_code")
        >>> print(wait_info)
        "Peak: 60 min early, Off-peak: 20 min early"
        
    Raises:
        ValueError: If no API access code is provided
        requests.RequestException: If API request fails
    """
    
    # API base URL for WSDOT Terminal Wait Times
    base_url = "https://wsdot.wa.gov/Ferries/API/Terminals/rest"
    
    # Kingston terminal ID: 12
    kingston_terminal_id = 12
    
    # If no API access code provided, try to get it from environment variables
    if api_access_code is None:
        api_access_code = os.getenv('WSDOT_API_ACCESS_CODE')
        if api_access_code is None:
            raise ValueError(
                "API access code is required. Either pass it as a parameter or set "
                "WSDOT_API_ACCESS_CODE environment variable. Register for free at: "
                "https://wsdot.wa.gov/traffic/api/"
            )
    
    try:
        # Get wait times for Kingston terminal
        wait_time_url = f"{base_url}/terminalwaittimes/{kingston_terminal_id}"
        params = {"apiaccesscode": api_access_code}
        
        response = requests.get(wait_time_url, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse the response (WSDOT API returns JSON)
        wait_data = response.json()
        
        # Extract wait time information based on documented API structure
        # Response structure: { "TerminalName": "Kingston", "WaitTimes": [{ "RouteName": "...", "WaitTimeNotes": "..." }] }
        if not isinstance(wait_data, dict) or 'WaitTimes' not in wait_data:
            return "Wait time information not available"
        
        wait_times = wait_data['WaitTimes']
        
        # Look for Kingston to Edmonds route (Route ID 6)
        for route_info in wait_times:
            if 'RouteName' in route_info and 'Edmonds' in route_info['RouteName']:
                if 'WaitTimeNotes' in route_info and route_info['WaitTimeNotes']:
                    notes = route_info['WaitTimeNotes']
                    # Extract the key information from the notes
                    if 'Peak traffic' in notes and '60 minute' in notes:
                        return "Peak: 60 min early, Off-peak: 20 min early"
                    elif '20 minute' in notes:
                        return "Arrive 20 min early recommended"
                    else:
                        # Return a shortened version of the notes
                        return notes[:50] + "..." if len(notes) > 50 else notes
                
                # If no notes, check for last updated time
                if 'WaitTimeLastUpdated' in route_info:
                    return "General wait guidance available"
        
        return "No wait time info for Edmonds route"
    
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch wait times: {str(e)}")
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to parse wait time data: {str(e)}")


if __name__ == "__main__":
    # Test with actual API using environment variable
    try:
        print("Fetching sailing times from WSDOT API...")
        times = get_kingston_edmonds_sailing_times()  # Will read from .env file
        print(f"Sailing times (Kingston to Edmonds): {times}")
        
        print("\nFetching wait times from WSDOT API...")
        wait_time = get_kingston_wait_time()  # Will read from .env file
        print(f"Current wait time at Kingston: {wait_time}")
    except Exception as e:
        print(f"Error fetching ferry data: {e}")
