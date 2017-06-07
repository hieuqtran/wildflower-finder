'''
Image preprocessing for CNN.
Input: jpg files exported from Mac Photo app
Output: Saved numpy array of images in specified shape for use in CNN. Corrects for class imbalance via image generation.
Images are resized to specified shape, cropped to square, then image generation is used to create flipped/rotated images.
'''

from __future__ import print_function
import numpy as np
import pandas as pd
import os
from os import listdir
from os.path import isfile, join
import cv2
import re
import PIL
from PIL import Image
from skimage import io
from skimage.transform import resize
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from keras.utils import np_utils

from img_resize import my_image_resize
from img_resize import my_image_rename

np.random.seed(1337)  # for reproducibility


def image_categories(img_root):
    ''' A dictionary that stores the image path name and flower species for each image
    Input: image path names (from root directory)
    Output: dictionary 'categories'
    '''
    flower_dict = {}
    files = [f for f in listdir(img_root) if isfile(join(img_root, f))]
    # for path, subdirs, files in os.walk(resized_root):
        # print(path, subdirs, files)
    for name in files:
        # name = name.replace(' ', '')
        # name = name.replace('-', '_')
        if not (name.startswith('.')):
        #     if name != 'cnn_capstone.py':
            img_path = '{}{}'.format(img_root, name)
            # img_path = os.path.join(path, name)
            img_cat = re.sub("\d+", "", name).rstrip('_.jpg')
            # img_cat = img_cat[:-3]
            flower_dict[img_path] = img_cat
    return flower_dict

def _center_image(img, new_size=[256, 256]):
    '''
    Helper function. Takes rectangular image resized to be max length on at least one side and centers it in a black square.
    Input: Image (usually rectangular - if square, this function is not needed).
    Output: Image, centered in square of given size with black empty space (if rectangular).
    '''
    row_buffer = (new_size[0] - img.shape[0]) // 2
    col_buffer = (new_size[1] - img.shape[1]) // 2
    centered = np.zeros(new_size + [img.shape[2]], dtype=np.uint8)
    centered[row_buffer:(row_buffer + img.shape[0]), col_buffer:(col_buffer + img.shape[1])] = img
    return centered

def resize_image_to_square(img, new_size=((256, 256))):
    '''
    Resizes images without changing aspect ratio. Centers image in square black box.
    Input: Image, desired new size (new_size = [height, width]))
    Output: Resized image, centered in black box with dimensions new_size
    '''
    if(img.shape[0] > img.shape[1]):
        tile_size = (int(img.shape[1]*new_size[1]/img.shape[0]),new_size[1])
    else:
        tile_size = (new_size[1], int(img.shape[0]*new_size[1]/img.shape[1]))
    # print(cv2.resize(img, dsize=tile_size))
    return _center_image(cv2.resize(img, dsize=tile_size), new_size)

def crop_image(img, crop_size):
    '''
    Crops image to new_dims, centering image in frame.
    Input: Image, desired cropped size (crop_size=[height, width])
    Output: Cropped image
    '''
    row_buffer = (img.shape[0] - crop_size[0]) // 2
    col_buffer = (img.shape[1] - crop_size[1]) // 2
    return img[row_buffer:(img.shape[0] - row_buffer), col_buffer:(img.shape[1] - col_buffer)]

def process_images(file_paths_list, resize_new_size=[256,256], crop_size=[224, 224]):
    '''
    Input: list of file paths (images)
    Output: numpy array of processed images: normalized, resized, centered)
    '''
    x = []

    for file_path in file_paths_list:
        img = cv2.imread(file_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = resize_image_to_square(img, new_size=resize_new_size)
        img = crop_image(img, crop_size=crop_size)
        x.append(img)
    x = np.array(x)
    return x

def train_validation_split(saved_arr='flowers_224.npz'):
    '''
    Splits train and validation data and images. (Will also load test images, names from saved array).
    Input: saved numpy array, files/columns in that array
    Output: Train/validation data (e.g., X_train, X_test, y_train, y_test), test images, test image names (file names minus '.png')
    '''
    data = np.load(saved_arr)

    x = data.files[0]
    x = data[x]
    y = data.files[1]
    y = data[y]
    yp = np.array(y)
    number = LabelEncoder()
    y = number.fit_transform(y.astype('str'))
    X_train, X_test, y_train, y_test = train_test_split(x, y)

    print('X_train: {} \ny_train: {} \nX_test: {} \ny_test: {}'.format(X_train.shape, y_train.shape, X_test.shape, y_test.shape))
    # X_train, X_test = image_asfloat(X_train, X_test)
    # X_train, X_test = image_rgb_unit_scale(X_train, X_test)
    X_train = X_train.astype('float32')
    X_test = X_test.astype('float32')
    X_train = X_train/255
    X_test = X_test/255
    return X_train, X_test, y_train, y_test

# def image_asfloat(X_train, X_test):
#     X_train = X_train.astype('float32')
#     X_test = X_test.astype('float32')
#     return X_train, X_test
#
# def image_rgb_unit_scale(X_train, X_test):
#     X_train /= 255
#     X_test /= 255
#     return X_train, X_test
#
# def print_X_shapes(X_train, X_test):
#     print('X_train shape:', X_train.shape)
#     print(X_train.shape[0], 'train samples')
#     print(X_test.shape[0], 'test samples')

def convert_to_binary_class_matrices(y_train, y_test, nb_classes):
    # convert class vectors to binary class matrices
    Y_train = np_utils.to_categorical(y_train, nb_classes)
    Y_test = np_utils.to_categorical(y_test, nb_classes)
    return Y_train, Y_test

if __name__ == '__main__':
    img_root = '../imgs_jpgs/'
    # Rename files exported from Mac Photo app (in place)
    my_image_rename(img_root)
    # Create y (labels) and file list (x) from image names
    y_dict = image_categories(img_root)
    y = list(y_dict.values())
    file_list = list(y_dict.keys())
    # with Pool(4) as p:
    #     p.map(process_images(file_list, resize_new_size=[256,256], crop_size=[224, 224]), file_list)
    image_array = process_images(file_list, resize_new_size=[256,256], crop_size=[224, 224])

    np.savez('flowers_224.npz', image_array, y)
    X_train, X_test, y_train, y_test = train_validation_split('flowers_224.npz')
    nb_classes = 13
    Y_train, Y_test = convert_to_binary_class_matrices(y_train, y_test, nb_classes)
    np.savez('validation_224.npz', X_train, X_test, Y_train, Y_test)
