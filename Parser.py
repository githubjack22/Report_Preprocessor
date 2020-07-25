#Python code to parse the pdf files

#dependencies
import os
from tika import parser
from bs4  import BeautifulSoup 
import re
import sys
from pdf2image import convert_from_path 
from pdf2image.exceptions import (
 PDFInfoNotInstalledError,
 PDFPageCountError,
 PDFSyntaxError
)
import cv2 #add later
import pytesseract 
import shutil
# import json
# from  more_itertools import unique_everseen

def pdfparser(file_path,delete_existing=True):
    ''' Use this function to automatically identify the type
    of pdf file and call corresponding functions to parse pdf and store the content
    of each page into a text file'''

    # use tika parser to read the file first and keep the xhtml structure
    if file_path[-4:] != '.pdf':
        raise Exception("Please make sure you are parsing a pdf file")
    parsed = parser.from_file(file_path, xmlContent=True)
    raw_text = parsed['content'] #xhtml structured text
    # all the contents are stored within "page"
    soup = BeautifulSoup(raw_text)
    first_page = soup.find('div', attrs={ "class" : "page"}).\
    text.replace('\n','')
    if len(first_page)>10: #this is a text-formatted pdf
        print('parsing text-formatted pdf file')
        # write the content into a text file in 
        # the same folder 
        textpdf_to_text(file_path,raw_text)

    else:
        # parsing from a image-formatted pdf 
        # write the content into a text file in 
        # the same folder 
        print('parsing image-formatted pdf file')
        imagepdf_to_text(file_path,delete_existing)
            	
def textpdf_to_text(file_path,text):
    '''Takes file_path and xhtml text as input and
    write the content of each page into a txt file'''
    soup = BeautifulSoup(text)
    page_list = soup.find_all('div', attrs={ "class" : "page"})
    # store all pages in a list
    page_list = [i.text for i in page_list]
    outfile=f'{file_path[:-4]}_text.txt'
    # check if the file contains bookmark
    bookmark = soup.find_all('li')
    toc = [x.text for x in bookmark if len(bookmark)>0]
    
    with open(outfile, "w+") as f:
        # Write pages
        for i,txt in enumerate(page_list):
            if i==0:
                f.write(f'<Read from Text>')
            f.write(f'<Page Start>')
            txt = txt.replace("’","'")
            f.write(txt)
            f.write(f'<Page End>')
        #Write table of contents if any
        if len(toc)>0:
            f.write(f'<PDF contains bookmark>')
            toc_string = '\n'.join(toc)
            f.write(toc_string)
    print(f'parsing finished:{file_path[:-4]}')

def imagepdf_to_text(file_path,delete_existing):
    '''Takes file_path as input, split the file into 
    pages and read text from each page write the 
    content of each page into a txt file'''
    new_folder = os.path.join(os.getcwd(),file_path[0:-4])
    try:
        os.mkdir(new_folder)
        images = convert_from_path(file_path)
        
        for i, image in enumerate(images,start=1):
            fname = f'{new_folder}/page-'+str(i)+'.png'
            image.save(fname, "PNG") 

    except:
        print(f'Folder of {file_path} already exsits')
        if delete_existing==True:
            print('Delete the exisiting folder')
            shutil.rmtree(new_folder)
            os.mkdir(new_folder)
            images = convert_from_path(file_path)

            for i, image in enumerate(images,start=1):
                fname = f'{new_folder}/page-'+str(i)+'.png'
                image.save(fname, "PNG") 
  
    outfile = f'{file_path[:-4]}_text.txt'
    maxpage = max([int(re.findall(r'[0-9]+',i)[0]) for i in os.listdir(f'{new_folder}') if i[-3:] == 'png'])

    with open(outfile, "w+") as f:
        for i in range(1, maxpage+1): 
            # reading image using opencv
            temp_filename =f'{new_folder}/page-'+str(i)+".png"
            image = cv2.imread(temp_filename)
            #converting image into gray scale image
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # converting it to binary image by Thresholding
            # this step is require if you have colored image because if you skip this part 
            # then tesseract won't able to detect text correctly and this will give incorrect result
            threshold_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            
            # Recognize the text as string in image using pytesserct 
            txt = pytesseract.image_to_string(threshold_img,lang='eng') 
            # Finally, write the processed text to the file. 
            txt = txt.replace("’","'")
            if i==1:
                f.write(f'<Read from Image>')
            f.write(f'<Page Start>')
            f.write(txt)
            f.write(f'<Page End>')
    print(f'parsing finished:{file_path[:-4]}')

def text_to_dict(file_path):
    '''Use this function to read the text file and 
    store it to dictionary'''
    page_dict = {}
    file_name = file_path.split('/')[-1]
    page_dict['file_name']=file_name[0:-4]
    with open(file_path,'r') as f:
        text = f.read()
        source_type = re.findall(r'<Read from (\w+)?>',text)
        page_list = re.findall(r'<Page Start>([\s\S]+?)<Page End>',text)
        toc = re.findall(r'<PDF contains bookmark>([\s\S]+)',text)
        page_dict['bookmark'] = toc
        page_dict['raw_text'] = page_list
        page_dict['source_type'] = source_type
        return page_dict


