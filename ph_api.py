import os
import config
import logging
import requests
from datetime import datetime


class OAuth:
    def __init__(self, domain = "", client_id = "", client_secret = ""):
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = ""
        
        if not os.path.exists(config.LOGS_PATH):
            os.makedirs(config.LOGS_PATH)
            
        logging.basicConfig(filename = config.LOGS_PATH + "ph_api.log")

    def token(self):
        url = self.domain + "/v2/oauth/token"

        try:
            response = requests.post(
                url,
                json = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials"
                    },
            )

            if response.status_code == 200:
                self.access_token = str(response.json()["access_token"])
            else:
                logging.warning("Bad response code while get token " + str(response.code))

        except Exception as e:
            self.access_token = 0
            logging.error(e)


    def graphql(self, query):
        url = self.domain + "/v2/api/graphql"

        if not self.access_token:
            self.token()

        # print(self.access_token)

        try:
            response = requests.post(
                url,
                json = {
                    "query": query,
                    },
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + self.access_token,
                    "Host": "api.producthunt.com"
                    }
            )
        
            if response.status_code == 200:
                # print(response.json())
                return response.json()
            else:
                logging.warning("Bad response code while exec query " + str(response.code))

        except Exception as e:
            self.access_token = 0
            logging.error(e)


    def get_posts(self, count = 0, date = ""):
       
        query = """
            query { 
                posts(first: """ + str(count) + """) { 
                    edges { 
                        node { 
                            id,
                            name,
                            tagline ,
                            description,
                            createdAt,
                            votesCount,
                            website,
                            media {
                                type,
                                url,
                                videoUrl
                            }
                        },
                        cursor
                    }
                }
            }
        """

        posts = self.graphql(query)["data"]["posts"]["edges"]

        posts_dict = list(map(lambda post: {
            "id": post["node"]["id"],
            "name": post["node"]["name"],
            "tagline": post["node"]["tagline"],
            "description": post["node"]["description"],
            "votesCount": post["node"]["votesCount"],
            "createdAt": post["node"]["createdAt"],
            "website": post["node"]["website"],
            "youtube": "",
            "preview": "",
            "media": post["node"]["media"],
            "cursor": post["cursor"]
        }, posts))

        posts_dict = list(map(self.youtube_link_find, posts_dict))

        if date:
            return list(filter(lambda post: post["createdAt"] == date, posts_dict))

        return posts_dict

    def get_posts_by_cursor(self, direction, cursor, count = 1):
        query = """
            query { 
                posts(first: """ + str(count) + """, """ + str(direction) + """: \"""" + str(cursor) + """\") { 
                    edges { 
                        node { 
                            id,
                            name,
                            tagline ,
                            description,
                            votesCount,
                            website,
                            media {
                                type,
                                url,
                                videoUrl
                            }
                        },
                        cursor
                    }
                }
            }
        """

        posts = self.graphql(query)["data"]["posts"]["edges"]

        posts_dict = list(map(lambda post: {
            "id": post["node"]["id"],
            "name": post["node"]["name"],
            "tagline": post["node"]["tagline"],
            "description": post["node"]["description"],
            "votesCount": post["node"]["votesCount"],
            "website": post["node"]["website"],
            "youtube": "",
            "preview": "",
            "media": post["node"]["media"],
            "cursor": post["cursor"]
        }, posts))

        posts_dict = self.youtube_link_find(posts_dict)

        posts_dict = list(map(self.youtube_link_find, posts_dict))

        return posts_dict
      

    def youtube_link_find(self, post):

        if "media" in post:
            for link in post["media"]:
                if link["type"] == "video" and (link["videoUrl"].find("youtube") != -1 or link["videoUrl"].find("youtu.be") != -1):
                    post["youtube"] = link["videoUrl"]
                    break

        return post

    def get_user_auth_url_v2(self, redirect_uri = "", response_type = "", scope = ""):

        url = self.domain + \
            "/v2/oauth/authorize/?" + \
            "client_id=" + self.client_id + \
            "&redirect_uri=" + redirect_uri + \
            "&response_type=" + response_type + \
            "&scope=" + scope

        return url

    def get_user_auth_url_v1(self, redirect_uri = "", response_type = "", scope = ""):

        url = self.domain + \
            "/v1/oauth/authorize?" + \
            "client_id=" + self.client_id + \
            "&redirect_uri=" + redirect_uri + \
            "&response_type=" + response_type + \
            "&scope=" + scope

        return url

# app = OAuth(
#         domain = "https://api.producthunt.com",
#         client_id = "djW1S1EtyMoO8Dm_yB0-ABI8gO0zztBr_Ie2kw2yxNI",
#         client_secret = "F7SJdKC9DXx7YXRpaGis7qQQSl92-VMeagmnQsAwncw",
#     )

# app.token()
# posts = app.get_posts(count = 3, date = datetime.now().date())

# for p in posts:
#     print(p["youtube"])

# 306848

#

# 306895