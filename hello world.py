import tensorflow as tf
tf.compat.v1.disable_eager_execution()
hello = tf.constant('hello,world')
sess= tf.compat.v1.Session()
print(sess.run(hello))
