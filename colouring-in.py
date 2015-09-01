from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, TableStyle
from reportlab.platypus.tables import Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader, getImageData
import cv2
import requests
import json

PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
style = getSampleStyleSheet

# From http://stackoverflow.com/questions/5327670/image-aspect-ratio-using-reportlab-in-python

def get_image_aspect(path):
    img = ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return (iw, ih, aspect)

# ORIENTATION = LANDSCAPE, PORTRAIT

class ColouringObject(object):
    canvas = None
    parts = []
    orientation = 'P'

    def __init__(self, obj="O122080", orientation="PORTRAIT"):
            self.canvas = canvas.Canvas("O122080-colouring.pdf", pagesize=A4)

            # self.canvas.setFont( V&A Font)

    def save(self):
        self.canvas.showPage()
        self.canvas.save()

    def edgeImage(self, name):
        orig_img = cv2.imread(name, -1)
        gray_img = cv2.cvtColor(orig_img, cv2.COLOR_BGR2GRAY)
        edge_img = cv2.Canny(gray_img, 50, 200)
        cv2.threshold(edge_img, 1, 255, cv2.THRESH_BINARY, edge_img)
        invert_img = None
        cv2.bitwise_not(edge_img, edge_img)
        l = edge_img[:, :]
        alpha_img = cv2.merge((l, l, l, l))
        cv2.imwrite("edge-" + name, alpha_img)
        self.image = "edge-" + name

    def drawImage(self):
        self.canvas.saveState()
        (width, height, aspect) = get_image_aspect(self.image)
# TODO make
        if(abs(width-height) < 150):
# Rectangular / Landscape
            scale_width = width * 0.7
            scale_height = height * 0.7
            self.canvas.drawImage(self.image, PAGE_WIDTH*0.2, PAGE_HEIGHT*0.3, width=scale_width, height=scale_height)
        else:
# Portrait
            scale = height / float(PAGE_HEIGHT*0.7)
            scale_width = (width * 0.7)
            scale_height = PAGE_HEIGHT*0.7
            self.canvas.drawImage(self.image, PAGE_WIDTH*0.1, PAGE_HEIGHT*0.2, width=(width * 0.7), height=PAGE_HEIGHT*0.7)
        self.canvas.restoreState()

    def drawPAD(self, pad=None, historical=None):
# TODO - Choose PAD or other description. Limit length. Longer if image small
        pad = "In contrast to the rich garnet-set jewellery of the earlier Anglo-Saxon period, finger rings of the ninth century are rarely adorned with precious stones. The skills of the goldsmith are seen in this example, where the different techniques of filigree and granulation are combined to produce an elaborately decorated ring."
        historical = "Other than having been found in the moat, this ring has no known connection to Meaux Abbey, which was founded in 1150 by William le Gros. There appears to have been no preceding settlement recorded on the site, which was in the flood plain of the River Hull, marshy land and prone to flooding. In the ninth-century the site was within the boundaries of the Anglo-Saxon kingdom of Northumbria. It was a turbulent period for the region, with Viking raids in the first half of the century, which included the sacking of Beverley Abbey. The second half of the century saw the settlement of Danish invaders. The Anglo-Saxon Chronicle describes armies of 865 and 871 as \"great\" and says that they shared out the land in Northumbria.\nIn contrast to the rich garnet-set jewellery of the earlier Anglo-Saxon period, finger rings are rarely adorned with precious stones. Gold finger rings have been found amongst the grave goods of both male and female adults in Scandanavian and Anglo-Saxon burials. The decoration on the ring is Anglo-Saxon with what Oman terms viking influence. R.Jessup suggests that the animal decoration should be compared with that on the Alfred jewel and Ethelswith's ring. Alfred and Ethelswith were royalty of the kingdom of Wessex, however Ethelswith's ring (in common with the present example) was found in the West Riding of Yorkshire rather than Wessex.\"Styles common in Wessex, especially near Winchester, have been found in the Danelaw, and a mould for making this sort of jewellery has been found at York\" (Invisible Vikings - British Archaeology Magazine April 2002)."
        parastyle = ParagraphStyle('pad')
        parastyle.textColor = 'black'
        parastyle.fontSize = 10
        paragraph = Paragraph(pad, parastyle)
#        self.canvas.saveState()
#        self.canvas.setFont('Times-Bold', 12)
#        self.canvas.drawString(PAGE_WIDTH*0.1, PAGE_HEIGHT*0.1, pad)
#        self.canvas.restoreState()
#        paragraph.WrapOn(self.canvas, 
        paragraph.wrapOn(self.canvas, PAGE_WIDTH*0.9, PAGE_HEIGHT*0.1)
        paragraph.drawOn(self.canvas, PAGE_WIDTH*0.05, PAGE_HEIGHT*0.35)
        parahist = Paragraph(historical, parastyle)
        parahist.wrapOn(self.canvas, PAGE_WIDTH*0.9, PAGE_HEIGHT*0.2)
        parahist.drawOn(self.canvas, PAGE_WIDTH*0.05, PAGE_HEIGHT*0.1)

    def drawTitle(self, title="Gold ring, with broad stirrup-shaped hoop, the shoulders ornamented with filigree and granulation in the form of dragon heads, the bezel a pellet of gold, Anglo Saxon, 800-900"):
# Todo - max length / multilines. Use descriptive line if no title attrib
        self.canvas.saveState()
        self.canvas.setFont('Times-Bold', 12)
        if len(title) > 32:
            parastyle = ParagraphStyle('pad')
            parastyle.textColor = 'black'
            parastyle.fontSize = 12
            paragraph = Paragraph(title, parastyle)
            paragraph.wrapOn(self.canvas, PAGE_WIDTH*0.75, PAGE_HEIGHT*0.75)
            paragraph.drawOn(self.canvas, PAGE_WIDTH*0.05, PAGE_HEIGHT*0.92)
        else:
            self.canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT*0.92, title)
            self.canvas.setTitle(title)
            self.canvas.restoreState()

    def drawLogo(self, name="V&A logo.png"):
#        print("Logo is %s" % getImageData(name)[0])
        self.canvas.saveState()
        logo = ImageReader(name)
#        parts.append(Image(name))
#        print("Logo is %s" % logo)
        self.canvas.drawImage(name, PAGE_WIDTH*0.8, PAGE_HEIGHT*0.9, mask='auto')
        self.canvas.restoreState()

    def drawFooter(self, footer="V&A Colouring-In is a product of V&A Digital Media. Over 500,000 objects to colour"):
        self.canvas.saveState()
        self.canvas.setFont('Times-Italic', 10)
        self.canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT*0.05, footer)
        self.canvas.restoreState()

        pass

    def drawURL():
        pass

    def drawMetadata(self):
        data = [('Artist', 'Unknown'), ('Made', 'Meaux'), ('Date', 'C10th')]
        table = Table(data, colWidths=50, rowHeights=25)
        table.setStyle(TableStyle([
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ]))
        table.wrapOn(self.canvas, 0, 0)
        table.drawOn(self.canvas, PAGE_WIDTH*0.72, PAGE_HEIGHT*0.7)

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
    col = ColouringObject(obj="O122080")
    col.drawLogo("./V&A logo-80x47.png")
    col.drawTitle()
    col.drawPAD()
    col.drawFooter()
    col.drawMetadata()
    col.edgeImage(name="2006BA0296.jpg")
    col.drawImage()
    col.save()

