"""Additional full-size sensor/control traces from the actual M20 showcase."""
from pathlib import Path
import pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent

if __name__=='__main__':
    d=pd.read_csv(HERE/'demo_runs/m20_mission/telemetry.csv')
    fig,a=plt.subplots(5,1,figsize=(8,8),sharex=True,layout='constrained')
    a[0].plot(d.time_s,d.speed_m_s,label='actual planar speed');a[0].plot(d.time_s,d.command_v_m_s,label='requested cruise speed',alpha=.7)
    a[0].set_ylabel('Speed (m/s)');a[0].legend()
    a[1].plot(d.time_s,d.slip_proxy);a[1].set_ylabel('Hub/body speed\ndiscrepancy (unitless)')
    a[2].plot(d.time_s,d.clearance_m);a[2].set_ylabel('Ideal forward\nclearance (m)')
    a[3].plot(d.time_s,d.map_coverage*100);a[3].set_ylabel('Observed grid (%)')
    a[4].plot(d.time_s,d.max_torque_Nm);a[4].set_ylabel('Peak motor\ntorque (N m)');a[4].set_xlabel('MuJoCo simulated time (s) | combined mission, seed 42')
    fig.suptitle('Measured M20 sensor/control diagnostics (simulation only)')
    fig.savefig(HERE.parent/'docs/figures/figure5_sensor_control_diagnostics.png',dpi=300)
    plt.close(fig)
