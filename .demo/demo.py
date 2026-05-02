import requests

def load_page(url):
    # This is the "magic" part. We copy a real User-Agent string from a modern browser.
    # This example is for Chrome on Windows 10.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/' # Pretending we came from Google helps avoid detection
    }

    try:
        # We pass the headers dictionary into the get request
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Successfully loaded page!")
            print(response.text[:500]) # Print first 500 characters of the HTML
        else:
            print(f"Failed to load page. Status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Example usage
load_page("https://en.wikipedia.org/wiki/Example.com") # This site echoes back your headers so you can verify it works

