import gpiozero


class Servo:
    """
    A custom class that represents a servo motor, controlling the extension of the airbrakes.
    """

    __slots__ = ("min_extension", "max_extension", "servo", "current_extension")

    def __init__(self, gpio_pin_number: int, min_extension: float, max_extension: float):
        self.min_extension = min_extension
        self.max_extension = max_extension
        self.current_extension = 0.0

        # Sets up the servo with the specified GPIO pin number
        gpiozero.Device.pin_factory = gpiozero.pins.pigpio.PiGPIOFactory()
        self.servo = gpiozero.Servo(gpio_pin_number)

    def set_extension(self, extension: float):
        """
        Sets the extension of the servo.
        :param extension: The extension of the servo, between 0 and 1.
        """

        # Clamps the extension value to be within the specified range
        extension = min(1.0, max(0.0, extension))

        # Converts the extension from 0 to 1 to the actual extension range
        self.current_extension = extension * (self.max_extension - self.min_extension) + self.min_extension

        # Sets the servo extension
        self.servo.value = self.current_extension
