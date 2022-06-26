# ----------------------------------
#          INSTALL & TEST
# ----------------------------------
install_requirements:
	@pip install -r requirements.txt

test:
	@coverage run -m pytest tests/*.py
	@coverage report -m --omit="${VIRTUAL_ENV}/lib/python*"

ftest:
	@Write me

clean:
	@rm -f */version.txt
	@rm -f .coverage
	@rm -fr */__pycache__ */*.pyc __pycache__
	@rm -fr build dist
	@rm -fr tok-gst-*.dist-info
	@rm -fr tok-gst.egg-info

install:
	@pip install . -U

all: clean install test black check_code

count_lines:
	@find ./ -name '*.py' -exec  wc -l {} \; | sort -n| awk \
        '{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''
	@find ./scripts -name '*-*' -exec  wc -l {} \; | sort -n| awk \
		        '{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''
	@find ./tests -name '*.py' -exec  wc -l {} \; | sort -n| awk \
        '{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''

# ----------------------------------
#      UPLOAD PACKAGE TO PYPI
# ----------------------------------
PYPI_USERNAME=<AUTHOR>
build:
	@python setup.py sdist bdist_wheel

pypi_test:
	@twine upload -r testpypi dist/* -u $(PYPI_USERNAME)

pypi:
	@twine upload dist/* -u $(PYPI_USERNAME)

# ----------------------------------
#      DEPLOY API TO GOOGLE CLOUD
# ----------------------------------

GOOGLE_APPLICATION_CREDENTIALS = "GOOGLE_APPLICATION_CREDENTIALS=/credentials.json"
PROJECT_ID=...
DOCKER_IMAGE_NAME=...

local_run_api:
	uvicorn api.fast:app --reload --host localhost --port 8080

gcp_push:
	docker build --platform linux/amd64 -t eu.gcr.io/${PROJECT_ID}/${DOCKER_IMAGE_NAME} .

gcp_push:
	docker push eu.gcr.io/${PROJECT_ID}/${DOCKER_IMAGE_NAME}

gcp_deploy:
gcloud run deploy \
    --image eu.gcr.io/${PROJECT_ID}/${DOCKER_IMAGE_NAME} \
    --platform managed \
    --region northamerica-northeast1 \
    --set-env-vars ${GOOGLE_APPLICATION_CREDENTIALS} \
		--memory 6Gi \
		--cpu 2

# ----------------------------------
#      CREATE DATA APP
# ----------------------------------

streamlit:
	-@streamlit run app/app.py
