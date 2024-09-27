"""Module which contains the Servo class, representing a servo motor that controls the extension of the airbrakes."""

import gpiozero


class Servo:
    """
    A custom class that represents a servo motor, controlling the extension of the airbrakes.
    """

    __slots__ = ("current_extension", "max_extension", "min_extension", "min_nobuzz", "servo")

    def __init__(self, gpio_pin_number: int, max_nobuzz: float, min_extension: float, max_extension: float, min_nobuzz: float, pin_factory=None):
        self.min_extension = min_extension
        self.max_extension = max_extension
        self.min_nobuzz = min_nobuzz
        self.max_nobuzz = max_nobuzz
        self.current_extension = 0.0

        # Sets up the servo with the specified GPIO pin number
        # For this to work, you have to run the pigpio daemon on the Raspberry Pi (sudo pigpiod)
        if pin_factory is None:
            gpiozero.Device.pin_factory = gpiozero.pins.pigpio.PiGPIOFactory()
        else:
            gpiozero.Device.pin_factory = pin_factory
        self.servo = gpiozero.Servo(gpio_pin_number)

   def set_extension(self, extension: float):
        """
        Sets the extension of the servo.
        :param extension: The extension of the servo, where 0 is min_extension, 1 is max_extension, and 2 is min_nobuzz.
        """

        if extension == 0:
            self.current_extension = self.min_extension
        elif extension == 1:
            self.current_extension = self.max_extension
        elif extension == 2:
            self.current_extension = self.min_nobuzz
        elif extension == 3:
            self.current_extension = self.max_no_buzz
            
        else:
            # Clamps the extension value to be within the specified range
            extension = min(1.0, max(0.0, extension))
            # Converts the extension from 0 to 1 to the actual extension range
            self.current_extension = extension * (self.max_extension - self.min_extension) + self.min_extension

        # Sets the servo extension
        self.servo.value = self.current_extension
