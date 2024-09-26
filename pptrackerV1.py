import requests
from requests.auth import HTTPBasicAuth
import json
import ossapi
from ossapi import Ossapi, Cursor, RankingType, GameMode, ossapiv2
import time
from PIL import Image, ImageDraw, ImageFont
import os
import subprocess

def get_oauth_token(client_id, client_secret):
    token_url = "https://osu.ppy.sh/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "public"
    }
    response = requests.post(token_url, data=data, auth=HTTPBasicAuth(client_id, client_secret))
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Failed to get OAuth token. Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

def get_osu_user_info(access_token, user_id):
    # Try the general users endpoint instead of the game-specific one
    user_base_url = f"https://osu.ppy.sh/api/v2/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.get(user_base_url, headers=headers)
    
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get user info. Response content: {response.text}")
        return None

# Get OAuth token
client_id = "YOUR_CLIENT_ID" 
client_secret = "YOUR_CLIENT_SECRET" 
mode = "fruits"  # Your desired mode here
access_token = get_oauth_token(client_id, client_secret)

if access_token:
    print(f"Access Token: {access_token}")
    
    # Get user info
    user_id = 14337744  # Your userID here (placeholder is for wormsniffer)
    user_info = get_osu_user_info(access_token, user_id)

    if user_info:
        # This is the data that will be displayed
        username = user_info['username']
        user_pp = user_info['statistics']['pp']
        user_ranking = user_info['statistics']['global_rank']
        user_country_ranking = user_info['statistics']['country_rank']
        user_country = user_info['country_code']

        print(f"-- {username} stats --")
        print(f"Name: {username}")
        print(f"PP: {user_pp}")
        print(f"Global Ranking: #{user_ranking}")
        print(f"Country Ranking: #{user_country_ranking} ({user_country})")
    else:
        print("Failed to retrieve user info.")
else:
    print("Failed to obtain access token.")

# Grabs the statistics from the rank #1000 player

#Api call for performance rankings
def get_rank1000_player(access_token, mode):
    rank_base_url = f"https://osu.ppy.sh/api/v2/rankings/{mode}/performance"
    rank_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    params = {
        "cursor[page]": 20,  # Assuming 50 players per page, rank 999 is on page 20
        "limit": 50
    }
    rank = requests.get(rank_base_url, headers=rank_headers, params=params)

    if rank.status_code == 200:
        return rank.json()
    else:
        print(f"Failed to get rank info. Response content: {rank.text}")
        return None

# Get the rank 999 player  // I was too lazy to change the variable names
time.sleep(2)
rank_info = get_rank1000_player(access_token, mode)
if rank_info and 'ranking' in rank_info:
    rankings = rank_info['ranking']
    if len(rankings) >= 50:  # Assuming 50 players per page
        rank_1000_player = rankings[-1]  # Last player on the page (closest to rank 1000)

        name = rank_1000_player['user']['username']
        rank_pp = rank_1000_player['pp']
        global_rank = rank_1000_player['global_rank']
        rank_country = rank_1000_player['user']['country_code']

        print(f"-- Rank 999 player --")
        print(f"Name: {name}")
        print(f"{rank_pp}PP")
        print(f"Rank: {global_rank}")
        print(f"Country: {rank_country}")
    else:
        print("Not enough rankings returned to find rank 1000 player")
else:
    print("Failed to retrieve rank information or 'ranking' key not found in response")

# Compare stats
rank_difference = (user_ranking - global_rank) 
pp_needed = (rank_pp - user_pp)

print(f" -- Comparison --")
print(f"PP needed for 3digit: {pp_needed}")
print(f"Rank Difference: {rank_difference}")

# Create image
imageTemplate = Image.open("bg.png")
draw = ImageDraw.Draw(imageTemplate)
font = ImageFont.truetype("arial.ttf", size=20)
text_color = (162, 171, 212)

# Your player info goes here # Left side
text_lines = [
    f"Player: {username}",
    f"PP: {user_pp:.2f}",
    f"Global Rank: #{user_ranking}",
    f"Country Rank: #{user_country_ranking} ({user_country})",
]

# Rank 999 info goes here    # Right side
text_lines_rank = [
    f"Highest 3digit: {name}",
    f"PP: {rank_pp:.2f}",
    f"Global Rank: #{global_rank}",
    f"Country: ({rank_country})", 
]

# Comparison stats goes here # Middle
text_lines_diff = [
    f"{username} 3 DIGIT WHEN?!",
    f"PP needed: {pp_needed:.2f}",
    f"Rank Difference: {rank_difference}",
    "Azura is making a banner design dw",
    "this is not final go follow him on",
    "twitter in the meanwhile @ItMeAzura"
]

def draw_centered_text(draw, text_lines, x_center, y_start, font, color):
    y = y_start
    for line in text_lines:
        text_width = draw.textlength(line, font=font)
        x = x_center - text_width / 2
        draw.text((x, y), line, fill=color, font=font)
        y += 30  # Move to the next line

# Write text on image - Left side (Your player info)
draw_centered_text(draw, text_lines, imageTemplate.width * 0.15, 50, font, text_color)

# Write text on image - Right side (Rank 999 info)
draw_centered_text(draw, text_lines_rank, imageTemplate.width * 0.85, 50, font, text_color)

# Write text on image - Middle (Comparison stats)
middle_y_start = (imageTemplate.height - len(text_lines_diff) * 30) / 2
draw_centered_text(draw, text_lines_diff, imageTemplate.width / 2, middle_y_start, font, text_color)

# Convert the image to RGB mode
imageTemplate = imageTemplate.convert('RGB')

# Create the output directory if it doesn't exist
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Save the image
imageTemplate.save(os.path.join(output_dir, "stats.jpg"))

# Display the image
imageTemplate.show()

