import gi
import signal

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib  # type: ignore # noqa: E402

Gst.init(None)

source = Gst.ElementFactory.make("uridecodebin")
source.set_property(
    "uri",
    "https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm",
)

video_convert = Gst.ElementFactory.make("videoconvert")
video_sink = Gst.ElementFactory.make("autovideosink")

audio_convert = Gst.ElementFactory.make("audioconvert")
audio_resample = Gst.ElementFactory.make("audioresample")
audio_sink = Gst.ElementFactory.make("autoaudiosink")

pipeline = Gst.Pipeline.new("test-pipeline")

pipeline.add(source)
pipeline.add(video_convert)
pipeline.add(video_sink)
pipeline.add(audio_convert)
pipeline.add(audio_resample)
pipeline.add(audio_sink)

video_convert.link(video_sink)
audio_convert.link(audio_resample)
audio_resample.link(audio_sink)


def pad_added_handler(pad: Gst.Element, src: Gst.Pad):
    def get_sink_by_type(type: str):
        if type.startswith("video/x-raw"):
            return video_convert.get_static_pad("sink")
        elif type.startswith("audio/x-raw"):
            return audio_convert.get_static_pad("sink")

    caps = src.get_current_caps()
    structure = caps.get_structure(0)
    type = structure.get_name()
    sink = get_sink_by_type(type)
    if sink is None:
        print(f"Unexpected type '{type}'. Ignoring.")
        return
    elif sink.is_linked():
        print("We already linked. Ignoring.")

    ret = src.link(sink)
    if ret is Gst.PadLinkReturn.OK:
        print(f"Link succeeded (type '{type}').")
    else:
        print(f"Type is '{type}' but link failed with error code: {ret}.")


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
