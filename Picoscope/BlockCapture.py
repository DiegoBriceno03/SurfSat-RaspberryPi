from picosdk import ps2000a
import picosdk.picostatus as st
import matplotlib.pyplot as plt
import os, time
from time import strftime
import numpy as np

def print_error(msg, end=True):
	print("ERRO: %s" % msg)
	if end: exit(1)

def error_check(tag, status):
	if status != st.pico_num("PICO_OK"):
		print_error("%s %s" % (tag, st.pico_tag(status)))

def main():

	print("INFO: Block mode test started %s" % strftime("%Y-%m-%d %H:%M:%S"))

	outdir = os.path.abspath("data")
	if not (os.path.exists(outdir) and os.path.isdir(outdir)):
		print_error("Output directory not found.")

	ps = ps2000a.Device()
	status = ps.open_unit(serial=None)
	if status != st.pico_num("PICO_OK"):
		print_error("Device open failed with %s" % (st.pico_tag(status)))

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
		datafile = os.path.join(logdir, "block_data.txt")
	except OSError:
		datafile = None
		print("WARN: Failed to create output directory")

	if datafile is not None:
		try: datad = open(datafile, "w")
		except OSError: datad = None
	else: datad = None

	print("INFO: Device connected: %s %s" % (ps.info.variant_info, ps.info.batch_and_serial))
	print("INFO: Driver: %s" % ps.info.driver_version)
	print("INFO: Firmware: %s/%s" % (ps.info.firmware_version_1, ps.info.firmware_version_2))

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
		print("INFO: Maximum number of samples per channel: %d" % int(max_samples / 4))
		if max_samples < 4 * samples:
			bufflen = int(max_samples / 4)
			print("WARN: Number of raw samples per channel reduced to %d" % bufflen)
		else: bufflen = samples
		print("INFO: Raw samples length: %d" % bufflen)

		print("INFO: Raw sample interval specified as %.2fns" % interval)

		error_check("VTrigger setup", ps.set_simple_trigger(enabled=True, source=triggc, threshold=triggv, direction=ps.m.ThresholdDirections.rising, delay=0, waitfor=0))
		error_check("HTrigger setup", ps.set_horizontal_trigger_ratio(ratio=triggh))

		samples = int(bufflen)
		buffers = dict()
		for c in channels:
			status, buffers[c] = ps.locate_buffer(channel=c, samples=samples, segment=0, mode=ps.m.RatioModes.raw, downsample=1)
			error_check("Buffer chan %s setup" % ps.m.Channels.labels[c], status)
		print("INFO: Waiting for trigger")
		error_check("Collection start", ps.collect_segment(segment=0, interval=interval, overlapped=False))
		print("INFO: Trigger detected")
		data = dict()
		info = None
		for c in channels:
			if info is None:
				status, info = ps.get_buffer_info(buffers[c])
				print("INFO: Effective interval of the trace %.2fns" % info["real_interval"])
			status, data[c] = ps.get_buffer_data(buffers[c])
			error_check("Buffer chan %s data" % ps.m.Channels.labels[c], status)

		if datad is not None:
			trigger_time = time.time()
			print("INFO: Saving data as %s" % os.path.join(logdir, datafile))
			datad.write("Initial Time: 0x%X\n" % int(trigger_time*1e6))
			datad.write("Time Interval: 0x%X\n" % int(info["real_interval"]))
			datad.write("Voltage Ranges (Channel A, B, C, D): 0x%X, 0x%X, 0x%X, 0x%X\n" % (voltage_range, voltage_range, voltage_range, voltage_range))
			datad.write("Data (Channel A, B, C, D):\n")
			for a, b, c, d in zip(data[channels[0]], data[channels[1]], data[channels[2]], data[channels[3]]):
				datad.write("%+05X, %+05X, %+05X, %+05X\n" % (a, b, c, d))

		timecut = info["real_interval"] * info["samples"]
		time_units = ps.m.TimeUnits.ns
		while timecut > 1000:
			timecut /= 1000.0
			time_units += 1
		time_step = timecut / info["samples"]
		graph_limit = [0, time_step * (info["samples"] - 1)]
		time_domain = time_step * np.arange(0, info["samples"])
		plt.xlim(graph_limit)

		for i in range(0, len(channels)):
			c = channels[i]

			label = "Ch%s [%s]" % (ps.m.Channels.labels[c], ps.m.TimeUnits.ascii_labels[time_units])

			data_limit = min(len(data[c]), info["samples"])
			plt.plot(time_domain[:data_limit], data[c][:data_limit], label=label)

			plt.legend()

			if triggc == c:
				triggx = triggh * samples
				triggy = triggv * ps.info.max_adc
				marker = '^' if triggd == ps.m.ThresholdDirections.rising else ('v' if triggd == ps.m.ThresholdDirections.falling else 'D')
				plt.plot([triggx * time_step], [triggy], marker, ms=9, label=("Ch%s Trigger" % ps.m.Channels.labels[c]))
			plt.grid()
		if logdir is not None:
			saveas = os.path.join(logdir, "block_plot.png")
			print("INFO: Saving graph as %s" % saveas)
			try: plt.savefig(saveas, dpi=300)
			except OSError: print("WARN: " + "Failed to write %s" % saveas)
		#plt.show(block=True)
	finally:
		if datad is not None:
			try: datad.close()
			except OSError: pass
		ps.close_unit()

if __name__ == "__main__": main()
