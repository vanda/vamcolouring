from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ORIENTATION = LANDSCAPE, PORTRAIT

class ColouringObject(object):
    canvas = None

    def __init__(self, id="O122080", orientation="PORTRAIT"):
            self.canvas = canvas.Canvas("O122080-colouring.pdf", pagesize=A4)

            # self.canvas.setFont( V&A Font)

            self.drawTitle()
            self.canvas.showPage()
            self.canvas.save()

    def colourImage(self):
        pass

    def drawImage(self):
        # self.canvas.drawInlineImage(self, image, x, y, width, height)
        pass

    def drawPAD(self):
        pass

    def drawTitle(self, title="Ring"):
        self.canvas.drawString(100, 100, title)
        self.canvas.setTitle(title)

    def drawHeader():
        pass

    def drawFooter():
        pass

    def drawLocation():
        pass

    def drawBiblio():
        pass

if __name__ == "__main__":
    ColouringObject()
