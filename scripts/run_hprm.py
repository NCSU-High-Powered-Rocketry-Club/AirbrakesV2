import math
from hprm import Rocket, ModelType, OdeMethod, AdaptiveTimeStep

def main():
    print("Testing out the High Powered Rocket Modeling Program")

    # Define the Test Vehicle
    test_vehicle = Rocket(
        10.0,   # mass kg
        0.3,    # drag coefficient
        0.005,  # cross-sectional reference area
        0,   # lifting-surface reference area
        0,    # Moment of Inertia (for a 3DoF rocket)
        0,    # Dimensional stability margin (distance between cp and cg)
        0     # Derivative of lift coefficient with alpha(angle of attack)
    )

    initial_height = 0.0
    initial_velocity = 100.0

    ats = AdaptiveTimeStep()
    ats.absolute_error_tolerance = 1.0
    print(f"Apogee: {test_vehicle.predict_apogee(initial_height, initial_velocity, ModelType.OneDOF, OdeMethod.RK45, ats)}")


if __name__ == "__main__":
    main()
