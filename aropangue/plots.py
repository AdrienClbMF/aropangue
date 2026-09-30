import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
import datetime as dt
from zoneinfo import ZoneInfo
from astral import LocationInfo
from astral.sun import sun
from matplotlib.ticker import FixedLocator, MultipleLocator, FuncFormatter

CMAP_TI = LinearSegmentedColormap.from_list(
    "thermal",
    [
        (0.00, "#3f8f9b"),  # teal: weak but non-zero
        (0.12, "#7fb890"),  # soft green
        (0.24, "#c9d65f"),  # lime-yellow
        (0.36, "#ffe01a"),  # yellow
        (0.50, "#ffb000"),  # amber
        (0.70, "#ff7a00"),  # orange
        (0.85, "#e63a14"),  # red-orange
        (1.00, "#8b0000"),  # dark red
    ],
)
CMAP_TI.set_under("white")


CMAP_CLOUDS = LinearSegmentedColormap.from_list(
    "clouds",
    [
        (0.00, "#f7f7f7"),  # 95
        (0.25, "#e6e6e6"),  # ~97.5
        (0.30, "#bdbdbd"),  # 98
        (0.40, "#7f7f7f"),  # 99
        (0.42, "#b39ddb"),  # just above 99
        (0.55, "#9575cd"),
        (0.70, "#673ab7"),
        (0.85, "#4527a0"),
        (1.00, "#311b92"),
    ],
)

CMAP_CLOUDS.set_under("white")


def add_sun_vlines(ax, time_local, lat, lon, tz="Indian/Reunion"):
    tzinfo = ZoneInfo(tz)
    obs = LocationInfo(latitude=lat, longitude=lon).observer
    t0, t1 = time_local[0], time_local[-1]

    # every local calendar day covered by the plot
    days = np.unique(time_local.astype("datetime64[D]")).astype(object)

    for d in days:
        s = sun(obs, date=d, tzinfo=tzinfo)
        for key, symbol in (("sunrise", "↑"), ("sunset", "↓")):
            t = s[key].replace(tzinfo=None)          # naive local time
            if t0 <= np.datetime64(t) <= t1:         # only if inside the plot
                x = mdates.date2num(t)
                ax.axvline(x, color="k", ls="--", lw=1.5, zorder=5)
                ax.text(
                    x, .95, f"{symbol} {t:%H:%M}",
                    transform=ax.get_xaxis_transform(),  # x in data, y in axes coords
                    ha="left", va="bottom",
                    fontsize=12, fontweight="bold",
                )


def compress_night(ax, time_local, start_hour=22, end_hour=5, factor=0.1):
    """Night hours take `factor` of their normal width on the x axis."""
    t0 = time_local[0].astype("datetime64[D]")
    t1 = time_local[-1].astype("datetime64[D]")
    days = np.arange(t0 - np.timedelta64(2, "D"), t1 + np.timedelta64(3, "D"))

    # breakpoints alternate: 06h (night ends) -> 22h (night starts) -> 06h ...
    bps = []
    for d in days:
        bps += [d + np.timedelta64(end_hour, "h"), d + np.timedelta64(start_hour, "h")]
    bx = mdates.date2num(np.array(bps, dtype="datetime64[ns]"))

    seg_weight = np.where(np.arange(len(bx) - 1) % 2 == 0, 1.0, factor)  # day, night, day...
    w = np.concatenate([[0], np.cumsum(np.diff(bx) * seg_weight)])

    ax.set_xscale(
        "function",
        functions=(lambda x: np.interp(x, bx, w), lambda y: np.interp(y, w, bx)),
    )

    # ticks: skip the crowded night hours, keep 00h (with date) and 06h to 20h
    ticks = [
        d + np.timedelta64(h, "h")
        for d in days for h in (0, 6, 8, 10, 12, 14, 16, 18, 20)
    ]
    ticks = [t for t in ticks if time_local[0] <= t <= time_local[-1]]
    ax.xaxis.set_major_locator(FixedLocator(mdates.date2num(np.array(ticks, dtype="datetime64[ns]"))))


def plot_tv_difference_hovmoller(tv_diff, u, v, add_windbarbs: bool = True, pointname: str = 'Unknown'):

    times = tv_diff["valid_time"].values
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

    mesh = ax.pcolormesh(
        time_edges,
        height_edges,
        tv_diff.T,
        shading="flat",
        cmap=CMAP_TI,
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

    # ---------------- Ticks strategy ----------------
    ax.xaxis_date()

    # Y axis: a tick every 200 m
    ax.yaxis.set_major_locator(MultipleLocator(200))

    # X axis: compressed night + custom ticks
    compress_night(ax, time_local)
    ax.set_xlim(time_edges[0], time_edges[-1])

    # Label: hour only, full date at midnight
    def _fmt(x, pos):
        t = mdates.num2date(x)
        return t.strftime("%d %b\n00h") if t.hour == 0 else t.strftime("%Hh")

    ax.xaxis.set_major_formatter(FuncFormatter(_fmt))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")
    # -------------------------------------------------

    # Axis labels
    ax.set_xlabel("Local time (UTC+4)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Height above ground (m)", fontsize=12, fontweight="bold")

    # Tick labels (x and y)
    ax.tick_params(axis="both", which="major", labelsize=12)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")

    # Colorbar label and ticks
    cbar.set_label("Virtual temperature difference (K)", fontsize=12, fontweight="bold")
    cbar.ax.tick_params(labelsize=12)
    for label in cbar.ax.get_yticklabels():
        label.set_fontweight("bold")

    ax.grid(True, color="lightgrey", linestyle="-", linewidth=0.8, zorder=3)

    add_sun_vlines(
        ax, time_local,
        lat=float(tv_diff.latitude),
        lon=float(tv_diff.longitude),
    )
    
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")
    plt.tight_layout()

    return fig, ax

def plot_ceiling_height(lcl, pointname="Unknown", ceiling_name="LCL"):
    """lcl: DataArray (valid_time,) in m, from get_lcl_height."""
    time_local = lcl["valid_time"].values + np.timedelta64(4, "h")   # UTC -> UTC+4
    time_num = mdates.date2num(time_local)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(time_num, np.squeeze(lcl.values), color="tab:blue", lw=2.5, marker="o", ms=4)

    ax.set_xlabel("Local time (UTC+4)", fontsize=12, fontweight="bold")
    ax.set_ylabel(f"{ceiling_name} height above ground (m)", fontsize=12, fontweight="bold")
    ax.set_title(f"{ceiling_name} height, {pointname}")

    # Ticks: every 2 h, date at midnight
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    def _fmt(x, pos):
        t = mdates.num2date(x)
        return t.strftime("%d %b\n00h") if t.hour == 0 else t.strftime("%Hh")
    ax.xaxis.set_major_formatter(FuncFormatter(_fmt))
    ax.yaxis.set_major_locator(MultipleLocator(200))
    ax.set_ylim(bottom=0)

    ax.grid(True, color="lightgrey", linewidth=0.8)
    ax.set_axisbelow(True)

    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")
    ax.tick_params(axis="both", labelsize=12)

    plt.tight_layout()
    return fig, ax




def plot_3d_clouds_hovmoller(rh_3d, lcl = None, pointname: str = 'Unknown'):

    times = rh_3d["valid_time"].values
    heights = rh_3d["heightAboveGround"].values

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

    mesh = ax.pcolormesh(
        time_edges,
        height_edges,
        rh_3d.T,
        shading="flat",
        cmap=CMAP_CLOUDS,
        vmin=95,
        vmax=105,
    )

    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label("Virtual temperature difference (K)")

    ax.set_xlabel("Local time (UTC+4)")
    ax.set_ylabel("Height above ground (m)")
    ax.set_title(f"Virtual temperature difference and wind — {pointname}")

    # ---------------- Ticks strategy ----------------
    ax.xaxis_date()

    # Y axis: a tick every 200 m
    ax.yaxis.set_major_locator(MultipleLocator(200))

    # X axis: compressed night + custom ticks
    compress_night(ax, time_local)
    ax.set_xlim(time_edges[0], time_edges[-1])

    # Label: hour only, full date at midnight
    def _fmt(x, pos):
        t = mdates.num2date(x)
        return t.strftime("%d %b\n00h") if t.hour == 0 else t.strftime("%Hh")

    ax.xaxis.set_major_formatter(FuncFormatter(_fmt))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")
    # -------------------------------------------------

    # Axis labels
    ax.set_xlabel("Local time (UTC+4)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Height above ground (m)", fontsize=12, fontweight="bold")

    # Tick labels (x and y)
    ax.tick_params(axis="both", which="major", labelsize=12)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")

    # Colorbar label and ticks
    cbar.set_label("Relative humidity (%)", fontsize=12, fontweight="bold")
    cbar.ax.tick_params(labelsize=12)
    for label in cbar.ax.get_yticklabels():
        label.set_fontweight("bold")

    ax.grid(True, color="lightgrey", linestyle="-", linewidth=0.8, zorder=3)

    add_sun_vlines(
        ax, time_local,
        lat=float(rh_3d.latitude),
        lon=float(rh_3d.longitude),
    )

    if lcl is not None :
        ax.plot(
            lcl["valid_time"].values + np.timedelta64(4, "h"),
            lcl.values,
            color="red",
            linestyle="--",
            linewidth=2,
            label="LCL",
            zorder=4,
        )
    
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")
    plt.tight_layout()

    return fig, ax
