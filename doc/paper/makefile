# TJHSST CSL
# Writing Assignment
# Jonathan Lee

# Place at the root of the directory containing the papers.

# Recursively generate PDF files for LaTeX source files.
# The name of the PDF file will be the same as that of the LaTeX file.
# Any BibTeX files must have the same name as the LaTeX file.
all: $(patsubst %.tex,%.pdf,$(shell find -name "*.tex"))

# Delete any intermediary files.
clean:
	find . -type f -name "*.aux" -delete
	find . -type f -name "*.bbl" -delete
	find . -type f -name "*.blg" -delete
	find . -type f -name "*.log" -delete

# Delete any PDF files.
scrub:
	find . -type f -name "*.pdf" -delete

%.pdf:
	$(eval NAME=$(patsubst %.pdf,%,$@))
	$(eval FULL=$(shell dirname $(NAME)))
	$(eval BASE=$(shell basename $(NAME)))

	pdflatex -output-directory $(FULL) $(NAME)
	if [ -e $(NAME).bib ]; then cd $(FULL); bibtex $(BASE); fi
	pdflatex -output-directory $(FULL) $(NAME)
	pdflatex -output-directory $(FULL) $(NAME)
