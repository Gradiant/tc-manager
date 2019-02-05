FROM python:3.7.2-alpine3.8
LABEL maintainer="Carlos Giraldo <cgiraldo@gradiant.org>"

COPY tc_manager.py tc_manager_rest.py requirements.txt /opt/tc-manager/
COPY static/ /opt/tc-manager/static/
COPY templates/ /opt/tc-manager/templates/
COPY images/ /opt/tc-manager/images/

RUN apk add --no-cache iproute2 && python3 -m pip install -r /opt/tc-manager/requirements.txt

EXPOSE 5000

WORKDIR /opt/tc-manager
ENTRYPOINT ["python3", "tc_manager_rest.py"]
