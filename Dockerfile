FROM ubuntu:14.04

LABEL authors="Órion Winter (orion.lima@ccc.ufcg.edu.br), Tarciso Braz (tarcisobraz@copin.ufcg.edu.br)"

# Installing R
RUN echo "deb http://lib.stat.cmu.edu/R/CRAN/bin/linux/ubuntu trusty/" >> /etc/apt/sources.list 
RUN apt-get update 
RUN apt-get -y --force-yes install r-base 

# Installing geos library
RUN echo "deb http://security.ubuntu.com/ubuntu trusty-security main restricted" >> /etc/apt/sources.list
RUN echo "deb-src http://security.ubuntu.com/ubuntu trusty-security main restricted" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get -y install libgeos-dev libgdal1-dev libproj-dev git

# Install R packages dependencies
RUN R -e 'install.packages(c("dplyr", "lubridate", "stringr", "sp", "rgeos", "rgdal"), repos = "http://cran.rstudio.com/")'

# Adding path finder script
RUN git clone https://github.com/analytics-ufcg/people-paths.git /home/people-paths



