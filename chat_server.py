import pickle
import socket
import threading

client_rooms = {}
lock = threading.Lock()


class Room:
    def __init__(self, room_name):
        self.room_name = room_name
        self.clients = list()

        self.game_condition = False
        self.used_cities = []
        self.turn = 0
        self.condition = threading.Condition()

    def add_to_room(self, client):
        self.clients.append(client)
        threading.Thread(target=self.start_game, args=(client,)).start()

    def remove_from_room(self, client):
        if self.game_condition:
            self.end_game(client)
        else:
            self.clients.remove(client)

    def start_game(self, client):
        # try:
        if len(self.clients) == 2:
            self.game_condition = True

        while not self.game_condition:
            message = pickle.loads(client.recv(1024))
            if message.startswith("/switch "):
                new_room = message.split(" ")[1]
                if new_room != self.room_name and new_room in rooms and len(rooms[new_room].clients) < 2:
                    with lock:
                        self.remove_from_room(client)
                        rooms[new_room].add_to_room(client)
                        client_rooms[client] = new_room
                    client.send(pickle.dumps(f'Switched to {new_room}'))
                    self.game_condition = False
                    self.turn = 0
                    self.used_cities = []
                    threading.Thread(target=client_handler, args=(client, new_room),
                                     daemon=True).start()
                    return
                else:
                    client.send(pickle.dumps('Room does not exist or is full'))
            if message.startswith("/exit"):
                self.remove_from_room(client)
                client_rooms[client] = None
                self.game_condition = False
                self.turn = 0
                self.used_cities = []
                break

        client_idx = self.clients.index(client)
        opponent_idx = 1 - client_idx
        if client_idx == 0:
            client.send(pickle.dumps("second player is here"))
            self.broadcast("game is starting")

        while self.game_condition:
            if self.game_condition:
                if not self.check_turn(client_idx):
                    client.send(pickle.dumps("wait for your turn"))
                    with self.condition:
                        self.condition.wait()

                message = pickle.loads(client.recv(1024))
                if message.startswith("/switch "):
                    new_room = message.split(" ")[1]
                    if new_room != self.room_name and new_room in rooms and len(rooms[new_room].clients) < 2:
                        with lock:
                            self.remove_from_room(client)
                            rooms[new_room].add_to_room(client)
                            client_rooms[client] = new_room
                        client.send(pickle.dumps(f'Switched to {new_room}'))
                        self.game_condition = False
                        self.turn = 0
                        self.used_cities = []
                        threading.Thread(target=self.start_game, args=(client, new_room),
                                         daemon=True).start()
                        break
                    else:
                        client.send(pickle.dumps('Room does not exist or is full'))
                if message.startswith("/exit"):
                    self.remove_from_room(client)
                    client_rooms[client] = None
                    self.game_condition = False
                    self.turn = 0
                    self.used_cities = []
                    break
                if message.startswith("/ban"):
                    for user in self.clients:
                        if user != client:
                            self.remove_from_room(user)
                            client_rooms[user] = None
                            self.game_condition = False
                            self.turn = 0
                            self.used_cities = []
                            user.send(pickle.dumps("banned"))
                            user.close()

                flag = not self.valid_city(client, message)

                while flag:
                    message = pickle.loads(client.recv(1024))
                    if message.startswith("/switch "):
                        new_room = message.split(" ")[1]
                        if new_room != self.room_name and new_room in rooms and len(rooms[new_room].clients) < 2:
                            with lock:
                                self.remove_from_room(client)
                                rooms[new_room].add_to_room(client)
                                client_rooms[client] = new_room
                            client.send(pickle.dumps(f'Switched to {new_room}'))
                            self.game_condition = False
                            self.turn = 0
                            self.used_cities = []
                            threading.Thread(target=self.start_game, args=(client, new_room),
                                             daemon=True).start()
                            break
                        else:
                            client.send(pickle.dumps('Room does not exist or is full'))
                    if message.startswith("/exit"):
                        self.remove_from_room(client)
                        client_rooms[client] = None
                        self.game_condition = False
                        self.turn = 0
                        self.used_cities = []
                        break
                    if message.startswith("/ban"):
                        for user in self.clients:
                            if user != client:
                                self.remove_from_room(user)
                                client_rooms[user] = None
                                self.game_condition = False
                                self.turn = 0
                                self.used_cities = []
                                user.send(pickle.dumps("banned"))
                                user.close()

                    flag = not self.valid_city(client, message)


                if not flag:
                    data = pickle.dumps(f'opponent city: "{message}"\n'
                                        f'your city must starts on letter: "{message[-1]}"')
                    try:
                        self.clients[opponent_idx].send(data)
                        self.turn = opponent_idx
                        with self.condition:
                            self.condition.notify()
                    except Exception as e:
                        for user in self.clients:
                            if user != client:
                                self.clients.remove(user)
                                client.send(pickle.dumps("You won, your opponent has left("))
                                break
                        self.game_condition = False
                        self.turn = 0
                        self.used_cities = []
                        print(e)
            else:
                threading.Thread(target=self.start_game, args=(client,), daemon=True).start()
        else:
            threading.Thread(target=self.start_game, args=(client,), daemon=True).start()

    # except Exception as e:
    #     print(e)

    def end_game(self, client):
        if len(self.clients) == 2:
            client.send(pickle.dumps("you lose ^-^"))
            self.game_condition = False
            for user in self.clients:
                if user != client:
                    user.send(pickle.dumps("you win"))
            with self.condition:
                self.condition.notify()
        self.clients.remove(client)

        self.turn = 0
        self.used_cities = []

    def broadcast(self, msg):
        for client in self.clients:
            client.send(pickle.dumps(msg))

    def valid_city(self, client, city):
        city = city.lower()
        if not self.used_cities:
            self.used_cities.append(city)
            return True
        elif city[0] == self.used_cities[-1][-1] and city not in self.used_cities:
            self.used_cities.append(city)
            return True
        else:
            (client.send(pickle.dumps(
                f'city starts with wrong letter or it is in "named before", your last letter is {self.used_cities[-1][-1]}')))

    def check_turn(self, idx):
        if self.turn == idx:
            return True

        return False


class Hub:
    def __init__(self):
        self.clients = list()

    def add_to_hub(self, client):
        self.clients.append(client)

    def remove_from_hub(self, client):
        self.clients.remove(client)


rooms = {'hub': Hub(),
         'room1': Room('room1'),
         'room2': Room('room2'),
         'room3': Room('room3')
         }


def client_handler(client_socket, room):
    client_room = room
    if client_room is None:
        rooms['hub'].add_to_hub(client_socket)
        client_rooms[client_socket] = 'hub'
        client_room = 'hub'

    try:
        while client_rooms[client_socket] == 'hub':
            message = pickle.loads(client_socket.recv(1024))
            if message.startswith("/switch "):
                new_room = message.split(" ")[1]
                if new_room in rooms and len(rooms[new_room].clients) < 2:
                    with lock:
                        rooms[client_room].remove_from_hub(client_socket)
                        client_room = new_room
                        rooms[client_room].add_to_room(client_socket)
                        client_rooms[client_socket] = client_room
                    client_socket.send(pickle.dumps(f'Switched to {new_room}'))
                else:
                    client_socket.send(pickle.dumps('Room does not exist or is full'))
            if message.startswith("/exit"):
                rooms[client_room].remove_from_hub(client_socket)
                client_rooms[client_socket] = None
    except Exception as e:
        with lock:
            rooms[client_room].remove_from_hub(client_socket)
            client_rooms[client_socket] = None
        client_socket.close()
        print(e)


def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()

    print(f"Listening on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"client connected: {client_socket, client_address}")
        threading.Thread(target=client_handler, args=(client_socket, None), daemon=True).start()


if __name__ == "__main__":
    start_server('localhost', 12345)
