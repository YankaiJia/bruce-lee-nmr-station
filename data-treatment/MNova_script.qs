//************************************************//
//This Qtscript loads the spectrum in the subfolders of a parent folder, pre-process them and then save them into .csv file.
//The pre-process includes baseline correction, phase correction and referencing etc.

//Author: Yankai Jia
//Last update: 2025.03
//************************************************//



// Global variable for the extension (can be changed later)
var dataExtension = "/data.1d";

// get the parent folder path, automatic or manual
//var parentFolder = "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\_Refs\\ref_B"
var parentFolder = FileDialog.getExistingDirectory("D:\\Dropbox\\brucelee\\data\\DPE_bromination", "Select Parent Folder");

function processSpectrum(){
	//**************************BASELINE CORRECTION**********************************//
	var spec = new NMRSpectrum(nmr.activeSpectrum());
	//Initialize NMRProcessing from the spectrum’s current processing parameters
	var p = new NMRProcessing(spec.proc);
	//Inspect existing baseline correction parameters
	//MessageBox.information("BC[1].Apply = " + p.getParameter("BC[1].Apply"));
	//MessageBox.information("BC[1].algorithm = " + p.getParameter("BC[1].algorithm"));
	//Enable baseline correction
	p.setParameter("BC[1].Apply", true);
	//Choose a baseline correction algorithm (e.g. "Splines", "Whittaker", "PolyFit", etc.)
	p.setParameter("BC[1].algorithm", "Bernstein");
	p.setParameter("BC[1].PolyOrder", 3);
	//Reassign the updated processing object to the spectrum and process
	spec.proc = p;
	spec.process();
	//******************************************************************************//

	//*****************************PHASE CORRECTION**********************************//
	var spec = new NMRSpectrum(nmr.activeSpectrum());
	var p1 = new NMRProcessing(spec.proc);
	print(p1.getParameter("PC"))
	p1.setParameter("PC.method", "Min Entropy")
	//Reassign the updated processing object to the spectrum and process
	spec.proc = p1;
	spec.process();
	//******************************************************************************//

	print(p1.getParameter("PC"))
	print(p1.getParameter("Apodization[1]"))
	print(p1.getParameter("FT"))
	//MessageBox.information(spec.experimentType);
	//MessageBox.information(spec.arrayedData);

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
       if (fullPath.indexOf("1D EXTENDED") === -1) continue;
		dirFullPathList.push(fullPath);
		}
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
       if (fullPath.indexOf("1D EXTENDED") === -1) continue;
		fileFullPathList.push(fullPath+dataExtension);
    }
    
    return fileFullPathList 
 }
 
 function saveOneSpectrum(spec, dir_path){
	// Get y-axis data (intensity)
	var yData = spec.real("all");
	//var yData = spec.real({from:0, to:512});
	var N = yData.length;

	// Retrieve the full scale x-axis limits (in ppm, Hz, etc.)
	var limits = spec.getFullScaleLimits();
	var fromX = limits.fromX;
	var toX = limits.toX;
		
	// Calculate x-axis values (linearly spaced)
	var xData = [];
	var step = (toX - fromX) / (N - 1);
	for (var i = 0; i < N; i++) {
			xData.push(fromX + i * step);
	}                

	// Build CSV content with header
	var csvContent = "x,y\n";
	for (var i = 0; i < N; i++) {
		csvContent += xData[i] + "," + yData[i] + "\n";
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
var file_path = fileFullPathList[j];
var dir_path = dirFullPathList[j];
var serObj  = serialization.open(file_path);
spec = processSpectrum();
print(j);
saveOneSpectrum(spec, dir_path);

}