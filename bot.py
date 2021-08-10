import os
import time
import queue
import ph_api
import config
import asyncio
import sqlite3
import telebot
import emoji_regex
# from threading import Thread
import multiprocessing as mp
from datetime import datetime
from libretranslatepy import LibreTranslateAPI
from prepare_markdown import italic, bold, prepare_markdown
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

user_auth_url = ""

bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
conn = sqlite3.connect("ph_ideas.db", check_same_thread = False)
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS  chats
                  (id text, lang text, access_grant text, cursor text, post_order integer)
               """)

# cursor.execute("""CREATE TABLE IF NOT EXISTS posts
#                   (id text, name text, tagline text, description text, url text, lang text)
#                """)

app = ph_api.OAuth(
        domain = config.PH_API_DOMAIN,
        client_id = config.PH_API_CLIENT_ID,
        client_secret = config.PH_API_CLIENT_SECRET
    )

lt = LibreTranslateAPI(config.TRANSLATE_URL)

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

# def translate(lang_from, lang_to, )


def update_lang(user_id, lang):
    sql = "SELECT * FROM chats WHERE id = ?;"
    cursor.execute(sql, [str(user_id)])

    if cursor.fetchone():
        sql = "UPDATE chats SET lang = ? WHERE id = ?;"
        cursor.execute(sql, [lang, str(user_id)])
        conn.commit()


# generate inline keyboard
def lang_gen_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 3

    markup.add(InlineKeyboardButton(text = "EN 🇬🇧", callback_data = "cb_en"), \
               InlineKeyboardButton(text = "RU 🇷🇺", callback_data = "cb_ru"), \
               InlineKeyboardButton(text = "AR 🇦🇪", callback_data = "cb_ar"), \
               InlineKeyboardButton(text = "ZH 🇨🇳", callback_data = "cb_zh"), \
               InlineKeyboardButton(text = "FR 🇫🇷", callback_data = "cb_fr"), \
               InlineKeyboardButton(text = "DE 🇩🇪", callback_data = "cb_de"), \
               InlineKeyboardButton(text = "HI 🇮🇳", callback_data = "cb_hi"), \
               InlineKeyboardButton(text = "ID 🇮🇩", callback_data = "cb_id"), \
               InlineKeyboardButton(text = "GA 🇮🇪", callback_data = "cb_ga"), \
               InlineKeyboardButton(text = "IT 🇮🇹", callback_data = "cb_it"), \
               InlineKeyboardButton(text = "JA 🇯🇵", callback_data = "cb_ja"), \
               InlineKeyboardButton(text = "KO 🇰🇷", callback_data = "cb_ko"), \
               InlineKeyboardButton(text = "PL 🇵🇱", callback_data = "cb_pl"), \
               InlineKeyboardButton(text = "PT 🇵🇹", callback_data = "cb_pt"), \
               InlineKeyboardButton(text = "ES 🇪🇸", callback_data = "cb_es"), \
               InlineKeyboardButton(text = "TR 🇹🇷", callback_data = "cb_tr"), \
               InlineKeyboardButton(text = "VI 🇻🇳", callback_data = "cb_vi"))

    return markup


# generate authorization inline keyboard
def auth_gen_markup(url):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1

    markup.add(InlineKeyboardButton(text = "Authorize", url = url))

    return markup


# generate post inline keyboard for auth users
def auth_post_gen_markup(votes_count):
    markup = InlineKeyboardMarkup()
    markup.row_width = 3

    markup.add(InlineKeyboardButton(text = "🔽", callback_data = "cb_down"), \
               InlineKeyboardButton(text = str(votes_count), callback_data = "cb_vote"), \
               InlineKeyboardButton(text = "🔼", callback_data = "cb_up"))

    return markup


# generate post inline keyboard for auth users with youtube
def auth_post_youtube_gen_markup(votes_count, youtube_link):
    markup = InlineKeyboardMarkup()
    markup.row_width = 3

    markup.add(InlineKeyboardButton(text = "🔽", callback_data = "cb_down"), \
               InlineKeyboardButton(text = str(votes_count), callback_data = "cb_vote"), \
               InlineKeyboardButton(text = "🔼", callback_data = "cb_up"), \
               InlineKeyboardButton(text = "Youtube", url = youtube_link))

    return markup


# generate post inline keyboard for auth users with youtube
def auth_post_youtube_switch_gen_markup(votes_count, youtube_link):
    markup = InlineKeyboardMarkup()
    markup.row_width = 5

    markup.add(InlineKeyboardButton(text = "⬅️", callback_data = "cb_back"), \
               InlineKeyboardButton(text = "🔽", callback_data = "cb_down"), \
               InlineKeyboardButton(text = str(votes_count), callback_data = "cb_vote"), \
               InlineKeyboardButton(text = "🔼", callback_data = "cb_up"), \
               InlineKeyboardButton(text = "➡️", callback_data = "cb_next"), \
               InlineKeyboardButton(text = "Youtube", url = youtube_link))

    return markup


# generate post inline keyboard for not auth users with youtube
def not_auth_post_youtube_switch_gen_markup(votes_count, youtube_link):
    markup = InlineKeyboardMarkup()
    markup.row_width = 3

    markup.add(InlineKeyboardButton(text = "⬅️", callback_data = "cb_back"), \
               InlineKeyboardButton(text = str(votes_count), callback_data = "cb_vote"), \
               InlineKeyboardButton(text = "➡️", callback_data = "cb_next"), \
               InlineKeyboardButton(text = "To top", callback_data = "cb_to_top"), \
               InlineKeyboardButton(text = "Youtube", url = youtube_link))

    return markup


# generate post inline keyboard for not auth users
def not_auth_post_switch_gen_markup(votes_count):
    markup = InlineKeyboardMarkup()
    markup.row_width = 3

    markup.add(InlineKeyboardButton(text = "⬅️", callback_data = "cb_back"), \
               InlineKeyboardButton(text = str(votes_count), callback_data = "cb_vote"), \
               InlineKeyboardButton(text = "➡️", callback_data = "cb_next"), \
               InlineKeyboardButton(text = "To top", callback_data = "cb_to_top"))

    return markup


# generate post inline keyboard for not auth users
def not_auth_post_gen_markup(votes_count):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1

    markup.add(InlineKeyboardButton(text = str(votes_count), callback_data = "cb_vote"))

    return markup


# generate post inline keyboard for not auth users with youtube
def not_auth_post_youtube_gen_markup(votes_count, youtube_link):
    # global votes_count
    markup = InlineKeyboardMarkup()
    markup.row_width = 4

    markup.add(InlineKeyboardButton(text = "Youtube", url = youtube_link), \
               InlineKeyboardButton(text = str(votes_count), callback_data = "cb_vote"),)

    return markup


# handler for inline keyboard
@bot.callback_query_handler(func = lambda call: True)
def callback_query(call):

    if call.data == "cb_en":
        bot.answer_callback_query(call.id, "EN")
        update_lang(call.from_user.id, "en")
    elif call.data == "cb_ru":
        bot.answer_callback_query(call.id, "RU")
        update_lang(call.from_user.id, "ru")
    elif call.data == "cb_ar":
        bot.answer_callback_query(call.id, "AR")
        update_lang(call.from_user.id, "ar")
    elif call.data == "cb_zh":
        bot.answer_callback_query(call.id, "ZH")
        update_lang(call.from_user.id, "zh")
    elif call.data == "cb_fr":
        bot.answer_callback_query(call.id, "FR")
        update_lang(call.from_user.id, "fr")
    elif call.data == "cb_de":
        bot.answer_callback_query(call.id, "DE")
        update_lang(call.from_user.id, "de")
    elif call.data == "cb_hi":
        bot.answer_callback_query(call.id, "HI")
        update_lang(call.from_user.id, "hi")
    elif call.data == "cb_id":
        bot.answer_callback_query(call.id, "ID")
        update_lang(call.from_user.id, "id")
    elif call.data == "cb_ga":
        bot.answer_callback_query(call.id, "GA")
        update_lang(call.from_user.id, "ga")
    elif call.data == "cb_it":
        bot.answer_callback_query(call.id, "IT")
        update_lang(call.from_user.id, "it")
    elif call.data == "cb_ja":
        bot.answer_callback_query(call.id, "JA")
        update_lang(call.from_user.id, "ja")
    elif call.data == "cb_ko":
        bot.answer_callback_query(call.id, "KO")
        update_lang(call.from_user.id, "ko")
    elif call.data == "cb_pl":
        bot.answer_callback_query(call.id, "PL")
        update_lang(call.from_user.id, "pl")
    elif call.data == "cb_pt":
        bot.answer_callback_query(call.id, "PT")
        update_lang(call.from_user.id, "pt")
    elif call.data == "cb_pt":
        bot.answer_callback_query(call.id, "ES")
        update_lang(call.from_user.id, "es")
    elif call.data == "cb_es":
        bot.answer_callback_query(call.id, "TR")
        update_lang(call.from_user.id, "tr")
    elif call.data == "cb_vi":
        bot.answer_callback_query(call.id, "VI")
        update_lang(call.from_user.id, "vi")
    elif call.data == "cb_vote":
        bot.answer_callback_query(call.id, "Vote count")
    elif call.data == "cb_up":
        pass
    elif call.data == "cb_next":
        chat_id = call.from_user.id
        message_id = call.message.id

        sql = "SELECT * FROM chats WHERE id = ?;"
        cursor.execute(sql, [str(chat_id)])

        row = cursor.fetchone()

        if not row:
            print("User not found")
            return None

        lang = row[1]
        post_order = int(row[4])
        next_post_order = post_order - 1

        if next_post_order == 0:
            bot.answer_callback_query(call.id, text = "You have reached the beginning")
            return None

        if next_post_order == 1999:
            sql = "SELECT * FROM last_posts"
            cursor.execute(sql)
            posts = cursor.fetchall()
            max_post_order = int(len(posts) / 17)

            next_post_order = max_post_order

        sql = "SELECT * FROM last_posts WHERE post_order = ? and lang = ?;"
        cursor.execute(sql, [next_post_order, lang])

        post = cursor.fetchone()

        if not post:            
            print("cant find post in last_posts")

            sql = "SELECT * FROM super_old_posts WHERE chat_id = ? and post_order = ?;"
            cursor.execute(sql, [chat_id, str(next_post_order)])
            post = cursor.fetchone()

            print(str(chat_id) + " | " + str(next_post_order))

            if not post:
                print("Upload posts")
                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text = "Prepare\.\.\.", parse_mode="MarkdownV2")
                os.system("python ./upload_prev_posts.py " + str(chat_id) + " before")

                while True:
                    sql = "SELECT * FROM super_old_posts WHERE chat_id = ?;"
                    cursor.execute(sql, [chat_id, ])
                    post = cursor.fetchone()

                    if post:
                        break

                    time.sleep(0.1)

                sql = "SELECT * FROM super_old_posts WHERE chat_id = ?"
                cursor.execute(sql, [chat_id, ])
                max_post_order = len(cursor.fetchone())

                next_post_order = max_post_order

        post_order = post[1]
        name = post[4]
        tagline = post[5]
        description = post[6]
        vote_count = post[7]
        youtube_link = post[8]
        tg_website = post[9]
        cursor_post = post[10]

        sql = "UPDATE chats SET cursor = ?, post_order = ? WHERE id = ?;"
        cursor.execute(sql, [cursor_post, next_post_order, str(chat_id)])
        conn.commit()

        message = name + "\n" + tagline + "\n\n" + description + "\n" + tg_website

        bot.answer_callback_query(call.id)

        if youtube_link:
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text = message, parse_mode="MarkdownV2", disable_web_page_preview = False, reply_markup = not_auth_post_youtube_switch_gen_markup(vote_count, youtube_link))
        else:
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text = message, parse_mode="MarkdownV2", disable_web_page_preview = False, reply_markup = not_auth_post_switch_gen_markup(vote_count))            
                
    elif call.data == "cb_back":
        chat_id = call.from_user.id
        message_id = call.message.id

        sql = "SELECT * FROM chats WHERE id = ?;"
        cursor.execute(sql, [str(chat_id)])

        row = cursor.fetchone()

        if not row:
            print("User not found")
            return None

        lang = row[1]
        post_order = int(row[4])
        prev_post_order = post_order + 1

        if prev_post_order == 900:
            
            print("Upload posts when post order 900")

            sql = "SELECT * FROM last_posts"
            cursor.execute(sql)

            posts_tmp = cursor.fetchall()
            ph_cursor = posts_tmp[len(posts_tmp) - 1][10]

            # bot.edit_message_text(chat_id = chat_id, message_id = message_id, text = "Prepare\.\.\.", parse_mode="MarkdownV2")
            os.system("python ./upload_prev_posts.py " + str(chat_id) + " after " + ph_cursor)

        sql = "SELECT * FROM last_posts WHERE post_order = ? and lang = ?;"
        cursor.execute(sql, [prev_post_order, lang])

        post = cursor.fetchone()

        if not post:            
            if prev_post_order < 2000:
                prev_post_order = 2000
            
            sql = "SELECT * FROM super_old_posts WHERE chat_id = ? and post_order = ?;"
            cursor.execute(sql, [chat_id, str(prev_post_order)])
            post = cursor.fetchone()


            if not post:
                print("Upload posts when end of posts in all db")

                bot.answer_callback_query(call.id, text = "Please wait, posts are being prepared")

                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text = "Prepare\.\.\.", parse_mode="MarkdownV2")
                os.system("python ./upload_prev_posts.py " + str(chat_id) + " after")

                while True:
                    sql = "SELECT * FROM super_old_posts WHERE chat_id = ?;"
                    cursor.execute(sql, [chat_id, ])
                    post = cursor.fetchone()

                    if post:
                        break

                    time.sleep(0.1)

                prev_post_order = 2000

        post_order = post[1]
        name = post[4]
        tagline = post[5]
        description = post[6]
        vote_count = post[7]
        youtube_link = post[8]
        tg_website = post[9]
        cursor_post = post[10]

        sql = "UPDATE chats SET cursor = ?, post_order = ? WHERE id = ?;"
        cursor.execute(sql, [cursor_post, prev_post_order, str(chat_id)])
        conn.commit()

        message = name + "\n" + tagline + "\n\n" + description + "\n" + tg_website

        bot.answer_callback_query(call.id)

        if youtube_link:
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text = message, parse_mode="MarkdownV2", disable_web_page_preview = False, reply_markup = not_auth_post_youtube_switch_gen_markup(vote_count, youtube_link))
        else:
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text = message, parse_mode="MarkdownV2", disable_web_page_preview = False, reply_markup = not_auth_post_switch_gen_markup(vote_count))            

    elif call.data == "cb_to_top":
        bot.answer_callback_query(call.id)
        chat_id = call.from_user.id
        message_id = call.message.id

        sql = "SELECT * FROM chats WHERE id = ?;"
        cursor.execute(sql, [str(chat_id)])

        row = cursor.fetchone()

        if not row:
            print("User not found")
            return None

        lang = row[1]
        dt = datetime.now().strftime("%d-%m-%Y")

        sql = "SELECT * FROM last_posts WHERE post_order = (SELECT MIN(post_order) FROM last_posts WHERE lang = ? and added_to_db_at = ?) and lang = ?;"
        cursor.execute(sql, [lang, dt, lang,])

        post = cursor.fetchone()

        if not post:
            print("Post not found in cb_to_top")
            return None

        post_order = post[1]
        name = post[4]
        tagline = post[5]
        description = post[6]
        vote_count = post[7]
        youtube_link = post[8]
        tg_website = post[9]
        cursor_post = post[10]

        message = name + "\n" + tagline + "\n\n" +  description + "\n" + tg_website

        if youtube_link:
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text = message, parse_mode="MarkdownV2", disable_web_page_preview = False, reply_markup = not_auth_post_youtube_switch_gen_markup(vote_count, youtube_link))
        else:
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text = message, parse_mode="MarkdownV2", disable_web_page_preview = False, reply_markup = not_auth_post_switch_gen_markup(vote_count))


@bot.message_handler(commands=['start'])
def start_cmd(message):
    lang = "en"
    chat_id = message.chat.id

    bot.send_message(chat_id, "Select language", reply_markup = lang_gen_markup())

    # bot.send_message(chat_id, "Auth in Product Hunt for voting", reply_markup = auth_gen_markup(
    #     app.get_user_auth_url_v1("https://19f65f1e43dc.ngrok.io?chat_id=" + str(chat_id), "code", "public+private+write")
    #     ))
    

    sql = "SELECT * FROM chats WHERE id = ?;"
    cursor.execute(sql, [str(chat_id)])

    if not cursor.fetchone():
        sql = "INSERT INTO chats VALUES (?, ?, ?, ?, ?);"
        cursor.execute(sql, [str(chat_id), lang, "", "", ""])
        conn.commit()


@bot.message_handler(commands=['posts'])
def posts_cmd(message):
    chat_id = message.chat.id

    sql = "SELECT * FROM chats WHERE id = ?;"
    cursor.execute(sql, [str(chat_id)])

    row = cursor.fetchone()

    if not row:
        print("User not found cmd posts | 1")
        return None

    lang = row[1]
    dt = datetime.now().strftime("%d-%m-%Y")

    sql = "SELECT * FROM last_posts WHERE post_order = (SELECT MIN(post_order) FROM last_posts WHERE lang = ? and added_to_db_at = ?) and lang = ?;"
    cursor.execute(sql, [lang, dt, lang,])

    post = cursor.fetchone()

    if not post:
        print("Post not found cmd posts | 2")
        return None

    post_order = post[1]
    name = post[4]
    tagline = post[5]
    description = post[6]
    vote_count = post[7]
    youtube_link = post[8]
    tg_website = post[9]
    cursor_post = post[10]

    message = name + "\n" + tagline + "\n\n" +  description + "\n" + tg_website

    sql = "UPDATE chats SET cursor = ?, post_order = ? WHERE id = ?;"
    cursor.execute(sql, [cursor_post, post_order, str(chat_id)])
    conn.commit()

    if youtube_link:
        bot.send_message(chat_id = chat_id, text = message, parse_mode="MarkdownV2", disable_web_page_preview = False, reply_markup = not_auth_post_youtube_switch_gen_markup(vote_count, youtube_link))
    else:
        bot.send_message(chat_id = chat_id, text = message, parse_mode="MarkdownV2", disable_web_page_preview = False, reply_markup = not_auth_post_switch_gen_markup(vote_count))


def translate(text, lang_from, lang_to, regex):
    new_text, emoji_seq = emoji_to_seq(text, regex)
    new_text = lt.translate(text, lang_from, lang_to)

    return seq_to_emoji(new_text, emoji_seq)


async def prepare_post_text(name, tagline, description, lang, tg_website, regex):
    result = (lang, prepare_markdown(name + "\n" + translate(tagline, "en", lang, regex) + "\n\n" + translate(description, "en", lang, regex))  + "\n" + tg_website)
    return result


@bot.message_handler(commands=['tmp'])
def tmp_cmd(message):
    tg_posts = []
    chat_id = message.chat.id
    langs = ["en", "ru", "ar", "zh", "fr", "de", "hi", "id", "ga", "it", "ja", "ko", "pl", "pt", "es", "tr", "vi"]

    app.token()
    posts = app.get_posts(count = 1) # datetime.now().date()

    for post in posts:
        # prepare text for post
        name = bold(prepare_markdown(post["name"]))
        tagline = italic(post["tagline"])
        description = post["description"]
        translate_text_dict = {}

        website = post["website"]
        vote = post["votesCount"]

        tg_website = prepare_markdown(website)

        tg_website = tg_website[0:tg_website.find("?")]
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        tasks = []

        for i in range(17):
            tasks.append(asyncio.ensure_future(prepare_post_text(name, tagline, description, langs[i], tg_website, emoji_regex.EMOJI_REGEXP)))

        results = loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

        for result in results[0]:
            res = result.result()
            lang = res[0]
            text = res[1]
            translate_text_dict[lang] = text

        tg_posts.append((translate_text_dict, vote, post["youtube"], post["preview"], tg_website, post["id"]))

    for post in tg_posts:
        sql = "SELECT * FROM chats;"
        cursor.execute(sql)
        rows = cursor.fetchall()

        if rows:
            for row in rows:
                chat_id = int(row[0])
                lang = row[1]
                message = ""
                translate_text_dict = post[0]

                if str(lang) in translate_text_dict:
                    message = translate_text_dict[lang]
                    message = message
                    
                    votes_count = post[1]
                    youtube_link = post[2]

                    if len(youtube_link) > 0: 
                        bot.send_message(chat_id, message, parse_mode="MarkdownV2", disable_web_page_preview = False, reply_markup = not_auth_post_youtube_gen_markup(votes_count, youtube_link))
                    else:
                        bot.send_message(chat_id, message, parse_mode="MarkdownV2", disable_web_page_preview = False, reply_markup = not_auth_post_gen_markup(votes_count))


@bot.message_handler(commands=['language'])
def language_cmd(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Select language", reply_markup = lang_gen_markup())

@bot.message_handler(func=lambda message: True)
def message_handler(message):
    pass

bot.polling(none_stop=True)


