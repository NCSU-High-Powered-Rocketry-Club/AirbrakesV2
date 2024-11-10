import numpy as np
import numpy.typing as npt


class SimulationConfig:
    def __init__(self,
                 raw_time_step: np.float64,
                 est_time_step: np.float64,
                 motor: str,
                 drag_coefficient: np.float64,
                 rocket_mass: np.float64,
                 reference_area: np.float64,
                 rocket_orientation: npt.NDArray[np.float64],
                 launch_rod_angle: np.float64,
                 launch_rod_direction: np.float64):
        # Time steps for data packet generation in the simulation
        self.raw_time_step = np.float64(raw_time_step)
        self.est_time_step = np.float64(est_time_step)

        # Motor selection (name of CSV file without extension)
        self.motor = motor

        # Rocket properties
        self.drag_coefficient = np.float64(drag_coefficient)
        self.rocket_mass = np.float64(rocket_mass)
        self.reference_area = np.float64(reference_area)

        # Rocket orientation on the launch pad
        self.rocket_orientation = np.asarray(rocket_orientation, dtype=np.float64)

        # Config for randomness in the simulation
        self.launch_rod_angle = np.float64(launch_rod_angle)
        self.launch_rod_direction = np.float64(launch_rod_direction)


FULL_SCALE_CONFIG = SimulationConfig(
    raw_time_step=0.001,
    est_time_step=0.002,
    motor="AeroTech_L1940X",
    drag_coefficient=0.4,
    rocket_mass=14.5,
    reference_area=0.01929,
    rocket_orientation=[0, 0, -1],
    launch_rod_angle=[10],
    launch_rod_direction=[0]
)

# TODO: get actual values for sub scale
SUB_SCALE_CONFIG = SimulationConfig(
    raw_time_step=0.001,
    est_time_step=0.002,
    motor="PLACEHOLDER",
    drag_coefficient=0.4,
    rocket_mass=0,
    reference_area=0.001929,
    rocket_orientation=[0, 0, -1],
    launch_rod_angle=[10],
    launch_rod_direction=[0]
)


def get_configuration(config_type: str) -> SimulationConfig:
    """
    Gets the configuration for the simulation
    :param config_type: The type of simulation to run. This can be either "full-scale" or "sub-scale".
    :return: The configuration for the simulation
    """
    match config_type:
        case "full-scale":
            return FULL_SCALE_CONFIG
        case "sub-scale":
            return SUB_SCALE_CONFIG
        case _:
            raise ValueError(f"Invalid config type: {config_type}")
