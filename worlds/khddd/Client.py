from __future__ import annotations
import sys
import asyncio
import time

from calendar import timegm

import ModuleUpdate
ModuleUpdate.update()

import Utils
item_num = 1

deathLink = False
sendDDDCmd = -1
dddConnected = -1
slotDataSent = False

from .Socket import KHDDDSocket

if __name__ == "__main__":
    Utils.init_logging("KHDDDClient", exception_logger="Client")

from NetUtils import NetworkItem, ClientStatus
from CommonClient import gui_enabled, logger, get_base_parser, ClientCommandProcessor, \
    CommonContext, server_loop

def check_stdin() -> None:
    if Utils.is_windows and sys.stdin:
        print("WARNING: Console input is not routed reliably on Windows, use the GUI instead.")

class KHDDDClientCommandProcessor(ClientCommandProcessor):

    def __init__(self, ctx):
        super().__init__(ctx)

    def _cmd_drop(self):
        """Instantly drops the player."""
        global sendDDDCmd
        sendDDDCmd = 0
        self.output("Dropping player.")

    def _cmd_unstuck(self):
        """Sends the inactive character to the World Map."""
        global sendDDDCmd
        sendDDDCmd = 1
        self.output("Sending inactive character to the World Map.")

    def _cmd_deathlink(self):
        """Toggles Deathlink"""
        global deathLink
        global sendDDDCmd
        if deathLink:
            deathLink = False
            self.output(f"Death Link turned off")
            sendDDDCmd = 3
        else:
            deathLink = True
            sendDDDCmd = 3
            self.output(f"Death Link turned on")



class KHDDDContext(CommonContext):
    command_processor: int = KHDDDClientCommandProcessor
    game = "Kingdom Hearts Dream Drop Distance"
    items_handling = 0b111 #Attempt full remote

    #Vars for socket
    socket: KHDDDSocket = None
    check_location_IDs = []
    received_items_IDs = []

    def __init__(self, server_address, password):
        super(KHDDDContext, self).__init__(server_address, password)

        #Socket
        self.socket = KHDDDSocket(self)
        asyncio.create_task(self.socket.start_server(), name="KHDDDSocketServer")

    async def server_auth(self, password_requested:bool = False):
        if password_requested and not self.password:
            await super(KHDDDContext, self).server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    async def connection_closed(self):
        await super(KHDDDContext, self).connection_closed()
        #for root, dirs, files in os.walk(self.game_communication_path):
        #    for file in files:
        #        if file.find("obtain") <= -1:
        #            os.remove(root + "/" + file)
        #global item_num
        #item_num = 1



    @property
    def endpoints(self):
        if self.server:
            return [self.server]
        else:
            return []

    async def shutdown(self):
        await super(KHDDDContext, self).shutdown()
        self.socket.shutdown_server()
    
    def on_package(self, cmd: str, args: dict):
        if cmd in {"Connected"}:
            global slotDataSent
            if not slotDataSent:
                if "keyblade_stats" in list(args['slot_data'].keys()):
                    self.socket.send_slot_data(0, str(args['slot_data']['keyblade_stats']))
                self.socket.send_slot_data(1, str(args['slot_data']['character']))
                self.socket.send_slot_data(2, str(args['slot_data']['play_destiny_islands']))
                self.socket.send_slot_data(3, str(args['slot_data']['exp_multiplier']))
                self.socket.send_slot_data(4, str(args['slot_data']['skip_light_cycle']))
                self.socket.send_slot_data(5, str(args['slot_data']['fast_go_mode']))
                self.socket.send_slot_data(6, str(args['slot_data']['recipe_reqs']))
                self.socket.send_slot_data(7, str(args['slot_data']['win_con']))
                self.socket.send_slot_data(8, str(args['slot_data']['stat_bonus']))


                slotDataSent = True
            pass

        if cmd in {"ReceivedItems"}:
            for item in args['items']:
                self.received_items_IDs.append(NetworkItem(*item).item)
            if len(args['items']) > 1:
                self.socket.send_multipleItems(args['items'], len(self.received_items_IDs))
            else:
                self.socket.send_singleItem(args['items'][0].item, len(self.received_items_IDs))
            pass


    def on_deathlink(self, data: dict[str, object]):
        self.last_death_link = max(data["time"], self.last_death_link)
        text = data.get("cause", "")
        if text:
            logger.info(f"Deathlink: {text}")
        else:
            logger.info(f"Deathlink: Received from {data['source']}")
        #Send to the game
        self.socket.send(8, [str(int(data["time"]))])

    def run_gui(self):
        """Import kivy UI system and start running it as self.ui_task"""
        from kvui import GameManager

        class KHDDDManager(GameManager):
            logging_pairs = [
                ("Client", "Archipelago")
            ]
            base_title = "Archipelago KHDDD Client"

        self.ui = KHDDDManager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name="UI")

async def game_watcher(ctx: KHDDDContext):
    while not ctx.exit_event.is_set():
        victory = False

        #Deathlink
        if deathLink and "DeathLink" not in ctx.tags:
            await ctx.update_death_link(deathLink)
        if not deathLink and "DeathLink" in ctx.tags:
            await ctx.update_death_link(deathLink)

        if ctx.socket.deathTime != "" and deathLink:
            if timegm(time.strptime(ctx.socket.deathTime, '%Y%m%d%H%M%S')) > ctx.last_death_link and int(time.time()) % int(timegm(time.strptime(ctx.socket.deathTime, '%Y%m%d%H%M%S'))) < 10:
                logger.info(f"Sending deathlink...")
                await ctx.send_death(death_text="Character defeated")



        #Send a command to the game
        global sendDDDCmd
        if sendDDDCmd > -1:
            if (sendDDDCmd == 3):
                ctx.socket.send_client_cmd(sendDDDCmd, str(deathLink))
            else:
                ctx.socket.send_client_cmd(sendDDDCmd, "")
            sendDDDCmd = -1

        #Check for game connection
        global dddConnected
        if dddConnected == -1:
            logger.info("Searching for KHDDD Game Client...Please load your save file before Connecting.")
            dddConnected = 0
        elif dddConnected == 0:
            if ctx.socket.isConnected:
                logger.info(f"KHDDD Game Client Found")
                dddConnected = 1
        elif dddConnected == 1: #Check for game completion
            if ctx.socket.goaled and not ctx.finished_game:
                await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                ctx.finished_game = True

        ctx.locations_checked = ctx.check_location_IDs
        message = [{"cmd": 'LocationChecks', "locations": ctx.check_location_IDs}]
        await ctx.send_msgs(message)
        await asyncio.sleep(0.5)

def launch():

    async def main(args):
        ctx = KHDDDContext(args.connect, args.password)
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        progression_watcher = asyncio.create_task(
                game_watcher(ctx), name="KHDDDProgressionWatcher")

        await ctx.exit_event.wait()
        ctx.server_address = None

        await progression_watcher

        await ctx.shutdown()

    import colorama

    parser = get_base_parser(description="KHDDD Client, for text interfacing.")

    args, rest = parser.parse_known_args()
    colorama.just_fix_windows_console()
    asyncio.run(main(args))
    colorama.deinit()