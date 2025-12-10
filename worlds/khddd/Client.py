from __future__ import annotations
import sys
import os
import json
import asyncio

from datetime import datetime, UTC, timedelta
from typing import Dict

import ModuleUpdate
ModuleUpdate.update()

import Utils
item_num = 1

deathLink = False
sendDDDCmd = -1
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
    slot_data_info: Dict[str, str] = {}
    _connectedToAp: bool = False
    _connectedToDDD: bool = False
    _confirmed_items_index: int = 0
    _save_file_path: str = None

    def __init__(self, server_address, password, ready_callback=None, error_callback=None):
        super(KHDDDContext, self).__init__(server_address, password)

        # Initialize save file path for tracking confirmed items
        # Use username to create per-slot save file
        save_filename = f"khddd_confirmed_items_{self.username}.json"
        self._save_file_path = Utils.user_path("apkhddd", save_filename)
        os.makedirs(os.path.dirname(self._save_file_path), exist_ok=True)
        self._load_confirmed_items_index()

        #Socket
        self.socket = KHDDDSocket(self)
        asyncio.create_task(self.socket.start_server(), name="KHDDDSocketServer")

    async def server_auth(self, password_requested:bool = False):
        if password_requested and not self.password:
            await super(KHDDDContext, self).server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    async def connection_closed(self):
        self.received_items_IDs = []
        await super(KHDDDContext, self).connection_closed()

    def _load_confirmed_items_index(self):
        """Load the last confirmed items index from local save file."""
        try:
            if os.path.exists(self._save_file_path):
                with open(self._save_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._confirmed_items_index = data.get('confirmed_index', 0)
                    logger.debug(f"Loaded confirmed items index: {self._confirmed_items_index}")
            else:
                self._confirmed_items_index = 0
                logger.debug("No save file found, starting with index 0")
        except (json.JSONDecodeError, IOError, KeyError) as e:
            logger.warning(f"Error loading confirmed items index: {e}, starting fresh")
            self._confirmed_items_index = 0

    def _save_confirmed_items_index(self):
        """Save the confirmed items index to local save file."""
        try:
            data = {'confirmed_index': self._confirmed_items_index}
            with open(self._save_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved confirmed items index: {self._confirmed_items_index}")
        except IOError as e:
            logger.warning(f"Error saving confirmed items index: {e}")

    def update_confirmed_items_index(self, new_index: int):
        """Update the confirmed items index and save to file."""
        if new_index > self._confirmed_items_index:
            self._confirmed_items_index = new_index
            self._save_confirmed_items_index()

    @property
    def connectedToAp(self) -> bool:
        return self._connectedToAp
    @connectedToAp.setter
    def connectedToAp(self, value: bool):
        self._connectedToAp = value

    @property
    def connectedToDDD(self) -> bool:
        return self._connectedToDDD
    @connectedToDDD.setter
    def connectedToDDD(self, value: bool):
        self._connectedToDDD = value

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
            self.connectedToAp = True
            global slotDataSent
            if not slotDataSent:
                if self.connectedToDDD:
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
                else: #Hold slot data until game client connects
                    if 'keyblade_stats' in list(args['slot_data'].keys()):
                        self.slot_data_info['keyblade_stats'] = str(args['slot_data']['keyblade_stats'])
                    self.slot_data_info['character'] = str(args['slot_data']['character'])
                    self.slot_data_info['play_destiny_islands'] = str(args['slot_data']['play_destiny_islands'])
                    self.slot_data_info['exp_multiplier'] = str(args['slot_data']['exp_multiplier'])
                    self.slot_data_info['skip_light_cycle'] = str(args['slot_data']['skip_light_cycle'])
                    self.slot_data_info['fast_go_mode'] = str(args['slot_data']['fast_go_mode'])
                    self.slot_data_info['recipe_reqs'] = str(args['slot_data']['recipe_reqs'])
                    self.slot_data_info['win_con'] = str(args['slot_data']['win_con'])
                    self.slot_data_info['stat_bonus'] = str(args['slot_data']['stat_bonus'])



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

    def get_items(self):
        """Send unconfirmed items to the game client."""
        # Get items that haven't been confirmed as received by the game
        unconfirmed_items = []
        for i, item in enumerate(self.items_received):
            # Only send items after the confirmed index
            if i >= self._confirmed_items_index:
                unconfirmed_items.append(item)

        if not unconfirmed_items:
            logger.debug("No unconfirmed items to send")
            return

        logger.debug(f"Sending {len(unconfirmed_items)} unconfirmed items (confirmed index: {self._confirmed_items_index}, total items: {len(self.items_received)})")

        if len(unconfirmed_items) > 1:
            self.socket.send_multipleItems(unconfirmed_items, len(self.items_received))
        else:
            self.socket.send_singleItem(unconfirmed_items[0].item, len(self.items_received))

        global slotDataSent
        if not slotDataSent:
            if 'keyblade_stats' in self.slot_data_info.keys():
                self.socket.send_slot_data(0, str(self.slot_data_info['keyblade_stats']))
            self.socket.send_slot_data(1, str(self.slot_data_info['character']))
            self.socket.send_slot_data(2, str(self.slot_data_info['play_destiny_islands']))
            self.socket.send_slot_data(3, str(self.slot_data_info['exp_multiplier']))
            self.socket.send_slot_data(4, str(self.slot_data_info['skip_light_cycle']))
            self.socket.send_slot_data(5, str(self.slot_data_info['fast_go_mode']))
            self.socket.send_slot_data(6, str(self.slot_data_info['recipe_reqs']))
            self.socket.send_slot_data(7, str(self.slot_data_info['win_con']))
            self.socket.send_slot_data(8, str(self.slot_data_info['stat_bonus']))
            slotDataSent = True



async def game_watcher(ctx: KHDDDContext):
    while not ctx.exit_event.is_set():

            #Deathlink
            if deathLink and "DeathLink" not in ctx.tags:
                await ctx.update_death_link(deathLink)
            if not deathLink and "DeathLink" in ctx.tags:
                await ctx.update_death_link(deathLink)

            if ctx.socket.deathTime != "" and deathLink:
                death_time = datetime.strptime(ctx.socket.deathTime, '%Y%m%d%H%M%S').replace(tzinfo=UTC)
                time_window = timedelta(seconds=10)
                if (death_time + time_window).timestamp() > ctx.last_death_link:
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