FROM python:3

LABEL vesion="0.1"
LABEL description="An easy graph generator and viewer."
LABEL author="now047@gmail.com"

USER root

RUN apt-get update
RUN apt-get install -y vim less
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools

RUN pip install pandas
RUN pip install bokeh==2.2.2
RUN pip install streamlit

WORKDIR /root
COPY *py /root
COPY .streamlit/config.toml /root/.streamlit/

EXPOSE 8001
CMD streamlit run app.py