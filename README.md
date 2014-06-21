metadata
========

Extract metadata of pdf and images from raw hard disk image files

Purpose: Get metadata of PDF and IMAGES form given image files and generate HTML report
Author: Hardik Darji ( NYU Poly ID:0526919)

Script was tested on Ubuntu 12.04 LTS 
Script needs super user permissions to run successfully.

Script uses jinja2 library to generate HTML report
Script uses hashlib to generate MD5 for files

Usage examples:
sudo python assignment5_working.py img.txt
sudo python assignment5_working.py IMAGE1,IMAGE2

Script will store all the data to sqlite3 database MetaData.db

Script needs index_template.html and report_template.html in working direcory to generate report
Script will generate HTML report files for all files in which MetaData was possible to retrive.
Full report can be seen using "index.html" from current working direcory

Script will also print every data to command line
PDF data printed on command line was inspired by pdf.py
