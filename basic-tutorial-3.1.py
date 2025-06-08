import gi
import signal

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib  # type: ignore # noqa: E402

Gst.init(None)

source = Gst.ElementFactory.make("uridecodebin")
source.set_property(
    "uri", "https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm"
)
convert = Gst.ElementFactory.make("audioconvert")
resample = Gst.ElementFactory.make("audioresample")
sink = Gst.ElementFactory.make("autoaudiosink")

pipeline = Gst.Pipeline.new("test-pipeline")

pipeline.add(source)
pipeline.add(convert)
pipeline.add(resample)
pipeline.add(sink)

convert.link(resample)
resample.link(sink)


def pad_added_handler(pad: Gst.Element, src: Gst.Pad):
    sink = convert.get_static_pad("sink")
    if sink.is_linked():
        print("We already linked. Ignoring.")
        return

    caps = src.get_current_caps()
    structure = caps.get_structure(0)
    type = structure.get_name()
    if not type.startswith("audio/x-raw"):
        print(f"It has type '{type}' which is not raw audio. Ignoring.")
        return

    ret = src.link(sink)
    if ret is Gst.PadLinkReturn.OK:
        print(f"Link succeeded (type '{type}').")
    else:
        print(f"Type is '{type}' but link failed with error code: {ret.value_nick}.")


source.connect("pad-added", pad_added_handler)

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
