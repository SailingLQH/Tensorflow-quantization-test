from utils.layers import *
import tensorflow as tf


def get_weights(weights, weight_name, bias_name='bbb'):
    w = tf.constant(weights[weight_name], dtype=tf.float32)
    try:
        b = tf.constant(weights[bias_name], dtype=tf.float32)
    except:
        b = None
    return w, b


def get_bn_param(weights, layer_num):
    mean = 'batchnormalization_' + str(layer_num) + '_running_mean:0'
    std = 'batchnormalization_' + str(layer_num) + '_running_std:0'
    beta = 'batchnormalization_' + str(layer_num) + '_beta:0'
    gamma = 'batchnormalization_' + str(layer_num) + '_gamma:0'

    mean = tf.constant(weights[mean], dtype=tf.float32)
    std = tf.constant(weights[std], dtype=tf.float32)
    beta = tf.constant(weights[beta], dtype=tf.float32)
    gamma = tf.constant(weights[gamma], dtype=tf.float32)
    return mean, std, beta, gamma


def conv_block(x, weights, conv_num, bn_num, strides=1, padding='SAME', activation=True):
    conv_name = 'convolution2d_{}_W:0'.format(conv_num)
    bias_name = 'convolution2d_{}_b:0'.format(conv_num)
    w, b = get_weights(weights, conv_name, bias_name)
    x = conv_2d(x, w, None, strides=strides, padding=padding)
    mean, std, beta, gamma = get_bn_param(weights, bn_num)
    x = batch_norm(x, mean, std, beta, gamma)
    if activation:
        x = tf.nn.relu(x)
    conv_num += 1
    bn_num += 1
    return x, conv_num, bn_num


def separable_conv_block(x, weights, sep_num, bn_num, strides=1, padding='SAME', activation=True):
    dw_name = 'separableconvolution2d_{}_depthwise_kernel:0'.format(sep_num)
    pw_name = 'separableconvolution2d_{}_pointwise_kernel:0'.format(sep_num)

    dw, b = get_weights(weights, dw_name)
    pw, b = get_weights(weights, pw_name)

    x = separable_conv2d(x, dw, pw, strides=strides, padding=padding)
    mean, std, beta, gamma = get_bn_param(weights, bn_num)
    x = batch_norm(x, mean, std, beta, gamma)
    if activation:
        x = tf.nn.relu(x)
    sep_num += 1
    bn_num += 1
    return x, sep_num, bn_num


def Xception(x, weights):
    bn_count = 1
    conv_count = 1
    sepconv_count = 1
    x = tf.reshape(x, shape=[-1, 299, 299, 3])

    x, conv_count, bn_count = conv_block(x, weights, conv_count, bn_count, strides=2, padding='VALID')
    x, conv_count, bn_count = conv_block(x, weights, conv_count, bn_count, strides=1, padding='VALID')
    residual, conv_count, bn_count = conv_block(x, weights, conv_count, bn_count,strides=2, activation=False)

    x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count)
    x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count, activation=False)
    x = maxpool_2d(x, k=3, s=2, padding='SAME')
    x = tf.add(x, residual)

    residual, conv_count, bn_count = conv_block(x, weights, conv_count, bn_count, strides=2, activation=False)

    x = tf.nn.relu(x)
    x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count)
    x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count, activation=False)
    x = maxpool_2d(x, k=3, s=2, padding='SAME')
    x = tf.add(x, residual)

    residual, conv_count, bn_count = conv_block(x, weights, conv_count, bn_count, strides=2, activation=False)

    x = tf.nn.relu(x)
    x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count)
    x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count, activation=False)
    x = maxpool_2d(x, k=3, s=2, padding='SAME')
    x = tf.add(x, residual)

    for i in range(8):
        residual = x
        x = tf.nn.relu(x)
        x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count)
        x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count)
        x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count, activation=False)
        x = tf.add(x, residual)

    residual, conv_count, bn_count = conv_block(x, weights, conv_count, bn_count, strides=2, activation=False)

    x = tf.nn.relu(x)
    x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count)
    x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count, activation=False)
    x = maxpool_2d(x, k=3, s=2, padding='SAME')
    x = tf.add(x, residual)

    x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count)
    x, sepconv_count, bn_count = separable_conv_block(x, weights, sepconv_count, bn_count)

    x = avgpool_2d(x, k=8)
    w = tf.constant(weights['dense_2_W:0'], dtype=tf.float32)
    b = tf.constant(weights['dense_2_b:0'], dtype=tf.float32)
    x = tf.reshape(x, [-1, w.get_shape().as_list()[0]])
    x = denselayer(x, w, b)
    return x
