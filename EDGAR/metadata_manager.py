
import os
import pickle as pkl
from yaml import load, CLoader as Loader, dump, CDumper as Dumper
import warnings


class metadata_manager(dict):
    def __init__(self, data_dir='data', *arg, **kw):
        super(metadata_manager, self).__init__(*arg, **kw)
        
        # Always gets the path of the current file
        self.path = os.path.abspath(os.path.join(__file__, os.pardir))
        
        self.meta_dir = os.path.join(self.path, data_dir, 'metadata')
        if not os.path.exists(self.meta_dir):
            os.system('mkdir -p ' + self.meta_dir)
        
        # Used by dataloader for API
        self.keys_path = os.path.join(self.path, data_dir, 'metadata', '.keys.yaml')
        self.keys = None
        
    def load_keys(self):

        if not os.path.exists(self.keys_path):
            warnings.warn("No .keys.yaml located", RuntimeWarning)
            self.keys = dict()
            return;
        self.keys = load(open(self.keys_path, 'r'), Loader=Loader)
    
    def save_keys(self):
        
        dump(self.keys, open(self.keys_path, 'w'), Dumper=Dumper) 
    
    def load_tikr_metadata(self, tikr):

        data_path = os.path.join(self.meta_dir, f"{tikr}.pkl")

        if os.path.exists(data_path):
        
            with open(data_path, 'rb') as f:
                self[tikr] = pkl.load(f)
            return True

        self.initialize_tikr_metadata(tikr);

        return False

    def save_tikr_metadata(self, tikr):

        self.initialize_tikr_metadata(tikr)

        data_path = os.path.join(self.meta_dir, f"{tikr}.pkl")

        with open(data_path, 'wb') as f:
            pkl.dump(self.get(tikr), f)

    def initialize_tikr_metadata(self, tikr):
        if tikr not in self:
            self[tikr] = {'attrs': dict(), 'submissions': dict()}
                
    def initialize_submission_metadata(self, tikr, fname):
        pdict = self[tikr]['submissions']
        if fname not in pdict:
            pdict[fname] = {'attrs': dict(), 'documents': dict()}
    
    def get_10q_name(self, tikr, submission):
        """
        Parameters
        ---------
        tikr: str
            a company identifier to query
        submission:
            the associated company filing for which to find a 10-Q form
            

        Returns
        --------
        filename: str
            The name of the 10-q file associated with the submission, or None
        """
        meta = self[tikr]['submissions'][submission]['documents']
        for file in meta:
            if meta[file]['type'] in ['10-Q', 'FORM 10-Q']:
                return meta[file]['filename']
        return None

    def get_submissions(self, tikr):
        """
        Parameters
        ---------
        tikr: str
            a company identifier to query

        Returns
        --------
        submissions: list
            a list of string names of filing submissions under the company tikr

        """
        if 'submissions' in self[tikr]:
            return [i for i in self[tikr]['submissions']]
        return None

    def find_sequence_of_file(self, tikr: str, submission: str, filename: str):
        level = self[tikr]['submissions'][submission]['documents']
        for sequence in level:
            if level[sequence]['filename'] == filename:
                return sequence
        return None
            
    def file_set_processed(self, tikr: str, submission: str, filename: str, val: bool):
        sequence = self.find_sequence_of_file(tikr, submission, filename)
        assert sequence is not None, "Error: filename not found"
        self[tikr]['submissions'][submission]['documents'][sequence]['features_pregenerated'] = val

    def file_was_processed(self, tikr: str, submission: str, filename: str):
        sequence = self.find_sequence_of_file(tikr, submission, filename)
        assert sequence is not None, "Error: filename not found"
        return self[tikr]['submissions'][submission]['documents'][sequence].get('features_pregenerated', False)
