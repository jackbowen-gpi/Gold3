
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "pdflib.h"
#include <time.h>

/*
	Contents of argv[]
	1 - KD to include
	2 - Output file for mini
	3 - Customer ID
	4 - Packaging ID
	5 - Board Spec
	6 - Manufacturing Plant
	7 - Artist
	8 - Dimension (W)
	9 - Dimension (L)
	10 - Dimension (H)
	11 - Box Format (Left|Right)
	12 - Case Quantity
	13 - Sleeve Quantity
	14 - Case Color
	15 - Job Number
	16 - Part Number
	17 - RIM Number
*/

int main(int argc, char *argv[]) {
    // The path to and filename of the corrugated mini template.
    const char *infile = "corrug_minitemp.pdf";
    // This always needs to equal the number of required arguments!
    const int num_required_args = 18;
	// Just for consistency and readability
	const size_t buffer_size = 255;
    // This is where font/image/PDF input files live. Adjust as necessary.
    const char *searchpath = ".";
	// We only want the first page of everything.
    const int pageno = 1;

    /*
		Various temporary variables.
	*/
	// PDF object representing the mini being generated.
    PDF		*p;
	// Item reference numbers to the mini template and its first (and only) page.
    int		doc, page;
	// Item reference numbers to the KD and its first page.
    int		jobdoc, jobpage;

    // Corrugated template variables from user input.
    char *jobinfile = argv[1];
    char *output = argv[2];
    char *custid = argv[3];
    char *pkgid = argv[4];
    char *boardspec = argv[5];
    char *mfgplant = argv[6];
    char *artist = argv[7];
    char *boxformat = argv[11];
    char *casequant = argv[12];
    char *sleevequant = argv[13];
    char *casecolor = argv[14];
    char *jobnum = argv[15];
    char *partnum = argv[16];
    char *rimnum = argv[17];

    // Data that needs to be massaged or gathered elsewhere.
    char boxdims[buffer_size];
    char date[buffer_size];
    time_t currtime;
    struct tm *loctime;

	// If they don't pass any arguments, show the syntax.
	if (argc == 1) {
		printf("Syntax: make_corrugmini <KD File> <Output File> <Customer ID> <Pkg ID> <Board Spec> <Mfg Plant> <Artist> <Width> <Length> <Height> <Box Format> <Case Quant> <Sleeve Quant> <Case Color> <Job Num> <Part Num> <RIM Num>\n");
    	return 0;
	}

    // Populate the box dimensions variable.
    (void) snprintf(boxdims, buffer_size, "%sx%sx%s", argv[8], argv[9], argv[10]);

    // Populate the job date variable.
    (void) time(&currtime);
    loctime = localtime(&currtime);
    (void) strftime(date, 256, "%d %b %Y", loctime);

    // Without the correct number of arguments, bad things tend to happen. It's
    // probably best to prevent that.
    if (argc != num_required_args) {
        printf("ERROR: %d arguments given, %d required.\n", argc-1, num_required_args-1);
		return(2);
    }

	// If for some reason we run out of memory, this handles it. Although this
	// really should never happen.
    if ((p = PDF_new()) == (PDF *) 0) {
        printf("ERROR: Couldn't create PDFlib object (out of memory)!\n");
        return(2);
    }

    // This is apparently something used to make sure our copy of PDFlib is legal.
    PDF_set_parameter(p, "license", "M600602-010000-109861-8C200D");

    // This looks to be the macro called to handle PDF generation. Yuck.
    PDF_TRY(p) {
        if (PDF_begin_document(p, output, 0, "") == -1) {
	    	printf("ERROR: %s\n", PDF_get_errmsg(p));
	    	return(2);
		}

        PDF_set_parameter(p, "SearchPath", searchpath);
        PDF_set_parameter(p,"spotcolorlookup","false");
        PDF_set_parameter(p, "pdiwarning", "true");

		// Set 'doc' to the integer item reference for the template.
        doc = PDF_open_pdi(p, infile, "", 0);
        if (doc == -1) {
            printf("ERROR: Couldn't open PDF template '%s'\n", infile);
	    	return (1);
    	}

        // Set 'jobdoc' to the integer item reference for the KD.
    	jobdoc = PDF_open_pdi(p, jobinfile, "", 0);
    	if (jobdoc == -1) {
    	printf("ERROR: Couldn't open job PDF template '%s'\n", infile);
        	return (1);
    	}

		// Set the integer item reference for the template's first (and only) page.
    	page = PDF_open_pdi_page(p, doc, pageno, "");
    	if (page == -1) {
        	printf("Couldn't open page %d of PDF template '%s'\n", pageno, infile);
			return (2);
    	}

		// Set the integer item reference for the KD's first page.
    	jobpage = PDF_open_pdi_page(p, jobdoc, pageno, "");
    	if (jobpage == -1) {
        	printf("Couldn't open page %d of job PDF template '%s'\n", pageno, infile);
			return (2);
    	}

    	// Dummy page size, replaced below by PDF_fit_pdi_page (?)
    	PDF_begin_page_ext(p, 792, 612, "");
    	// Adjust page size to the block container's size.
    	PDF_fit_pdi_page(p, page, 0, 0, "adjustpage");

    	// Fill the template blocks.
    	PDF_fill_textblock(p, page, "custid", custid, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "pkgid", pkgid, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "boardspec", boardspec, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "mfgplant", mfgplant, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "artist", artist, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "boxdims", boxdims, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "boxformat", boxformat, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "casequant", casequant, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "sleevequant", sleevequant, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "casecolor", casecolor, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "jobnum", jobnum, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "partnum", partnum, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "rimnum", rimnum, 0, "encoding=winansi");
    	PDF_fill_textblock(p, page, "date", date, 0, "encoding=winansi");

    	// The KD file may be invalid or unreadable.
    	if (PDF_fill_pdfblock(p, page, "mini", jobdoc, "") == -1) {
        	printf("ERROR: Unable to insert box KD pdf file.\n");
			return (2);
    	}

    	// Clean up.
    	PDF_close_pdi_page(p, page);
    	PDF_end_page_ext(p, "");
    	PDF_end_document(p, "");
    	PDF_close_pdi(p, doc);
    	PDF_close_pdi(p, jobdoc);
    } // end macro PDF_TRY()

    /*
        If an "exception" is thrown, this catches it.
    */
    PDF_CATCH(p) {
        printf("ERROR: PDFlib exception occurred in make_template:\n");
        printf("[%d] %s: %s\n",
            PDF_get_errnum(p), PDF_get_apiname(p), PDF_get_errmsg(p));
        PDF_delete(p);
        return(2);
    }

	// Free up ze memory, comrade!
    PDF_delete(p);
    printf("Corrugated miniature template generation completed.\n");
    return 0;
} // end function main()
