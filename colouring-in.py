from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader, getImageData

PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
style = getSampleStyleSheet

# ORIENTATION = LANDSCAPE, PORTRAIT

class ColouringObject(object):
    canvas = None
    parts = []

    def __init__(self, id="O122080", orientation="PORTRAIT"):
            self.canvas = canvas.Canvas("O122080-colouring.pdf", pagesize=A4)

            # self.canvas.setFont( V&A Font)

    def save(self):
        self.canvas.showPage()
        self.canvas.save()

    def colourImage(self):
        pass

    def drawImage(self):
        # self.canvas.drawInlineImage(self, image, x, y, width, height)
        pass

    def drawPAD(self, pad=None):
# TODO - Choose PAD or other description. Limit length.
        pad = "In contrast to the rich garnet-set jewellery of the earlier Anglo-Saxon period, finger rings of the ninth century are rarely adorned with precious stones. The skills of the goldsmith are seen in this example, where the different techniques of filigree and granulation are combined to produce an elaborately decorated ring."
        parastyle = ParagraphStyle('pad')
        parastyle.textColor = 'black'
        parastyle.fontSize = 12
        paragraph = Paragraph(pad, parastyle)
#        self.canvas.saveState()
#        self.canvas.setFont('Times-Bold', 12)
#        self.canvas.drawString(PAGE_WIDTH*0.1, PAGE_HEIGHT*0.1, pad)
#        self.canvas.restoreState()
#        paragraph.WrapOn(self.canvas, 
        paragraph.wrapOn(self.canvas, PAGE_WIDTH*0.8, PAGE_HEIGHT*0.2)
        paragraph.drawOn(self.canvas, PAGE_WIDTH*0.1, PAGE_HEIGHT*0.1)

    def drawTitle(self, title="Ring"):
# Todo - max length / multilines. Use alt if no title attrib
        self.canvas.saveState()
        self.canvas.setFont('Times-Bold', 32)
        self.canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT*0.91, title)
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

    def drawFooter(self, footer="V&A Colouring-In is a product of V&A Digital Media"):
        self.canvas.saveState()
        self.canvas.setFont('Times-Bold', 12)
        self.canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT*0.05, footer)
        self.canvas.restoreState()

        pass

    def drawURL():
        pass

    def drawLocation():
        pass

    def drawBiblio():
        pass

if __name__ == "__main__":
    col = ColouringObject()
    col.drawLogo("./V&A logo-80x47.png")
    col.drawTitle()
    col.drawPAD()
    col.drawFooter()
    col.save()
