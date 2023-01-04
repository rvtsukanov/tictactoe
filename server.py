import socket
import threading

from constants import HOST, PORT

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

print(f"Listening: {(HOST, PORT)}")
server.listen()

global common_sentence
common_sentence = ""

all_players = []


def handle(conn, addr):
    print(conn, addr)
    global common_sentence

    if addr == all_players[0]:
        print(f"Checking {addr} == {all_players[-1]}")
        conn.send("1".encode("utf-8"))

    else:
        print(f"Checking {addr} != {all_players[-1]}")
        conn.send("2".encode("utf-8"))

    while True:
        val = conn.recv(10000).decode("utf-8")
        if val == "done":
            break

        common_sentence += val
        conn.sendall(common_sentence.encode("utf-8"))

    # msg = conn.recv(86400)

    # d = pickle.loads(msg)
    # print(msg)
    # d.render_console()
    # conn.close()


while True:
    print(f"Common sentence: {common_sentence}")
    conn, addr = server.accept()
    all_players.append(addr)
    print(f"All players: {all_players}")
    thread = threading.Thread(target=handle, args=(conn, addr)).start()
