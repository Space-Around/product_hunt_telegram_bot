import time
import ph_api
import config
import sqlite3
import asyncio
import emoji_regex
from datetime import datetime
from libretranslatepy import LibreTranslateAPI
from prepare_markdown import italic, bold, prepare_markdown

def seq_to_emoji(text, emoji_seq):

   while text.find("[-101]") != -1:
      text = text.replace("[-101]", emoji_seq[0])
      emoji_seq.pop(0)

   return text

def emoji_to_seq(text, regex):
   emoji_seq = []
   new_text = ""
   text_tuple = tuple(text)

   for i in range(0, len(text_tuple)):
      emoji_char = regex.findall(text_tuple[i])

      if emoji_char:
         emoji_seq.append(emoji_char[0])

   new_text = regex.sub('[-101]', text)

   return new_text, emoji_seq

async def task(ph_post_id, lang, name, tagline,
               description, vote_count, youtube_link,
               website, cursor_post, post_order,
               cursor, conn, lt):
               
   name = bold(prepare_markdown(name))
   tagline = italic(prepare_markdown(tagline))
   description, emoji_seq = emoji_to_seq(description, emoji_regex.EMOJI_REGEXP)
   description = prepare_markdown(seq_to_emoji(lt.translate(description, "en", lang), emoji_seq))
   dt = datetime.now().strftime("%d-%m-%Y")

   sql = "INSERT INTO last_posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
   cursor.execute(sql, [None, str(post_order), str(ph_post_id), lang, name, tagline, description, vote_count, youtube_link, website, cursor_post, dt])
   conn.commit()

def main():
   app = ph_api.OAuth(
         domain = config.PH_API_DOMAIN,
         client_id = config.PH_API_CLIENT_ID,
         client_secret = config.PH_API_CLIENT_SECRET
      )

   lt = LibreTranslateAPI(config.TRANSLATE_URL)

   conn = sqlite3.connect("ph_ideas.db", check_same_thread = False)
   cursor = conn.cursor()

   cursor.execute("DROP TABLE IF EXISTS last_posts")

   cursor.execute("""CREATE TABLE IF NOT EXISTS last_posts
                     (
                     id INTEGER PRIMARY KEY,
                     post_order TEXT,
                     ph_id TEXT,
                     lang TEXT,
                     title TEXT,
                     tag TEXT,
                     description TEXT,
                     votes TEXT,
                     youtube TEXT,
                     website TEXT,
                     cursor TEXT,
                     added_to_db_at TEXT)
                  """)

   langs = ["en", "ru", "ar", "zh", "fr", "de", "hi", "id", "ga", "it", "ja", "ko", "pl", "pt", "es", "tr", "vi"]

   # get posts from product hunt
   posts = app.get_posts(20)

   post_order = 0
   dt_old = ""

   sql = "SELECT * FROM last_posts"
   cursor.execute(sql)

   rows = cursor.fetchall()

   if rows:
      last_index = len(rows) - 1
      post_order = int(rows[last_index][1])
      dt_old = rows[0][10]
   else:
      post_order = 1

   for post in posts:
      ph_post_id = post["id"]
      name = post["name"]
      tagline = post["tagline"]
      description = post["description"]
      cursor_post = post["cursor"]
      youtube_link = ""

      if "youtube" in post and len(post["youtube"]):
         youtube_link = post["youtube"]

      website = post["website"]
      vote_count = post["votesCount"]

      tg_website = prepare_markdown(website)

      tg_website = tg_website[0:tg_website.find("?")]

      # for i in range(0, 17):
      #    task(id_post, langs[i], name, tagline, description, vote_count, youtube_link, website, cursor_post, cursor)

      # check if post already exist in db then don't add
      sql = "SELECT * FROM last_posts WHERE ph_id = ?"
      cursor.execute(sql, [ph_post_id, ])

      if cursor.fetchone():
         return None
         
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)

      tasks = []

      # paralleling tasks by languages
      for i in range(0, 17):
         tasks.append(
            asyncio.ensure_future(
               task(
                  ph_post_id, langs[i], name,
                  tagline, description, vote_count,
                  youtube_link, tg_website, cursor_post,
                  post_order, cursor, conn,
                  lt)))

      loop.run_until_complete(asyncio.wait(tasks))
      loop.close()

      post_order = post_order + 1

   # delete oldest posts when posts is more than 1000
   sql = "SELECT * FROM last_posts"
   cursor.execute(sql)

   posts = cursor.fetchall()

   if not posts:
      return None

   unic_posts = len(posts) / 17

   if (unic_posts) <= 1000:
      return None

   sql = "DELETE FROM last_posts WHERE added_to_db_at = ?"
   cursor.execute(sql, [dt_old])
   conn.commit()

if __name__ == "__main__":
   main()