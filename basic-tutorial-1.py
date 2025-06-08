import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # type: ignore # noqa: E402

Gst.init(None)

pipeline = Gst.parse_launch(
    "playbin uri=https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm"
)

pipeline.set_state(Gst.State.PLAYING)
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
    Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS
)

if msg:
    if msg.type == Gst.MessageType.ERROR:
        err, debug = msg.parse_error()
        print(f"Error: {err}, Debug: {debug}")
    elif msg.type == Gst.MessageType.EOS:
        print("End of stream")

pipeline.set_state(Gst.State.NULL)
