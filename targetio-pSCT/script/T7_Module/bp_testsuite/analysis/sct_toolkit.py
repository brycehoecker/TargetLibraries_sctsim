from __future__ import division, print_function
import sys, os, pwd
import datetime
import warnings
import h5py
import numpy as np

try:
    import target_io
    import target_driver
except ImportError,e:
    warnings.warn("{}: proceeding without module may result in limited usage".format(e),
                  stacklevel=2)

class pedestal(object):
    def __init__(self, ped_database=None):
	""" 
        class for handling pedestal databases

        Args:
          ped_database: (optional) If not 'None', loads an existing pedestal database 
                        to be used for pedestal subtraction, etc.; type: str, default: Non. 
                        Note: new databases should be created with new_database() 
        """
        self._generate_maps()
        self.ped_database = ped_database
        if ped_database:
            self._load_database(ped_database)

    def _add_branch(self, ped_waveform, module, asic, channel):
        """ create new branch to hold pedestal waveforms """
	branch_name = "Module{}/Asic{}/Channel{}".format(module ,asic, channel)
	branch = self.ped_database.create_group(branch_name)
	branch.create_dataset("pedestal", data=ped_waveform)

    def _average_events(self, mod_i, module, asic, channel):
        """ calculate average over all events in a given module, asic, and channel """
        ped_array = np.zeros(512*32)
        count_array = np.zeros(512*32)
	for ievt in xrange(self.n_events):
            if(ievt%1000==0):
                sys.stdout.write('\r')
                sys.stdout.write("[%-100s] %d%%" % ('='*int((ievt)*100.0/(self.n_events)),
                                (ievt)*100.0/(self.n_events)))
                sys.stdout.flush() 

	    rawdata = self.reader.GetEventPacket(ievt,(4*mod_i+asic)\
                      *16//self.channels_per_packet+channel//self.channels_per_packet)
	    self.packet.Assign(rawdata, self.reader.GetPacketSize())
	    block = int(self.packet.GetColumn()*8+self.packet.GetRow())
	    phase = int(self.packet.GetBlockPhase())
            #packetID = self.packet.GetPacketID()
            #if packetID[0]:   #checks for lost packets 
            wf = self.packet.GetWaveform(channel%self.channels_per_packet)
	    samples = map(wf.GetADC, self.waveform)
	    if np.amin(samples)>100:   #reject events with data spikes
                cells = self._get_cell_ids(block, phase)
		ped_array[cells]+=samples
		count_array[cells]+=1

        pedestal = ped_array/count_array
        ped_waveform = np.round(pedestal,decimals=2)
        self._add_branch(ped_waveform, module, asic, channel)
        sys.stdout.write('\n')

    def _calculate_pedestals(self):
        """ iterate through modules, asics, and channels to calculate all pedestals """
	for mod_i, module in enumerate(self.modules):
	    for asic in self.asics:
		for channel in self.channels:
                    print("Processing {} Events from Module {}, Asic {}, Channel {}".format(
                           self.n_events, module, asic, channel))
                    self._average_events(mod_i, module, asic, channel)

    def _check_type(self,data):
        """ check input type and map to integer(s) list """
        if isinstance(data,list):
            return map(int,data)
        elif isinstance(data,int):
            return [int(data)]
        else:
            raise TypeError('Input must be an integer or a list, got {}'.format(type(data)))

    def _generate_maps(self):
        """ generates block and cell id mappings """
        block_id_map = [0]
        for i in xrange(511):
            if block_id_map[-1]%2==0:
                next_block = (block_id_map[-1]+3)%512
                block_id_map.append(next_block)
            else:
                next_block = (block_id_map[-1]-1)%512
                block_id_map.append(next_block)

        cell_id_map = np.array([])
        block_cells = np.arange(32)
        for i in xrange(512):
            cell_id_map = np.append(cell_id_map,block_id_map[i]*32+block_cells)

        self.block_id_map = block_id_map
        self.cell_id_map = cell_id_map.astype(int)

    def _get_cell_ids(self, block, phase):
        """ 
        convert block to cell id, shift to account for phase, return cell ids   
        """
        first_cell = self.block_id_map.index(int(block))*32
        cells = np.arange(first_cell,first_cell+self.n_samples,1)+phase
        shifted_cells = np.mod(cells,512*32)
        return self.cell_id_map[shifted_cells]

    def _get_pedestal(self, module, asic, channel):
        """ return pedestal array """
        ped_group = self.ped_database['Module{}/Asic{}/Channel{}'.format(module,asic,channel)]
        return np.array(ped_group['pedestal'])

    def _load_database(self,name):
        """ load an existing hdf5 pedestal database """
        try:
            self.ped_database = h5py.File(name,"r",libver='latest')
            self.n_samples = self.ped_database.attrs['waveform_length']
            self.modules = self.ped_database.attrs['modules']
            self.asics = self.ped_database.attrs['asics']
            self.channels = self.ped_database.attrs['channels']
        except IOError:
            raise IOError("file '{}' not found. Check name and/or path ".format(name))

    def _new_database(self, name, check_overwrite):
        """ generates a new hdf5 database """
        if check_overwrite:
	    if os.path.isfile(name):
		print("The file '{}' already exists.".format(name))
		answers = {"yes","no"}
		choice = None
		while True:
		    choice = raw_input("Would you like to overwrite it? (yes/no) ").lower()
		    if choice in answers:
			break
		    else:
			print("Not an acceptable input, try again!")
		if choice == 'no':
		    raise SystemExit('exiting...')

        self.ped_database = h5py.File(name,"w",libver='latest')

    def _set_attributes(self):
        """ assign metadata attributes to database """
        self.ped_database.attrs['name'] = str(self.ped_database.filename)
        self.ped_database.attrs['date'] = str(datetime.datetime.today())
        self.ped_database.attrs['created_by'] = pwd.getpwuid(os.getuid()).pw_name
        self.ped_database.attrs['comments'] = self.comments
        self.ped_database.attrs['run_path'] = self.filename
        self.ped_database.attrs['run'] = self.run_number
        self.ped_database.attrs['modules'] = self.modules
        self.ped_database.attrs['asics'] = self.asics
        self.ped_database.attrs['channels'] = self.channels
        self.ped_database.attrs['channels_per_packet'] = self.channels_per_packet
        self.ped_database.attrs['packet_size'] = self.packet_size
        self.ped_database.attrs['waveform_length'] = self.n_samples
        self.ped_database.attrs['num_events'] = self.n_events
        self.ped_database.attrs['keys'] = "pedestal"
        self.ped_database.attrs['structure'] = "Module#/Asic#/Channel#/'key'"

    def _set_channels_per_packet(self):
        """ assign channels per packet  """
	self.channels_per_packet = int((0.5*self.packet_size-10.)/(self.n_samples+1.))

    def _set_data_packet_parameters(self):
        """ assigns data packet characteristics """
	self.reader = target_io.EventFileReader(self.filename)
	self.n_events = self.reader.GetNEvents()
	rawdata = self.reader.GetEventPacket(0,0)
	self.packet = target_driver.DataPacket()
	self.packet_size = self.reader.GetPacketSize()
	self.packet.Assign(rawdata, self.packet_size)
	wf = self.packet.GetWaveform(0)
	self.n_samples = wf.GetSamples()
        self.waveform = np.arange(self.n_samples,dtype=int)
	self._set_channels_per_packet()

    def _set_run_file_path(self):
        """ assigns file path for run number """
	self.filename = "{}/target5and7data/run{}.fits".format(os.environ['HOME'],
			 self.run_number)
	if not os.path.isfile(self.filename):
	    new_path = "{0}/target5and7data/runs_{1}0000_"\
		       "through_{1}9999/".format(os.environ['HOME'],
			str(self.run_number)[:-4])
	    self.filename = new_path+"run{}.fits".format(self.run_number)
	    if not os.path.isfile(self.filename):
		raise IOError("File run{}.fits cannot be located".format(self.run_number))

    def _set_run_parameters(self, run_number, modules, asics, channels, filepath, comments):
        """ assign parameters to be used for constructing pedestal database """
        self.run_number = int(run_number)
        print('Creating pedestal database from run {}'.format(self.run_number))
        self.modules = self._check_type(modules)
        if asics:
            self.asics = self._check_type(asics)
        if channels:
            self.channels = self._check_type(channels)
        if filepath:
            self.filename = str(filepath)
            if not os.path.isfile(self.filename):
                raise IOError("Invalid file path: {} cannot be located".format(self.filename))
        if not filepath:
            self._set_run_file_path()
        self.comments = str(comments)

    def close_database(self):
        """ close currently loaded/created pedestal database """
        if isinstance(self.ped_database, h5py.File):
            self.ped_database.close()
        else:
            warnings.warn("No database currently open!",stacklevel=2)

    def get_attributes(self,verbose=True):
        """ returns list of tuples containing database attributes """
        attributes = [tuple([str(key), val]) for key, val in sorted(self.ped_database.attrs.items())]
        if verbose:
            print('\n'.join('{}: {}'.format(key, val) for key, val in attributes))
        return attributes

    def get_block_id_map(self):
        """ returns the block id map """
        return self.block_id_map

    def get_branch(self,branch_name):
        """ 
        returns pointer to data in a single specified branch

        Args:
          branch_name: (required) name of branch; type: str
        """
        if isinstance(self.ped_database, h5py.File):
            return self.ped_database.get(str(branch_name))
        else:
            warnings.warn("No database currently open!",stacklevel=2)

    def get_branches(self, verbose=False, filter_by=None):
        """ 
        returns a list of branch names for each group/subgroup in database

        Args:
          verbose: (optional) if True, prints branch names; type: bool, default: False 
          filter_by: (optional) return all branch names matching specified pattern(s),
                     ex. single ["Module118/Asic10/"] or mutltiple ["Module118","Channel10"];
                     type: list(str), default: None. Note: case sensitive
        """
        if isinstance(self.ped_database, h5py.File):
            branches = set()
            self.ped_database.visit(branches.add)
            if filter_by:
                branches = [b for b in branches if all([f in b for f in set(filter_by)])]
            if verbose:
                print('\n'.join(b for b in branches))
            return map(str,branches)
        else:
            warnings.warn("No database currently open!",stacklevel=2)

    def get_cell_id_map(self):
        """ returns the cell id map """
        return self.cell_id_map

    def get_database(self):
        """ returns currently loaded pedestal database """
        if isinstance(self.ped_database, h5py.File):
            return self.ped_database
        else:
            warnings.warn("No database currently open!",stacklevel=2)

    def get_database_name(self):
        """ returns name of current pedestal database """
        if isinstance(self.ped_database, h5py.File):
            return str(self.ped_database.filename)
        else:
            warnings.warn("No database currently open!",stacklevel=2)

    def get_pedestal_waveform(self, module, asic, channel, block, phase):
        """
        returns the pedestal waveform for a given trigger block

        args:
          module: (required) module number; type: int
          asic: (required) asic number; type: int
          channel: (required) channel number; type: int
          block: (required) block number; type: int
          phase: (required) phase number; type: int
        """
        pedestal = self._get_pedestal(module, asic, channel)
        cells = self._get_cell_ids(block, phase)
        ped_values = pedestal[cells]
        return ped_values

    def make_pedestal_database(self, ped_name, run_number, modules, 
                               asics=range(4),channels=range(16), filepath=None, 
                               check_overwrite=True, comments=None):
        """ 
        create a new pedestal database 

        Args:
          ped_name: (required) full name and path for new database; type: str
          run_number: (required) run number to be used for pedestal data; type: int
          modules: (required) ordered list of module numbers; ex [123,124,...]
          asics: (optional) list of asics used in run_number; default 0-3
          channels: (optional) list of channels used in run_number; default 0-15
          filepath: (optional) if data is not in target5and7data, specify alternate 
                    path and name; type: str
          check_overwrite: (optional) if True, checks if ped_name exists before blindly
                          overwriting it; default True
        """
	#Check if remote data directory is mounted
	if os.path.ismount(os.environ['HOME']+'/target5and7data')==True:
	    print("Output-directory is mounted")
	else:
	    print("Cannot connect to the remote output directory!")
	    print("Make sure '{}/target5and7data' is mounted!".format(os.environ['HOME']))
	    raise SystemExit

        self._set_run_parameters(run_number, modules, asics=asics, channels=channels, 
                                 filepath=filepath, comments=comments)
        self._new_database(ped_name, check_overwrite)
        self._set_data_packet_parameters()
        self._calculate_pedestals()
        self._set_attributes()
        self.close_database()
        print("Database successfully created, saving to {}".format(ped_name))

class waveform(object):
    def __init__(self, database=None):
        """
        class for writing waveform data

        Args:
          database: (optional) If not 'None', loads an existing database; 
                     type: str, default: None.
        """
        self.ped_database = None
        self.database = database
        if database:
            self._load_database(database)

    def _add_branch(self, event, block , phase, waveform, timestamp,
                    lost_packets, module, asic, channel):
        """ create new branch to hold waveform data """
	branch_name = "Module{}/Asic{}/Channel{}".format(module ,asic, channel)
	branch = self.database.create_group(branch_name)
	branch.create_dataset("event", data=event)
	branch.create_dataset("block", data=block)
	branch.create_dataset("phase", data=phase)
        branch.create_dataset("timestamp", data=timestamp)
	branch.create_dataset("waveform", data=waveform)
        branch.create_dataset("lost_packets", data=lost_packets)

    def _add_ped_sub_branch(self, event, block , phase, waveform, cal_waveform, 
                            timestamp, lost_packets, module, asic, channel,
                            amplitude, position, charge):
        """ create new branch to hold waveform data """
        branch_name = "Module{}/Asic{}/Channel{}".format(module ,asic, channel)
        branch = self.database.create_group(branch_name) 
	branch.create_dataset("event", data=event)
	branch.create_dataset("block", data=block)
	branch.create_dataset("phase", data=phase)
        branch.create_dataset("timestamp", data=timestamp)
	branch.create_dataset("waveform", data=waveform)
	branch.create_dataset("cal_waveform",data=cal_waveform)
        branch.create_dataset("lost_packets", data=lost_packets)
        branch.create_dataset("amplitude", data=amplitude)
        branch.create_dataset("position", data=position)
        branch.create_dataset("charge", data=charge)

    def _check_type(self,data):
        """ check input type and map to integer(s) list """
        if isinstance(data,list):
            return map(int,data)
        elif isinstance(data,int):
            return [data]
        else:
            raise TypeError('Input must be integer or list, got {}'.format(type(data)))

    def _generate_maps(self):
        """ generates block and cell id mappings """
        block_id_map = [0]
        for i in xrange(511):
            if block_id_map[-1]%2==0:
                next_block = (block_id_map[-1]+3)%512
                block_id_map.append(next_block)
            else:
                next_block = (block_id_map[-1]-1)%512
                block_id_map.append(next_block)

        cell_id_map = np.array([])
        block_cells = np.arange(32)
        for i in xrange(512):
            cell_id_map = np.append(cell_id_map,block_id_map[i]*32+block_cells)

        self.block_id_map = block_id_map
        self.cell_id_map = cell_id_map.astype(int)

    def _get_cell_ids(self, block, phase):
        """ convert block to cell id, shift for phase, return cell ids """
        first_cell = self.block_id_map.index(int(block))*32
        cells = np.arange(first_cell,first_cell+self.n_samples,1)+phase
        shifted_cells = np.mod(cells,512*32)
        return self.cell_id_map[shifted_cells]

    def _get_pedestal(self, module, asic, channel):
        """ return pedestal array """
        ped_group = self.ped_database['Module{}/Asic{}/Channel{}'.format(module,asic,channel)]
        return np.array(ped_group['pedestal'])

    def _load_database(self,name):
        """ load an existing hdf5 database """
        try:
            self.database = h5py.File(name,"r",libver='latest')
            self.n_samples = self.database.attrs['waveform_length']
            self.n_events = self.database.attrs['num_events']
            self.modules = self.database.attrs['modules']
            self.asics = self.database.attrs['asics']
            self.channels = self.database.attrs['channels']
            self.run_number = self.database.attrs['run']
        except IOError:
            raise IOError("file '{}' not found. Check name and/or path ".format(name))

    def _load_ped_database(self,ped_name):
        """ load an existing hdf5 pedestal database """
        try:
            self.ped_database = h5py.File(ped_name,"r",libver='latest')
        except IOError:
            raise IOError("file '{}' not found. Check name and/or path ".format(name))

    def _new_database(self, name, check_overwrite):
        """ generates a new hdf5 database """
        if check_overwrite:
	    if os.path.isfile(name):
		print("The file '{}' already exists.".format(name))
		answers = {"yes","no"}
		choice = None
		while True:
		    choice = raw_input("Would you like to overwrite it? (yes/no) ").lower()
		    if choice in answers:
			break
		    else:
			print("Not an acceptable input, try again!")
		if choice == 'no':
		    raise SystemExit('exiting...')

        self.database = h5py.File(name,"w",libver='latest')

    def _process_events(self):
        """ iterate through modules, asics, and channels to process all events """
	for mod_i, module in enumerate(self.modules):
	    for asic in self.asics:
		for channel in self.channels:
                    print("Processing {} Events from Module {}, Asic {}, Channel {}".format(
                           self.n_events, module, asic, channel))
                    self._write_events(mod_i, module, asic, channel)

    def _process_ped_sub_events(self):
        """ iterate through modules, asics, and channels to process/subtract all events """
        for mod_i, module in enumerate(self.modules):
            for asic in self.asics:
                for channel in self.channels:
                    print("Processing {} Events from Module {}, Asic {}, Channel {}".format(
                           self.n_events, module, asic, channel))
                    self._write_subtracted_events(mod_i, module, asic, channel)

    def _set_attributes(self):
        """ assign metadata attributes to database """
        self.database.attrs['name'] = str(self.database.filename)
        self.database.attrs['date'] = str(datetime.datetime.today())
        self.database.attrs['created_by'] = pwd.getpwuid(os.getuid()).pw_name
        self.database.attrs['comments'] = self.comments
        self.database.attrs['run_path'] = self.filename
        self.database.attrs['run'] = self.run_number
        self.database.attrs['modules'] = self.modules
        self.database.attrs['asics'] = self.asics
        self.database.attrs['channels'] = self.channels
        self.database.attrs['channels_per_packet'] = self.channels_per_packet
        self.database.attrs['packet_size'] = self.packet_size
        self.database.attrs['waveform_length'] = self.n_samples
        self.database.attrs['num_events'] = self.n_events
        self.database.attrs['structure'] = "Module#/Asic#/Channel#/'key'"
        if self.ped_database:
            self.database.attrs['keys'] = "event, block, phase, timestamp, waveform, cal_waveform," \
                                           " lost_packets, amplitude, position, charge"
            self.database.attrs['ped_name'] = str(self.ped_database.filename)
            self.database.attrs['charge_interval'] = "-{}, +{}".format(self.lower, self.upper)
        else:
            self.database.attrs['keys'] = "event, block, phase, timestamp, waveform, lost_packets"

    def _set_channels_per_packet(self):
        """ assign channels per packet  """
	self.channels_per_packet = int((0.5*self.packet_size-10.)/(self.n_samples+1.))

    def _set_data_packet_parameters(self):
        """ assigns data packet characteristics """
	self.reader = target_io.EventFileReader(self.filename)
	self.n_events = self.reader.GetNEvents()
	rawdata = self.reader.GetEventPacket(0,0)
	self.packet = target_driver.DataPacket()
	self.packet_size = self.reader.GetPacketSize()
	self.packet.Assign(rawdata, self.packet_size)
	wf = self.packet.GetWaveform(0)
	self.n_samples = wf.GetSamples()
        self.waveform = np.arange(self.n_samples, dtype=int)
	self._set_channels_per_packet()

    def _set_run_file_path(self):
        """ assigns file path for run number """
	self.filename = "{}/target5and7data/run{}.fits".format(os.environ['HOME'],
			 self.run_number)
	if not os.path.isfile(self.filename):
	    new_path = "{0}/target5and7data/runs_{1}0000_"\
		       "through_{1}9999/".format(os.environ['HOME'],
			str(self.run_number)[:-4])
	    self.filename = new_path+"run{}.fits".format(self.run_number)
	    if not os.path.isfile(self.filename):
		raise IOError("File run{}.fits cannot be located".format(self.run_number))

    def _set_run_parameters(self, run_number, modules, asics, channels, 
                            filepath, comments, charge_interval):
        """ assign parameters to be used for constructing pedestal database """
        self.run_number = int(run_number)
        print('Creating database for run {}'.format(self.run_number))
        self.modules = self._check_type(modules)
        if asics:
            self.asics = self._check_type(asics)
        if channels:
            self.channels = self._check_type(channels)
        if filepath:
            self.filename = str(filepath)
            if not os.path.isfile(self.filename):
                raise IOError("Invalid file path: {} cannot be located".format(self.filename))
        if not filepath:
            self._set_run_file_path()
        self.comments = str(comments)
        assert len(charge_interval)==2, "charge_interval must be list of length 2, i.e. [lower,upper]"
        self.lower = int(np.fabs(charge_interval[0]))
        self.upper = int(np.fabs(charge_interval[1]))

    def _write_events(self, mod_i, module, asic, channel):
        """ write all events in a given module, asic, and channel """
        event = np.zeros(self.n_events,dtype=int)
        block = np.zeros(self.n_events,dtype=int)
        phase = np.zeros(self.n_events,dtype=int)
        timestamp = np.zeros(self.n_events,dtype=int)
        waveform = np.zeros((self.n_events,self.n_samples),dtype=int)
        lost_packets = list()
	for ievt in xrange(self.n_events):
            if(ievt%1000==0):
		sys.stdout.write('\r')
		sys.stdout.write("[%-100s] %d%%" % ('='*int((ievt)*100.0/(self.n_events)), 
                                (ievt)*100.0/(self.n_events)))
		sys.stdout.flush()

	    rawdata = self.reader.GetEventPacket(ievt,(4*mod_i+asic)\
                      *16//self.channels_per_packet+channel//self.channels_per_packet)
	    self.packet.Assign(rawdata, self.reader.GetPacketSize())
            event[ievt] = int(ievt)
            block[ievt] = int(self.packet.GetColumn()*8+self.packet.GetRow())
	    phase[ievt] = int(self.packet.GetBlockPhase())
            timestamp[ievt] = self.packet.GetTACKTime()
            packetID = self.packet.GetPacketID()
	    if not packetID[0]:
		lost_packets.append([event[ievt],timestamp[ievt]])
	    else:
	        wf = self.packet.GetWaveform(channel%self.channels_per_packet)
	        waveform[ievt,:] = map(wf.GetADC, self.waveform)

        lost_packets = np.array(lost_packets).reshape(-1,2)
        self._add_branch(event, block, phase, waveform, timestamp, lost_packets, module, asic, channel)
        sys.stdout.write('\n')

    def _write_subtracted_events(self, mod_i, module, asic, channel):
        """ write pedestal subtracted events in a given module, asic, and channel """
        event = np.zeros(self.n_events,dtype=int)
        block = np.zeros(self.n_events,dtype=int)
        phase = np.zeros(self.n_events,dtype=int)
        timestamp = np.zeros(self.n_events,dtype=int)
        waveform = np.zeros((self.n_events,self.n_samples),dtype=int)
        cal_waveform = np.zeros((self.n_events,self.n_samples),dtype=int)
        amplitude = np.zeros(self.n_events,dtype=float)
        position = np.zeros(self.n_events,dtype=int)
        charge = np.zeros(self.n_events,dtype=float)
        pedestal = self._get_pedestal(module, asic, channel)
        lost_packets = list()
        for ievt in xrange(self.n_events):
            if(ievt%1000==0):
                sys.stdout.write('\r')
                sys.stdout.write("[%-100s] %d%%" % ('='*int((ievt)*100.0/(self.n_events)),
                                (ievt)*100.0/(self.n_events)))
                sys.stdout.flush()

            rawdata = self.reader.GetEventPacket(ievt,(4*mod_i+asic)\
                      *16//self.channels_per_packet+channel//self.channels_per_packet)
            self.packet.Assign(rawdata, self.reader.GetPacketSize())
            event[ievt] = int(ievt)
            block[ievt] = b = int(self.packet.GetColumn()*8+self.packet.GetRow())
            phase[ievt] = p = int(self.packet.GetBlockPhase())
            timestamp[ievt] = self.packet.GetTACKTime()
            packetID = self.packet.GetPacketID()
            if not packetID[0]:
                lost_packets.append([event[ievt],timestamp[ievt]])
            else:
		wf = self.packet.GetWaveform(channel%self.channels_per_packet)
		samples = map(wf.GetADC, self.waveform)
		waveform[ievt,:] = samples
		cells = self._get_cell_ids(b, p)
		ped_values = pedestal[cells]
                cal_samples = np.array(samples)-ped_values
		cal_waveform[ievt,:] = cal_samples
                amplitude[ievt] = np.amax(cal_samples)
                peak_pos = np.argmax(cal_samples)
                position[ievt] = peak_pos
                if peak_pos < self.lower:
                    charge[ievt] = np.sum(cal_samples[:peak_pos+self.upper])
                elif peak_pos >=  (self.n_samples-self.upper):
                    charge[ievt] = np.sum(cal_samples[peak_pos-self.lower:])
                else:
                    charge[ievt] = np.sum(cal_samples[peak_pos-self.lower:peak_pos+self.upper])

        cal_waveform = np.round(cal_waveform,decimals=2)
        lost_packets = np.array(lost_packets).reshape(-1,2)
        self._add_ped_sub_branch(event, block, phase, waveform, cal_waveform, 
                                 timestamp, lost_packets, module, asic, channel,
                                 amplitude, position, charge)
        sys.stdout.write('\n')

    def close_database(self):
        """ close currently loaded/created pedestal database """
        if isinstance(self.database, h5py.File):
            self.database.close()
        else:
            warnings.warn("No database currently open!",stacklevel=2)
        if isinstance(self.ped_database, h5py.File):
            self.ped_database.close()

    def get_attributes(self,verbose=True):
        """ returns list of tuples containing database attributes """
        attributes = [tuple([str(key), val]) for key, val in sorted(self.database.attrs.items())]
        if verbose:
            print('\n'.join('{}: {}'.format(key, val) for key, val in attributes))
        return attributes

    def get_asic_list(self):
        """ returns list of asics """
        return list(self.asics)

    def get_block_id_map(self):
        """ returns the block id map """
        return self.block_id_map

    def get_branch(self,branch_name):
        """ 
        returns pointer to data in a single specified branch

        Args:
          branch_name: (required) name of branch; type: str
        """
        if isinstance(self.database, h5py.File):
            return np.array(self.database.get(str(branch_name)))
        else:
            warnings.warn("No database currently open!",stacklevel=2)

    def get_branches(self, verbose=False, filter_by=None):
        """ 
        returns a list of branch names for each group/subgroup in database

        Args:
          verbose: (optional) if True, prints branch names; type: bool, default: False 
          filter_by: (optional) return all branch names matching specified pattern(s),
                     ex. single ["Module118/Asic10/"] or mutltiple ["Module118","Channel10"];
                     type: list(str), default: None. Note: case sensitive
        """
        if isinstance(self.database, h5py.File):
            branches = set()
            self.database.visit(branches.add)
            if filter_by:
                branches = [b for b in branches if all([f in b for f in set(filter_by)])]
            if verbose:
                print('\n'.join(b for b in branches))
            return map(str,branches)
        else:
            warnings.warn("No database currently open!",stacklevel=2)

    def get_cell_id_map(self):
        """ returns the cell id map """
        return self.cell_id_map

    def get_channel_list(self):
        """ returns waveform length """
        return list(self.channels)

    def get_database(self):
        """ returns currently loaded pedestal database """
        if isinstance(self.database, h5py.File):
            return self.database
        else:
            warnings.warn("No database currently open!",stacklevel=2)

    def get_database_name(self):
        """ returns name of current pedestal database """
        if isinstance(self.database, h5py.File):
            return str(self.database.filename)
        else:
            warnings.warn("No database currently open!",stacklevel=2)

    def get_module_list(self):
        """ returns waveform length """
        return list(self.modules)

    def get_n_samples(self):
        """ returns waveform length """
        return self.n_samples

    def get_n_events(self):
        """ returns number of events in run """
        return self.n_events

    def write_events(self, run_number, modules, outname=None, outdir='./runFiles', 
                     ped_name=None, asics=range(4),channels=range(16), filepath=None, 
                     check_overwrite=True, comments=None, charge_interval=[8,8]):
        """ 
        create a new database from waveform data

        Args:
          run_number: (required) run number; type: int
          modules: (required) ordered list of module numbers; type: int or list of ints 
                   ex. 123 or [123, 124, ...]
          outname: (optional) specify custom output name for h5py database; type: str,
                   default: None. Note: if None, database name will be 'run######.h5'
          outdir: (optional) specify custom output directory for h5py database; type: str,
                  default: '[current_dir]/runFiles/'
          ped_name: (optional) full name and path of pedestal database to be used
                    for calibrating events; type: str, default: None
          asics: (optional) list of asics used in run_number; default 0-3
          channels: (optional) list of channels used in run_number; default 0-15
          filepath: (optional) if data is not in target5and7data, specify alternate 
                    path and name; type: str
          check_overwrite: (optional) if True, checks if ped_name exists before blindly
                          overwriting it; default True
          charge_interval: (optional) interval to use for charge integration, +- peak 
                           ampltide. type: list of ints, default: [lower,upper]=[8,8]
        """
	if not os.path.ismount(os.environ['HOME']+'/target5and7data'):
	    raise IOError('{}/target5and7data must be mounted!'.format(os.environ['HOME']))

        if not outname:
            outname = 'run{}.h5'.format(run_number)
        outfile = outdir+'/'+outname

	if not os.path.isdir(outdir):
            os.mkdir(outdir)

        self._set_run_parameters(run_number, modules, asics=asics, channels=channels, 
                                 filepath=filepath, comments=comments, 
                                 charge_interval=charge_interval)
        self._new_database(outfile, check_overwrite)
        self._set_data_packet_parameters()
        if ped_name:
            self._load_ped_database(ped_name)
            self._generate_maps()
            self._process_ped_sub_events()
        else:
            self._process_events()
        self._set_attributes()
        self.close_database()
        print("Database successfully created, saving to {}".format(outfile))

