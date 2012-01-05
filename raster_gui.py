import sys

def app():
    import Tkinter
    app = Tkinter.Tk(className='emcM144')
    app.withdraw()
    return app

def image_not_found(P):
    import tkFileDialog, tkMessageBox
    app()
    tkMessageBox.showwarning(title='M144 Raster Image Not Found',
	message='Could not find image *-%u.*\nafter searching [RASTER]IMAGE_PATH (default $HOME)' % P)
    name = tkFileDialog.askopenfilename(title='M144 Raster Image',
	initialfile='%u' % P,
	filetypes=[('Images',('*.png', '*.gif', '*.jpg', '*.tif', '*.bmp')),
	           ('Any File', '*.*')])
    if not name:
	sys.exit(2)
    return name


def fatal(msg):
    import tkMessageBox
    app()
    tkMessageBox.showerror(title='M144 Raster Error', message=msg)
    sys.exit(2)

