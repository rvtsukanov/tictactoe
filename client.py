import socket

# from models import Deck
import pickle

from constants import HOST, PORT

# d1 = pickle.dumps(d)
# client.close()


def run_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"Connectiong to: {HOST, PORT}")
    client.connect((HOST, PORT))

    status = client.recv(10000).decode("utf-8")  # who is first ?
    print("Status is: ", status)

    if status == "1":
        val = input()
        client.sendall(val.encode("utf-8"))

    while True:
        val = client.recv(10000).decode("utf-8")

        print(f"Current common sentence is: {val}")

        if val == "done":
            break

        client.sendall(input().encode("utf-8"))

    client.close()


run_client()
