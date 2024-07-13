import requests, livejson

class TweetApi:
    def __init__(self) -> None:
        self.host = "twitter154.p.rapidapi.com"
        self.api_key = livejson.File("config.json", True,True,4)["api_key"]
        self.http = "https://"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.host
        }
        
    def TweetAPIReplies(self, tweet_id):
        url = f"{self.http}{self.host}/tweet/replies"
        querystring = {
            "tweet_id":tweet_id
        }
        response = requests.get(url, headers=self.headers, params=querystring)
        return response.json(), response.status_code
            
    def TweetAPISearchContinuation(self, tweet_id, token):
        url = f"{self.http}{self.host}/tweet/replies/continuation"

        querystring = {
            "tweet_id":tweet_id,
            "continuation_token":token
        }
        
        response = requests.get(url, headers=self.headers, params=querystring)

        return response.json(), response.status_code