import numpy as np

class pedestal(object):
    """ class for handling block to cell id mappings """

    def __init__(self,n_samples=64):
        """
        generate block id and cell id mappings upon initialization

        Args:
          n_samples: int, number of samples per waveform (blocks*32)
        """
        self.n_samples = n_samples
        self.n_blocks = 512
        #self.n_blocks = 128
        self.cells_per_block = 32
        self.n_capacitors = self.n_blocks*self.cells_per_block
        self._generate_maps()

    def _generate_maps(self):
        """ generates block and cell id mappings """
        block_id_map = [0]
        for i in range(self.n_blocks-1):
            if block_id_map[-1]%2==0:
                next_block = (block_id_map[-1]+3)%self.n_blocks
                block_id_map.append(next_block)
            else:
                next_block = (block_id_map[-1]-1)%self.n_blocks
                block_id_map.append(next_block)

        cell_id_map = np.array([])
        block_cells = np.arange(self.cells_per_block)
        for i in range(self.n_blocks):
            cell_id_map = np.append(cell_id_map,
                          block_id_map[i]*self.cells_per_block+block_cells)

        self.block_id_map = block_id_map
        self.cell_id_map = cell_id_map.astype(int)

    def get_block_id_map(self):
        """ returns block id map """
        return self.block_id_map

    def get_cell_id_map(self):
        """ returns cell id map """
        return self.cell_id_map

    def get_cell_ids(self, block, phase):
        """ 
        convert block to cell id, shift to account for phase, return cell ids   
        """
        first_cell = self.block_id_map.index(int(block))*32
        cells = np.arange(first_cell,first_cell+self.n_samples,1)+phase
        shifted_cells = np.mod(cells,self.n_capacitors)
        return self.cell_id_map[shifted_cells]


