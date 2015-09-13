from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, TableStyle
from reportlab.platypus.tables import Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader, getImageData
from io import StringIO
import numpy
import cv2
from skimage import io
import requests
import json

PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
style = getSampleStyleSheet

vam_api = "http://www.vam.ac.uk/api/json/museumobject/"
vam_images = "http://media.vam.ac.uk/media/thira/collection_images/"

# from http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python

from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
# From http://stackoverflow.com/questions/5327670/image-aspect-ratio-using-reportlab-in-python

def get_image_aspect(img):
    h, w = img.shape[:2]
    aspect = h / float(w)
    return (w, h, aspect)

# ORIENTATION = LANDSCAPE, PORTRAIT

class ColouringObject(object):
    object = None
    canvas = None
    parts = []
    orientation = 'P'

    def __init__(self, obj="O122080", orientation="PORTRAIT"):
            # TODO get data for obj
            self.canvas = canvas.Canvas("%s-colouring.pdf" % obj, pagesize=A4)
            self.obj = obj

            # self.canvas.setFont( V&A Font)

    def getData(self):
        obj_url = vam_api + self.obj
        r = requests.get(obj_url)
        data = r.json()
        self.title = data[0]['fields']['title']
        self.descriptive_line = data[0]['fields']['descriptive_line']
        self.history_note = data[0]['fields']['history_note']
        self.historical_context_note = strip_tags(data[0]['fields']['historical_context_note'])
        self.place = data[0]['fields']['place']
        self.artist = data[0]['fields']['artist']
        self.object = data[0]['fields']['object']
        self.pad = data[0]['fields']['public_access_description']
        self.primary_image = data[0]['fields']['primary_image_id']
        self.date = data[0]['fields']['date_text']

# Download primary image
        if self.primary_image:
           img_url = vam_images + self.primary_image[0:6] + '/' + \
                    self.primary_image + ".jpg"
           print("DOwnloading image url: %s" % img_url)
# oooh no error handling...
#           r = requests.get(img_url)
#           image = numpy.asarray(bytearray(r.content), dtype="uint8")
#           self.image = cv2.imdecode(image, cv2.IMREAD_COLOR)
           image = io.imread(img_url)
           self.image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


    def save(self):
        self.canvas.showPage()
        self.canvas.save()

    def edgeImage(self):
        gray_img = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        edge_img = cv2.Canny(gray_img, 50, 200)
        cv2.threshold(edge_img, 1, 255, cv2.THRESH_BINARY, edge_img)
        (self.width, self.height, self.aspect) = get_image_aspect(edge_img)
        cv2.bitwise_not(edge_img, edge_img)
        cv2.imwrite("edge-" + self.obj + ".png", edge_img)
# TODO do this in memory - can't pass it to reportlab though ?
        alpha = StringIO(str(cv2.imencode('.png', edge_img)[1]))
#        invert_img = None
        l = edge_img[:, :]
        print("Got alpha: %s" % alpha)
#        self.alpha_img = cv2.merge((l, l, l, alpha))
#        cv2.imwrite("edge-" + name, self.alpha_img, -1)
#        self.image = "edge-" + name

    def drawImage(self):
        self.canvas.saveState()
# TODO make
        if((self.width > self.height) or (abs(self.width-self.height) < 150)):
# Rectangular / Landscape
            print("Landscape")
            print("Width: %d Height %d" % (self.width, self.height))
            self.orientation = 'L'
            scale_width = self.width * 0.65
            scale_height = self.height * 0.65
            self.canvas.drawImage("edge-" + self.obj + ".png", PAGE_WIDTH*0.05, PAGE_HEIGHT*0.30, width=scale_width, height=scale_height, mask='auto', preserveAspectRatio=True)
        else:
            print("Portrait")
            print("Width: %d Height %d" % (self.width, self.height))
            self.orientation = 'P'
# Portrait
            scale = self.height / float(PAGE_HEIGHT*0.7)
            scale_width = (self.width * 0.5)
            scale_height = PAGE_HEIGHT*0.5
            self.canvas.drawImage("edge-" + self.obj + ".png", PAGE_WIDTH*0.1, PAGE_HEIGHT*0.2, width=(self.width * 0.5), height=PAGE_HEIGHT*0.7, mask='auto', preserveAspectRatio=True)
        self.canvas.restoreState()

    def drawPAD(self, pad=None, historical=None):
# TODO - Choose PAD or other description. Limit length. Longer if image small
        if self.pad:
            pad_text = self.pad
        else:
            pad_text = ''
        if self.historical_context_note:
            hist_text = self.historical_context_note
        else:
            hist_text = None
        if self.descriptive_line:
            desc_text = self.descriptive_line

        parastyle = ParagraphStyle('pad')
        parastyle.textColor = 'black'
        parastyle.fontSize = 10
        paragraph = Paragraph(pad_text, parastyle)
#        self.canvas.saveState()
#        self.canvas.setFont('Times-Bold', 12)
#        self.canvas.drawString(PAGE_WIDTH*0.1, PAGE_HEIGHT*0.1, pad)
#        self.canvas.restoreState()
#        paragraph.WrapOn(self.canvas, 
        if self.orientation == 'L':
            paragraph.wrapOn(self.canvas, PAGE_WIDTH*0.9, PAGE_HEIGHT*0.1)
            paragraph.drawOn(self.canvas, PAGE_WIDTH*0.05, PAGE_HEIGHT*0.35)
        else:
            paragraph.wrapOn(self.canvas, PAGE_WIDTH*0.28, PAGE_HEIGHT*0.6)
            paragraph.drawOn(self.canvas, PAGE_WIDTH*0.68, PAGE_HEIGHT*0.15)

        if hist_text:
            parahist = Paragraph(hist_text, parastyle)
            parahist.wrapOn(self.canvas, PAGE_WIDTH*0.9, PAGE_HEIGHT*0.2)
            parahist.drawOn(self.canvas, PAGE_WIDTH*0.05, PAGE_HEIGHT*0.1)

        if desc_text:
            paradesc = Paragraph(desc_text, parastyle)
            if self.orientation == 'L':
                paradesc.wrapOn(self.canvas, PAGE_WIDTH*0.9, PAGE_HEIGHT*0.2)
                paradesc.drawOn(self.canvas, PAGE_WIDTH*0.05, PAGE_HEIGHT*0.1)

    def drawTitle(self):
# Todo - max length / multilines. Use descriptive line if no title attrib
        self.canvas.saveState()
        self.canvas.setFont('Times-Bold', 12)
        if self.title == '':
            self.title = self.descriptive_line
        if len(self.title) > 60:
            parastyle = ParagraphStyle('pad')
            parastyle.textColor = 'black'
            parastyle.fontSize = 12
            parastyle.font = 'Times-Bold'
            paragraph = Paragraph(self.title, parastyle)
            paragraph.wrapOn(self.canvas, PAGE_WIDTH*0.75, PAGE_HEIGHT*0.75)
            paragraph.drawOn(self.canvas, PAGE_WIDTH*0.05, PAGE_HEIGHT*0.92)
        else:
            self.canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT*0.92, self.title)
            self.canvas.setTitle(self.title)
            self.canvas.restoreState()

    def drawLogo(self, name="V&A-logo.png"):
#        print("Logo is %s" % getImageData(name)[0])
        self.canvas.saveState()
        logo = ImageReader(name)
#        parts.append(Image(name))
#        print("Logo is %s" % logo)
        self.canvas.drawImage(name, PAGE_WIDTH*0.8, PAGE_HEIGHT*0.9, mask='auto', width=PAGE_WIDTH*0.1, preserveAspectRatio=True)
        self.canvas.restoreState()

    def drawFooter(self, footer="V&A Colouring-In is a product of V&A Digital Media. Over 500,000 objects to colour. Gotta colour them all"):
        self.canvas.saveState()
        self.canvas.setFont('Times-Italic', 10)
        self.canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT*0.05, footer)
        self.canvas.restoreState()

        pass

    def drawURL():
        pass

    def drawMetadata(self):
        data = [('Artist', self.artist), ('Made', self.place), ('Date', self.date)]
        table = Table(data, colWidths=75, rowHeights=25)
        table.setStyle(TableStyle([
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ]))
        if self.orientation == 'L':
            table.wrapOn(self.canvas, PAGE_WIDTH*0.15, PAGE_HEIGHT*0.18)
            table.drawOn(self.canvas, PAGE_WIDTH*0.05, PAGE_HEIGHT*0.20)
        else:
            table.wrapOn(self.canvas, 0, 0)
            table.drawOn(self.canvas, PAGE_WIDTH*0.68, PAGE_HEIGHT*0.78)

    def drawLocation(self):
# TODO - Come Visit Me! I am in the ... Gallery, Room X, Case X
        data = "Medieval and Renaissance, room 8, case 13"
        pass

    def drawHistorical(self):
# TODO - historical context note ?
        pass

    def drawBiblio():
        pass

# Given Object id:
# Request JSON
# Parse JSON for fields
# Retrieve main image
# Run CO on 
# Return PDF

if __name__ == "__main__":
    col = ColouringObject(obj="O17543")
    col.getData()
    col.edgeImage()
    col.drawImage()

    col.drawLogo()
    col.drawTitle()
    col.drawPAD()
    col.drawFooter()
    col.drawMetadata()
    col.save()

