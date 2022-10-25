FUNCTIONS_PATH = ./src/datalake_api/code
ZIP_PATH = ./src/datalake_api/code

all: zip_lambdas deploy

zip_lambdas:
	$(foreach file, $(wildcard $(FUNCTIONS_PATH)/*.py), zip -j $(ZIP_PATH)/$(basename $(notdir $(file))).zip $(file);)


deploy:
	cdktf deploy
	cdktf output --outputs-file outputs.json --outputs-file-include-sensitive-outputs true

destroy:
	cdktf destroy