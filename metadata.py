#! /usr/bin/python
"""

Purpose: Get metadata of PDF and IMAGES form given image files and generate HTML report
Author: Hardik Darji

Script was successfully tested on Ubuntu 12.04 LTS 
Script needs super user permissions to run successfully.

Script uses jinja2 library to generate HTML report
Script uses hashlib to generate MD5 for files

Usage examples:
sudo python metadata.py img.txt
sudo python metadata.py IMAGE1,IMAGE2

Script will store all the data to sqlite3 database MetaData.db

Script needs index_template.html and report_template.html in working direcory to generate report
Script will generate HTML report files for all files in which MetaData was possible to retrive.
Full report can be seen using "index.html" from current working direcory

Script will also print every data to command line
PDF data printed on command line was inspired by pdf.py

"""
import os
import re
import sys
import logging
import argparse
import subprocess
import pyPdf
import hashlib
import string
import jinja2

from PIL import Image
from PIL.ExifTags import TAGS

try:
	from sqlalchemy import Column, Integer, Float, String, Text
	from sqlalchemy.ext.declarative import declarative_base
	from sqlalchemy.orm import sessionmaker
	from sqlalchemy import create_engine
	from jinja2 import Environment
except ImportError as e:
	print "Module `{0}` not installed".format(error.message[16:])
	sys.exit()

# === SQLAlchemy Config ============================================================================
Base = declarative_base()

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

# === Database Classes =============================================================================
class imageInfo(Base):

	__tablename__ = 'img'

	id = Column(Integer,primary_key = True)
	FileName = Column(String)
	Label = Column(String)
	Value = Column(String)
	
	def __init__(self,FileName,Label,Value):
		self.FileName=FileName
		self.Label=Label
		self.Value=Value
		
# === Metadata Classes with extraction methods========================================================
class Metadata(object):
	
	def __init__(self, img = ''):
		if img == '' or not os.path.exists(img):		
			raise Exception('No disk image provided')
			
		self.img = img
		self.fn  = os.path.splitext(os.path.basename(img))[0]
		self.dir = '{0}/extract/{1}'.format(os.path.dirname(os.path.abspath(__file__)), self.fn)
		if not os.path.exists(self.dir): os.makedirs(self.dir)

		self.db = 'MetaData.db'
		self.engine = create_engine('sqlite:///'+self.db, echo=False)
		Base.metadata.create_all(self.engine)

		Session = sessionmaker(bind=self.engine)
		self.session = Session()
		self.session.text_factory = str

#========= Function to generate HTML reports for individual files

	def print_html_doc(self,listoffilenames):
		templateLoader = jinja2.FileSystemLoader( searchpath="/" )
		templateEnv = jinja2.Environment( loader=templateLoader )
		currentpath = os.getcwd();
		TEMPLATE_FILE = currentpath + "/report_template.html"
		template = templateEnv.get_template( TEMPLATE_FILE )
		self.listoffilenames=listoffilenames
		connection = self.engine.connect()
		for afile in listoffilenames:
			if (afile.lower()).endswith('.pdf') or (afile.lower()).endswith('.jpg') or (afile.lower()).endswith('.jpeg') or (afile.lower()).endswith('.png') or (afile.lower()).endswith('.tif') or (afile.lower()).endswith('.gif') or (afile.lower()).endswith('.bmp'):
				query = "select * from img where filename=" + "'" + afile + "'"
				#print query
				result = connection.execute(query)
				data={}
				for row in result:
					data[str(row[2])]=str(row[3])
				variables = { "alldata" : data }
				outputText = template.render( variables )
				try:
					file = open(afile + ".html" ,'w')
					file.write(outputText)
				except:
					print "file was not generated"
		connection.close()

#========= Function which will generate a index report file which will link to all other report files		
	def indexhtml(self,listoffilenames):
		filteredlist = []
		templateLoader = jinja2.FileSystemLoader( searchpath="/" )
		templateEnv = jinja2.Environment( loader=templateLoader )
		currentpath = os.getcwd();
		TEMPLATE_FILE = currentpath + "/index_template.html"
		template = templateEnv.get_template( TEMPLATE_FILE )
		self.listoffilenames=listoffilenames
		for file_name in listoffilenames:
			if os.path.exists(file_name + ".html"):
				filteredlist.append(file_name)

		variables = { "allfiles" : filteredlist }
		outputText = template.render( variables )
		try:
			file = open( "index.html" ,'w')
			file.write(outputText)
		except:
			print "file was not generated"


	def carve(self):
		try:
			subprocess.Popen(["tsk_recover","-e",self.img,self.dir])
			subprocess.Popen(["tsk_loaddb","-d","{0}/{1}.db".format(self.dir, self.fn),self.img])
		except:
			raise Exception('Error carving image.')

	def reportPDF(self,filename,item,dat):
		self.filename=filename
		row = imageInfo(filter(lambda x: x in string.printable, filename.decode("utf-8")),str(item), str(dat))
		self.session.add(row)
		self.session.commit()
			
	def reportEXIF(self,exif,filename):
		self.exif=exif
		for exifkey,exifval in exif.iteritems():
			self.filename=filename
			row = imageInfo(filter(lambda x: x in string.printable, filename.decode("utf-8")),str(exifkey), str(exifval))
			self.session.add(row)
			self.session.commit()
			
def main(argv):
	parser = argparse.ArgumentParser(description='OS Fingerprinting and Carving')
	parser.add_argument('img',help='Disk Image(s) to be analyzed; newline delimited text file or single filename')
	args=parser.parse_args()
	listofallfiles = []
	listoffilenames = []
	try:
		if os.path.isfile(args.img) and os.path.splitext(os.path.basename(args.img))[1] == '.txt':
			with open(args.img) as ifile:
				imgs = ifile.read().splitlines()
		else:
			raise Exception('')
	except:
		try:
			imgs = [img for img in args.img.split(',')]
		except:
			imgs = args.img

	for img in imgs:
		osf = Metadata(img)
		#osf.fingerprint()
		osf.carve()
		
	for dirname, dirnames, filenames in os.walk('./extract'):
		for fn in filenames:
			#try:
			filename = fn
			listoffilenames.append(filter(lambda x: x in string.printable, filename.decode("utf-8")))
			fn=os.path.join(dirname, fn)
			MD5 = hashlib.md5(fn).hexdigest()
			#print MD5
			if (fn.lower()).endswith('.pdf'):
				#print fn
				listofallfiles.append(filter(lambda x: x in string.printable, fn.decode("utf-8")))
				#osf.PDFmetadata(fn)
				try:
					print "\n\n====================== FILE NAME =========================="
					print fn
					print "===========================================================\n"
					MD5 = hashlib.md5(fn).hexdigest()
					pdf = pyPdf.PdfFileReader(file(fn, 'rb'))
					info = pdf.getDocumentInfo()
					for item, dat in info.items():
						try:
							print '[+]  {0}: {1}'.format(item, pdf.resolvedObjects[0][1][item])
							osf.reportPDF(filename,item,str(format(item, pdf.resolvedObjects[0][1][item])))
						except:
							print '[+]  {0}: {1}'.format(item, dat)
							osf.reportPDF(filename,item,str(dat))
				except Exception, e:
					print "Could not analyze PDF"
					print e
				osf.reportPDF(filename,'MD5',MD5)
			elif (fn.lower()).endswith('.jpg' or '.jpeg' or '.png' or '.tif' or '.gif' or '.bmp'):
				exif = {}
				listofallfiles.append(filter(lambda x: x in string.printable, fn.decode("utf-8")))
				try:
					print "\n\n====================== FILE NAME =========================="
					print fn
					print "===========================================================\n"
					MD5 = hashlib.md5(fn).hexdigest()
					img = Image.open(fn)
					info = img._getexif()
					for tag, value in info.items():
						decoded = TAGS.get(tag, tag)
						print "[+] " + decoded + ":",value
						exif[decoded]=value 
				except Exception, e:
					exif=exif
					print "Could not retrive exif data"
				exif['MD5']=MD5
				osf.reportEXIF(exif,filename)
									
				
	print "_______________________________________________________________________________________________"
	print '\n\n\nAll images analyzed.\nExtracted files saved in `./extract/`.\nImage and data information is saved in `MetaData.db`'
	print "open index.html to see report file"
	#print listofallfiles
	#print listofallfiles
	osf.print_html_doc(listoffilenames)
	osf.indexhtml(listoffilenames)

if __name__ == '__main__':
	main(sys.argv)
