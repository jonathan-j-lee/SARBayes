BUILD_CMD=latexmk -cd -quiet -pdf -shell-escape
CLEAN_CMD=latexmk -cd -C -f

PAPER_PATH=paper/paper.pdf
POSTER_PATH=poster/poster.pdf
SLIDES_PATH=slides/slides.pdf

all: $(PAPER_PATH) $(POSTER_PATH) $(SLIDES_PATH)

clean:
	$(CLEAN_CMD) $(PAPER_PATH)
	$(CLEAN_CMD) $(POSTER_PATH)
	$(CLEAN_CMD) $(SLIDES_PATH)

%.pdf:
	$(BUILD_CMD) $(@:.pdf=.tex)
