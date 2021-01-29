import math
import os
import random
import concurrent.futures
import time

import GetAlbums
from PIL import Image
import joblib

try:
    imagelist = joblib.load("imagelist.jblib")
except FileNotFoundError:
    imagelist = {}


def get_average(image):
    img = Image.open("images/" + image).convert("RGB")
    r, g, b = 0, 0, 0
    width, height = img.size
    size = width * height
    pixel_values = list(img.getdata())
    for x in range(width):
        for y in range(height):
            try:
                r += pixel_values[width * y + x][0]
                g += pixel_values[width * y + x][1]
                b += pixel_values[width * y + x][2]
            except TypeError:
                img.show()
                print(type(pixel_values[width * y + x]))
                print(type(r))
                return
    r //= size
    g //= size
    b //= size
    return r, g, b


def find_distance(a, b):
    return math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2) + ((a[2] - b[2]) ** 2))


# pls use square image
def chunk_image(image, resolution):
    img = Image.open(image).convert("RGB")
    img = img.resize((resolution, resolution), Image.ANTIALIAS)
    img_vals = [[[None] for _ in range(resolution)] for _ in range(resolution)]
    pixel_values = img.getdata()
    width, height = img.size

    for x in range(width):
        for y in range(height):
            img_vals[x][y] = rgb2lab(pixel_values[width * y + x])

    return img_vals


# Downscale images in images folder so we get 100x100 versions.  still visible and not necessarily humongous file
def downscale_images():
    for root, dirs, files in os.walk("largeimages/"):
        for image in files:
            img = Image.open("largeimages/" + image).convert("RGB")
            img = img.resize((100, 100), Image.ANTIALIAS)
            img.save("images/" + image, "JPEG")


# Finds album matches in order from top left to bottom right.  results have cool effect, very accurate on left, not so much on right.  fades in betweenallCoords = [[(f, q) for f in range(width) for q in range(height)]]
#     allCoords
def compare_vals(img, imgdict):
    width = len(img)
    height = len(img[0])
    newimg = [[[None] for _ in range(width)] for _ in range(height)]
    for x in range(width):
        for y in range(height):
            newimg[x][y] = min(imgdict, key=lambda z: find_distance(imgdict[z], img[x][y]))
            imgdict.pop(newimg[x][y])
            print("Found image for X: " + str(x) + " Y: " + str(y))
            print("Len of imgdict " + str(len(imgdict)))
    return newimg


# Finds album matches for random pixels.  Results are fuzzier, however more consistent throughout
def rand_compare_vals(img, imgdict):
    width = len(img)
    height = len(img[0])
    newimg = [[[None] for _ in range(width)] for _ in range(height)]

    allCoords = [(f, q) for f in range(width) for q in range(height)]
    random.shuffle(allCoords)
    for i in allCoords:
        newimg[i[0]][i[1]] = min(imgdict, key=lambda z: find_distance(imgdict[z], img[i[0]][i[1]]))
        imgdict.pop(newimg[i[0]][i[1]])
        print("Found image for X: " + str(i[0]) + ", " + str(i[1]))
    return newimg

# different pixel orders for different effects
def diagonal_compare_vals(img, imgdict):
    width = len(img)
    height = len(img[0])
    print("type of imglist " + str(type(imgdict)))

    newimg = [[[None] for _ in range(width)] for _ in range(height)]
    print("size: " + str(len(newimg)) + ", " + str(len(newimg[0])))

    # print("Our starting coordinate: " + str(a) + ", " + str(b))
    # print("Color found is " + str(img[a][b]))
    for k in range(width - 1):
        for j in range(k):
            i = k - j
            dist = None
            file = None
            for q in imgdict:
                distance = find_distance(img[i][j], imgdict[q])
                if not dist:
                    dist = distance
                    file = q
                elif distance < dist:
                    dist = distance
                    file = q
            newimg[i][j] = file
            print("Type for file is " + str(type(file)))
            print("Image found for pixel: " + str(i) + ", " + str(j))
            try:
                imgdict.pop(file)
            except KeyError:
                print("we stressin over distance: " + str(dist))
                exit()
    for k in range(width - 2):
        k = width - 2 - k
        for j in range(k):
            i = k - j
            dist = None
            file = None
            for q in imgdict:
                distance = find_distance(img[width - j - 1][width - i - 1], imgdict[q])
                if not dist:
                    dist = distance
                    file = q
                elif distance < dist:
                    dist = distance
                    file = q
            newimg[width - j - 1][width - i - 1] = file
            print("I promise we're not skipping this section")
            try:
                imgdict.pop(file)
            except KeyError:
                print("we stressin over distance: " + str(dist))
                exit()

    joblib.dump(newimg, "orderednewimgvals.jblib")
    return newimg


# Creates the new version of image.  Creates empty photo and pastes images.  Must have images assigned in vals matrix
def create_new_image(vals):
    print("We made it to starting the new image")
    newimg = Image.new("RGB", (15100, 15100))
    x_off = 0
    print("Length of x" + str(len(vals)))
    # Iterate over image and paste each image in next slot
    for x in range(len(vals)):
        y_off = 0
        for y in range(len(vals[x])):
            print("Pasting image at x:" + str(x_off) + ", y: " + str(y_off))
            newimg.paste(Image.open("images/" + vals[x][y]), (x_off, y_off))
            y_off += 100
        x_off += 100
    # Show image and save it as new file
    newimg.show()
    newimg.save("final.jpg", "JPEG")


# Converts RGB to LAB  taken from Adobe cookbook
def rgb2lab(inputColor):
    if not inputColor:
        return
    num = 0
    RGB = [0, 0, 0]

    for value in inputColor:
        value = float(value) / 255

        if value > 0.04045:
            value = ((value + 0.055) / 1.055) ** 2.4
        else:
            value = value / 12.92

        RGB[num] = value * 100
        num = num + 1

    XYZ = [0, 0, 0, ]

    X = RGB[0] * 0.4124 + RGB[1] * 0.3576 + RGB[2] * 0.1805
    Y = RGB[0] * 0.2126 + RGB[1] * 0.7152 + RGB[2] * 0.0722
    Z = RGB[0] * 0.0193 + RGB[1] * 0.1192 + RGB[2] * 0.9505
    XYZ[0] = round(X, 4)
    XYZ[1] = round(Y, 4)
    XYZ[2] = round(Z, 4)

    XYZ[0] = float(XYZ[0]) / 95.047  # ref_X =  95.047   Observer= 2°, Illuminant= D65
    XYZ[1] = float(XYZ[1]) / 100.0  # ref_Y = 100.000
    XYZ[2] = float(XYZ[2]) / 108.883  # ref_Z = 108.883

    num = 0
    for value in XYZ:

        if value > 0.008856:
            value = value ** (0.3333333333333333)
        else:
            value = (7.787 * value) + (16 / 116)

        XYZ[num] = value
        num = num + 1

    Lab = [0, 0, 0]

    L = (116 * XYZ[1]) - 16
    a = 500 * (XYZ[0] - XYZ[1])
    b = 200 * (XYZ[1] - XYZ[2])

    Lab[0] = round(L, 4)
    Lab[1] = round(a, 4)
    Lab[2] = round(b, 4)

    return Lab


# Gets LAB values for all images and stores them to imagelist
def get_images_info():
    global imagelist
    for root, dirs, files in os.walk("images/"):
        for img in files:
            if img not in imagelist:
                lab = rgb2lab(get_average(img))
                if not lab:
                    continue
                imagelist[img] = lab
                print(lab)
    joblib.dump(imagelist, "imagelist.jblib")


playlists = [
    'https://open.spotify.com/playlist/2doesLfLSBsRFLcGfIUiPl?si=cmesMEI3RVm0P8uHa4JlIQ',
    'https://open.spotify.com/playlist/3DkNkNGKobBjHV9q0rPH7w?si=KNI4tbwdThuNo-OlY9uhjQ',
    'https://open.spotify.com/playlist/0s41JrXArBRe61V3rgYxwT?si=fkOGfi1ySn21rtA6FgNFkA',
    'https://open.spotify.com/playlist/4OLJaA2XIVOOJFkmXmpsuC?si=OMSvsCoxS_KBZW_qyXG8og',
    'https://open.spotify.com/playlist/37i9dQZF1DWSDoVybeQisg?si=B3VP3a8kTLWsRuXmr99opA',
    'https://open.spotify.com/playlist/37i9dQZF1DX8gDIpdqp1XJ?si=ey8TB69fQvOHHVOgrJk0WQ',
    'https://open.spotify.com/playlist/6LsfM2jpshd8kcZP425oB0?si=WlDDvMVCT5WLAqnc-CC65w',
    'https://open.spotify.com/playlist/4Db0RcdReoK3K6NYUgR0CD?si=8OOcX33dQ2u0z7W1QFGiDw',
    'https://open.spotify.com/playlist/0rQ4JogJ2U5Z0XR2RqVo75?si=qPEEXnViQlqlhqoMB3qFBg',
    'https://open.spotify.com/playlist/0icVACcVcAb8tnCHHHTHZ0?si=mqlf_sdpThahf4u-fTwOBw',
    'https://open.spotify.com/playlist/0RulRtPLXdJiztHdy9UCJZ?si=lSPvO997Qeu3Rlrjw6_kyg',
    'https://open.spotify.com/playlist/0RulRtPLXdJiztHdy9UCJZ?si=2HPC9OJ9T1mz9ysVrGZhxQ',
    'https://open.spotify.com/playlist/0D3L4SNpM5fcfphmpmWQV3?si=zjPT6958RTmTXpv1tg5a5A',
    'https://open.spotify.com/playlist/4lyPVNgeY4MlbJcmqvqkzQ?si=5o5VvVMRSF6OHPI-ASAqkQ',
    'https://open.spotify.com/playlist/68xcQLj1AR18GPr4QBMBMi?si=Gs1QyIReSPqqWG_53k7wRQ',
    'https://open.spotify.com/playlist/12FJuP1Y62vFOBDpZxBNTn?si=jaPCNTXETMS4Xg0mXJkUZg',
    'https://open.spotify.com/playlist/1NtLA8HHnkYxUZlYvyiYhy?si=pvumtzW9S_iUqg-i8K0d4g',
    'https://open.spotify.com/playlist/0rQ4JogJ2U5Z0XR2RqVo75?si=qsutP7UER7mH9KAFnZLITw',
    'https://open.spotify.com/playlist/5NuSYWaTYPqaJwvFqjRLIG?si=JnuMmupSTTKTpdWogDg-9A',
    'https://open.spotify.com/playlist/1kSjAXEiKBm8vpyQysF5Im?si=L5eFin2MTAy5d7W70Qytag',
    'https://open.spotify.com/playlist/0gvjytW5IawFjQuhi8foFw?si=nIz1n5bTTI2X5jF2SqGjSQ',
    'https://open.spotify.com/playlist/5I5VBP5DVLbJJnpyw0Nm3q?si=4F_YumKRR2GxP9jI_x_rAg',
    'https://open.spotify.com/playlist/3PZHKpNa2kBmlbkPZTOfOO?si=wl_lm3z0TtuPriosU8gz7w',
    'https://open.spotify.com/playlist/6EGhgsPJofJxdCnY5MxUNx?si=Ddsu7pMoRvW785DR-IVBfw',
    'https://open.spotify.com/playlist/7IQhUg1E2K1055KnaIZZRE?si=OOS_B4gKS1eEJ3XrSUWoiQ',
    'https://open.spotify.com/playlist/2xRG5hs3ybO0CoiMMmzC9Q?si=65ooGtzWS2qSSZligFWEgQ',
    'https://open.spotify.com/playlist/6nywQtk8isGhP49p8wKJL9?si=3wegu25TTN-8wYPsyl6-DA',
    'https://open.spotify.com/playlist/3UEc3hd2pEyFhrENvdFWGU?si=QG5CmO1zTueQ4MNaAnW2VA'
]

# Load all playlists, download images then dump info list to a file
# imglist = GetAlbums.get_albums(playlists=playlists)
# joblib.dump(imglist, imagelist.jblib)
# exit()
# get_images_info()
# downscale_images()

# ordered_vals = diagonal_compare_vals(chunk_image("Mike.jpg", 151), imagelist)

start = time.perf_counter()
ordered_vals = rand_compare_vals(chunk_image("kitty.jpg", 151), imagelist)
orderedtime = time.perf_counter() - start
start = time.perf_counter()
#ordered_vals = compare_vals(chunk_image("kitty.jpg", 151), imagelist)
lambdatime = time.perf_counter() - start
print("ordered time took: " + str(orderedtime))
print("new time took: " + str(lambdatime))
create_new_image(vals=ordered_vals)

