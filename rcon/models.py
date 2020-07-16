import pydantic

# custom validator for EA GUID
EAGUID = pydantic.constr(regex=r"EA_[0-9A-F]{32}")


class PlayerOnJoin(pydantic.BaseModel):
    player_name: str
    player_guid: EAGUID


class PlayerOnAuthenticated(pydantic.BaseModel):
    player_name: str


class PlayerOnDisconnect(pydantic.BaseModel):
    player_name: str
    reason: str


class PlayerOnLeave(pydantic.BaseModel):
    player_name: str
    player_guid: EAGUID
    team_id: int
    squad_id: int
    kills: int
    deaths: int
    score: int
    rank: int
    ping: int
    player_type: int


class PlayerOnSpawn(pydantic.BaseModel):
    player_name: str
    team_id: int


class PlayerOnKill(pydantic.BaseModel):
    killer_name: str
    victim_name: str
    weapon_key: str
    is_hs: bool


# TODO fix target
class PlayerOnChat(pydantic.BaseModel):
    source: str
    message: str
    target: str


class PlayerOnSquadOrTeamChange(pydantic.BaseModel):
    player_name: str
    team_id: int
    squad_ind: int


class PunkBusterOnMessage(pydantic.BaseModel):
    message: str


class ServerOnMaxPlayerCountChange(pydantic.BaseModel):
    count: int


class ServerOnLevelLoaded(pydantic.BaseModel):
    level_key: str
    game_mode: str
    rounds_played: int
    rounds_total: int


class ServerOnRoundOver(pydantic.BaseModel):
    team_id: int


# TODO
class ServerOnRoundOverPlayers(pydantic.BaseModel):
    pass


# TODO
class ServerOnRoundOverTeamScores(pydantic.BaseModel):
    pass
