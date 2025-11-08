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


from typing import Optional
from game_state import DojoGameState, GymMode, ScenarioPhase, CUSTOM_MODES
from constants import (
    SCORE_BOX_START_X, SCORE_BOX_START_Y, SCORE_BOX_WIDTH, SCORE_BOX_HEIGHT,
    CUSTOM_MODE_MENU_START_X, CUSTOM_MODE_MENU_START_Y, CUSTOM_MODE_MENU_WIDTH, CUSTOM_MODE_MENU_HEIGHT,
    CONTROLS_MENU_WIDTH, CONTROLS_MENU_HEIGHT
)
import utils


class ReplayUIRenderer:
    """Handles all UI rendering for the Dojo application"""

    def __init__(self, renderer, game_state: DojoGameState):
        self.renderer = renderer
        self.game_state = game_state

    def render_main_ui(self):
        """Render the main UI elements (score, time, etc.)"""
        if self.game_state.game_phase in [ScenarioPhase.MENU, *CUSTOM_MODES]:
            return
        minutes, seconds = self.game_state.get_time_since_start()
        seconds_str = f"{seconds:02d}"

        # Prepare text content
        text = "Welcome to the Replay mode. Press 'm' to enter menu."
        previous_record = "No record"

        """ Draft menu
        
        Mode: Replay-to-playlist
        Current playlist: *name*
        
        Playlist details:
            ...
        
        Instructions: Go to a replay. Press hotkey 'SAVE_STATE' to add a custom scenario to the playlist.
        
        """

        if self.game_state.gym_mode == GymMode.SCENARIO:
            scores = f"Human: {self.game_state.human_score} Bot: {self.game_state.bot_score}"
            total_score = f"Total: {self.game_state.human_score + self.game_state.bot_score}"
            time_since_start = f"Time: {minutes}:{seconds_str}"
            timeout_enabled = f"Timeouts enabled: {self.game_state.enable_timeouts}"
            freeze_scenario_enabled = f"Scenario frozen: {self.game_state.freeze_scenario}"
            offensive_mode_name = f"Offensive Mode: {self.game_state.offensive_mode.name}"
            defensive_mode_name = f"Defensive Mode: {self.game_state.defensive_mode.name}"
            player_role_name = "offense" if self.game_state.player_offense else "defense"
            player_role_string = f"Player Role: {player_role_name}"
            previous_record = ""
            game_phase_name = f"Game Phase: {self.game_state.game_phase.name}"
        elif self.game_state.gym_mode == GymMode.RACE:
            scores = f"Completed: {self.game_state.human_score}"
            total_score = f"Out of: {self.game_state.num_trials}"
            time_since_start = f"Time: {minutes}:{seconds_str}"
            previous_record_data = self.game_state.get_previous_record()
            if previous_record_data:
                prev_minutes = int(previous_record_data // 60)
                prev_seconds = int(previous_record_data % 60)
                previous_record = f"Previous Record: {prev_minutes}:{prev_seconds:02d}"

        # Render UI elements
        self.renderer.begin_rendering()

        # Main instruction text
        self.renderer.draw_string_2d(20, 50, 1, 1, text, self.renderer.yellow())

        current_y = SCORE_BOX_START_Y + 10

        text_elements = ["wohoo", "replay_mode", "yay"]
        text_elements.extend([scores, total_score, time_since_start, previous_record])
        if self.game_state.gym_mode == GymMode.SCENARIO:
            text_elements.extend([offensive_mode_name, defensive_mode_name, player_role_string, game_phase_name])
            text_elements.extend([timeout_enabled, freeze_scenario_enabled])

        for i, text in enumerate(text_elements):
            self.renderer.draw_string_2d(SCORE_BOX_START_X + 10, current_y, 1, 1, text, self.renderer.white())
            current_y += 30


        self.renderer.end_rendering()

    def render_velocity_vectors(self, rlbot_game_state):
        """Render velocity vectors for all objects in custom mode"""
        if not rlbot_game_state:
            return

        from game_state import CarIndex

        # Human car velocity vector
        if CarIndex.HUMAN.value in rlbot_game_state.cars:
            human_car = rlbot_game_state.cars[CarIndex.HUMAN.value]
            human_start = utils.vector3_to_list(human_car.physics.location)
            human_end_vector = utils.add_vector3(human_car.physics.location, human_car.physics.velocity)
            human_end = utils.vector3_to_list(human_end_vector)
            self.renderer.draw_line_3d(human_start, human_end, self.renderer.white())

        # Ball velocity vector
        if rlbot_game_state.ball:
            ball_start = utils.vector3_to_list(rlbot_game_state.ball.physics.location)
            ball_end_vector = utils.add_vector3(rlbot_game_state.ball.physics.location,
                                                rlbot_game_state.ball.physics.velocity)
            ball_end = utils.vector3_to_list(ball_end_vector)
            self.renderer.draw_line_3d(ball_start, ball_end, self.renderer.white())

        # Bot car velocity vector
        if CarIndex.BOT.value in rlbot_game_state.cars:
            bot_car = rlbot_game_state.cars[CarIndex.BOT.value]
            bot_start = utils.vector3_to_list(bot_car.physics.location)
            bot_end_vector = utils.add_vector3(bot_car.physics.location, bot_car.physics.velocity)
            bot_end = utils.vector3_to_list(bot_end_vector)
            self.renderer.draw_line_3d(bot_start, bot_end, self.renderer.white())
