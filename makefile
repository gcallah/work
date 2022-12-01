export PUB_DIR = ./to_publisher
export BIO_DIR = ./bios
export ABS_DIR = ./abstracts
export TMP_DIR = ./tmp
export BIN_DIR = ./bin

prod: abstracts bios github

github:
	-git commit -a
	git push origin main

abstracts: $(PUB_DIR)/abstracts.docx

$(PUB_DIR)/abstracts.docx: $(TMP_DIR)/abstracts.md
	pandoc -o $@ -f markdown -t docx $(TMP_DIR)/abstracts.md

$(TMP_DIR)/abstracts.md: $(ABS_DIR)/*.md
	$(BIN_DIR)/collect_abstracts.sh

bios: $(PUB_DIR)/bios.docx

$(PUB_DIR)/bios.docx: $(TMP_DIR)/bios.md
	pandoc -o $@ -f markdown -t docx $(TMP_DIR)/bios.md

$(TMP_DIR)/bios.md: $(BIO_DIR)/*.md
	cat $^ > $@
