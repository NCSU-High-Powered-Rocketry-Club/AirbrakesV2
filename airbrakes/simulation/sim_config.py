"""Module containing static config settings for simulation"""

import numpy as np
import numpy.typing as npt

from airbrakes.simulation.random_config import (
    DEFAULT_RAND_CONFIG,
    SUB_SCALE_RAND_CONFIG,
    RandomConfig,
)


class SimulationConfig:
    """
    Configuration settings for static values in the simulation. Includes presets of full-scale
    and sub-scale flights.
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
        launch_rod_pitch: np.float64,
        launch_rod_azimuth: np.float64,
        air_temperature: np.float64,
        airbrakes_reference_area: np.float64,
        rand_config: RandomConfig,
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

        # Rocket orientation and initial direction on the launch pad
        self.wgs_vertical = wgs_vertical
        self.launch_rod_pitch = launch_rod_pitch
        self.launch_rod_azimuth = launch_rod_azimuth

        # The randomness configuration settings for the specified flight
        self.rand_config = rand_config


FULL_SCALE_CONFIG = SimulationConfig(
    raw_time_step=np.float64(0.001),
    est_time_step=np.float64(0.002),
    motor="AeroTech_L1940X",
    airbrake_retracted_cd=np.array([[0.1, 0.2, 0.3, 0.5, 0.7], [0.55, 0.45, 0.375, 0.34, 0.34]]),
    airbrake_extended_cd=np.array([[0.1, 0.2, 0.3, 0.5, 0.7], [0.7, 0.6, 0.525, 0.49, 0.49]]),
    rocket_mass=np.float64(17.6),
    reference_area=np.float64(0.01929),
    airbrakes_reference_area=np.float64(0.01),
    air_temperature=np.float64(25),
    wgs_vertical=np.array([0, 0, -1]),
    launch_rod_pitch=np.float64(5.0),
    launch_rod_azimuth=np.float64(0.0),
    rand_config=DEFAULT_RAND_CONFIG,
)

SUB_SCALE_CONFIG = SimulationConfig(
    raw_time_step=np.float64(0.001),
    est_time_step=np.float64(0.002),
    motor="AeroTech_J500G",
    airbrake_retracted_cd=np.array([[0.05, 0.2, 0.3], [0.5, 0.445, 0.43]]),
    airbrake_extended_cd=np.array([[0.05, 0.2, 0.3], [0.65, 0.595, 0.58]]),
    rocket_mass=np.float64(6.172),
    reference_area=np.float64(0.008205),
    airbrakes_reference_area=np.float64(0.00487741),
    air_temperature=np.float64(15),
    wgs_vertical=np.array([-1, 0, 0]),
    launch_rod_pitch=np.float64(5.0),
    launch_rod_azimuth=np.float64(0.0),
    rand_config=SUB_SCALE_RAND_CONFIG,
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
