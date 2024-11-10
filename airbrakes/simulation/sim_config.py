"""Module containing config settings for simulation"""

import numpy as np
import numpy.typing as npt


class SimulationConfig:
    """
    config class for simulation
    """

    def __init__(
        self,
        raw_time_step: np.float64,
        est_time_step: np.float64,
        motor: str,
        drag_coefficient: np.float64,
        rocket_mass: np.float64,
        reference_area: np.float64,
        rocket_orientation: npt.NDArray[np.float64],
        launch_rod_angle: npt.NDArray[np.float64],
        launch_rod_direction: npt.NDArray[np.float64],
    ):
        # Time steps for data packet generation in the simulation
        self.raw_time_step = raw_time_step
        self.est_time_step = est_time_step

        # Motor selection (name of CSV file without extension)
        self.motor = motor

        # Rocket properties
        self.drag_coefficient = drag_coefficient
        self.rocket_mass = rocket_mass  # This is wetted mass (including propellant weight)
        self.reference_area = reference_area

        # Rocket orientation on the launch pad
        self.rocket_orientation = rocket_orientation

        # Config for randomness in the simulation
        self.launch_rod_angle = launch_rod_angle
        self.launch_rod_direction = launch_rod_direction


FULL_SCALE_CONFIG = SimulationConfig(
    raw_time_step=np.float64(0.001),
    est_time_step=np.float64(0.002),
    motor="AeroTech_L1940X",
    drag_coefficient=np.float64(0.4),
    rocket_mass=np.float64(15.856),
    reference_area=np.float64(0.01929),
    rocket_orientation=np.array([0, 0, 1]),
    launch_rod_angle=np.array([10]),
    launch_rod_direction=np.array([90]),
)

# TODO: get actual values for sub scale
SUB_SCALE_CONFIG = SimulationConfig(
    raw_time_step=np.float64(0.001),
    est_time_step=np.float64(0.002),
    motor="PLACEHOLDER",
    drag_coefficient=np.float64(0.4),
    rocket_mass=np.float64(0),
    reference_area=np.float64(0.001929),
    rocket_orientation=np.array([-1, 0, 0]),
    launch_rod_angle=np.array([10]),
    launch_rod_direction=np.array([90]),
)


def get_configuration(config_type: str) -> SimulationConfig:
    """
    Gets the configuration for the simulation
    :param config_type: The type of simulation to run. This can be either "full-scale"
      or "sub-scale".
    :return: The configuration for the simulation
    """
    match config_type:
        case "full-scale":
            return FULL_SCALE_CONFIG
        case "sub-scale":
            return SUB_SCALE_CONFIG
        case _:
            raise ValueError(f"Invalid config type: {config_type}")
