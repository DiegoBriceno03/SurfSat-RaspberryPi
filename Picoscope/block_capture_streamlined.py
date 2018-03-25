from picosdk import ps2000a
import matplotlib.pyplot as plt
from example_utils import *
import os, time
from time import strftime
import numpy as np

def main():

	p_info("Block mode test started %s" % strftime("%Y-%m-%d %H:%M:%S"))

	outdir = os.path.abspath("data")
	if not (os.path.exists(outdir) and os.path.isdir(outdir)):
		p_error("Output directory not found.")

	ps = ps2000a.Device()
	status = ps.open_unit(serial=None)
	if status != st.pico_num("PICO_OK"):
		p_error("Device open failed with %s" % (st.pico_tag(status)))

	samples = 8192
	interval = 4
	triggv = 0.2
	triggh = 0.2
	triggc = ps.m.Channels.A
	triggd = ps.m.ThresholdDirections.rising
	voltage_range = ps.m.Ranges.r5v

	dname = strftime("%Y%m%d%H%M%S")
	logdir = os.path.join(outdir, dname)
	try:
		if not os.path.exists(logdir): os.mkdir(logdir)
		logfile = os.path.join(logdir, "block_test.log")
		datafile = os.path.join(logdir, "block_data.txt")
	except OSError:
		logfile = None
		datafile = None
		p_warn("Failed to create output directory")

	if logfile is not None:
		try:
			logd = open(logfile, "w")
			p_setlogd(logd)
		except OSError: logd = None
	else: logd = None

	if datafile is not None:
		try:
			datad = open(datafile, "w")
		except OSError: datad = None
	else: datad = None

	p_info("Device connected: %s %s" % (ps.info.variant_info, ps.info.batch_and_serial))
	p_info("Driver: %s" % ps.info.driver_version)
	p_info("Firmware: %s/%s" % (ps.info.firmware_version_1, ps.info.firmware_version_2))

	try:
		dev_channels = ps.m.Channels.map[:ps.info.num_channels]
		channels = dev_channels

		for c in dev_channels:
			status, state = ps.get_channel_state(channel=c)
			state.range = voltage_range
			state.enabled = c in channels
			error_check("Channel %s Setup" % ps.m.Channels.labels[c], ps.set_channel(channel=c, state=state))

		status, max_samples = ps.set_memory_segments(1)
		error_check("Segments setup", status)
		p_info("Maximum number of samples per channel: %d" % int(max_samples / 4))
		if max_samples < 4 * samples:
			bufflen = int(max_samples / 4)
			p_warn("Number of raw samples per channel reduced to %d" % bufflen)
		else: bufflen = samples
		p_info("Raw samples length: %d" % bufflen)

		p_info("Raw sample interval specified as %.2fns" % interval)

		error_check("VTrigger setup", ps.set_simple_trigger(enabled=True, source=triggc, threshold=triggv, direction=ps.m.ThresholdDirections.rising, delay=0, waitfor=0))
		error_check("HTrigger setup", ps.set_horizontal_trigger_ratio(ratio=triggh))

		samples = int(bufflen)
		buffers = dict()
		for c in channels:
			status, buffers[c] = ps.locate_buffer(channel=c, samples=samples, segment=0, mode=ps.m.RatioModes.raw, downsample=1)
			error_check("Buffer chan %s mode %s setup" % (ps.m.Channels.labels[c], "raw"), status)
		p_info("Waiting for trigger")
		error_check("Collection start", ps.collect_segment(segment=0, interval=interval, overlapped=False))
		p_info("Trigger detected")
		data = dict()
		info = None
		for c in channels:
			if info is None:
				status, info = ps.get_buffer_info(buffers[c])
				p_info("Effective interval of the trace %.2fns" % info["real_interval"])
			status, data[c] = ps.get_buffer_data(buffers[c])
			error_check("Buffer chan %s mode %s data" % (ps.m.Channels.labels[c], "raw"), status)

		if datad is not None:
			trigger_time = time.time()
			p_info("Saving data as %s" % os.path.join(logdir, datafile))
			datad.write("Initial Time: 0x%X\n" % int(trigger_time*1e6))
			datad.write("Time Interval: 0x%X\n" % int(info["real_interval"]))
			datad.write("Voltage Ranges (Channel A, B, C, D): 0x%X, 0x%X, 0x%X, 0x%X\n" % (voltage_range, voltage_range, voltage_range, voltage_range))
			datad.write("Data (Channel A, B, C, D):\n")
			for a, b, c, d in zip(data[channels[0]], data[channels[1]], data[channels[2]], data[channels[3]]):
				datad.write("%+05X, %+05X, %+05X, %+05X\n" % (a, b, c, d))

		fig, pts = plt.subplots(1, 1)

		timecut = info["real_interval"] * info["samples"]
		time_units = ps.m.TimeUnits.ns
		while timecut > 1000:
			timecut /= 1000.0
			time_units += 1
		time_step = timecut / info["samples"]
		graph_limit = [0, time_step * (info["samples"] - 1)]
		time_domain = time_step * np.arange(0, info["samples"])

		for i in range(0, len(channels)):
			c = channels[i]
			p = pts
			p.set_xlim(graph_limit)

			label = "Ch%s M%s [%s]" % (ps.m.Channels.labels[c], "raw", ps.m.TimeUnits.ascii_labels[time_units])

			data_limit = min(len(data[c]), info["samples"])
			li, = p.plot(time_domain[:data_limit], data[c][:data_limit], label=label)
			li.set_color(colors[c])

			p.legend()

			if triggc == c:
				triggx = triggh * samples
				triggy = triggv * ps.info.max_adc
				marker = '^' if triggd == ps.m.ThresholdDirections.rising else ('v' if triggd == ps.m.ThresholdDirections.falling else 'D')
				li, = p.plot([triggx * time_step], [triggy], marker, ms=9)
				li.set_color(triggcolor)
			p.grid()
		if logdir is not None:
			saveas = "block_plot.png"
			saveas = os.path.join(logdir, saveas)
			p_info("Saving graph as %s" % saveas)
			try: fig.savefig(saveas, dpi=300)
			except OSError: p_warn("Failed to write %s" % saveas)
		plt.show(block=True)
	finally:
		if logd is not None:
			try: logd.close()
			except OSError: pass
		if datad is not None:
			try: datad.close()
			except OSError: pass
		ps.close_unit()

if __name__ == "__main__": main()
