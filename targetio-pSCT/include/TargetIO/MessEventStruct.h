//structs by ramin.
typedef struct {
  int status; // if there is data or not
  int type_ic, type_adc;  // full cam, mes, list or image?
                          // can be set by modules to filter out a televent;
                          // for all modules in the pipeline that filter that tag, the televent will look like it has no data;
                          // for all other modules, it will look like normal
  int tag;
  int tel_id;
  int time_offset;    // offset to event trigger time
  int compression;
  
  float roi_radius, roi_phi, roi_cx, roi_cy; // parameters describing the region of interest
  int img_r; // if the shower is stored as rectangular image, img_r*2+1 is its width and height
  
  char has_ic;        // integrated charge
  char has_adc;       // samples
  char has_tom;       // time of maximum
  char has_lg;        // has low gain
  
  int adc_n;          // number of pixels with raw data
  int ic_n;           // number of pixels with integrated charge
  int adc_win_start;  // if != -1, it contains the index of the first sample of the window that is kept
  int adc_win_len;    // if != -1, it contains the length of the window that is kept
  
  float ic_tom_thresh;  // keep time of maximum only for pixels with an integrated charge > ic_tom_thresh
  float pe_res;         // photoelectron resolution; needed for quantization when writing to disk
  float tom_res;        // time of maximum resolution; needed for quantization when writing to disk
  
  short *ic_id;       // ids of pixels in ROI or list
  float *ic;          // integrated charge
  float *tom;         // time of maximum
  float *ped[2];      // pedestal of each pixel
  unsigned char *clean_mask;    // if 0 ==> cleaned, otherwise n_th neighbour row after cleaning
  
  short *adc_id;      // ids of pixels in ROI or list
  unsigned short **adc[2];     // adc counts for low gain and high gain for each pixel and trace
} Televent;

typedef struct {
  int version;
  int status;
  int type;
  int changed;
  int tag;
  int last;
//  TimeID time; ///HARM: I don't have this struct yet...
  Televent **tel;  // you only need this
} Event;
