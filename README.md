# Bioline Preprocessor
The Bioline Preprocessor performs a preprocessing of XML files used to display information at [Bioline International](http://www.bioline.org.br/).

## Actions Performed
Upon running the script, the following actions will be performed to each XML file in the directory specified by the user:
* Article id will be correctly set in `article` and `index` tags
* Copyright will be filled in with user-specified value (or the default copyright for the journal being processed)
* "NA" and its derivatives will be removed from tags in which they are the only element
* Formatting (italics, subscript, etc.) will be applied to words commonly formatted
* Abstract section headings (Background, Methods, etc.) will be automatically formatted
* `year`, `number`, and `volume` fields will automatically be fixed if they contain the incorrect value for this issue
* Redundant page numberings will be shortened (e.g. "1-1" becomes "1")
* Automatically adds species links for common species (and italicizes subsequent occurrences)

## Usage
1. Run preprocessor.py
2. When prompted, enter the path to the XML folder for this issue
3. Follow on-screen prompts to fill in any required information for processing

### Notes
The files for all assigned Bioline tickets as downloaded by the Bioline employees have the same directory structure:  
```
.../JJV(N)  
	├ pdf  
	│  ├ #####.pdf  
	│  └ ...  
	└ xml  
	   ├ #####.xml  
	   └ ...
```  
Furthermore, all XML files follow one default template. Successful operation of this program requires a directory structure as specified above and that all xml files in .../JJV(N)/xml follow the proprietary Bioline xml format.