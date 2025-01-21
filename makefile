include $(INI_HOME)/common.mk

export ABS_DIR = ./abstracts
export BIN_DIR = ./bin
export BIO_DIR = ./bios
export CHAP_DIR = ./chaps
export FINAL_TEXT_DIR = ./final_text
export PDF_DIR = ./pdfs
export PDF_ARCH_NAME = PdfFiles
export PDF_ARCH_FILE = $(PUB_DIR)/$(PDF_ARCH_NAME).zip
export PROP_DIR = ./proposal
export PUB_DIR = ./to_publisher
export SRC_ARCH_NAME = SourceFiles
export SRC_ARCH_FILE = $(PUB_DIR)/$(SRC_ARCH_NAME).zip
export STRUCT_DIR = ./structure
export TMP_DIR = ./tmp

FORCE:

prod: parts github

archive: $(ARCH_FILE)

$(ARCH_FILE): parts
	echo "Do we need this?"

github:
	-git commit -a
	git push origin main

parts: abstracts bios toc final_text permissions pdfs

final_text: FORCE
	zip -r $(SRC_ARCH_FILE) $(FINAL_TEXT_DIR)/*.docx

pdfs: FORCE
	zip -r $(PDF_ARCH_FILE) $(PDF_DIR)/*.pdf

%.pdf: $(FINAL_TEXT_DIR)/%.docx
	pandoc $< -o $(PDF_DIR)/$@

permissions:
	ls permissions

toc: $(CHAP_DIR)/toc.docx

$(CHAP_DIR)/toc.docx: toc.md
	pandoc -o $@ -f markdown -t docx toc.md

proposal: $(CHAP_DIR)/prop.docx $(CHAP_DIR)/palgrave.docx

$(PROP_DIR)/prop.docx: $(PROP_DIR)/prop.md
	pandoc -o $@ -f markdown -t docx $(PROP_DIR)/prop.md

$(PROP_DIR)/palgrave.docx: $(PROP_DIR)/palgrave.md
	pandoc -o $@ -f markdown -t docx $(PROP_DIR)/palgrave.md

abstracts: $(ABS_DIR)/abstracts.docx

$(ABS_DIR)/abstracts.docx: $(TMP_DIR)/abstracts.md
	pandoc -o $@ -f markdown -t docx $(TMP_DIR)/abstracts.md

$(TMP_DIR)/abstracts.md: $(ABS_DIR)/*.md $(STRUCT_DIR)/chap_order.txt
	$(BIN_DIR)/collect_abstracts.sh

bios: $(CHAP_DIR)/bios.docx

$(BIO_DIR)/bios.docx: $(TMP_DIR)/bios.md
	pandoc -o $@ -f markdown -t docx $(TMP_DIR)/bios.md

$(TMP_DIR)/bios.md: $(BIO_DIR)/*.md
	cat $^ > $@
