import json
from collections import defaultdict
from pathlib import Path

def analyze_posts():
    # Load the posts from the JSON file
    with open('random_posts.json', 'r') as f:
        posts = json.load(f)
    
    # Initialize counters
    channel_counts = defaultdict(int)
    category_counts = defaultdict(int)
    channel_category_map = defaultdict(set)
    
    # Process each post
    for post in posts:
        channel_name = post['channel_name']
        category_name = post['category_name']
        
        # Count posts per channel
        channel_counts[channel_name] += 1
        
        # Count posts per category
        category_counts[category_name] += 1
        
        # Map channels to categories
        channel_category_map[channel_name].add(category_name)
    
    # Print results
    print("\n=== Posts per Category ===")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{category}: {count} posts")
    
    print("\n=== Posts per Channel ===")
    for channel, count in sorted(channel_counts.items(), key=lambda x: x[1], reverse=True):
        categories = ', '.join(channel_category_map[channel])
        print(f"{channel}: {count} posts (Categories: {categories})")
    
    print(f"\nTotal posts analyzed: {len(posts)}")

if __name__ == "__main__":
    analyze_posts() 