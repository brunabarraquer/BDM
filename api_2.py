import re
import os
import logging
from atproto import Client, client_utils
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def login_to_client():
    """
    Log in to the AT Proto client using environment variables.
    Returns:
        Client: Logged-in AT Proto client instance.
        Profile: Profile object for the logged-in user.
    """
    try:
        user = os.getenv("LBXD_USERNAME")
        password = os.getenv("LBXD_PASSWORD")
        if not user or not password:
            raise ValueError("Missing ATP_EMAIL or ATP_PASSWORD in environment variables.")

        client = Client()
        profile = client.login(user, password)
        logger.info("Login successful. Welcome, %s!", profile.display_name)
        return client, profile
    except Exception as e:
        logger.error("Failed to log in: %s", e)
        raise


def list_posts(client, handle, limit=10):
    """
    List posts for the given BlueSky handle.

    Args:
        client (Client): Logged-in AT Proto client instance.
        handle (str): The handle of the user to retrieve posts for.
        limit (int): Number of posts to retrieve.

    Returns:
        list: A list of posts for the given handle.
    """
    try:
        res = []
        cursor = ''
        while len(res) < limit:
            profile_feed = client.get_author_feed(actor=handle, cursor=cursor)
            cursor = profile_feed.cursor
            for feed_view in profile_feed.feed:
                if feed_view.post.record.langs and 'en' in feed_view.post.record.langs:
                    res.append(feed_view.post)
                    if len(res) == limit:
                        break
            if cursor is None:
                break

        logger.info("Total posts retrieved: %d", len(res))
        return res
    except Exception as e:
        logger.error("Failed to list posts: %s", e)
        raise


emoticons_str = r"""
    (?:
        [:=;] # Eyes
        [oO\-]? # Nose (optional)
        [D\)\]\(\]/\\OpP] # Mouth
    )"""

regex_str = [
    emoticons_str,
    r'<[^>]+>',  # HTML tags
    r'(?:@[\w_]+)',  # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)",  # hash-tags
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+',  # URLs

    r'(?:(?:\d+,?)+(?:\.?\d+)?)',  # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])",  # words with - and '
    r'(?:[\w_]+)',  # other words
    r'(?:\S)'  # anything else
]

tokens_re = re.compile(r'(' + '|'.join(regex_str) + ')', re.VERBOSE | re.IGNORECASE)
emoticon_re = re.compile(r'^' + emoticons_str + '$', re.VERBOSE | re.IGNORECASE)


def tokenize(s):
    return tokens_re.findall(s)


def preprocess(s, lowercase=False):
    tokens = tokenize(s)
    if lowercase:
        tokens = [token if emoticon_re.search(token) else token.lower() for token in tokens]
    return tokens


if __name__ == "__main__":
    try:
        # Log in to the client and get the profile info.
        client, profile = login_to_client()

        # List posts with a limit on how many to fetch.
        posts = list_posts(client, os.getenv("BLUESKY_USER"), limit=10)

        # Process a maximum of 10 posts
        for i, post in enumerate(posts):
            logger.info(f"Examining Post {i + 1}: {post.record.text}")
            tokens = preprocess(post.record.text, lowercase=True)
            logger.info(f"Tokens for Post {i + 1}: {tokens}")

    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
