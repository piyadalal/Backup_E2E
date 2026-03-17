
'''
Created on 17.08.2020

Implements image operations(search, compare, color tolerances) using CV lib
     - except func. findImageOnScreen using StormTest for getting all screen region infos
       images(and save functions) and doing search itself using CV lib.
     - to be implemented getScreenRegionDict working with .regchk files

@author: MOLO01
'''
import os
from PIL import Image, ImageDraw
import cv2 as cv
import numpy as np
from pprint import pprint, pformat
from colorConstants import ColorDictionary
import time as ti


class ImageManager():

    def __init__(self):
        self.__st = None
        self.__lrm = None
        self.__tp = None

    def setTestParams(self, testParms):
        self.__tp = testParms
        self.__st = testParms.stormtestClient
        self.__lrm = testParms.logRegionManager

    def __convertPIL_to_cv(self, pilImage, color=False):
        tempImageFile = os.path.join(self.__st.getLogPath(), "xx.png")
        pilImage.save(tempImageFile)

        cvImage = None
        if color:
            cvImage = cv.imread(tempImageFile)
        else:
            cvImage = cv.imread(tempImageFile, cv.IMREAD_GRAYSCALE)
        os.unlink(tempImageFile)
        return cvImage

    def findImageInImage(self, haystackImgPath, needleImgPath, thresholdPerCent):
        logIdx = self.__lrm.open("ImageManager.findImageInImage %s" % (os.path.basename(needleImgPath)))
        msg = "haystackImgPath=%s, needleImgPath=%s, thresholdPerCent=%s" % (
        haystackImgPath, needleImgPath, thresholdPerCent)
        print(msg)

        imgFile = self.__st.saveScreen()
        rc = True
        needleImage = cv.imread(needleImgPath)
        haystackImage = cv.imread(haystackImgPath)

        needleImageH, needleImageW, _ = needleImage.shape
        haystackImageH, haystackImageW, _ = haystackImage.shape
        if needleImageW > haystackImageH:
            raise Exception("ImageManager.findImageInImage: Image Height larger than search area")
            return False
        if needleImageH > haystackImageW:
            raise Exception("ImageManager.findImageInImage: Image Width larger than search area")
            return False

        result = cv.matchTemplate(haystackImage, needleImage, cv.TM_CCOEFF_NORMED)
        threshold = float(thresholdPerCent) / 100
        loc = np.where(result >= threshold)
        if len(loc[0]) == 0:
            rc = False
            s = "threshold=%.2f returned=%s" % (threshold, rc)
            print(s)
            cv.imwrite(imgFile, haystackImage)
            self.updateThumbnail(imgFile)
            self.__lrm.close(logIdx, rc, s)
            return rc

        doMarkImage = True
        # Create a green rectangle on the mainImage and then write it to the disk
        if doMarkImage:
            # Green (0, 128, 0)
            colorDict = ColorDictionary()
            lineColor = colorDict.bgr("yellow")

            pilImage = Image.open(needleImgPath)
            w, h = pilImage.size
            pilImage.close()
            for pt in zip(*loc[::-1]):
                cv.rectangle(haystackImage, pt, (pt[0] + w, pt[1] + h), lineColor, 2)
            cv.imwrite(haystackImgPath, haystackImage)
            cv.imwrite(imgFile, haystackImage)
            self.updateThumbnail(imgFile)

        s = " threshold=%.2f returned=%s %s" % (threshold, rc, haystackImgPath)
        print(s)
        self.__lrm.close(logIdx, rc, s)
        return rc

    def findImageInRegion(self, haystackScreen, haystackRegion, needleScreen, needleRegion, imgFile=None,
                          threshold=None):
        logidx = self.__lrm.open("ImageManager.findImageInRegion haystack=%s.%s needle=%s.%s" % (
        haystackScreen, haystackRegion, needleScreen, needleRegion))
        msg = "haystack=%s.%s needle=%s.%s imgFile=%s" % (
        haystackScreen, haystackRegion, needleScreen, needleRegion, imgFile)
        print(msg)
        if imgFile is None:
            imgFile = self.__st.saveScreen("findImageInRegion: ")

        regChecker = self.__tp.regionChecker
        needleDict = regChecker.getScreenRegion(needleScreen, needleRegion, loadImages=True)
        if threshold:
            thresholdPerCent = threshold
        else:
            thresholdPerCent = needleDict["checkParams"]["threshold"]
        pilImage = needleDict["checkParams"]["image"]
        imageName = needleDict['checkParams']['referenceImage']
        needleImageFile = os.path.join(self.__st.getLogPath(), imageName)
        pilImage.save(needleImageFile)

        haystackDict = regChecker.getScreenRegion(haystackScreen, haystackRegion)
        regionRect = haystackDict["region"]
        cropCoords = self.regionRect2boxCoords(regionRect)
        imgObj = Image.open(imgFile)
        imgObjCropped = imgObj.crop(cropCoords)

        t = int(ti.time())
        imgName = "cropped_%s_%s_%s.png" % (t, haystackScreen, haystackRegion)
        fpCropped = os.path.join(self.__st.getLogPath(), imgName)
        imgObjCropped.save(fpCropped)
        print("findImageInRegion: haystackImage=%s" % (fpCropped))

        rc = self.findImageInImage(fpCropped, needleImageFile, thresholdPerCent)
        self.__lrm.close(logidx, rc, "findImageInImage returned %s" % (rc))

        return rc

    def imageCompare(self, pilImage1, pilImage2, thresholdPC):
        '''
            pilImage1 - Screen Image
            pilImage2 - Reference Image
            thresholdPC - Threshold percent

            Images are already read to byte arrays and are the same size.
        '''
        w1, h1 = pilImage1.size
        w2, h2 = pilImage2.size
        if (w1 == w2) and (h1 == h2):
            pass
        else:
            print("pilImage1.size", pilImage1.size)
            print("pilImage2.size", pilImage2.size)
            raise Exception("ImageManager.imageCompare image sizes don't match")

        # print("ImageManager.imageCompare", imagePath, imageRegion, imageParams)
        haystackImage = self.__convertPIL_to_cv(pilImage1)
        needleImage = self.__convertPIL_to_cv(pilImage2)

        result = cv.matchTemplate(haystackImage, needleImage, cv.TM_CCOEFF_NORMED)  # TM_CCORR_NORMED TM_CCOEFF_NORMED
        result2 = cv.minMaxLoc(result)
        deltaPC = abs(100 - ((1 - result2[1]) * 100))
        print("ImageManager.imageCompare percentage match %.2f Threshold is %s" % (deltaPC, thresholdPC))
        rc = (deltaPC > thresholdPC)
        return rc

    def colorCompare(self, pilImage, checkParams):
        '''
            pilImage - Screen Image already cropped

            Images are already read to byte arrays.
        '''
        referenceColor = checkParams.referenceColor
        tolerance = checkParams.tolerance
        threshold = checkParams.flatness

        img = self.__convertPIL_to_cv(pilImage, color=True)

        colour_range = [
            referenceColor[0] - tolerance[0],
            referenceColor[0] + tolerance[0],
            referenceColor[1] - tolerance[1],
            referenceColor[1] + tolerance[1],
            referenceColor[2] - tolerance[2],
            referenceColor[2] + tolerance[2]
        ]

        # 0 ... 256
        colour_range2 = []
        for v in colour_range:
            if v > 256:
                v = 256
            if v < 0:
                v = 0
            colour_range2.append(v)

        mask = None
        ranges = [colour_range2[n] for n in [4, 5, 2, 3, 0, 1]]  # RGB -> BGR
        hist = cv.calcHist([img], [0, 1, 2], mask, [1, 1, 1], ranges)
        # pprint(hist)
        npixel = img.shape[0] * img.shape[1]

        nPixel_inRange = int(hist[0][0][0])

        rc = False
        # actualFlatness = 98
        actualFlatness = int((nPixel_inRange / npixel) * 100)
        if actualFlatness > threshold:
            rc = True
        # print(rc, nPixel_inRange, npixel, actualFlatness)

        # [True, [0, 62, 142], 88.95013609755966, 2.2772170585365545]
        # actual color, actual flatness, actual peak error
        _actualColor = self.__actualColor(pilImage)
        retArray = [rc, list(_actualColor), actualFlatness, 0.0]
        s = pformat(retArray, indent=2)
        # print("ImageManager.colorCompare: %s" % (s))
        return retArray

    def __actualColor(self, pilImage):
        max_colors = pilImage.size[0] * pilImage.size[1]
        mainPixelColorIndex = -1
        colorList = pilImage.getcolors(max_colors)
        for i in range(len(colorList)):
            npixel = colorList[i][0]
            # color = colorList[i][1]
            # print(npixel, color)

            if mainPixelColorIndex < 0:
                mainPixelColorIndex = i
                continue
            if npixel > colorList[mainPixelColorIndex][0]:
                mainPixelColorIndex = i

        colorListItem = colorList[mainPixelColorIndex]
        print("__actualColor: colorListItem %s" % (colorListItem))
        return colorListItem[1]

    def updateThumbnail(self, imageObjPath):
        bn = os.path.basename(imageObjPath)
        extType = ".png"
        if bn.endswith(extType):
            thumbnailName = bn.replace(extType, "_thumb.jpeg")
        extType = ".jpg"
        if bn.endswith(extType):
            thumbnailName = bn.replace(extType, "_thumb.jpeg")
        dn = os.path.dirname(imageObjPath)
        thumbnailPath = os.path.join(dn, "thumbs", thumbnailName)

        if not os.path.exists(thumbnailPath):
            print("updateThumbnail: missing %s" % (thumbnailPath))
            return

        tnImageObj = Image.open(thumbnailPath)
        thumbnailSize = tnImageObj.size
        del tnImageObj

        im = Image.open(imageObjPath)
        im.thumbnail(thumbnailSize, Image.ANTIALIAS)
        im.save(thumbnailPath, "JPEG")
        del im
        print("updateThumbnail: updated %s" % (thumbnailPath))

    def regionRect2boxCoords(self, regionRect):
        (x, y, w, h) = regionRect
        cropArea = (x, y, x + w, y + h)
        return cropArea

    def boxCoords2regionRect(self, cropArea):
        (x0, y0, x1, y1) = cropArea
        regionRect = (x0, y0, x1 - x0, y1 - y0)
        return regionRect

    def markImage(self, fn, result, boxCoords):
        '''
        PIL version is very old and rectangle does not support width
        Hence, we make the rectangle ourselves.
        '''
        redColor = "red"
        greenColor = "green"
        yellowColor = "yellow"
        if isinstance(result, bool):
            if result:
                color = greenColor
            else:
                color = redColor
        else:
            color = yellowColor
        x1, y1, x2, y2 = boxCoords
        imgObj = Image.open(fn)
        draw = ImageDraw.Draw(imgObj)
        lineWidth = 5
        draw.line((x1, y1, x2, y1), fill=color, width=lineWidth)
        draw.line((x2, y1, x2, y2), fill=color, width=lineWidth)
        draw.line((x1, y1, x1, y2), fill=color, width=lineWidth)
        draw.line((x1, y2, x2, y2), fill=color, width=lineWidth)
        regionRect = self.boxCoords2regionRect(boxCoords)
        print("markImage: color=%s boxCoords=%s regionRect=%s fn=%s" % (color, boxCoords, regionRect, fn))
        imgObj.save(fn)
        del imgObj
        self.updateThumbnail(fn)


if __name__ == '__main__':
    print("Done")
