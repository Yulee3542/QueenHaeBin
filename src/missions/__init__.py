from .track import TrackMission
from .obstacle import ObstacleMission
from .parking import ParkingMission
from .escape import EscapeMission

MISSIONS = {m.name: m for m in (TrackMission, ObstacleMission, ParkingMission, EscapeMission)}
