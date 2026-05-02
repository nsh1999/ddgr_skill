import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def extract_webpage_to_markdown(url):
    # 1. Pretend to be a browser (Method 1)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        print(f"Fetching: {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise error for bad status codes (404, 500, etc)
        
        # Ensure we use the correct character encoding
        response.encoding = response.apparent_encoding
        html_content = response.text

        # 2. Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # 3. Clean the page (Remove noise)
        # We remove scripts, styles, and common "junk" elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()

        # Try to find the "Main" content area to avoid extracting the sidebar/footer
        # Common tags for main content are <article>, <main>, or divs with id='content' or 'main'
        main_content = soup.find('article') or soup.find('main') or \
                       soup.find('div', id='content') or soup.find('div', id='main') or \
                       soup.body

        if main_content:
            # 4. Convert the specific HTML section to Markdown
            # We pass the inner HTML of the main content block to markdownify
            markdown_text = md(str(main_content), heading_style="ATX")
            
            # Add the page title at the top for better organization
            title = soup.title.string if soup.title else url
            final_output = f"# {title}\n\nSource: {url}\n\n---\n\n{markdown_text}"
            
            return final_output
        else:
            return "Could not find a valid content area on the page."

    except requests.exceptions.RequestException as e:
        return f"Network error occurred: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    target_url = "https://en.wikipedia.org/wiki/Example.com"
    result = extract_webpage_to_markdown(target_url)
    
    # Save to a file
    with open("output.md", "w", encoding="utf-8") as f:
        f.write(result)
        
    print("\n--- Extraction Complete! ---")
    print("The content has been saved to output.md")

