# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 15:42:44 2020

@author: Ania
"""

import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scipy.ndimage import zoom
from keras.preprocessing.image import ImageDataGenerator
from keras import backend as K
import tensorflow as tf
import numpy as np
import nibabel as nib
import os, glob

BATCH_SIZE = 16
TARGET_SIZE = (256,256)
NUM_TEST_SAMPLES=[365, 146, 161, 349, 133, 233, 135,  98, 178, 162, 269, 121, 103,  96, 383, 620,  75, 93,  60, 140,  89, 102]
model_path = 'Unet_model'
seg_path = 'kits19/data'
vol_path = os.path.join('images/test', 'case_*')
vol_files = glob.glob(vol_path)


#Dice Score Function
def dice_coef(y_true, y_pred):
    smooth = 1.0
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    
    intersection = K.sum(y_true_f * y_pred_f).numpy()
    print('intersection ' + str(intersection))
    union =( K.sum(y_true_f) + K.sum(y_pred_f) ).numpy()
    print('union ' +str(union))
    return (2. * intersection + smooth) / (union + smooth)


def dice_coef2(y_true, y_pred):
    
    y_true_0 = tf.where(y_true ==0, 1,0)
    y_pred_0 = tf.where(y_pred ==0, 1,0)
    y_true_1 = tf.where(y_true ==1, 1,0)
    y_pred_1 = tf.where(y_pred ==1, 1,0)
    y_true_2 = tf.where(y_true ==2, 1,0)
    y_pred_2 = tf.where(y_pred ==2, 1,0)
    
    score0 = dice_coef(y_true_0, y_pred_0)
    score1 = dice_coef(y_true_1, y_pred_1)
    score2 = dice_coef(y_true_2, y_pred_2)
    
    dice_kidney.append(score1)
    dice_tumor.append(score2)
    score = score0*0.1+score1*0.3+score2*0.6
    
    return score


def dice_coef_loss(y_true, y_pred):
    return 1-dice_coef2(y_true, y_pred)

#%% Prediction for each patient
image_test_datagen =  ImageDataGenerator(rescale = 1./255)
seed =1

model = tf.keras.models.load_model(model_path, custom_objects={'dice_coef_loss': dice_coef_loss, 'dice_coef2':dice_coef2})


dice =[]
dice_kidney =[]
dice_tumor =[]
predictions =[]
seg =[]
tmp =0
for i in vol_files:
        test_generator = image_test_datagen.flow_from_directory(
            directory =os.path.join(i, 'vol'),
            target_size = (256,256),
            batch_size = BATCH_SIZE,
            class_mode=None,
            seed=seed)
        
        prediction = model.predict(test_generator, 
                                   steps = NUM_TEST_SAMPLES[tmp]/BATCH_SIZE,
                                   verbose=1)
    
        predict_class = np.argmax(prediction, axis=3)
  
        
        mask_directory = os.path.join(seg_path,  'case_00'+str(188+tmp),'segmentation.nii.gz')
        mask = nib.load(mask_directory)
        mask = mask.get_data()
        
        predict_class = zoom(predict_class, (1,2,2), order =1, mode='nearest')
        seg.append(mask)
        predictions.append(predict_class)
        
        mask  = tf.convert_to_tensor(mask, dtype=tf.int32)
    
        dice_tmp = dice_coef2(mask, predict_class)
        dice.append(dice_tmp)
       
        tmp+=1
    
 #%% Results analysis

dice_mean = np.mean(dice)
dice_max = np.max(dice)
dice_min = np.min(dice)
dice_std = np.std(dice)

dice_mean_kidney = np.mean(dice_kidney)
dice_max_kidney = np.max(dice_kidney)
dice_min_kidney = np.min(dice_kidney)
dice_std_kidney = np.std(dice_kidney)

dice_mean_tumor = np.mean(dice_tumor)
dice_max_tumor = np.max(dice_tumor)
dice_min_tumor = np.min(dice_tumor)
dice_std_tumor = np.std(dice_tumor)

print(dice)

print("Dice max: "+str(dice_max))
print("Dice min: "+str(dice_min))
print("Dice mean: "+str(dice_mean))
print("Dice standard deviation: "+str(dice_std))

print("Dice max for kidney: "+str(dice_max_kidney))
print("Dice min for kidney: "+str(dice_min_kidney))
print("Dice mean for kidney: "+str(dice_mean_kidney))
print("Dice standard deviation for kidney: "+str(dice_std_kidney))

print("Dice max for tumor: "+str(dice_max_tumor))
print("Dice min for tumor: "+str(dice_min_tumor))
print("Dice mean for tumor: "+str(dice_mean_tumor))
print("Dice standard deviation for tumor: "+str(dice_std_tumor))

#%% Choosing cases for visualization

best_dice = (predictions[7]).astype(np.uint8)
best_mask = (seg[7]).astype(np.uint8)
worst_dice = (predictions[2]).astype(np.uint8)
worst_mask = (seg[2]).astype(np.uint8)

average_dice = (predictions[1]).astype(np.uint8)
average_mask = (seg[1]).astype(np.uint8)

#%% Visualization of results
fig = plt.figure()
ax = fig.add_subplot(1,1,1, projection='3d' )
ax.voxels(best_dice )
ax.set_title('Our best results')
plt.show()

fig = plt.figure()
ax = fig.add_subplot(1,1,1, projection='3d' )
ax.voxels(best_mask )
ax.set_title('True best results')
plt.show()

fig = plt.figure()
ax = fig.add_subplot(1,1,1, projection='3d' )
ax.voxels(worst_dice )
ax.set_title('Our worsk results')
plt.show()

fig = plt.figure()
ax = fig.add_subplot(1,1,1, projection='3d' )
ax.voxels(worst_mask )
ax.set_title('True worst results')
plt.show()

fig = plt.figure()
ax = fig.add_subplot(1,1,1, projection='3d' )
ax.voxels(average_dice , cmap = 'cividis')
ax.set_title('Our average results')
plt.show()


fig = plt.figure()
ax = fig.add_subplot(1,1,1, projection='3d' )
ax.voxels(average_mask )
ax.set_title('True average results')
plt.show()


