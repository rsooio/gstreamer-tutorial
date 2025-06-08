import gi
import signal

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib  # type: ignore # noqa: E402

Gst.init(None)

source = Gst.ElementFactory.make("videotestsrc")
source.set_property("pattern", 0)

sink = Gst.ElementFactory.make("autovideosink")

pipeline = Gst.Pipeline.new("test-pipeline")

pipeline.add(source)
pipeline.add(sink)

source.link(sink)

loop = GLib.MainLoop()


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
            if msg.src is pipeline:
                old_state, new_state, pending = msg.parse_state_changed()
                print(
                    "Pipeline state changed "
                    f"from {old_state.value_nick} "
                    f"to {new_state.value_nick}"
                )


bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message", bus_call)


def handle_stop(signalnum, stack_frame):
    print("\nSIGINT received, exiting...")
    loop.quit()


signal.signal(signal.SIGINT, handle_stop)

pipeline.set_state(Gst.State.PLAYING)

loop.run()
