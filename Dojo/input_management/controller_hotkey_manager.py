import os
import threading
import time
import pygame

# This is needed to capture input even when Rocket League is in focus
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"


class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 25)

    def tprint(self, screen, text):
        text_bitmap = self.font.render(text, True, (0, 0, 0))
        screen.blit(text_bitmap, (self.x, self.y))
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10


class ControllerHotkeyManager:
    # Standard SDL Game Controller button mapping
    # This works for most modern controllers (Xbox, PlayStation, Switch Pro, etc.)
    BUTTON_NAMES = {
        0: "A",  # Cross on PS, B on Nintendo
        1: "B",  # Circle on PS, A on Nintendo
        2: "X",  # Square on PS, Y on Nintendo
        3: "Y",  # Triangle on PS, X on Nintendo
        4: "LB",  # L1
        5: "RB",  # R1
        6: "Back",  # Select/Share
        7: "Start",  # Start/Options
        8: "LS",  # L3 (Left stick click)
        9: "RS",  # R3 (Right stick click)
        10: "Guide",  # Home/PS button (if accessible)
        11: "Misc1",  # Share/Capture button
    }

    # D-pad hat directions
    HAT_NAMES = {
        (0, 1): "D-Up",
        (0, -1): "D-Down",
        (-1, 0): "D-Left",
        (1, 0): "D-Right",
        (-1, 1): "D-Up-Left",
        (1, 1): "D-Up-Right",
        (-1, -1): "D-Down-Left",
        (1, -1): "D-Down-Right",
        (0, 0): None,
    }

    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.thread = None
        self.running = False
        self.hotkeys = {}
        self.keys_pressed = []
        self.dpad_pressed = []
        self.joysticks = {}

        # Rebinding state
        self.rebind_mode = False
        self.rebind_result = None
        self.rebind_lock = threading.Lock()
        self.rebind_event = threading.Event()

        # Debug-only components
        self.screen = None
        self.clock = None
        self.text_print = None

    def get_button_name(self, button_index, joystick):
        """Get a human-readable name for a button."""
        # For controllers with more buttons than our standard mapping
        if button_index in self.BUTTON_NAMES:
            return self.BUTTON_NAMES[button_index]
        else:
            return f"Button {button_index}"

    def get_hat_name(self, hat_position):
        """Get a human-readable name for a hat/d-pad position."""
        return self.HAT_NAMES.get(hat_position, None)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        return self.thread

    def stop(self):
        self.running = False
        self.thread.join()

    def get_keys_pressed(self):
        return self.keys_pressed

    def register_hotkey(self, hotkey, callback):
        self.hotkeys[hotkey] = callback

    def wait_for_rebind(self, timeout=None):
        """
        Wait for a controller button press and return the button name.
        This method blocks until a button is pressed or timeout is reached.

        Args:
            timeout: Optional timeout in seconds. None means wait indefinitely.

        Returns:
            str: The name of the button that was pressed, or None if timeout occurred.
        """
        with self.rebind_lock:
            self.rebind_mode = True
            self.rebind_result = None
            self.rebind_event.clear()

        # Wait for the pygame thread to detect a button press
        button_detected = self.rebind_event.wait(timeout=timeout)

        with self.rebind_lock:
            self.rebind_mode = False
            result = self.rebind_result
            self.rebind_result = None

        return result if button_detected else None

    def cancel_rebind(self):
        """Cancel an ongoing rebind operation."""
        with self.rebind_lock:
            self.rebind_mode = False
            self.rebind_result = None
        self.rebind_event.set()

    def _initialize_pygame(self):
        """Initialize pygame and debug window if debug mode is enabled."""
        pygame.init()

        if self.debug_mode:
            self.screen = pygame.display.set_mode((600, 600))
            pygame.display.set_caption("RLDojo Controller Hotkey Manager")
            self.clock = pygame.time.Clock()
            self.text_print = TextPrint()

    def _process_events(self):
        """Process all pygame events and update joystick state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.JOYBUTTONDOWN:
                self._handle_button_down(event)
            elif event.type == pygame.JOYBUTTONUP:
                self._handle_button_up(event)
            elif event.type == pygame.JOYHATMOTION:
                self._handle_hat_motion(event)
            elif event.type == pygame.JOYDEVICEADDED:
                self._handle_device_added(event)
            elif event.type == pygame.JOYDEVICEREMOVED:
                self._handle_device_removed(event)

    def _handle_button_down(self, event):
        """Handle button press events."""
        joystick = self.joysticks[event.instance_id]
        button_name = self.get_button_name(event.button, joystick)
        print(f"Button pressed: {button_name} (index {event.button})")

        # Check if we're in rebind mode
        with self.rebind_lock:
            if self.rebind_mode:
                self.rebind_result = button_name
                self.rebind_event.set()
                return

        # Normal hotkey handling
        if button_name in self.hotkeys:
            self.hotkeys[button_name]()

    def _handle_button_up(self, event):
        """Handle button release events."""
        joystick = self.joysticks[event.instance_id]
        button_name = self.get_button_name(event.button, joystick)
        print(f"Button released: {button_name} (index {event.button})")

    def _handle_hat_motion(self, event):
        """Handle D-pad motion events."""
        hat_name = self.get_hat_name(event.value)
        if hat_name:
            print(f"D-pad: {hat_name}")

            # Check if we're in rebind mode
            with self.rebind_lock:
                if self.rebind_mode:
                    self.rebind_result = hat_name
                    self.rebind_event.set()
                    return

    def _handle_device_added(self, event):
        """Handle joystick connection events."""
        joy = pygame.joystick.Joystick(event.device_index)
        self.joysticks[joy.get_instance_id()] = joy
        print(f"Joystick {joy.get_instance_id()} connected")

    def _handle_device_removed(self, event):
        """Handle joystick disconnection events."""
        del self.joysticks[event.instance_id]
        print(f"Joystick {event.instance_id} disconnected")

    def _update_input_state(self):
        """Update the current input state by polling all connected joysticks."""
        self.keys_pressed.clear()
        self.dpad_pressed.clear()

        for joystick in self.joysticks.values():
            # Check button states
            buttons = joystick.get_numbuttons()
            for i in range(buttons):
                if joystick.get_button(i) == 1:
                    button_name = self.get_button_name(i, joystick)
                    self.keys_pressed.append(button_name)

            # Check hat/D-pad states
            hats = joystick.get_numhats()
            for i in range(hats):
                hat = joystick.get_hat(i)
                hat_name = self.get_hat_name(hat)
                if hat_name:
                    self.dpad_pressed.append(hat_name)

    def _debug_draw(self):
        """Draw debug information to the screen (only if debug mode is enabled)."""
        if not self.debug_mode:
            return

        self.screen.fill((255, 255, 255))
        self.text_print.reset()

        joystick_count = pygame.joystick.get_count()
        self.text_print.tprint(self.screen, f"Number of joysticks: {joystick_count}")
        self.text_print.indent()

        for joystick in self.joysticks.values():
            self._debug_draw_joystick(joystick)

        pygame.display.flip()

    def _debug_draw_joystick(self, joystick):
        """Draw information about a single joystick."""
        jid = joystick.get_instance_id()

        self.text_print.tprint(self.screen, f"Joystick {jid}")
        self.text_print.indent()

        # Basic info
        name = joystick.get_name()
        self.text_print.tprint(self.screen, f"Joystick name: {name}")

        guid = joystick.get_guid()
        self.text_print.tprint(self.screen, f"GUID: {guid}")

        power_level = joystick.get_power_level()
        self.text_print.tprint(self.screen, f"Joystick's power level: {power_level}")

        # Axes
        self._debug_draw_axes(joystick)

        # Buttons
        self._debug_draw_buttons(joystick)

        # Hats
        self._debug_draw_hats(joystick)

        self.text_print.unindent()

    def _debug_draw_axes(self, joystick):
        """Draw axis information for a joystick."""
        axes = joystick.get_numaxes()
        self.text_print.tprint(self.screen, f"Number of axes: {axes}")
        self.text_print.indent()

        for i in range(axes):
            axis = joystick.get_axis(i)
            self.text_print.tprint(self.screen, f"Axis {i} value: {axis:>6.3f}")

        self.text_print.unindent()

    def _debug_draw_buttons(self, joystick):
        """Draw button information for a joystick."""
        buttons = joystick.get_numbuttons()
        self.text_print.tprint(self.screen, f"Number of buttons: {buttons}")
        self.text_print.indent()

        for i in range(buttons):
            button = joystick.get_button(i)
            button_name = self.get_button_name(i, joystick)
            if button == 1:
                self.text_print.tprint(self.screen, f"{button_name} (btn {i}): PRESSED")
            else:
                self.text_print.tprint(self.screen, f"{button_name} (btn {i}): {button}")

        self.text_print.unindent()

    def _debug_draw_hats(self, joystick):
        """Draw hat/D-pad information for a joystick."""
        hats = joystick.get_numhats()
        self.text_print.tprint(self.screen, f"Number of hats: {hats}")
        self.text_print.indent()

        for i in range(hats):
            hat = joystick.get_hat(i)
            hat_name = self.get_hat_name(hat)
            if hat_name:
                self.text_print.tprint(self.screen, f"Hat {i}: {hat_name} {str(hat)}")
            else:
                self.text_print.tprint(self.screen, f"Hat {i} value: {str(hat)}")

        self.text_print.unindent()

    def _run(self):
        """Main loop for controller input handling."""
        self._initialize_pygame()

        while self.running:
            self._process_events()
            self._update_input_state()

            if self.debug_mode:
                self._debug_draw()
                self.clock.tick(30)

        pygame.quit()


if __name__ == "__main__":
    # Enable debug mode when running standalone
    manager = ControllerHotkeyManager(debug_mode=False)
    thread = manager.start()
    try:
        for i in range(10):
            time.sleep(10)
            print(manager.keys_pressed)
    except KeyboardInterrupt:
        manager.stop()
    manager.stop()