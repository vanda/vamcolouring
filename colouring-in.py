from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, TableStyle
from reportlab.platypus.tables import Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors, utils
from reportlab.pdfgen import canvas
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader, getImageData
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
#    print("Image Height: %d Width: %d") % (h, w)
    aspect = h / float(w)
    return (w, h, aspect)

# ORIENTATION = LANDSCAPE, PORTRAIT

class ColouringObject(object):
    object = None
    canvas = None
    parts = []
    orientation = 'P'

    def __init__(self, obj="O122080", orientation="PORTRAIT", font=""):
            # TODO get data for obj
            self.canvas = canvas.Canvas("%s-colouring.pdf" % obj, pagesize=landscape(A4))
            self.obj = obj

            self.loadFont(font)


    def loadFont(self, font):
        ttf = pdfmetrics.registerFont(TTFont("TheSans", font))
        ttf = pdfmetrics.registerFont(TTFont("TheSans-Bold", "TheSans_LP_700_Bold.ttf", subfontIndex=1))
        ttf = pdfmetrics.registerFont(TTFont("TheSans-Light", "TheSans_LP_200_ExtraLight.ttf", subfontIndex=2))
        pdfmetrics.registerFontFamily("TheSans", normal="TheSans", bold="TheSans-Bold", italic="TheSans-Light")

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
        self.location = data[0]['fields']['location']
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
       # img_path = "edge-" + self.obj + ".png"
       # img = utils.ImageReader(img_path)
       # iw, ih = img.getSize()
# TODO make
        print("Width: %d Height %d" % (self.width, self.height))
        if self.width <= PAGE_WIDTH*0.65:
            scale_width = self.width
        else:
            scale_width = PAGE_WIDTH*0.65
        if self.height <= PAGE_HEIGHT*0.95:
            scale_height = self.height
        else:
            scale_height = PAGE_HEIGHT*0.95
#        scale_width = self.width * 0.75
#        scale_height = self.height * 0.75
        self.canvas.drawImage("edge-" + self.obj + ".png", PAGE_HEIGHT*0.1, PAGE_WIDTH*0.05, width=scale_width, height=scale_height, mask='auto', preserveAspectRatio=True)
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
        else:
            desc_text = None

        if len(pad_text) > 1000:
            pad_text_short = pad_text[0:1000]
            i = 0
            while i < 100:
                if pad_text[1000+i] == "." or pad_text[1000+i] == "?":
                    break
                i += 1
            pad_text_short = pad_text_short + pad_text[1000:1000+i+1] + "[...]"
        else:
            pad_text_short = pad_text

        parastyle = ParagraphStyle('pad')
        parastyle.textColor = 'black'
        parastyle.fontSize = 12
        parastyle.leading = 20
        parastyle.fontName = "TheSans"
        paragraph = Paragraph(pad_text_short, parastyle)
#        self.canvas.saveState()
#        self.canvas.setFont('Times-Bold', 12)
#        self.canvas.drawString(PAGE_WIDTH*0.1, PAGE_HEIGHT*0.1, pad)
#        self.canvas.restoreState()
#        paragraph.WrapOn(self.canvas, 
        print("Public Access Text: %s", pad_text)
        paragraph.wrapOn(self.canvas, PAGE_HEIGHT*0.35, PAGE_WIDTH*0.78)
        paragraph.drawOn(self.canvas, PAGE_HEIGHT*0.635, PAGE_WIDTH*0.12)

    def drawTitle(self):
# Todo - max length / multilines. Use descriptive line if no title attrib
        self.canvas.saveState()
        self.canvas.setFont('TheSans-Bold', 14)
        if self.title == '':
            if self.descriptive_line:
                self.title = self.descriptive_line
            elif self.object:
                self.title = self.object
            else:
                self.title = "Untitled Object"

        print("Title is " + self.title)
        if len(self.title) > 60:
            self.title = self.title[0:20] + "..."
        
#            parastyle = ParagraphStyle('pad')
#            parastyle.textColor = 'black'
#            parastyle.fontSize = 12
#            parastyle.font = 'TheSans-Bold'
#            paragraph = Paragraph(self.title, parastyle)
#            paragraph.wrapOn(self.canvas, PAGE_WIDTH*0.75, PAGE_HEIGHT*0.75)
#            paragraph.drawOn(self.canvas, PAGE_WIDTH*0.05, PAGE_HEIGHT*0.92)
#        else:
        self.canvas.drawString(PAGE_HEIGHT*0.635, PAGE_WIDTH*0.92, self.title)
        self.canvas.setTitle(self.title)
        self.canvas.restoreState()

    def drawLogo(self, name="V&A-logo.png"):
#        print("Logo is %s" % getImageData(name)[0])
        self.canvas.saveState()
        logo = ImageReader(name)
#        parts.append(Image(name))
#        print("Logo is %s" % logo)
        self.canvas.drawImage(name, PAGE_HEIGHT*0.9, PAGE_WIDTH*0.85, mask='auto', width=PAGE_WIDTH*0.1, height=PAGE_WIDTH*0.1, preserveAspectRatio=True)
        self.canvas.restoreState()

    def drawFooter(self, footer=""):
        self.canvas.saveState()
        self.canvas.setFont('TheSans', 12)
        self.canvas.drawString(PAGE_WIDTH*0.9, PAGE_HEIGHT*0.04, "Find out more at")

        self.canvas.drawString(PAGE_HEIGHT*0.743, PAGE_WIDTH*0.0565, "collections.vam.ac.uk/item/%s" % self.obj)

        self.canvas.linkURL("http://collections.vam.ac.uk/item/%s" % self.obj, (PAGE_HEIGHT*0.743, PAGE_WIDTH*0.055, PAGE_HEIGHT, PAGE_WIDTH*0.1), relative=0)
        self.canvas.drawString(PAGE_WIDTH*0.9, PAGE_HEIGHT*0.02, "Visit me at the Museum. Find me in " + self.location)
        self.canvas.restoreState()

        pass

    def drawURL():
        pass

    def drawMetadata(self):
        data = [('Artist', self.artist), ('Made', self.place), ('Date', self.date)]
        data = self.artist + ", " + self.date + ", " + self.place
#        self.canvas.setFont('TheSans', 12)
#        self.canvas.drawString(PAGE_HEIGHT*0.635, PAGE_WIDTH*0.86, data)

        parastyle = ParagraphStyle('pad')
        parastyle.textColor = 'black'
        parastyle.fontSize = 10
        parastyle.leading = 20
        parastyle.font = 'TheSans-Bold'
        paragraph = Paragraph(data, parastyle)
        paragraph.wrapOn(self.canvas, PAGE_HEIGHT*0.25, PAGE_WIDTH*0.1)
        paragraph.drawOn(self.canvas, PAGE_HEIGHT*0.635, PAGE_WIDTH*0.84)

    def drawLocation(self):
# TODO - Come Visit Me! I am in the ... Gallery, Room X, Case X
        data = "Medieval and Renaissance, room 8, case 13"
        pass

    def drawHistorical(self):
# TODO - historical context note ?
        pass

    def drawBiblio():
        pass

    def drawLines(self):
        self.canvas.setLineWidth(.5)
# Divider
        self.canvas.line(PAGE_HEIGHT*0.62, PAGE_WIDTH*0.02, PAGE_HEIGHT*0.62, PAGE_WIDTH*0.95)
# Title separator
        self.canvas.line(PAGE_HEIGHT*0.635, PAGE_WIDTH*0.84, PAGE_HEIGHT*0.98, PAGE_WIDTH*0.84)


# Given Object id:
# Request JSON
# Parse JSON for fields
# Retrieve main image
# Run CO on 
# Return PDF

if __name__ == "__main__":
    col = ColouringObject(obj="O85932", font="TheSans_LP_500_Regular.ttf")
    col.getData()
    col.edgeImage()
    col.drawImage()

    col.drawLogo()
    col.drawLines()
    col.drawTitle()
    col.drawPAD()
    col.drawFooter()
    col.drawMetadata()
    col.save()

