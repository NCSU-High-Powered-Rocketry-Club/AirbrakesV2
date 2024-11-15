"""Module containing config settings for simulation"""

import numpy as np
import numpy.typing as npt


class SimulationConfig:
    """
    Configuration settings for the simulation. Includes presets of full-scale and sub-scale flights.
    """

    def __init__(
        self,
        raw_time_step: np.float64,
        est_time_step: np.float64,
        motor: str,
        airbrake_retracted_cd: npt.NDArray,
        airbrake_extended_cd: npt.NDArray,
        rocket_mass: np.float64,
        reference_area: np.float64,
        wgs_vertical: npt.NDArray[np.float64],
        launch_rod_pitch: npt.NDArray[np.float64],
        launch_rod_azimuth: npt.NDArray[np.float64],
        air_temperature: np.float64,
        airbrakes_reference_area: np.float64,
    ):
        # Time steps for data packet generation in the simulation
        self.raw_time_step = raw_time_step
        self.est_time_step = est_time_step

        # Motor selection (name of CSV file without extension)
        self.motor = motor

        # Rocket properties
        self.airbrakes_retracted_cd = airbrake_retracted_cd  # coefficient of drag at mach numbers
        self.airbrakes_extended_cd = airbrake_extended_cd
        self.rocket_mass = rocket_mass  # This is wetted mass (including propellant weight)
        self.reference_area = reference_area
        self.airbrakes_reference_area = airbrakes_reference_area

        # Atmospheric properties
        self.air_temperature = air_temperature  # ground temperature, in celcius

        # Rocket orientation on the launch pad
        self.wgs_vertical = wgs_vertical

        # Config for randomness in the simulation
        self.launch_rod_pitch = launch_rod_pitch
        self.launch_rod_azimuth = launch_rod_azimuth


FULL_SCALE_CONFIG = SimulationConfig(
    raw_time_step=np.float64(0.001),
    est_time_step=np.float64(0.002),
    motor="AeroTech_L1940X",
    # drag_coefficient=np.array([[0.1, 0.3, 0.5, 0.7], [0.3565, 0.3666, 0.3871, 0.41499]]),
    airbrake_retracted_cd=np.array([[0.1, 1], [0.29, 0.29]]),
    airbrake_extended_cd=np.array([[0.1, 1], [0.49, 0.49]]),
    rocket_mass=np.float64(17.6),
    reference_area=np.float64(0.01929),
    airbrakes_reference_area=np.float64(0.01),
    air_temperature=np.float64(25),
    wgs_vertical=np.array([0, 0, -1]),
    launch_rod_pitch=np.array([5]),
    launch_rod_azimuth=np.array([90]),
)

SUB_SCALE_CONFIG = SimulationConfig(
    raw_time_step=np.float64(0.001),
    est_time_step=np.float64(0.002),
    motor="AeroTech_J500G",
    airbrake_retracted_cd=np.array([[0.05, 0.2, 0.3], [0.41, 0.4175, 0.425]]),
    airbrake_extended_cd=np.array([[0.05, 0.2, 0.3], [0.51, 0.5175, 0.525]]),
    rocket_mass=np.float64(6.391),
    reference_area=np.float64(0.008205),
    airbrakes_reference_area=np.float64(0.00487741),
    air_temperature=np.float64(15),
    wgs_vertical=np.array([-1, 0, 0]),
    launch_rod_pitch=np.array([5]),
    launch_rod_azimuth=np.array([0]),
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
