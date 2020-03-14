# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 15:57:38 2020

"""
import tensorflow.compat.v1 as tf
import cv2
import numpy as np
import os
import random
import sys
from sklearn.model_selection import train_test_split
tf.disable_v2_behavior()

"""
输出路径
"""
path_mine=".././texture/mine/output"
path_others=".././texture/others/output"
size=64

"""
调整图片大小
"""
imgs=[]
labs=[]

"""
创建图形相关变量
"""
tf.reset_default_graph()

#获取需要填充的图片的大小
def getImageSize(img):
    h,w,_=img.shape
    top,bottom,left,right=(0,0,0,0)
    longest=max(h,w)
    
    if w<longest:
        tmp=longest-w
        left=tmp//2
        right=tmp-left 
    elif h<longest:
        tmp=longest-h
        top=tmp//2
        bottom=tmp-top
    else:
        pass
    return top,bottom,left,right

"""
读取测试图片
"""
def readImage(path,h=size,w=size):
    for filename in os.listdir(path):
        if filename.endswith('jpg'):
            filename=path+'/'+filename
            
            img=cv2.imread(filename)
            top,bottom,left,right=getImageSize(img)
            #扩充边缘
            img=cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT,value=[0,0,0])
            img=cv2.resize(img,(h,w))
            
            imgs.append(img)
            labs.append(path)
            
readImage(path_mine)
readImage(path_others)
            
#将数据存入数组
imgs=np.array(imgs)
labs=np.array([[0,1] if lab ==path_mine else [1,0] for lab in labs])

#随机划分测试集和训练集
train_x,test_x,train_y,test_y=train_test_split(imgs, labs,test_size=0.05,random_state=random.randint(0,100))
            
train_x=train_x.reshape(train_x.shape[0],size,size,3)
test_x=test_x.reshape(test_x.shape[0],size,size,3)

#将数据转化成百分数
train_x=train_x.astype('float32')/255.0
test_x=test_x.astype('float32')/255.0
            
print('train size:%s,test size:%s'%(len(train_x),len(test_x)))

#图片块，每次取100张图片
batch_size=100
num_batch=len(train_x)//batch_size
            
x = tf.placeholder(tf.float32, [None, size, size, 3])
y_ = tf.placeholder(tf.float32, [None, 2])
            
keep_prob_5 = tf.placeholder(tf.float32)
keep_prob_75= tf.placeholder(tf.float32)
            
def weightVariable(shape): 
    init = tf.random.normal(shape, stddev=0.01)
    return tf.Variable(init)

def biasVariable(shape): 
    init = tf.random.normal(shape)
    return tf.Variable(init)

def conv2d(x, W):
    return tf.nn.conv2d(x, W, strides=[1,1,1,1], padding='SAME')
 
def maxPool(x):
    return tf.nn.max_pool(x, ksize=[1,2,2,1], strides=[1,2,2,1], padding='SAME')
 
def dropout(x, keep):
    return tf.nn.dropout(x, keep)

#卷积神经网络
def cnnLayer():
    # 第一层
    W1 = weightVariable([3,3,3,32]) # 卷积核大小(3,3)， 输入通道(3)， 输出通道(32)
    b1 = biasVariable([32])
    # 卷积
    conv1 = tf.nn.relu(conv2d(x, W1) + b1)
    # 池化
    pool1 = maxPool(conv1)
    # 减少过拟合，随机让某些权重不更新
    drop1 = dropout(pool1, keep_prob_5)
 
    # 第二层
    W2 = weightVariable([3,3,32,64])
    b2 = biasVariable([64])
    conv2 = tf.nn.relu(conv2d(drop1, W2) + b2)
    pool2 = maxPool(conv2)
    drop2 = dropout(pool2, keep_prob_5)
 
    # 第三层
    W3 = weightVariable([3,3,64,64])
    b3 = biasVariable([64])
    conv3 = tf.nn.relu(conv2d(drop2, W3) + b3)
    pool3 = maxPool(conv3)
    drop3 = dropout(pool3, keep_prob_5)
 
    # 全连接层
    Wf = weightVariable([8*16*32, 512])
    bf = biasVariable([512])
    drop3_flat = tf.reshape(drop3, [-1, 8*16*32])
    dense = tf.nn.relu(tf.matmul(drop3_flat, Wf) + bf)
    dropf = dropout(dense, keep_prob_75)
 
    # 输出层
    Wout = weightVariable([512,2])
    bout = weightVariable([2])
    #out = tf.matmul(dropf, Wout) + bout
    out = tf.add(tf.matmul(dropf, Wout), bout)
    return out


def cnnTrain():
    
    out = cnnLayer()
 
    cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=out, labels=y_))
 
    train_step = tf.train.AdamOptimizer(0.01).minimize(cross_entropy)
    
    # 比较标签是否相等，再求的所有数的平均值，tf.cast(强制转换类型)
    accuracy = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(out, 1), tf.argmax(y_, 1)), tf.float32))
    # 将loss与accuracy保存以供tensorboard使用
    tf.summary.scalar('loss', cross_entropy)
    tf.summary.scalar('accuracy', accuracy)
    merged_summary_op = tf.summary.merge_all()
    
    # 数据保存器的初始化
    saver = tf.train.Saver()
 
    with tf.Session() as sess:
 
        sess.run(tf.global_variables_initializer())
 
        summary_writer = tf.summary.FileWriter(".././tmp", graph=tf.get_default_graph())
 
        for n in range(10):
             # 每次取128(batch_size)张图片
            for i in range(num_batch):
                batch_x = train_x[i*batch_size : (i+1)*batch_size]
                batch_y = train_y[i*batch_size : (i+1)*batch_size]
                # 开始训练数据，同时训练三个变量，返回三个数据
                
                _,loss,summary = sess.run([train_step, cross_entropy, merged_summary_op],
                                           feed_dict={x:batch_x,y_:batch_y,keep_prob_5:0.5,keep_prob_75:0.75})
                summary_writer.add_summary(summary, n*num_batch+i)
                # 打印损失
                print(n*num_batch+i, loss)
 
                if (n*num_batch+i) % 100 == 0:
                    # 获取测试数据的准确率
                    acc = accuracy.eval({x:test_x, y_:test_y, keep_prob_5:1.0, keep_prob_75:1.0})
                    print(n*num_batch+i, acc,'acc %s'%n)
                    # 准确率大于0.95时保存并退出
                    if acc > 0.95 and n > 4:
                        saver.save(sess, '.././model/train_faces.model', global_step=n*num_batch+i)
                        sys.exit(0)
        print('accuracy less 0.95, exited!')
        

cnnTrain()
