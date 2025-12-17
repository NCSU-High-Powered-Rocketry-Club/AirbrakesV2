# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "casadi==3.7.2",
#     "numpy==2.3.5",
#     "pandas==2.3.3",
#     "plotly==6.5.0",
# ]
# ///

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import math
    return (math,)


@app.cell
def _():
    import json

    with open("../launch_data/metadata.json") as file:
        metadata = json.load(file)
    return (metadata,)


@app.cell
def _(metadata):
    import marimo as mo
    keys = list(metadata.keys())
    keys.remove("$schema")
    # keys = [item for item in keys if metadata[item]["rocket"]["rocket_Cd"] is not None]
    dropdown = mo.ui.dropdown(
        options=keys, value="government_work_1.csv", label="Choose flight"
    )
    dropdown
    return dropdown, mo


@app.cell
def _(dropdown, metadata, mo):
    # metadata_flight_name = "government_work_1.csv"
    # metadata_flight_name = "pelicanator_launch_4.csv"
    metadata_flight_name = dropdown.value
    mo.md(metadata[metadata_flight_name]["flight_description"])
    return (metadata_flight_name,)


@app.cell
def _(metadata, metadata_flight_name):
    # metadata[metadata_flight_name]
    ROCKET_CD = metadata[metadata_flight_name]["rocket"]["rocket_Cd"]
    ROCKET_CROSS_SECTIONAL_AREA_M2 = metadata[metadata_flight_name]["rocket"]["rocket_cross_sectional_area_m2"]
    ROCKET_DRY_MASS_KG = metadata[metadata_flight_name]["rocket"]["rocket_mass_kg"] or 14.5
    # ROCKET_DRY_MASS_KG = 14.5 if ROCKET_DRY_MASS_KG is None else ROCKET_DRY_MASS_KG
    return ROCKET_CD, ROCKET_CROSS_SECTIONAL_AREA_M2, ROCKET_DRY_MASS_KG


@app.cell
def _(ROCKET_CD, ROCKET_CROSS_SECTIONAL_AREA_M2, ROCKET_DRY_MASS_KG):
    ROCKET_CD, ROCKET_CROSS_SECTIONAL_AREA_M2, ROCKET_DRY_MASS_KG
    return


@app.cell
def _(metadata_flight_name):
    import pandas as pd

    df = pd.read_csv(f"../launch_data/{metadata_flight_name}")
    df = df.dropna(subset=['current_altitude', 'vertical_velocity'])
    df = df[df['state_letter'] == 'C']
    # df = df.filter(items=['timestamp', 'current_altitude', 'vertical_velocity'])
    df_timestamp_initial = df['timestamp'].iloc[0]
    df['timestamp'] = (df['timestamp'] - df_timestamp_initial) / 1e9
    df.rename(columns={
        'timestamp': 't',
        'current_altitude': 'py',
        'vertical_velocity': 'vy',
    }, inplace=True)
    df.set_index('t')

    df_apogee = df['py'].max()

    # df
    return df, df_apogee


@app.cell
def _(df, df_apogee, go, metadata_flight_name):
    # Plot velocity and altitude over time
    def plot_data():
        fig = go.Figure()
        fig.add_scatter(x=df['t'], y=df['py'], mode='lines', name='Altitude (m)')
        fig.add_scatter(x=df['t'], y=df['vy'], mode='lines', name='Vertical Velocity (m/s)')
        fig.add_hline(y=df_apogee, line_dash="dot",  annotation_text="Actual Apogee: {:.1f} m".format(df_apogee))
        fig.layout.title = f"Flight Data for {metadata_flight_name}"
        fig.layout.xaxis.title = "Time (s)"
        fig.layout.yaxis.title = "Altitude (m)"
        return fig
    # plot_data()
    return (plot_data,)


@app.cell
def _():
    import casadi as ca
    from casadi import MX, Function
    import numpy as np
    return Function, MX, ca, np


@app.cell
def _():
    import plotly.graph_objects as go
    return (go,)


@app.cell
def _(MX, ca, rocket_area, rocket_cd, rocket_mass):
    py = MX.sym("py")
    vy = MX.sym("vy")
    # x = ca.vertcat(py, vy)
    x = ca.vertcat(py, vy, rocket_cd, rocket_area, rocket_mass)
    return vy, x


@app.cell
def _(MX):
    rocket_cd = MX.sym("cd")
    rocket_area = MX.sym("area")
    rocket_mass = MX.sym("m")
    return rocket_area, rocket_cd, rocket_mass


@app.cell
def _(ca, rocket_area, rocket_cd, rocket_mass, vy):
    rho = 1.224 # density
    g = -9.8
    drag_force = -0.5 * rho * (vy ** 2) * rocket_cd * rocket_area
    ay = drag_force / rocket_mass + g

    # x_dot = ca.vertcat(vy, ay)
    x_dot = ca.vertcat(vy, ay, 0, 0, 0)
    return (x_dot,)


@app.cell
def _(ca, x, x_dot):
    dt = 0.01

    # T = 12 # time horizon
    # N = T / dt

    intg_options = {
        "tf": dt,
        "simplify": True,
        "number_of_finite_elements": 4,
    }

    dae = {
        "x": x,
        # "p": u,
        "ode": x_dot,
    }

    # Single step of the system
    intg = ca.integrator('intg', 'rk', dae, intg_options)
    return dt, intg


@app.cell
def _(Function, intg, x):
    x_next = intg(x0=x)['xf']
    F = Function('F', [x], [x_next])
    return (F,)


@app.cell
def _(F, dt):
    horizon = 0.25
    N = int(horizon/dt)
    sim = F.mapaccum(N)
    long_sim = F.mapaccum(int(20/dt))
    return N, long_sim


@app.cell
def _(df, dt, np):
    # t_new = np.arange(t_start, t_start + horizon + dt, dt)
    t_end = 6

    t_new = np.arange(0, t_end + dt, dt)
    data_pys = np.interp(t_new, df['t'], df['py'])
    data_vys = np.interp(t_new, df['t'], df['vy'])
    data_interp = np.stack([data_pys, data_vys])
    # data_interp[:, :101].shape
    return data_interp, t_new


@app.cell
def _(F, N, ROCKET_CROSS_SECTIONAL_AREA_M2, ROCKET_DRY_MASS_KG, ca):
    opti = ca.Opti()
    o_x = opti.variable(5, N+1)
    o_target = opti.parameter(2, N+1)

    # o_err = o_x[0:2, :] - data_interp
    o_err = o_x[0:2, :] - o_target
    opti.minimize(ca.sumsqr(o_err))

    for k in range(0, N):
        opti.subject_to(o_x[:,k+1] == F(o_x[:,k]))

    opti.subject_to(o_x[2,:] >= 0) # Cd >= 0
    opti.subject_to(o_x[3,0] == ROCKET_CROSS_SECTIONAL_AREA_M2)
    opti.subject_to(o_x[4,0] == ROCKET_DRY_MASS_KG)
    return o_target, o_x, opti


@app.cell
def _(ROCKET_CROSS_SECTIONAL_AREA_M2, ROCKET_DRY_MASS_KG, o_target, o_x, opti):
    opti_opts = {
        # "qpsol": "osqp",
        # "qpsol": "qpoases",
        "qpsol": "qrqp", # good one
        # "qpsol": "proxqp",
        "print_header": False,
        "print_iteration": False,
        "print_time": False,
        "max_iter": 10000
    }

    s_opts = {
        "error_on_fail": False
    }

    jit_options = {"flags": ["-O2"], "verbose": True}
    options = {"jit": True, "compiler": "shell", "jit_options": jit_options}
    # opti.solver('ipopt', options, {})
    opti.solver('ipopt')

    # opti.set_initial(o_x[0:2,:], o_target[0:2,:])
    # opti.set_initial(o_x[2,:], ROCKET_CD)
    # opti.set_initial(o_x[2,:], 1)
    opti.set_initial(o_x[3,:], ROCKET_CROSS_SECTIONAL_AREA_M2)
    opti.set_initial(o_x[4,:], ROCKET_DRY_MASS_KG)

    o_f = opti.to_function('f', [o_target], [o_x[2,0]])
    # res = o_f(data_interp[:, :N+1])
    # # res = o_f(data_interp)
    # res
    return (o_f,)


@app.cell
def _():
    # o_f.generate("a.c")
    # C = ca.Importer('a.c','clangd')
    # f = ca.external('f',C)
    # print(f(3.14))
    return


@app.cell
def _(N, ROCKET_CD, data_interp, go, np, o_f, t_new):
    def plot_cd(fig = None):
        if fig is None:
            fig = go.Figure()

        subsample = 20
        length = data_interp.shape[1] - N
        prediction = np.zeros(length)
        for i in range(0, length, subsample):
            sub_data = data_interp[:, i:i+N+1]
            res = o_f(sub_data)
            prediction[i] = res

        # fig.add_scatter(x=df['t'][:length], y=prediction, mode='lines', name='Estimated Cd')
        mask = prediction != 0
        fig.add_scatter(x=t_new[:length][mask], y=prediction[mask] , mode='lines', name='Estimated Cd')
        fig.add_hline(y=ROCKET_CD, line_dash="dot",  annotation_text="Actual Cd: {:.3f}".format(ROCKET_CD))
        return fig
    # plot_cd(plot_data())
    # plot_cd()
    return


@app.cell
def _(ca, long_sim, np):
    def apogee(cd, area, mass, py0, vy0):
        x0 = ca.vertcat(py0, vy0, cd, area, mass)
        res = long_sim(x0)
        py_max = np.array(res[0, :]).max()
        return py_max

    # apogee(ROCKET_CD, ROCKET_CROSS_SECTIONAL_AREA_M2, ROCKET_DRY_MASS_KG, 0, 100)
    return (apogee,)


@app.cell
def _(
    ROCKET_CD,
    ROCKET_CROSS_SECTIONAL_AREA_M2,
    ROCKET_DRY_MASS_KG,
    apogee,
    df,
    np,
    plot_data,
):
    def plot_old_predicted_apogee(fig = None):
        if fig is None:
            fig = plot_data()

        subsample = 50
        predicted_ts = np.zeros(len(df) // subsample + 1)
        predicted_apogees = np.zeros(len(df) // subsample + 1)
        for i in range(0, len(df), subsample):
            py0 = df['py'].iloc[i]
            vy0 = df['vy'].iloc[i]
            py_max = apogee(ROCKET_CD, ROCKET_CROSS_SECTIONAL_AREA_M2, ROCKET_DRY_MASS_KG, py0, vy0)

            predicted_ts[i // subsample] = df['t'].iloc[i]
            predicted_apogees[i // subsample] = py_max

        fig.add_scatter(x=predicted_ts, y=predicted_apogees, mode='lines', name='Predicted Apogee (RK45 Craig)')
        return fig
    # plot_old_predicted_apogee()
    return


@app.cell
def _(
    ROCKET_CD,
    ROCKET_CROSS_SECTIONAL_AREA_M2,
    ROCKET_DRY_MASS_KG,
    df,
    math,
    np,
    plot_data,
):
    import hprm
    def plot_hprm_predicted_apogee(fig = None):
        if fig is None:
            fig = plot_data()

        # Define the Test Vehicle
        test_vehicle = hprm.Rocket(
            ROCKET_DRY_MASS_KG,   # mass kg
            ROCKET_CD,    # drag coefficient
            ROCKET_CROSS_SECTIONAL_AREA_M2,  # cross-sectional reference area
            0,   # lifting-surface reference area
            0,    # Moment of Inertia (for a 3DoF rocket)
            0,    # Dimensional stability margin (distance between cp and cg)
            0     # Derivative of lift coefficient with alpha(angle of attack)
        )

        ats = hprm.AdaptiveTimeStep()
        ats.absolute_error_tolerance = 1.0
        ats.dt_max = 1.0
        ode_method = hprm.OdeMethod.RK45

        subsample = 50
        predicted_ts = np.zeros(len(df) // subsample + 1)
        predicted_apogees = np.zeros(len(df) // subsample + 1)
        for i in range(0, len(df), subsample):
            py0 = df['py'].iloc[i]
            vy0 = df['vy'].iloc[i]
            py_max = test_vehicle.predict_apogee(py0, vy0, hprm.ModelType.OneDOF, ode_method, ats, math.pi)

            predicted_ts[i // subsample] = df['t'].iloc[i]
            predicted_apogees[i // subsample] = py_max

        fig.add_scatter(x=predicted_ts, y=predicted_apogees, mode='lines', name='Predicted Apogee (HPRM)')

        return fig
    # plot_hprm_predicted_apogee()
    return


@app.cell
def _():
    # plot_hprm_predicted_apogee(plot_old_predicted_apogee())
    return


@app.cell
def _(
    N,
    ROCKET_CROSS_SECTIONAL_AREA_M2,
    ROCKET_DRY_MASS_KG,
    apogee,
    data_interp,
    df,
    dt,
    np,
    o_f,
    plot_data,
):
    def plot_data_predicted_apogee(fig = None):
        if fig is None:
            fig = plot_data()

        subsample = 300
        predicted_ts = np.zeros(len(df) // subsample + 1)
        predicted_apogees = np.zeros(len(df) // subsample + 1)
        for i in range(0, len(df), subsample):
            py0 = df['py'].iloc[i]
            vy0 = df['vy'].iloc[i]
            t0 = df['t'].iloc[i]
            start_i = t0 // dt
            end_i = start_i + N + 1
            try:
                cd_est = o_f(data_interp[:, int(start_i):int(end_i)])
                py_max = apogee(cd_est, ROCKET_CROSS_SECTIONAL_AREA_M2, ROCKET_DRY_MASS_KG, py0, vy0)

                predicted_ts[i // subsample] = df['t'].iloc[i] + dt
                predicted_apogees[i // subsample] = py_max
            except:
                pass

        mask = predicted_apogees != 0
        fig.add_scatter(x=predicted_ts[mask], y=predicted_apogees[mask], mode='lines', name='Predicted Apogee (Craig method)')
        return fig
    # plot_data_predicted_apogee(plot_hprm_predicted_apogee())
    plot_data_predicted_apogee()
    return


if __name__ == "__main__":
    app.run()
