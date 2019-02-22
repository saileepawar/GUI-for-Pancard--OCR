from flask import Flask, render_template, request 
from werkzeug import secure_filename
import os
import cv2
import pytesseract
import nltk
import re
import numpy as np
from PIL import Image
from pymongo import MongoClient

UPLOAD_FOLDER = '/home/nimesh/My-Files/GBF/Project2/UPLOAD_FOLDER'

def filterOut(d_list):
  empty_free = d_list
  empty_free = list(filter(str.strip,empty_free))
  a=[y.strip('~!@#$%^&*()=+ "|') for y in empty_free]
  empty_free = a
  return empty_free

def storeDB(j_details):
  myclient = MongoClient("mongodb://127.0.0.1:27017")
  db = myclient.pan_cardDB
  if(db.panDetails.count()==0):
    db.panDetails.insert_one(dict(j_details))
  else:
    db.panDetails.update({"pan-number":j_details["pan-number"]},{"$set":{"name":j_details["name"],"fathers-name":j_details["fathers-name"],"DOB":j_details["DOB"]},},upsert=True)  

def fetchDetail(d_tuple,form_input):  
  global panD
  panD = dict()
  global flag
  flag = 0
  d_list = np.array(d_tuple)
  for i in range(len(d_list)):
    #CHECKING THE FIRST CONDITION
    if(len(d_list)!=i):
      if(d_list[i][0].find("numb" or "num" or "account")!=-1):
        #print(d_list[i+1])
        flag+=1
        if((d_list[i+1][1]=='NN' or d_list[i+1][1]=='VBD') and len(d_list[i+1][0])==10):
          #pan number will be added first
          panD['pan-number'] = str(d_list[i+1][0]).upper()
          flag+=1
          #print(panD)
        #CHECKING THE SECOND CONDITION     
      if(d_list[i][0].find("income" or "tax" or "department" or "gov" or "india" or "incometaxdepartment" or "income tax department")!=-1):
        flag+=1
        if(d_list[i+1][1]==('NN' or 'NNP' or 'NNPS')):
          flag+=1
          panD['name'] = str(d_list[i+1][0]).upper()
          if((d_list[i+2][0])!=None and d_list[i+3][0]!=None):
              flag+=1
              panD['fathers-name']=str(d_list[i+2][0]).upper()
              if(d_list[i+3][1]=='CD'):
                flag+=1
                panD['DOB']=str(d_list[i+3][0])
  #print(panD)
  if((flag==6)):
    storeDB(panD)
    return True
  else:
    return False



def extractUnorganisedText(im):
  print(im.shape)
  #im = cv2.resize(im,(500,340))
  text = pytesseract.image_to_string(im,config='--oem 1 --psm 3')
  store_text = text.lower()
  lis=store_text.split('\n')
  print(lis)
  return store_text,lis 

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/registeration',methods = ['POST', 'GET'] )
def reg_form():
   return render_template('reg_form.html')

@app.route('/result',methods = ['POST', 'GET'])
def result():
	reg = dict()
	reg['FirstName'] = request.form['fName']
	reg['MiddleName'] = request.form['mName']
	reg['LastName'] = request.form['lName']
	reg['Address'] = request.form['address']
	reg['Phone-Number'] = request.form['phone_number']
	file = request.files['file']
	filename = secure_filename(file.filename)
	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))	
	reg['filename'] = filename
	print("-----The Image of size of Doc should be 600x500 and the scanned doc should be in jpg format-----")
	b = reg['filename']
	imPath = 'UPLOAD_FOLDER/'+ b
	im = cv2.imread(imPath,cv2.COLOR_BGR2GRAY)
	im_one = Image.fromarray(im)
	im_one = im_one.convert('L')
	im_one = cv2.cvtColor(np.array(im_one),cv2.COLOR_RGB2BGR)
	size = im.shape
	height = size[0]
	width = size[1]


	check = 0
	if((height>=300) and (width>=500)):
		try:
			text,text_list=extractUnorganisedText(im_one)
			temp_list = filterOut(text_list)
			finalOCR = nltk.pos_tag(temp_list)
			print(finalOCR)
			bol1= fetchDetail(finalOCR,reg)
			print(bol1)
			if(bol1==False):
				try:
					text,text_list=extractUnorganisedText(im)
					temp_list = filterOut(text_list)
					finalOCR = nltk.pos_tag(temp_list)
					print(finalOCR)
					bol2= fetchDetail(finalOCR,reg)
					print(bol2)
				except(Exception): 
					check+=1
		except(Exception):
			check+=1
	else:
		value = "Size too low !"
		return render_template('low.html',value=value)
	if(check==2):
		value = "Error in the doc,Unclear image can be a reason"
		return reg_template('low.html',value=value)  
	if(bol1==True or bol2==True):
		reg['Submit Status']= "Data stored in Database !!"
	else:
		reg['Submit Status']= " Data couldn't be stored in Database,Incorrect Details or unclear image !!" 
	return render_template('result.html',result=reg)

if __name__ == '__main__':
   app.run(debug = True)