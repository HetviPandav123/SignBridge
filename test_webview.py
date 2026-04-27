import webview
import sys

def test_webview():
    print("Testing pywebview initialization...")
    try:
        # Create a hidden window or just check imports
        window = webview.create_window('Test', 'https://www.google.com', width=100, height=100)
        print("Webview window created successfully.")
        # We don't necessarily need to start it if we just want to check initialization
        # but starting briefly can reveal backend issues.
        # webview.start() 
    except Exception as e:
        print(f"Webview failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_webview()
