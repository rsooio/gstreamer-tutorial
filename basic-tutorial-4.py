import gi
import signal

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib  # type: ignore # noqa: E402

Gst.init(None)

playbin = Gst.ElementFactory.make("playbin")
playbin.set_property(
    "uri",
    "https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm",
)

loop = GLib.MainLoop()

seek_enabled = False


def poll_position():
    success, position = playbin.query_position(Gst.Format.TIME)
    if success and position >= 10 * Gst.SECOND:
        if seek_enabled:
            print("Reached 10s, performing seek.")
            playbin.seek_simple(
                Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                30 * Gst.SECOND,
            )
        else:
            print("Seeking is DISABLED, skiping seek.")
        return False
    return True


GLib.timeout_add(100, poll_position)


def bus_call(bus: Gst.Bus, msg: Gst.Message):
    match msg.type:
        case Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            print(f"Error: {err}, Debug: {debug}")
            loop.quit()
        case Gst.MessageType.EOS:
            print("End of stream")
            loop.quit()
        case Gst.MessageType.STATE_CHANGED:
            if msg.src is playbin:
                old_state, new_state, pending = msg.parse_state_changed()
                print(
                    "Pipeline state changed "
                    f"from {old_state.value_nick} "
                    f"to {new_state.value_nick}"
                )
                if new_state is Gst.State.PLAYING:
                    global seek_enabled
                    query = Gst.Query.new_seeking(Gst.Format.TIME)
                    success = playbin.query(query)
                    if success:
                        _, seek_enabled, start, end = query.parse_seeking()
                        if seek_enabled:
                            print(f"Seeking is ENABLED from {start} to {end}")
                        else:
                            print("Seeking is DISABLED for this stream.")


bus = playbin.get_bus()
bus.add_signal_watch()
bus.connect("message", bus_call)


def handle_stop(signalnum, stack_frame):
    print("\nSIGINT received, exiting...")
    loop.quit()


signal.signal(signal.SIGINT, handle_stop)

playbin.set_state(Gst.State.PLAYING)

loop.run()
