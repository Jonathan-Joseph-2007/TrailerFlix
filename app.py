from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import re
from youtubesearchpython import VideosSearch

app = Flask(__name__)
CORS(app)

# --- YOUR OMDb KEY ---
OMDB_API_KEY = "e57a99a"
# ---------------------

def custom_youtube_search(query):
    """Backup search using raw requests and regex if the library fails"""
    try:
        # Search URL
        url = f"https://www.youtube.com/results?search_query={query}"
        # Fake User-Agent to look like a real browser
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers)
        
        # Regex to find video IDs (looks for 'watch?v=XXXXXXXXXXX')
        video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
        if video_ids:
            return video_ids[0]
        return None
    except Exception as e:
        print(f"Backup search error: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get-movie', methods=['GET'])
def get_movie():
    movie_name = request.args.get('name')
    print(f"\n--- Searching for: {movie_name} ---")

    if not movie_name:
        return jsonify({"status": "error", "message": "No name provided"}), 400

    # 1. Get Details from OMDb
    omdb_url = f"http://www.omdbapi.com/?t={movie_name}&apikey={OMDB_API_KEY}"
    try:
        omdb_data = requests.get(omdb_url).json()
    except:
        return jsonify({"status": "error", "message": "OMDb Connection Failed"})

    if omdb_data.get("Response") != "True":
        return jsonify({"status": "error", "message": "Movie not found"})

    # 2. Find YouTube ID (Library + Backup)
    video_id = None
    search_query = omdb_data.get("Title") + " Official Trailer"
    
    # Method A: Try Library
    try:
        print("Attempting Library Search...")
        search = VideosSearch(search_query, limit=1)
        results = search.result()
        if results and results.get('result') and len(results['result']) > 0:
            video_id = results['result'][0]['id'] # This was the correct way to access it
            print(f"Library Success: {video_id}")
    except:
        print("Library Search Failed.")

    # Method B: Try Backup if Library Failed
    if not video_id:
        print("Attempting Backup Regex Search...")
        video_id = custom_youtube_search(search_query)
        if video_id:
            print(f"Backup Success: {video_id}")
        else:
            print("All search methods failed.")

    # 3. Send Response
    return jsonify({
        "status": "success",
        "title": omdb_data.get("Title"),
        "year": omdb_data.get("Year"),
        "rating": omdb_data.get("imdbRating"),
        "plot": omdb_data.get("Plot"),
        "poster": omdb_data.get("Poster"),
        "youtube_id": video_id
    })

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
