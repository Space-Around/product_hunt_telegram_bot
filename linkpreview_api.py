import config
import random
import logging
import requests

class linkPreview:
    def __init__(self, domain = "", key = "", preview_path = ""):
        self.domain = domain
        self.key = key
        self.preview_path = preview_path

        logging.basicConfig(filename = config.LOGS_PATH + "linkpreview_api.log")

    def get_preview(self, link = ""):
        try:
            url = self.domain

            response = requests.get(
                url,
                params={
                    "key": self.key,
                    "q": link
                    }
            )

            preview_link = response.json()["image"]

            preview_file = requests.get(preview_link)
            file_name = str(random.randint(1000, 9999))
            open(self.preview_path + file_name + ".png", 'wb').write(preview_file.content)

            return file_name

        except Exception as e:
            logging.error(e)

            return None


# lp = linkPreview(
#     domain = "http://api.linkpreview.net/",
#     key = "5ba4cb1c69c019415a2a994a118ebc72",
#     preview_path = "C:\\Users\\mviksna\\Desktop\\prj\\product_hunt_projects_bot\\preview\\"
# )

# print(lp.get_preview("https://removal.ai/download/?ref=producthunt"))

        



        

