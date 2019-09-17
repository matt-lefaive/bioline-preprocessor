# Bioline Preprocessor
The *Bioline Preprocessor* performs a preprocessing of XML files used to display abstracts at [Bioline International](http://www.bioline.org.br/). It fills in information that would previously have to be manually entered by a "Processing Student" while simultaneously correcting common errors from the submission process.

## Usage
1. Open a terminal and navigate to the folder containing `preprocess.py` (and all the other project files)
2. Enter: `python preprocess.py` and, when prompted, paste the path to the folder containing XML files to be preprocessed.  
![C:\bioline-preprocessor>python preprocess.py](media/1.gif)

## Command-Line Args
`-d`, `--debug` | Turns on debug mode. Preprocessed XML files will be printed to `stdout` instead of being overwritten
`-p`, `--path <PATH>` | [OPTIONAL] Specify the path to the XML folder containing files to be preprocessed.

## Actions Performed
Upon running the script, the following actions will be performed to each XML file in the directory specified by the user:
* Article id will be correctly set in `article` and `index` tags
* Copyright will be filled in with user-specified value (or the default copyright for the journal being processed)
* "NA" and its derivatives will be removed from tags in which they are the only element
* Formatting (italics, subscript, etc.) will be applied to commonly-formatted words
* Abstract section headings (Background, Methods, etc.) will be formatted (bolded, linebreaks, etc.)
* `year`, `number`, and `volume` fields will be fixed if they contain the incorrect value for this issue
* Redundant page numberings will be shortened (e.g. "1-1" becomes "1")
* Adds species links for common species (and italicizes subsequent occurrences)

Furthermore, the script will also:
* Generate `Problems.txt` file to be filled in by the "proofer"

## Usage
1. Run preprocessor.py
2. When prompted, enter the path to the XML folder for this issue
3. Follow on-screen prompts to fill in any required information for processing

## Notes
The files for all assigned Bioline tickets as downloaded by the Bioline employees have the same directory structure:  
```
.../JJV(N)  
	├/pdf  
	│  ├ #####.pdf  
	│  └ ...  
	└/xml  
	   ├ #####.xml  
	   └ ...
```  
Furthermore, all XML files follow one default template. Successful operation of this program requires a directory structure as specified above and that all xml files in .../JJV(N)/xml follow the proprietary Bioline xml format.
