from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Optional

from rlbot.utils.game_state_util import CarState, GameState, BallState

from custom_scenario import CustomScenario
from game_modes import BaseGameMode

if TYPE_CHECKING:
    from game_state import DojoGameState
    from rlbot.utils.structures.game_interface import GameInterface
    from rlbot.utils.structures.game_data_struct import GameTickPacket

class EditPhase(Enum):
    # INIT = -1
    # SETUP = 0
    # ACTIVE = 1
    # MENU = 2
    # EXITING_MENU = 3
    # FINISHED = 4
    IN_REPLAY = 5  # DRAFT: Shows playlist details and hotkeys in UI
    EDIT_MODE = 6  # DRAFT: Use hotkeys to switch between scenarios. Edit or delete scenarios.

class PlaylistEditMode(BaseGameMode):
    """"""
    
    def __init__(self, game_state: 'DojoGameState', game_interface: 'GameInterface'):
        super().__init__(game_state, game_interface)
        self.game_state = game_state
        self.game_interface = game_interface
        self.current_packet: Optional['GameTickPacket'] = None

    def update(self, packet: 'GameTickPacket') -> None:
        """Update the game mode with the current packet"""
        self.current_packet = packet

    def initialize(self) -> None:
        """Initialize the game mode"""
        pass

    def cleanup(self) -> None:
        """Clean up resources when switching away from this mode"""
        pass
    
    def get_current_game_state(self) -> GameState:
        packet = self.current_packet
        car_states = {}
        # Player indices should match already? The first index is the human player.
        for i, player_info in enumerate(packet.game_cars):
            car_states[i] = CarState(physics=player_info.physics, boost_amount=player_info.boost,
                                     jumped=player_info.jumped, double_jumped=player_info.double_jumped)
        ball_state = BallState(physics=packet.game_ball.physics)
        rlbot_game_state = GameState(ball=ball_state, cars=car_states)
        return rlbot_game_state
