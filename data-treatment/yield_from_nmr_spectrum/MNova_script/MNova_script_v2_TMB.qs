//************************************************//
//This Qtscript loads the spectrum in the subfolders of a parent folder, pre-process them and then save them into .csv file.
//The pre-process includes baseline correction, phase correction and referencing etc.

//Author: Yankai Jia
//Last update: 2025.04
//************************************************//

const TMB_ref_peak = 2.30;
const TMB_peak_search_from_ppm = 2.2;//Search range for REF peak pick
const TMB_peak_search_to_ppm = 2.9;


// Global variables
const REF_peak_ppm = TMB_ref_peak;//Real peak ppm
const REF_peak_search_from_ppm = TMB_peak_search_from_ppm;//Search range for REF peak pick
const REF_peak_search_to_ppm = TMB_peak_search_to_ppm;

var dataExtension = "/fid";// Global variable for the file extension

// useful methods, get params of how the spectrum is processed
//MessageBox.information(spec.proc.getParameter("PC"))       
        
// get the parent folder path, automatic or manual
//var parentFolder = "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\_Refs\\ref_B_TEST"
var parentFolder = FileDialog.getExistingDirectory("D:\\Dropbox\\brucelee\\data\\", "Select Parent Folder");

function processSpectrum(){

	var spec = new NMRSpectrum(nmr.activeSpectrum());
	var p = new NMRProcessing(spec.proc);		
	
	page_info = spec.originalFileName;		
						
	print(spec.originalFileName);
								
	//**********************************Trimming*************************************//
	var regs = new Array(2);
	regs[0]  = new SpectrumRegion(-28, 0);
	regs[1] = new SpectrumRegion(9, 36);
	p.setParameter("cuts.apply", true);
	p.setParameter("cuts.list", regs);
	
	//*******************************************************************************//

	//*****************************PHASE CORRECTION**********************************//
	//p.setParameter("PC.method", "NoPC")
	//p.setParameter("PC.method", "Global, Metabonomics"); // this is good for DPE
	//p.setParameter("PC.method", "Imported, Metabonomics"); // this is for TMB
		
	//MessageBox.information(p.getParameter("PC"))
	//	p.setParameter("PC.method", "Min Entropy")
	//Reassign the updated processing object to the spectrum and process
	//spec.proc = p;
	//spec.process();
	
	
	 print("Old Method: ", p.getParameter("PC.algorithms"));
    p.setParameter("PC.method", "Global, Metabonomics");
    print("New Method: ", p.getParameter("PC.algorithms"));    
    
     //p.setParameter("PC.method", "Manual");
     //p.setParameter("PC.PH0",-2.01498262);
     //p.setParameter("PC.PHI", -0.50230576);    
	
	 print("Init: {0}".format(p.getParameter("PC.InitMode")));
    p.setParameter("PC.InitMode", "InitZero");
    print("New Init: {0}".format(p.getParameter("PC.InitMode")));    
	
	//******************************************************************************//
	
	//**************************BASELINE CORRECTION**********************************//
	//var spec = new NMRSpectrum(nmr.activeSpectrum());
	//Initialize NMRProcessing from the spectrum’s current processing parameters
	//var p = new NMRProcessing(spec.proc);
	//Inspect existing baseline correction parameters
	//MessageBox.information("BC[1].Apply = " + p.getParameter("BC[1].Apply"));
	//MessageBox.information("BC[1].algorithm = " + p.getParameter("BC[1].algorithm"));
	//Enable baseline correction
	
	
	p.setParameter("BC[1].Apply", true);
	
	
	//Choose a baseline correction algorithm (e.g. "Splines", "Whittaker", "PolyFit", etc.)
	//p.setParameter("BC[1].algorithm", "Bernstein");
	//p.setParameter("BC[1].PolyOrder", 5);
	
		
	p.setParameter("BC[1].algorithm", "Whittaker");
	//p.setParameter("BC[1].Filter", 0); // Zero value means "autodetect"
	//p.setParameter("BC[1].Smooth", 1)  // Zero value means "autodetect"		
	
	
			//Reassign the updated processing object to the spectrum and process
	//spec.proc = p;
	//spec.process();	
	//******************************************************************************//
	
	//*************************PEAK PICKING(for referencing)***********************//
	 // Create a processing object from the spectrum's current processing parameters
    //var p = new NMRProcessing(spec.proc);	 
    // Enable peak picking
    p.setParameter("PP.Apply", true);
    // Set the peak picking method. Options might include "GSD" or "Standard" depending on your version.
    p.setParameter("PP.Method", "Standard");
    // Optionally adjust sensitivity and noise factor:
    p.setParameter("PP.Sensitivity", 0.05);
    p.setParameter("PP.NoiseFactor", 1);
    // Set the maximum number of peaks to detect
    p.setParameter("PP.MaxPeaks", 3); // Find one peak, it should be the solvent peak.
    // Update the spectrum's processing parameters and re-process the spectrum
    //spec.proc = p;
    //spec.process(); 
//***********************************************************************************//
    // Process the spectrum with the updated processing parameters
	spec.proc = p;
    spec.process();
    spec.update();	
    	  	
//*****************************REFERENCING*******************************************//
    // Retrieve the list of detected peaks
    var peaks = spec.peaks();
    //MessageBox.critical(peaks);
    		
    
    // find the solvent peak
    var solvent_peak_ppm = [];
    for (var i = 0; i < peaks.count; i++) {
		var peak = peaks.at(i);
		    //MessageBox.critical(peak.delta());
		    
		var delta = peak.delta(); // Assumes delta() returns the ppm value
		if (delta >= REF_peak_search_from_ppm && delta <= REF_peak_search_to_ppm) {
				solvent_peak_ppm.push(peak.delta());
				}
    	}
    if (solvent_peak_ppm.length==0){
		MessageBox.critical("No solvent peak is found!");
		}
    if (solvent_peak_ppm.length>1){
		MessageBox.critical("More than one solvent is found!");
		}
    
    //var spec = new NMRSpectrum(nmr.activeSpectrum());
    // Do referencing    
    //var p = new NMRProcessing(spec.proc)
    p.setParameter("ref[1].Apply", true);
    p.setParameter("ref[1].Shift", solvent_peak_ppm[0], REF_peak_ppm);
    p.setParameter("ref.autotune", false);
            
                                                             
//******************************************************************************//
	// Process the spectrum with the updated processing parameters
	//print(p.getParameter("cuts"));	
	//print(p.getParameter("PC"))
	//print(p.getParameter("BC"))
	//print(p.getParameter("Ref"))
	//print(p.getParameter("PP"))
	spec.proc = p;
  spec.process();   
	
//*****************************************************************************//
	//print(p1.getParameter("PC"))
	//print(p1.getParameter("Apodization[1]"))
	//print(p1.getParameter("FT"))
	//MessageBox.information(spec.experimentType);
	//MessageBox.information(spec.arrayedData);
	
	//limits = spec.getFullScaleLimits()
	//print("limits: ",limits)
	
	//spec.scaleToPage();
	//spec.selectSpectra(2000);
	
	//**********************ZOOM*****************************//
	//spec.horZoom(0, 12);
	spec.vertZoom(-50000, 1000000);
	spec.update();
	//**********************************************************//
	
	return spec;
}

  
function getSubfolderPath_dir(folderPath){

	var dirFullPathList = [];	
	var myDir = new Dir(folderPath);
	// Get a list of subfolders in the parent folder
	var subFolders = myDir.entryList("*", Dir.Dirs, Dir.Name)
	// Iterate over each subfolder name to get its full path
	for (var i = 0; i < subFolders.length; i++) {
		// Skip current and parent directory entries
   		if (subFolders[i] == "." || subFolders[i] == "..") continue;
     	var fullPath = myDir.filePath(subFolders[i]);
     	//MessageBox.information("Subfolder path: " + fullPath);
       // Skip the subfolder if it does not contain "1D EXTENSION" in the full path
       //if (fullPath.indexOf("1D EXTENDED") == -1) continue;
		dirFullPathList.push(fullPath);
		}
		
	MessageBox.information(dirFullPathList);
		
   return dirFullPathList    
}

function getSubfolderPath_file(folderPath){

	var fileFullPathList = [];
	var myDir = new Dir(folderPath);
	// Get a list of subfolders in the parent folder
	var subFolders = myDir.entryList("*", Dir.Dirs, Dir.Name)
	// Iterate over each subfolder name to get its full path
	for (var i = 0; i < subFolders.length; i++) {
		// Skip current and parent directory entries
   		if (subFolders[i] == "." || subFolders[i] == "..") continue;
     	var fullPath = myDir.filePath(subFolders[i]);
     	//MessageBox.information("Subfolder path: " + fullPath);
       // Skip the subfolder if it does not contain "1D EXTENSION" in the full path
       //if (fullPath.indexOf("1D EXTENDED") == -1) continue;
		fileFullPathList.push(fullPath+dataExtension);
    }
    
    MessageBox.information(fileFullPathList);
    	    
    return fileFullPathList 
 }
 
 function saveOneSpectrum(spec, dir_path){
	// Get y-axis data (intensity)
	var yData = spec.real("all");
	//var yData = spec.real({from:0, to:512});
	var N = yData.length;	
	// Retrieve the full scale x-axis limits (in ppm, Hz, etc.)
	var limits = spec.getFullScaleLimits();
	
	// Be careful about the sequence
	var fromX = limits.fromX;
	var toX = limits.toX;
	
	//MessageBox.information(fromX)
	//MessageBox.information(toX)
		
	// Calculate x-axis values (linearly spaced)
	var xData = [];
	var step = (toX - fromX) / (N - 1);
	for (var i = 0; i < N; i++) {
			xData.push(fromX + i * step);
	}                
	//MessageBox.information(xData[0]);
	//MessageBox.information(xData[100]);
		
		// Build CSV content with header
	var csvContent = "x,y\n";
	for (var i = 0; i < N; i++) {
		csvContent += xData[i] + "," + yData[N-1-i] + "\n";
	} 

	var outPath = dir_path + "/" + "data.csv";
	//MessageBox.information(outPath)
	File.create(outPath);
		
	// Create a File object and open it in WriteOnly mode
	var file = new File(outPath);
	if (!file.open(File.WriteOnly)) {
		print("Error: Unable to open file for writing: " + outPath);
		return;
	}        
		
	// Create a BinaryStream from the File and write the CSV string
	var stream = new BinaryStream(file);
	//MessageBox.information(csvContent)
	stream.writeBytes(csvContent);
	// Close the file to ensure the data is saved
	file.close();  
}  
 
// Get the full path of all subfolders and files in the parent folder
var dirFullPathList=getSubfolderPath_dir(parentFolder);
var fileFullPathList=getSubfolderPath_file(parentFolder);
//MessageBox.information(dirFullPathList);
//MessageBox.information(fileFullPathList);
for (var j=0; j<dirFullPathList.length; j++){
	print('**************************************')
	print("Window NO: ", j+1);
	var file_path = fileFullPathList[j];
	var dir_path = dirFullPathList[j];
	var serObj  = serialization.open(file_path);
	spec = processSpectrum();

	saveOneSpectrum(spec, dir_path);
	print('**************************************\n\n')
		
}
