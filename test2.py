import argparse
parser = argparse.ArgumentParser()
parser.add_argument('chat_id', help="Enter number to triple it.")
parser.add_argument('direction', help="Enter number to triple it.")
args = parser.parse_args()

print(args.chat_id)
print(args.direction)