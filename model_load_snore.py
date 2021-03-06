from keras.models import Sequential, Model
from keras.layers import LSTM, Dense, Dropout, concatenate, Input, Lambda, Conv2D, Flatten, Permute, Reshape, multiply, Activation, add, dot, Conv2DTranspose, average, maximum, GRU, Conv1D
from keras.layers.pooling import MaxPooling1D, MaxPooling2D
from keras.layers.normalization import BatchNormalization
from keras.layers.noise import GaussianDropout
from keras.applications.vgg16 import VGG16
from keras.applications.vgg16 import preprocess_input
from keras import metrics
from keras import backend as K
import numpy as np
from snore_data_extractor import *
from keras.callbacks import ModelCheckpoint, EarlyStopping, TensorBoard
import tensorflow as tf
from keras import losses
from sklearn.metrics import recall_score, confusion_matrix
from keras.preprocessing.image import ImageDataGenerator
from keras.utils import plot_model


#class for slicing tensors in keras
class Slice:

    def __init__(self, dim=0, portion=0):
        if dim != 0:
            self.dim = dim
        if portion != 0:
            self.portion = portion
            self.start = 0
        else:
            self.i = 0

    def slice_pieces_3D(self, x):
        if self.dim == 3:
            original_shape = K.int_shape(x)
            output = x[:, :, :, self.i]
        elif self.dim == 2:
            original_shape = K.int_shape(x)
            output = x[:, :, self.i, :]
        elif self.dim == 1:
            original_shape = K.int_shape(x)
            output = x[:, self.i, :, :]
        self.i += 1
        return output

    def slice_pieces_2D(self, x):
        if self.dim == 2:
            original_shape = K.int_shape(x)
            output = x[:, :, self.i]
        elif self.dim == 1:
            original_shape = K.int_shape(x)
            output = x[:, self.i, :]
        self.i += 1
        return output

    def slice_portions_3D(self, x):
        if self.dim == 3:
            original_shape = K.int_shape(x)
            output = x[:, :, :, self.start:self.start+int(original_shape[3]/self.portion)]
            self.start += int(original_shape[3]/self.portion)
        elif self.dim == 2:
            original_shape = K.int_shape(x)
            output = x[:, :, self.start:self.start+int(original_shape[2]/self.portion), :]
            self.start += int(original_shape[2]/self.portion)
        elif self.dim == 1:
            original_shape = K.int_shape(x)
            output = x[:, self.start:self.start+int(original_shape[1]/self.portion), :, :]
            self.start += int(original_shape[1]/self.portion)
        return output

    def slice_portions_2D(self, x):
        if self.dim == 2:
            original_shape = K.int_shape(x)
            output = x[:, :, self.start:self.start+int(original_shape[2]/self.portion)]
            self.start += int(original_shape[2]/self.portion)
        elif self.dim == 1:
            original_shape = K.int_shape(x)
            output = x[:, self.start:self.start+int(original_shape[1]/self.portion), :]
            self.start += int(original_shape[1]/self.portion)
        return output


# DenConvGRU+Channel Slice Model
def image_entry_model_32(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 3))

    x_0 = inputs
    x_1_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_2_1 = MaxPooling2D(pool_size=(2,2), padding='same')(x_1_1)
    x_3_1 = MaxPooling2D(pool_size=(4,4), padding='same')(x_1_1)
    x_1 = x_1_1
    x_2_2 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_3_2 = MaxPooling2D(pool_size=(2,2), padding='same')(x_2_2)
    x_2 = concatenate([x_2_1, x_2_2])
    x_3_3 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3 = concatenate([x_3_1, x_3_2, x_3_3])

    x_3 = MaxPooling2D(pool_size=(3,3))(x_3)

    x_shape = K.int_shape(x_3)
    x_3 = [Lambda(slicer_3D.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_3) for _ in range(x_shape[3])]
    x_3 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_3]
    x_3 = concatenate(x_3, axis=1)

    x_4 = GRU(256, return_sequences=True)(x_3)
    x_5 = GRU(128)(x_4)

    prediction = Dense(4, activation="softmax")(x_5)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts))
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.01).minimize(loss)
    '''

    return model


# DenConvGRU+Time Slice Model
def image_entry_model_33(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 3))

    x_0 = inputs
    x_1_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_2_1 = MaxPooling2D(pool_size=(2,2), padding='same')(x_1_1)
    x_3_1 = MaxPooling2D(pool_size=(4,4), padding='same')(x_1_1)
    x_1 = x_1_1
    x_2_2 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_3_2 = MaxPooling2D(pool_size=(2,2), padding='same')(x_2_2)
    x_2 = concatenate([x_2_1, x_2_2])
    x_3_3 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3 = concatenate([x_3_1, x_3_2, x_3_3])

    x_3 = MaxPooling2D(pool_size=(3,3))(x_3)

    x_3 = Permute((3, 2, 1))(x_3)

    x_shape = K.int_shape(x_3)
    x_3 = [Lambda(slicer_3D.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_3) for _ in range(x_shape[3])]
    x_3 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_3]
    x_3 = concatenate(x_3, axis=1)

    x_4 = GRU(256, return_sequences=True)(x_3)
    x_5 = GRU(128)(x_4)

    prediction = Dense(4, activation="softmax")(x_5)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts))
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.01).minimize(loss)
    '''

    return model


# Fusion-DualConvGRU+L2 Regularizer
def image_entry_model_36(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 3))

    x_0 = inputs

    def Conv_filters(x_0):

        x_1_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_0)
        x_1_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_0)
        x_1 = average([x_1_1, x_1_2])

        x_2_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_1)
        x_2_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_1)
        x_2 = average([x_2_1, x_2_2])

        x_3_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_2)
        x_3_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_2)
        x_3 = average([x_3_1, x_3_2])

        x_4 = MaxPooling2D(pool_size=(3, 3), padding="same")(x_3)

        return x_4

    x_4_1 = Conv_filters(x_0)
    x_4_1 = Permute((3, 2, 1))(x_4_1)

    x_shape = K.int_shape(x_4_1)
    x_4_1 = [Lambda(slicer_3D_0.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_4_1) for _ in range(x_shape[3])]
    x_4_1 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_4_1]
    x_4_1 = concatenate(x_4_1, axis=1)

    x_5_1 = GRU(256, return_sequences=True)(x_4_1)
    x_6_1 = GRU(128)(x_5_1)

    x_4_2 = Conv_filters(x_0)
    x_shape = K.int_shape(x_4_2)

    x_4_2 = [Lambda(slicer_3D_1.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_4_2) for _ in range(x_shape[3])]
    x_4_2 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_4_2]
    x_4_2 = concatenate(x_4_2, axis=1)

    x_5_2 = GRU(256, return_sequences=True)(x_4_2)
    x_6_2 = GRU(128)(x_5_2)

    x_6 = concatenate([x_6_1, x_6_2])

    x_7 = Dense(128, activation="relu")(x_6)

    prediction = Dense(4, activation="softmax")(x_7)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts))
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.01).minimize(loss)
    '''

    return model


# Fusion-DualConvGRU+Dropout
def image_entry_model_37(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 3))

    x_0 = inputs

    def Conv_filters(x_0):

        x_1_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_0)
        x_1_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_0)
        x_1 = average([x_1_1, x_1_2])

        x_2_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_1)
        x_2_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_1)
        x_2 = average([x_2_1, x_2_2])

        x_3_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_2)
        x_3_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_2)
        x_3 = average([x_3_1, x_3_2])

        x_4 = MaxPooling2D(pool_size=(3, 3), padding="same")(x_3)

        x_4 = Dropout(0.5)(x_4)

        return x_4

    x_4_1 = Conv_filters(x_0)
    x_4_1 = Permute((3, 2, 1))(x_4_1)

    x_shape = K.int_shape(x_4_1)
    x_4_1 = [Lambda(slicer_3D_0.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_4_1) for _ in range(x_shape[3])]
    x_4_1 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_4_1]
    x_4_1 = concatenate(x_4_1, axis=1)

    x_5_1 = GRU(256, return_sequences=True)(x_4_1)
    x_6_1 = GRU(128)(x_5_1)

    x_4_2 = Conv_filters(x_0)
    x_shape = K.int_shape(x_4_2)

    x_4_2 = [Lambda(slicer_3D_1.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_4_2) for _ in range(x_shape[3])]
    x_4_2 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_4_2]
    x_4_2 = concatenate(x_4_2, axis=1)

    x_5_2 = GRU(256, return_sequences=True)(x_4_2)
    x_6_2 = GRU(128)(x_5_2)

    x_6 = concatenate([x_6_1, x_6_2])

    x_7 = Dense(128, activation="relu")(x_6)

    prediction = Dense(4, activation="softmax")(x_7)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts))
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.01).minimize(loss)
    '''

    return model


# 1DConvGRU
def image_entry_model_38(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 1))

    x_0 = Reshape((time_steps, data_dim))(inputs)

    x_1 = Conv1D(filters=128, kernel_size=3, strides=2, padding="same", activation="relu")(x_0)

    x_2 = Conv1D(filters=128, kernel_size=3, strides=2, padding="same", activation="relu")(x_1)

    x_3 = Conv1D(filters=128, kernel_size=3, strides=2, padding="same", activation="relu")(x_2)

    x_3 = MaxPooling1D(pool_size=3, padding="same")(x_3)

    x_4 = GRU(256, return_sequences=True)(x_3)
    x_5 = GRU(128)(x_4)

    prediction = Dense(4, activation="softmax")(x_5)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts))
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.0).minimize(loss)
    '''

    return model



# DualConvGRU+Channel Slice Model
def image_entry_model_41(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 3))

    x_0 = inputs
    x_1_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1 = average([x_1_1, x_1_2])

    x_2_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2 = average([x_2_1, x_2_2])

    x_3_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3 = average([x_3_1, x_3_2])

    x_4 = MaxPooling2D(pool_size=(3, 3), padding="same")(x_3)

    x_shape = K.int_shape(x_4)
    x_4 = [Lambda(slicer_3D.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_4) for _ in range(x_shape[3])]
    x_4 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_4]
    x_4 = concatenate(x_4, axis=1)

    x_5 = GRU(256, return_sequences=True)(x_4)
    x_6 = GRU(128)(x_5)

    prediction = Dense(4, activation="softmax")(x_6)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts))
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.01).minimize(loss)
    '''

    return model


# DualConvGRU+Time Slice Model
def image_entry_model_42(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 3))

    x_0 = inputs
    x_1_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1 = average([x_1_1, x_1_2])

    x_2_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2 = average([x_2_1, x_2_2])

    x_3_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3 = average([x_3_1, x_3_2])

    x_4 = MaxPooling2D(pool_size=(3, 3), padding="same")(x_3)
    x_4 = Permute((3, 2, 1))(x_4)

    x_shape = K.int_shape(x_4)
    x_4 = [Lambda(slicer_3D.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_4) for _ in range(x_shape[3])]
    x_4 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_4]
    x_4 = concatenate(x_4, axis=1)

    x_5 = GRU(256, return_sequences=True)(x_4)
    x_6 = GRU(128)(x_5)

    prediction = Dense(4, activation="softmax")(x_6)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts))
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.01).minimize(loss)
    '''

    return model


# DualConvGRU+Channel Slice Model+Dropout
def image_entry_model_43(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 3))

    x_0 = inputs
    x_1_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1 = average([x_1_1, x_1_2])

    x_2_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2 = average([x_2_1, x_2_2])

    x_3_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3 = average([x_3_1, x_3_2])

    x_4 = MaxPooling2D(pool_size=(3, 3), padding="same")(x_3)

    x_4 = Dropout(0.5)(x_4)

    x_shape = K.int_shape(x_4)
    x_4 = [Lambda(slicer_3D.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_4) for _ in range(x_shape[3])]
    x_4 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_4]
    x_4 = concatenate(x_4, axis=1)

    x_5 = GRU(256, return_sequences=True)(x_4)
    x_6 = GRU(128)(x_5)

    prediction = Dense(4, activation="softmax")(x_6)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts))
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.01).minimize(loss)
    '''

    return model


# DualConvGRU+Time Slice Model+Dropout
def image_entry_model_44(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 3))

    x_0 = inputs
    x_1_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1 = average([x_1_1, x_1_2])

    x_2_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2 = average([x_2_1, x_2_2])

    x_3_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3 = average([x_3_1, x_3_2])

    x_4 = MaxPooling2D(pool_size=(3, 3), padding="same")(x_3)
    x_4 = Permute((3, 2, 1))(x_4)
    x_4 = Dropout(0.5)(x_4)

    x_shape = K.int_shape(x_4)
    x_4 = [Lambda(slicer_3D.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_4) for _ in range(x_shape[3])]
    x_4 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_4]
    x_4 = concatenate(x_4, axis=1)

    x_5 = GRU(256, return_sequences=True)(x_4)
    x_6 = GRU(128)(x_5)

    prediction = Dense(4, activation="softmax")(x_6)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts))
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.01).minimize(loss)
    '''

    return model


# DualConvGRU+Channel Slice Model+L2 Regularizer
def image_entry_model_45(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 3))

    x_0 = inputs
    x_1_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1 = average([x_1_1, x_1_2])

    x_2_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2 = average([x_2_1, x_2_2])

    x_3_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3 = average([x_3_1, x_3_2])

    x_4 = MaxPooling2D(pool_size=(3, 3), padding="same")(x_3)

    x_shape = K.int_shape(x_4)
    x_4 = [Lambda(slicer_3D.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_4) for _ in range(x_shape[3])]
    x_4 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_4]
    x_4 = concatenate(x_4, axis=1)

    x_5 = GRU(256, return_sequences=True)(x_4)
    x_6 = GRU(128)(x_5)

    prediction = Dense(4, activation="softmax")(x_6)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    regularizer = tf.contrib.layers.l2_regularizer(0.01)
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts)) + tf.contrib.layers.apply_regularization(regularizer, weights_list=train_var[:-8])
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001).minimize(loss)
    '''

    return model


# DualConvGRU+Time Slice Model+L2 Regularizer
def image_entry_model_46(time_steps, data_dim):

    inputs = Input(shape=(time_steps, data_dim, 3))

    x_0 = inputs
    x_1_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_0)
    x_1 = average([x_1_1, x_1_2])

    x_2_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_1)
    x_2 = average([x_2_1, x_2_2])

    x_3_1 = Conv2D(filters=16, kernel_size=(3, 4), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3_2 = Conv2D(filters=16, kernel_size=(3, 2), strides=(2, 2), padding="same", activation="relu")(x_2)
    x_3 = average([x_3_1, x_3_2])

    x_4 = MaxPooling2D(pool_size=(3, 3), padding="same")(x_3)
    x_4 = Permute((3, 2, 1))(x_4)

    x_shape = K.int_shape(x_4)
    x_4 = [Lambda(slicer_3D.slice_pieces_3D, output_shape=(x_shape[1],x_shape[2], 1))(x_4) for _ in range(x_shape[3])]
    x_4 = [Reshape((1, K.int_shape(Flatten()(each))[1]))(Flatten()(each)) for each in x_4]
    x_4 = concatenate(x_4, axis=1)

    x_5 = GRU(256, return_sequences=True)(x_4)
    x_6 = GRU(128)(x_5)

    prediction = Dense(4, activation="softmax")(x_6)

    model = Model(inputs=inputs, outputs=prediction)
    model.summary()

    '''
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=True)
    epoch_num = 500
    batch_size = 16
    regularizer = tf.contrib.layers.l2_regularizer(0.01)
    loss = tf.reduce_mean(losses.kullback_leibler_divergence(labels, predicts)) + tf.contrib.layers.apply_regularization(regularizer, weights_list=train_var[:-8])
    train_step = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.01).minimize(loss)
    '''

    return model


if __name__ == "__main__":

    # some basic setups of model
    ############################################################################
    num_classes = 4
    time_steps = 252
    data_dim = 176

    slicer_3D = Slice(dim=3)
    slicer_3D_0 = Slice(dim=3)
    slicer_3D_1 = Slice(dim=3)

    load_folder_path = "/data/jw11815/snore_spectrogram_5/"


    # extract train data with preprocessing
    ############################################################################
    train = snore_data_extractor(load_folder_path, one_hot=True, data_mode="train", resize=(data_dim, time_steps), timechain=False, duplicate=True, colour_mode="RGB")

    train_features, train_labels = train.full_data()
    train_features = np.array(train_features).astype("float32")
    train_features /= 255
    x_train = np.rollaxis(train_features, 2, 1)
    y_train = np.array(train_labels)


    # extract dev data with preprocessing
    ############################################################################
    devel = snore_data_extractor(load_folder_path, one_hot=True, data_mode="devel", resize=(data_dim, time_steps), timechain=False, duplicate=False, colour_mode="RGB")

    devel_features, devel_labels = devel.full_data()
    devel_features = np.array(devel_features).astype("float32")
    devel_features /= 255
    x_devel = np.rollaxis(devel_features, 2, 1)
    y_devel = np.array(devel_labels)


    # extract test data with preprocessing
    ############################################################################
    test = snore_data_extractor(load_folder_path, one_hot=True, data_mode="test", resize=(data_dim, time_steps), timechain=False, duplicate=False, colour_mode="RGB")

    test_features, test_labels = test.full_data()
    test_features = np.array(test_features).astype("float32")
    test_features /= 255
    x_test = np.rollaxis(test_features, 2, 1)
    y_test = np.array(test_labels)


    # restore the model according to the best results of dev data during training
    ############################################################################
    model = image_entry_model_45(time_steps, data_dim)

    model.load_weights("weights_spectro_5_45_dev.h5")

    predict_train = model.predict(x_train)
    train_UAR = recall_score(np.argmax(y_train, axis=1), np.argmax(predict_train, axis=1), average="macro")
    print ("This is the current train UAR: ", train_UAR)
    print (confusion_matrix(np.argmax(y_train, axis=1), np.argmax(predict_train, axis=1)))
    print ("\n")
    predict_devel = model.predict(x_devel)
    devel_UAR = recall_score(np.argmax(y_devel, axis=1), np.argmax(predict_devel, axis=1), average="macro")
    print ("This is the current devel UAR: ", devel_UAR)
    print (confusion_matrix(np.argmax(y_devel, axis=1), np.argmax(predict_devel, axis=1)))
    print ("\n")
    predict_test = model.predict(x_test)
    test_UAR = recall_score(np.argmax(y_test, axis=1), np.argmax(predict_test, axis=1), average="macro")
    print ("This is the current test UAR: ", test_UAR)
    print (confusion_matrix(np.argmax(y_test, axis=1), np.argmax(predict_test, axis=1)))
    print ("\n")
