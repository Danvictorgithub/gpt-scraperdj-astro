import os
import google.generativeai as genai
import random
def generate_text(prompt:str):
    genai.configure(api_key=os.getenv("API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

def generate_random_subject():
    subjects = [
        "Technology", "Science", "Health", "Education", "Business", "Entertainment", 
        "Sports", "Politics", "Environment", "History", "Travel", "Food", "Music", 
        "Books", "Movies", "Fashion", "Hobbies", "Relationships", "Fitness", "Culture",
        "Games", "Cartoons", "Toys", "Friends", "School", "Holidays"
    ]
    return random.choice(subjects)
