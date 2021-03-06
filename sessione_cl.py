import itertools
import thread
import glob
import cv2
import re
import numpy as np
import scipy.interpolate as si
import scipy.signal as signal
import scipy.fftpack as fft
import scipy.optimize as sopt
from scipy import stats
from scipy import ndimage
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.cm as cm
import matplotlib.image as mpimg
import matplotlib.patches as patches
from matplotlib.patches import BoxStyle
from matplotlib import gridspec
from matplotlib.cbook import get_sample_data
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.transforms import Bbox, TransformedBbox, blended_transform_factory
from mpl_toolkits.axes_grid1.inset_locator import BboxPatch, BboxConnector, BboxConnectorPatch
from mpl_toolkits.mplot3d import Axes3D
import matplotlib 
import pickle
import os.path


def referencePanel(ax,text,x,y):
	ax.text(x,y, text ,horizontalalignment='center',verticalalignment='center',fontweight='bold',fontsize=18,transform=ax.transAxes)



def customaxis(ax, c_left='k', c_bottom='k', c_right='none', c_top='none',
               lw=1, size=12, pad=5):

    for c_spine, spine in zip([c_left, c_bottom, c_right, c_top],
                              ['left', 'bottom', 'right', 'top']):
        if c_spine != 'none':
            ax.spines[spine].set_color(c_spine)
            ax.spines[spine].set_linewidth(lw)
        else:
            ax.spines[spine].set_color('none')
    if (c_bottom == 'none') & (c_top == 'none'): # no bottom and no top
        ax.xaxis.set_ticks_position('none')
    elif (c_bottom != 'none') & (c_top != 'none'): # bottom and top
        ax.tick_params(axis='x', direction='out', width=lw, length=7,
                      color=c_bottom, labelsize=size, pad=pad)
    elif (c_bottom != 'none') & (c_top == 'none'): # bottom but not top
        ax.xaxis.set_ticks_position('bottom')
        ax.tick_params(axis='x', direction='out', width=lw, length=7,
                       color=c_bottom, labelsize=size, pad=pad)
    elif (c_bottom == 'none') & (c_top != 'none'): # no bottom but top
        ax.xaxis.set_ticks_position('top')
        ax.tick_params(axis='x', direction='out', width=lw, length=7,
                       color=c_top, labelsize=size, pad=pad)
    if (c_left == 'none') & (c_right == 'none'): # no left and no right
        ax.yaxis.set_ticks_position('none')
    elif (c_left != 'none') & (c_right != 'none'): # left and right
        ax.tick_params(axis='y', direction='out', width=lw, length=7,
                       color=c_left, labelsize=size, pad=pad)
    elif (c_left != 'none') & (c_right == 'none'): # left but not right
        ax.yaxis.set_ticks_position('left')
        ax.tick_params(axis='y', direction='out', width=lw, length=7,
                       color=c_left, labelsize=size, pad=pad)
    elif (c_left == 'none') & (c_right != 'none'): # no left but right
        ax.yaxis.set_ticks_position('right')
        ax.tick_params(axis='y', direction='out', width=lw, length=7,
                       color=c_right, labelsize=size, pad=pad)




class zoomPanel():
	def __init__(self,Test=False,x1=0.3,x2=0.35):
		if Test:
			plt.figure(1, figsize=(5, 5))
			ax1 = plt.subplot(211)
			ax2 = plt.subplot(212)
			ax1.set_xlim(0, 2.25)
			ax2.set_xlim(x1, x2)
			for a in [ax1,ax2]:
				for spine in ['top','bottom','left','right']:
					a.spines[spine].set_visible(False)
			self.zoom_effect(ax1, ax2, x1, x2)
			plt.show()

	def connect_bbox(self,bbox1, bbox2,loc1a, loc2a, loc1b, loc2b,prop_lines, prop_patches=None):
		if prop_patches is None:
			prop_patches = prop_lines.copy()
			prop_patches["alpha"] = prop_patches.get("alpha", 1)*0.2

		c1 = BboxConnector(bbox1, bbox2, loc1=loc1a, loc2=loc2a, **prop_lines)
		c1.set_clip_on(False)
		c2 = BboxConnector(bbox1, bbox2, loc1=loc1b, loc2=loc2b, **prop_lines)
		c2.set_clip_on(False)

		bbox_patch1 = BboxPatch(bbox1, **prop_patches)
		bbox_patch2 = BboxPatch(bbox2, **prop_patches)

		p = BboxConnectorPatch(bbox1, bbox2,loc1a=loc1a, loc2a=loc2a, loc1b=loc1b, loc2b=loc2b,**prop_patches)
		p.set_clip_on(False)

		return c1, c2, bbox_patch1, bbox_patch2, p


	def zoom_effect(self,ax1, ax2, xmin, xmax, **kwargs):
		"""
		ax1 : the main axes
		ax1 : the zoomed axes
		(xmin,xmax) : the limits of the colored area in both plot axes.

		connect ax1 & ax2. The x-range of (xmin, xmax) in both axes will
		be marked.  The keywords parameters will be used ti create
		patches.

		"""

		trans1 = blended_transform_factory(ax1.transData, ax1.transAxes)
		trans2 = blended_transform_factory(ax2.transData, ax2.transAxes)

		bbox = Bbox.from_extents(xmin, 0, xmax, 1)

		mybbox1 = TransformedBbox(bbox, trans1)
		mybbox2 = TransformedBbox(bbox, trans2)

		prop_patches = kwargs.copy()
		prop_patches["ec"] = "none"
		prop_patches["alpha"] = 0.1

		c1, c2, bbox_patch1, bbox_patch2, p = self.connect_bbox(mybbox1, mybbox2,loc1a=3, loc2a=2, loc1b=4, loc2b=1,prop_lines=kwargs, prop_patches=prop_patches)

		ax1.add_patch(bbox_patch1)
		ax2.add_patch(bbox_patch2)
		ax2.add_patch(c1)
		ax2.add_patch(c2)
		ax2.add_patch(p)

		return c1, c2, bbox_patch1, bbox_patch2, p



class simulatedAndSetup():
	def __init__(self):
		# confronto spettri
		simulatedD21 = DATA_PATH+'/elab_video/simulatedWhisker/transffunct_D21_bw1000Hz_sim.txt'  
		a = sessione('d21','12May','_NONcolor_','puppa',(0,0,0,0),-1,True, False)
		lamp    = DATA_PATH+'/elab_video/Setup_color_transparent_background_LAMP.png'
		whisker = DATA_PATH+'/elab_video/Setup_color_transparent_background_WHISKER.png'
		LAMP    = mpimg.imread(lamp)
		WHISKER = mpimg.imread(whisker)
		WHISKER = np.fliplr(WHISKER)
		#
		a.calcoloTransferFunction(False)
		spettroVero = a.TFM 
		spettroSim = np.flipud(np.loadtxt(simulatedD21))
		spettroSim = spettroSim[:-2,3:]
		# figura
		f = plt.figure(figsize=(FIGSIZEx,2*FIGSIZEy))
		gs  = gridspec.GridSpec(4,2,width_ratios=[0.03,0.7,0,1],hspace=0.35, wspace=0.15)
		gs2 = gridspec.GridSpec(18,5)
		gs3 = gridspec.GridSpec(4,2,width_ratios=[0.03,1,0,1],hspace=0.35, wspace=0.15)
		a1 = f.add_subplot(gs[0,1])
		a3 = f.add_subplot(gs[1,1])
		a1.set_title(r'Log$_{10}$(TF)',fontsize=FONTSIZE)
		customaxis(a1,size=FONTSIZE,pad=5)
		customaxis(a3,size=FONTSIZE,pad=5)
		a2l = f.add_subplot(4,2,2)
		a2l.imshow(LAMP)
		a2w = f.add_subplot(4,2,4)
		a2w.imshow(WHISKER)
		a4  = f.add_subplot(gs2[12,0])
		a4z = f.add_subplot(gs2[13,0])
		a5  = f.add_subplot(gs[2,1])
		# panel con lo stacked dell'image processing
		stacked = creoImageProcessing_Stacked()
		def plotStacked(ax,x_offset,y_offset,stacked):
			FS = FONTSIZE
			ax.text(100-80,30,"Raw Image",fontsize=FS,color='white') 
			ax.text(100+y_offset-80,30+x_offset,"Thresholding",fontsize=FS,color='white') 
			ax.text(100+2*y_offset-80,30+2*x_offset,"B-spline model",fontsize=FS,color='white') 
			ax.set_xticks([])
			ax.set_yticks([])
			ax.imshow(stacked,cmap='gray')
		x_offset,y_offset = stacked.offset
		plotStacked(a5,x_offset,y_offset,stacked.stacked)
			
		# panel con l'andamento dello shaker, ovvero l'input al sistema baffo, ovvero il punto alla base del baffo che ho stimato con il tracking
		def getShakerTimeTrend():
			if 0: 	# estimate the shaker movement as the base of the whisker. camera resolution cause low resolution for a proper visualization of the signal. 
					# however, it is correct to use this signal as input to each LTI system (the points from the discretization of the whisker) not to lose the GAIN of TF
				elabSessione = False
				sess = sessione('d21','12May','_NONcolor_',DATA_PATH+'/ratto1/d2_1/',(310, 629, 50, 210),29,True,elabSessione,False,True) # carico la sessione senza elabolarla
				sess.loadTracking() # carico i dati
				v = sess.V[0] # prendo un video
				traiettorie,nPunti,nCampioni = (v.wst,v.wst.__len__(),v.wst[0].__len__())
				base = traiettorie[nPunti-1].tolist()
				base[:2]   = [] # compatto il numero di campioni in cui il baffo sta fermo prima e dopo lo stimolo
				base[-380:] = [] 
				return base-np.mean(base)
			if 1:  # load the input from the shaker
				frozenNoises = np.loadtxt(DATA_PATH+'/camrec450_verFunc/stim/stimoli.txt')
				return frozenNoises[0]
			
		s = getShakerTimeTrend() 
		STD = np.std(s)
		Np = len(s)
		zoom = zoomPanel()
		wTime = .2 			# sec
		w = int(wTime*2000)	# samples
		x1,x2 = (Np/2-w/2,Np/2+w/2)
		kkk = 100 # fattore di ragguaglio perche` lo zoom non ombreggia sui valori giusti
		a4.plot([x1+kkk,x2-kkk],[4,4],color='k',linewidth=3)
		a4.text(x1-500,5,str(int(wTime*1000))+' ms',fontsize=FONTSIZE*0.8)
		a4.plot([-500,-500],[-1*STD,1*STD],color='k',linewidth=2)
		a4.text(-1500,1,r'$\pm$1 STD', rotation=90,fontsize=FONTSIZE*0.8)
		#a4.annotate('', xy=(x1,-1), xycoords='axes fraction', xytext=(x2,-1), arrowprops=dict(color='k',width=1,headwidth=5,headlength=5))
		#a4.annotate('', xy=(x2,-1), xycoords='axes fraction', xytext=(x1,-1), arrowprops=dict(color='k',width=1,headwidth=5,headlength=5))
		#a4.annotate('', xy=(-.1, .1), xycoords='axes fraction', xytext=(-.1, .9), arrowprops=dict(color='k',width=.1,headwidth=5,headlength=5))
		#a4.annotate('', xy=(-.1, .9), xycoords='axes fraction', xytext=(-.1, .1), arrowprops=dict(color='k',width=.1,headwidth=5,headlength=5))
		#a4z.annotate('', xy=(0,-.3), xycoords='axes fraction', xytext=(.95,-.3), arrowprops=dict(color='k',width=.1,headwidth=5,headlength=5))
		#a4z.annotate('', xy=(.95,-.3), xycoords='axes fraction', xytext=(0,-.3), arrowprops=dict(color='k',width=.1,headwidth=5,headlength=5))
		#a4z.text(0,0, 'ppp') #str(int(wTime*1000))+' ms') #, fontsize=FONTSIZE)
		zoom.zoom_effect(a4, a4z, x1, x2)
		t = xrange(10,Np+10,1)
		a4.plot(t,s,linewidth=0.5,color='k')
		a4z.plot(xrange(x1,x2),s[x1:x2],linewidth=0.5,color='k')
		def unvisibleAxes(ax):
			ax.axes.get_xaxis().set_visible(False)
			ax.axes.get_yaxis().set_visible(False)
			for spine in ['top', 'right','bottom','left']:
				ax.spines[spine].set_visible(False)
		[unvisibleAxes(ax) for ax in [a2l,a2w,a4,a4z,a5]]
		cax1 = a1.imshow(np.log10(spettroSim[:,SPECTRAL_RANGE]),vmin=-0.4,vmax=1.2,aspect='auto', interpolation="gaussian",cmap='RdBu_r')
		cax3 =a3.imshow(np.log10(spettroVero[:,SPECTRAL_RANGE]),vmin=-0.4,vmax=1.2,aspect='auto', interpolation="gaussian",cmap='RdBu_r')
		# colorbar
		#cbar1 = f.colorbar(cax1,ax=a1)
		#cbar3 = f.colorbar(cax3,ax=a3)
		def setcolorbar(acb):
			cbar =  matplotlib.colorbar.ColorbarBase(acb,orientation='vertical',cmap='RdBu_r')
			cbar.ax.set_yticklabels(['']+[str(l/10.) for l in xrange(-4,14,2)])
			cbar.ax.tick_params(labelsize=FONTSIZE) 
			acb.yaxis.set_ticks_position('left')
			acb.set_ylabel(r'Log$_{10}$(|H|)')
			acb.yaxis.set_label_coords(-6,0.5)

		a01 = f.add_subplot(gs3[0,0])
		a11 = f.add_subplot(gs3[1,0])
		setcolorbar(a01)
		setcolorbar(a11)
		
		#
		a1.set_yticks([])
		a3.set_yticks([])
		a1.set_xticks(xrange(0,400,100))
		a3.set_xticks(xrange(0,400,100))
		a1.set_ylabel(r'Base     $\longrightarrow$      Tip',fontsize = FONTSIZE)
		a1.set_xlabel('Frequency [Hz]',fontsize = FONTSIZE) 
		a3.set_ylabel(r'Base     $\longrightarrow$      Tip',fontsize = FONTSIZE)
		a3.set_xlabel('Frequency [Hz]',fontsize = FONTSIZE)
		#
		posa01 = a01.get_position()
		a01.set_position([posa01.x0-0.02, posa01.y0+0, posa01.width+0, posa01.height+0])
		posa11 = a11.get_position()
		a11.set_position([posa11.x0-0.02, posa11.y0+0, posa11.width+0, posa11.height+0])
		posa1 = a1.get_position()
		a1.set_position([posa1.x0-0.04, posa1.y0+0, posa1.width+0, posa1.height+0])
		pos2w = a2w.get_position()
		a2w.set_position([pos2w.x0-0.09, pos2w.y0-0, pos2w.width+0, pos2w.height+0])
		pos2l = a2l.get_position()
		a2l.set_position([pos2l.x0-0.03, pos2l.y0+0, pos2l.width+0, pos2l.height+0])
		posa3 = a3.get_position()
		a3.set_position([posa3.x0-0.04, posa3.y0+0, posa3.width+0, posa3.height+0])
		posa5 = a5.get_position()
		a5.set_position([posa5.x0+0.515, posa5.y0+.21, posa5.width+0, posa5.height+0])
		for ax in [a4,a4z]:
			pos4 = ax.get_position()
			ax.set_position([pos4.x0+.36, pos4.y0+.333, pos4.width+0, pos4.height+0])
			ax.patch.set_alpha(0.5)
		referencePanel(a01,'A',-8	, 1.1)
		referencePanel(a01,'B', 35  , 1.1)
		referencePanel(a11,'C',-8	, 1.1)
		if 0: # save subplot with signal
			print 'specific subplot'
			#extent = ax2.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
			#f.savefig(DATA_PATH+'/elab_video/simulationAndSetup.pdf',dpi=400,bbox_inches='tight')
		else:
			f.savefig(DATA_PATH+'/elab_video/simulationAndSetup.pdf',dpi=400,bbox_inches='tight')
		
	
class creoImageProcessing_Stacked(): # 
	def __init__(self,Stampa=False): 
		self.stacked,self.offset = self.getStacked()
		if Stampa:
			x_offset,y_offset = offset
			fig = plt.figure()
			ax = fig.add_subplot(1,1,1)		
			FS = 22
			ax.text(100-80,30,"Raw Image",fontsize=FS,color='white') 
			ax.text(100+y_offset-80,30+x_offset,"Thresholding",fontsize=FS,color='white') 
			ax.text(100+2*y_offset-80,30+2*x_offset,"B-spline model",fontsize=FS,color='white') 
			ax.set_xticks([])
			ax.set_yticks([])
			ax.imshow(stacked,cmap='gray')
			fig.savefig(DATA_PATH+'/elab_video/stacked.png') # <--- serve per la base della figura 2
	
	def getStacked(self):

		elabSessione = False
		s = sessione('d21','12May','_NONcolor_',DATA_PATH+'/ratto1/d2_1/',(310, 629, 50, 210),29,True,elabSessione,False,True) # carico la sessione senza elabolarla
		s.resolvePath(s.path)
		avi = s.aviList[0]
		v = video(avi,(0,650-340,0,235-100),29,False,False,False)
		cap = cv2.VideoCapture(avi) 	
		_,Read = cap.read()
		Read = Read[110:235,358:650]   	
		Frame_raw = cv2.cvtColor(Read, cv2.COLOR_BGR2GRAY) 						
		Frame_blur = cv2.medianBlur(Frame_raw,3)  											
		Frame_ths = cv2.threshold(Frame_blur,v.videoThs,255,cv2.THRESH_BINARY)[1]  	     # ths 
		Frame_Bspline = cv2.threshold(Frame_blur,v.videoThs,255,cv2.THRESH_BINARY)[1]  	 # blur 
		x,y = v.get_whisker(Frame_Bspline) 
		x,y = v.norm_whisker(x,y,35,3)
		x = x[:-2] # tolgo la base dalla stima (NON ho definito una ROI qui...) 
		y = y[:-2] # tolgo la base dalla stima (NON ho definito una ROI qui...) 
		Frame_Bspline/=5 #3.0 
		for i,j in zip(x,y): 
			if not np.isnan(j):
				i = int(i)
				j = int(j)
				for k1 in range(-2,2):
					for k2 in range(-2,2):
						Frame_Bspline[j+k1][i+k2] = 255
		# le salvo
		cv2.imwrite(DATA_PATH+'/elab_video/ImageProc_Raw.jpg',			Frame_raw)     
		cv2.imwrite(DATA_PATH+'/elab_video/ImageProc_Blurred.jpg',		Frame_blur)     
		cv2.imwrite(DATA_PATH+'/elab_video/ImageProc_Thresholded.jpg',	Frame_ths)     
		cv2.imwrite(DATA_PATH+'/elab_video/ImageProc_Bspline.jpg',		Frame_Bspline)     
	
		# plot	
		Layers = [] 
		Layers.append(np.fliplr(Frame_raw))     
		Layers.append(np.fliplr(Frame_ths))     
		Layers.append(np.fliplr(Frame_Bspline)) 

		x_offset, y_offset = 90, 90  # Number of pixels to offset each image.
		r = Frame_raw
		new_shape = ((Layers.__len__() - 1)*y_offset + r.shape[0],
					 (Layers.__len__() - 1)*x_offset + r.shape[1])  # the last number, i.e. 4, refers to the 4 different channels, being RGB + alpha

		stacked = 100*np.ones(new_shape, dtype=np.float)
		for layer,L in zip(range(Layers.__len__()),Layers):
			stacked[layer*y_offset:layer*y_offset + r.shape[0],
					layer*x_offset:layer*x_offset + r.shape[1], 
					...] = L*1./Layers.__len__()
		return stacked,(x_offset,y_offset)
		

class stampo_lunghezza_whiskers(): # calcolo le lunghezze dei baffi e le stampo a video
	def __init__(self,SovrascriviPickle=False,Stampa=False): 
		self.FILEs = [\
				DATA_PATH+"/ratto1/a1_1/0951_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/a3_1/1011_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/a4_1/1056_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/b1_1/1033_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/c1_1/1251_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/c1_2/0215_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/c2_1/0114_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/c2_2/0133_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/c3_1/11May2016/1054_110516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/c4_1/0236_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/c5_1/0442_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/d1_1/0504_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/d2_1/0525_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/d2_2/0547_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/d3_1/0625_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/delta_1/0847_120516_NONcolor_trial1.avi",
				DATA_PATH+"/ratto1/gamma_1/1012_120516_NONcolor_trial1.avi"]
		self.NAMEs = [\
				"a1_1",
				"a3_1",
				"a4_1",
				"b1_1",
				"c1_1",
				"c1_2",
				"c2_1",
				"c2_2",
				"c3_1",
				"c4_1",
				"c5_1",
				"d1_1",
				"d2_1",
				"d2_2",
				"d3_1",
				"delta_1",
				"gamma_1"
					]
		self.ROIs = [\
				# ordine imshow come y-x
				(315,621,64,193),  # a11
				(490,630,173,210), # a31
				(565,636,137,196), # a41
				(453,625,186,239), # b11
				(217,638,172,206), # c11
				(334,644,98,213),  # c12
				(393,623,149,220), # c21
				(272,664,101,162), # c22
				(348,626,177,212), # c31
				(450,643,106,138), # c41
				(500,635,185,204), # c51
				(246,642,122,185), # d11
				(336,629,115,192), # d21
				(360,637,91,165),  # d22
				(427,624,166,238), # d31
				(348,741,10,238),  # delta1
				(337,755,123,173), # gamma1
				]
		# misure diametri alla base ed alla punta presi al microscopio
		self.Diameters = [\
				(10.44  , 168.431),   # a11    
				(5.691  , 79.327 ),   # a31    
				(3.686  , 83.690 ),   # a41    
				(7.164  , 98.353 ),   # b11     
				(14.150 , 187.985),   # c11     
				(8.944  , 162.327),   # c12    
				(11.757 , 164.994),   # c21     
				(12.100 , 188.878),   # c22     
				(18.265 , 133.237),   # c31     
				(6.036  , 96.673 ),   # c41
				(6.096  , 113.736),   # c51    
				(14.454 , 188    ),   # d11
				(13.21  , 165.938),   # d21    
				(14.286 , 178.881),   # d22     
				(11.624 , 149.476),   # d31     
				(16.926 , 204.415),   # delta1  
				(11.136 , 173.164),   # gamma1  
				]

		self.px_mm = 6.9 # calcolato con matlab, inquadratura fissa
						 # 1 mm sono circa 7 pixel

		self.pickleNameDatiGeometrici = DATA_PATH+'/elab_video/dati_geometrici_whiskers.pickle'
		if not SovrascriviPickle:
			if os.path.isfile(self.pickleNameDatiGeometrici):
				# carico il file
				self.caricoFile()
				print 'il file '+self.pickleNameDatiGeometrici+' esiste'
		else:
			# qualche test prima
			tuttoOk = True
			if len(self.FILEs) is not len(self.NAMEs):
				tuttoOk = False
			if len(self.NAMEs) is not len(self.ROIs):
				tuttoOk = False
			if len(self.ROIs) is not len(self.Diameters):
				tuttoOk = False
			# creo il file 
			if tuttoOk:
				self.creoFile()
			else:
				print 'qualcosa non va bene nei dati'
		if Stampa:
			self.scatterPlot()

	def scatterPlot(self):
		# scatter con nomi di baffo
		plt.scatter(self.lunghezza,self.somma_angolo)
		plt.xlabel('length')
		plt.ylabel('|abs|')
		for l,sa,n in zip(self.lunghezza,self.somma_angolo,self.NAMEs):
			print n, l
			plt.annotate(n,(l,sa)) 
		plt.savefig(DATA_PATH+'/elab_video/featuresWhiskersScatter.pdf')

	def caricoFile(self):
		with open(self.pickleNameDatiGeometrici, 'rb') as f:
			data = pickle.load(f)	
		self.FILEs = data[0]
		self.NAMEs = data[1]
		self.ROIs  = data[2]
		self.px_mm = data[3]
		self.Diameters = data[4]
		self.lunghezza = data[5]
		self.somma_angolo = data[6]
		self.angle010 = data[7]
		self.angle0100 = data[8]

	def creoFile(self):
		self.lunghezza = []
		self.somma_angolo = [] 
		self.angle010 = []  		
		self.angle0100 = [] 		
		V = video('pippo',(0,0,0,0),0,False,False,False) # mi servono due metodi
		for i in xrange(0,len(self.FILEs)):
			l,somma_angolo,angle010,angle0100 = self.analizzoPrimoFrame(i,V)
			self.lunghezza.append(l)
			self.somma_angolo.append(somma_angolo)
			self.angle010.append(angle010)
			self.angle0100.append(angle0100)
			#print self.NAMEs[i],self.analizzoPrimoFrame(i,V) # debug
		with open(self.pickleNameDatiGeometrici, 'w') as f:
			pickle.dump([self.FILEs,self.NAMEs,self.ROIs,self.px_mm,self.Diameters,self.lunghezza,self.somma_angolo,self.angle010,self.angle0100], f)	

	def analizzoPrimoFrame(self,idx,V):
		def distanza2Punti(p1,p2): # clear what it is...
			x1,y1 = p1
			x2,y2 = p2
			x12 = np.power(x2-x1,2)
			y12 = np.power(y2-y1,2)
			return np.sqrt(x12+y12) 
		def angoloMedio(d,dy): # d is distance, dy is the difference between y coordinates of two points
			return np.arcsin(dy/d)*(180./np.pi) # in degree
		#
		f = self.FILEs[idx]		
		n = self.NAMEs[idx]		
		roi = self.ROIs[idx]		
		d = self.Diameters[idx]		
		px_mm = self.px_mm
		cap = cv2.VideoCapture(f)
		#	
		c = 0
		while(cap.isOpened()):
			c += 1
			ret, frame = cap.read()
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			if c == 10: #2: # prima un si vede na sega 
				break
		gray = cv2.threshold(gray,33,255,cv2.THRESH_BINARY)[1]#int(1.25*np.median(frame)),255,cv2.THRESH_BINARY)[1]
		gray = gray[roi[2]:roi[3],roi[0]:roi[1]]
		#plt.imshow(gray,aspect='auto', interpolation="nearest")
		X,Y = V.get_whisker(gray)
		Xb,Yb = V.norm_whisker(X,Y,100,3)
		X = []
		Y = []
		#print len(frame)
		#print len(frame[0])
		#print len(frame[0][0])
		idx_nan = []
		for k,x,y in zip(xrange(0,len(Xb)),Xb,Yb):
			if not np.isnan(x*y):
				frame[np.round(y)+roi[2]][np.round(x)+roi[0]][:] = 0
				X.append(Xb[k])
				Y.append(Yb[k])
		X = np.asarray(X)
		Y = np.asarray(Y)
		x,y,w,h = ( roi[0]		 ,roi[2],\
					roi[1]-roi[0],roi[3]-roi[2])
		cv2.rectangle(frame, (x,y), (x+w,y+h), 255, 2)
		if 1:
			name = DATA_PATH+'/elab_video/'+n+'.jpg'
			cv2.imwrite(name, frame)     # save frame as JPEG file
		#
		X,Y = (X/px_mm, Y/px_mm)
		l=0  # integrale lunghezza
		s1=0 # integrale angolo
		for i in xrange(1,X.__len__()):
			x, xp = (X[i],X[i-1])
			y, yp = (Y[i],Y[i-1])
			dwhisk = np.sqrt(np.power(x-xp,2)+np.power(y-yp,2))
			angle = np.arcsin((y-yp)/dwhisk)*dwhisk # e se lo pesassi con il delta baffo?
			l += dwhisk 
			s1 += np.abs(angle)
		angle010  = angoloMedio(distanza2Punti((X[90],Y[90]),(X[-1],Y[-1])), Y[-1]-Y[90])       
		angle0100 = angoloMedio(distanza2Punti((X[0] ,Y[0]) ,(X[-1],Y[-1])), Y[-1]-Y[0])  
		angle0 = np.arcsin((Y[-1]-Y[0])/l)*l # angolo medio... (se il baffo e` dritto ma montato non orizzontale)
		somma_angolo = s1-angle0
		cap.release()
		cv2.destroyAllWindows()
		return l,somma_angolo,angle010,angle0100
		
class creoSpettriBaffi(): # carico i dati per riplottare gli spettri
	def __init__(self): 
		a = confrontoBaffiDiversi('baffi_12May','diversiBaffi',False) # per le lunghezze dei baffi 
		info = stampo_lunghezza_whiskers()					

		ig1 = 1#3 # gruppo 1
		ig2 = 2#4 # gruppo 1
		ig3 = 8#10 # gruppo 3
		maxFrame = 4500
		Np = maxFrame/2. 		# numero di campioni frequenze positive
		bw = 2000.0 			# frame/sec - bandwidth
		df = (bw/2)/Np			# df 
		freq = [int(df*c) for c in xrange(0,801)]	
		# prendo i dati
		ba = sessione('d11','12May','_NONcolor_',DATA_PATH+'/ratto1/0_acciaio_no_rot/',(260, 780, 0, 205),33,True, False)
		bb = sessione('c22','12May','_NONcolor_',DATA_PATH+'/ratto1/0_acciaio_no_rot/',(260, 780, 0, 205),33,True, False)
		bc = sessione('b11','12May','_NONcolor_',DATA_PATH+'/ratto1/0_acciaio_no_rot/',(260, 780, 0, 205),33,True, False)
		for baffo in [ba,bb,bc]:
			baffo.calcoloTransferFunction(False)
		g1 = ba.TFM[:,SPECTRAL_RANGE]
		g2 = bb.TFM[:,SPECTRAL_RANGE]
		g3 = bc.TFM[:,SPECTRAL_RANGE]
		g1_to_plot = np.log10(g1)
		g2_to_plot = np.log10(g2)
		g3_to_plot = np.log10(g3)


		def getLine(g,h): 
			slope, intercept, r_value, p_value, std_err = stats.linregress(g,h)
			r2 = r_value**2
			xv = [a for a in np.arange(0,18,.1)] # area che voglio rappresentare nel plot
			yv = [a*slope+intercept for a in xv]
			if np.sign(intercept)>0:
				segno='+'
			else:
				segno=r'$-$'
			text = 'y = '+str(np.floor(slope*100)/100)+'x'+segno+str(np.abs(np.floor(intercept*100)/100))+'\n'+r' (R$^2$ = '+str(np.floor(r2*100)/100)+')'
			#text = 'y = '+str(slope)+'x'+segno+str(np.abs(intercept))+'\n'+r' (R$^2$ = '+str(r2)+')'
			return xv,yv,r_value**2, text

		def doFigura(a,wLog,f): 
			'''
			a1 = f.add_subplot(2,3,1)
			a2 = f.add_subplot(2,3,2)
			a3 = f.add_subplot(2,3,3)
			a4 = f.add_subplot(2,3,4)
			a5 = f.add_subplot(2,3,5)
			#a61 = plt.subplot(gs[8])
			#a62 = plt.subplot(gs[11])
			a6 = f.add_subplot(2,3,6)
			'''
			#f.subplots_adjust(wspace=1,hspace=0.6)
			gs = gridspec.GridSpec(2,3,width_ratios=[0.033,1,1],wspace=0.22,hspace=0.6)
			a1 = f.add_subplot(gs[0,1])
			a2 = f.add_subplot(gs[0,2])
			a3 = f.add_subplot(gs[1,1])
			def setcolorbar(acb,Orientation='horizontal'):
				cbar =  matplotlib.colorbar.ColorbarBase(acb,orientation=Orientation,cmap='RdBu_r')
				cbar.ax.set_yticklabels(['']+[str(l/10.) for l in xrange(-4,14,2)])
				cbar.ax.tick_params(labelsize=FONTSIZE) 
				acb.yaxis.set_ticks_position('left')
				acb.set_ylabel(r'Log$_{10}$(|H|)')
				acb.yaxis.set_label_coords(-6,0.5)
			a01 = f.add_subplot(gs[0,0])
			a11 = f.add_subplot(gs[1,0])
			setcolorbar(a01,'vertical')
			setcolorbar(a11,'vertical')
			# spettri
			cax1 = a1.imshow(g1_to_plot,aspect='auto',vmin=-0.4,vmax=1.2, interpolation="gaussian",cmap='RdBu_r')#'OrRd')	
			cax2 = a2.imshow(g2_to_plot,aspect='auto',vmin=-0.4,vmax=1.2, interpolation="gaussian",cmap='RdBu_r')#'OrRd')
			cax3 = a3.imshow(g3_to_plot,aspect='auto',vmin=-0.4,vmax=1.2, interpolation="gaussian",cmap='RdBu_r')#'OrRd')	
			#
			lunghezze = []
			for idx1,idx2 in zip([ig1,ig2,ig3],[7,11,3]):
				print a.ROOT[idx1], info.NAMEs[idx2]
				lunghezze.append(info.lunghezza[idx2])
			a1.set_title(r'whisker W$_1$ ('+str(int(lunghezze[0]))+' mm)',fontsize=FONTSIZE)#,fontweight='')
			a2.set_title(r'whisker W$_2$ ('+str(int(lunghezze[1]))+' mm)',fontsize=FONTSIZE)#,fontweight='')
			a3.set_title(r'whisker W$_3$ ('+str(int(lunghezze[2]))+' mm)',fontsize=FONTSIZE)#,fontweight='')
			a1.set_xlabel('Frequency [Hz]',fontsize=FONTSIZE)
			a2.set_xlabel('Frequency [Hz]',fontsize=FONTSIZE)
			a3.set_xlabel('Frequency [Hz]',fontsize=FONTSIZE)
			a1.set_ylabel(r'Base     $\longrightarrow$      Tip',fontsize = FONTSIZE)
			a3.set_ylabel(r'Base     $\longrightarrow$      Tip',fontsize = FONTSIZE)

			# scatter plot o density plot?
			g1r = np.reshape(g1,g1.__len__()*g1[0].__len__())
			g2r = np.reshape(g2,g1.__len__()*g1[0].__len__())
			g3r = np.reshape(g3,g1.__len__()*g1[0].__len__())
			idx = np.random.permutation(len(g1r))[0:2000] #20000 
			plotType = 'density'#'scatter' #
			if plotType is 'scatter':
				gs2 = gridspec.GridSpec(2,2,wspace=0.6)
				a4 = f.add_subplot(gs2[1,1],aspect='equal')
				a4.set_title(r'|H|$_1$ vs |H|$_2$',fontsize=FONTSIZE)										  #,fontweight='bold')
				a4.set_xlabel('|H|',fontsize=FONTSIZE)
				a4.set_ylabel('|H|',fontsize=FONTSIZE)
				# scatter e regressione 
				w12 = a4.scatter(g2r[idx],g1r[idx],s=6**2,facecolor='r',color='r',marker='x', alpha=.4, rasterized=True)
				x12,y12,r12,pp12 = getLine(g2r,g1r)
				a4.plot(x12,y12,color='#8B4C4B',linewidth=2)
				a4.text(12,9,pp12,fontsize=FONTSIZE*0.9)
				color_g3r = 'g'
				if color_g3r is 'g':
					color_lg3r = '#3D5F3A'
				if color_g3r is 'b':
					color_lg3r = '#336699'
				w13 = a4.scatter(g3r[idx],g1r[idx],s=6**2,facecolor=color_g3r,color=color_g3r, marker='o', alpha=.4, rasterized=True)
				x13,y13,r13,pp13 = getLine(g3r,g1r)
				a4.plot(x13,y13,color=color_lg3r,linewidth=2) # se blu #336699 se verde 
				a4.text(-.2,18,pp13,fontsize=FONTSIZE*0.9)
				a4.legend((w12,w13), (r'W$_1$ vs W$_2$',r'W$_1$ vs W$_3$'), scatterpoints=1,markerscale=2, loc=4,prop={'size':FONTSIZE*0.9},fontsize=FONTSIZE)
				# 
				a4.set_xlim([min(g1r)-.7,max(g1r)])
				a4.set_ylim([min(g1r)-.7,max(g1r)])

				referencePanel(a01,'A',-5	, 1.1)
				referencePanel(a2 ,'B',-0.03 , 1.1)
				referencePanel(a11,'C',-5	, 1.1)
				referencePanel(a4 ,'D',-.5	, 1.1)
				customaxis(a1,size=FONTSIZE,pad=-3)
				customaxis(a2,size=FONTSIZE,pad=-3)
				customaxis(a3,size=FONTSIZE,pad=-3)
				customaxis(a4,size=FONTSIZE,pad=-3)
				for a in [a1,a2,a3,a4]:
					a.tick_params(labelsize=FONTSIZE) 
				for a in [a1,a2,a3]:
					a.set_yticks([])
					a.set_xticks(xrange(0,400,100))
				return a1,a2,a3,a4

			if plotType is 'density':
				props = dict(facecolor='white', edgecolor='white', alpha=0.6)
				gs2 = gridspec.GridSpec(2,5,wspace=0.1,hspace=0)
				a4 = f.add_subplot(gs2[1,3],aspect='equal')
				a5 = f.add_subplot(gs2[1,4],aspect='equal')
				x12,y12,r12,pp12 = getLine(g2r,g1r)
				a4.plot(x12,y12,color='k',linewidth=2, alpha=0.5)  #'#8B4C4B'
				a4.text(4.5,1,pp12,fontsize=FONTSIZE*0.7,bbox=props)
				xy = np.vstack([g2r[idx],g1r[idx]])
				z = stats.gaussian_kde(xy)(xy)
				w12 = a4.scatter(g2r[idx],g1r[idx], c=z, s=2**2, edgecolor='', cmap='RdBu_r')
				a4.set_title(r'W$_1$ vs W$_2$')
				x13,y13,r13,pp13 = getLine(g3r,g1r)
				a5.plot(x13,y13,color='k',linewidth=2, alpha=0.5)  #'#8B4C4B'
				a5.text(4.5,1,pp13,fontsize=FONTSIZE*0.7,bbox=props)
				xy = np.vstack([g3r[idx],g1r[idx]])
				z = stats.gaussian_kde(xy)(xy)
				w13 = a5.scatter(g3r[idx],g1r[idx], c=z, s=2**2, edgecolor='', cmap='RdBu_r')
				a5.set_yticklabels([])
				a5.set_title(r'W$_1$ vs W$_3$')
				for a in [a4,a5]:
					a.set_xlim([0,11])
					a.set_ylim([0,11])
					a.set_yticks(range(0,11,2))
					a.set_xticks(range(0,11,2))
					a.set_xlabel('|H|',fontsize=FONTSIZE)
					posA = a.get_position()
					a.set_position([posA.x0+0.01, posA.y0-.08, posA.width+0, posA.height+0])
				a4.set_ylabel('|H|',fontsize=FONTSIZE)
				wl1 = a4.scatter(-1,-1,c='b',edgecolor='b')
				wl2 = a5.scatter(-1,-1,c='r',edgecolor='r')
				leg_a45 = a4.legend((wl1,wl2),('One Point','Highest density'), ncol=2, loc='upper center',bbox_to_anchor=(1.1,1.5),handlelength=0.5,scatterpoints=1,frameon=False,fontsize = FONTSIZE) #,facecolor='white', edgecolor='white'))
				#a4 = plt.gca().add_artist(leg_a45)
				'''
				setcolorbar(a45)
				a45.set_xticklabels([])
				a45.set_xlabel(r'Single Point     $\longrightarrow$      Highest density',fontsize = FONTSIZE)
				pos45 = a45.get_position()
				a45.set_position([pos45.x0+0, pos45.y0-.04, pos45.width+0, pos45.height+0])
				'''

				referencePanel(a1 ,'A', -0.45 , 1.2)
				referencePanel(a1 ,'B',  1.1 , 1.2)
				referencePanel(a3 ,'C', -0.45 , 1.2)
				referencePanel(a3 ,'D',  1.1 , 1.2)
				padVal = -5.5
				customaxis(a1,size=FONTSIZE,pad=-padVal)
				customaxis(a2,size=FONTSIZE,pad=-padVal)
				customaxis(a3,size=FONTSIZE,pad=-padVal)
				customaxis(a4,size=FONTSIZE,pad=-padVal)
				customaxis(a5,size=FONTSIZE,pad=-padVal)
				return a1,a2,a3,(a4,a5)
				
		# faccio figura
		f1 = plt.figure(figsize=(FIGSIZEx,FIGSIZEy))
		a11,a12,a13,a14 = doFigura(a,True, f1)
		a11.set_yticks([])
		a12.set_yticks([])
		a13.set_yticks([])
		a11.set_xticks(xrange(0,400,100))
		a12.set_xticks(xrange(0,400,100))
		a13.set_xticks(xrange(0,400,100))
		f1.savefig(DATA_PATH+'/elab_video/DiffTransferFunction.pdf',bbox_inches='tight')


		# per mathew
		if 0:
			for rip in range(0,10):
				f = plt.figure()
				a4 = f.add_subplot(1,1,1,aspect='equal')
				g1r = np.reshape(g1,g1.__len__()*g1[0].__len__())
				g2r = np.reshape(g2,g1.__len__()*g1[0].__len__())
				g3r = np.reshape(g3,g1.__len__()*g1[0].__len__())
				idx = np.random.permutation(len(g1r))[0:500] #20000 
				w12 = a4.scatter(g2r[idx],g1r[idx],s=6**2,facecolor='r',color='r',marker='x', alpha=.4, rasterized=True)
				x12,y12,r12,pp12 = getLine(g2r[idx],g1r[idx])
				a4.plot(x12,y12,color='#8B4C4B',linewidth=2)
				a4.text(12,9,pp12,fontsize=FONTSIZE*0.9)
				color_g3r = 'g'
				if color_g3r is 'g':
					color_lg3r = '#3D5F3A'
				if color_g3r is 'b':
					color_lg3r = '#336699'
				w13 = a4.scatter(g3r[idx],g1r[idx],s=6**2,facecolor=color_g3r,color=color_g3r, marker='o', alpha=.4, rasterized=True)
				x13,y13,r13,pp13 = getLine(g3r[idx],g1r[idx])
				a4.plot(x13,y13,color=color_lg3r,linewidth=2) # se blu #336699 se verde 
				a4.text(-.2,18,pp13,fontsize=FONTSIZE*0.9)
				a4.legend((w12,w13), (r'W$_1$ vs W$_2$',r'W$_1$ vs W$_3$'), scatterpoints=1,markerscale=2, loc=4,prop={'size':FONTSIZE*0.9},fontsize=FONTSIZE)
				a4.set_xlim([min(g1r)-.7,max(g1r)])
				a4.set_ylim([min(g1r)-.7,max(g1r)])
				f.savefig(DATA_PATH+'/elab_video/comparison_scatter_'+str(rip)+'.pdf')

class mergeComparisonsResults():
	def __init__(self):

		typeComparison = 'transferFunction'  # 'spettri' # 

		# carico dati
		a = confrontoBaffiDiversi('baffi_12May','diversiBaffi',False)
		a.info = stampo_lunghezza_whiskers()					
		a.compareWhiskers(typeComparison) 
		b = confrontoBaffiDiversi('baffi_12May','diversiTempi',False)    
		b.compareWhiskers(typeComparison) 
		FS = FONTSIZE

		#print cbd.info.lunghezza
		lung = []
		names = [] 
		for i in a.ROOT:
			for j,l in zip(a.info.NAMEs,a.info.lunghezza):
				if i.find(j) is not -1:
					names.append(j)
					lung.append(l)
					break
		print a.ROOT
		print names
		print lung
		#
		# axes arrangements
		f = plt.figure(figsize=((3/2)*FIGSIZEx,FIGSIZEy))
		gs  = gridspec.GridSpec(2,4,width_ratios=[0.053,1,1,1],hspace=0.5, wspace=0.6)
		UnDyed = f.add_subplot(gs[0,1])
		ColorC = f.add_subplot(gs[0,2])
		Dyed = f.add_subplot(gs[0,3])
		TimeC = f.add_subplot(gs[1,2])
		WhiskerGroup = f.add_subplot(gs[1,1])
		gs2  = gridspec.GridSpec(5,3,width_ratios=[1,1,0.6],hspace=0.55)
		ColorD = plt.subplot(gs2[3,2])
		TimeSD = plt.subplot(gs2[4,2],sharey=ColorD)

		def setcolorbar(acb):
			cbar =  matplotlib.colorbar.ColorbarBase(acb,orientation='vertical')
			cbar.ax.tick_params(labelsize=FONTSIZE) 
			acb.yaxis.set_ticks_position('left')
			acb.set_ylabel(r'Determination coeff. R$^2$')
			acb.yaxis.set_label_coords(-6,0.5)
		a01 = f.add_subplot(gs[0,0])
		a11 = f.add_subplot(gs[1,0])
		setcolorbar(a01)
		setcolorbar(a11)

		# plot stuff
		# self.sizeWhiskerGroups(a,WhiskerGroup,lung) # <--- sostituisco questo scatter con le matrici dei baffi simulati
		CORR2SIM = funTemporaneoConfrontoBaffiSimulatiTraLoro()
		lung = [int(l) for l in lung]
		self.colorComparison(a,WhiskerGroup,lung,CORR2SIM       ,'  Sim \n  Sim'       , FS)
		self.colorComparison(a,ColorC,lung,a.CORR2       		,'  Undyed \n  Dyed'   , FS)
		self.colorComparison(a,UnDyed,lung,a.CORR2_undyed		,'  Undyed \n  Undyed' , FS)
		self.colorComparison(a,Dyed  ,lung,a.CORR2_dyed  		,'  Dyed \n  Dyed'     , FS)


		self.diagColComp(a,ColorD,lung,a.CORR2                                         , FS)
		self.supradiagTimeComp(b,TimeSD                                                , FS)
		cax = self.timeComparison(b,TimeC                       ,'  Time \n  Time'     , FS)

		for ax in [UnDyed,Dyed,ColorC,WhiskerGroup]: 
			customaxis(ax,size=FS*0.9,pad=-2)
		customaxis(TimeC,size=FS*0.9,pad=0)
		for ax in [ColorD,TimeSD]: 
			customaxis(ax,size=FS*0.9,pad=-2)
			
		v1 = a.CORR2_undyed.reshape(-1)
		v2 = a.CORR2.reshape(-1)
		v3 = a.CORR2_dyed.reshape(-1)
		vs = CORR2SIM.reshape(-1)
		print 'corr2 sim vs undyed',np.power(np.corrcoef(v1,vs)[0,1],2)
		print 'corr2 sim vs mixed',np.power(np.corrcoef(v2,vs)[0,1],2)
		print 'corr2 sim vs dyed',np.power(np.corrcoef(v3,vs)[0,1],2)
		
		# stampo
		referencePanel(UnDyed      ,'A',-1, 1.15)
		referencePanel(ColorC      ,'B',-0.35, 1.15)
		referencePanel(Dyed        ,'C',-0.35, 1.15)
		referencePanel(WhiskerGroup,'D',-1, 1.15)
		referencePanel(TimeC       ,'E',-0.35, 1.15)
		referencePanel(Dyed        ,'F',-0.35, -.51)
		f.savefig(DATA_PATH+'/elab_video/mergeComparisonsResults_'+typeComparison+'.pdf',bbox_inches='tight')

	def getSuperDiagThs(self,CORR2,k):
		media = 0
		for i in range(1,len(CORR2)-k): 
			print i
			media += CORR2[i-k,i-k]+CORR2[i+k,i+k]
		return media / (2*len(CORR2))		

	def diagColComp(self,cbd,a51,lung,CORR2,FS):
		lengths = [int(l) for l in lung]
		#
		d_c2 = []
		for i in xrange(0,CORR2.__len__()):
			d_c2.append(CORR2[i][i])
		a51.plot(d_c2,'k.',markersize=10)
		#a51.plot(d_c2,'k')
		a51.set_xticks(np.arange(0,len(lung),1))
		#a51.set_xlabel('Length [mm]',fontsize=FS)
		a51.set_yticks(np.arange(0,1.2,0.2))
		a51.axis([-0.2, len(cbd.ROOT)-0.8, 0.1, 1])
		#a51.set_xticklabels([])
		#a51.text(2,0.4,'Dye effect', color='k',fontsize=FS*0.8)
		a51.set_ylabel(r'R$^2$ (dye)', color='k',fontsize=FS) 
		a51.tick_params(labelsize=FS) 
		a51.set_xticklabels(lengths,rotation=90) #cbd.ROOT[0:14],rotation=90)
		a51.set_xlim([-.5, len(lung)-.5])
		#a51.set_ylim([0, 1.1])
		#a51.axes.get_xaxis().set_visible(False)
		# vediamo quanto alti sono i valori sulla diagonale rispetto agli altri
		Colors = cm.gray(np.linspace(0, 1, CORR2.__len__()-1))
		vals = []
		for i in xrange(1,len(Colors)):
			val = self.getSuperDiagThs(CORR2,i)
			a51.plot([-.5,len(lung)-.5],[val,val],color=Colors[i])
			a51.plot([-.5,len(lung)-.5],[val,val],color=Colors[i])
			vals.append(val)
		print vals
		a51.annotate('', (5, min(vals)),(5, max(vals)),ha="right", va="center",size=10,arrowprops=dict(arrowstyle="->",connectionstyle="arc3",fc="k", ec="k",),)
		a51.text(6,0.35,r'$\mu_{i \searrow}$',rotation=0,fontsize=1.3*FS,bbox=dict(boxstyle='round', fc='w', ec='w', alpha=0.7))


	def supradiagTimeComp(self,cbd,a51,FS):
		ROOT  	= [re.sub('[$]','',cbd.ROOT[i]) for i in xrange(0,cbd.ROOT.__len__()) if cbd.group3[i] == 0] # uso le regular expression per togliere i $ che mi servono per l'interpreter latex per fare il corsivo 
		d_c2 = []
		for i in xrange(0,12):
			d_c2.append(cbd.CORR2[i][i+1])
		a51.plot(d_c2,'k.',markersize=10)
		#a51.plot(d_c2,'k')
		a51.axis([-0.2, len(cbd.CORR2)-0.8, 0.1, 1])
		a51.set_yticks(np.arange(0,1.2,0.2))
		a51.set_xticks(xrange(0,len(cbd.CORR2)-1))
		#a51.text(2,0.4,'Time effect', color='k',fontsize=FS*0.8)
		a51.set_ylabel(r'R$^2$ (time)', color='k',fontsize=FS) 
		for tl in a51.get_yticklabels():
			tl.set_color('k')
		a51.tick_params(labelsize=FS) 
		#a51.set_xlabel('Time',fontsize=FS) # C3 o 37.99mm
		#a51.set_xticklabels(ROOT[1:])
		a51.set_xticklabels(ROOT[1:13],rotation=90)
		a51.set_xlim([-.5, len(d_c2)-.5])
		a51.set_ylim([0, 1.1])
		#a51.axes.get_xaxis().set_visible(False)



	def colorComparison(self,cbd,a2,lung,CORR2,text,FS):
		# faccio il plot
		cax2 = a2.imshow(np.flipud(CORR2),aspect='equal', interpolation="nearest",clim=(0,1))
		a2.set_xticks(np.arange(len(cbd.ROOT)))
		a2.set_xticklabels(lung,rotation=90)#cbd.ROOT,rotation=90)
		a2.set_yticks(np.arange(len(cbd.ROOT)))
		a2.set_yticklabels(reversed(lung))#cbd.ROOT)
		a2.set_xlabel('Length [mm]',fontsize=FS)
		a2.set_ylabel('Length [mm]',fontsize=FS)
		a2.text(-.18, -.18, text,horizontalalignment='center',verticalalignment='center',rotation=45,transform=a2.transAxes,fontsize=FS)
		a2.annotate('', xy=(-0.3, -0.3), xycoords='axes fraction', xytext=(0, 0), arrowprops=dict(arrowstyle="-", color='k'))
		a2.tick_params(labelsize=FS) 
		#a2.set_xlim([0,len(lung)])
		#a2.set_ylim([0,len(lung)])
		return cax2

	def timeComparison(self,cbd,a1,text,FS):
		ROOT  	= [re.sub('[$]','',cbd.ROOT[i]) for i in xrange(0,cbd.ROOT.__len__()) if cbd.group3[i] == 0] # uso le regular expression per togliere i $ che mi servono per l'interpreter latex per fare il corsivo 
		CORR2 	= cbd.CORR2[0:ROOT.__len__(),0:ROOT.__len__()]
		cax1 = a1.imshow(np.flipud(CORR2),aspect='equal', interpolation="nearest",clim=(0,1))
		a1.set_xticks(np.arange(len(ROOT)))
		a1.set_xticklabels(ROOT,rotation=90)
		a1.set_yticks(np.arange(len(ROOT)))
		a1.set_yticklabels(reversed(ROOT))
		a1.text(-.18, -.18, text,horizontalalignment='center',verticalalignment='center',rotation=45,transform=a1.transAxes,fontsize=FS)
		a1.annotate('', xy=(-0.3, -0.3), xycoords='axes fraction', xytext=(0, 0), arrowprops=dict(arrowstyle="-", color='k'))
		#a1.set_xlabel('Time',fontsize=FS) # C3 o 37.99mm
		#a1.set_ylabel('Time',fontsize=FS) # C3 o 37.99mm
		a1.tick_params(labelsize=FS) 
		return cax1


	def sizeWhiskerGroups(self,cbd,a1,lung):
		#
		dist  = []
		corr2 = []
		corr2c = []
		corr2nc = []
		for i in xrange(0,cbd.CORR2.__len__()):
			for j in xrange(0,cbd.CORR2.__len__()):
				dist.append(np.abs(lung[i]-lung[j]))
				corr2.append(cbd.CORR2[i,j])
				corr2c.append(cbd.CORR2_dyed[i,j])
				corr2nc.append(cbd.CORR2_undyed[i,j])
		a1.scatter(dist, corr2, s=6**2, color='0.3', alpha=0.5)
		#a1.scatter(dist, corr2, s=3**2, color='r', alpha=0.5)   # <--- vengono identici
		#a1.scatter(dist, corr2, s=2**2, color='g', alpha=0.5)   # <--- vengono identici
		a1.set_xlabel('Length Difference',fontsize=14)
		a1.set_ylabel('Similarity',fontsize=14)
		a1.set_ylim([-0.05, 1.05])
		a1.set_xlim([-2, 42])
		a1.tick_params(labelsize=10) 
		'''
		for spine in ('top','bottom','left','right'):
			a1.spines[spine].set_visible(False)
		'''

class dyeEnhanceAndBehavioralEffect(): # confronto le performance di 4 ratti, pre/post-anestesia, due di controllo due con colorazione nel post-anestesia
	def __init__(self):
		self.initData()
		self.trendData(True)

	def initData(self):
		# colore: ratto 1 e 3
		self.ratto_1_pre  = [80,87.80,80.60,83.60,85.60,82,84.60,77.90,77.60,80,80,84,86,84.70,86.60,83,85.50,85.90,87.90]
		self.ratto_1_post = [82.70,83.80,84.50,81.80,80,84.60,80.50,81,88,84,84,86.40,86,82.70,80.50,90,80,85.50,90,78,80,79.80,83.90,87] 
		self.ratto_3_pre  = [79,83.70,77.30,77.60,74.70,80.60,81.40,78,78.30,82,80.50,81,81,82,80.50,81.70,85.90,80.40,82.80]	
		self.ratto_3_post = [80,83.90,84.70,80.50,80.70,83,79.50,87,84,80.70,81.60,76,81.30,81.30,83.80,85.50,78.80,83.70,85,85,82.60,81.80,80.80,82.30]
		# controllo: ratto 2 e 4
		self.ratto_2_pre  = [83,83,77.80,81,85,81.70,82.40,85.30,80.80,80.70,82,84,83.80,79,81.40,81.40,85.70,83,82]
		self.ratto_2_post = [82,79,78.50,83,81.50,83,87.60,84,81.50,81,83.70,81,81,88,88.30,86,82.80,81.30,81,77.90,76.40,85.50,80,83.80]
		self.ratto_4_pre  = [80.50,78.40,81.90,78.40,84.90,79.40,77.50,75.30,83,75.60,79.30,84,79,79.50,76.80,76.50,80.70,83,81.70]
		self.ratto_4_post = [78.70,79,81.30,83.80,81,83.00,84,77,81,82,79.40,82.80,80.70,80,79.80,83.30,76,82,80.50,82,81,81.40,81.70,82.60]

	def trendData(self,salva=False):
		colors = ['b','c','m','g'] #cm.rainbow(np.linspace(0, 1, 4)) # 4 gruppi 
		ALPHA= 0.5
		FS = FONTSIZE

		def panel_D(a):
			# disegno i trend
			area = np.pi*(1.5**2)
			Rats_name = ['colored rat','control rat','colored rat','control rat']
			Rats_pre  = [self.ratto_1_pre, self.ratto_2_pre, self.ratto_3_pre, self.ratto_4_pre]
			Rats_post = [self.ratto_1_post, self.ratto_2_post, self.ratto_3_post, self.ratto_4_post]
			xx = 0
			for rat_pre,rat_post,n,c in zip(Rats_pre,Rats_post,Rats_name,colors): 
				a.scatter(np.linspace(0, 9.5, rat_pre.__len__()), rat_pre, area,color=c,alpha=0.8)
				a.scatter(np.linspace(10.5, 20, rat_post.__len__()),rat_post,area,color=c,alpha=0.5)
				a.plot(np.linspace(0, 9.5, rat_pre.__len__()), rat_pre, color=c, linewidth=1.2,alpha=0.5)
				a.plot(np.linspace(10.5, 20, rat_post.__len__()),rat_post, color=c, linewidth=1.2,alpha=0.5)
				a.plot(np.linspace(9.5, 10.5, 2), [rat_pre[-1],rat_post[0]], color=c, linestyle='--',alpha=0.5)
				xx += 0.25
			a.get_xaxis().tick_top()
			a.get_yaxis().tick_left()
			a.set_ylabel('Correct trials [%]', fontsize=FS)
			a.set_xlabel('Sessions',fontsize=FS)
			a.set_yticks([75,80,85,90]) # niente
			a.set_xticks([]) # niente
			a.set_xlim([-.5, 20.5])
			a.set_ylim([74, 91])
			a.tick_params(labelsize=FS) 
			# patches
			p1 = a.add_patch(patches.Rectangle((-.5, 74),10.25,18))
			p1.set_alpha(0.2)
			p1.set_color('gray')
			p2 = a.add_patch(patches.Rectangle((10.25,74),11.25,18))
			p2.set_alpha(0.2)
			p2.set_color('gray')
			# annotations
			a.annotate('before', ( 5, 89),( 4, 93.5),ha="right", va="center",size=12,arrowprops=dict(arrowstyle='wedge',fc="w", ec="k",),)
			a.annotate('after' , (15, 89),(14, 93.5),ha="right", va="center",size=12,arrowprops=dict(arrowstyle='wedge',fc="w", ec="k",),)

		def panel_E(a):
			a.set_xticks([]) 
			def permutoPerf(pre,post):
				dp = []
				for r in itertools.product(pre,post):	
					dp.append(r[1]-r[0])
				return dp
			dr1 = permutoPerf(self.ratto_1_pre,self.ratto_1_post)
			dr2 = permutoPerf(self.ratto_2_pre,self.ratto_2_post)
			dr3 = permutoPerf(self.ratto_3_pre,self.ratto_3_post)
			dr4 = permutoPerf(self.ratto_4_pre,self.ratto_4_post)
			dr = [dr2,dr4,dr1,dr3] 
			# calcolo intervallo di confidenza
			def bootstrap(data, num_samples, statistic, alpha):
				"""Returns bootstrap estimate of 100.0*(1-alpha) CI for statistic."""
				n = len(data)
				idx = np.random.randint(0, n, (num_samples, n))
				print n, '\n----\n----\n', idx
				samples = [data[i] for i in idx] 
				stat = np.sort(statistic(samples, 1))
				return (stat[int((alpha/2.0)*num_samples)],
						stat[int((1-alpha/2.0)*num_samples)])
			ci = []
			ci.append(bootstrap(np.asarray(dr2), 1000, np.mean, 0.05))
			ci.append(bootstrap(np.asarray(dr4), 1000, np.mean, 0.05))
			ci.append(bootstrap(np.asarray(dr1), 1000, np.mean, 0.05))
			ci.append(bootstrap(np.asarray(dr3), 1000, np.mean, 0.05))
			print ci # due ratti hanno migliorato le performance in modo significativo...
			# faccio il violinplot
			violin_parts = a.violinplot(dr,showextrema=False,showmeans=False,showmedians=True)
			violin_parts['cmedians'].set_color('k')
			for pc,c in zip(violin_parts['bodies'],colors):
				pc.set_color(c)
				pc.set_alpha(ALPHA)
			a.set_ylabel('Difference [%]',fontsize=FS)
			a.set_xlabel('Rats',fontsize=FS)
			a.set_yticks(np.arange(-10,11,5))
			a.tick_params(labelsize=FS) 
			a.set_ylim([-10, 11])
			a.set_xlim([.6, 4.4])
			# patches
			p1 = a.add_patch(patches.Rectangle((.6, -10.2),1.8,23))
			p1.set_alpha(0.2)
			p1.set_color('gray')
			p2 = a.add_patch(patches.Rectangle((2.6, -10.2),1.8,23))
			p2.set_alpha(0.2)
			p2.set_color('red')
			# annotations
			a.annotate('sham', (1.5, 10),(1, 15),ha="right", va="center",size=12,arrowprops=dict(arrowstyle='wedge',fc="w", ec="k",),)
			a.annotate('dyed', (3.5, 10),(3, 15),ha="right", va="center",size=12,arrowprops=dict(arrowstyle='wedge',fc="w", ec="k",),)

		# luce bianca - luce blu filtro rosso - luce blu  filtro passa lungo 
		# 				effetto sulla behavioral performance
		directory = DATA_PATH+'/elab_video/'
		self.luceBianca 		= directory+'IMG_0239.JPG'
		self.luceBluFiltroRosso = directory+'IMG_0238.JPG'
		self.luceBluFiltroPLung = directory+'IMG_0236.JPG'
		LB=mpimg.imread(self.luceBianca)
		FR=mpimg.imread(self.luceBluFiltroRosso)
		FPL=mpimg.imread(self.luceBluFiltroPLung)
		#textSize, labelSize = fontSizeOnFigures(True)
		fW = plt.figure(figsize=((3/2)*FIGSIZEx,FIGSIZEy))
		fW.subplots_adjust(wspace=0.15,hspace=0.5)
		aw1 = fW.add_subplot(2,3,1)
		aw2 = fW.add_subplot(2,3,2)
		aw3 = fW.add_subplot(2,3,3)
		aw1.imshow(LB)
		referencePanel(aw1,'A',-0.03, 1.15)
		aw2.imshow(FPL)
		referencePanel(aw2,'B',-0.03, 1.15)
		aw3.imshow(FR)
		referencePanel(aw3,'C',-0.03, 1.15)
		def unvisibleAxes(ax):
			ax.axes.get_xaxis().set_visible(False)
			ax.axes.get_yaxis().set_visible(False)
		[unvisibleAxes(ax) for ax in [aw1,aw2,aw3]] 
		gs = gridspec.GridSpec(2,4,width_ratios=[0,3,0,1],wspace=0.4)
		aw41 = fW.add_subplot(gs[1,1])
		aw42 = fW.add_subplot(gs[1,3]) #,sharey=aw41)
		panel_D(aw41)
		customaxis(aw41,size=FS,pad=0)
		referencePanel(aw1,'D',-0.03, -0.4)
		panel_E(aw42)
		customaxis(aw42,size=FS,pad=0)
		referencePanel(aw1,'E',2.2785, -0.4)
		for a in [aw41,aw42]:
			for spine in ['right','top']: #'left','bottom'
				a.spines[spine].set_visible(False)

		#	
		if salva:
			fW.savefig(DATA_PATH+'/elab_video/dyeEnhanceAndBehavioralEffect.pdf',dpi=300,bbox_inches='tight')
		else:
			plt.show()

class confrontoBaffiDiversi: # elaboro le diverse sessioni fra loro
	def __init__(self,name,testType,doCompare):
		self.name					= name
		self.testType 				= testType
		self.completeName 			= self.name+'_'+self.testType
		self.pickleEndTracking		= '.pickle'
		self.pickleEndSpectrum		= '_spectrum.pickle'
		self.pickleEndTransFun		= '_transferFunction.pickle'
		self.pickleEndTransFunTip	= '_transferFunctionTip.txt' # per Ale per fare l'ottimizzazione del modello in COMSOL
		self.integrale_lunghezza = []
		self.integrale_absAngolo = []
		self.angle010 = [] 
		self.angle0100 = [] 
		self.deflessione = []

		#if os.path.isfile(self.pickleName):
		#	print 'il file '+self.pickleName+' esiste'
		#	self.loadWhiskers()

		# modifiche al volo di variabili che non devo precalcolare
		if self.testType == 'diversiBaffi':
			'''
			# ordine usato finora
			self.listaWhisker = [\
								#DATA_PATH+'/elab_video/a11_12May_',
								#DATA_PATH+'/elab_video/c11_12May_',
								DATA_PATH+'/elab_video/c12_12May_', # 1
								DATA_PATH+'/elab_video/c22_12May_', # 2
								DATA_PATH+'/elab_video/d11_12May_', # 3
								DATA_PATH+'/elab_video/c21_12May_', # 4
								DATA_PATH+'/elab_video/c31_12May_', # 5
								DATA_PATH+'/elab_video/d21_12May_', # 6
								DATA_PATH+'/elab_video/d22_12May_', # 7
								DATA_PATH+'/elab_video/a31_12May_', # 8
								DATA_PATH+'/elab_video/b11_12May_', # 9
								DATA_PATH+'/elab_video/c41_12May_', # 10
								# 			in d31 e` comparsa una imperfezione dopo la colorazione
								#DATA_PATH+'/elab_video/d31_12May_',
								#DATA_PATH+'/elab_video/a41_12May_',
								#DATA_PATH+'/elab_video/c51_12May_',
								]
			'''
			# ordino per ordine crescente di dimensione
			self.listaWhisker = [\
								DATA_PATH+'/elab_video/a31_12May_', # 8
								DATA_PATH+'/elab_video/b11_12May_', # 9
								DATA_PATH+'/elab_video/c41_12May_', # 10
								DATA_PATH+'/elab_video/c21_12May_', # 4
								DATA_PATH+'/elab_video/c31_12May_', # 5
								DATA_PATH+'/elab_video/d22_12May_', # 7
								DATA_PATH+'/elab_video/d21_12May_', # 6
								DATA_PATH+'/elab_video/c12_12May_', # 1
								DATA_PATH+'/elab_video/c22_12May_', # 2
								DATA_PATH+'/elab_video/d11_12May_', # 3
								]
			# creo le due liste di cose da confrontare
			self.listaWhisker1 = []
			self.listaWhisker2 = []
			for lW in self.listaWhisker:
				self.listaWhisker1.append(lW+'_NONcolor_')
			for lW in self.listaWhisker:
				self.listaWhisker2.append(lW+'_color_')
			
			# ora non stampo piu` i nomi dei whisker nelle label...
			#self.group1 = ['$A1_L$','$C1_L$','$C1_R$','$C2_R$','$D1_L$']
			#self.group2 = ['$C2_L$','$C3_L$','$D2_L$','$D2_R$']
			#self.group3 = ['$A3_L$','$B1_L$','$C4_L$','$D3_L$']
			#self.group4 = ['$A4_L$','$C5_L$']
			#self.ROOT = self.group1[2:] + self.group2 + self.group3[:-1] #+ self.group4
			self.ROOT = []
			bias = len(DATA_PATH+'/elab_video/')
			for i in self.listaWhisker:
				self.ROOT.append(i[bias:bias+2]+'_'+i[bias+2]) # lo costruisco con il '_' nel mezzo
			
		elif self.testType == 'diversiTempi': 
			
			self.group1 = ['$A1_L$','$C1_L$','$C2_R$','$D1_L$'] # ne manca uno, perche`???`
			self.group2 = ['$C2_L$','$C3_L$','$D2_L$','$D2_R$']
			self.group3 = ['$A3_L$','$B1_L$','$C4_L$','$D3_L$']
			self.group4 = ['$A4_L$','$C5_L$']
			self.ROOT =	['$cut$','$+1h$','$+2h$','$+3h$','$+4h$','$+5h$','$+6h$','$+7h$','$+1d$','$dye$','$+2M$','$+3M$','$pol$']+self.group1 + self.group2 + self.group3 + self.group4
			'''
			self.ROOT =	['@cut','+1h','+2h','+3h','+4h','+5h','+6h','+7h','+1d','@color','+2M','+3M','@polish',\
						 'a11','c11','c22','d11','c21','c31','d21','d22','a31','b11','c41','d31','a41','c51']
			'''
			self.listaWhisker1 = [	DATA_PATH+'/elab_video/c31_11May_hour1__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour2__NONcolor_',\
								  	DATA_PATH+'/elab_video/c31_11May_hour3__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour4__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour5__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour6__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour7__NONcolor_',
									DATA_PATH+'/elab_video/c31_11May_hour8__NONcolor_',\
									\
									DATA_PATH+'/elab_video/c31_12May__NONcolor_',\
									DATA_PATH+'/elab_video/c31_12May__color_',\
									DATA_PATH+'/elab_video/c31_6Jul__color_',\
									DATA_PATH+'/elab_video/c31_2Ago_senzaSmaltoTrasparente__color_',\
									DATA_PATH+'/elab_video/c31_2Ago_conSmaltoTrasparente__color_',\
									\
									DATA_PATH+'/elab_video/a11_12May__color_',\
									DATA_PATH+'/elab_video/c11_12May__color_',\
									DATA_PATH+'/elab_video/c22_12May__color_',\
									DATA_PATH+'/elab_video/d11_12May__color_',\
									DATA_PATH+'/elab_video/c21_12May__color_',\
									DATA_PATH+'/elab_video/c31_12May__color_',\
									DATA_PATH+'/elab_video/d21_12May__color_',\
									DATA_PATH+'/elab_video/d22_12May__color_',\
									DATA_PATH+'/elab_video/a31_12May__color_',\
									DATA_PATH+'/elab_video/b11_12May__color_',\
									DATA_PATH+'/elab_video/c41_12May__color_',\
									DATA_PATH+'/elab_video/d31_12May__color_',\
									DATA_PATH+'/elab_video/a41_12May__color_',\
									DATA_PATH+'/elab_video/c51_12May__color_']
			self.listaWhisker2 = [	DATA_PATH+'/elab_video/c31_11May_hour1__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour2__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour3__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour4__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour5__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour6__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour7__NONcolor_',\
									DATA_PATH+'/elab_video/c31_11May_hour8__NONcolor_',\
									\
									DATA_PATH+'/elab_video/c31_12May__NONcolor_',\
									DATA_PATH+'/elab_video/c31_12May__color_',\
									DATA_PATH+'/elab_video/c31_6Jul__color_',\
									DATA_PATH+'/elab_video/c31_2Ago_senzaSmaltoTrasparente__color_',\
									DATA_PATH+'/elab_video/c31_2Ago_conSmaltoTrasparente__color_',\
									\
									DATA_PATH+'/elab_video/a11_6Jul__color_',\
									DATA_PATH+'/elab_video/c11_6Jul__color_',\
									DATA_PATH+'/elab_video/c22_6Jul__color_',\
									DATA_PATH+'/elab_video/d11_6Jul__color_',\
									DATA_PATH+'/elab_video/c21_6Jul__color_',\
									DATA_PATH+'/elab_video/c31_6Jul__color_',\
									DATA_PATH+'/elab_video/d21_6Jul__color_',\
									DATA_PATH+'/elab_video/d22_6Jul__color_',\
									DATA_PATH+'/elab_video/a31_6Jul__color_',\
									DATA_PATH+'/elab_video/b11_6Jul__color_',\
									DATA_PATH+'/elab_video/c41_6Jul__color_',\
									DATA_PATH+'/elab_video/d31_6Jul__color_',\
									DATA_PATH+'/elab_video/a41_6Jul__color_',\
									DATA_PATH+'/elab_video/c51_6Jul__color_']

			self.group1 = ['0  m','12 m','24 m','36 m','48 m','60 m','72 m','84 m','1 day','@color','2 M'] 	# stesso baffo dati nel tempo
			self.group2 = ['another 2 M']																	# baffi diversi dati prima dopo 2 mesi
			self.group3 = [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1]								# 0 dati nel tempo 1 dati diversi baffi
			self.group4 = [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]								# 0 dati giorno di estrazione e colorazione meno uno (per fare le differenze) 
			# piccolo check
			if self.ROOT.__len__() is not self.listaWhisker1.__len__():
				print 'err1'
				err1
			if self.ROOT.__len__() is not self.listaWhisker2.__len__():
				print 'err2' 
				err2
			if self.ROOT.__len__() == (self.group1.__len__()+self.group2.__len__()):
				print 'err3'
				err3
			if self.ROOT.__len__() is not self.group3.__len__():
				print 'err4'
				err4
			if self.ROOT.__len__() is not self.group4.__len__():
				print 'err5'
				err5
			for l,m,n in zip(self.listaWhisker1, self.listaWhisker2, self.ROOT):
				print l,m,n
				
		else:
			print 'questo test NON esiste. Correggere self.testType'
			return

		if doCompare:
			self.compareWhiskers()

	def checkTipTracking(self,TrialNumber=5,baffo='a11'): # controllo il baffo a11
		def loadTracking(fname): 
			with open(fname, 'rb') as f:
				return pickle.load(f)[0]
		def evalFFT(x):
			nCampioni = len(x)
			window = (1.0/0.54)*signal.hamming(nCampioni) # coefficiente di ragguaglio = 0.54
			x = window*(x-np.mean(x))
			X = fft.fft(x)
			return (2.0/nCampioni)*np.abs(X[0:nCampioni/2])
			
		trovato_baffo = False
		for lW1,lW2 in zip(self.listaWhisker1,self.listaWhisker2): # non color, color
			if lW1.find(baffo)>=0:
				trovato_baffo = True
				break
		if trovato_baffo:
			noncolorTrack = loadTracking(lW1+self.pickleEndTracking)
			colorTrack    = loadTracking(lW2+self.pickleEndTracking)
		for k,v1,v2 in zip(xrange(0,len(colorTrack)),noncolorTrack,colorTrack): # scorro i video
			if k==TrialNumber:
				traiettorie,nPunti,nCampioni = (v1.wst,v1.wst.__len__(),v1.wst[0].__len__())
				tipNc  = traiettorie[0]
				baseNc = traiettorie[99]
				TIPNc  = evalFFT(tipNc)
				traiettorie,nPunti,nCampioni = (v2.wst,v2.wst.__len__(),v2.wst[0].__len__())
				tipC   = traiettorie[0]
				baseC  = traiettorie[99]
				TIPC   = evalFFT(tipC)
				
		f  = plt.figure()
		a1 = f.add_subplot(1,2,1) 
		a2 = f.add_subplot(1,2,2) 
		#a1.plot(baseNc)
		#a1.plot(baseC)
		a1.plot(tipNc)
		a1.plot(tipC)
		a2.plot(TIPNc)
		a2.plot(TIPC)
		plt.show() 


 
	def checkTF(self,TrialNumber=5,baffo='a11'): # controllo il baffo a11
		def getBaseThisWhisker(baffo,TrialNumber): 
			for lW1 in self.listaWhisker1: 
				if lW1.find(baffo)>=0:
					break
			noncolorTrack = loadTracking(lW1+self.pickleEndTracking)
			for k,v1,v2 in zip(xrange(0,len(colorTrack)),noncolorTrack,colorTrack): # scorro i video
				if k==TrialNumber:
					traiettorie,nPunti,nCampioni = (v1.wst,v1.wst.__len__(),v1.wst[0].__len__())
					base = traiettorie[nPunti-1] 
			return base
			
		def evalFFT(x):
			nCampioni = len(x)
			window = (1.0/0.54)*signal.hamming(nCampioni) # coefficiente di ragguaglio = 0.54
			x = window*(x-np.mean(x))
			X = fft.fft(x)
			return (2.0/nCampioni)*np.abs(X[0:nCampioni/2])
		def evalTF(v,newBase=None):
			traiettorie,nPunti,nCampioni = (v.wst,v.wst.__len__(),v.wst[0].__len__())
			base = ingresso = traiettorie[nPunti-1] 
			tip  = traiettorie[0]
			if newBase is not None:
				base = ingresso = newBase
			Ingresso = (2.0/nCampioni)*np.abs(fft.fft(ingresso))
			f,Sxx = signal.csd(ingresso,ingresso,2000.0,nperseg=2000,scaling='spectrum')
			TF = []
			for t in traiettorie: 
				#t = t-np.mean(t)
				f,Syy = signal.csd(t,t,2000.0,nperseg=2000,scaling='density')          #scaling='spectrum'
				f,Syx = signal.csd(t,ingresso,2000.0,nperseg=2000,scaling='density')
				f,Sxy = signal.csd(ingresso,t,2000.0,nperseg=2000,scaling='density')
				H1 = [ syx/sxx  for sxx,syx in zip(Sxx,Syx)]
				H2 = [ syy/sxy  for syy,sxy in zip(Syy,Sxy)]
				H = [ np.sqrt(h1*h2) for h1,h2 in zip(H1,H2)]
				TF.append(np.asarray(np.abs(H)))
			return TF,base,tip

		def loadTracking(fname): 
			with open(fname, 'rb') as f:
				return pickle.load(f)[0]

		def loadTF(fname): 
			with open(fname, 'rb') as f:
				return pickle.load(f)[0]
		trovato = False
		for lW1,lW2 in zip(self.listaWhisker1,self.listaWhisker2): 
			if lW1.find(baffo)>=0:
				trovato = True
				break
		if trovato:
			if 0: #carico la TF
				TF_NC = loadTF(lW1+self.pickleEndTransFun)
				TF_C  = loadTF(lW2+self.pickleEndTransFun)
			else: # computo la TF o lo spettro
				noncolorTrack = loadTracking(lW1+self.pickleEndTracking)
				colorTrack    = loadTracking(lW2+self.pickleEndTracking)
				for k,v1,v2 in zip(xrange(0,len(colorTrack)),noncolorTrack,colorTrack): # scorro i video
					if k==TrialNumber:
						if 0: # transfer function
							TF_NC,base,tip = evalTF(v1)
							base_c31 = getBaseThisWhisker('c31',TrialNumber)
							base_baffo = getBaseThisWhisker(baffo,TrialNumber)
							for b in [base_c31,base_baffo]:
								b -= np.mean(b)
							TF_C,base2,tip2  = evalTF(v1,base_c31)
						else: # spettro
							TF_NC = []
							TF_C  = []
							traiettorie,nPunti,nCampioni = (v1.wst,v1.wst.__len__(),v1.wst[0].__len__())
							traiettorie = [t[1000:-1000] for t in traiettorie] # test Gibbs rimuovendo i bordi https://en.wikipedia.org/wiki/Gibbs_phenomenon 
							base = traiettorie[nPunti-1] 
							tip  = traiettorie[0]
							for t in traiettorie: 
								T = evalFFT(t)
								TF_NC.append(T)
							traiettorie,nPunti,nCampioni = (v2.wst,v2.wst.__len__(),v2.wst[0].__len__())
							traiettorie = [t[1000:-1000] for t in traiettorie]
							base2 = traiettorie[nPunti-1] 
							tip2  = traiettorie[0]
							TIP = evalFFT(tip)
							TIP2 = evalFFT(tip2)
							for t in traiettorie: 
								T = evalFFT(t)
								TF_C.append(T)
							TF_NC = np.asarray(TF_NC)
							TF_C  = np.asarray(TF_C)
							
				
			
			f = plt.figure()
			a1 = f.add_subplot(1,2,1)
			#a2 = f.add_subplot(1,3,2)
			a3 = f.add_subplot(1,2,2)
			#a21 = f.add_subplot(2,1,1)
			#a22 = f.add_subplot(2,1,2)
			a1.imshow(np.log10(TF_NC),aspect='auto', interpolation="nearest",cmap='RdBu_r')#'OrRd')
			#a2.imshow(np.log10(TF_C) ,aspect='auto', interpolation="nearest",cmap='RdBu_r')#'OrRd')
			a3.plot(TIP  ,'b')
			a3.plot(TIP2 ,'r')
			#a3.plot(base ,'b')
			#a3.plot(base2,'r')
			#a3.plot(base-base2)
			#a21.plot(TF_NC[99,:]  ,'b')	
			#a21.plot(TF_C[99,:]   ,'r')	
			#a22.plot(TF_NC[0,:]   ,'b')	
			#a22.plot(TF_C[0,:]    ,'r')	
			
			
			plt.show()
		else: 
			print 'baffo non pervenuto'
			
				

	def saveTipTF(self): # per Ale per fare l'ottimizzazione del modello in COMSOL
		def loadTF(fname): 
			with open(fname, 'rb') as f:
				return pickle.load(f)[0]
		for lW1 in self.listaWhisker1: # non color
			loadTipTF = loadTF(lW1+self.pickleEndTransFun)[0,:]
			TipTF = [(f,tf) for f,tf in zip(xrange(0,len(loadTipTF)),loadTipTF) ]
			np.savetxt(lW1+self.pickleEndTransFunTip,TipTF)
	
	def checkBaseTracking(self): # alcune misure vengono male, non e` che dipende da un errore nella stima della base?
		def loadTracking(fname): 
			with open(fname, 'rb') as f:
				return pickle.load(f)[0]
		for lW1,lW2 in zip(self.listaWhisker1,self.listaWhisker2): # non color, color
			noncolorTrack = loadTracking(lW1+self.pickleEndTracking)
			colorTrack    = loadTracking(lW2+self.pickleEndTracking)
			noncolorBaseTrack = []
			colorBaseTrack = []
			baseVarNoncolor = []
			baseVarColor = []
			for v1,v2 in zip(noncolorTrack,colorTrack): # scorro i video
				traiettorie,nPunti,nCampioni = (v1.wst,v1.wst.__len__(),v1.wst[0].__len__())
				base = traiettorie[nPunti-1]
				baseVarNoncolor.append(np.var(base))
				noncolorBaseTrack.append(base)
				traiettorie,nPunti,nCampioni = (v2.wst,v2.wst.__len__(),v2.wst[0].__len__())
				base = traiettorie[nPunti-1]
				baseVarColor.append(np.var(base))
				colorBaseTrack.append(base)
			print lW1, np.mean(baseVarNoncolor)
			print lW2, np.mean(baseVarColor)
			print '\n~~~~~~~~~~~~~~\n'
			f = plt.figure()
			a1 = f.add_subplot(2,1,1)	
			a2 = f.add_subplot(2,1,2)	
			a1.plot(np.asarray(noncolorBaseTrack).T)
			a2.plot(np.asarray(colorBaseTrack).T)
			a1.set_title(lW1)
			lW = lW1[:-len('__NONcolor_')]
			plt.savefig(lW1+'mecojoni.pdf')
			#colorTrack
			#
	
	def compareWhiskers(self,var2compare='spettri'):  #
		def loadPickle(fname):
			with open(fname, 'rb') as f:
				return pickle.load(f)	

		if var2compare == 'spettri': # pickleEndSpectrum indici: lista sessioni - variabili (freq,spectrum) - dimensioni variabile... 
			lista1 = [loadPickle(f+self.pickleEndSpectrum) for f in self.listaWhisker1]
			lista2 = [loadPickle(f+self.pickleEndSpectrum) for f in self.listaWhisker2]
			print len(lista1), len(lista1[0][1]), len(lista1[0][1][0]) 
			var2compare1 = [l[1][:,:800] for l in lista1]
			var2compare2 = [l[1][:,:800] for l in lista2]
		elif var2compare == 'transferFunction': 
			lista1 = [loadPickle(f+self.pickleEndTransFun) for f in self.listaWhisker1]
			lista2 = [loadPickle(f+self.pickleEndTransFun) for f in self.listaWhisker2]
			var2compare1 = [l[0][:,SPECTRAL_RANGE] for l in lista1] # fino a 350Hz
			var2compare2 = [l[0][:,SPECTRAL_RANGE] for l in lista2] # fino a 350Hz
		else: 
			print 'quale variabile si vuole comparare?'
			errore
		self.CORR2_undyed 	= self.comparisonKernel(var2compare1,var2compare1)
		self.CORR2_dyed 	= self.comparisonKernel(var2compare2,var2compare2)
		self.CORR2 			= self.comparisonKernel(var2compare1,var2compare2)


	def plotComparisons(self,var2compare='spettri'): 
		f = plt.figure(figsize=(10,10))
		a1 = f.add_subplot(2,2,1)
		a2 = f.add_subplot(2,2,2)
		a3 = f.add_subplot(2,2,3)
		a4 = f.add_subplot(2,2,4)
		a1.imshow(self.CORR2_undyed,aspect='equal', interpolation="nearest",clim=(0,1))
		a1.set_title('undyed vs undyed')
		a2.imshow(self.CORR2       ,aspect='equal', interpolation="nearest",clim=(0,1))
		a2.set_title('undyed vs dyed')
		a3.imshow(self.CORR2_dyed  ,aspect='equal', interpolation="nearest",clim=(0,1))
		a3.set_title('dyed vs dyed')
		a4.plot(([M[i] for M,i in zip(self.CORR2,xrange(0,len(self.CORR2)))]))
		a4.set_title('color effect')

		plt.savefig(DATA_PATH+'/elab_video/maialedeh'+var2compare+self.testType+'.pdf')
		

	def comparisonKernel(self,var1,var2): 
		N = var1.__len__()
		CORR2 = np.zeros((N,N))
		print N
		for i in xrange(0,var1.__len__()):
			for j in xrange(0,var2.__len__()): 
				CORR = np.corrcoef( var1[i].reshape(-1),\
									var2[j].reshape(-1))[0,1]
				CORR2[i,j] = np.power(CORR,2) 
		return CORR2

class sessione: # una sessione e` caratterizzata da tanti video
	def __init__(self,whiskerName,recordingDate,colorNonColor_status,path,ROI,videoThs,videoShow=True,go=True,justPlotRaw=False,overWriteElab=False):	
		self.name    	= whiskerName                               		# campione
		self.date    	= recordingDate                             		# giorno
		self.status  	= colorNonColor_status                      		# stato campione
		self.path 		= path
		self.ROI 		= ROI
		self.videoThs  	= videoThs
		self.videoShow 	= videoShow
		self.justPlotRaw = justPlotRaw
		self.overWriteElab = overWriteElab
		if self.justPlotRaw is True:
			self.overWriteElab = False
		self.id_name 					= self.name+'_'+self.date+'_'+self.status 
		self.pickleNameTracking			= DATA_PATH+'/elab_video/'+self.id_name+'.pickle'
		self.pickleNameSpectrum			= DATA_PATH+'/elab_video/'+self.id_name+'_spectrum.pickle'
		self.pickleNameTransFun			= DATA_PATH+'/elab_video/'+self.id_name+'_transferFunction.pickle'
		self.spettroMedName 			= DATA_PATH+'/elab_video/'+self.id_name+'_spectrum.pdf'
		self.transferFunctionMedName 	= DATA_PATH+'/elab_video/'+self.id_name+'_transferFunction.pdf'
		self.fig1Name 					= DATA_PATH+'/elab_video/'+self.id_name+'_test_fig1'
		if go: #  tutto in un colpo solo
			self.elaboroFilmati()
			self.doTestFig1()				
			self.calcoloTransferFunction()  
			self.calcoloSpettroMedio()		

	def elaboroFilmati(self): 
		if self.justPlotRaw is False:
			if self.overWriteElab is False:
				if os.path.isfile(self.pickleNameTracking):
					print 'il file '+self.pickleNameTracking+' esiste'
					return False
		self.resolvePath(self.path)                                   						# identifico quali sono i video da analizzare 
		print self.path
		self.V = [video(al,self.ROI,self.videoThs,self.videoShow,self.justPlotRaw) for al in self.aviList]	# XXX PROCESSING XXX: analizzo i filmati # TODO aggiungere il multithreading		
		self.saveTracking()
		return True

	def doTestFig1(self):
		self.loadTracking() # carico i dati
		for v,i in zip(self.V,xrange(0,self.V.__len__())): 
			fname = self.fig1Name+'_tr'+str(i)+'.pdf'
			if os.path.isfile(fname):
				print 'il file '+fname+' esiste'
			else:
				v.test_fig1(True,fname) 

	def calcoloTransferFunction(self,evalFigure=True): 
		if os.path.isfile(self.pickleNameTransFun):
			print 'il file '+self.pickleNameTransFun+' esiste'
		else:
			self.loadTracking() # carico i dati
			self.TF = []
			for v in self.V: # scorro i video
				traiettorie,nPunti,nCampioni = (v.wst,v.wst.__len__(),v.wst[0].__len__())
				ingresso = traiettorie[nPunti-1] 
				Ingresso = (2.0/nCampioni)*np.abs(fft.fft(ingresso))
				f,Sxx = signal.csd(ingresso,ingresso,2000.0,nperseg=2000,scaling='spectrum')
				TF = []
				for t in traiettorie: 
					f,Syy = signal.csd(t,t,2000.0,nperseg=2000,scaling='density')          #scaling='spectrum'
					f,Syx = signal.csd(t,ingresso,2000.0,nperseg=2000,scaling='density')
					f,Sxy = signal.csd(ingresso,t,2000.0,nperseg=2000,scaling='density')
					H1 = [ syx/sxx  for sxx,syx in zip(Sxx,Syx)]
					H2 = [ syy/sxy  for syy,sxy in zip(Syy,Sxy)]
					H = [ np.sqrt(h1*h2) for h1,h2 in zip(H1,H2)]
					TF.append(np.abs(H))
				self.TF.append(TF)
			self.TFM = np.mean(self.TF,axis=0)
			self.saveTransferFunction()
		self.loadTransferFunction()
		if evalFigure:
			f0 = [tf[0] for tf in self.TFM]
			f = plt.figure()
			a1 = f.add_subplot(1,1,1)
			cax1 = a1.imshow(np.log10(self.TFM),aspect='auto', interpolation="gaussian",cmap='RdBu_r')#'OrRd')	
			cbar1 = f.colorbar(cax1,ax=a1)
			plt.savefig(self.transferFunctionMedName)
	
	def calcoloSpettroMedio(self,evalFigure=True):
		if os.path.isfile(self.pickleNameSpectrum):
			print 'il file '+self.pickleNameSpectrum+' esiste'
		else:
			self.loadTracking()
			spettri = []
			for v in self.V:
				spettri.append(v.WSF)
			self.spettro_medio = np.mean(spettri,axis=0)
			self.freq = self.V[0].freq
			self.saveSpectrum()
		self.loadSpectrum()	
		if evalFigure:
			ff,a1 = plt.subplots(1)
			a1.imshow(np.log10(self.spettro_medio),aspect='auto', interpolation="nearest")	
			a1.set_xlabel('Freq [Hz]')
			V = [0,200,400,600,800,1000]
			i = []
			for v in V:
				print v
				m = [np.abs(f-v) for f in self.freq]
				i.append(m.index(min(m)))
			a1.set_xticks(i)
			a1.set_xticklabels(V)
			plt.savefig(self.spettroMedName)

	def resolvePath(self,path):	# trovo gli della sessione richiesta
		self.aviList = glob.glob(path+'*'+self.status+'*.avi')

	def saveTransferFunction(self): 
		with open(self.pickleNameTransFun, 'w') as f:
			pickle.dump([self.TFM], f)	

	def loadTransferFunction(self): 
		with open(self.pickleNameTransFun, 'rb') as f:
			data = pickle.load(f)	
		self.TFM = data[0]

	def saveSpectrum(self): 
		with open(self.pickleNameSpectrum, 'w') as f:
			pickle.dump([self.freq,self.spettro_medio], f)	

	def loadSpectrum(self): 
		with open(self.pickleNameSpectrum, 'rb') as f:
			data = pickle.load(f)	
		self.freq          = data[0]
		self.spettro_medio = data[1]

	def saveTracking(self): 
		with open(self.pickleNameTracking, 'w') as f:
			pickle.dump([self.V], f)	

	def loadTracking(self): 
		with open(self.pickleNameTracking, 'rb') as f:
			data = pickle.load(f)	
		self.V = data[0]

	def printSessionName(self): # test...
		print self.id_name

class video: # ogni fideo va elaborato
	def __init__(self,avi,ROI,videoThs,videoShow,justPlotRaw=False,processAllVideo=True):	
		self.avi= avi						# path del filmato
		self.ROI = ROI						# ROI ottimale per quel filmato 
		self.videoThs = videoThs			# soglia ottimale per quel filmato (binarizzazione)
		self.videoShow = videoShow			# mostro filmato o no (debug)
		self.justPlotRaw = justPlotRaw		# bypasso tutto per mostrare il filmato con box senza nessuna operazione
		if processAllVideo:
			cap = self.computeVideoParameters() 
			self.wst = np.zeros((self.N,self.maxFrame)) 	# whisker samples time per ogni cap
			self.elaboroFilmato(cap)				# faccio il tracking
			self.postProcessing()					# abbellisco il tracking con intorpolazione dei NaN e antialias (media mobile)
			self.WSF = self.trasformataBaffo()		# eseguo la trasformata di Fourier dei punti del baffo ricostruiti
			#self.test_fig1() 						# due subplot con overlap tracking e trends nel tempo
			#self.test_fig2()						# un subplot con lo spettro del baffo

	def computeVideoParameters(self): 
		self.bw = 2000.0 					# frame/sec - bandwidth
		cap = cv2.VideoCapture(self.avi) 
		self.maxFrame = int(cap.get(7))		# contatore dei frame
		if 0: # quanti frame ho ? 
			print self.maxFrame # == 4500
			fermati
		Np = int(self.maxFrame/2) 			# numero di campioni frequenze positive
		df = (self.bw/2)/Np								# df 
		dt = 1.0/self.bw								# dt
		self.time = [dt*c for c in xrange(0,self.maxFrame)]	
		self.freq = [df*c for c in xrange(0,self.maxFrame/2)]	
		self.N = 100 # XXX era 100 									# punti equidistanziati per il tracking del baffo
		return cap

	def test_fig1(self,salva=False,name=''): 
		ff, (a1,a2) = plt.subplots(1,2)
		a1.plot(self.time,self.wst.transpose())	
		a2.plot(self.wst)	
		if salva:
			plt.savefig(name)
		else:
			plt.show()

	def test_fig2(self): 
		ff,a1 = plt.subplots(1)
		a1.imshow(self.WSF,aspect='auto', interpolation="nearest")	
		rng = xrange(0,self.freq.__len__(),120)
		idx  = [i for i in rng] 
		freq = [int(self.freq[i]) for i in rng] 
		a1.set_xticks(idx)
		a1.set_xticklabels(freq)
		a1.set_xlabel('Freq [Hz]')
		plt.show()

	def postProcessing(self):
		# print self.wst.__len__()  # 100
		# print self.wst[0].__len__()  # 4500
		self.wst = self.interpoloNan(self.wst.transpose()).transpose() # lungo il tempo 
		self.antiAliasing()

	def interpoloNan(self,Mat):
		res = np.copy(Mat)
		for i in xrange(0,res.__len__()): # elimino il problema dei nan
			nans, x= np.isnan(res[i]), lambda z: z.nonzero()[0]
			res[i][nans]= np.interp(x(nans), x(~nans), res[i][~nans])	
		return res
	
	def antiAliasing(self):
		for i in xrange(0,self.wst.__len__()): 
			self.wst[i] = np.convolve(self.wst[i], np.ones((3,))/3,mode='same')
	
	def elaboroFilmato(self,cap): 
		#print aviPaths
		fn=-1
		while fn<self.maxFrame-1: # 100: #	
			fn+=1
			#~~~~~~~~~~ INIZIO ANALISI ~~~~~~~~~~#
			_,Read = cap.read() 
			if self.justPlotRaw:
				Frame = Read
			else:
				Read,_,Frame = self.doElabFrame(fn,self.N,Read)
			#~~~~~~~~~~ FINE   ANALISI ~~~~~~~~~~#
			if self.videoShow: # mostro i filmati 
				x,y,w,h = ( self.ROI[0]			   ,self.ROI[2],\
							self.ROI[1]-self.ROI[0],self.ROI[3]-self.ROI[2])
				cv2.rectangle(Frame, (x,y), (x+w,y+h), 255, 2)
				cv2.imshow('rip',Frame) 
			if not fn%50: # mostro a quale frame mi trovo
				print 'fn == 100'
				print 'Video'+self.avi,' Frame #',fn, '-> videoThs ~= ', int(1.12*np.median(Read)), self.videoThs # XXX prima era cosi`
			if cv2.waitKey(1) & 0xFF == ord('q'): # indispensabile per il corretto funzionamento 
				break
		self.maxFrame = fn

	def getBeamShape(self):
		cap = cv2.VideoCapture(self.avi) 										# calcolo al volo, quindi il cap non lo ho
		_,Read = cap.read()
		Read,_,Frame = self.doElabFrame(0,self.N,Read)
		cv2.imwrite("../elab_video/%s.jpg"%re.sub('/','',self.avi)[2:-4],Read)        # immagine del primo frame salvata su disco
		return self.puntiBaffoEquidistanziati(self.doROI(Frame),0,self.N,3) 	# ri-calcolo i punti sul Frame

	def doElabFrame(self,fn,N,Read): 
		#Frame = Read[1]   														# prendo i frame da tutti i filmati
		Frame = Read   															# prendo i frame da tutti i filmati
		Frame = Frame[10:-1,1:-1]   											# tolgo il frame number
		Frame = cv2.cvtColor(Frame, cv2.COLOR_BGR2GRAY) 						# transformo in scala di grigi
		Frameb = Frame
		Frame_blur = Frameb #cv2.medianBlur(Frameb,3)  											# se filtro l'immagine qui aiuta 
		Frame_ths = cv2.threshold(Frame_blur,self.videoThs,255,cv2.THRESH_BINARY)[1]  	# soglia e divido 
		self.puntiBaffoEquidistanziati(self.doROI(Frame_ths),fn,N,3) 					# calcolo i punti sul Frame
		return Frameb,Frame_blur,Frame_ths


	def doROI(self,f): # inquadro
		return f[self.ROI[2]:self.ROI[3],self.ROI[0]:self.ROI[1]]

	def puntiBaffoEquidistanziati(self,frame,fn,N,Degree): 
		x,y = self.get_whisker(frame)
		x,y = self.norm_whisker(x,y,N,Degree)
		for c in xrange(0,N):
			self.wst[c][fn] = y[c] # qui sto raccogliendo i dati
		if 1: # cambiare il frame serve solo per il plot 
			frame/=3 #10.0 
			for i,j in zip(x,y): 
				if not np.isnan(j):
					frame[j][i] = 255
		return x, y

	def get_whisker(self,frame):
		frame = frame.transpose()
		x = np.zeros(frame.__len__())
		y = np.zeros(frame.__len__())
		c = 0
		for i in frame:
			ths = np.sum(i)
			if ths > 10:
				M = cv2.moments(i)
				try: 
					y[c] = int(M['m01']/M['m00'])
				except :
					if y[c-1]:
						y[c] = y[c-1]
					else: 
						y[c] = np.nan
			else:
				y[c] = np.nan
			x[c] = c
			c += 1
		frame = frame.transpose()
		if 0:
			plt.imshow(frame)
			plt.plot(x,y,'k.')
			plt.show()
			fermati
		return x,y

	def norm_whisker(self,x,y,N,Degree): 
		# elimino la parte di ROI - piena di NaN - a sinistra del baffo
		c = 0
		for i in y: 
			if np.isnan(i):
				c+=1
			else: 
				break
		x = x[c+1:]
		y = y[c+1:]
		cv = self.bspline(zip(x,y), N, Degree, False) # mai periodico (e` un baffo non un anello) 
		cv = cv.transpose()
		return cv[0],cv[1]

	def bspline(self,cv, n=100, degree=3, periodic=False):  # Script taken from http://stackoverflow.com/questions/34803197/fast-b-spline-algorithm-with-numpy-scipy
		""" Calculate n samples on a bspline
			cv :      Array ov control vertices
			n  :      Number of samples to return
			degree:   Curve degree
			periodic: True - Curve is closed
					  False - Curve is open
		"""
		# If periodic, extend the point array by count+degree+1
		cv = np.asarray(cv)
		count = len(cv)
		if periodic:
			factor, fraction = divmod(count+degree+1, count)
			cv = np.concatenate((cv,) * factor + (cv[:fraction],))
			count = len(cv)
			degree = np.clip(degree,1,degree)
		# If opened, prevent degree from exceeding count-1
		else:
			degree = np.clip(degree,1,count-1)
		# Calculate knot vector
		kv = None
		if periodic:
			kv = np.arange(0-degree,count+degree+degree-1,dtype='int')
		else:
			kv = np.array([0]*degree + range(count-degree+1) + [count-degree]*degree,dtype='int')
		# Calculate query range
		u = np.linspace(periodic,(count-degree),n)
		# Calculate result
		arange = np.arange(len(u))
		points = np.zeros((len(u),cv.shape[1]))
		for i in xrange(cv.shape[1]):
			points[arange,i] = si.splev(u, (kv,cv[:,i],degree))
		return points

	def trasformataBaffo(self): # non voglio fare figure ma ritornare lo spettro per fare analisi prima/dopo la colorazione
		# print self.wst.__len__() # 100
		# print self.wst[0].__len__() # 4500
		traiettorie,nPunti,nCampioni = (self.wst,self.wst.__len__(),self.wst[0].__len__())
		window = (1.0/0.54)*signal.hamming(nCampioni) # coefficiente di ragguaglio = 0.54
		spettri_abs = np.zeros((nPunti,nCampioni/2)) 
		spettri_phs = np.zeros((nPunti,nCampioni/2)) 
		traiettorie = [t-traiettorie[nPunti-1] for t in traiettorie] # osservo dal punto di vista dello shaker
		traiettorie = [window*(t-np.mean(t)) for t in traiettorie] # finestro usando hamming e tolgo (se mai fosse rimasta) la media del segnale
		return self.fft_whisker(traiettorie,nCampioni)

	def fft_whisker(self,x,Np): 
		Xabs = np.zeros((x.__len__(),Np/2))
		Xphs = np.zeros((x.__len__(),Np/2))
		for i in range(0,x.__len__()): # si possono accorpare i cicli di nan-removal ed FFT	
			f = fft.fft(x[i])
			Xabs[i] = (2.0/Np)*np.abs(f[0:Np/2])
		return Xabs

	def prova(self):
		print 'stampami questo!'


def funTemporaneoConfrontoBaffiSimulatiTraLoro(SalvaImg=False): #FIXME TODO mettere nelle figure opportunamente
	CORR2 = np.loadtxt('/media/jaky/DATI BAFFO/elab_video/simulatedWhisker/comparisonSimWhiskers_CORR2_visualInspection.txt') 
	if SalvaImg: 
		f = plt.figure()
		a1 = f.add_subplot(1,1,1)
		cax1 = a1.imshow(CORR2,aspect='equal', interpolation="nearest",clim=(0,1))	
		cbar1 = f.colorbar(cax1,ax=a1)
		plt.savefig(DATA_PATH+'elab_video/simulatedWhisker/comparisonSimWhisker_ordered.pdf') #comparisonSimWhiskers_CORR2_visualInspection.pdf')
	return CORR2 



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# supplementary figures code
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
class photobleachingTest(): #elab photobleaching images
	def __init__(self,filesPath):
		# load images
		orderedList=['/image_0001_31MAR2017_9-00_50Hz_G1.bmp',\
					'/image_0002_31MAR2017_10-00_50Hz_G1.bmp',\
					'/image_0003_31MAR2017_11-00_50Hz_G1.bmp',\
					'/image_0004_31MAR2017_12-00_50Hz_G1.bmp',\
					'/image_0005_31MAR2017_13-00_50Hz_G1.bmp',\
					'/image_0006_31MAR2017_14-00_50Hz_G1.bmp',\
					'/image_0007_31MAR2017_15-00_50Hz_G1.bmp',\
					'/image_0008_31MAR2017_16-00_50Hz_G1.bmp']
		imgw = []
		imgb = []
		for i in orderedList:
			print filesPath+i
			img = cv2.imread(filesPath+i,0)
			maskw_img = img[150:200, 200:325]
			maskb_img = img[100:150, 200:325]
			imgw.append(maskw_img) # here the whiskers are displayed
			imgb.append(maskb_img) # here only background is displayed

		if 0: # test ROIs
			for i,j,name in zip(imgw,imgb,orderedList):
				plt.subplot(211),plt.imshow(i,'gray',vmin=0,vmax=255)
				plt.subplot(212),plt.imshow(j,'gray',vmin=0,vmax=255)
				plt.show()
			stop

		# sum all pixel values in both ROIs
		sumW = [] # sum pixels in whiskers' roi
		sumB = [] # sum pixels in background's roi
		diffWB = [] # in case light would change conditions, it will be considered (sumW-sumB) 
		x = 0
		for i,j in zip(imgw,imgb):
			sumW.append(np.sum(i))
			sumB.append(np.sum(j))
			if x == 0:
				diff0 = np.sum(i)-np.sum(j)
			x+=1
			diffwb = np.sum(i)-np.sum(j)
			diffWB.append(diffwb*1./diff0)
		time = np.asarray(range(0,len(diffWB)))
		diffWB = np.asarray(diffWB)
		# model -> dN/dt = -\lambda*N
		# N(t) = N0*exp(-\lambda*t)
		#      = N0*exp(-t/\tau), where \tau = 1/\lambda
		# --> log(N(t)/N0) = -\lambda*t 
		# proper fit parameters: N0 = 0.9619017; \lambda = -0.06709847 
		def photobleaching(x,y):

			func 	= lambda params, x: params[0]*np.exp(params[1] * x)
			errfunc = lambda p, x, y: func(p, x) - y 
			init_p 	= np.array((0.5, min(y)))  #bundle initial values in initial parameters
			p, success = sopt.leastsq(errfunc, init_p.copy(), args = (x, y))

			if 0:
				f = plt.figure() 
				a1=plt.subplot(111)
				a1.plot(x,y)
				xx = xrange(0,100)
				y_fit = func(p, xx)          #create a fit with those parameters
				a1.plot(xx,y_fit)
				show()
			return p

		params = photobleaching(time,diffWB)
		tau = -params[0]/params[1]

		# faccio figura 
		colors = ['b','c','r'] #cm.rainbow(np.linspace(0, 1, 4)) # 4 gruppi 
		FS = FONTSIZE
		fW = plt.figure(figsize=((3/2)*FIGSIZEx,FIGSIZEy))
		fW.subplots_adjust(wspace=0.15,hspace=0.5)
		a = fW.add_subplot(1,1,1)

		Npoints = 22
		WB  = [params[0]*np.exp(params[1]*t) for t in range(0,Npoints)]
		WBr = [params[0] + params[1]*t for t in range(0,Npoints)]
		dec_exp = a.plot(range(0,Npoints),WB,marker='.',markersize=10,color=colors[1],label='Exponential decay')
		dec_lin = a.plot(range(0,Npoints),WBr,'--',linewidth=2,color='0.65')
		misure = a.plot(time,diffWB,marker='.',markersize=10,color=colors[0],label='Measured data')
		a.annotate('', xy=(20,40), xycoords='axes fraction', xytext=(2,2), arrowprops=dict(color='k',width=1,headwidth=5,headlength=5))
		ticks = [tau]
		print tau
		for i in range(0,Npoints,10):
			ticks.append(i)
		a.set_xticks(ticks) # niente
		p0 = str(np.floor(params[0]*100)/100)
		p1 = str(np.floor(params[1]*100)/100)
		a.text(15,0.5,r"$y="+p0+" e^{"+p1+"t}$",fontsize=1.5*FS) 
		a.annotate("Decay time",
					xy=(tau, 0), xycoords='data',
					xytext=(15, 0.1), textcoords='data',
					fontsize=FS,
					arrowprops=dict(arrowstyle="->",
									connectionstyle="arc3"),
					)

		a.set_xlabel('Exposure time [hours]',fontsize=FS)
		a.set_ylim([0, 1]) # niente
		a.set_xlim([0, Npoints]) # niente
		a.set_ylabel('Normalized fluorescence intensity', fontsize=FS)
		customaxis(a,size=FONTSIZE,pad=10)
		plt.legend(fontsize=FONTSIZE,bbox_to_anchor=(0.3,0.4),frameon=False) #,loc='best'
		if 0:
			plt.show()
		else:
			# MY DRIVE PATH
			if os.path.isdir('/home/jaky/Documents/GoogleDrive/Whisker Paper/Figure'): 
				fW.savefig('/home/jaky/Documents/GoogleDrive/Whisker Paper/Figure/supplementary_photobleaching.pdf')#,dpi=400,bbox_inches='tight')
				fW.savefig('/home/jaky/Documents/GoogleDrive/Whisker Paper/Figure/supplementary_1.png')#,dpi=400,bbox_inches='tight')
			# DRYAD PATH
			if os.path.isdir(DATA_PATH+'/elab_video/'): 
				fW.savefig(DATA_PATH+'/elab_video/supplementary_photobleaching.pdf')#,dpi=400,bbox_inches='tight')
				fW.savefig(DATA_PATH+'/elab_video/supplementary_1.png')#,dpi=400,bbox_inches='tight')


def colorationProcess(directory):
	print directory
	chembleaching	= directory+'chembleaching.jpg' 
	cleaning		= directory+'cleaning.jpg' 
	drying			= directory+'drying.jpg' 
	isolateWhisker	= directory+'isolateWhisker.jpg' 
	dyeApplication	= directory+'dyeApplication.jpg' 
	testDyeing		= directory+'testDyeing.jpg'
	CB=mpimg.imread(chembleaching)
	CL=mpimg.imread(cleaning)
	CL=ndimage.rotate(CL, 90, reshape=True)
	DR=mpimg.imread(drying)
	IW=mpimg.imread(isolateWhisker)
	DA=mpimg.imread(dyeApplication)
	TD=mpimg.imread(testDyeing)

	print CB.shape
	print CL.shape
	'''
	self.luceBianca 		= directory+'IMG_0239.JPG'
	self.luceBluFiltroRosso = directory+'IMG_0238.JPG'
	self.luceBluFiltroPLung = directory+'IMG_0236.JPG'
	FR=mpimg.imread(self.luceBluFiltroRosso)
	FPL=mpimg.imread(self.luceBluFiltroPLung)
	#textSize, labelSize = fontSizeOnFigures(True)
	'''
	fW = plt.figure(figsize=((3/2)*FIGSIZEx,FIGSIZEy))
	fW.subplots_adjust(wspace=0.15,hspace=0.5)
	aw1 = fW.add_subplot(2,3,1)
	aw2 = fW.add_subplot(2,3,2)
	aw3 = fW.add_subplot(2,3,3)
	aw4 = fW.add_subplot(2,3,4)
	aw5 = fW.add_subplot(2,3,5)
	aw6 = fW.add_subplot(2,3,6)
	aw1.imshow(CB)
	referencePanel(aw1,'A',-0.03, 1.15)
	aw2.imshow(CL)
	referencePanel(aw2,'B',-0.03, 1.15)
	aw3.imshow(DR)
	referencePanel(aw3,'C',-0.03, 1.15)
	aw4.imshow(IW)
	referencePanel(aw4,'D',-0.03, 1.15)
	aw5.imshow(DA)
	referencePanel(aw5,'E',-0.03, 1.15)
	aw6.imshow(TD)
	referencePanel(aw6,'F',-0.03, 1.15)
	def unvisibleAxes(ax):
		ax.axes.get_xaxis().set_visible(False)
		ax.axes.get_yaxis().set_visible(False)
	[unvisibleAxes(ax) for ax in [aw1,aw2,aw3,aw4,aw5,aw6]] 

	if 0:
		plt.show()
	else:
		#fW.savefig(DATA_PATH+'/elab_video/supplementary_colorationProcess.pdf',dpi=400,bbox_inches='tight')
		fW.savefig
		fW.savefig

		# MY DRIVE PATH
		if os.path.isdir('/home/jaky/Documents/GoogleDrive/Whisker Paper/Figure'): 
			fW.savefig('/home/jaky/Documents/GoogleDrive/Whisker Paper/Figure/supplementary_colorationProcess.pdf',dpi=600,bbox_inches='tight')
			fW.savefig('/home/jaky/Documents/GoogleDrive/Whisker Paper/Figure/supplementary_2.png',dpi=600,bbox_inches='tight')
		# DRYAD PATH
		if os.path.isdir(DATA_PATH+'/elab_video/'): 
			fW.savefig(DATA_PATH+'/elab_video/supplementary_colorationProcess.pdf',dpi=600,bbox_inches='tight')
			fW.savefig(DATA_PATH+'/elab_video/supplementary_2.png',dpi=600,bbox_inches='tight')
	
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#





if __name__ == '__main__': 
	
	# XXX you are in branch *shared4paper
	
	# define global values 
	global ELAB_PATH 
	global DATA_PATH 
	global SPECTRAL_RANGE
	global FIGSIZEx
	global FIGSIZEy
	global FONTSIZE
	ELAB_PATH = os.path.abspath(__file__)[:-len(os.path.basename(__file__))] 		# code path
	DATA_PATH =  '..'																# data path (for Dryad sharing)
	#DATA_PATH = '/home/jaky/Documents/GoogleDrive/Whisker Paper/Figure/temp/' 
	SPECTRAL_RANGE = xrange(0,350) # [Hz]
	FIGSIZEx = 10
	FIGSIZEy = 6
	FONTSIZE    = 11 
	matplotlib.rcParams.update({'font.size': FONTSIZE })
	print '~~~~~~~~~~~~\nPLEASE NOTE:'
	print 'ELAB_PATH = '+ELAB_PATH
	print 'DATA_PATH = '+DATA_PATH
	print '~~~~~~~~~~~~\n:'

	#DEMO_TRACKING = True  		# play the demo 
	DEMO_TRACKING = False 		# draw figures 

	if DEMO_TRACKING: # whisker 'toShare d21 12May NONcolor' shared as demo of tracking 
		sessione('d21','12May','_NONcolor_',DATA_PATH+'/ratto1/d2_1/',(310, 629, 50, 210),33,True,True,False,True) 
	else:  
		#stampo_lunghezza_whiskers(True)    # to create pickle with whisker info, which should be present already in the folder
		dyeEnhanceAndBehavioralEffect()		# fig1 - dyeEnhanceAndBehavioralEffect.pdf
		simulatedAndSetup() 				# fig2 - simulationAndSetup.pdf				
		creoSpettriBaffi()					# fig3 - DiffTransferFunction.pdf			
		mergeComparisonsResults()			# fig4 - mergeComparisonsResults_transferFunction.pdf				
		#supplementary 
		photobleachingTest('../photobleaching/') 	# path for Dryad sharing
		colorationProcess('../colorationprocess/')
		if 0: # resize image eventually
			from PyPDF2 import PdfFileWriter, PdfFileReader
			for i,j in zip(['dyeEnhanceAndBehavioralEffect.pdf','simulationAndSetup.pdf','DiffTransferFunction.pdf','mergeComparisonsResults_transferFunction.pdf'],[1,2,3,4]): 
				InputPdf  = PdfFileReader(file(DATA_PATH+'/elab_video/'+i),'rb')
				OutputPdf = PdfFileWriter()
				for p in xrange(InputPdf.getNumPages()):
					page = InputPdf.getPage(p)
					page.scale(0.6,0.6)
					OutputPdf.addPage(page)
				with open (DATA_PATH+'/elab_video/'+'final_figure'+str(j)+'.pdf','wb') as f:
					OutputPdf.write(f)
			
