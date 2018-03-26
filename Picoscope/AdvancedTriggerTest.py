import sys, time

launchtime = time.mktime(time.strptime("2018/01/01 00:00:00", "%Y/%m/%d %H:%M:%S"))
print("%X" % int(launchtime*1e6))

sys.stdout.write("Loading PicoSDK into RAM ... ")
sys.stdout.flush()
try:
	from picosdk import ps2000a
	print("done!")
except ImportError:
	print("import error!")
	sys.exit(1)

sys.stdout.write("Connecting to Picoscope ... ")
sys.stdout.flush()
ps = ps2000a.Device()
status = ps.open_unit()
print(ps.m.pico_tag(status))

if status != ps.m.pico_num("PICO_OK"):
	ps.close_unit()
	exit(1)

print("Device: %s %s" % (ps.info.variant_info, ps.info.batch_and_serial))
print("Driver: %s" % ps.info.driver_version)
print("Firmware: %s/%s" % (ps.info.firmware_version_1, ps.info.firmware_version_2))
print("ADC Range: %+X/%+X" % (ps.info.min_adc, ps.info.max_adc))
print("Memory: %X (%.0f MiB)" % (ps.info.memory, ps.info.memory/8.0/1024.0/1024.0))

channels = ps.m.Channels.map[:ps.info.num_channels] 
for c in channels:
	status, state = ps.get_channel_state(channel=c)
	state.range = ps.m.Ranges.r2v
	state.enabled = True
	sys.stdout.write("Enabling channel %s and setting range to %s ... " % (ps.m.Channels.labels[c], ps.m.Ranges.labels[state.range]))
	sys.stdout.flush()
	status = ps.set_channel(channel=c, state=state)
	if status != ps.m.pico_num("PICO_OK"):
		ps.close_unit()
		exit(1)
	else: print("done!")

samples = 1024
interval = 4
htrigr = 0.2
vtrigr = 0.2

sys.stdout.write("Allocating memory segments ... ")
sys.stdout.flush()
status, max_samples = ps.set_memory_segments(1)
print(ps.m.pico_tag(status))
max_samples = max_samples/len(channels)
print("Maximum samples per channel ... %X (%d MiS)" % (int(max_samples), int(max_samples/1024.0)))

sys.stdout.write("Setting up vertical triggering ... ")
sys.stdout.flush()
status = ps.set_advanced_trigger(
	conditions=(
		ps.m.TriggerConditions(chA=ps.m.TriggerState.true),
		ps.m.TriggerConditions(chB=ps.m.TriggerState.true),
		ps.m.TriggerConditions(chC=ps.m.TriggerState.true),
		ps.m.TriggerConditions(chD=ps.m.TriggerState.true)
	),
	analog=(
		ps.create_trigger_channel_properties(
			channel=ps.m.TriggerChannels.A,
			upperbound=vtrigr,
			mode=ps.m.ThresholdModes.level,
			direction=ps.m.ThresholdDirections.rising),
		ps.create_trigger_channel_properties(
			channel=ps.m.TriggerChannels.B,
			upperbound=vtrigr,
			mode=ps.m.ThresholdModes.level,
			direction=ps.m.ThresholdDirections.rising),
		ps.create_trigger_channel_properties(
			channel=ps.m.TriggerChannels.C,
			upperbound=vtrigr,
			mode=ps.m.ThresholdModes.level,
			direction=ps.m.ThresholdDirections.rising),
		ps.create_trigger_channel_properties(
			channel=ps.m.TriggerChannels.D,
			upperbound=vtrigr,
			mode=ps.m.ThresholdModes.level,
			direction=ps.m.ThresholdDirections.rising)
	)
)
print(ps.m.pico_tag(status))

sys.stdout.write("Setting up horizontal triggering ... ")
sys.stdout.flush()
status = ps.set_horizontal_trigger_ratio(ratio=htrigr)
print(ps.m.pico_tag(status))

while True:
	try:

		print("Triggering enabled: %s" % ps.is_trigger_set())

		buffers = dict()
		for c in channels:
			#sys.stdout.write("Locating channel %s buffer ... " % ps.m.Channels.labels[c])
			#sys.stdout.flush()
			status, buffers[c] = ps.locate_buffer(channel=c, samples=samples, segment=0, mode=ps.m.RatioModes.raw, downsample=1)
			#print(ps.m.pico_tag(status))

		sys.stdout.write("Waiting for trigger ... ")
		sys.stdout.flush()
		status = ps.collect_segment(segment=0, interval=interval, overlapped=False)
		print(ps.m.pico_tag(status))

		print("Trigger time: %X" % int((time.time()-launchtime)*1e6))

		sys.stdout.write("Trigger time offset: ")
		status, offset = ps.get_trigger_time_offset(segment=0)
		if offset is not None: print(offset)
		else: print(ps.m.pico_tag(status))

		data = dict()
		for c in channels:
			status, info = ps.get_buffer_info(buffers[c])
			#sys.stdout.write("Reading channel %s buffer with interval %.2fns... " % (ps.m.Channels.labels[c], info["real_interval"]))
			#sys.stdout.flush()
			status, data[c] = ps.get_buffer_data(buffers[c])
			#print(ps.m.pico_tag(status))

	except KeyboardInterrupt:
		break

ps.close_unit()
