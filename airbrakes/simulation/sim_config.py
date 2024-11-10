class SimulationConfig:
    def __init__(self,
                 raw_time_step,
                 est_time_step,
                 motor,
                 drag_coefficient,
                 rocket_mass,
                 reference_area,
                 rocket_orientation,
                 launch_rod_angle,
                 launch_rod_direction):
        # Time steps for data packet generation in the simulation
        self.raw_time_step = raw_time_step
        self.est_time_step = est_time_step

        # Motor selection (name of CSV file without extension)
        self.motor = motor

        # Rocket properties
        self.drag_coefficient = drag_coefficient
        self.rocket_mass = rocket_mass
        self.reference_area = reference_area

        # Rocket orientation on the launch pad
        self.rocket_orientation = rocket_orientation

        # Config for randomness in the simulation
        self.launch_rod_angle = launch_rod_angle
        self.launch_rod_direction = launch_rod_direction


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
