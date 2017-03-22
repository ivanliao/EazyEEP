import json
import copy
import binascii
import string

class EepromBin(object):
    '''
    EEPROM file definition
    '''
    def __init__(self, bin_file, size=256):
        '''
        Constructor
        '''
        self.file = bin_file
        self.size = size
        self.content = [0xff] * size

    def read(self, offset):
        if 0 <= offset < self.size:
            return self.content[offset]
        else:
            return None
    def write(self, offset, value):
        if 0 <= offset < self.size:
            self.content[offset] = value & 0xff
        return
    def data_write(self, offset, data = []):
        for i in xrange(0,len(data)):
            if offset+i >= self.size: break # out of bound
            self.write(offset+i, data[i])
        return
    def string_write(self, offset, str_val, wr_len=None):
        if wr_len == None: wr_len = len(str_val)+1
        if wr_len <= len(str_val):
            str_val = str_val[:wr_len]
        str_val = string.ljust(str_val, wr_len, '\0')
        self.data_write(offset, map(ord, str_val))
        return
    def string_read(self, offset, rd_len=None):
        if rd_len == None: rd_len = self.size
        output_string = ''
        for i in xrange(offset, offset+rd_len):
            value = self.read(i)
            if value == None or value == 0x00 or value == 0xff: # check ending
                break
            output_string += '%c' % value
        return output_string
    def erase(self, offset, size):
        # erase bytes of EEPROM
        data = [0xff] * size
        self.data_write(offset, data)
        return
    def dump(self):
        buf = '     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f\n'
        for y in xrange(0,16,1):
            line = ''
            for x in xrange(0,16,1):
                offset = (y*16) + x
                value = self.read(offset)
                line = '%s %02x' % (line, value)
            buf += '%x0: %s\n' % (y, line)
        return buf
    def reload(self):
        with open(self.file, 'rb') as f:
            self.content = [byte & 0xff for byte in bytearray(f.read())]
    def save(self):
        with open(self.file, 'wb') as f:
            f.write(bytearray(self.content))

class EepromProg(object):
    '''
    EEPROM type definition
    '''

    # class for fields
    class DataField(object):
        def __init__(self, descr, value, offset, size):
            self.descr = descr
            self.value = value # default value
            self.offset = offset
            self.size = size # in byte

    def __init__(self, eep_dev):
        '''
        Constructor
        '''
        self.eep_dev = eep_dev
        self.base_offset =0x0
        self.fields = {}
        # Children have to define it by themselves
        self.block = None

    def get_field(self, fname):
        return self.eep_dev.string_read(self.fields[fname].offset+self.base_offset)

    def set_field(self, fname, str):
        self.eep_dev.string_write(self.fields[fname].offset+self.base_offset, str ,self.fields[fname].size+1)

    def init_default(self):
        for key, f in self.fields.items():
            if f.value != None:
                self.set_field(key, f.value)

    def erase_block(self):
        self.eep_dev.erase(self.block.offset+self.base_offset, self.block.size)

    def erase_all(self):
        self.eep_dev.erase(0, self.eep_dev.size)

class JsonEepromProg(EepromProg):
    '''
    EEPROM type definition
    '''
    # class for fields
    class DataField(object):
        def __init__(self, data_field):
            self.descr = data_field['descr']
            self.value = data_field['value'] # default value
            self.offset = data_field['offset']
            self.size = data_field['size'] # in byte

    def __init__(self, eep_dev, j_data):
        self.eep_dev = eep_dev
        self.base_offset = j_data['base_offset']
        self.fields = {}
        for key, f in j_data['fields'].items():
            self.fields[key] = self.DataField(f)
        self.block = self.DataField(j_data['block'])

    def toJSON(self):
        obj = copy.deepcopy(self)
        #obj.fields = sorted(obj.fields.values(), key=attrgetter('offset'))
        # update the value of fields with real data
        for key in obj.fields.keys():
            obj.fields[key].value = obj.get_field(key)
        del obj.eep_dev # skip eep class
        return json.dumps(obj, default=lambda o: o.__dict__, indent=4)
