from enum import IntEnum
import asyncio
import socket
from CommonClient import logger

class MessageType(IntEnum):
      Invalid = -1,
      Test = 0,
      ChestChecked = 1,
      LevelChecked = 2,
      ReceiveAllItems = 3,
      RequestAllItems = 4,
      ReceiveSingleItem = 5,
      StoryChecked = 6,
      ClientCommand = 7,
      Deathlink = 8,
      PortalChecked = 9,
      SendSlotData = 10,
      Victory = 11,
      Handshake = 12
      pass

class SlotDataType(IntEnum):
    KeybladeStats = 0,
    Character = 1,
    SkipDI = 2,
    Exp = 3,

class KHDDDSocket():
    def __init__(self, client, host: str = "127.0.0.1", port:int = 13713):
        self.client: KHDDDContext = client
        self.host: str = host
        self.port: int = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket = None
        self.deathTime = ""
        self.isConnected = False
        self.goaled = False
        pass;

    async def start_server(self):
        self.loop = asyncio.get_event_loop()
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        await self._accept_client()

    async def _accept_client(self):
        """Wait for a client to connect and start a listener task."""
        logger.info("Waiting for KHDDD game connection...")
        while True:
            try:
                self.client_socket, addr = await self.loop.sock_accept(self.server_socket)
                self.isConnected = True
                print(f"Client connected from {addr}")
                self.loop.create_task(self.listen())
                return
            except OSError as e:
                print(f"Socket accept failed ({e}); retrying in 5s")
                await asyncio.sleep(5)

    def _safe_close_client(self):
        """Close the current client socket without killing the server socket."""
        try:
            if self.client_socket:
                self.client_socket.close()
        finally:
            self.client_socket = None
            self.isConnected = False


    async def listen(self):
        while True:
            try:
                message = await self.loop.sock_recv(self.client_socket, 1024)
                if not message:
                    raise ConnectionResetError("Client disconnected")
                msgStr = message.decode("utf-8").replace("\n", "")
                values = msgStr.split(";")
                print("Received message: "+msgStr)
                self.handle_message(values)
            except (ConnectionResetError, OSError) as e:
                logger.info(f"Connection lost, waiting for KHDDD to reconnect")
                self._safe_close_client()
                await self._accept_client()
                return

    def send(self, msgId: int, values: list):
        msg = str(msgId)
        for val in values:
            msg += ";" + str(val)
        msg += "\n"
        self.client_socket.send(msg.encode("utf-8"))
        print("Sent message: "+msg)

    def handle_message(self, message: list[str]):
        if message[0] == '':
            return

        print("Handling message: "+str(message))
        msgType = MessageType(int(message[0]))

        if msgType == MessageType.ChestChecked:
            locid = int(message[1])
            self.client.check_location_IDs.append(locid)
            print("Chest location checked: "+str(locid))

        elif msgType == MessageType.LevelChecked:
            print("Level checked")
            self.client.check_location_IDs.append(int(message[1]))

        elif msgType == MessageType.StoryChecked:
            for x in message:
                if len(x) > 1:
                    locid = int(x)
                    self.client.check_location_IDs.append(locid)
                    print("Story location checked: " + str(locid))

        elif msgType == MessageType.PortalChecked:
            for x in message:
                if len(x) > 1:
                    locid = int(x)
                    self.client.check_location_IDs.append(locid)
                    print("Secret portal location checked: " + str(locid))

        elif msgType == MessageType.Deathlink:
            self.deathTime = message[1]

        elif msgType == MessageType.Victory:
            self.goaled = True

        elif msgType == MessageType.RequestAllItems:
            self.client.get_items()

        elif msgType == MessageType.Handshake:
            print("Attempting to respond to handshake")
            self.send(MessageType.Handshake, [str(self.client.connectedToAp)])
            print("Responded to Handshake")

    def send_singleItem(self, id: int, itemCnt):
        msgCont = [str(id), str(itemCnt)]
        self.send(MessageType.ReceiveSingleItem, msgCont)


    def send_multipleItems(self, items, itemCnt):
        print(f"Sending multiple items {len(items)}")
        values = []

        msgLimit = 3 #Need to cap how long each message can be to prevent data from being lost

        currItemCount = 0
        currMsg = 0

        sendCnt = 0
        for item in items:
            if currItemCount == 0:
                values.append([])
            values[currMsg].append(item.item)
            currItemCount += 1
            sendCnt += 1
            if currItemCount > msgLimit:
                currItemCount = 0
                currMsg = currMsg + 1


        sendMsg = 0
        for msg in values:
            msg.append(itemCnt-(sendCnt-(msgLimit*sendMsg)))
            sendCnt -= 1
            sendMsg += 1
            self.send(MessageType.ReceiveAllItems, msg)

    def send_slot_data(self, slotType, data):
        if slotType == SlotDataType.KeybladeStats:
            splitNums = data.split(",")
            sendVal = [str(slotType)]
            currStat = 1

            sendLimit = 10

            for x in splitNums:
                sendVal.append(x)
                if currStat >= sendLimit:
                    self.send(MessageType.SendSlotData, sendVal)
                    sendVal = [str(slotType)]
                    currStat = 0
                currStat = currStat + 1
        else:
            self.send(MessageType.SendSlotData, [str(slotType), str(data)])

    def send_client_cmd(self, cmdId, extParam):
        values = [str(cmdId)]
        if extParam != "":
            values.append(extParam)
        print(f"Sending client command to player: {cmdId}")
        self.send(MessageType.ClientCommand, values)

    def shutdown_server(self):
        self.client_socket.close()
        self.server_socket.close()