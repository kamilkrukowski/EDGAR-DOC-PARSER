
import os
import pickle as pkl


class metadata_manager(dict):
    def __init__(self, data_dir='edgar_downloads', *arg, **kw):
        super(metadata_manager, self).__init__(*arg, **kw)
        
        # Always gets the path of the current file
        self.path = os.path.abspath(os.path.join(__file__, os.pardir))
        
        self.meta_dir = os.path.join(self.path, data_dir, 'metadata')
        if not os.path.exists(self.meta_dir):
            os.system('mkdir -p ' + self.meta_dir)
    
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
    
    """
        Returns 10-q filename associated with submission
    """
    def get_10q_name(self, tikr, filename):
        meta = self[tikr]['submissions'][filename]['documents']
        for file in meta:
            if meta[file]['type'] in ['10-Q', 'FORM 10-Q']:
                return meta[file]['filename']
