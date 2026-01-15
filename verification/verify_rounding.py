import time
from playwright.sync_api import sync_playwright

def verify_rounding():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("http://localhost:5173")

        # Inject LocalStorage for Auth and Language
        # We don't need to inject Channel/API key here because we can type them or rely on the component reading them if we reload.
        # But since the component initializes state from localStorage, if we set it and reload, the inputs should be filled.

        page.evaluate("""() => {
            localStorage.setItem("language", "en");
            localStorage.setItem("googleUser", JSON.stringify({
                name: "Test User",
                picture: "https://via.placeholder.com/150",
                email: "test@example.com"
            }));
            localStorage.setItem("channelId", "123456");
            localStorage.setItem("apiKey", "ABCDEF123456");
        }""")

        # Reload to apply localStorage to the initial state of the React component
        page.reload()

        # Mock ThingSpeak API Response
        # field2: "99.9" -> Should display as "100"
        mock_response = {
            "channel": {
                "id": 123456,
                "name": "Microgrid"
            },
            "feeds": [
                {
                    "created_at": "2023-10-27T10:00:00Z",
                    "entry_id": 1,
                    "field1": "230.5",
                    "field2": "99.9",  # Test Case: 99.9 should round to 100
                    "field3": "45",
                    "field4": "100",
                    "field5": "25"
                }
            ]
        }

        page.route("https://api.thingspeak.com/**", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=str(mock_response).replace("'", '"')
        ))

        # Now we are on the "Connect to Grid" screen.
        # The inputs should be filled because we set localStorage and reloaded.
        # We need to click "Launch Dashboard".

        try:
            # Wait for button and click
            page.get_by_text("Launch Dashboard").click()
            print("Clicked Launch Dashboard")
        except Exception as e:
            print(f"Failed to click dashboard button: {e}")
            page.screenshot(path="verification/error_click.png")
            browser.close()
            return

        # Wait for Dashboard to load
        try:
            # Check for specific dashboard element
            page.wait_for_selector("text=Light Intensity", timeout=10000)
            print("Dashboard loaded.")
        except:
            print("Dashboard failed to load or timed out.")
            page.screenshot(path="verification/error_load.png")
            browser.close()
            return

        # Wait a bit for data to render
        time.sleep(2)

        # Take screenshot
        page.screenshot(path="verification/dashboard_rounding.png")
        print("Screenshot taken at verification/dashboard_rounding.png")

        browser.close()

if __name__ == "__main__":
    verify_rounding()
