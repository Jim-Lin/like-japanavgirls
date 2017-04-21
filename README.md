# dark-classifier

# TensorFlow Image Classifier
## how to classify

## how to retrain
### docker image requisites
* bamos/openface
* gcr.io/tensorflow/tensorflow:latest-devel

### Step 1: collect face data
* /face/training-images/<xxx>/...
* /face/training-images/<yyy>/...
* /face/training-images/<zzz>/...
* ...

### (option) Step 2: face detection and alignment
`docker run -v /face:/face --rm bamos/openface /root/openface/util/align-dlib.py /face/training-images align outerEyesAndNose /face/aligned-images/ --size 96`

### (option) Step 3: check every face image count and convert png to jpeg
avoid issues ('WARNING: Folder has less than 20 images, which may cause issues.')

### Step 4: retrain model
[How to Retrain Inception's Final Layer for New Categories](https://www.tensorflow.org/tutorials/image_retraining)
`python /tensorflow/tensorflow/examples/image_retraining/retrain.py --image_dir /face/aligned-images-jpeg --output_graph /face/output_graph.gb --output_labels /face/output_labels.txt --how_many_training_steps 500 --model_dir /face/inception --bottleneck_dir /face/bottleneck`

and you will get the new classifier (output_graph.gb and output_labels.txt) to able to do DARK Facial Recognition
