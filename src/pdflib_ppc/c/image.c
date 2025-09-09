/* $Id: image.c,v 1.21 2004/05/27 13:31:59 york Exp $
 *
 * PDFlib client: image example in C
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pdflib.h"

// ./image #colors rotation(cc/ccw) outputname.pdf tiff1 tiff2 tiff3...
int
main(int argc, char *argv[])
{
    PDF *p;
	int platecount;
	char optlist[64];
    int image,gstate,spot;
  //  char *output = argv[1];

	platecount=atoi(argv[1]);
    /* This is where font/image/PDF input files live. Adjust as necessary. */
    //char *searchpath = "../data";

    /* create a new PDFlib object */
    if ((p = PDF_new()) == (PDF *) 0)
    {
        printf("Couldn't create PDFlib object (out of memory)!\n");
        return(2);
    }
	PDF_set_parameter(p, "license", "M600602-010000-109861-8C200D");
    PDF_TRY(p){
	if (PDF_begin_document(p, argv[1], 0, "") == -1) {
	    printf("Error: %s\n", PDF_get_errmsg(p));
	    return(2);
	}

	//PDF_set_parameter(p, "SearchPath", searchpath);

	/* This line is required to avoid problems on Japanese systems */
	PDF_set_parameter(p, "hypertextencoding", "host");

	PDF_set_info(p, "Creator", "gchub");

	PDF_begin_page_ext(p, 10, 10, "");

//set overprint
	gstate=PDF_create_gstate(p,"overprintfill true");
	PDF_set_gstate(p,gstate);

//load black plate
	//
	PDF_setcolor(p, "fill", "cmyk", 0.0, 0.0, 0.0,1.0);
	//spot = PDF_makespotcolor(p, "Process Black", 0);
	//PDF_setcolor(p, "fill", "spot", spot, 1, 0, 0);
	//sprintf(optlist,"colorize %d",spot);
	image = PDF_load_image(p, "auto", argv[5], 0, "");
	if (image == -1) {
	    printf("Error: %s\n", PDF_get_errmsg(p));
	    return(3);
	}
	PDF_fit_image(p, image, 0.0, 0.0, "orientate north adjustpage");
	PDF_close_image(p, image);

//load cyan

	PDF_setcolor(p, "fill", "cmyk",
                1,
                0,
                0,
                0);

	spot = PDF_makespotcolor(p, "Cyan", 0);
	sprintf(optlist,"colorize %d",spot);

	image = PDF_load_image(p, "auto", argv[2], 0, optlist);

	if (image == -1) {
	    printf("Error: %s\n", PDF_get_errmsg(p));
	    return(3);
	}


	PDF_fit_image(p, image, 0.0, 0.0, "orientate north");
	PDF_close_image(p, image);

//load magenta plate
	/*
	PDF_setcolor(p, "fill", "cmyk",
                0,
                1,
                0,
                0);
	*/
	spot = PDF_makespotcolor(p, "Magenta", 0);
	sprintf(optlist,"colorize %d",spot);

	image = PDF_load_image(p, "auto", argv[3], 0, optlist);
	if (image == -1) {
	    printf("Error: %s\n", PDF_get_errmsg(p));
	    return(3);
	}
	PDF_fit_image(p, image, 0.0, 0.0, "orientate north");
	PDF_close_image(p, image);

//load yellow plate
	/*
	PDF_setcolor(p, "fill", "cmyk",
                0,
                0,
                1,
                0);
	*/
	spot = PDF_makespotcolor(p, "Yellow", 0);
	sprintf(optlist,"colorize %d",spot);

	image = PDF_load_image(p, "auto", argv[4], 0, optlist);
	if (image == -1) {
	    printf("Error: %s\n", PDF_get_errmsg(p));
	    return(3);
	}
	PDF_fit_image(p, image, 0.0, 0.0, "orientate north");
	PDF_close_image(p, image);

	PDF_end_page_ext(p, "");

	PDF_end_document(p, "");
    }

    PDF_CATCH(p) {
        printf("PDFlib exception occurred in image sample:\n");
        printf("[%d] %s: %s\n",
	    PDF_get_errnum(p), PDF_get_apiname(p), PDF_get_errmsg(p));
        PDF_delete(p);
        return(2);
    }

    PDF_delete(p);

    return 0;
}
