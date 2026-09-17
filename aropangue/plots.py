import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_tv_difference_hovmoller(tv_diff, u, v, add_windbarbs: bool = True, pointname:str = 'Unknown'):

    times = tv_diff["time"].values
    heights = tv_diff["heightAboveGround"].values

    # UTC -> local time (Réunion, UTC+4), for plotting only
    time_local = times + np.timedelta64(4, "h")

    # Convert local times to matplotlib dates
    time_num = mdates.date2num(time_local)

    # Cell edges: centers are at the local time coordinates
    time_edges = np.empty(len(time_num) + 1)
    time_edges[1:-1] = (time_num[:-1] + time_num[1:]) / 2
    time_edges[0] = time_num[0] - (time_num[1] - time_num[0]) / 2
    time_edges[-1] = time_num[-1] + (time_num[-1] - time_num[-2]) / 2

    height_edges = np.empty(len(heights) + 1)
    height_edges[1:-1] = (heights[:-1] + heights[1:]) / 2
    height_edges[0] = heights[0] - (heights[1] - heights[0]) / 2
    height_edges[-1] = heights[-1] + (heights[-1] - heights[-2]) / 2

    fig, ax = plt.subplots(figsize=(14, 7))

    cmap = plt.cm.YlOrRd.copy()
    cmap.set_under("white")

    mesh = ax.pcolormesh(
        time_edges,
        height_edges,
        tv_diff.T,
        shading="flat",
        cmap=cmap,
        vmin=0,
        vmax=5,
    )

    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label("Virtual temperature difference (K)")

    # Wind barbs
    if add_windbarbs:
        T, H = np.meshgrid(time_num, heights, indexing="ij")

        step_time = 2
        step_height = 2

        ax.barbs(
            T[::step_time, ::step_height],
            H[::step_time, ::step_height],
            u.values[::step_time, ::step_height],
            v.values[::step_time, ::step_height],
            length=6,
        )

    ax.set_xlabel("Local time (UTC+4)")
    ax.set_ylabel("Height above ground (m)")
    ax.set_title(f"Virtual temperature difference and wind — {pointname}")

    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%H:%M"))
    fig.autofmt_xdate()

    plt.tight_layout()

    return fig, ax