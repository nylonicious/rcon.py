import asyncio
from typing import List

from loguru import logger
from pydantic import ValidationError

from . import exceptions, models
from .client import Client


class Listener(Client):
    def __init__(self, ip, port, password):
        super().__init__(ip, port, password)

    def run(self):
        try:
            self._loop.run_until_complete(self.main())
        except KeyboardInterrupt:
            raise SystemExit

    async def main(self):
        await self.connect()
        tasks = [
            asyncio.create_task(self.server_event_loop()),
            asyncio.create_task(self.server_info_loop()),
        ]
        await asyncio.gather(*tasks)

    async def server_event_loop(self):
        event_handlers = {
            "player.onJoin": self._handle_player_on_join,
            "player.onAuthenticated": self._handle_player_on_auth,
            "player.onDisconnect": self._handle_player_on_disconnect,
            "player.onLeave": self._handle_player_on_leave,
            "player.onSpawn": self._handle_player_on_spawn,
            "player.onKill": self._handle_player_on_kill,
            "player.onChat": self._handle_player_on_chat,
            "player.onSquadChange": self._handle_player_on_squad_or_team_change,
            "player.onTeamChange": self._handle_player_on_squad_or_team_change,
            "punkBuster.onMessage": self._handle_punk_buster_on_message,
            "server.onMaxPlayerCountChange": self._handle_server_on_max_player_count_change,
            "server.onLevelLoaded": self._handle_server_on_level_loaded,
            "server.onRoundOver": self._handle_server_on_round_over,
            "server.onRoundOverPlayers": self._handle_server_on_round_over_players,
            "server.onRoundOverTeamScores": self._handle_server_on_round_over_team_scores,
        }
        while True:
            try:
                event = await self._protocol.listen()
                await event_handlers[event[0]](event)
            except asyncio.TimeoutError:
                pass
            except KeyError:
                logger.error(f"{event} it's not a valid event {self.ip}:{self.port}")

    async def server_info_loop(self):
        while True:
            try:
                server_info = await self.send_command(["serverInfo"])  # noqa
                await asyncio.sleep(10)
            except exceptions.RCONException:
                await self.reconnect()

    async def _handle_player_on_join(self, event: List[str]):
        try:
            on_join = models.PlayerOnJoin(player_name=event[1], player_guid=event[2])
        except ValidationError:
            return

    async def _handle_player_on_auth(self, event: List[str]):
        try:
            on_auth = models.PlayerOnAuthenticated(player_name=event[1])
        except ValidationError:
            return

    async def _handle_player_on_disconnect(self, event: List[str]):
        try:
            on_disconnect = models.PlayerOnDisconnect(player_name=event[1], reason=event[2])
        except ValidationError:
            return

    async def _handle_player_on_leave(self, event: List[str]):
        try:
            offset = int(event[2]) + 4
            event = event[offset:]
            on_leave = models.PlayerOnLeave(
                player_name=event[0],
                player_guid=event[1],
                team_id=event[2],
                squad_id=event[3],
                kills=event[4],
                deaths=event[5],
                score=event[6],
                rank=event[7],
                ping=event[8],
                player_type=event[9],
            )
        except (ValidationError, IndexError):
            # we catch IndexError in case the event has not enough data positions
            return

    async def _handle_player_on_spawn(self, event: List[str]):
        try:
            on_spawn = models.PlayerOnSpawn(player_name=event[1], team_id=event[2])
        except ValidationError:
            return

    async def _handle_player_on_kill(self, event: List[str]):
        try:
            on_kill = models.PlayerOnKill(
                killer_name=event[1], victim_name=event[2], weapon_key=event[3], is_hs=event[4]
            )
        except ValidationError:
            return

    async def _handle_player_on_chat(self, event: List[str]):
        # TODO
        pass

    async def _handle_player_on_squad_or_team_change(self, event: List[str]):
        try:
            on_change = models.PlayerOnSquadOrTeamChange(
                player_name=event[1], team_id=event[2], squad_id=event[3]
            )
        except ValidationError:
            return

    async def _handle_punk_buster_on_message(self, event: List[str]):
        try:
            pb_msg = models.PunkBusterOnMessage(message=event[1])
        except ValidationError:
            return

    async def _handle_server_on_max_player_count_change(self, event: List[str]):
        try:
            on_count_change = models.ServerOnMaxPlayerCountChange(count=event[1])
        except ValidationError:
            return

    async def _handle_server_on_level_loaded(self, event: List[str]):
        try:
            on_level_loaded = models.ServerOnLevelLoaded(
                level_key=event[1],
                game_mode=event[2],
                rounds_player=event[3],
                rounds_total=event[4],
            )
        except ValidationError:
            return

    async def _handle_server_on_round_over(self, event: List[str]):
        try:
            on_round_over = models.ServerOnRoundOver(team_id=event[1])
        except ValidationError:
            return

    async def _handle_server_on_round_over_players(self, event: List[str]):
        # TODO
        pass

    async def _handle_server_on_round_over_team_scores(self, event: List[str]):
        # TODO
        pass
