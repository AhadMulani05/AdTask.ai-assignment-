import time
import sqlite3
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from flask import Flask, jsonify
import openai

# Set up OpenAI API
openai.api_key = "YOUR_OPENAI_API_KEY"

# SQLite database setup
def setup_database():
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS leads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        email TEXT,
                        details TEXT,
                        enriched_data TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                      )''')
    conn.commit()
    conn.close()

# Scrape Crunchbase (simplified for demo purposes)
def scrape_crunchbase():
    service = Service('chromedriver')
    driver = webdriver.Chrome(service=service)
    driver.get("https://www.crunchbase.com/discover")
    time.sleep(5)  # Allow page to load

    leads = []
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, '.entity-name-primary')
        for elem in elements:
            leads.append(elem.text)
    except Exception as e:
        print(f"Error scraping Crunchbase: {e}")
    finally:
        driver.quit()

    return leads

# Enrich data using GPT API
def enrich_data(name):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Provide a quick analysis of the business {name}, including potential challenges and online presence improvements."}
            ]
        )
        enriched_info = response['choices'][0]['message']['content']
        return enriched_info
    except Exception as e:
        print(f"Error enriching data: {e}")
        return None

# Store data in SQLite
def store_data(name, email, details, enriched_data):
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO leads (name, email, details, enriched_data) 
                      VALUES (?, ?, ?, ?)''', (name, email, details, enriched_data))
    conn.commit()
    conn.close()

# Flask app for monitoring
app = Flask(__name__)

@app.route('/leads', methods=['GET'])
def get_leads():
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads")
    leads = cursor.fetchall()
    conn.close()
    return jsonify(leads)

# Continuous operation
def main():
    setup_database()
    while True:
        try:
            leads = scrape_crunchbase()
            for lead in leads:
                email = f"{lead.lower().replace(' ', '')}@example.com"  # Mock email
                details = f"Details about {lead} from Crunchbase"
                enriched_data = enrich_data(lead)
                store_data(lead, email, details, enriched_data)

            print("Scraping and enrichment completed. Data stored.")
            time.sleep(14400)  # Wait 4 hours before next run
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(300)  # Retry after 5 minutes

if __name__ == '__main__':
    # Run the Flask app in a separate thread for monitoring
    from threading import Thread
    flask_thread = Thread(target=app.run, kwargs={"debug": False, "port": 5000})
    flask_thread.start()

    # Start the main automation script
    main()
