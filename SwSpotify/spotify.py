import sys
from SwSpotify import SpotifyClosed, SpotifyPaused


def get_info_windows():
    """
    Reads the window titles to get the data.

    Older Spotify versions simply use FindWindow for "SpotifyMainWindow",
    the newer ones create an EnumHandler and flood the list with
    Chrome_WidgetWin_0s
    """

    import win32gui

    windows = []

    old_window = win32gui.FindWindow("SpotifyMainWindow", None)
    old = win32gui.GetWindowText(old_window)

    def find_spotify_uwp(hwnd, windows):
        text = win32gui.GetWindowText(hwnd)
        classname = win32gui.GetClassName(hwnd)
        if classname == "Chrome_WidgetWin_0" and len(text) > 0:
            windows.append(text)

    if old:
        windows.append(old)
    else:
        win32gui.EnumWindows(find_spotify_uwp, windows)

    # If Spotify isn't running the list will be empty
    if len(windows) == 0:
        raise SpotifyClosed

    # Local songs may only have a title field
    try:
        artist, track = windows[0].split(" - ", 1)
    except ValueError:
        artist = ''
        track = windows[0]

    # The window title is the default one when paused
    if windows[0] in ('Spotify Premium', 'Spotify Free'):
        raise SpotifyPaused

    return track, artist


def get_info_linux():
    """
    Uses the dbus API to get the data.
    """

    import dbus

    session_bus = dbus.SessionBus()
    try:
        spotify_bus = session_bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
    except dbus.exceptions.DBusException:
        raise SpotifyClosed

    spotify_properties = dbus.Interface(spotify_bus, "org.freedesktop.DBus.Properties")

    metadata = spotify_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")
    track = str(metadata['xesam:title'])
    artist = str(metadata['xesam:artist'][0])
    status = str(spotify_properties.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus"))
    if status.lower() != 'playing':
        raise SpotifyPaused

    return track, artist


def get_info_mac():
    """
    Runs an AppleScript script to get the data.

    Exceptions aren't thrown inside get_info_mac because it automatically
    opens Spotify if it's closed.
    """

    from Foundation import NSAppleScript

    apple_script_code = """
    getCurrentlyPlayingTrack()

    on getCurrentlyPlayingTrack()
        tell application "Spotify"
            set isPlaying to player state as string
            set currentArtist to artist of current track as string
            set currentTrack to name of current track as string
            return {currentArtist, currentTrack, isPlaying}
        end tell
    end getCurrentlyPlayingTrack
    """

    s = NSAppleScript.alloc().initWithSource_(apple_script_code)
    x = s.executeAndReturnError_(None)
    a = str(x[0]).split('"')
    if a[5].lower != 'playing':
        raise SpotifyPaused

    return a[3], a[1]


def current():
    if sys.platform.startswith("win"):
        return get_info_windows()
    elif sys.platform.startswith("darwin"):
        return get_info_mac()
    else:
        return get_info_linux()


def artist():
    return current()[1]


def song():
    return current()[0]
