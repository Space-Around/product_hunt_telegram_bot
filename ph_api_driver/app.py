from flask import Flask, request, render_template
import sqlite3

app = Flask(__name__, template_folder='')

conn = sqlite3.connect("../telegram_chats.db", check_same_thread = False)
cursor = conn.cursor()

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        request_data = request.args.to_dict()
        print(request_data)
        print(len(request_data))
        print("code" in request_data)
        if len(request_data) and "code" in request_data and "chat_id" in request_data:
            access_grant = request_data["code"]
            chat_id = request_data["chat_id"]

            sql = "SELECT * FROM chats WHERE id = ?;"
            cursor.execute(sql, [str(chat_id)])
            row = cursor.fetchone()

            if row:
                sql = "UPDATE chats SET access_grant = ? WHERE id = ?;"
                cursor.execute(sql, [access_grant, str(chat_id)])
                conn.commit()     

                return render_template("success.html", title = 'index')
            else:
                return render_template("error_chat_id.html", title = 'index')

    return render_template("index.html", title = 'index')

if __name__ == "__main__":
    app.run(debug = True)
    # access grant
    # https://api.producthunt.com/v1/oauth/authorize?client_id=lgeNvVfmr3W8ELkpDEOptvA9SWw-2r4TikVHBYhUuC4&redirect_uri=https://19f65f1e43dc.ngrok.io&response_type=code&scope=public+private+write
                                                            #  lgeNvVfmr3W8ELkpDEOptvA9SWw-2r4TikVHBYhUuC4 

    # token
    # https://api.producthunt.com/v1/oauth/token?client_id=lgeNvVfmr3W8ELkpDEOptvA9SWw-2r4TikVHBYhUuC4&redirect_uri=https://19f65f1e43dc.ngrok.io&response_type=code&scope=public+private