import matplotlib.pyplot as plt
from picosdk import ps2000a

# number of samples per channel
samples = 1024
# interval between samples in ns
interval = 4

if __name__ == "__main__":
	ps = ps2000a.Device()
	status = ps.open_unit()
	if status == ps.m.pico_num("PICO_OK"):
		time = [interval*i for i in range(samples)]
		data = {}
		for channel in [ps.m.Channels.A, ps.m.Channels.B, ps.m.Channels.C, ps.m.Channels.D]:
			s, state = ps.get_channel_state(channel=channel)
			state.enabled = True
			state.range = ps.m.Ranges.r5v
			status = ps.set_channel(channel=channel, state=state)
			if status == ps.m.pico_num("PICO_OK"):
				s, index = ps.locate_buffer(channel=channel,
											samples=samples,
											segment=0,
											mode=ps.m.RatioModes.raw,
											downsample=0)
				status = ps.collect_segment(segment=0, interval=interval)
				if status == ps.m.pico_num("PICO_OK"):
					status, data[channel] = ps.get_buffer_volts(index=index)
				else: print(ps.m.pico_tag(status))
			else: print(ps.m.pico_tag(status))
		print(len(time))
		plt.plot(time, data[ps.m.Channels.A], label='Channel A')
		plt.plot(time, data[ps.m.Channels.B], label='Channel B')
		plt.plot(time, data[ps.m.Channels.C], label='Channel C')
		plt.plot(time, data[ps.m.Channels.D], label='Channel D')
		plt.title('Picoscope Data')
		plt.xlabel('Time (ns)')
		plt.ylabel('Voltage (V)')
		plt.legend()		
		plt.show()
	else: print(ps.m.pico_tag(status))
