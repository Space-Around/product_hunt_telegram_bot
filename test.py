import emoji_regex
import config
import time
import asyncio
import queue
from threading import Thread
from libretranslatepy import LibreTranslateAPI


lt = LibreTranslateAPI(config.TRANSLATE_URL)

text = "🧠 Heights Smart supplements and clever content for the brain, intelligently delivered. Think of our team as your personal brain coach, with one goal in mind; to feed your brain and help you reach your Heights.🧠"

def seq_to_emoji(text, emoji_seq):

    while text.find("[-101]") != -1:
        text = text.replace("[-101]", emoji_seq[0])
        emoji_seq.pop(0)

    return text


def emoji_to_seq(text, regex):
    emoji_seq = []

    for i in range(0, len(text)):
        emoji_char = regex.findall(text[i])

        if emoji_char:
            emoji_seq.append(emoji_char[0])

    text = regex.sub('[-101]', text)

    return text, emoji_seq


async def test(text):
    # start_time = time.time()
    text, emoji_seq = emoji_to_seq(text, emoji_regex.EMOJI_REGEXP)

    text = lt.translate(text, "en", "ru")

    text = seq_to_emoji(text, emoji_seq)

    # print("--- %s seconds ---" % (time.time() - start_time))

    return text


# que = queue.Queue()

# for i in range(0, 5):
#     t = Thread(target = lambda q, args: q.put(test(args)), args = (que, text))
#     t.start() 
#     t.join()

# while not que.empty():
#     print(que.get())

# # print("1234")

# # print(text)

# async def asynchronous(text):
#     futures = [test(text) for i in range(17)]

#     done, pending = await asyncio.wait(futures)

if __name__ == '__main__':
    start_time = time.time()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks = []

    for i in range(17):
        tasks.append(asyncio.ensure_future(test(text)))

    result = loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    [print(elem.result()) for elem in result[0]]

    print("--- %s seconds ---" % (time.time() - start_time))

